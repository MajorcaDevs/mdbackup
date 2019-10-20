import subprocess

from mdbackup.actions.builtin.command import action_command
from mdbackup.actions.container import action
from mdbackup.actions.ds import InputDataStream


@action('compress-xz', input='stream', output='stream:process')
def action_compress_xz(inp: InputDataStream, params) -> subprocess.Popen:
    cpus = params.get('cpus')
    compression_level = params.get('compressionLevel')
    extra_compression = params.get('extraCompression', False)

    args = ['xz', '-z']
    if cpus is not None:
        args.extend(['-T', str(cpus)])
    if compression_level is not None:
        if extra_compression:
            args.append(f'-{compression_level}e')
        else:
            args.append(f'-{compression_level}')

    return action_command(inp, {'args': args})


@action('compress-gz', input='stream', output='stream:process')
def action_compress_gzip(inp: InputDataStream, params) -> subprocess.Popen:
    compression_level = params.get('compressionLevel')

    args = ['gzip', '-c']
    if compression_level is not None:
        args.append(f'-{compression_level}')

    return action_command(inp, {'args': args})


@action('compress-bz2', input='stream', output='stream:process')
def action_compress_bzip2(inp: InputDataStream, params) -> subprocess.Popen:
    compression_level = params.get('compressionLevel')

    args = ['bzip2', '-z', '-c']
    if compression_level is not None:
        args.append(f'-{compression_level}')

    return action_command(inp, {'args': args})


@action('compress-br', input='stream', output='stream:process')
def action_compress_brotli(inp: InputDataStream, params) -> subprocess.Popen:
    compression_level = params.get('compressionLevel')

    args = ['brotli', '-c']
    if 'compressionLevel' in params:
        args.append(f'-{compression_level}')

    return action_command(inp, {'args': args})
