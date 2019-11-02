# Small but customizable utility to create backups and store them in
# cloud storage providers
# Copyright (C) 2018  Melchor Alejo Garau Madrigal
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from datetime import datetime
import logging
import os
from pathlib import Path
import re
from typing import Dict, List, Tuple

from .actions.runner import run_task_actions
from .config import SecretConfig
from .hooks import run_hook
from .tasks.tasks import Tasks
from .utils import write_data_file


MANIFEST_VERSION = 1


def generate_backup_path(backups_folder: Path) -> Path:
    """
    Creates a path with the folder (named with the right structure)
    that will be used as backup folder in this run.
    """
    now = datetime.utcnow()
    isostring = now.isoformat(timespec='minutes')
    return Path(backups_folder, isostring).resolve()


def get_tasks_definitions(config_path: Path) -> List[Path]:
    """
    Gets the list of available tasks definitions files inside the 'tasks' folder.
    """
    defs_dir = config_path / 'tasks'
    if not defs_dir.exists():
        raise FileNotFoundError(f'The tasks folder does not exist')
    definitions = [x for x in defs_dir.iterdir() if x.is_file() and x.name.split('.')[-1] in ('json', 'yaml', 'yml')]
    definitions.sort()
    return [script.absolute() for script in definitions]


def run_tasks(
    tasks: Tasks,
    backup_path: Path,
    prev_backup_path: Path,
    env: dict,
    secrets: List[SecretConfig],
) -> Dict[str, Path]:
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
        resolved_env = resolve_secrets({**env, **task.env}, secrets)
        run_hook(f'backup:tasks:{tasks.name}:task:{task.name}:before', str(final_backup_path), tasks.name, task.name)

        try:
            actions = []
            for it in task.actions:
                key, value = next(iter(it.items()))
                if isinstance(value, dict):
                    new_value = {
                        **resolved_env,
                        **value,
                        '_backup_path': final_backup_path,
                        '_prev_backup_path': prev_backup_path,
                    }
                    new_value = resolve_secrets(new_value, secrets)
                    actions.append({key: new_value})
                else:
                    actions.append({key: value})

            tasks_results[task.name] = run_task_actions(task.name, actions).relative_to(backup_path)
        except Exception as e:
            logger.exception(f'Task {task.name} failed')
            run_hook(f'backup:tasks:{tasks.name}:task:{task.name}:error',
                     ', '.join(e.args),
                     str(backup_path),
                     tasks.name,
                     task.name)
            if task.stop_on_fail:
                raise e

        run_hook(f'backup:tasks:{tasks.name}:task:{task.name}:after', str(backup_path), tasks.name, task.name)

    return tasks_results


def resolve_secret(key_parts: List[str], secret: SecretConfig):
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


def resolve_secrets(env: dict, secrets: List[SecretConfig]) -> dict:
    """
    Given a environment dict, tries to resolve all secrets found and returns a
    copy of the dict with secrets resolved.
    """
    logger = logging.getLogger(__name__).getChild('resolve_secrets')
    new_env = {}
    for key, value in env.items():
        if isinstance(value, str):
            if value.startswith('#'):
                logger.debug(f'Trying to resolve env {key} with secret alias {value}')
                for secret in secrets:
                    new_value = resolve_secret(value[1:].split('.'), secret)
                    if new_value is not None:
                        logger.debug(f'Env {key} resolved using {secret.type}')
                        new_env[key] = new_value
                        break

                if new_value is None:
                    logger.warn(f'Env {key} with secret alias {value} cannot be resolved')
                    new_env[key] = value
            else:
                new_env[key] = value
        elif isinstance(value, dict):
            new_env[key] = resolve_secrets(value, secrets)
        else:
            new_env[key] = value

    return new_env


def create_backup_manifest(backup_path: Path, results: Dict[str, Tuple[Tasks, Dict[str, Path]]]):
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
                'result': tasks_results[task.name],
            } for task in tasks.tasks],
        }

    manifest_path = backup_path / '.manifest.yaml'
    logger.debug(f'Writing manifest at {manifest_path}')
    write_data_file(manifest_path, manifest_dict)


def do_backup(backups_folder: Path,
              config_path: Path,
              action_modules: List[str] = [],
              env: dict = {},
              secrets: List[SecretConfig] = []) -> Path:
    """
    Looks for the tasks defs, prepares the directory where the backups will
    be stored, run the tasks and saves the directory with the right name.
    Returns the created directory with the backups. You must define where to
    store the backups in ``backups_folder``. The ``action_modules`` allows
    you to load external modules that contain extra actions. The ``env`` are
    environment variables that will be defined in the tasks execution. Finally,
    the ``secrets`` parameter declares a list of secret backends from where
    secrets will be extracted when requested from ``env`` sections.
    """
    logger = logging.getLogger(__name__).getChild('do_backup')
    tmp_backup = Path(backups_folder, '.partial')
    prev_backup = backups_folder / 'current'
    prev_backup = prev_backup.resolve() if prev_backup.exists() else None
    resolved_env = resolve_secrets(env, secrets)

    run_hook('backup:before', str(tmp_backup))

    logger.info(f'Temporary backup folder is {tmp_backup}')
    tmp_backup.mkdir(exist_ok=True, parents=True)
    tmp_backup.chmod(0o755)
    tasks_definitions_results: Dict[str, Tuple[Tasks, Dict[str, Path]]] = {}
    for tasks_definition in get_tasks_definitions(config_path):
        try:
            logger.debug(f'Loading tasks definition file {tasks_definition}')
            tasks = Tasks(tasks_definition)
        except KeyError:
            logger.error(f'Could not parse {tasks_definition}')
            raise

        logger.info(f'Preparing to run tasks of {tasks.name}')
        run_hook(f'backup:tasks:{tasks.name}:before', str(tmp_backup), tasks.name)
        try:
            resolved_tasks_env = resolve_secrets({**resolved_env, **tasks.env}, secrets)
            result = run_tasks(tasks, tmp_backup, prev_backup, resolved_tasks_env, secrets)
            tasks_definitions_results[tasks.file_name] = (tasks, result)
        except Exception as e:
            logger.error(f'One of the tasks of {tasks.name} failed')
            run_hook(f'backup:tasks:{tasks.name}:error', str(tmp_backup), ', '.join(e.args), tasks.name)
            raise Exception(f'One of the tasks of {tasks.name} failed, backup will stop', tasks.name)

        run_hook(f'backup:tasks:{tasks.name}:after', str(tmp_backup), tasks.name)

    backup = generate_backup_path(backups_folder)
    logger.info(f'Moving {tmp_backup} to {backup}')
    tmp_backup.rename(backup)

    logger.info(f'Creating manifest of backup {backup}')
    create_backup_manifest(backup, tasks_definitions_results)

    current_backup = Path(backups_folder, 'current')
    if current_backup.is_symlink():
        current_backup.unlink()
    os.symlink(backup, current_backup)

    run_hook('backup:after', str(backup))

    return backup


def get_backup_folders_sorted(backups_folder: Path) -> List[Path]:
    """
    Gets the backups folders sorted.
    """
    regex = re.compile(r'\d{4}-\d{2}-\d{2}T\d{1,2}:\d{2}')
    folders = [folder for folder in backups_folder.iterdir() if folder.is_dir() and regex.match(folder.name)]
    folders.sort()
    return [folder.absolute() for folder in folders]
