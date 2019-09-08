import fcntl
import io
import logging
import os
from pathlib import Path

from mdbackup.actions.builtin._os_utils import _preserve_stats, _read_xattrs
from mdbackup.actions.builtin.command import action_command
from mdbackup.actions.container import action
from mdbackup.actions.ds import InputDataStream


@action('from-file', output='stream:file')
def action_read_file(_, params) -> io.FileIO:
    return open(params['path'] if isinstance(params, dict) else str(params), 'rb', buffering=0)


@action('from-file-ssh', output='stream:process')
def action_read_file_from_ssh(_, params):
    args = []
    env = {}

    password = params.get('password')
    port = params.get('port')
    known_hosts_policy = params.get('knownHostsPolicy')
    identity_file = params.get('identityFile')
    config_file = params.get('configFile')
    user = params.get('user')

    if password is not None:
        args.extend(['sshpass', '-e'])
        env = {'SSHPASS': password}

    args.append('scp')

    if port is not None:
        args.append('-P', str(port))

    if known_hosts_policy == 'ignore':
        args.extend(['-o', 'UserKnownHostsFile=/dev/null', '-o', 'StrictHostKeyChecking=no'])

    if identity_file is not None:
        args.extend('-i', identity_file)

    if config_file is not None:
        args.extend('-F', config_file)

    args.append(f"{params['host']}:{params['path']}")
    if user is not None:
        args[-1] = f"{user}@{args[-1]}"

    args.append('/dev/stdout')
    return action_command(None, {'args': args, 'env': env})


def _checks(params: dict) -> Path:
    _fp = params.get('path', params.get('to'))
    if _fp is None:
        raise KeyError('to')

    file_path = Path(_fp)
    full_path = Path(params['_backup_path']) / file_path
    if file_path.is_absolute():
        raise ValueError('Path cannot be absolute')
    if params.get('mkdirParents', False):
        full_path.parent().mkdir(0o755, parents=True, exist_ok=True)
    else:
        if not full_path.parent.exists():
            raise FileNotFoundError('Directory does not exist')

    return full_path


def _file_has_changed(entry, old_file: Path) -> bool:
    mod_time_current = entry.st_mtime_ns
    mod_time_prev = old_file.stat().st_mtime_ns
    return mod_time_current != mod_time_prev


@action('to-file', input='stream')
def action_write_file(inp: InputDataStream, params):
    full_path = _checks(params)

    file_object = open(full_path, 'wb', buffering=0)
    chunk_size = params.get('chunkSize', 1024 * 8)
    data = inp.read(chunk_size)
    while data is not None and len(data) != 0:
        file_object.write(data)
        data = inp.read(chunk_size)
    file_object.close()


@action('copy-file')
def action_copy_file(_, params: dict):
    logger = logging.getLogger(__name__).getChild('action_copy_file')
    orig_path = Path(params['from']) if params.get('from') is not None else None
    orig_stream = params.get('_stream')
    orig_stat = orig_path.stat() if orig_path is not None else params['_stat']
    dest_path = _checks(params)
    in_path = Path(params['to'])

    avoid_copy = False
    if params.get('_prev_backup_path') is not None and not params.get('forceCopy', False):
        logger.debug(f'Checking if the file can be cloned from previous backup')
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

    if params.get('preserveStats', 'utime') and orig_path is not None:
        xattrs = _read_xattrs(orig_path)
        _preserve_stats(dest_path, orig_stat, xattrs, params['preserveStats'])


@action('clone-file')
def action_clone_file(_, params: dict):
    logger = logging.getLogger(__name__).getChild('action_clone_file')
    orig_path = Path(params['from'])
    dest_path = _checks(params)

    cow_failed = False
    if params.get('reflink', True):
        if os.uname().sysname == 'Linux':
            # Do a Copy on Write clone if possible (only on Linux)
            # https://stackoverflow.com/questions/52766388/how-can-i-use-the-copy-on-write-of-a-btrfs-from-c-code
            # https://github.com/coreutils/coreutils/blob/master/src/copy.c#L370
            src_fd = os.open(orig_path, flags=os.O_RDONLY)
            dst_fd = os.open(dest_path, dest_path.stat().st_mode, os.O_WRONLY | os.O_TRUNC)
            try:
                logger.debug(f'Copying using CoW from {orig_path} to {dest_path}')
                fcntl.ioctl(dst_fd, fcntl.FICLONE, src_fd)
            except OSError:
                logger.debug('Could not copy using CoW')
                cow_failed = True
            os.close(src_fd)
            os.close(dst_fd)
        else:
            cow_failed = True

    if cow_failed or not params.get('reflink', False):
        # Do a hard-link clone (fallback if CoW fails)
        logger.debug(f'Creating hardlink from {orig_path} to {dest_path}')
        os.link(str(orig_path), str(dest_path))

    if params.get('preserveStats', 'utime'):
        xattrs = _read_xattrs(orig_path)
        _preserve_stats(dest_path, orig_path.stat(), xattrs, params['preserveStats'])