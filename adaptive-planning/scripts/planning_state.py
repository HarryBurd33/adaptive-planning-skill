#!/usr/bin/env python3
"""Optional state integrity checker; does not generate plans or contact services."""
import argparse
import calendar
import copy
import hashlib
import json
import os
import math
import re
from pathlib import Path
import sys
import tempfile
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

SCHEMA = Path(__file__).resolve().parents[1] / 'state.schema.json'
UTC = timezone.utc


def load(path):
    with Path(path).open(encoding='utf-8') as f:
        return json.load(f)


def stamp(value, zone=None):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.utcoffset() is None:
        raise ValueError('timestamp requires explicit UTC offset')
    if zone is not None:
        local = d.astimezone(zone)
        if local.replace(tzinfo=None) != d.replace(tzinfo=None) or local.utcoffset() != d.utcoffset():
            raise ValueError('local timestamp/offset does not exist in profile timezone')
    return d


def structural(value, rule, path='$'):
    errors = []
    types = rule.get('type', [])
    if isinstance(types, str): types = [types]
    ok = {'object': isinstance(value, dict), 'array': isinstance(value, list),
          'string': isinstance(value, str), 'integer': type(value) is int,
          'boolean': type(value) is bool, 'null': value is None,
          'number': type(value) in (int, float) and math.isfinite(value)}
    if types and not any(ok.get(t, False) for t in types):
        return [path + ': wrong type']
    if 'enum' in rule and value not in rule['enum']: errors.append(path + ': invalid value')
    if isinstance(value, dict):
        for key in rule.get('required', []):
            if key not in value: errors.append(path + ': missing ' + key)
        props = rule.get('properties', {})
        for k, v in value.items():
            if k in props: errors += structural(v, props[k], path + '.' + k)
            elif rule.get('additionalProperties') is False: errors.append(path + ': unknown field ' + k)
            elif isinstance(rule.get('additionalProperties'), dict): errors += structural(v, rule['additionalProperties'], path + '.' + k)
    if isinstance(value, list):
        if len(value) < rule.get('minItems', 0): errors.append(path + ': too few items')
        for i, v in enumerate(value): errors += structural(v, rule.get('items', {}), path + '[' + str(i) + ']')
    if type(value) in (int, float) and value < rule.get('minimum', value): errors.append(path + ': below minimum')
    if type(value) in (int, float) and value > rule.get('maximum', value): errors.append(path + ': above maximum')
    if isinstance(value, str):
        if len(value) < rule.get('minLength', 0): errors.append(path + ': empty value')
        if 'pattern' in rule and re.search(rule['pattern'], value) is None: errors.append(path + ': invalid pattern')
        fmt = rule.get('format')
        try:
            if fmt == 'date': date.fromisoformat(value)
            elif fmt == 'date-time': stamp(value)
            elif fmt == 'time':
                t = time.fromisoformat(value)
                if t.tzinfo is not None or len(value) != 5: raise ValueError('use HH:MM')
        except ValueError as e: errors.append(path + ': ' + str(e))
    return errors


def period(day, frequency, week_start):
    if frequency == 'daily': return day, day + timedelta(days=1)
    if frequency == 'weekly':
        first = day - timedelta(days=(day.weekday() - week_start) % 7)
        return first, first + timedelta(days=7)
    first = day.replace(day=1)
    return first, (first.replace(year=first.year+1, month=1) if first.month == 12 else first.replace(month=first.month+1))


