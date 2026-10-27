"""Independent arithmetic/whole-fixture checks, not a scheduling solver."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WholeExampleTests(unittest.TestCase):
    def test_initial_week_and_capacity(self):
        state = json.loads((ROOT / 'examples/initial-state.json').read_text())
        run = subprocess.run([sys.executable, str(ROOT/'scripts/planning_state.py'),
                              'check', str(ROOT/'examples/initial-state.json')],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        checked = json.loads(run.stdout)
        self.assertEqual(checked['errors'], [])
        self.assertEqual(checked['warnings'], [])
        totals = checked['totals']
        self.assertEqual(totals['paper']['scheduled_minutes'], 360)
        for prefix, count, minutes in [('lift@weekly:', 3, 180),
                                        ('reading@daily:', 7, 210),
                                        ('laundry@weekly:', 1, 120)]:
            matches = [v for k,v in totals.items() if k.startswith(prefix)]
            self.assertEqual(len(matches), count)
            self.assertEqual(sum(v['scheduled_minutes'] for v in matches), minutes)
        capacity = state['extensions']['capacity_minutes']
        self.assertEqual(capacity['candidate'], 7*16*60 - 9*60 - 7*150 - 180 - 7*90)
        self.assertEqual(capacity['buffer'], capacity['candidate']*.2)
        self.assertEqual(capacity['usable'], capacity['candidate']-capacity['buffer'])
        self.assertEqual(capacity['allocated'], 360+180+210+120)
        self.assertEqual(capacity['unallocated_usable'], capacity['usable']-capacity['allocated'])

    def test_saved_resume_state_does_not_double_count_completed_work(self):
        state = json.loads((ROOT/'examples/resume-state.json').read_text())
        paper = next(t for t in state['tasks'] if t['id']=='paper')
        self.assertEqual(paper['remaining_minutes'], 240)
        completed = [b for b in state['dated_plan']['blocks'] if b['status']=='completed']
        self.assertEqual([b['id'] for b in completed], ['P2'])
        self.assertEqual(state['progress'][0]['remaining_minutes'], 240)
        self.assertEqual(state['profile']['sleep']['end'], '07:00')
        self.assertEqual(len(state['model_week']), 7)
        self.assertEqual(state['adaptations'][0]['evidence_ids'], ['f-reading'])
        self.assertIn('Thursday',state['extensions']['exam_week_exception'])


if __name__ == '__main__':
    unittest.main()
