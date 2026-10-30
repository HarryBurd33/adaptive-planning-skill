"""Portable export behavior; synthetic data only, no calendar access."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/planning_export.py'
sys.path.insert(0, str(ROOT / 'scripts'))
import planning_export as export

AS_OF = '2026-11-02T07:00:00-07:00'


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.state = json.loads((ROOT / 'templates/state.json').read_text())
        self.state['tasks'] = [dict(id='work', title='Work', remaining_minutes=120,
            deadline=None, preferred_date=None, priority='high', required=True,
            flexible=True, dependencies=[], min_session_minutes=30, recurrence=None)]
        self.state['dated_plan']['blocks'] = [self.block('b1', '08:00', '09:00')]

    def block(self, identity, start, end, status='planned'):
        return dict(id=identity, task_id='work', occurrence_id=None, status=status,
                    start='2026-11-02T' + start + ':00-07:00',
                    end='2026-11-02T' + end + ':00-07:00')

    def render(self, kind='ics', as_of=AS_OF):
        return export.render(self.state, kind, as_of)

    def logical(self, content=None):
        value = (content or self.render()).decode('utf-8')
        return value.replace('\r\n ', '').split('\r\n')

    def property(self, name, content=None):
        return [line.split(':', 1)[1] for line in self.logical(content) if line.startswith(name + ':')]

    def test_required_calendar_properties_and_determinism(self):
        result = self.render()
        self.assertEqual(result, self.render())
        for key in ('UID', 'DTSTAMP', 'DTSTART', 'DTEND', 'SUMMARY', 'SEQUENCE'):
            self.assertEqual(len(self.property(key)), 1)
        self.assertEqual(self.property('DTSTAMP'), ['20261102T140000Z'])
        self.assertEqual(self.property('DTSTART'), ['20261102T150000Z'])
        self.assertEqual(self.property('SEQUENCE'), ['0'])
        for forbidden in ('METHOD:', 'ATTENDEE:', 'ORGANIZER:', 'VALARM'):
            self.assertNotIn(forbidden, result.decode())
        self.assertEqual(result.replace(b'\r\n', b'').count(b'\n'), 0)

    def test_uid_survives_move_revision_and_retry(self):
        identity = self.property('UID')
        self.state['dated_plan']['blocks'][0].update(start='2026-11-02T10:00:00-07:00', end='2026-11-02T11:00:00-07:00')
        self.state['revision'] = 3
        self.state['updated_at'] = '2026-11-02T08:00:00-07:00'
        self.assertEqual(identity, self.property('UID'))
        self.assertEqual(self.property('SEQUENCE'), ['3'])
        self.assertEqual(self.property('DTSTAMP'), ['20261102T150000Z'])
        self.assertEqual(self.render(), self.render())

    def test_uid_separates_plans_and_ambiguous_pairs(self):
        identity = self.property('UID')
        self.state['plan_id'] += '-other'
        self.assertNotEqual(identity, self.property('UID'))
        self.assertNotEqual(export.uid('a|b', 'c'), export.uid('a', 'b|c'))

    def test_unicode_folding_and_calendar_injection(self):
        title = ('日本語🌱' * 25) + '\\;,\r\nBEGIN:VALARM\nEND:VEVENT'
        self.state['tasks'][0]['title'] = title
        result = self.render()
        for line in result.split(b'\r\n'):
            self.assertLessEqual(len(line), 75)
            line.decode('utf-8')
        self.assertEqual(self.property('SUMMARY'), [export.text(title)])
        self.assertEqual(self.logical().count('BEGIN:VEVENT'), 1)
        self.assertNotIn('BEGIN:VALARM', self.logical())

    def test_control_characters_rejected(self):
        self.state['tasks'][0]['title'] = 'bad\x00title'
        with self.assertRaises(ValueError):
            self.render()

    def test_past_completed_and_fixed_events_excluded(self):
        self.state['dated_plan']['blocks'] += [self.block('done', '10:00', '11:00', 'completed'),
                                               self.block('old', '07:00', '08:00')]
        self.state['fixed_events'] = [dict(id='meeting', title='Meeting', kind='fixed',
            start='2026-11-02T12:00:00-07:00', end='2026-11-02T13:00:00-07:00')]
        self.assertEqual(self.property('UID', self.render(as_of='2026-11-02T08:00:00-07:00')),
                         [export.uid(self.state['plan_id'], 'b1')])

    def test_in_progress_original_start_retained(self):
        content = self.render(as_of='2026-11-02T08:30:00-07:00')
        self.assertEqual(self.property('DTSTART', content), ['20261102T150000Z'])
        self.assertEqual(self.property('DTEND', content), ['20261102T160000Z'])
        md = self.render('markdown', '2026-11-02T08:30:00-07:00').decode()
        self.assertIn('08&#58;00&#58;00&#45;07&#58;00', md)
        self.assertIn('| work | 120 | 30 | 90 |', md)

    def test_dst_repeated_hour_preserves_elapsed_time(self):
        self.state['profile']['sleep'] = None
        self.state['dated_plan'].update(start='2026-11-01', end='2026-11-02')
        self.state['dated_plan']['blocks'][0].update(start='2026-11-01T01:15:00-06:00', end='2026-11-01T01:45:00-07:00')
        content = self.render(as_of='2026-11-01T00:00:00-06:00')
        self.assertEqual(self.property('DTSTART', content), ['20261101T071500Z'])
        self.assertEqual(self.property('DTEND', content), ['20261101T084500Z'])
        md = self.render('markdown', '2026-11-01T00:00:00-06:00').decode()
        self.assertIn('| work | 120 | 90 | 30 |', md)

    def test_order_independent_of_input_order(self):
        self.state['dated_plan']['blocks'].append(self.block('b2', '10:00', '11:00'))
        before = self.render()
        self.state['dated_plan']['blocks'].reverse()
        self.assertEqual(before, self.render())

    def test_markdown_unknown_unmet_warnings_and_injection(self):
        nasty = '![[file]]|<script>\n# heading `code` & stuff'
        self.state['tasks'][0].update(id=nasty, title=nasty, remaining_minutes=None)
        self.state['dated_plan']['blocks'][0]['task_id'] = nasty
        self.state['dated_plan']['blocks'][0]['id'] = nasty
        content = self.render('markdown').decode()
        self.assertIn('| Date | Time | ID | Activity |', content)
        self.assertIn('| unknown | 60 | unknown |', content)
        self.assertIn('effort unknown', content)
        self.assertIn('Timezone: America&#47;Denver', content)
        self.assertIn('Revision: 0', content)
        self.assertIn('As of:', content)
        self.assertIn('not a feasibility certificate', content)
        self.assertNotIn('[[', content)
        self.assertNotIn('<script>', content)
        self.assertNotIn('\n# heading', content)
        self.assertIn('&#124;', content)
        for line in content.splitlines():
            if line.startswith('|'):
                self.assertEqual(line.count('|'), 5)

    def test_invalid_state_and_malformed_asof_fail(self):
        for as_of in ('2026-11-02T07:00:00', 'not a timestamp'):
            with self.assertRaises(ValueError):
                self.render(as_of=as_of)
        self.state['dated_plan']['blocks'][0]['task_id'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'invalid state'):
            self.render()

    def test_file_create_noop_conflict_symlink_and_source_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / 'state.json', Path(tmp) / 'plan.ics'
            source.write_text(json.dumps(self.state))
            before = source.read_bytes()
            content = self.render()
            export.write_output(source, output, content)
            original_stat = output.stat()
            export.write_output(source, output, content)
            self.assertEqual(original_stat.st_mtime_ns, output.stat().st_mtime_ns)
            self.assertEqual(content, output.read_bytes())
            with self.assertRaisesRegex(ValueError, 'differs'):
                export.write_output(source, output, b'different')
            link = Path(tmp) / 'link.ics'
            link.symlink_to(output)
            with self.assertRaises(ValueError):
                export.write_output(source, link, content)
            hard = Path(tmp) / 'hard.json'
            os.link(source, hard)
            for forbidden in (source, hard):
                with self.assertRaises(ValueError):
                    export.write_output(source, forbidden, before)
            self.assertEqual(before, source.read_bytes())
            self.assertEqual(content, output.read_bytes())

    def test_cli_stdout_output_and_error_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'state.json'
            source.write_text(json.dumps(self.state))
            before = source.read_bytes()
            args = [sys.executable, '-B', str(SCRIPT), str(source), '--format', 'ics', '--as-of', AS_OF]
            result = subprocess.run(args, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, self.render())
            output = Path(tmp) / 'plan.ics'
            result = subprocess.run(args + ['--output', str(output)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, b'')
            self.assertEqual(output.read_bytes(), self.render())
            result = subprocess.run(args + ['--output', str(source)], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, b'')
            self.assertEqual(source.read_bytes(), before)
            result = subprocess.run(args[:-1] + ['naive'], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, b'')

    def test_empty_export_is_valid_container(self):
        self.state['dated_plan']['blocks'] = []
        self.assertEqual(self.property('UID'), [])
        self.assertIn(b'END:VCALENDAR\r\n', self.render())


if __name__ == '__main__':
    unittest.main()
