from pathlib import Path
import sys

import jsonschema

from mdbackup.utils import read_data_file


def _stringify_path(path):
    str_path = ''
    for value in path:
        if isinstance(value, int):
            str_path += f'[{value}]'
        else:
            if not str_path or str_path[-1] == '[':
                str_path += value
            else:
                str_path += f'.{value}'
    return str_path


def validate(schema, instance, output=sys.stderr):
    schema_path = Path(schema)
    schema = read_data_file(schema_path)
    schema['$id'] = f'file://{schema_path.absolute()}'

    validator = jsonschema.Draft7Validator(schema=schema)
    validator.check_schema(schema)

    is_valid = True
    for error in validator.iter_errors(instance):
        output.write(f'- {_stringify_path(error.path)}: {error.message}\n')
        is_valid = False

    return is_valid
