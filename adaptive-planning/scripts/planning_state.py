#!/usr/bin/env python3
"""Optional state integrity checker; does not generate plans or contact services."""
import argparse
import calendar
import copy
import hashlib
import json
import os
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
          'boolean': type(value) is bool, 'null': value is None}
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
    if isinstance(value, list):
        for i, v in enumerate(value): errors += structural(v, rule.get('items', {}), path + '[' + str(i) + ']')
    if type(value) is int and value < rule.get('minimum', value): errors.append(path + ': below minimum')
    if type(value) is int and value > rule.get('maximum', value): errors.append(path + ': above maximum')
    if isinstance(value, str):
        if len(value) < rule.get('minLength', 0): errors.append(path + ': empty value')
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


def check(state):
    errors = structural(state, load(SCHEMA)); warnings = []; totals = {}; outside_horizon = {}
    if errors: return {'valid': False, 'errors': errors, 'warnings': warnings, 'totals': totals, 'outside_horizon': outside_horizon}
    try: zone = ZoneInfo(state['profile']['timezone'])
    except Exception as e: return {'valid':False, 'errors':['timezone unavailable: ' + str(e)], 'warnings':[], 'totals':{}, 'outside_horizon':{}}
    profile = state['profile']; sleep = profile['sleep']; horizon = state['dated_plan']
    if sleep and sleep['start'] == sleep['end']: errors.append('sleep window cannot have equal endpoints')
    if profile['week_start'] > 6: errors.append('week_start must be 0..6')
    start = date.fromisoformat(horizon['start']); end = date.fromisoformat(horizon['end'])
    if end <= start: errors.append('dated_plan.end must be after start (exclusive)')
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
        if occurrence['remaining_minutes'] > r['minutes']: errors.append(oid + ': remaining exceeds occurrence target')
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
    spans = []; ids = set(); scheduled = {}; all_by_task = {}
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
                if minutes < task['min_session_minutes']: errors.append(label + ': shorter than minimum useful session')
                if not (start <= a.date() < end) or b > datetime.combine(end, time(), zone): errors.append(label + ': outside dated plan')
                if item['status'] == 'planned':
                    scheduled[key] = scheduled.get(key, 0) + minutes
                    all_by_task.setdefault(task['id'], []).append((au, bu))
                    if task['deadline'] is not None and bu > stamp(task['deadline'], zone).astimezone(UTC): errors.append(label + ': after deadline')
            if sleep:
                day = a.astimezone(zone).date() - timedelta(days=1)
                last = b.astimezone(zone).date()
                while day <= last:
                    sa = datetime.combine(day, time.fromisoformat(sleep['start']), zone)
                    sd = day + timedelta(days=1) if sleep['end'] < sleep['start'] else day
                    sb = datetime.combine(sd, time.fromisoformat(sleep['end']), zone)
                    if au < sb.astimezone(UTC) and sa.astimezone(UTC) < bu: errors.append(label + ': overlaps protected sleep'); break
                    day += timedelta(days=1)
    spans.sort()
    for i, (a,b,label) in enumerate(spans):
        for c,d,other in spans[i+1:]:
            if c >= b: break
            errors.append(label + ': overlaps ' + other)
    for tid, blocks in all_by_task.items():
        for dep in tasks[tid]['dependencies']:
            if dep in all_by_task and max(x[1] for x in all_by_task[dep]) > min(x[0] for x in blocks): errors.append(tid + ': scheduled before dependency ' + dep + ' finishes')
            elif dep in tasks and tasks[dep]['remaining_minutes'] != 0 and dep not in all_by_task: warnings.append(tid + ': dependency remaining effort unresolved: ' + dep)
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
    return {'valid': not errors, 'errors': sorted(set(errors)), 'warnings': sorted(set(warnings)), 'totals': totals, 'outside_horizon': outside_horizon}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def commit(current_path, proposed_path, expected, update_id, replace_extensions=()):
    current_path = Path(current_path)
    if current_path.is_symlink(): raise ValueError('refuse symbolic-link state')
    proposal = load(proposed_path)
    allowed_extensions = set(replace_extensions)
    if any(not key.strip() for key in allowed_extensions): raise ValueError('replacement extension key must not be empty')
    proposal_hash = digest({'proposal':proposal, 'replace_extensions':sorted(allowed_extensions)})
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
        result = check(proposal)
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
    c=sub.add_parser('check');c.add_argument('state')
    c=sub.add_parser('commit');c.add_argument('current');c.add_argument('proposed');c.add_argument('--expected-revision',type=int,required=True);c.add_argument('--update-id',required=True);c.add_argument('--replace-extension',action='append',default=[],metavar='KEY')
    a=p.parse_args()
    try:
        if a.command=='check':
            result=check(load(a.state));print(json.dumps(result,indent=2));return 0 if result['valid'] else 2
        if not a.update_id.strip(): raise ValueError('update ID must not be empty')
        print(json.dumps(commit(a.current,a.proposed,a.expected_revision,a.update_id,a.replace_extension),indent=2));return 0
    except (ValueError,KeyError,TypeError,OSError,RecursionError) as e:
        print(json.dumps({'error':str(e)}));return 2

if __name__=='__main__': sys.exit(main())
