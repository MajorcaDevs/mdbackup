import json
import logging
import shlex
import subprocess
from threading import Thread
from typing import Any, Dict, List


_hooks_config: Dict[str, List[str]] = {}


def run_hook(hook_name: str, obj: Dict[str, Any]):
    logger = logging.getLogger(__name__)
    if hook_name not in _hooks_config:
        logger.debug(f'The hook {hook_name} is not defined, not running it')
        return

    obj_in_json = json.dumps(obj, indent=2)

    logger.info(f'Running hook {hook_name}')
    joins = [(_hook_runner(hook_name, hook, obj_in_json), hook)
             for hook in _hooks_config[hook_name]]
    for join, hook in joins:
        try:
            join()
        except Exception as e:
            logger.debug(f'Failed running the hook {hook}', e)


def _hook_runner(name: str, path: str, stdin: str):
    logger = logging.getLogger(f'{__name__}:{name}')
    logger.debug(f'Running script {path}')
    args = shlex.split(path, posix=True)
    process = subprocess.Popen(args,
                               stdin=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               bufsize=0)

    # Write the data
    process.stdin.write(stdin.encode('UTF-8'))
    process.stdin.close()

    # Print stderr lines in a thread
    def stderr_process():
        for err_line in process.stderr:
            logger.debug(err_line[:-1].decode('UTF-8'))
        process.stderr.close()

    stderr_thread = Thread(target=stderr_process)
    stderr_thread.start()

    # Read every line (from stdout) into the logger
    for line in process.stdout:
        logger.debug(line[:-1].decode('UTF-8'))
    process.stdout.close()

    # Join thread and wait to wait process (same as join, but in processes)
    def join():
        stderr_thread.join()
        return process.wait()

    return join


def define_hook(hook_name: str, hook_script: str):
    if hook_name not in _hooks_config:
        _hooks_config[hook_name] = []

    _hooks_config[hook_name].append(hook_script)
