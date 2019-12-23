import logging
import os
from pathlib import Path
from threading import Thread

try:
    import xattr
except ImportError:
    xattr = None


# Portable way to access to these xattr function across linux, macOS, freebsd...
_python_has_xattr_lib = hasattr(os, 'listxattr') and hasattr(os, 'getxattr') and hasattr(os, 'setxattr')


def _listxattr(path, symlink=True):
    if _python_has_xattr_lib:
        return os.listxattr(path, follow_symlinks=symlink)
    else:
        return xattr.listxattr(path, symlink=symlink)


def _getxattr(path, attribute, symlink=True):
    if _python_has_xattr_lib:
        return os.getxattr(path, attribute, follow_symlinks=symlink)
    else:
        return xattr.getxattr(path, attribute, symlink=symlink)


def _setxattr(path, attribute, value, flags=0, symlink=True):
    if _python_has_xattr_lib:
        return os.setxattr(path, attribute, value, flags=flags, follow_symlinks=symlink)
    else:
        return xattr.setxattr(path, attribute, value, options=flags, symlink=symlink)


def _preserve_stats(entry_path: Path, stat: os.stat_result, xattrs: dict, mode):
    logger = logging.getLogger(__name__).getChild('_preserve_stats')
    new_mode = stat.st_mode & (os.st.S_IRWXU | os.st.S_IRWXG | os.st.S_IRWXO)
    new_uid = stat.st_uid
    new_gid = stat.st_gid
    new_utime = stat.st_atime_ns, stat.st_mtime_ns

    if mode is True or 'chmod' in mode:
        if hasattr(os, 'lchmod'):
            logger.debug(f'lchmod {new_mode} {entry_path}')
            os.lchmod(entry_path, new_mode)
        elif not entry_path.is_symlink():
            logger.debug(f'chmod {new_mode} {entry_path}')
            os.chmod(entry_path, new_mode)
        else:
            logger.warn(f'Current platform has no lchmod implemented: symlink {entry_path} will loose the perms')
    if mode is True or 'chown' in mode:
        logger.debug(f'lchown {new_uid}:{new_gid} {entry_path}')
        os.lchown(entry_path, new_uid, new_gid)
    if mode is True or 'utime' in mode:
        logger.debug(f'utime {new_utime} {entry_path}')
        os.utime(entry_path, ns=new_utime, follow_symlinks=False)
    if (mode is True or 'xattr' in mode) and xattrs is not None:
        for xattr_key, xattr_value in xattrs.items():
            logger.debug(f'xattr {xattr_key}:{xattr_value} {entry_path}')
            _setxattr(
                entry_path,
                xattr_key,
                xattr_value,
                symlink=False,
            )


def _read_xattrs(path: Path) -> dict:
    return {xattr_key: _getxattr(path, xattr_key, symlink=True)
            for xattr_key in _listxattr(path, symlink=True)}


def _manual_pipe_boilerplate(action, args=(), name='undefined'):
    read_fd, write_fd = os.pipe()
    write_stream = os.fdopen(write_fd, 'wb', buffering=0, closefd=True)
    p = Thread(target=action, args=(write_stream, *args), name=f'mdbackup-{name}', daemon=True)
    p.start()
    return os.fdopen(read_fd, 'rb', buffering=0, closefd=True)
