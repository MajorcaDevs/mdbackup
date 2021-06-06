from datetime import datetime
import logging
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any, Dict, List, Tuple

from ..actions.runner import run_task_actions
from ..config import Config, SecretConfig
from ..hooks import run_hook
from ..tasks.tasks import Tasks
from ..utils import write_data_file


MANIFEST_VERSION = 1


def _generate_backup_path(backups_folder: Path) -> Path:
    """
    Creates a path with the folder (named with the right structure)
    that will be used as backup folder in this run.
    """
    now = datetime.utcnow()
    isostring = now.isoformat(timespec='minutes')
    return Path(backups_folder, isostring).resolve()


def _get_tasks_definitions(config_path: Path) -> List[Path]:
    """
    Gets the list of available tasks definitions files inside the 'tasks' folder.
    """
    defs_dir = config_path / 'tasks'
    if not defs_dir.exists():
        raise FileNotFoundError('The tasks folder does not exist')
    definitions = [x for x in defs_dir.iterdir() if x.is_file() and x.name.split('.')[-1] in ('json', 'yaml', 'yml')]
    definitions.sort()
    return [script.absolute() for script in definitions]


def _inject_resolved_env_into_actions(
    actions: List[Dict[str, Any]],
    env: dict,
    secrets: List[SecretConfig],
) -> List[Dict[str, Any]]:
    """
    Given a list of actions for a task, resolves all secrets, injects them in the parameters to pass to each action
    and returns the new parameters for the actions.
    """
    resolved_env = _resolve_secrets(env, secrets)
    resolved_env = _resolve_env_vars(resolved_env, resolved_env)
    new_actions = []
    for it in actions:
        key, value = next(iter(it.items()))
        resolved_value = _resolve_secrets(value, secrets)
        if isinstance(value, dict):
            new_value = {
                **resolved_env,
                **resolved_value,
            }
            new_value = _resolve_secrets(new_value, secrets)
            new_value = _resolve_env_vars(new_value, resolved_env)
            new_actions.append({key: new_value})
        elif isinstance(value, str):
            new_value = _resolve_secrets({'v': value}, secrets)['v']
            new_value = _resolve_env_vars(new_value, resolved_env)
            new_actions.append({key: new_value})
        else:
            new_actions.append({key: value})

    return new_actions


def _run_tasks(
    tasks: Tasks,
    backup_path: Path,
    prev_backup_path: Path,
    env: dict,
    secrets: List[SecretConfig],
) -> Dict[str, Path]:
    """
    Given a tasks file (already parsed), runs each of the tasks.

    If the tasks file has defined a ``inside`` path, it will create the folder and store all the results inside
    the folder. For the each task ``env``section, will resolve all secrets using the providers (if possible) and
    inject them as parameters into each action. Then will run each task and store the result path into a dictionary
    that will be returned at the end. If a task fails and ``stopOnFail`` is set to true, then it will raise an
    exception and stop running the tasks file.
    """
    logger = logging.getLogger(__name__).getChild('run_tasks')
    final_backup_path = backup_path
    if tasks.inside_folder is not None:
        logger.info(f'Tasks {tasks.name} will store files in {tasks.inside_folder}')
        final_backup_path = backup_path / tasks.inside_folder
        if not str(final_backup_path).startswith(str(backup_path)):
            raise ValueError('inside is not valid: cannot go outside the backup path, use relative paths')
        prev_backup_path = prev_backup_path / tasks.inside_folder if prev_backup_path is not None else None
        final_backup_path.mkdir(exist_ok=True, parents=True)
        final_backup_path.chmod(0o755)

    tasks_results: Dict[str, Path] = {}
    for task in tasks.tasks:
        run_hook('backup:tasks:task:pre', {
            'path': str(final_backup_path),
            'previousPath': str(prev_backup_path) if prev_backup_path is not None else None,
            'tasksName': tasks.name,
            'taskName': task.name,
        })

        try:
            actions = _inject_resolved_env_into_actions(task.actions,
                                                        {
                                                            **env,
                                                            **task.env,
                                                            '_backup_path': final_backup_path,
                                                            '_prev_backup_path': prev_backup_path,
                                                        },
                                                        secrets)

            tasks_results[task.name] = run_task_actions(task.name, actions).relative_to(backup_path)

            run_hook('backup:tasks:task:post', {
                'path': str(final_backup_path),
                'previousPath': str(prev_backup_path) if prev_backup_path is not None else None,
                'tasksName': tasks.name,
                'taskName': task.name,
                'result': str(tasks_results[task.name]),
            })
        except Exception as e:
            logger.exception(f'Task {task.name} failed')
            run_hook('backup:tasks:task:error', {
                'message': ', '.join(e.args),
                'path': str(final_backup_path),
                'previousPath': str(prev_backup_path) if prev_backup_path is not None else None,
                'tasksName': tasks.name,
                'taskName': task.name,
            })
            if task.stop_on_fail:
                raise e
            else:
                tasks_results[task.name] = None

    return tasks_results


