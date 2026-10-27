"""Validate packaged file hashes, skill metadata and local documentation links."""
import hashlib
import json
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
skill = root / 'adaptive-planning'
errors = []
manifest = json.loads((skill / 'validation/manifest.json').read_text())
actual = {str(p.relative_to(skill)): p for p in skill.rglob('*')
          if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'
          and p != skill/'validation/manifest.json'}
if set(actual) != set(manifest['files']):
    errors.append('Manifest does not match package file inventory')
for name, expected in manifest['files'].items():
    if name not in actual or hashlib.sha256(actual[name].read_bytes()).hexdigest() != expected:
        errors.append('Hash mismatch: ' + name)
text = (skill/'SKILL.md').read_text()
if not text.startswith('---\n') or '\nname: adaptive-planning\n' not in text.split('---',2)[1]:
    errors.append('Skill name/frontmatter invalid')
for path in [root/'README.md', *skill.rglob('*.md')]:
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if '://' in target or target.startswith('#'):
            continue
        target = target.split('#',1)[0]
        if target and not (path.parent/target).exists():
            errors.append('Missing local link: ' + str(path.relative_to(root)) + ' -> ' + target)
if not (root/'LICENSE').read_text().startswith('MIT License\n'):
    errors.append('Root MIT license missing')
if not (root/'NOTICE.md').exists():
    errors.append('Required third-party notice missing')
print(json.dumps({'valid': not errors, 'errors': errors,
                  'skill_files': len(actual)+1}, indent=2))
sys.exit(0 if not errors else 1)
