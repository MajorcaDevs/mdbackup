from typing import Dict


def snakeify(camel_case: str) -> str:
    if not isinstance(camel_case, str):
        return camel_case
    snaked = ''
    for c in camel_case:
        if c.isupper() and len(snaked) == 0:
            snaked += c.lower()
        elif c.isupper():
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