def _resolve_secret(key_parts: List[str], secret: SecretConfig):
    """
    Given a key in parts and a secret configuration, tries to resolve the secret
    from the backend using the configured alias in the ``env`` section of the
    secret backend configuration. If no secret alias is found, then it will
    return None.
    """
    if len(key_parts) == 0:
        return

    value = secret.env
    while len(key_parts) > 0:
        key_part = key_parts.pop(0)
        if isinstance(value, dict) and key_part in value:
            value = value[key_part]
        else:
            return

    return secret.backend.get_secret(value)


def _resolve_secrets(env: dict, secrets: List[SecretConfig]) -> dict:
    """
    Given a environment dict, tries to resolve all secrets found and returns a
    copy of the dict with secrets resolved.
    """
    logger = logging.getLogger(__name__).getChild('resolve_secrets')
    if not isinstance(env, dict):
        return env

    new_env = {}
    for key, value in env.items():
        if isinstance(value, str):
            if value.startswith('#'):
                logger.debug(f'Trying to resolve env {key} with secret alias {value}')
                new_value = None
                for secret in secrets:
                    new_value = _resolve_secret(value[1:].split('.'), secret)
                    if new_value is not None:
                        logger.debug(f'Env {key} resolved using {secret.type}')
                        new_env[key] = new_value
                        break

                if new_value is None:
                    logger.warning(f'Env {key} with secret alias {value} cannot be resolved')
                    new_env[key] = value
            else:
                new_env[key] = value
        elif isinstance(value, dict):
            new_env[key] = _resolve_secrets(value, secrets)
        else:
            new_env[key] = value

    return new_env


def _resolve_env_vars(value, task_env: dict) -> dict:
    logger = logging.getLogger(__name__).getChild('resolve_env_vars')
    if not isinstance(value, (str, list, dict)):
        return value

    expr = re.compile(r'\$\{[a-z0-9_-]*\}', re.IGNORECASE)
    if isinstance(value, str):
        env_var_match = expr.search(value)
        while env_var_match is not None:
            env_var = env_var_match[0][2:-1]
            env_var_value = ''
            if env_var in task_env:
                if isinstance(task_env[env_var], (str, int, float, Path)):
                    env_var_value = str(task_env[env_var])
                else:
                    logger.warning(f'Environment variable value from task {env_var} is not a string, ignoring...')
            elif env_var in os.environ:
                env_var_value = os.environ[env_var]
            else:
                logger.warning(f'Environment variable {env_var} cannot be found, ignoring...')

            value = (
                value[0:env_var_match.start()] +
                env_var_value +
                value[env_var_match.end():]
            )
            end_pos = env_var_match.start() + len(env_var_value)
            env_var_match = expr.search(value, pos=end_pos)

        return value
    elif isinstance(value, list):
        return list(map(lambda x: _resolve_env_vars(x, task_env), value))
    else:
        for key, val in value.items():
            value[key] = _resolve_env_vars(val, task_env)
        return value


def _create_backup_manifest(backup_path: Path, results: Dict[str, Tuple[Tasks, Dict[str, Path]]]):
    """
    Given the backup path and all tasks with their results, writes the manifest into the backup folder.
    """
    logger = logging.getLogger(__name__).getChild('create_backup_manifest')
    manifest_dict = {
        'version': MANIFEST_VERSION,
        'createdAt': datetime.utcnow().isoformat(),
        'uploaded': False,
        'tasksDefinitions': {},
    }

    for tasks_def_name, (tasks, tasks_results) in results.items():
        manifest_dict['tasksDefinitions'][tasks_def_name] = {
            'env': tasks.env,
            'inside': tasks.inside_folder,
            'tasks': [{
                'name': task.name,
                'env': task.env,
                'actions': task.actions,
                'cloud': task.cloud,
                'result': tasks_results[task.name],
            } for task in tasks.tasks],
        }

    manifest_path = backup_path / '.manifest.yaml'
    logger.debug(f'Writing manifest at {manifest_path}')
    write_data_file(manifest_path, manifest_dict)