def sleep_intervals(state, start_day, end_day):
    """UTC protected windows by local start-date anchor, [start_day, end_day)."""
    constraints = state['extensions'].get('constraints_v2', {})
    problems = structural(constraints, load(SCHEMA)['properties']['extensions']['properties']['constraints_v2'])
    if problems: raise ValueError('; '.join(problems))
    if constraints and state['schema_version'] != 2: raise ValueError('constraints_v2 requires schema_version 2')
    zone = ZoneInfo(state['profile']['timezone'])
    normal = state['profile']['sleep']
    overrides = state['extensions'].get('constraints_v2', {}).get('sleep_exceptions', {})
    validated = {}
    for anchor, windows in overrides.items():
        day = date.fromisoformat(anchor)
        if day.isoformat() != anchor or not windows: raise ValueError('sleep exception requires ISO anchor and nonempty windows')
        validated[day] = []
        for window in windows:
            a, b = stamp(window['start'], zone), stamp(window['end'], zone)
            if a.date() != day: raise ValueError('sleep exception start must match anchor date')
            au, bu = a.astimezone(UTC), b.astimezone(UTC)
            if bu <= au: raise ValueError('sleep exception end must follow start')
            validated[day].append((au, bu))
    if normal and normal['start'] == normal['end']: raise ValueError('sleep window cannot have equal endpoints')
    if isinstance(start_day, str): start_day = date.fromisoformat(start_day)
    if isinstance(end_day, str): end_day = date.fromisoformat(end_day)
    result = []
    day = start_day
    while day < end_day:
        if day in validated: result.extend(validated[day])
        elif normal:
            a = datetime.combine(day, time.fromisoformat(normal['start']), zone)
            end = day + timedelta(days=normal['end'] < normal['start'])
            b = datetime.combine(end, time.fromisoformat(normal['end']), zone)
            # Reject imaginary local normal windows instead of silently changing protection.
            stamp(a.isoformat(), zone); stamp(b.isoformat(), zone)
            result.append((a.astimezone(UTC), b.astimezone(UTC)))
        day += timedelta(days=1)
    return sorted(result)


