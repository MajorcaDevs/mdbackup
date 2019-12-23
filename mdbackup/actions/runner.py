import io
import logging
from pathlib import Path
import subprocess
import types
from typing import Any, Dict, List, Optional, Tuple

from mdbackup.actions.container import are_compatible, get_action, get_unaction, is_final
from mdbackup.actions.ds import OutputDataStream


def _get_action_key_from_definition(action_def: dict):
    return next(iter(action_def.keys()))


def _get_action_from_definition(action_def: dict) -> Tuple[Any, dict, str]:
    key = _get_action_key_from_definition(action_def)
    return (get_action(key), action_def[key], key)


def _get_unaction_from_definition(action_def: dict) -> Tuple[Any, dict, str]:
    key = _get_action_key_from_definition(action_def)
    return (get_unaction(key), action_def[key], key)


def _check_for_incompatible_actions(actions: List[Dict[str, Any]]):
    if len(actions) == 0:
        return

    logger = logging.getLogger(__name__).getChild('_check_for_incompatible_actions')
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


def _check_for_missing_unactions(actions: List[Dict[str, Any]]):
    for action_def in actions:
        unaction, _, action_name = _get_unaction_from_definition(action_def)
        if not callable(unaction):
            raise Exception(f'The action {action_name} has no unaction')


def _process_output(output, action_key: str):
    logger = logging.getLogger(__name__).getChild('_process_output')
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
    logger = logging.getLogger(__name__).getChild('_cleanup')
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


def run_task_actions(task_name: str, actions: List[Dict[str, Any]]) -> Optional[Path]:
    logger = logging.getLogger(__name__).getChild('run_task_actions')
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
            things_to_dipose.append(thing) if thing is not None else None

        action, params, action_key = _get_action_from_definition(actions[-1])
        logger.info(f'Running final action {action_key} and waiting for the whole process to end')
        result = action(prev_input, params)
        if result is None or not isinstance(result, Path):
            raise ValueError(f'Action {action_key} does not return the path of its output (return value must be Path)')
        return result
    except Exception as e:
        has_raised = True
        logger.exception('An action raised an exception')
        raise e
    finally:
        _cleanup(things_to_dipose, has_raised)
        logger.info(f'End running task {task_name}')


def run_task_unactions(task_name: str, actions: List[Dict[str, Any]]):
    logger = logging.getLogger(__name__).getChild('run_task_unactions')
    if len(actions) == 0:
        logger.warning(f'Task {task_name} has no actions')
        return

    logger.info(f'Starting run of task {task_name}')
    _check_for_incompatible_actions(actions)
    _check_for_missing_unactions(actions)

    things_to_dipose: List[Tuple[OutputDataStream, str]] = []
    prev_input = None
    has_raised = False
    unactions = list(reversed(actions))
    try:
        for unaction_def in unactions[:-1]:
            unaction, params, unaction_key = _get_unaction_from_definition(unaction_def)
            logger.info(f'Running unaction {unaction_key}')

            output = unaction(prev_input, params)
            prev_input, thing = _process_output(output, unaction_key)
            things_to_dipose.append(thing) if thing is not None else None

        unaction, params, unaction_key = _get_unaction_from_definition(unactions[-1])
        logger.info(f'Running final unaction {unaction_key} and waiting for the whole process to end')
        unaction(prev_input, params)
    except Exception as e:
        has_raised = True
        logger.exception('An unaction raised an exception')
        raise e
    finally:
        _cleanup(things_to_dipose, has_raised)
        logger.info(f'End running task {task_name}')
