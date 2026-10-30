"""Capacity contracts use explicit synthetic windows; no scheduling solver assumed."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/planning_capacity.py'

class CapacityTests(unittest.TestCase):
    def setUp(self):
        self.s=json.loads((ROOT/'templates/state.json').read_text())
        self.s['schema_version']=2
        self.s['extensions']['constraints_v2']={}
    def interval(self,a,b):return {'start':'2026-11-02T'+a+':00-07:00','end':'2026-11-02T'+b+':00-07:00'}
    def task(self,remaining=480,minimum=30):
        return {'id':'work','title':'Work','remaining_minutes':remaining,'deadline':None,'preferred_date':None,'priority':'high','required':True,'flexible':True,'dependencies':[],'min_session_minutes':minimum,'recurrence':None}
    def runreport(self,expected=0,as_of=None):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'state.json';p.write_text(json.dumps(self.s))
            args=[sys.executable,'-B',str(SCRIPT),str(p)]
            if as_of:args += ['--as-of',as_of]
            r=subprocess.run(args,text=True,capture_output=True)
            self.assertEqual(r.returncode,expected,r.stdout+r.stderr)
            return json.loads(r.stdout)
    def config(self,**kwargs):self.s['extensions']['constraints_v2'].update(kwargs)
    def test_eight_hours_against_four_usable(self):
        self.s['tasks']=[self.task()];self.config(availability=[self.interval('08:00','13:00')],buffer_percent=20)
        out=self.runreport();self.assertEqual(out['usable_minutes'],240);self.assertEqual(out['shortfall_minutes'],240);self.assertEqual(out['feasibility'],'overloaded')
    def test_missing_and_empty_availability_differ(self):
        self.s['tasks']=[self.task(60)];out=self.runreport();self.assertFalse(out['availability_known']);self.assertIsNone(out['usable_minutes']);self.assertIsNone(out['shortfall_minutes'])
        self.config(availability=[]);out=self.runreport();self.assertTrue(out['availability_known']);self.assertEqual(out['usable_minutes'],0);self.assertEqual(out['shortfall_minutes'],60)
    def test_overlap_is_subtracted_once_and_constraints_disclosed(self):
        self.config(availability=[self.interval('08:00','12:00')],buffer_percent=0)
        self.s['fixed_events']=[dict(id='p1',title='protected',kind='protected',**self.interval('09:00','10:00')),dict(id='p2',title='protected',kind='protected',**self.interval('09:30','10:30'))]
        out=self.runreport();self.assertEqual(out['candidate_minutes'],150);self.assertEqual(out['feasibility'],'not-proven')
    def test_short_gaps_excluded(self):
        self.s['tasks']=[self.task(30)];self.config(availability=[self.interval('08:00','08:15'),self.interval('09:00','09:15')],buffer_percent=0)
        out=self.runreport();self.assertEqual(out['tasks']['work']['eligible_upper_bound_minutes'],0);self.assertEqual(out['tasks']['work']['shortfall_lower_bound_minutes'],30)
    def test_explicit_buffer_not_double_charged(self):
        self.config(availability=[self.interval('08:00','10:00')],buffer_percent=20)
        self.s['fixed_events']=[dict(id='reserve',title='buffer',kind='buffer',**self.interval('09:30','10:00'))]
        out=self.runreport();self.assertEqual(out['usable_minutes'],90);self.assertEqual(out['buffer_minutes'],30);self.assertEqual(out['buffer_method'],'explicit blocks')
    def test_unknown_effort_not_zero(self):
        self.s['tasks']=[self.task(None)];self.config(availability=[self.interval('08:00','10:00')],buffer_percent=0)
        out=self.runreport();self.assertIsNone(out['required_minutes']);self.assertIsNone(out['shortfall_minutes']);self.assertEqual(out['feasibility'],'not-proven')
    def test_zero_effort_retained(self):
        self.s['tasks']=[self.task(0)];self.config(availability=[]);out=self.runreport();self.assertEqual(out['required_minutes'],0);self.assertEqual(out['shortfall_minutes'],0)
    def test_deadline_specific_upper_bound(self):
        self.s['tasks']=[self.task(120)];self.s['tasks'][0]['deadline']='2026-11-02T09:00:00-07:00';self.config(availability=[self.interval('08:00','11:00')],buffer_percent=0)
        out=self.runreport();self.assertEqual(out['tasks']['work']['eligible_upper_bound_minutes'],60);self.assertEqual(out['tasks']['work']['shortfall_lower_bound_minutes'],60)
    def test_future_deadline_not_compressed_into_current_view(self):
        self.s['tasks']=[self.task(480)];self.s['tasks'][0]['deadline']='2026-11-20T17:00:00-07:00';self.config(availability=[])
        out=self.runreport();self.assertEqual(out['required_minutes'],0);self.assertEqual(out['deferred_requirements'][0]['id'],'work');self.assertEqual(out['feasibility'],'not-proven')
    def test_dst_views_conserve_elapsed_minutes(self):
        self.s['profile']['sleep']=None;self.s['dated_plan'].update(start='2026-11-01',end='2026-11-02');self.s['tasks']=[self.task(90)]
        self.s['dated_plan']['blocks']=[dict(id='repeat',task_id='work',occurrence_id=None,status='planned',start='2026-11-01T01:15:00-06:00',end='2026-11-01T01:45:00-07:00')]
        out=self.runreport()
        for scale in ['day','week','month']:self.assertEqual(sum(v['planned_minutes'] for v in out['views'][scale].values()),90)
    def test_weekly_occurrence_shared_between_month_views(self):
        self.s['dated_plan'].update(start='2026-10-26',end='2026-11-02');t=self.task(60);t.update(id='lift',recurrence={'frequency':'weekly','count':1,'minutes':60},remaining_minutes=None);self.s['tasks']=[t]
        oid='lift@weekly:2026-10-26#1';self.s['occurrences']=[dict(id=oid,task_id='lift',period_start='2026-10-26',period_end='2026-11-02',remaining_minutes=60)]
        self.s['dated_plan']['blocks']=[dict(id='oct',task_id='lift',occurrence_id=oid,status='planned',start='2026-10-31T12:00:00-06:00',end='2026-10-31T12:30:00-06:00'),dict(id='nov',task_id='lift',occurrence_id=oid,status='planned',start='2026-11-01T12:00:00-07:00',end='2026-11-01T12:30:00-07:00')]
        out=self.runreport();self.assertEqual(len(out['views']['week']),1);self.assertEqual(len(out['views']['month']),2)
        for v in out['views']['month'].values():self.assertEqual(v['occurrence_ids'],[oid])
    def test_asof_clips_available_and_planned_future(self):
        self.s['tasks']=[self.task(60)];self.config(availability=[self.interval('08:00','10:00')],buffer_percent=0)
        self.s['dated_plan']['blocks']=[dict(id='current',task_id='work',occurrence_id=None,status='planned',**self.interval('08:00','09:00'))]
        out=self.runreport(as_of='2026-11-02T08:30:00-07:00');self.assertEqual(out['usable_minutes'],90);self.assertEqual(out['allocated_minutes'],30)
    def test_legacy_state_without_v2_constraints_remains_readable(self):
        self.s['schema_version']=1;self.s['extensions']={};out=self.runreport();self.assertFalse(out['availability_known']);self.assertIsNone(out['usable_minutes'])
    def test_capacity_never_claims_joint_feasibility(self):
        self.s['tasks']=[self.task(60)];self.config(availability=[self.interval('08:00','10:00')],buffer_percent=0)
        self.assertEqual(self.runreport()['feasibility'],'not-proven')

    def test_long_prior_sleep_anchor_blocks_current_capacity(self):
        self.s['profile']['sleep']=None;self.s['dated_plan'].update(start='2026-11-04',end='2026-11-05')
        self.config(availability=[{'start':'2026-11-04T08:00:00-07:00','end':'2026-11-04T10:00:00-07:00'}],buffer_percent=0,sleep_exceptions={'2026-11-01':[{'start':'2026-11-01T23:00:00-07:00','end':'2026-11-04T12:00:00-07:00'}]})
        out=self.runreport();self.assertEqual(out['usable_minutes'],0)
    def test_aggregate_buffer_can_be_after_task_deadline(self):
        self.s['tasks']=[self.task(60)];self.s['tasks'][0]['deadline']='2026-11-02T09:00:00-07:00';self.config(availability=[self.interval('08:00','10:00')],buffer_percent=20)
        out=self.runreport();self.assertEqual(out['usable_minutes'],96);self.assertEqual(out['tasks']['work']['eligible_upper_bound_minutes'],60);self.assertEqual(out['feasibility'],'not-proven')
    def test_missing_required_occurrence_is_unknown_not_zero(self):
        task=self.task(None);task['recurrence']={'frequency':'weekly','count':1,'minutes':60};self.s['tasks']=[task];self.config(availability=[self.interval('08:00','10:00')],buffer_percent=20)
        out=self.runreport();self.assertIsNone(out['required_minutes']);self.assertIsNone(out['shortfall_minutes']);self.assertEqual(out['unresolved_requirements'][0]['occurrence_id'],'work@weekly:2026-11-02#1')

if __name__=='__main__':unittest.main()
