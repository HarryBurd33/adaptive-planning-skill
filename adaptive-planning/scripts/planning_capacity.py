#!/usr/bin/env python3
"""Report explicit capacity and canonical views; never place work or certify feasibility."""
import argparse
import calendar
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
import json
import math
import sys
from zoneinfo import ZoneInfo
import planning_state as state_api

UTC = timezone.utc


def merge(spans):
    result = []
    for a, b in sorted((a, b) for a, b in spans if a < b):
        if result and a <= result[-1][1]:
            result[-1] = (result[-1][0], max(b, result[-1][1]))
        else:
            result.append((a, b))
    return result


def clip(spans, start, end):
    return merge((max(a, start), min(b, end)) for a, b in spans)


def subtract(spans, reserved):
    free = merge(spans)
    for a, b in merge(reserved):
        next_free = []
        for c, d in free:
            if b <= c or d <= a:
                next_free.append((c, d))
            else:
                if c < a:
                    next_free.append((c, a))
                if b < d:
                    next_free.append((b, d))
        free = next_free
    return free


def minutes(spans):
    return sum((b-a).total_seconds()/60 for a, b in merge(spans))


def number(value):
    return int(value) if float(value).is_integer() else round(value, 6)


def canonical_views(state, as_of=None):
    """Split actual UTC elapsed minutes at local midnight; IDs remain canonical."""
    zone = ZoneInfo(state['profile']['timezone'])
    cutoff = state_api.stamp(as_of).astimezone(UTC) if isinstance(as_of, str) else as_of
    buckets = {scale: defaultdict(lambda: {'planned_minutes': 0, 'block_ids': set(), 'occurrence_ids': set()})
               for scale in ['day', 'week', 'month']}
    for block in state['dated_plan']['blocks']:
        if block['status'] != 'planned':
            continue
        a = state_api.stamp(block['start'], zone).astimezone(UTC)
        b = state_api.stamp(block['end'], zone).astimezone(UTC)
        if cutoff is not None:
            a = max(a, cutoff)
        while a < b:
            day = a.astimezone(zone).date()
            midnight = datetime.combine(day+timedelta(days=1), time(), zone).astimezone(UTC)
            stop = min(b, midnight)
            week = day-timedelta(days=(day.weekday()-state['profile']['week_start']) % 7)
            keys = {'day': day.isoformat(), 'week': week.isoformat(), 'month': day.strftime('%Y-%m')}
            elapsed = (stop-a).total_seconds()/60
            for scale, key in keys.items():
                item = buckets[scale][key]
                item['planned_minutes'] += elapsed
                item['block_ids'].add(block['id'])
                if block['occurrence_id'] is not None:
                    item['occurrence_ids'].add(block['occurrence_id'])
            a = stop
    return {scale: {key: {'planned_minutes': number(item['planned_minutes']),
                         'block_ids': sorted(item['block_ids']),
                         'occurrence_ids': sorted(item['occurrence_ids'])}
                    for key, item in sorted(items.items())} for scale, items in buckets.items()}


