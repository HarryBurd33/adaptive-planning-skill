"""Frozen upgrade acceptance regressions, independent of implementation helpers."""
import copy
import importlib.util
import unittest
import test_state
from datetime import date
ROOT=test_state.ROOT

spec=importlib.util.spec_from_file_location('planning_state', ROOT/'scripts/planning_state.py')
ps=importlib.util.module_from_spec(spec);spec.loader.exec_module(ps)

class UpgradeTests(unittest.TestCase):
    setUp = test_state.StateTests.setUp
    tearDown = test_state.StateTests.tearDown
    task = test_state.StateTests.task
    block = test_state.StateTests.block
    write = test_state.StateTests.write
    runcli = test_state.StateTests.runcli
    check = test_state.StateTests.check
    def test_model_overlap_regression(self):
        self.s['model_week']=[{'weekday':0,'start':'08:30','end':'09:30','task_id':None,'label':'one'},{'weekday':0,'start':'09:00','end':'10:00','task_id':None,'label':'two'}]
        self.assertFalse(ps.check(self.s)['valid'])
    def test_partial_dependency_regression(self):
        self.s['tasks']=[self.task('a',120),self.task('b',60)];self.s['tasks'][1]['dependencies']=['a']
        self.s['dated_plan']['blocks']=[self.block('a1','a'),self.block('b1','b','2026-11-02T10:00:00-07:00','2026-11-02T11:00:00-07:00')]
        self.assertFalse(ps.check(self.s)['valid'])

    def model(self, weekday, start, end):
        return {'weekday':weekday,'start':start,'end':end,'task_id':None,'label':'window'}
    def test_week_wrap_and_touch(self):
        self.s['model_week']=[self.model(6,'23:30','01:00'),self.model(0,'00:30','01:30')]
        self.assertFalse(ps.check(self.s)['valid'])
        self.s['model_week'][1]=self.model(0,'01:00','01:30')
        self.assertTrue(ps.check(self.s)['valid'])
    def dependency(self, remaining):
        self.s['tasks']=[self.task('a',remaining),self.task('b',60)];self.s['tasks'][1]['dependencies']=['a']
        self.s['dated_plan']['blocks']=[self.block('b1','b','2026-11-02T10:00:00-07:00','2026-11-02T11:00:00-07:00')]
    def test_dependency_full_zero_and_unknown(self):
        self.dependency(60);self.s['dated_plan']['blocks'].insert(0,self.block('a1','a'))
        self.assertEqual(ps.check(self.s)['dependency_readiness']['b'],'ready')
        self.dependency(0);self.assertEqual(ps.check(self.s)['dependency_readiness']['b'],'ready')
        self.dependency(None);r=ps.check(self.s)
        self.assertTrue(r['valid']);self.assertEqual(r['dependency_readiness']['b'],'unknown')
    def exception(self):
        self.s['schema_version']=2
        self.s['extensions']['constraints_v2']={'sleep_exceptions':{'2026-11-02':[{'start':'2026-11-02T23:00:00-07:00','end':'2026-11-03T06:00:00-07:00'}]}}
    def test_sleep_anchor_next_night(self):
        self.exception();self.s['tasks']=[self.task()]
        self.s['dated_plan']['blocks']=[self.block(start='2026-11-03T06:30:00-07:00',end='2026-11-03T07:30:00-07:00')]
        self.assertTrue(ps.check(self.s)['valid'])
        self.s['dated_plan']['blocks']=[self.block(start='2026-11-04T06:30:00-07:00',end='2026-11-04T07:30:00-07:00')]
        self.assertFalse(ps.check(self.s)['valid'])
    def test_sleep_multiple_and_dst(self):
        self.s['schema_version']=2;self.s['extensions']['constraints_v2']={'sleep_exceptions':{'2026-11-01':[{'start':'2026-11-01T01:15:00-06:00','end':'2026-11-01T01:45:00-07:00'},{'start':'2026-11-01T23:00:00-07:00','end':'2026-11-02T07:00:00-07:00'}]}}
        windows=ps.sleep_intervals(self.s,date(2026,11,1),date(2026,11,2))
        self.assertEqual(len(windows),2);self.assertEqual((windows[0][1]-windows[0][0]).total_seconds()/60,90)
    def test_invalid_exceptions(self):
        self.exception();c=self.s['extensions']['constraints_v2']
        for windows in ([],[{'start':'2026-11-03T23:00:00-07:00','end':'2026-11-04T06:00:00-07:00'}],[{'start':'2026-11-02T23:00:00-06:00','end':'2026-11-03T06:00:00-07:00'}]):
            c['sleep_exceptions']['2026-11-02']=windows
            self.assertFalse(ps.check(self.s)['valid'])
    def test_schema_v2_gate_number_and_time(self):
        self.s['extensions']['constraints_v2']={'availability':[],'buffer_percent':20.5}
        self.assertFalse(ps.check(self.s)['valid']);self.s['schema_version']=2
        self.assertTrue(ps.check(self.s)['valid'])
        for x in (-1,101,float('nan'),float('inf'),True):
            self.s['extensions']['constraints_v2']['buffer_percent']=x
            self.assertFalse(ps.check(self.s)['valid'])
        self.s['extensions']['constraints_v2']['buffer_percent']=20
        self.s['profile']['sleep']['start']='24:61'
        self.assertFalse(ps.check(self.s)['valid'])
    def commit_pair(self, proposal, as_of=None, update='upgrade'):
        cur=self.write('cur.json',self.s);pro=self.write('pro.json',proposal)
        return cur, pro, ps.commit(cur,pro,0,update,as_of=as_of)
    def test_lossless_upgrade_and_downgrade(self):
        self.s['tasks']=[self.task(remaining=0)];self.s['dated_plan']['blocks']=[self.block(status='completed')]
        self.s['extensions']={'opaque':{'keep':[1,2]}}
        pro=copy.deepcopy(self.s);pro['schema_version']=2
        cur,_,_=self.commit_pair(pro)
        saved=ps.load(cur)
        for key in ('tasks','dated_plan','extensions','progress'):self.assertEqual(saved[key],self.s[key])
        pro=copy.deepcopy(saved);pro['schema_version']=1;path=self.write('down.json',pro)
        with self.assertRaisesRegex(ValueError,'downgrade'):ps.commit(cur,path,1,'down')
    def test_asof_future_totals_unknown_history(self):
        self.s['tasks']=[self.task(remaining=None)];self.s['dated_plan']['blocks']=[self.block()]
        out=ps.check(self.s,'2026-11-02T09:30:00-07:00')
        self.assertTrue(out['valid']);self.assertEqual(out['totals']['paper']['scheduled_minutes'],30)
        self.assertIsNone(out['totals']['paper']['remaining_minutes'])
        self.assertEqual(self.s['dated_plan']['blocks'][0]['start'],'2026-11-02T09:00:00-07:00')
    def test_asof_elapsed_immutable_future_split_allowed(self):
        self.s['tasks']=[self.task(remaining=60)];self.s['dated_plan']['blocks']=[self.block()]
        pro=copy.deepcopy(self.s);pro['dated_plan']['blocks'][0]=self.block(start='2026-11-02T10:00:00-07:00',end='2026-11-02T11:00:00-07:00')
        with self.assertRaisesRegex(ValueError,'elapsed'):self.commit_pair(pro,'2026-11-02T09:30:00-07:00')
        pro=copy.deepcopy(self.s);pro['dated_plan']['blocks'][0]['end']='2026-11-02T09:30:00-07:00'
        pro['dated_plan']['blocks'].append(self.block('future',start='2026-11-02T11:00:00-07:00',end='2026-11-02T12:00:00-07:00'))
        _,_,r=self.commit_pair(pro,'2026-11-02T09:30:00-07:00');self.assertTrue(r['committed'])
    def test_asof_ended_timing_immutable(self):
        self.s['tasks']=[self.task(remaining=60)];self.s['dated_plan']['blocks']=[self.block()]
        pro=copy.deepcopy(self.s);pro['dated_plan']['blocks'][0]['end']='2026-11-02T10:30:00-07:00'
        with self.assertRaisesRegex(ValueError,'elapsed'):self.commit_pair(pro,'2026-11-02T11:00:00-07:00')
    def test_asof_idempotency_contract_and_oldhash(self):
        cur,pro,_=self.commit_pair(copy.deepcopy(self.s),'2026-11-02T09:30:00-07:00')
        self.assertTrue(ps.commit(cur,pro,0,'upgrade',as_of='2026-11-02T09:30:00-07:00')['duplicate'])
        with self.assertRaisesRegex(ValueError,'conflicts'):ps.commit(cur,pro,0,'upgrade',as_of='2026-11-02T09:31:00-07:00')
        cur,pro,_=self.commit_pair(copy.deepcopy(self.s),update='old')
        self.assertEqual(ps.load(cur)['applied_updates'][-1]['sha256'],ps.digest({'proposal':self.s,'replace_extensions':[]}))
        self.assertTrue(ps.commit(cur,pro,0,'old')['duplicate'])
    def test_unknown_occurrence_distinct_zero(self):
        self.s['tasks']=[self.task('read',None,{'frequency':'weekly','count':1,'minutes':60})]
        oid='read@weekly:2026-11-02#1';self.s['occurrences']=[{'id':oid,'task_id':'read','period_start':'2026-11-02','period_end':'2026-11-09','remaining_minutes':None}]
        self.assertIsNone(ps.check(self.s)['totals'][oid]['unallocated_minutes'])
        self.s['occurrences'][0]['remaining_minutes']=0
        self.assertEqual(ps.check(self.s)['totals'][oid]['unallocated_minutes'],0)

    def test_short_elapsed_prefix_preserved(self):
        self.s['tasks']=[self.task(remaining=60)];self.s['dated_plan']['blocks']=[self.block()]
        pro=copy.deepcopy(self.s);pro['dated_plan']['blocks'][0]['end']='2026-11-02T09:15:00-07:00'
        pro['dated_plan']['blocks'].append(self.block('future',start='2026-11-02T11:00:00-07:00',end='2026-11-02T12:00:00-07:00'))
        self.assertTrue(self.commit_pair(pro,'2026-11-02T09:15:00-07:00')[2]['committed'])
    def test_fixed_sleep_outside_horizon(self):
        self.s['fixed_events']=[{'id':'outside','title':'outside','kind':'fixed','start':'2026-11-10T23:00:00-07:00','end':'2026-11-11T00:00:00-07:00'}]
        self.assertTrue(any('protected sleep' in e for e in ps.check(self.s)['errors']))
    def test_long_exception_remains_protected(self):
        self.exception();self.s['profile']['sleep']=None
        self.s['extensions']['constraints_v2']['sleep_exceptions']['2026-11-02'][0]['end']='2026-11-05T06:00:00-07:00'
        self.s['tasks']=[self.task()];self.s['dated_plan']['blocks']=[self.block(start='2026-11-04T09:00:00-07:00',end='2026-11-04T10:00:00-07:00')]
        self.assertFalse(ps.check(self.s)['valid'])
    def test_cli_asof_and_naive_rejection(self):
        self.s['tasks']=[self.task()];self.s['dated_plan']['blocks']=[self.block()]
        path=self.write('cli.json',self.s)
        r=self.runcli('check',path,'--as-of','2026-11-02T09:30:00-07:00')
        self.assertEqual(r['totals']['paper']['scheduled_minutes'],30)
        self.runcli('check',path,'--as-of','2026-11-02T09:30:00',expected=2)

    def test_generic_reservation_layers_union_but_appointments_collide(self):
        first={'id':'p1','title':'protected','kind':'protected','start':'2026-11-02T10:00:00-07:00','end':'2026-11-02T12:00:00-07:00'}
        second={'id':'p2','title':'protected','kind':'protected','start':'2026-11-02T11:00:00-07:00','end':'2026-11-02T13:00:00-07:00'}
        self.s['fixed_events']=[first,second]
        self.assertTrue(ps.check(self.s)['valid'])
        for kind in ('protected','buffer','unavailable'):
            second['kind']=kind
            self.assertTrue(ps.check(self.s)['valid'])
        first['kind']='fixed';second['kind']='fixed'
        self.assertFalse(ps.check(self.s)['valid'])
        for kind in ('meal','break','transition'):
            first['kind']=kind;second['kind']='protected'
            self.assertFalse(ps.check(self.s)['valid'])
        first['kind']='protected';second['kind']='protected'
        self.s['tasks']=[self.task()]
        self.s['dated_plan']['blocks']=[self.block(start='2026-11-02T10:00:00-07:00',end='2026-11-02T11:00:00-07:00')]
        self.assertFalse(ps.check(self.s)['valid'])

    def test_dependency_readiness_transitive_unknown_and_known(self):
        self.s['tasks']=[self.task('a',None),self.task('b',60),self.task('c',60)]
        self.s['tasks'][1]['dependencies']=['a'];self.s['tasks'][2]['dependencies']=['b']
        self.s['dated_plan']['blocks']=[self.block('b1','b'),self.block('c1','c',start='2026-11-02T10:00:00-07:00',end='2026-11-02T11:00:00-07:00')]
        result=ps.check(self.s)
        self.assertEqual(result['dependency_readiness']['b'],'unknown')
        self.assertEqual(result['dependency_readiness']['c'],'unknown')
        self.s['tasks'][0]['remaining_minutes']=60
        self.s['dated_plan']['blocks'].insert(0,self.block('a1','a',start='2026-11-02T08:00:00-07:00',end='2026-11-02T09:00:00-07:00'))
        result=ps.check(self.s)
        self.assertTrue(result['valid']);self.assertEqual(result['dependency_readiness']['c'],'ready')
    def test_dependency_readiness_transitive_blocked(self):
        self.s['tasks']=[self.task('a',120),self.task('b',60),self.task('c',60)]
        self.s['tasks'][1]['dependencies']=['a'];self.s['tasks'][2]['dependencies']=['b']
        self.s['dated_plan']['blocks']=[self.block('a1','a',start='2026-11-02T08:00:00-07:00',end='2026-11-02T09:00:00-07:00'),self.block('b1','b'),self.block('c1','c',start='2026-11-02T10:00:00-07:00',end='2026-11-02T11:00:00-07:00')]
        self.assertEqual(ps.check(self.s)['dependency_readiness']['c'],'blocked')

if __name__=='__main__':unittest.main()
