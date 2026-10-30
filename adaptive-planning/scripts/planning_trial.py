#!/usr/bin/env python3
"""Read an optional private trial ledger without scoring or inferring missing progress."""
import argparse
from datetime import date, datetime, time, timedelta, timezone
import json
import math
import sys
from zoneinfo import ZoneInfo
import planning_state as state_api
from planning_capacity import canonical_views


def trial_report(state, as_of):
    try:
        checked = state_api.check(state, as_of=as_of)
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError) as exc:
        return {'valid': False, 'errors': [str(exc)], 'warnings': []}
    if not checked['valid']:
        return {'valid': False, 'errors': checked['errors'], 'warnings': checked['warnings']}
    try:
        cutoff = state_api.stamp(as_of).astimezone(timezone.utc)
        zone = ZoneInfo(state['profile']['timezone'])
        today = cutoff.astimezone(zone).date()
        trial = state['extensions'].get('trial')
        if trial is None:
            return {'valid': True, 'configured': False, 'errors': [], 'warnings': checked['warnings'],
                    'message': 'No trial metadata recorded; no trial results can be inferred.'}
        if not isinstance(trial, dict) or not isinstance(trial.get('id'), str) or not trial['id']:
            raise ValueError('trial must have a nonempty id')
        start, end = date.fromisoformat(trial['start_date']), date.fromisoformat(trial['end_date'])
        if start >= end or (end-start).days > 366:
            raise ValueError('trial range must be positive and at most 366 days')
        revision = trial['baseline_revision']
        if isinstance(revision, bool) or not isinstance(revision, int) or not 0 <= revision <= state['revision']:
            raise ValueError('trial baseline_revision must be a known nonfuture revision')
        baseline = trial['baseline_blocks']
        if not isinstance(baseline, list):
            raise ValueError('trial baseline_blocks must be an explicit list')
        old = {}
        seen_blocks = set()
        window_start = datetime.combine(start, time(), zone).astimezone(timezone.utc)
        window_end = datetime.combine(end, time(), zone).astimezone(timezone.utc)
        for block in baseline:
            if not isinstance(block, dict) or not isinstance(block.get('id'), str) or not block['id'] or block['id'] in seen_blocks:
                raise ValueError('trial baseline block ids must be nonempty and unique')
            seen_blocks.add(block['id'])
            a, b = state_api.stamp(block['start'], zone), state_api.stamp(block['end'], zone)
            if b.astimezone(timezone.utc) <= a.astimezone(timezone.utc):
                raise ValueError('trial baseline block end must follow start')
            if a.astimezone(timezone.utc) < window_end and window_start < b.astimezone(timezone.utc):
                old[block['id']] = block
        reviews = trial.get('reviews', [])
        if not isinstance(reviews, list):
            raise ValueError('trial reviews must be a list')
        seen = set()
        for review in reviews:
            if not isinstance(review, dict) or not isinstance(review.get('id'), str) or not review['id'] or review['id'] in seen:
                raise ValueError('trial review ids must be nonempty and unique')
            seen.add(review['id'])
            state_api.stamp(review['observed_at'])
            burden = review.get('burden_minutes')
            if burden is not None and (isinstance(burden, bool) or not isinstance(burden, (float, int)) or not math.isfinite(burden) or burden < 0):
                raise ValueError('review burden_minutes must be null or finite nonnegative minutes')
            if review.get('helped') is not None and not isinstance(review['helped'], bool):
                raise ValueError('review helped must be null or boolean')
            for key in ('reason', 'note'):
                if review.get(key) is not None and not isinstance(review[key], str):
                    raise ValueError('review '+key+' must be null or text')
        def in_window(item):
            instant = state_api.stamp(item['observed_at']).astimezone(timezone.utc)
            return instant <= cutoff and start <= instant.astimezone(zone).date() < end
        progress = [p for p in state['progress'] if in_window(p)]
        feedback = [f for f in state['feedback'] if in_window(f)]
        reviews = [r for r in reviews if in_window(r)]
        days = []
        day = start
        while day < end:
            def ids(items):
                return [i['id'] for i in items if state_api.stamp(i['observed_at']).astimezone(zone).date() == day]
            row = {'date': day.isoformat(), 'progress_ids': ids(progress), 'feedback_ids': ids(feedback), 'review_ids': ids(reviews)}
            reported = row['progress_ids'] or row['feedback_ids'] or row['review_ids']
            row['status'] = 'future' if today < day else ('reported' if reported else ('awaiting-report' if today == day else 'unreported'))
            days.append(row)
            day += timedelta(days=1)
        current = {b['id']: b for b in state['dated_plan']['blocks']}
        moves = [{'id': key, 'before': {'start': b['start'], 'end': b['end']},
                  'after': {'start': current[key]['start'], 'end': current[key]['end']}}
                 for key, b in old.items() if key in current and
                 any(state_api.stamp(b[k]).astimezone(timezone.utc) != state_api.stamp(current[key][k]).astimezone(timezone.utc) for k in ('start', 'end'))]
        views = canonical_views(state, as_of)
        future_minutes = sum(v['planned_minutes'] for d, v in views['day'].items() if start.isoformat() <= d < end.isoformat())
        return {'valid': True, 'configured': True, 'errors': [], 'warnings': checked['warnings'],
                'trial_id': trial['id'], 'state_revision': state['revision'], 'baseline_revision': revision,
                'timezone': state['profile']['timezone'], 'as_of': as_of,
                'start_date': start.isoformat(), 'end_date': end.isoformat(),
                'phase': 'not-started' if today < start else ('window-ended' if end <= today else 'in-progress'),
                'days': days, 'progress_reports': progress,
                'actual_duration_samples': [{'progress_id': p['id'], 'task_id': p['task_id'],
                    'occurrence_id': p['occurrence_id'], 'actual_minutes': p['actual_minutes'],
                    'remaining_minutes': p['remaining_minutes']} for p in progress],
                'feedback': feedback, 'reviews': reviews, 'moved_blocks': moves,
                'baseline_block_ids_absent_now': sorted(set(old)-set(current)),
                'future_planned_minutes': future_minutes,
                'interpretation': 'Observation dates are reporting dates, not inferred work dates. Missing reports stay unknown. Duration samples are not summed: they may describe overlapping scope. Moves do not establish their cause. Window-ended does not mean goals completed.'}
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError) as exc:
        return {'valid': False, 'errors': ['invalid trial: '+str(exc)], 'warnings': checked['warnings']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('state')
    parser.add_argument('--as-of', required=True)
    args = parser.parse_args()
    try:
        result = trial_report(state_api.load(args.state), args.as_of)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        result = {'valid': False, 'errors': [str(exc)]}
    print(json.dumps(result, indent=2))
    return 0 if result['valid'] else 2


if __name__ == '__main__':
    sys.exit(main())
