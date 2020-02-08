import io
import os
from pathlib import Path
import subprocess
from typing import Callable, Generator, Optional, Union

from mdbackup.actions.builtin._os_utils import _read_xattrs


class DirEntry:
    stream: Optional[io.IOBase] = None
    link_content: Optional[str] = None
    real_path: Optional[Path] = None
    xattrs: Optional[dict] = None

    def __init__(self, _type: str, path: Path, stats, **kwargs):
        self.type = _type
        self.path = path
        self.stats = stats
        if self.type == 'file':
            self.stream = kwargs['stream']
        elif self.type == 'symlink':
            self.link_content = kwargs['link_content']

        self.real_path = kwargs.get('real_path')
        self.xattrs = kwargs.get('xattrs')

    @staticmethod
    def from_real_path(path: Path, root_path: Optional[Path] = None, **kwargs) -> 'DirEntry':
        stats = path.lstat()
        rel_path = path.relative_to(root_path) if root_path is not None else path
        try:
            xattrs = _read_xattrs(path)
        except (PermissionError, OSError):
            # Extended attributes cannot be read for some good reason
            xattrs = None

        if path.is_dir():
            return DirEntry('dir', rel_path, stats, real_path=path, xattrs=xattrs, **kwargs)
        elif path.is_symlink():
            return DirEntry('symlink',
                            rel_path,
                            stats,
                            link_content=os.readlink(path),
                            real_path=path,
                            xattrs=xattrs,
                            **kwargs)
        elif path.is_file():
            return DirEntry('file',
                            rel_path, stats,
                            stream=open(path, 'rb', buffering=0),
                            real_path=path,
                            xattrs=xattrs,
                            **kwargs)
        else:
            raise TypeError('Expected directory, symlink or file for a path')

    @staticmethod
    def from_tar_info(tar_info, **kwargs) -> 'DirEntry':
        stats = StatResult()
        stats.st_mode = tar_info.mode
        stats.st_uid = tar_info.uid
        stats.st_gid = tar_info.gid
        stats.st_mtime = tar_info.mtime
        stats.st_size = tar_info.size

        if tar_info.isdir():
            stats.st_mode = stats.st_mode | os.st.S_IFDIR
            return DirEntry('dir', tar_info.name, stats, **kwargs)
        elif tar_info.islnk() or tar_info.issym():
            stats.st_mode = stats.st_mode | os.st.S_IFLNK
            return DirEntry('symlink', tar_info.name, stats, link_content=tar_info.linkname, **kwargs)
        elif tar_info.isreg():
            stats.st_mode = stats.st_mode | os.st.S_IFREG
            return DirEntry('file', tar_info.name, stats, **kwargs)
        else:
            raise NotImplementedError('tar_info entry of type ' + tar_info.type)


DirEntryGenerator = Generator[DirEntry, None, None]
OutputDataStream = Union[io.TextIOBase, io.BufferedIOBase, io.FileIO, subprocess.Popen]
InputDataStream = io.FileIO

DataStreamAction = Callable[[dict], OutputDataStream]
DataStreamTransformAction = Callable[[InputDataStream, dict], OutputDataStream]
DataStreamFinalAction = Callable[[InputDataStream, dict], None]
DataStreamToDirEntryTransformAction = Callable[[OutputDataStream, dict], DirEntryGenerator]
DirEntryAction = Callable[[dict], DirEntryGenerator]
DirEntryTransformAction = Callable[[DirEntryGenerator, dict], DirEntryGenerator]
DirEntryToDataStreamTransformAction = Callable[[DirEntryGenerator, dict], OutputDataStream]
DirEntryFinalAction = Callable[[DirEntryGenerator, dict], None]


class StatResult:
    st_mode: int = 0
    st_ino: int = 0
    st_dev: int = 0
    st_nlink: int = 0
    st_uid: int = 0
    st_gid: int = 0
    st_size: int = 0
    st_atime: float = 0.0
    st_mtime: float = 0.0
    st_ctime: float = 0.0
    st_atime_ns: int = 0
    st_mtime_ns: int = 0
    st_ctime_ns: int = 0
