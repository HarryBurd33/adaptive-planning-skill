"""Independent dev-only RFC5545 parser round-trip on synthetic portable exports."""
import copy
from datetime import timezone
import json
from pathlib import Path
import sys
try:
    from icalendar import Calendar
except ImportError:
    raise SystemExit('Install requirements-dev.txt in a Python3.10+ development environment')
root=Path(__file__).resolve().parents[1]/'adaptive-planning'
sys.path.insert(0,str(root/'scripts'))
import planning_export as export
import planning_state
s=json.loads((root/'templates/state.json').read_text())
s['profile'].update(timezone='America/Denver',sleep=None)
s['dated_plan'].update(start='2026-11-01',end='2026-11-02')
title='Synthetic \\ ,;\nBEGIN:VEVENT\nATTENDEE:untrusted@example.test\n'+'読書😀'*40
s['tasks']=[{'id':'work','title':title,'remaining_minutes':60,'deadline':None,'preferred_date':None,'priority':'high','required':True,'flexible':True,'dependencies':[],'min_session_minutes':30,'recurrence':None}]
s['dated_plan']['blocks']=[{'id':'b1','task_id':'work','occurrence_id':None,'start':'2026-11-01T01:30:00-06:00','end':'2026-11-01T01:30:00-07:00','status':'planned'}]
before=copy.deepcopy(s)
payload=export.render(s,'ics','2026-11-01T00:00:00-06:00')
assert payload==export.render(s,'ics','2026-11-01T00:00:00-06:00') and s==before
assert payload.endswith(b'\r\n') and not payload.replace(b'\r\n',b'').count(b'\n')
assert all(len(line)<=75 for line in payload.split(b'\r\n'))
cal=Calendar.from_ical(payload);events=cal.walk('VEVENT');assert len(events)==1
assert not cal.errors and not events[0].errors and cal.get('METHOD') is None and not cal.walk('VALARM')
event=events[0];assert str(event['SUMMARY'])==title and event.get('ATTENDEE') is None and event.get('ORGANIZER') is None
assert (event.decoded('DTEND')-event.decoded('DTSTART')).total_seconds()==3600
identity=str(event['UID']);moved=copy.deepcopy(s);moved['revision']+=1
moved['dated_plan']['blocks'][0].update(start='2026-11-01T02:30:00-07:00',end='2026-11-01T03:30:00-07:00')
new=Calendar.from_ical(export.render(moved,'ics','2026-11-01T00:00:00-06:00')).walk('VEVENT')[0]
assert str(new['UID'])==identity and int(new['SEQUENCE'])==moved['revision']
assert new.decoded('DTSTART').astimezone(timezone.utc)==planning_state.stamp(moved['dated_plan']['blocks'][0]['start']).astimezone(timezone.utc)
assert Calendar.from_ical(export.render(s,'ics','2026-11-01T05:00:00-07:00')).walk('VEVENT')==[]
print(json.dumps({'independent_calendar_parser':True,'unicode_text_roundtrip':True,'utc_dst_duration_minutes':60,'stable_uid_on_move':True,'no_invites_alarms_or_injected_events':True,'expired_excluded':True}))
