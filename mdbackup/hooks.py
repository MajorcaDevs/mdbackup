# Small but customizable utility to create backups and store them in
# cloud storage providers
# Copyright (C) 2019  Melchor Alejo Garau Madrigal / Andrés Mateos García
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

import logging
from pathlib import Path
import subprocess
from threading import Thread
from typing import Optional, List, Dict


hooks_config: Dict[str, List[str]] = {}


def run_hook(hook_name: str, *args: str, cwd: Optional[str] = None):
    logger = logging.getLogger(__name__)
    if hook_name not in hooks_config:
        logger.debug(f'The hook {hook_name} is not defined, not running it')
        return

    if cwd is not None:
        cwd_path = Path(cwd)
        if not cwd_path.exists():
            logger.warning(f'The CWD {cwd} does not exist')
            return
        if not cwd_path.is_dir():
            logger.warning(f'The CWD {cwd} is not a folder')
            return

    logger.info(f'Running hook {hook_name}')
    joins = [(_hook_runner(hook_name, hook, hook_name, *args, cwd=cwd, shell=True), hook)
             for hook in hooks_config[hook_name]]
    for join, hook in joins:
        try:
            join()
        except Exception:
            logger.debug(f'Failed running the hook {hook}')


def _hook_runner(name: str, path: str, *args: str, cwd: Optional[str] = None, shell: bool = False):
    logger = logging.getLogger(f'{__name__}:{name}')
    logger.debug(f'Running script {path}')
    process = subprocess.Popen([path, *args],
                               stderr=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               cwd=cwd,
                               bufsize=1,
                               shell=shell)

    # Print stderr lines in a thread
    stderr_thread = Thread(target=lambda: [logger.debug(err_line[:-1].decode('UTF-8')) for err_line in process.stderr])
    stderr_thread.start()

    # Read every line (from stdout) into the logger
    for line in process.stdout:
        logger.debug(line[0:-1].decode('UTF-8'))

    # Join thread and wait to wait process (same as join, but in processes)
    def join():
        stderr_thread.join()
        return process.wait()

    return join


def define_hook(hook_name: str, hook_script: str):
    if hook_name not in hooks_config:
        hooks_config[hook_name] = []

    hooks_config[hook_name].append(hook_script)
