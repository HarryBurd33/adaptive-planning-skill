"""Trial reporting regressions using synthetic data; no personal outcomes asserted."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from planning_trial import trial_report


def fixture():
    s = json.loads((ROOT/'templates/state.json').read_text())
    s['profile']['timezone'] = 'America/Denver'
    s['profile']['sleep'] = None
    s['dated_plan'].update(start='2026-11-02', end='2026-11-05')
    s['tasks'] = [{'id':'work','title':'Work','remaining_minutes':180,'deadline':None,'preferred_date':None,
                   'priority':'high','required':True,'flexible':True,'dependencies':[],
                   'min_session_minutes':30,'recurrence':None}]
    s['dated_plan']['blocks'] = [{'id':'w1','task_id':'work','occurrence_id':None,'start':'2026-11-02T10:00:00-07:00',
                                 'end':'2026-11-02T11:00:00-07:00','status':'planned'}]
    s['extensions']['trial'] = {'id':'synthetic-trial','start_date':'2026-11-02','end_date':'2026-11-05',
        'baseline_revision':s['revision'],'baseline_blocks':copy.deepcopy(s['dated_plan']['blocks']),'reviews':[]}
    return s


class TrialTests(unittest.TestCase):
    def test_missing_trial_does_not_invent_setup(self):
        s=fixture(); del s['extensions']['trial']
        r=trial_report(s,'2026-11-02T09:00:00-07:00')
        self.assertTrue(r['valid']); self.assertFalse(r['configured'])

    def test_not_started_and_missing_days_do_not_imply_failure(self):
        s=fixture(); before=copy.deepcopy(s)
        r=trial_report(s,'2026-10-30T13:00:00-06:00')
        self.assertEqual(r['phase'],'not-started'); self.assertEqual([d['status'] for d in r['days']],['future']*3)
        r=trial_report(s,'2026-11-05T12:00:00-07:00')
        self.assertEqual(r['phase'],'window-ended'); self.assertEqual([d['status'] for d in r['days']],['unreported']*3)
        self.assertEqual(r['progress_reports'],[]); self.assertEqual(s,before)

    def test_actual_null_zero_and_partial_samples_are_not_summed(self):
        s=fixture()
        for i,actual in enumerate([120,None,0]):
            s['progress'].append({'id':'p'+str(i),'task_id':'work','occurrence_id':None,
                'observed_at':'2026-11-0'+str(2+i)+'T15:00:00-07:00','remaining_minutes':180,'actual_minutes':actual,'note':'reported sample'})
        r=trial_report(s,'2026-11-04T16:00:00-07:00')
        self.assertTrue(r['valid'],r); self.assertEqual([p['actual_minutes'] for p in r['actual_duration_samples']],[120,None,0])
        self.assertNotIn('actual_minutes_total',r)

    def test_future_reports_excluded_and_local_dates_used(self):
        s=fixture();s['feedback']=[{'id':'f','observed_at':'2026-11-03T02:00:00+00:00','text':'Evening report'},
                                  {'id':'future','observed_at':'2026-11-04T15:00:00-07:00','text':'Future'}]
        r=trial_report(s,'2026-11-03T08:00:00-07:00')
        self.assertEqual([f['id'] for f in r['feedback']],['f'])
        self.assertEqual(r['days'][0]['feedback_ids'],['f']);self.assertEqual(r['days'][1]['status'],'awaiting-report')

    def test_same_id_move_and_review_are_evidence_not_inferred_cause(self):
        s=fixture();s['dated_plan']['blocks'][0]['start']='2026-11-02T11:00:00-07:00';s['dated_plan']['blocks'][0]['end']='2026-11-02T12:00:00-07:00'
        s['extensions']['trial']['reviews']=[{'id':'r1','observed_at':'2026-11-02T15:00:00-07:00','burden_minutes':0,'helped':False,'reason':None,'note':'Too much logging'}]
        r=trial_report(s,'2026-11-02T16:00:00-07:00')
        self.assertEqual(r['moved_blocks'][0]['id'],'w1');self.assertNotIn('reason',r['moved_blocks'][0])
        self.assertEqual(r['reviews'][0]['burden_minutes'],0);self.assertIs(r['reviews'][0]['helped'],False)
        self.assertEqual(r,trial_report(s,'2026-11-02T16:00:00-07:00'))

    def test_removed_baseline_is_not_called_missed(self):
        s=fixture();s['dated_plan']['blocks']=[]
        r=trial_report(s,'2026-11-05T10:00:00-07:00')
        self.assertEqual(r['baseline_block_ids_absent_now'],['w1']);self.assertNotIn('missed',r)

    def test_invalid_metadata_is_rejected(self):
        variants=[('baseline_revision',True),('baseline_revision',10),('baseline_blocks',{}),('end_date','2026-11-01'),('reviews',{})]
        for key,value in variants:
            s=fixture();s['extensions']['trial'][key]=value
            self.assertFalse(trial_report(s,'2026-11-02T08:00:00-07:00')['valid'],key)

    def test_bad_review_types_and_duplicate_ids_rejected(self):
        for value in [True,-1,float('nan')]:
            s=fixture();s['extensions']['trial']['reviews']=[{'id':'r','observed_at':'2026-11-02T15:00:00-07:00','burden_minutes':value}]
            self.assertFalse(trial_report(s,'2026-11-03T08:00:00-07:00')['valid'])
        s=fixture();review={'id':'r','observed_at':'2026-11-02T15:00:00-07:00'};s['extensions']['trial']['reviews']=[review,review]
        self.assertFalse(trial_report(s,'2026-11-03T08:00:00-07:00')['valid'])

    def test_bad_asof_or_invalid_state_rejected(self):
        self.assertFalse(trial_report(fixture(),'2026-11-02T08:00:00')['valid'])
        s=fixture();s['dated_plan']['blocks'][0]['end']='2026-11-02T09:00:00-07:00'
        self.assertFalse(trial_report(s,'2026-11-02T08:00:00-07:00')['valid'])

    def test_null_baseline_and_review_times_fail_cleanly(self):
        s=fixture();s['extensions']['trial']['baseline_blocks'][0]['start']=None
        self.assertFalse(trial_report(s,'2026-11-02T08:00:00-07:00')['valid'])
        s=fixture();s['extensions']['trial']['reviews']=[{'id':'r','observed_at':None}]
        self.assertFalse(trial_report(s,'2026-11-02T08:00:00-07:00')['valid'])

    def test_duplicate_baseline_ids_outside_window_rejected(self):
        s=fixture();early=copy.deepcopy(s['dated_plan']['blocks'][0])
        early.update(start='2026-11-01T10:00:00-07:00',end='2026-11-01T11:00:00-07:00')
        s['extensions']['trial']['baseline_blocks'].insert(0,early)
        self.assertFalse(trial_report(s,'2026-11-02T08:00:00-07:00')['valid'])

    def test_half_open_baseline_window_excludes_midnight_end(self):
        s=fixture();s['extensions']['trial']['baseline_blocks']=[{'id':'earlier','start':'2026-11-01T23:00:00-07:00','end':'2026-11-02T00:00:00-07:00'}]
        r=trial_report(s,'2026-11-02T08:00:00-07:00')
        self.assertEqual(r['baseline_block_ids_absent_now'],[])

    def test_equivalent_timestamp_spelling_is_not_a_move(self):
        s=fixture();s['extensions']['trial']['baseline_blocks'][0].update(start='2026-11-02T10:00-07:00',end='2026-11-02T11:00-07:00')
        self.assertEqual(trial_report(s,'2026-11-02T08:00:00-07:00')['moved_blocks'],[])

    def test_cli_never_changes_source(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';p.write_text(json.dumps(fixture()));before=p.read_bytes()
            r=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/planning_trial.py'),str(p),'--as-of','2026-11-02T08:00:00-07:00'],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(p.read_bytes(),before)


if __name__=='__main__':unittest.main()