def capacity(state, as_of=None):
    checked = state_api.check(state, as_of=as_of)
    errors = list(checked['errors'])
    warnings = list(checked['warnings'])
    if state_api.structural(state, state_api.load(state_api.SCHEMA)):
        return {'valid': False, 'errors': errors, 'warnings': warnings, 'feasibility': 'not-proven'}
    try:
        zone = ZoneInfo(state['profile']['timezone'])
        start_day = date.fromisoformat(state['dated_plan']['start'])
        end_day = date.fromisoformat(state['dated_plan']['end'])
        start = datetime.combine(start_day, time(), zone).astimezone(UTC)
        end = datetime.combine(end_day, time(), zone).astimezone(UTC)
        if end <= start:
            raise ValueError('invalid dated horizon')
        cutoff = state_api.stamp(as_of).astimezone(UTC) if isinstance(as_of, str) else as_of
        if cutoff is not None:
            start = max(start, cutoff)
        end = max(start, end)
        views = canonical_views(state, cutoff)
        allocated = sum(v['planned_minutes'] for v in views['day'].values())
        config = state['extensions'].get('constraints_v2', {})
        result = {'valid': checked['valid'], 'errors': errors, 'warnings': warnings,
                  'feasibility': 'not-proven', 'availability_known': 'availability' in config,
                  'views': views, 'allocated_minutes': number(allocated),
                  'dependency_readiness': checked.get('dependency_readiness', {})}
        if 'availability' not in config:
            warnings.append('availability unknown; do not infer free time from an empty calendar')
            result.update(candidate_minutes=None, buffer_minutes=None, usable_minutes=None,
                          required_minutes=None, shortfall_minutes=None, tasks={}, deferred_requirements=[])
            return result
        if state['schema_version'] != 2:
            raise ValueError('explicit capacity constraints require schema_version 2')
        def span(item):
            a = state_api.stamp(item['start'], zone).astimezone(UTC)
            b = state_api.stamp(item['end'], zone).astimezone(UTC)
            if a >= b:
                raise ValueError('capacity interval end must follow start')
            return a, b
        available = clip([span(v) for v in config['availability']], start, end)
        fixed = [(v, span(v)) for v in state['fixed_events']]
        reserved = [s for v, s in fixed if v['kind'] != 'buffer']
        reserved += state_api.sleep_intervals(state, start_day-timedelta(days=1), end_day)
        # Explicit multi-day overrides may start before the normal overnight lookback.
        for anchor, windows in config.get('sleep_exceptions', {}).items():
            if date.fromisoformat(anchor) < start_day-timedelta(days=1):
                reserved.extend(span(window) for window in windows)
        candidate = subtract(available, reserved)
        explicit = [s for v, s in fixed if v['kind'] == 'buffer' and s[0] < end and start < s[1]]
        pct = config.get('buffer_percent', 20)
        if isinstance(pct, bool) or not isinstance(pct, (int, float)) or not math.isfinite(pct) or not 0 <= pct <= 100:
            raise ValueError('buffer_percent must be finite within 0..100')
        use_explicit = bool(explicit)
        free = subtract(candidate, explicit) if use_explicit else candidate
        candidate_m = minutes(candidate)
        buffer_m = candidate_m-minutes(free) if use_explicit else math.ceil(candidate_m*pct/100)
        usable = max(0, candidate_m-buffer_m)
        result.update(candidate_minutes=number(candidate_m), buffer_minutes=number(buffer_m),
                      buffer_method='explicit blocks' if use_explicit else 'percentage',
                      buffer_percent=None if use_explicit else pct, usable_minutes=number(usable),
                      unallocated_usable_minutes=number(max(0, usable-allocated)),
                      allocated_over_capacity_minutes=number(max(0, allocated-usable)))
        if use_explicit and 'buffer_percent' in config:
            warnings.append('explicit buffer blocks used; percentage reserve not charged again')
        task_map = {t['id']: t for t in state['tasks']}
        requirements = []
        deferred = []
        for t in state['tasks']:
            if t['recurrence']:
                continue
            deadline = state_api.stamp(t['deadline'], zone).astimezone(UTC) if t['deadline'] else end
            item = (t['id'], t, t['remaining_minutes'], start, min(deadline, end))
            if deadline > end:
                deferred.append({'id': t['id'], 'remaining_minutes': t['remaining_minutes'],
                                 'reason': 'deadline extends beyond this horizon; later capacity is unknown'})
            else:
                requirements.append(item)
        for o in state['occurrences']:
            a = datetime.combine(date.fromisoformat(o['period_start']), time(), zone).astimezone(UTC)
            b = datetime.combine(date.fromisoformat(o['period_end']), time(), zone).astimezone(UTC)
            if b <= start or end <= a:
                continue
            if b > end:
                deferred.append({'id': o['id'], 'remaining_minutes': o['remaining_minutes'],
                                 'reason': 'full recurrence period extends beyond view; quota is not compressed'})
            else:
                requirements.append((o['id'], task_map[o['task_id']], o['remaining_minutes'], max(start,a), min(end,b)))
        tasks = {}
        required = 0
        unknown_required = False
        unresolved = []
        occurrence_ids = {o['id'] for o in state['occurrences']}
        for task in state['tasks']:
            recurrence = task['recurrence']
            if not task['required'] or recurrence is None:
                continue
            day = max(start_day, start.astimezone(zone).date())
            while day < end_day:
                ps, pe = state_api.period(day, recurrence['frequency'], state['profile']['week_start'])
                for n in range(1, recurrence['count']+1):
                    oid = task['id']+'@'+recurrence['frequency']+':'+ps.isoformat()+'#'+str(n)
                    if oid not in occurrence_ids:
                        unresolved.append({'task_id':task['id'],'occurrence_id':oid,'reason':'required occurrence inventory missing; remaining effort unknown'})
                        unknown_required = True
                day = pe
        known_shortfall = False
        for key, task, remaining, a, b in requirements:
            eligible = [(x,y) for x,y in clip(free, a, max(a,b))
                        if (y-x).total_seconds()/60 >= task['min_session_minutes']]
            upper = minutes(eligible)
            # An aggregate buffer can lie outside this task's deadline window.
            # Cap by the shared usable budget instead of reserving a percentage twice.
            upper = min(upper, usable)
            if upper < task['min_session_minutes']:
                upper = 0
            shortfall = None if remaining is None else max(0, remaining-upper)
            tasks[key] = {'remaining_minutes': remaining, 'eligible_upper_bound_minutes': number(upper),
                          'shortfall_lower_bound_minutes': None if shortfall is None else number(shortfall),
                          'minimum_session_minutes': task['min_session_minutes'],
                          'dependency_readiness': checked.get('dependency_readiness', {}).get(task['id'], 'not-applicable')}
            if task['required']:
                if remaining is None:
                    unknown_required = True
                else:
                    required += remaining
                    if shortfall:
                        known_shortfall = True
        shortfall = None if unknown_required else max(0, required-usable)
        result.update(required_minutes=None if unknown_required else number(required),
                      shortfall_minutes=None if shortfall is None else number(shortfall),
                      tasks=tasks, deferred_requirements=deferred, unresolved_requirements=unresolved)
        if unknown_required:
            warnings.append('required effort unknown; numerical shortfall cannot be certified')
        if deferred:
            warnings.append('some requirements extend beyond this view; do not infer their full-period feasibility')
        if not checked['valid']:
            result['feasibility'] = 'constraints-invalid'
        elif (shortfall is not None and shortfall > 0) or known_shortfall or allocated > usable:
            result['feasibility'] = 'overloaded'
        warnings.append('capacity is an aggregate bound; task capacities share time and do not prove joint placement or readiness')
        return result
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        return {'valid': False, 'errors': sorted(set(errors+[str(exc)])),
                'warnings': warnings, 'feasibility': 'not-proven'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('state')
    parser.add_argument('--as-of')
    args = parser.parse_args()
    try:
        result = capacity(state_api.load(args.state), args.as_of)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        result = {'valid': False, 'errors': [str(exc)], 'feasibility': 'not-proven'}
    print(json.dumps(result, indent=2))
    return 0 if result['valid'] else 2


if __name__ == '__main__':
    sys.exit(main())
