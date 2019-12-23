import io
import tarfile

from mdbackup.actions.builtin._os_utils import _manual_pipe_boilerplate
from mdbackup.actions.container import action, unaction
from mdbackup.actions.ds import DirEntry, DirEntryGenerator


@action('tar', input='directory', output='stream:pipe')
def action_tar(inp: DirEntryGenerator, params) -> io.FileIO:
    def action_tar_impl(out):
        tar = tarfile.open(mode='w|', fileobj=out)
        for entry in inp:
            tar_info = tarfile.TarInfo(str(entry.path))
            file_info = entry.stats
            tar_info.mode = file_info.st_mode
            tar_info.uid = file_info.st_uid
            tar_info.gid = file_info.st_gid
            tar_info.mtime = file_info.st_mtime
            if entry.type == 'file':
                tar_info.type = tarfile.REGTYPE
                tar_info.size = file_info.st_size
                tar.addfile(tar_info, entry.stream)
            elif entry.type == 'symlink':
                tar_info.type = tarfile.SYMTYPE
                tar_info.linkname = entry.link_content
                tar.addfile(tar_info)
            elif entry.type == 'dir':
                tar_info.type = tarfile.DIRTYPE
                tar.addfile(tar_info)
        tar.close()
        out.close()

    return _manual_pipe_boilerplate(action_tar_impl, name='tar')


@unaction('tar')
def action_untar(stream, params) -> DirEntryGenerator:
    tar = tarfile.open(mode='r|', fileobj=stream)
    for tar_info in tar:
        tar_info: tarfile.TarInfo
        if tar_info.isdir() or tar_info.islnk() or tar_info.issym():
            yield DirEntry.from_tar_info(tar_info)
        elif tar_info.isreg():
            yield DirEntry.from_tar_info(tar_info, stream=tar.extractfile(tar_info))
    tar.close()
