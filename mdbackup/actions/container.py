from functools import wraps
from importlib import import_module
import logging
import re
from typing import Dict, Optional, Union

from mdbackup.actions.ds import (
    DataStreamAction,
    DataStreamFinalAction,
    DataStreamToDirEntryTransformAction,
    DataStreamTransformAction,
    DirEntry,
    DirEntryAction,
    DirEntryFinalAction,
    DirEntryToDataStreamTransformAction,
    DirEntryTransformAction,
)


__all__ = [
    'register_action',
    'register_actions_from_module',
    'get_action',
    'is_final',
    'are_compatible',
]


_AnyAction = Union[
    DataStreamAction,
    DataStreamTransformAction,
    DataStreamToDirEntryTransformAction,
    DataStreamFinalAction,
    DirEntryAction,
    DirEntryTransformAction,
    DirEntryToDataStreamTransformAction,
    DirEntryFinalAction,
]


class _Action:
    def __init__(self,
                 action: _AnyAction,
                 unaction: _AnyAction,
                 _id: str,
                 _input: Optional[str],
                 output: Optional[str]):
        self.action = action
        self.unaction = unaction
        self.id = _id
        self.input = _input
        self.output = output


_actions: Dict[str, _Action] = {}
_id_regex = re.compile(r'[a-z_][a-z0-9_-]+', re.IGNORECASE)
_valid_expected_inputs = [
    'stream',
    'directory',
]
_valid_outputs = [
    'stream',
    'stream:file',
    'stream:process',
    'stream:pipe',
    'directory',
]


def register_action(identifier: str,
                    action: _AnyAction = None,
                    unaction: _AnyAction = None,
                    expected_input: Optional[str] = None,
                    output: Optional[str] = None):
    if identifier in _actions:
        raise KeyError(f'Action {identifier} already exists')

    if not _id_regex.fullmatch(identifier):
        raise KeyError(f'{identifier} is invalid')

    if expected_input is not None and expected_input not in _valid_expected_inputs:
        raise ValueError(f'Invalid expected input type {expected_input}')

    if output is not None and output not in _valid_outputs:
        raise ValueError(f'Invalid output type {output}')

    if not callable(action):
        raise TypeError('action is not a callable object')

    if unaction is not None and not callable(unaction):
        raise TypeError('unaction is not a callable object')

    logging.getLogger(__name__).getChild('register_action').debug(f'Registering action {identifier}')
    _actions[identifier] = _Action(action, unaction, identifier, expected_input, output)


def register_actions_from_module(full_thing: str):
    full_thing_split = full_thing.split('#')
    if len(full_thing_split) != 2:
        raise ValueError('Module name is invalid: should contain the module and the function with #')

    module = full_thing_split[0]
    func_name = full_thing_split[1]
    package = import_module(module)
    func = getattr(package, func_name)
    func(register_action=register_action,
         get_action=get_action,
         get_unaction=get_unaction,
         dir_entry=DirEntry,
         action=action,
         unaction=unaction)


def get_action(identifier: str) -> _AnyAction:
    return _actions[identifier].action


def get_unaction(identifier: str) -> _AnyAction:
    return _actions[identifier].unaction


def are_compatible(id1: str, id2: str) -> Optional[str]:
    action1 = _actions[id1]
    action2 = _actions[id2]

    if action1.output is None:
        return f'{id1} cannot be connected to {id2}: {id1} has no output'
    elif action1.output.startswith('stream'):
        if action2.input != 'stream':
            return f'{id1} cannot be connected to {id2}: {id2} expected input is not a stream'
    else:
        if action2.input != 'directory':
            return f'{id1} cannot be connected to {id2}: {id2} expected input is not a directory'


def is_final(id1: str) -> bool:
    action = _actions[id1]
    return action.output is None


def _clean_actions():
    _actions.clear()


def action(identifier: str, input: Optional[str] = None, output: Optional[str] = None, unaction=None):
    def _action_impl(func):
        register_action(identifier, action=func, expected_input=input, output=output, unaction=unaction)

        @wraps(func)
        def _nothing_in_fact(*args, **kwargs):
            return func(*args, **kwargs)

        return _nothing_in_fact

    return _action_impl


def unaction(identifier: str):
    def _unaction_impl(func):
        if identifier not in _actions:
            raise SystemError(f'Cannot register unaction {identifier} before registering its action counterpart')
        if callable(_actions[identifier].unaction):
            raise SystemError(f'Cannot register again an already registered unaction for action {identifier}')

        _actions[identifier].unaction = func

        @wraps(func)
        def _nothing_in_fact(*args, **kwargs):
            return func(*args, **kwargs)

        return _nothing_in_fact

    return _unaction_impl
