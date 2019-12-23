import logging
import os
from pathlib import Path

from mdbackup.actions.builtin._os_utils import _preserve_stats
from mdbackup.actions.builtin.command import action_command
from mdbackup.actions.builtin.file import action_copy_file, action_reverse_copy_file
from mdbackup.actions.container import action, unaction
from mdbackup.actions.ds import DirEntry, DirEntryGenerator
from mdbackup.utils import raise_if_type_is_incorrect


def _recurse_dir(path: Path, root_path: Path, resolve_symlinks: bool):
    if path.is_dir():
        if path != root_path:
            yield DirEntry.from_real_path(path, root_path)
        for item in path.iterdir():
            yield from _recurse_dir(item, root_path, resolve_symlinks)
    elif path.is_symlink():
        if resolve_symlinks:
            relative_path = path.relative_to(root_path)
            resolved = path.resolve()
            yield from map(
                lambda entry: DirEntry(entry.type,
                                       relative_path / entry.path,
                                       entry.stats,
                                       stream=entry.stream,
                                       link_content=entry.link_content),
                _recurse_dir(resolved, resolved, True),
            )
        else:
            yield DirEntry.from_real_path(path, root_path)
    elif path.is_file():
        yield DirEntry.from_real_path(path, root_path)
    # Ignore the rest of file types


@action('from-directory', output='directory')
def action_read_dir(_, params: dict):
    root_path = Path(params['path'] if isinstance(params, dict) else params).resolve()
    if not root_path.is_dir():
        raise NotADirectoryError(root_path)

    resolve_symlinks = params.get('resolveSymlinks', False) if isinstance(params, dict) else False
    return _recurse_dir(root_path, root_path, resolve_symlinks=resolve_symlinks)


@unaction('from-directory')
def action_reverse_read_dir(inp, params: dict):
    logger = logging.getLogger(__name__).getChild('action_reverse_read_dir')
    if isinstance(params, str):
        params = {'path': params}
    root_path = Path(params['path'])
    preserve_stats = params.get('preserveStats', 'utime')

    raise_if_type_is_incorrect(preserve_stats, (str, bool), 'preserveStats must be a string or a boolean')
    root_path.mkdir(0o755, parents=True, exist_ok=True)

    for entry in inp:
        entry_path = root_path / entry.path
        if entry.type == 'dir':
            logger.debug(f'Creating directory {entry_path}')
            entry_path.mkdir(0o755, exist_ok=True)
        elif entry.type == 'symlink':
            logger.debug(f'Creating symlink {entry_path} pointing to {entry.link_content}')
            os.symlink(entry.link_content, str(entry_path))
        elif entry.type == 'file':
            logger.debug(f'Creating file {entry_path}')
            action_reverse_copy_file(None, {
                '_stream': entry.stream,
                '_stat': entry.stats,
                '_backup_path': params['_backup_path'],
                'from': entry_path,
                'chunkSize': params.get('chunkSize', 1024 * 8),
                'forceCopy': params.get('forceCopy', False),
                'preserveStats': False,
            })

        if preserve_stats:
            logger.debug(f'Modifying stats of file {entry_path} to match the originals')
            _preserve_stats(entry_path, entry.stats, entry.xattrs, preserve_stats)


def _get_physical_path_to_docker_volume(params: dict):
    logger = logging.getLogger(__name__).getChild('_get_physical_path_to_docker_volume')
    if isinstance(params, str):
        params = {'volume': params}
    volume = params['volume']

    raise_if_type_is_incorrect(volume, str, 'volume must be a string')

    proc = action_command(None, {'command': f'docker volume inspect "{volume}" --format "{{{{.Mountpoint}}}}"'})
    path, error = proc.communicate(None)
    if proc.returncode != 0:
        error_dec = error.decode("utf-8")[:-1]
        logger.error(f'Failed getting volume path with exit code {proc.returncode} and error: {error_dec}')
        raise RuntimeError(f'Get docker volume path failed: {error_dec}')

    path = path.decode('utf-8')[:-1]
    logger.debug(f'Docker volume {volume} has phisical path of {path}')
    return path


@action('from-physical-docker-volume', output='directory')
def action_read_physical_docker_volume(_, params: dict):
    if isinstance(params, str):
        params = {'volume': params}
    params['path'] = _get_physical_path_to_docker_volume(params)
    return action_read_dir(None, params)


@unaction('from-physical-docker-volume')
def action_write_physical_docker_volume(inp, params: dict):
    if isinstance(params, str):
        params = {'volume': params}
    params['path'] = _get_physical_path_to_docker_volume(params)
    return action_reverse_read_dir(inp, params)


@action('to-directory', input='directory')
def action_write_dir(inp: DirEntryGenerator, params: dict):
    logger = logging.getLogger(__name__).getChild('action_write_dir')
    if Path(params['path']).is_absolute():
        raise ValueError('path cannot be absolute')

    backup_path = Path(params['_backup_path'])
    dest_path = Path(params['path'])
    parent = backup_path / dest_path
    preserve_stats = params.get('preserveStats', 'utime')
    parent.mkdir(0o755, parents=params.get('parents', False), exist_ok=True)

    raise_if_type_is_incorrect(preserve_stats, (str, bool), 'preserveStats must be a string or a boolean')

    logger.debug(f'Writing directory generator to {parent}')
    for entry in inp:
        entry_path = parent / entry.path
        if entry.type == 'dir':
            logger.debug(f'Creating directory {entry_path}')
            entry_path.mkdir(0o755, exist_ok=True)
        elif entry.type == 'symlink':
            logger.debug(f'Creating symlink {entry_path} pointing to {entry.link_content}')
            os.symlink(entry.link_content, str(entry_path))
        elif entry.type == 'file':
            logger.debug(f'Creating file {entry_path}')
            action_copy_file(None, {
                '_stream': entry.stream,
                '_stat': entry.stats,
                '_backup_path': params['_backup_path'],
                '_prev_backup_path': params.get('_prev_backup_path'),
                'to': dest_path / entry.path,
                'chunkSize': params.get('chunkSize', 1024 * 8),
                'reflink': params.get('reflink', False),
                'forceCopy': params.get('forceCopy', False),
                'preserveStats': False,
            })

        if preserve_stats:
            logger.debug(f'Modifying stats of file {entry_path} to match the originals')
            _preserve_stats(entry_path, entry.stats, entry.xattrs, preserve_stats)

    return parent


@unaction('to-directory')
def action_reverse_write_dir(_, params: dict):
    backup_path = Path(params['_backup_path'])
    dest_path = Path(params['path'])
    parent = backup_path / dest_path
    return action_read_dir(_, {'path': parent, 'resolveSymlinks': params.get('resolveSymlinks')})


@action('copy-directory')
def action_copy_directory(_, params: dict):
    new_params = params.copy()
    new_params['path'] = params['to']
    return action_write_dir(
        action_read_dir(_, {'path': params['from'], 'resolveSymlinks': params.get('resolveSymlinks')}),
        new_params,
    )


@unaction('copy-directory')
def action_reverse_copy_directory(_, params: dict):
    new_params = params.copy()
    new_params['path'] = params['to']
    return action_reverse_read_dir(
        action_reverse_write_dir(_, new_params),
        {
            'path': params['from'],
            'resolveSymlinks': params.get('resolveSymlinks'),
            '_backup_path': params['_backup_path'],
        },
    )