def _do_backup(backups_folder: Path,
               config_path: Path,
               env: dict = {},
               secrets: List[SecretConfig] = []) -> Path:
    """
    Looks for the tasks defs, prepares the directory where the backups will
    be stored, run the tasks and saves the directory with the right name.
    Returns the created directory with the backups. You must define where to
    store the backups in ``backups_folder``. The ``env`` are environment
    variables that will be defined in the tasks execution. Finally, the
    ``secrets`` parameter declares a list of secret backends from where
    secrets will be extracted when requested from ``env`` sections.
    """
    logger = logging.getLogger(__name__).getChild('do_backup')
    tmp_backup = Path(backups_folder, '.partial')
    prev_backup = backups_folder / 'current'
    prev_backup = prev_backup.resolve() if prev_backup.exists() else None
    resolved_env = _resolve_secrets(env, secrets)

    run_hook('backup:pre', {'path': str(tmp_backup)})

    logger.info(f'Temporary backup folder is {tmp_backup}')
    tmp_backup.mkdir(exist_ok=True, parents=True)
    tmp_backup.chmod(0o755)
    tasks_definitions_results: Dict[str, Tuple[Tasks, Dict[str, Path]]] = {}
    for tasks_definition in _get_tasks_definitions(config_path):
        try:
            logger.debug(f'Loading tasks definition file {tasks_definition}')
            tasks = Tasks(tasks_definition)
        except KeyError:
            logger.error(f'Could not parse {tasks_definition}')
            raise

        logger.info(f'Preparing to run tasks of {tasks.name}')
        run_hook('backup:tasks:pre', {'path': str(tmp_backup), 'tasksName': tasks.name})
        try:
            resolved_tasks_env = _resolve_secrets({**resolved_env, **tasks.env}, secrets)
            result = _run_tasks(tasks, tmp_backup, prev_backup, resolved_tasks_env, secrets)
            tasks_definitions_results[tasks.file_name] = (tasks, result)
        except Exception as e:
            logger.error(f'One of the tasks of {tasks.name} failed')
            run_hook('backup:tasks:error', {
                'path': str(tmp_backup),
                'message': ', '.join(e.args),
                'tasksName': tasks.name,
            })
            raise Exception(f'One of the tasks of {tasks.name} failed, backup will stop', tasks.name)

        run_hook('backup:tasks:post', {
            'path': str(tmp_backup),
            'tasksName': tasks.name,
            'created': [str(p) for p in tasks_definitions_results[tasks.file_name][1].values()],
        })

    backup = _generate_backup_path(backups_folder)
    logger.info(f'Moving {tmp_backup} to {backup}')
    tmp_backup.rename(backup)

    logger.info(f'Creating manifest of backup {backup}')
    _create_backup_manifest(backup, tasks_definitions_results)

    current_backup = Path(backups_folder, 'current')
    if current_backup.is_symlink():
        current_backup.unlink()
    os.symlink(backup, current_backup)

    run_hook('backup:post', {
        'path': str(backup),
        'created': {value[0].name: [str(p) for p in value[1].values()]
                    for _, value in tasks_definitions_results.items()},
    })

    return backup


def main_backup(config: Config) -> Path:
    logger = logging.getLogger(__name__).getChild('backup')
    # Do backups
    try:
        return _do_backup(config.backups_path,
                          config.config_folder,
                          env={
                             **config.env,
                          },
                          secrets=config.secrets)
    except Exception as e:
        logger.error(e)
        run_hook('backup:error', {
            'path': str(config.backups_path / '.partial'),
            'message': str(e),
            'stepName': e.args[1] if len(e.args) > 2 else None,
        })
        shutil.rmtree(str(config.backups_path / '.partial'))
        sys.exit(1)