def check(state, as_of=None):
    errors = structural(state, load(SCHEMA)); warnings = []; totals = {}; outside_horizon = {}; dependency_readiness = {}
    try: as_of = stamp(as_of).astimezone(UTC) if isinstance(as_of, str) else (stamp(as_of.isoformat()).astimezone(UTC) if as_of is not None else None)
    except (ValueError, AttributeError) as e: errors.append('as_of: ' + str(e))
    if errors: return {'valid': False, 'errors': errors, 'warnings': warnings, 'totals': totals, 'outside_horizon': outside_horizon, 'dependency_readiness': dependency_readiness}
    try: zone = ZoneInfo(state['profile']['timezone'])
    except Exception as e: return {'valid':False, 'errors':['timezone unavailable: ' + str(e)], 'warnings':[], 'totals':{}, 'outside_horizon':{}, 'dependency_readiness':{}}
    if state['schema_version'] == 1 and 'constraints_v2' in state['extensions']: errors.append('constraints_v2 requires schema_version 2')
    constraints = state['extensions'].get('constraints_v2', {})
    for window in constraints.get('availability', []):
        try:
            if stamp(window['end'], zone).astimezone(UTC) <= stamp(window['start'], zone).astimezone(UTC): raise ValueError('end must follow start')
        except ValueError as e: errors.append('availability: ' + str(e))
    profile = state['profile']; sleep = profile['sleep']; horizon = state['dated_plan']
    if sleep and sleep['start'] == sleep['end']: errors.append('sleep window cannot have equal endpoints')
    if profile['week_start'] > 6: errors.append('week_start must be 0..6')
    start = date.fromisoformat(horizon['start']); end = date.fromisoformat(horizon['end'])
    if end <= start: errors.append('dated_plan.end must be after start (exclusive)')
    try: sleep_intervals(state, start - timedelta(days=1), end + timedelta(days=1))
    except ValueError as e: errors.append('sleep: ' + str(e))
    def indexed(items, label):
        result = {}
        for item in items:
            if item['id'] in result: errors.append(label + ': duplicate id ' + item['id'])
            result[item['id']] = item
        return result
    tasks = indexed(state['tasks'], 'task'); occurrences = indexed(state['occurrences'], 'occurrence')
    indexed(state['progress'], 'progress'); indexed(state['feedback'], 'feedback'); indexed(state['adaptations'], 'adaptation'); indexed(state['applied_updates'], 'update')
    for entry in state['model_week']:
        if entry['task_id'] is not None and entry['task_id'] not in tasks: errors.append('model_week: unknown task ' + entry['task_id'])
        if entry['start'] == entry['end']: errors.append('model_week: equal start/end is invalid')
    model_spans = []
    for i, entry in enumerate(state['model_week']):
        a = entry['weekday'] * 1440 + int(entry['start'][:2])*60 + int(entry['start'][3:])
        b = entry['weekday'] * 1440 + int(entry['end'][:2])*60 + int(entry['end'][3:])
        if b <= a: b += 1440
        for c, d, j in model_spans:
            if any(a < d + shift and c + shift < b for shift in (-10080, 0, 10080)): errors.append('model_week: overlap entries ' + str(j) + ' and ' + str(i))
        model_spans.append((a,b,i))
    evidence_ids = {x['id'] for x in state['feedback']} | {x['id'] for x in state['progress']}
    for progress in state['progress']:
        task = tasks.get(progress['task_id'])
        occurrence = occurrences.get(progress['occurrence_id'])
        if task is None: errors.append(progress['id'] + ': unknown progress task')
        elif task['recurrence'] and (occurrence is None or occurrence['task_id'] != task['id']): errors.append(progress['id'] + ': missing/mismatched progress occurrence')
        elif not task['recurrence'] and progress['occurrence_id'] is not None: errors.append(progress['id'] + ': nonrecurring progress has occurrence')
    prior_adaptations = set()
    for adaptation in state['adaptations']:
        if adaptation['reverts'] is not None and adaptation['reverts'] not in prior_adaptations: errors.append(adaptation['id'] + ': reversal must reference a previously recorded adaptation')
        prior_adaptations.add(adaptation['id'])
        if not adaptation['evidence_ids']: errors.append(adaptation['id'] + ': adaptation requires evidence')
        for eid in adaptation['evidence_ids']:
            if eid not in evidence_ids: errors.append(adaptation['id'] + ': unknown evidence ' + eid)
    for task in tasks.values():
        for dep in task['dependencies']:
            if dep not in tasks or dep == task['id']: errors.append(task['id'] + ': invalid dependency ' + dep)
        if task['deadline'] is not None:
            try: stamp(task['deadline'], zone)
            except ValueError as e: errors.append(task['id'] + ': deadline ' + str(e))
    def visit(tid, stack):
        if tid in stack: errors.append('dependency cycle: ' + tid); return
        if tid not in tasks: return
        for dep in tasks[tid]['dependencies']: visit(dep, stack | {tid})
    for tid in tasks: visit(tid, set())
    for oid, occurrence in occurrences.items():
        task = tasks.get(occurrence['task_id']); r = task and task['recurrence']
        if not r: errors.append(oid + ': occurrence requires recurring task'); continue
        pstart = date.fromisoformat(occurrence['period_start']); pend = date.fromisoformat(occurrence['period_end'])
        if (pstart, pend) != period(pstart, r['frequency'], profile['week_start']): errors.append(oid + ': period must be full anchored recurrence period')
        prefix = task['id'] + '@' + r['frequency'] + ':' + pstart.isoformat() + '#'
        suffix = oid[len(prefix):] if oid.startswith(prefix) else ''
        if not suffix.isdigit() or not 1 <= int(suffix) <= r['count']: errors.append(oid + ': invalid occurrence identity')
        if occurrence['remaining_minutes'] is not None and occurrence['remaining_minutes'] > r['minutes']: errors.append(oid + ': remaining exceeds occurrence target')
    # Verify expected occurrence inventory for every full period touching the dated view.
    for tid, task in tasks.items():
        r = task['recurrence']
        if not r: continue
        day = start
        while day < end:
            ps, pe = period(day, r['frequency'], profile['week_start'])
            for n in range(1, r['count'] + 1):
                oid = tid + '@' + r['frequency'] + ':' + ps.isoformat() + '#' + str(n)
                if oid not in occurrences: warnings.append(oid + ': recurrence occurrence missing; requirement unresolved')
            day = pe
    spans = []; ids = set(); reservation_ids = set(); scheduled = {}; all_by_task = {}
    for group, items in [('fixed', state['fixed_events']), ('block', horizon['blocks'])]:
        for item in items:
            label = item['id']
            if label in ids: errors.append('duplicate event/block id ' + label)
            ids.add(label)
            try:
                a = stamp(item['start'], zone); b = stamp(item['end'], zone)
                au, bu = a.astimezone(UTC), b.astimezone(UTC)
                if bu <= au: raise ValueError('end must follow start')
            except ValueError as e: errors.append(label + ': ' + str(e)); continue
            spans.append((au, bu, label))
            if group == 'fixed' and item['kind'] in {'protected', 'buffer', 'unavailable'}:
                reservation_ids.add(label)
            if group == 'block':
                task = tasks.get(item['task_id'])
                if not task: errors.append(label + ': unknown task'); continue
                oid = item['occurrence_id']; key = oid or item['task_id']
                if task['recurrence']:
                    o = occurrences.get(oid)
                    if not o or o['task_id'] != task['id']: errors.append(label + ': missing/mismatched occurrence'); continue
                    if a.date() < date.fromisoformat(o['period_start']) or b > datetime.combine(date.fromisoformat(o['period_end']), time(), zone): errors.append(label + ': outside recurrence period')
                elif oid is not None: errors.append(label + ': nonrecurring task has occurrence')
                minutes = (bu-au).total_seconds()/60
                if minutes < task['min_session_minutes'] and (as_of is None or bu > as_of): errors.append(label + ': shorter than minimum useful session')
                if not (start <= a.date() < end) or b > datetime.combine(end, time(), zone): errors.append(label + ': outside dated plan')
                if item['status'] == 'planned':
                    future_a = max(au, as_of) if as_of is not None else au
                    future_minutes = max(0, (bu-future_a).total_seconds()/60)
                    scheduled[key] = scheduled.get(key, 0) + future_minutes
                    if future_minutes: all_by_task.setdefault(task['id'], []).append((future_a, bu))
                    if task['deadline'] is not None and bu > stamp(task['deadline'], zone).astimezone(UTC): errors.append(label + ': after deadline')
            try:
                item_sleep = sleep_intervals(state, a.astimezone(zone).date() - timedelta(days=1), b.astimezone(zone).date() + timedelta(days=1))
                # Exceptions may explicitly span more than one day; their start anchor
                # can precede the ordinary overnight lookback.
                for anchor, windows in constraints.get('sleep_exceptions', {}).items():
                    if date.fromisoformat(anchor) < a.astimezone(zone).date() - timedelta(days=1):
                        item_sleep.extend((stamp(w['start'], zone).astimezone(UTC), stamp(w['end'], zone).astimezone(UTC)) for w in windows)
                if any(au < sb and sa < bu for sa, sb in item_sleep): errors.append(label + ': overlaps protected sleep')
            except ValueError as e: errors.append(label + ': sleep ' + str(e))
    spans.sort()
    for i, (a,b,label) in enumerate(spans):
        for c,d,other in spans[i+1:]:
            if c >= b: break
            # Generic reservation layers describe a union of protected time.
            # Actual appointments and scheduled work still collide with every layer.
            if label in reservation_ids and other in reservation_ids: continue
            errors.append(label + ': overlaps ' + other)
    for tid, blocks in all_by_task.items():
        readiness = 'ready'
        first = min(x[0] for x in blocks)
        for dep in tasks[tid]['dependencies']:
            prerequisite = tasks.get(dep)
            if prerequisite is None: continue
            remaining = prerequisite['remaining_minutes']
            if prerequisite['recurrence'] or remaining is None:
                if readiness != 'blocked': readiness = 'unknown'
                warnings.append(tid + ': dependency readiness unverified (unknown/series-level): ' + dep)
            elif remaining > 0:
                allocated_before = sum((b-a).total_seconds()/60 for a,b in all_by_task.get(dep, []) if b <= first)
                if allocated_before < remaining:
                    readiness = 'blocked'
                    errors.append(tid + ': scheduled before dependency ' + dep + ' full remaining effort finishes')
        dependency_readiness[tid] = readiness
    # A valid allocation of an intermediate task does not resolve uncertainty
    # or a known blocker earlier in its prerequisite chain.
    direct_readiness = dict(dependency_readiness)
    propagated = {}
    def readiness_for(tid, visiting):
        if tid in propagated: return propagated[tid]
        if tid in visiting: return 'blocked'  # Cycle is already an explicit error.
        readiness = direct_readiness.get(tid, 'ready')
        for dep in tasks[tid]['dependencies']:
            prerequisite = tasks.get(dep)
            if prerequisite is None: continue  # Unknown references already fail validation.
            if not prerequisite['recurrence'] and prerequisite['remaining_minutes'] == 0:
                continue  # Completed prerequisites need no further allocation.
            upstream = readiness_for(dep, visiting | {tid})
            if upstream == 'blocked': readiness = 'blocked'
            elif upstream == 'unknown' and readiness == 'ready': readiness = 'unknown'
        propagated[tid] = readiness
        return readiness
    for tid in dependency_readiness:
        readiness = readiness_for(tid, set())
        if readiness != direct_readiness[tid]:
            if readiness == 'blocked': errors.append(tid + ': prerequisite chain blocked')
            elif readiness == 'unknown': warnings.append(tid + ': prerequisite chain readiness unverified')
        dependency_readiness[tid] = readiness
    requirements = [(t['id'], t['remaining_minutes'], t['required']) for t in tasks.values() if not t['recurrence']]
    for occurrence in occurrences.values():
        if occurrence['task_id'] not in tasks: continue
        ps = date.fromisoformat(occurrence['period_start']); pe = date.fromisoformat(occurrence['period_end'])
        if ps < end and start < pe:
            requirements.append((occurrence['id'], occurrence['remaining_minutes'], tasks[occurrence['task_id']]['required']))
        else:
            outside_horizon[occurrence['id']] = {'relation': 'historical' if pe <= start else 'future', 'remaining_minutes': occurrence['remaining_minutes']}
    for key, remaining, required in requirements:
        allocated = scheduled.get(key, 0)
        totals[key] = {'remaining_minutes': remaining, 'scheduled_minutes': allocated, 'unallocated_minutes': None if remaining is None else max(0, remaining-allocated)}
        if remaining is None: warnings.append(key + ': effort unknown; feasibility unverified')
        elif allocated > remaining: errors.append(key + ': scheduled effort exceeds remaining effort')
        elif allocated < remaining: warnings.append(key + ': ' + str(remaining-allocated) + ' minutes unallocated' + (' (required)' if required else ' (optional)'))
    if sleep is None: warnings.append('sleep unknown; hard-constraint feasibility unverified')
    return {'valid': not errors, 'errors': sorted(set(errors)), 'warnings': sorted(set(warnings)), 'totals': totals, 'outside_horizon': outside_horizon, 'dependency_readiness': dependency_readiness}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def commit(current_path, proposed_path, expected, update_id, replace_extensions=(), as_of=None):
    current_path = Path(current_path)
    if current_path.is_symlink(): raise ValueError('refuse symbolic-link state')
    proposal = load(proposed_path)
    allowed_extensions = set(replace_extensions)
    if any(not key.strip() for key in allowed_extensions): raise ValueError('replacement extension key must not be empty')
    contract = {'proposal':proposal, 'replace_extensions':sorted(allowed_extensions)}
    as_of = stamp(as_of).astimezone(UTC) if isinstance(as_of, str) else (stamp(as_of.isoformat()).astimezone(UTC) if as_of is not None else None)
    if as_of is not None: contract['as_of'] = as_of.isoformat()
    proposal_hash = digest(contract)
    lock = current_path.with_name(current_path.name + '.lock')
    fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, str(os.getpid()).encode()); os.close(fd)
        current = load(current_path)
        current_errors = structural(current, load(SCHEMA))
        if current_errors: raise ValueError('current state requires reconciliation: ' + '; '.join(current_errors))
        for record in current['applied_updates']:
            if record['id'] == update_id:
                if record['sha256'] != proposal_hash: raise ValueError('update ID conflicts with different proposal')
                return {'committed':False, 'duplicate':True, 'revision':current['revision']}
        if current['revision'] != expected or proposal['revision'] != expected: raise ValueError('stale revision; reread and reconcile')
        if current['schema_version'] > proposal['schema_version']: raise ValueError('schema version downgrade forbidden')
        if current['plan_id'] != proposal['plan_id']: raise ValueError('plan identity changed')
        for key in allowed_extensions:
            if key not in proposal['extensions']: raise ValueError('replacement extension must be present in proposal: ' + key)
        for key in set(current['extensions']) | set(proposal['extensions']):
            if key not in allowed_extensions and (key not in current['extensions'] or key not in proposal['extensions'] or current['extensions'][key] != proposal['extensions'][key]): raise ValueError('unrelated extensions changed/deleted; preserve them: ' + key)
        for key in ['tasks','occurrences']:
            if {x['id'] for x in current[key]} - {x['id'] for x in proposal[key]}: raise ValueError('existing records deleted: ' + key)
        for key in ['progress','feedback','adaptations','applied_updates']:
            if proposal[key][:len(current[key])] != current[key]: raise ValueError('history changed/deleted: ' + key)
        old_completed = {b['id']:b for b in current['dated_plan']['blocks'] if b['status'] == 'completed'}
        new_blocks = {b['id']:b for b in proposal['dated_plan']['blocks']}
        for bid, block in old_completed.items():
            if new_blocks.get(bid) != block: raise ValueError('completed work changed/deleted: ' + bid)
        if as_of is not None:
            for old in current['dated_plan']['blocks']:
                a, b = stamp(old['start']).astimezone(UTC), stamp(old['end']).astimezone(UTC)
                if a >= as_of: continue
                new = new_blocks.get(old['id'])
                if new is None or any(new[k] != old[k] for k in ('task_id','occurrence_id','start')): raise ValueError('elapsed work changed/deleted: ' + old['id'])
                new_end = stamp(new['end']).astimezone(UTC)
                if (b <= as_of and new['end'] != old['end']) or (b > as_of and new_end < as_of): raise ValueError('elapsed work timing changed: ' + old['id'])
        result = check(proposal, as_of)
        if as_of is None: result['warnings'].append('elapsed preservation unverified; provide --as-of')
        if not result['valid']: raise ValueError('invalid proposed state: ' + '; '.join(result['errors']))
        proposal['revision'] += 1
        proposal['updated_at'] = datetime.now(UTC).isoformat()
        proposal['applied_updates'].append({'id':update_id, 'sha256':proposal_hash})
        temp = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=current_path.parent, prefix='.'+current_path.name+'.', delete=False) as f:
                temp = Path(f.name); os.chmod(f.name, 0o600)
                json.dump(proposal,f,indent=2,ensure_ascii=False);f.write('\n');f.flush();os.fsync(f.fileno())
            os.replace(str(temp),str(current_path))
        finally:
            if temp and temp.exists(): temp.unlink()
        return {'committed':True,'duplicate':False,'revision':proposal['revision'],'warnings':result['warnings']}
    finally:
        lock.unlink()


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    c=sub.add_parser('check');c.add_argument('state');c.add_argument('--as-of')
    c=sub.add_parser('commit');c.add_argument('current');c.add_argument('proposed');c.add_argument('--expected-revision',type=int,required=True);c.add_argument('--update-id',required=True);c.add_argument('--replace-extension',action='append',default=[],metavar='KEY');c.add_argument('--as-of')
    a=p.parse_args()
    try:
        if a.command=='check':
            result=check(load(a.state),a.as_of);print(json.dumps(result,indent=2));return 0 if result['valid'] else 2
        if not a.update_id.strip(): raise ValueError('update ID must not be empty')
        print(json.dumps(commit(a.current,a.proposed,a.expected_revision,a.update_id,a.replace_extension,a.as_of),indent=2));return 0
    except (ValueError,KeyError,TypeError,OSError,RecursionError) as e:
        print(json.dumps({'error':str(e)}));return 2

if __name__=='__main__': sys.exit(main())
