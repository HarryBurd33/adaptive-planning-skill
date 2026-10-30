#!/usr/bin/env python3
"""Export a validated proposed plan locally; never writes state or contacts calendars.

Python 3.9+ stdlib. Both formats contain only planned blocks ending after --as-of.
ICS timestamps have RFC 5545 second precision; Markdown retains ISO precision.
Existing outputs are accepted only when regular, non-symlink and byte-identical.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from zoneinfo import ZoneInfo

import planning_state


def text(value):
    """RFC 5545 TEXT escaping, before physical-line folding."""
    value = str(value).replace('\r\n', '\n').replace('\r', '\n')
    if any(ord(c) < 32 and c not in '\n\t' for c in value) or '\x7f' in value:
        raise ValueError('calendar text contains unsupported control characters')
    return value.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')


def fold(line):
    """Count UTF-8 octets including continuation space; never split a code point."""
    parts = []
    current = ''
    size = 0
    for char in line:
        width = len(char.encode('utf-8'))
        if size + width > 75:
            parts.append(current)
            current, size = ' ', 1
        current += char
        size += width
    parts.append(current)
    return '\r\n'.join(parts)


def utc(value):
    return planning_state.stamp(value).astimezone(planning_state.UTC)


def calendar_stamp(value):
    return utc(value).strftime('%Y%m%dT%H%M%SZ')


def uid(plan_id, block_id):
    identity = json.dumps([plan_id, block_id], ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(identity.encode('utf-8')).hexdigest() + '@adaptive-planning.local'


def selected_blocks(state, as_of):
    return sorted((b for b in state['dated_plan']['blocks']
                   if b['status'] == 'planned' and utc(b['end']) > as_of),
                  key=lambda b: (utc(b['start']), utc(b['end']), b['id']))


def ics(state, blocks):
    tasks = {t['id']: t for t in state['tasks']}
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Adaptive Planning//Portable Plan Export//EN', 'CALSCALE:GREGORIAN']
    for block in blocks:
        description = ('Proposed plan; not a confirmed appointment.\nTask ID: ' + block['task_id'] +
                       '\nOccurrence ID: ' + (block['occurrence_id'] if block['occurrence_id'] is not None else '(none)') +
                       '\nBlock ID: ' + block['id'])
        lines.extend(['BEGIN:VEVENT', 'UID:' + uid(state['plan_id'], block['id']),
                      'DTSTAMP:' + calendar_stamp(state['updated_at']),
                      'DTSTART:' + calendar_stamp(block['start']), 'DTEND:' + calendar_stamp(block['end']),
                      'SUMMARY:' + text(tasks[block['task_id']]['title']),
                      'SEQUENCE:' + str(state['revision']), 'DESCRIPTION:' + text(description), 'END:VEVENT'])
    lines.append('END:VCALENDAR')
    return ('\r\n'.join(fold(line) for line in lines) + '\r\n').encode('utf-8')


def cell(value):
    """Entity-encode punctuation so Markdown/Obsidian cannot interpret user markup."""
    value = str(value).replace('\r\n', '\n').replace('\r', '\n').replace('\n', ' ↵ ')
    return ''.join(c if c.isalnum() or c == ' ' or ord(c) > 127 else '&#' + str(ord(c)) + ';'
                   for c in value if ord(c) >= 32 or c == '\t').replace('\t', ' ')


def number(value):
    if value is None:
        return 'unknown'
    return format(value, '.12g')


def markdown(state, blocks, result, as_of):
    tasks = {t['id']: t for t in state['tasks']}
    zone = ZoneInfo(state['profile']['timezone'])
    lines = ['# Proposed plan', '', 'Local planning view; not a feasibility certificate or confirmed calendar.', '',
             'Plan: ' + cell(state['plan_id']), 'Timezone: ' + cell(state['profile']['timezone']),
             'Revision: ' + str(state['revision']), 'As of: ' + cell(as_of.isoformat()), '',
             '| Date | Time | ID | Activity |', '| --- | --- | --- | --- |']
    for block in blocks:
        a, b = utc(block['start']).astimezone(zone), utc(block['end']).astimezone(zone)
        identity = block['id'] + ' / task: ' + block['task_id']
        if block['occurrence_id'] is not None:
            identity += ' / occurrence: ' + block['occurrence_id']
        lines.append('| ' + ' | '.join(map(cell, [a.date().isoformat(),
                     a.isoformat().split('T', 1)[1] + ' – ' + b.isoformat(), identity, tasks[block['task_id']]['title']])) + ' |')
    lines.extend(['', '## Remaining work', '',
                  'Minutes below use remaining effort and future allocation as of the timestamp above.', '',
                  '| ID | Known remaining minutes | Future planned minutes | Unmet minutes |',
                  '| --- | --- | --- | --- |'])
    for key, total in sorted(result['totals'].items()):
        lines.append('| ' + ' | '.join([cell(key), number(total['remaining_minutes']),
                     number(total['scheduled_minutes']), number(total['unallocated_minutes'])]) + ' |')
    lines.extend(['', '## Unscheduled', ''])
    for item in sorted(state['dated_plan']['unscheduled'], key=lambda x: (x['task_id'], x['occurrence_id'] or '', x['reason'])):
        lines.append('- ' + cell(item['occurrence_id'] or item['task_id']) + ': ' + number(item['minutes']) + ' minutes; ' + cell(item['reason']))
    if not state['dated_plan']['unscheduled']:
        lines.append('None recorded.')
    lines.extend(['', '## Warnings', ''])
    lines.extend('- ' + cell(warning) for warning in result['warnings'])
    if not result['warnings']:
        lines.append('None from state validation; feasibility is still not certified.')
    return ('\n'.join(lines) + '\n').encode('utf-8')


def render(state, format_name, as_of):
    as_of = utc(as_of)  # Explicit offset required, including for empty plans.
    result = planning_state.check(state, as_of)
    if not result['valid']:
        raise ValueError('invalid state: ' + '; '.join(result['errors']))
    blocks = selected_blocks(state, as_of)
    if format_name == 'ics':
        return ics(state, blocks)
    if format_name == 'markdown':
        return markdown(state, blocks, result, as_of)
    raise ValueError('unknown export format')


def write_output(source_path, output_path, content):
    """Exclusive creation; no replacement, including aliases of the source state."""
    source, output = Path(source_path), Path(output_path)
    if output.is_symlink():
        raise ValueError('refuse symbolic-link output')
    if source.resolve() == output.resolve() or (output.exists() and os.path.samefile(source, output)):
        raise ValueError('refuse output at source state path')
    try:
        fd = os.open(str(output), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        # O_NOFOLLOW also closes the symlink check/open race on supported hosts.
        fd = os.open(str(output), os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
        with os.fdopen(fd, 'rb') as existing:
            info = os.fstat(existing.fileno())
            source_info = source.stat()
            if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino) == (source_info.st_dev, source_info.st_ino):
                raise ValueError('refuse nonregular or source-state output')
            if existing.read() != content:
                raise ValueError('existing output differs; choose a new path')
        return
    with os.fdopen(fd, 'wb') as target:
        target.write(content)
        target.flush()
        os.fsync(target.fileno())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('state')
    parser.add_argument('--format', choices=['ics', 'markdown'], required=True)
    parser.add_argument('--as-of', required=True, metavar='AWARE_TIMESTAMP')
    parser.add_argument('--output')
    args = parser.parse_args(argv)
    try:
        content = render(planning_state.load(args.state), args.format, args.as_of)
        if args.output is None:
            sys.stdout.buffer.write(content)
        else:
            write_output(args.state, args.output, content)
        return 0
    except (ValueError, TypeError, KeyError, AttributeError, OSError, RecursionError) as error:
        print('export error: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
