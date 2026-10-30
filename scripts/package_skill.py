"""Build a deterministic skill ZIP and file manifest from reviewed skill sources."""
import hashlib
import json
from pathlib import Path
import re
import zipfile

root=Path(__file__).resolve().parents[1]
skill=root/'adaptive-planning'
version=re.search(r'version:\s*"([0-9.]+)"',(skill/'SKILL.md').read_text()).group(1)
manifest=skill/'validation/manifest.json'
files=sorted(p for p in skill.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p!=manifest)
for p in files:
    if p.is_symlink() or any(part.startswith('.') for part in p.relative_to(skill).parts):
        raise SystemExit('Refuse hidden or linked package source: '+str(p))
manifest.write_text(json.dumps({'algorithm':'sha256','files':{str(p.relative_to(skill)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'excludes':['validation/manifest.json']},indent=2)+'\n')
files=sorted(p for p in skill.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
destination=root/'dist';destination.mkdir(exist_ok=True)
archive=destination/('adaptive-planning-'+version+'.zip')
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in files:
        info=zipfile.ZipInfo('adaptive-planning/'+str(p.relative_to(skill)),date_time=(2026,10,30,12,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
        z.writestr(info,p.read_bytes())
with zipfile.ZipFile(archive) as z:
    assert set(z.namelist())=={'adaptive-planning/'+str(p.relative_to(skill)) for p in files}
    for p in files:assert z.read('adaptive-planning/'+str(p.relative_to(skill)))==p.read_bytes()
print(json.dumps({'archive':str(archive.relative_to(root)),'files':len(files),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'folder_bytes_match':True}))
