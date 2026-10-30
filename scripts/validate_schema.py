"""Independent full JSON Schema validation; development dependency only."""
import copy
import json
from pathlib import Path
import sys
try:
    import jsonschema
except ImportError:
    raise SystemExit("Install requirements-dev.txt in a Python3.10+ development environment")
root=Path(__file__).resolve().parents[1]/'adaptive-planning'
schema=json.loads((root/'state.schema.json').read_text())
cls=jsonschema.validators.validator_for(schema)
cls.check_schema(schema)
validator=cls(schema,format_checker=jsonschema.FormatChecker())
files=[root/'templates/state.json',*sorted((root/'examples').glob('*state.json'))]
for p in files:
    validator.validate(json.loads(p.read_text()))
valid=json.loads((root/'templates/state.json').read_text())
validator.validate(valid)
bad=copy.deepcopy(valid);bad['profile']['sleep']['start']='24:61'
if not list(validator.iter_errors(bad)):
    raise SystemExit('Independent validator accepted invalid HH:MM')
bad=copy.deepcopy(valid);bad['updated_at']='not-a-date'
if not list(validator.iter_errors(bad)):
    raise SystemExit('Independent validator did not enforce date-time format')
print(json.dumps({'full_schema_valid':True,'valid_fixtures':len(files),'invalid_time_and_timestamp_rejected':True}))
