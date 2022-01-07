import logging
import os
import shlex
import subprocess
from typing import List

from mdbackup.actions.container import action, unaction
from mdbackup.utils import raise_if_type_is_incorrect


def _parse_command(command: str) -> List[str]:
    return list(shlex.shlex(command, punctuation_chars=True, posix=True))


def reverse_action(func):
    def impl(inp, params: dict):
        logger = logging.getLogger(__name__).getChild(func.__name__ + '_reversed')
        new_params = params.copy()
        if 'reverse' not in params:
            raise ValueError('no reverse option is defined')
        args = params['reverse'].get('args')
        command = params['reverse'].get('command')
        if args is not None:
            new_params['args'] = args
            if 'command' in new_params:
                del new_params['command']
        elif command is not None:
            new_params['command'] = command
            if 'args' in new_params:
                del new_params['args']
        else:
            raise ValueError('no reverse args nor command defined')
        logger.debug('Next command is run reversed')
        return func(inp, new_params)

    return impl


@action('command', input='stream', output='stream:process')
def action_command(inp, params) -> subprocess.Popen:
    logger = logging.getLogger(__name__).getChild('action_command')
    if inp is None:
        inp = subprocess.PIPE

    if isinstance(params, str):
        args = None
        command = params
        extra_env: dict = None
        params = {}
    else:
        args = params.get('args')
        command = params.get('command')
        extra_env: dict = params.get('env')

    raise_if_type_is_incorrect(args, list, 'args must be a list')
    raise_if_type_is_incorrect(extra_env, dict, 'env must be a dictionary')

    if command is not None:
        args = _parse_command(command)
    elif args is None:
        raise KeyError('no args nor command defined')

    env = os.environ.copy()
    if extra_env is not None:
        for key, value in extra_env.items():
            env[key] = value

    str_args = " ".join((f'"{s}"' if ' ' in s else s for s in args))
    str_env = ", ".join((f"{key}={value}" for key, value in (extra_env if extra_env is not None else {}).items()))
    logger.debug(f'Running command {str_args} with environment {str_env}')
    return subprocess.Popen(
        args=args,
        stdin=inp,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
        env=env,
        cwd=params.get('_backup_path'),
        pass_fds=params.get('_pass_fds', ()),
    )


@action('ssh', input='stream', output='stream:process')
def action_ssh(inp, params) -> subprocess.Popen:
    logger = logging.getLogger(__name__).getChild('action_ssh')
    args = []
    env = {}

    password = params.get('password')
    port = params.get('port')
    known_hosts_policy = params.get('knownHostsPolicy')
    forward_agent = params.get('forwardAgent', False)
    identity_file = params.get('identityFile')
    user = params.get('user')
    config_file = params.get('configFile')
    param_args: list = params.get('args')
    param_command = params.get('command')

    raise_if_type_is_incorrect(args, list, 'args must be a list')
    raise_if_type_is_incorrect(password, str, 'password must be a string')
    raise_if_type_is_incorrect(identity_file, str, 'identityFile must be a string')
    raise_if_type_is_incorrect(user, str, 'user must be a string')
    raise_if_type_is_incorrect(config_file, str, 'configFile must be a string')
    raise_if_type_is_incorrect(port, int, 'port must be an int')
    raise_if_type_is_incorrect(params['host'], str, 'host must be a string', required=True)

    if password is not None:
        logger.warning('Using sshpass to connect to a SSH server is highly discouraged')
        args.extend(['sshpass', '-e'])
        env = {'SSHPASS': password}

    args.append('ssh')

    if port is not None:
        args.append('-p', str(port))

    if known_hosts_policy == 'ignore':
        args.extend(['-o', 'UserKnownHostsFile=/dev/null', '-o', 'StrictHostKeyChecking=no'])

    if forward_agent:
        args.append('-A')
    else:
        args.append('-a')

    if identity_file is not None:
        args.extend(['-i', identity_file])

    if user is not None:
        args.extend(['-l', user])

    if config_file is not None:
        args.extend(['-F', config_file])

    args.extend(['-x', params['host']])
    if param_args is not None:
        args.extend(param_args)
    elif param_command is not None:
        args.extend(_parse_command(param_command))
    else:
        raise KeyError('no args nor command defined')

    return action_command(inp, {'args': args, 'env': env})


@action('docker', input='stream', output='stream:process')
def action_docker(inp, params) -> subprocess.Popen:
    logger = logging.getLogger(__name__).getChild('action_docker')
    args = ['docker', 'container', 'run', '--rm', '-i']

    volumes: list = params.get('volumes', [])
    env = params.get('env', [])
    user = params.get('user')
    group = params.get('group')
    network = params.get('network', 'host')
    workdir = params.get('workdir')
    param_args: list = params.get('args')
    param_command = params.get('command')
    pull = params.get('pull', False)
    image = params['image']

    raise_if_type_is_incorrect(volumes, list, 'volumes is not a list')
    raise_if_type_is_incorrect(env, (list, dict), 'env is not a list nor a dictionary')
    raise_if_type_is_incorrect(args, list, 'args must be a list')
    raise_if_type_is_incorrect(user, str, 'user must be a string')
    raise_if_type_is_incorrect(group, str, 'group must be a string')
    raise_if_type_is_incorrect(network, str, 'network must be a string')
    raise_if_type_is_incorrect(workdir, str, 'workdir must be a string')
    raise_if_type_is_incorrect(image, str, 'image must be a string', required=True)

    for volume in volumes:
        args.extend(['-v', volume])

    if isinstance(env, dict):
        env = map(lambda pair: f'{pair[0]}={pair[1]}', env.items())
    for env_var in env:
        args.extend(['-e', env_var])

    if user is not None:
        args.extend(['-u', user])
        if group is not None:
            args[-1] = f'{args[-1]}:{group}'

    args.append(f'--network={network}')

    if workdir is not None:
        args.extend(['-w', workdir])

    if pull:
        logger.info(f'Pulling image {image}...')
        proc = action_command(None, {'command': f'docker image pull -q "{image}"'})
        _, stderr = proc.communicate()
        if proc.returncode != 0:
            logger.error(f'Image pull for {image} failed:\n{stderr.decode("utf-8")}')
            raise ChildProcessError(f'Could not pull image {image}')

    args.append(image)
    if param_args is not None:
        args.extend(param_args)
    elif param_command:
        args.extend(_parse_command(param_command))
    else:
        raise KeyError('no args nor command defined')

    return action_command(inp, {'args': args})


unaction('command')(reverse_action(action_command))
unaction('ssh')(reverse_action(action_ssh))
unaction('docker')(reverse_action(action_docker))
