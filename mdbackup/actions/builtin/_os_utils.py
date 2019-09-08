import logging
import os
from pathlib import Path
from threading import Thread

import xattr

# Portable way to access to these xattr function across linux, macOS, freebsd...
xm = os if hasattr(os, 'listxattr') and hasattr(os, 'getxattr') and hasattr(os, 'setxattr') else xattr


def _preserve_stats(entry_path: Path, stat: os.stat_result, xattrs: dict, mode):
    logger = logging.getLogger(__name__).getChild('_preserve_stats')
    new_mode = stat.st_mode & (os.st.S_IRWXU | os.st.S_IRWXG | os.st.S_IRWXO)
    new_uid = stat.st_uid
    new_gid = stat.st_gid
    new_utime = stat.st_atime_ns, stat.st_mtime_ns

    if mode is True or 'chmod' in mode:
        logger.debug(f'chmod {new_mode} {entry_path}')
        os.lchmod(entry_path, new_mode)
    if mode is True or 'chown' in mode:
        logger.debug(f'chown {new_uid}:{new_gid} {entry_path}')
        os.lchown(entry_path, new_uid, new_gid)
    if mode is True or 'utime' in mode:
        logger.debug(f'utime {new_utime} {entry_path}')
        os.utime(entry_path, ns=new_utime, follow_symlinks=False)
    if (mode is True or 'xattr' in mode) and xattrs is not None:
        existing_xattrs = xm.listxattr(entry_path, symlink=False)
        for xattr_key, xattr_value in xattrs.items():
            xm.setxattr(
                entry_path,
                xattr_key,
                xattr_value,
                xm.XATTR_REPLACE if xattr_key in existing_xattrs else xm.XATTR_CREATE,
            )


def _read_xattrs(path: Path) -> dict:
    return {xattr_key: xm.getxattr(path, xattr_key, symlink=True)
            for xattr_key in xm.listxattr(path, symlink=True)}


def _manual_pipe_boilerplate(action, args=(), name='undefined'):
    read_fd, write_fd = os.pipe()
    write_stream = os.fdopen(write_fd, 'wb', buffering=0, closefd=True)
    p = Thread(target=action, args=(write_stream, *args), name=f'mdbackup-{name}', daemon=True)
    p.start()
    return os.fdopen(read_fd, 'rb', buffering=0, closefd=True)