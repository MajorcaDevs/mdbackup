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


def validate(schema, instance):
    if isinstance(schema, (str, Path)):
        schema = read_data_file(Path(schema))
    if isinstance(instance, (str, Path)):
        instance = read_data_file(Path(instance))

    validator = jsonschema.Draft7Validator(schema=schema)
    validator.check_schema(schema)

    is_valid = True
    for error in validator.iter_errors(instance):
        sys.stderr.write(f'- {_stringify_path(error.path)}: {error.message}\n')
        is_valid = False

    return is_valid
