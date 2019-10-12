import io
import logging
import subprocess
import types
from typing import Any, Dict, List, Tuple

from mdbackup.actions.container import are_compatible, get_action, is_final
from mdbackup.actions.ds import OutputDataStream


logger = logging.getLogger(__name__)


def _get_action_key_from_definition(action_def: dict):
    return next(iter(action_def.keys()))


def _get_action_from_definition(action_def: dict) -> Tuple[Any, dict, str]:
    key = _get_action_key_from_definition(action_def)
    return (get_action(key), action_def[key], key)


def _check_for_incompatible_actions(actions: List[Dict[str, Any]]):
    if len(actions) == 0:
        return

    prev_action = _get_action_key_from_definition(actions[0])
    for action_def in actions[1:]:
        action = _get_action_key_from_definition(action_def)
        comp = are_compatible(prev_action, action)
        if comp is not None:
            logger.warning(comp)
            raise Exception(comp)
        prev_action = action

    if not is_final(prev_action):
        raise Exception(f'The final action {prev_action} has output and should not have')


def _process_output(output, action_key: str):
    if isinstance(output, subprocess.Popen):
        prev_input = output.stdout
        thing = (output, action_key)
        logger.debug(f'{action_key} returned a process')
    elif isinstance(output, io.TextIOBase):
        prev_input = output.buffer.raw
        if not isinstance(prev_input, io.FileIO):
            raise IOError(
                'The stream from {action_key} does not have associated a file-descriptor (must contain a io.FileIO)',
            )
        thing = (output, action_key)
        logger.debug(f'{action_key} returned a text-buffered file')
    elif isinstance(output, io.BufferedIOBase):
        prev_input = output.raw
        if not isinstance(prev_input, io.FileIO):
            raise IOError(
                'The stream from {action_key} does not have associated a file-descriptor (must contain a io.FileIO)',
            )
        thing = (output, action_key)
        logger.debug(f'{action_key} returned a byte-buffered file')
    elif isinstance(output, io.FileIO):
        prev_input = output
        thing = (output, action_key)
        logger.debug(f'{action_key} returned a file')
    elif isinstance(output, types.GeneratorType):
        prev_input = output
        thing = None
        logger.debug(f'{action_key} returned a directory generator')
    else:
        raise Exception(f'Unsupported output type {type(output)} for {action_key}')
    return prev_input, thing


def _cleanup(things_to_dipose: List[Tuple[OutputDataStream, str]], has_raised: bool):
    failed = []
    for (thing, action) in things_to_dipose:
        logger.debug(f'Waiting for {action} to dispose')
        if isinstance(thing, subprocess.Popen):
            thing.send_signal(subprocess.signal.SIGTERM) if has_raised else None
            lines = ''.join(map(lambda l: l.decode('utf-8'), thing.stderr))
            rc = thing.wait()
            if rc != 0:
                failed.append((action, lines))
        else:
            thing.close()

    if len(failed) > 0:
        raise RuntimeError('\n\n'.join((f'{action}:\n{lines}' for action, lines in failed)), failed)


def run_task_actions(task_name: str, actions: List[Dict[str, Any]]):
    if len(actions) == 0:
        logger.warning(f'Task {task_name} has no actions')
        return

    logger.info(f'Starting run of task {task_name}')
    _check_for_incompatible_actions(actions)

    things_to_dipose: List[Tuple[OutputDataStream, str]] = []
    prev_input = None
    has_raised = False
    try:
        for action_def in actions[:-1]:
            action, params, action_key = _get_action_from_definition(action_def)
            logger.info(f'Running action {action_key}')

            output = action(prev_input, params)
            prev_input, thing = _process_output(output, action_key)
            if thing is not None:
                things_to_dipose.append(thing)

        action, params, action_key = _get_action_from_definition(actions[-1])
        logger.info(f'Running final action {action_key} and waiting for the whole process to end')
        action(prev_input, params)
    except Exception as e:
        has_raised = True
        logger.exception('An action raised an exception')
        raise e
    finally:
        _cleanup(things_to_dipose, has_raised)
        logger.info(f'End running task {task_name}')
