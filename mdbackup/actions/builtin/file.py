import fcntl
import io
import logging
import os
from pathlib import Path

from mdbackup.actions.builtin._os_utils import _preserve_stats, _read_xattrs
from mdbackup.actions.builtin.command import action_command
from mdbackup.actions.container import action, unaction
from mdbackup.actions.ds import InputDataStream
from mdbackup.utils import raise_if_type_is_incorrect


@action('from-file', output='stream:file')
def action_read_file(_, params) -> io.FileIO:
    raise_if_type_is_incorrect(params, (dict, str), 'parameters must be a dictionary or an object')
    return open(params['path'] if isinstance(params, dict) else str(params), 'rb', buffering=0)


def _parse_ssh_args(params: dict):
    logger = logging.getLogger(__name__).getChild('action_read_file_from_ssh')
    args = []
    env = {}

    password = params.get('password')
    port = params.get('port')
    known_hosts_policy = params.get('knownHostsPolicy')
    identity_file = params.get('identityFile')
    config_file = params.get('configFile')
    user = params.get('user')

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

    args.append('scp')

    if port is not None:
        args.append('-P', str(port))

    if known_hosts_policy == 'ignore':
        args.extend(['-o', 'UserKnownHostsFile=/dev/null', '-o', 'StrictHostKeyChecking=no'])

    if identity_file is not None:
        args.extend(['-i', identity_file])

    if config_file is not None:
        args.extend(['-F', config_file])

    remote = f"{params['host']}:{params['path']}"
    if user is not None:
        remote = f'{user}@{remote}'

    return args, env, remote


@action('from-file-ssh', output='stream:process')
def action_read_file_from_ssh(_, params):
    args, env, remote = _parse_ssh_args(params)

    args.append(remote)
    args.append('/dev/stdout')
    return action_command(None, {'args': args, 'env': env})


@unaction('from-file-ssh')
def action_write_file_to_ssh(inp: InputDataStream, params):
    args, env, remote = _parse_ssh_args(params)

    args.append('/dev/stdin')
    args.append(remote)
    return action_command(inp, {'args': args, 'env': env})


def _checks(params: dict) -> Path:
    _fp = params.get('path', params.get('to'))
    if _fp is None:
        raise KeyError('to')
    raise_if_type_is_incorrect(_fp, (str, Path), 'to must be a string')

    file_path = Path(_fp)
    full_path = Path(params['_backup_path']) / file_path
    if file_path.is_absolute():
        raise ValueError('Path cannot be absolute')
    if params.get('mkdirParents', False):
        full_path.parent.mkdir(0o755, parents=True, exist_ok=True)
    else:
        if not full_path.parent.exists():
            raise FileNotFoundError('Parent directory does not exist')

    return full_path


def _file_has_changed(entry, old_file: Path) -> bool:
    mod_time_current = entry.st_mtime_ns
    mod_time_prev = old_file.lstat().st_mtime_ns
    return mod_time_current != mod_time_prev


def _write_file(inp: InputDataStream, out, chunk_size):
    raise_if_type_is_incorrect(chunk_size, int, 'chunkSize is not a string')
    data = inp.read(chunk_size)
    while data is not None and len(data) != 0:
        out.write(data)
        data = inp.read(chunk_size)
    out.close()


@action('to-file', input='stream')
def action_write_file(inp: InputDataStream, params):
    full_path = _checks(params)

    file_object = open(full_path, 'wb', buffering=0)
    chunk_size = params.get('chunkSize', 1024 * 8)
    _write_file(inp, file_object, chunk_size)

    return full_path


@unaction('to-file')
def action_reverse_write_file(inp: InputDataStream, params):
    if 'path' not in params:
        params['path'] = params['to']
    params['path'] = Path(params['_backup_path']) / params['path']
    return action_read_file(inp, params)


@unaction('from-file')
def action_reverse_read_file(inp: InputDataStream, params):
    if isinstance(params, str):
        params = {'path': params}
    file_object = open(params['path'], 'wb', buffering=0)
    chunk_size = params.get('chunkSize', 1024 * 8)
    _write_file(inp, file_object, chunk_size)


