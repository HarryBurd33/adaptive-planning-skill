"""Frozen deterministic contract cases; invokes the shipped CLI in fresh processes."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/planning_state.py'

class StateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name)
        self.s=json.loads((ROOT/'templates/state.json').read_text())
    def tearDown(self):self.tmp.cleanup()
    def task(self,id='paper',remaining=60,recurrence=None):
        return {'id':id,'title':id,'remaining_minutes':remaining,'deadline':None,'preferred_date':None,'priority':'high','required':True,'flexible':True,'dependencies':[],'min_session_minutes':25,'recurrence':recurrence}
    def block(self,id='b1',task='paper',start='2026-11-02T09:00:00-07:00',end='2026-11-02T10:00:00-07:00',occ=None,status='planned'):
        return {'id':id,'task_id':task,'occurrence_id':occ,'start':start,'end':end,'status':status}
    def write(self,name,data):
        p=self.d/name;p.write_text(json.dumps(data));return p
    def runcli(self,*args,expected=0):
        r=subprocess.run([sys.executable,str(SCRIPT),*map(str,args)],text=True,capture_output=True)
        self.assertEqual(r.returncode,expected,r.stdout+r.stderr);return json.loads(r.stdout)
    def check(self,expected=0):return self.runcli('check',self.write('state.json',self.s),expected=expected)
    def test_valid_effort(self):
        self.s['tasks']=[self.task()];self.s['dated_plan']['blocks']=[self.block()]
        self.assertEqual(self.check()['totals']['paper']['unallocated_minutes'],0)
    def test_unknown_distinct_zero(self):
        self.s['tasks']=[self.task('unknown',None),self.task('done',0)]
        out=self.check();self.assertIsNone(out['totals']['unknown']['unallocated_minutes']);self.assertEqual(out['totals']['done']['unallocated_minutes'],0)
        self.assertTrue(any('unknown' in x for x in out['warnings']))
    def test_overlap(self):
        self.s['tasks']=[self.task()];self.s['dated_plan']['blocks']=[self.block()]
        self.s['fixed_events']=[{'id':'meeting','title':'meeting','kind':'fixed','start':'2026-11-02T09:30:00-07:00','end':'2026-11-02T11:00:00-07:00'}]
        self.assertTrue(any('overlaps' in x for x in self.check(2)['errors']))
    def test_fixed_conflicts_and_overnight_sleep(self):
        self.s['fixed_events']=[{'id':'a','title':'a','kind':'fixed','start':'2026-11-02T23:30:00-07:00','end':'2026-11-03T00:30:00-07:00'},{'id':'b','title':'b','kind':'fixed','start':'2026-11-03T00:00:00-07:00','end':'2026-11-03T01:00:00-07:00'}]
        out=self.check(2);self.assertTrue(any('sleep' in x for x in out['errors']));self.assertTrue(any('overlaps b' in x for x in out['errors']))
    def test_deadline_and_session(self):
        self.s['tasks']=[self.task()];self.s['tasks'][0]['deadline']='2026-11-02T09:15:00-07:00'
        self.s['dated_plan']['blocks']=[self.block(end='2026-11-02T09:20:00-07:00')]
        out=self.check(2);self.assertTrue(any('deadline' in x for x in out['errors']));self.assertTrue(any('minimum' in x for x in out['errors']))
    def test_dependency_order(self):
        self.s['tasks']=[self.task('research'),self.task('draft')];self.s['tasks'][1]['dependencies']=['research']
        self.s['dated_plan']['blocks']=[self.block(task='draft'),self.block('b2','research','2026-11-02T10:00:00-07:00','2026-11-02T11:00:00-07:00')]
        self.assertTrue(any('dependency' in x for x in self.check(2)['errors']))
    def test_overload_unallocated_not_fabricated(self):
        self.s['tasks']=[self.task(remaining=480)];self.s['dated_plan']['blocks']=[self.block(end='2026-11-02T13:00:00-07:00')]
        out=self.check();self.assertEqual(out['totals']['paper']['unallocated_minutes'],240);self.assertTrue(out['warnings'])
    def test_week_crosses_month(self):
        self.s['dated_plan'].update(start='2026-10-26',end='2026-11-02')
        self.s['tasks']=[self.task('lift',None,{'frequency':'weekly','count':1,'minutes':60})]
        oid='lift@weekly:2026-10-26#1';self.s['occurrences']=[{'id':oid,'task_id':'lift','period_start':'2026-10-26','period_end':'2026-11-02','remaining_minutes':60}]
        self.s['dated_plan']['blocks']=[self.block(task='lift',start='2026-11-01T10:00:00-07:00',end='2026-11-01T11:00:00-07:00',occ=oid)]
        self.assertEqual(self.check()['totals'][oid]['unallocated_minutes'],0)
    def test_missing_recurrence_visible(self):
        self.s['tasks']=[self.task('read',None,{'frequency':'daily','count':1,'minutes':30})]
        out=self.check();self.assertEqual(len([x for x in out['warnings'] if 'occurrence missing' in x]),7)
    def test_dst_repeated_hour_real_elapsed_minutes(self):
        self.s['profile']['sleep']=None;self.s['dated_plan'].update(start='2026-11-01',end='2026-11-02');self.s['tasks']=[self.task(remaining=90)]
        self.s['dated_plan']['blocks']=[self.block(start='2026-11-01T01:15:00-06:00',end='2026-11-01T01:45:00-07:00')]
        self.assertEqual(self.check()['totals']['paper']['scheduled_minutes'],90)
    def test_dst_nonexistent_time_rejected(self):
        self.s['profile']['sleep']=None;self.s['dated_plan'].update(start='2026-03-08',end='2026-03-09');self.s['tasks']=[self.task()]
        self.s['dated_plan']['blocks']=[self.block(start='2026-03-08T02:30:00-07:00',end='2026-03-08T04:30:00-06:00')]
        self.assertTrue(any('does not exist' in x for x in self.check(2)['errors']))
    def test_partial_commit_retry_and_conflicting_id(self):
        self.s['tasks']=[self.task(remaining=120)]
        cur=self.write('current.json',self.s);proposal=copy.deepcopy(self.s);proposal['tasks'][0]['remaining_minutes']=60
        proposal['progress']=[{'id':'progress-1','task_id':'paper','occurrence_id':None,'observed_at':'2026-11-02T10:00:00-07:00','remaining_minutes':60,'actual_minutes':60,'note':'Completed first hour'}]
        pro=self.write('proposal.json',proposal)
        self.assertEqual(self.runcli('commit',cur,pro,'--expected-revision',0,'--update-id','u1')['revision'],1)
        self.assertTrue(self.runcli('commit',cur,pro,'--expected-revision',0,'--update-id','u1')['duplicate'])
        self.assertEqual(json.loads(cur.read_text())['tasks'][0]['remaining_minutes'],60)
        proposal['tasks'][0]['remaining_minutes']=0;self.write('proposal.json',proposal)
        self.assertIn('conflicts',self.runcli('commit',cur,pro,'--expected-revision',0,'--update-id','u1',expected=2)['error'])
    def test_stale_revision_preserves_bytes(self):
        cur=self.write('current.json',self.s);pro=self.write('proposal.json',self.s);before=cur.read_bytes()
        self.runcli('commit',cur,pro,'--expected-revision',2,'--update-id','u2',expected=2);self.assertEqual(cur.read_bytes(),before)
    def test_extensions_and_history_preserved(self):
        self.s['extensions']={'unrelated':{'keep':True}};cur=self.write('current.json',self.s);proposal=copy.deepcopy(self.s);proposal['extensions']={};pro=self.write('proposal.json',proposal)
        self.assertIn('extensions',self.runcli('commit',cur,pro,'--expected-revision',0,'--update-id','u',expected=2)['error'])
    def test_existing_lock_blocks_and_is_retained(self):
        cur=self.write('current.json',self.s);pro=self.write('proposal.json',self.s);lock=self.d/'current.json.lock';lock.write_text('other-owner')
        self.runcli('commit',cur,pro,'--expected-revision',0,'--update-id','u',expected=2);self.assertEqual(lock.read_text(),'other-owner')
    def test_completed_block_immutable(self):
        self.s['tasks']=[self.task(remaining=0)];self.s['dated_plan']['blocks']=[self.block(status='completed')]
        cur=self.write('current.json',self.s);proposal=copy.deepcopy(self.s);proposal['dated_plan']['blocks']=[];pro=self.write('proposal.json',proposal)
        self.assertIn('completed',self.runcli('commit',cur,pro,'--expected-revision',0,'--update-id','u',expected=2)['error'])
    def test_model_week_not_modified_by_dated_commit(self):
        self.s['model_week']=[{'weekday':2,'start':'16:00','end':'17:00','task_id':None,'label':'normal exercise'}]
        cur=self.write('current.json',self.s);pro=self.write('proposal.json',self.s)
        self.runcli('commit',cur,pro,'--expected-revision',0,'--update-id','exam-week');self.assertEqual(json.loads(cur.read_text())['model_week'],self.s['model_week'])
    def test_unknown_existing_content_not_silently_dropped(self):
        current=copy.deepcopy(self.s);current['unrelated_note']='retain me';cur=self.write('current.json',current);pro=self.write('proposal.json',self.s);before=cur.read_bytes()
        self.assertIn('reconciliation',self.runcli('commit',cur,pro,'--expected-revision',0,'--update-id','u',expected=2)['error']);self.assertEqual(cur.read_bytes(),before)
    def test_existing_tasks_and_occurrences_cannot_be_deleted(self):
        self.s['tasks']=[self.task('paper',60),self.task('lift',None,{'frequency':'weekly','count':1,'minutes':60})]
        self.s['occurrences']=[{'id':'lift@weekly:2026-11-02#1','task_id':'lift','period_start':'2026-11-02','period_end':'2026-11-09','remaining_minutes':60}]
        for collection in ['tasks','occurrences']:
            cur=self.write('current.json',self.s);proposal=copy.deepcopy(self.s);proposal[collection]=[];pro=self.write('proposal.json',proposal);before=cur.read_bytes()
            self.assertIn('records deleted',self.runcli('commit',cur,pro,'--expected-revision',0,'--update-id','delete-'+collection,expected=2)['error']);self.assertEqual(cur.read_bytes(),before)
    def test_selected_extension_update_retry_and_flag_contract(self):
        self.s['extensions']={'capacity':{'minutes':120},'unrelated':{'keep':True}}
        cur=self.write('current.json',self.s);proposal=copy.deepcopy(self.s);proposal['extensions']['capacity']={'minutes':60};proposal['extensions']['assumptions']=['delay'];pro=self.write('proposal.json',proposal)
        args=['commit',cur,pro,'--expected-revision',0,'--update-id','capacity-change','--replace-extension','capacity','--replace-extension','assumptions']
        self.assertTrue(self.runcli(*args)['committed']);self.assertTrue(self.runcli(*args)['duplicate']);self.assertEqual(json.loads(cur.read_text())['extensions']['unrelated'],{'keep':True})
        self.assertIn('conflicts',self.runcli('commit',cur,pro,'--expected-revision',0,'--update-id','capacity-change','--replace-extension','capacity',expected=2)['error'])
    def test_selected_extension_cannot_delete_other_key(self):
        self.s['extensions']={'capacity':120,'unrelated':True};cur=self.write('current.json',self.s);proposal=copy.deepcopy(self.s);proposal['extensions']={'capacity':60};pro=self.write('proposal.json',proposal)
        self.assertIn('unrelated extensions',self.runcli('commit',cur,pro,'--expected-revision',0,'--update-id','bad','--replace-extension','capacity',expected=2)['error'])
    def test_progress_reference_and_reversal_reference_checked(self):
        self.s['progress']=[{'id':'p1','task_id':'missing','occurrence_id':None,'observed_at':'2026-11-02T10:00:00-07:00','remaining_minutes':0,'actual_minutes':60,'note':'reported'}]
        self.s['adaptations']=[{'id':'a1','observed_at':'2026-11-02T10:00:00-07:00','evidence_ids':['p1'],'before':{},'after':{},'reason':'feedback','reversible':True,'reverts':'missing'}]
        out=self.check(2);self.assertTrue(any('progress task' in x for x in out['errors']));self.assertTrue(any('reversal' in x for x in out['errors']))
    def test_progress_occurrence_must_match_task(self):
        self.s['tasks']=[self.task('read',None,{'frequency':'daily','count':1,'minutes':30})]
        self.s['progress']=[{'id':'p1','task_id':'read','occurrence_id':'missing','observed_at':'2026-11-02T10:00:00-07:00','remaining_minutes':0,'actual_minutes':30,'note':'reported'}]
        self.assertTrue(any('progress occurrence' in x for x in self.check(2)['errors']))
    def test_independent_invalid_model_week_regression(self):
        self.s['model_week']=[{'weekday':99,'start':'10:00','end':'11:00','task_id':'ghost','label':'invalid weekday'}]
        self.assertFalse(self.check(2)['valid'])
    def test_model_week_zero_and_six_valid_with_overnight(self):
        self.s['tasks']=[self.task('read',0)]
        self.s['model_week']=[{'weekday':0,'start':'10:00','end':'11:00','task_id':'read','label':'Monday reading'},{'weekday':6,'start':'22:00','end':'01:00','task_id':None,'label':'Sunday overnight routine'}]
        self.assertTrue(self.check()['valid'])
    def test_model_week_unknown_task_and_equal_endpoints_invalid(self):
        self.s['model_week']=[{'weekday':0,'start':'10:00','end':'11:00','task_id':'ghost','label':'invalid task'},{'weekday':6,'start':'10:00','end':'10:00','task_id':None,'label':'empty block'}]
        out=self.check(2);self.assertTrue(any('unknown task ghost' in x for x in out['errors']));self.assertTrue(any('equal start/end' in x for x in out['errors']))
    def test_profile_week_start_maximum_enforced(self):
        self.s['profile']['week_start']=7
        self.assertTrue(any('above maximum' in x for x in self.check(2)['errors']))
    def test_historical_occurrence_retained_without_current_habit_debt(self):
        self.s['tasks']=[self.task('reading',None,{'frequency':'daily','count':1,'minutes':30})]
        oid='reading@daily:2026-11-01#1'
        occurrence={'id':oid,'task_id':'reading','period_start':'2026-11-01','period_end':'2026-11-02','remaining_minutes':30}
        self.s['occurrences']=[occurrence]
        for n in range(2,9):
            self.s['occurrences'].append({'id':'reading@daily:2026-11-'+str(n).zfill(2)+'#1','task_id':'reading','period_start':'2026-11-'+str(n).zfill(2),'period_end':'2026-11-'+str(n+1).zfill(2),'remaining_minutes':0})
        out=self.check();self.assertNotIn(oid,out['totals']);self.assertEqual(out['outside_horizon'][oid],{'relation':'historical','remaining_minutes':30});self.assertFalse(any(oid in x for x in out['warnings']))
        self.assertIn(occurrence,self.s['occurrences'])
        cur=self.write('current.json',self.s);pro=self.write('proposal.json',self.s);self.runcli('commit',cur,pro,'--expected-revision',0,'--update-id','resume-week')
        self.assertIn(occurrence,json.loads(cur.read_text())['occurrences'])
    def test_future_occurrence_separate_and_nonrecurring_work_retained(self):
        self.s['tasks']=[self.task('paper',60),self.task('lift',None,{'frequency':'weekly','count':1,'minutes':60})]
        oid='lift@weekly:2026-11-09#1';self.s['occurrences']=[{'id':oid,'task_id':'lift','period_start':'2026-11-09','period_end':'2026-11-16','remaining_minutes':60}]
        out=self.check();self.assertEqual(out['outside_horizon'][oid]['relation'],'future');self.assertNotIn(oid,out['totals']);self.assertEqual(out['totals']['paper']['unallocated_minutes'],60)
    def test_schema_unknown_field_rejected(self):
        self.s['surprise']='unknown';self.assertTrue(any('unknown field' in x for x in self.check(2)['errors']))

if __name__=='__main__':unittest.main()
