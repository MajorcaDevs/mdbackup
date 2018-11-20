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
from pathlib import Path
import re
import os
import subprocess
from tempfile import NamedTemporaryFile
from typing import List, Dict


def generate_backup_path(backups_folder: Path) -> Path:
    """
    Creates a path with the folder (named with the right structure)
    that will be used as backup folder in this run.
    """
    now = datetime.now()
    isostring = now.isoformat(timespec='minutes')
    return Path(backups_folder, isostring)


def get_steps_scripts() -> List[Path]:
    """
    Gets the list of available steps scripts inside the relative
    path 'steps'.
    """
    steps_dir = Path('steps')
    if not steps_dir.exists():
        steps_dir.mkdir()
    scripts = [x for x in steps_dir.iterdir() if x.is_file() and x.stat().st_mode & 73]
    scripts.sort()
    return [script.absolute() for script in scripts]


def run_step(step: Path, cwd: Path, env: Dict[str, str] = {}):
    """
    Runs this step, with the current working directory defined in ``cwd``
    and, optionally, extra environment variables defined in ``env``.
    Returns the completed subprocess object.
    """
    full_env = dict(os.environ)
    for key, value in env.items():
        if value is not None:
            full_env[key.upper()] = value
    return subprocess.run([str(step)],
                          stderr=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          cwd=str(cwd),
                          env=full_env)


def generate_script(step_script: Path, custom_utils: str = None) -> Path:
    """
    Given the original step script path, and an optional custom utils script,
    will generate a script that will run in sh, with the app's utils script
    and the custom utils (if defined). Returns the path to the temporary script.
    """
    logger = logging.getLogger(__name__)
    me_irl = os.path.dirname(os.path.realpath(__file__))
    with NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b'#!/usr/bin/env bash\n')
        tmp.write(f'source {me_irl}/utils.sh\n'.encode('utf-8'))
        if custom_utils is not None: tmp.write(f'source {custom_utils}\n'.encode('utf-8'))
        tmp.write(b'\n')
        with open(step_script, 'r') as script_file:
            script_file_contents = script_file.read()
            logger.debug(f'''Generating temporary script {tmp.name}
#!/usr/bin/env bash
source {me_irl}/utils.sh
{"source " + custom_utils if custom_utils is not None else ""}

{script_file_contents}''')
            tmp.write(script_file_contents.encode('utf-8'))

        return Path(tmp.name)


def do_backup(backups_folder: Path, custom_utils: str = None, **kwargs) -> Path:
    """
    Looks for the step scripts, prepares the directory where the backups will
    be stored, run the scripts and saves the directory with the right name.
    Returns the created directory with the backups. You must define where to
    store the backups in ``backups_folder``. The ``custom_utils`` allows you
    to define an extra utilities script that will be injected in every step
    script. The ``kwargs`` are environment variables that will be defined in
    the steps execution.
    """
    logger = logging.getLogger(__name__)
    tmp_backup = Path(backups_folder, '.partial')

    logger.info(f'Temporary backup folder is {tmp_backup}')
    tmp_backup.mkdir(exist_ok=True, parents=True)
    for step_script in get_steps_scripts():
        logger.info(f'Running script {step_script}')
        tmp_path = generate_script(step_script, custom_utils)
        tmp_path.chmod(0o755)

        output = run_step(tmp_path, tmp_backup, kwargs)
        if output.returncode != 0:
            logger.error(f'Script returned {output.returncode}')
            if output.stdout: logger.error(f'stdout\n{output.stdout.decode("utf-8")}')
            if output.stderr: logger.error(f'stderr\n{output.stderr.decode("utf-8")}')
        else:
            if output.stdout: logger.debug(f'stdout\n{output.stdout.decode("utf-8")}')
            if output.stderr: logger.debug(f'stderr\n{output.stderr.decode("utf-8")}')
        tmp_path.unlink()

    backup = generate_backup_path(backups_folder)
    logger.info(f'Moving {tmp_backup} to {backup}')
    tmp_backup.rename(backup)

    current_backup = Path(backups_folder, 'current')
    if current_backup.is_symlink():
        current_backup.unlink()
    os.symlink(backup, current_backup)

    return backup


def get_backup_folders_sorted(backups_folder: Path) -> List[Path]:
    """
    Gets the backups folders sorted.
    """
    regex = re.compile(r'\d{4}-\d{2}-\d{2}T\d{1,2}:\d{2}')
    folders = [folder for folder in backups_folder.iterdir() if folder.is_dir() and regex.match(folder.name)]
    folders.sort()
    return [folder.absolute() for folder in folders]