@action('copy-file')
def action_copy_file(_, params: dict):
    logger = logging.getLogger(__name__).getChild('action_copy_file')
    orig_path = Path(params['from']) if params.get('from') is not None else None
    orig_stream = params.get('_stream')
    orig_stat = orig_path.lstat() if orig_path is not None else params['_stat']
    dest_path = _checks(params)
    in_path = Path(params['to'])
    preserve_stats = params.get('preserveStats', 'utime')

    raise_if_type_is_incorrect(preserve_stats, (str, bool), 'preserveStats must be a string or a boolean')

    avoid_copy = False
    if params.get('_prev_backup_path') is not None and not params.get('forceCopy', False):
        logger.debug('Checking if the file can be cloned from previous backup')
        prev_in_path = Path(params['_prev_backup_path']) / in_path
        avoid_copy = not _file_has_changed(orig_stat, prev_in_path) if prev_in_path.exists() else False

    if avoid_copy:
        try:
            logger.debug(f'Trying to clone {in_path} from previous backup')
            action_clone_file(None, {
                'to': in_path,
                '_backup_path': params['_backup_path'],
                'from': prev_in_path,
                'reflink': params.get('reflink', False),
                'preserveStats': False,
            })
        except OSError:
            logger.debug(f'Could not clone {in_path} from previous backup, normal copy will be done')
            # Probably the clone cannot be done due to hard-link cannot be created
            avoid_copy = False

    if not avoid_copy:
        logger.debug(f'Copying file {orig_path} to {in_path}')
        action_write_file(
            open(orig_path, 'rb', buffering=0) if orig_path is not None else orig_stream,
            {
                '_backup_path': params['_backup_path'],
                'to': in_path,
                'chunkSize': params.get('chunkSize', 1024 * 8),
            },
        )

    if preserve_stats:
        xattrs = _read_xattrs(orig_path) if orig_path is not None else None
        _preserve_stats(dest_path, orig_stat, xattrs, preserve_stats)

    return dest_path


@unaction('copy-file')
def action_reverse_copy_file(_, params: dict):
    logger = logging.getLogger(__name__).getChild('action_reverse_copy_file')
    dest_path = Path(params['from'])
    orig_path = _checks(params) if 'to' in params or 'path' in params else None
    orig_stream = params.get('_stream')
    orig_stat = orig_path.lstat() if orig_path is not None else params['_stat']
    preserve_stats = params.get('preserveStats', 'utime')

    raise_if_type_is_incorrect(preserve_stats, (str, bool), 'preserveStats must be a string or a boolean')

    avoid_copy = False
    if not params.get('forceCopy', False):
        logger.debug('Checking if the file can be needs to be copied')
        avoid_copy = not _file_has_changed(orig_stat, dest_path) if dest_path.exists() else False

    if avoid_copy:
        logger.debug('File will not be copied')
    else:
        logger.debug(f'Copying file {orig_path if orig_path is not None else "*stream*"} to {dest_path}')
        _write_file(
            open(orig_path, 'rb', buffering=0) if orig_path is not None else orig_stream,
            open(dest_path, 'wb', buffering=0),
            params.get('chunkSize', 1024 * 8),
        )

    if preserve_stats:
        xattrs = _read_xattrs(orig_path) if orig_path is not None else None
        _preserve_stats(dest_path, orig_stat, xattrs, preserve_stats)


@action('clone-file')
def action_clone_file(_, params: dict):
    logger = logging.getLogger(__name__).getChild('action_clone_file')
    orig_path = Path(params['from'])
    dest_path = _checks(params)
    preserve_stats = params.get('preserveStats', 'utime')

    raise_if_type_is_incorrect(preserve_stats, (str, bool), 'preserveStats must be a string or a boolean')

    cow_failed = False
    if params.get('reflink', True):
        if os.uname().sysname == 'Linux':
            # Do a Copy on Write clone if possible (only on Linux)
            # https://stackoverflow.com/questions/52766388/how-can-i-use-the-copy-on-write-of-a-btrfs-from-c-code
            # https://github.com/coreutils/coreutils/blob/master/src/copy.c#L370
            if not dest_path.exists():
                dest_path.touch(orig_path.lstat().st_mode)
            src_fd = os.open(orig_path, flags=os.O_RDONLY)
            dst_fd = os.open(dest_path, flags=os.O_WRONLY | os.O_TRUNC)
            try:
                logger.debug(f'Copying using CoW from {orig_path} to {dest_path}')
                fcntl.ioctl(dst_fd, 1074041865, src_fd)  # FICLONE but hardcoded
            except OSError:
                logger.debug('Could not copy using CoW', exc_info=1)
                cow_failed = True
            os.close(src_fd)
            os.close(dst_fd)
            if cow_failed:
                os.unlink(dest_path)

            if preserve_stats:
                xattrs = _read_xattrs(orig_path)
                _preserve_stats(dest_path, orig_path.lstat(), xattrs, preserve_stats)
        else:
            cow_failed = True

    if cow_failed or not params.get('reflink', False):
        # Do a hard-link clone (fallback if CoW fails)
        logger.debug(f'Creating hardlink from {orig_path} to {dest_path}')
        os.link(str(orig_path), str(dest_path))

    return dest_path


@unaction('clone-file')
def action_reverse_clone_file(_, params: dict):
    orig = params['from']
    dest = params.get('path', params.get('to'))
    params['from'] = dest
    params['to'] = orig
    if 'path' in params:
        del params['path']
    return action_clone_file(None, params)
