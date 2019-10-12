import json
from typing import Dict

try:
    from yaml import CLoader as Loader, CDumper as Dumper, load as yaml_load, dump as yaml_dump
except ImportError:
    from yaml import Loader, Dumper, load as yaml_load, dump as yaml_dump


def snakeify(camel_case: str) -> str:
    if not isinstance(camel_case, str):
        return camel_case
    snaked = ''
    for c in camel_case:
        if c.isupper() and len(snaked) == 0:
            snaked += c.lower()
        elif c.isupper():
            if snaked.endswith('_'):
                snaked += c.lower()
            else:
                snaked += f'_{c.lower()}'
        else:
            snaked += c
    return snaked


def change_keys(d: Dict[str, any]) -> Dict[str, any]:
    new_dict = {}
    for key, value in d.items():
        new_key = snakeify(key)
        if isinstance(value, dict):
            new_dict[new_key] = change_keys(value)
        else:
            new_dict[new_key] = value
    return new_dict


def raise_if_type_is_incorrect(obj, types, message, required=False):
    if required and obj is None:
        raise TypeError(message)
    elif not required and obj is None:
        return
    if not isinstance(obj, types):
        raise TypeError(message)


def read_data_file(path):
    with open(path, 'r') as data_file:
        if path.name.endswith('.json'):
            return json.load(data_file)
        elif path.name.endswith('.yaml') or path.name.endswith('.yml'):
            return yaml_load(data_file, Loader=Loader)
        else:
            return None


def write_data_file(path, data):
    with open(path, 'w') as data_file:
        if path.name.endswith('.json'):
            json.dump(data, data_file)
        elif path.name.endswith('.yaml') or path.name.endswith('.yml'):
            yaml_dump(data, data_file, Dumper=Dumper)
        else:
            raise NotImplementedError(f'Write data to {path.name} is not implemented')
