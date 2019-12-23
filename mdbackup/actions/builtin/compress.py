import subprocess

from mdbackup.actions.builtin.command import action_command
from mdbackup.actions.container import action, unaction
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


@unaction('compress-xz')
def action_decompress_xz(inp: InputDataStream, params) -> subprocess.Popen:
    cpus = params.get('cpus')

    args = ['xz', '-d']
    if cpus is not None:
        args.extend(['-T', str(cpus)])

    return action_command(inp, {'args': args})


@action('compress-gz', input='stream', output='stream:process')
def action_compress_gzip(inp: InputDataStream, params) -> subprocess.Popen:
    compression_level = params.get('compressionLevel')

    args = ['gzip', '-c']
    if compression_level is not None:
        args.append(f'-{compression_level}')

    return action_command(inp, {'args': args})


@unaction('compress-gz')
def action_decompress_gz(inp: InputDataStream, _) -> subprocess.Popen:
    return action_command(inp, {'args': ['gzip', '-d']})


@action('compress-bz2', input='stream', output='stream:process')
def action_compress_bzip2(inp: InputDataStream, params) -> subprocess.Popen:
    compression_level = params.get('compressionLevel')

    args = ['bzip2', '-z', '-c']
    if compression_level is not None:
        args.append(f'-{compression_level}')

    return action_command(inp, {'args': args})


@unaction('compress-bz2')
def action_decompress_bz2(inp: InputDataStream, _) -> subprocess.Popen:
    return action_command(inp, {'args': ['bzip2', '-d', '-c']})


@action('compress-br', input='stream', output='stream:process')
def action_compress_brotli(inp: InputDataStream, params) -> subprocess.Popen:
    compression_level = params.get('compressionLevel')

    args = ['brotli', '-c']
    if 'compressionLevel' in params:
        args.append(f'-{compression_level}')

    return action_command(inp, {'args': args})


@unaction('compress-br')
def action_decompress_brotli(inp: InputDataStream, _) -> subprocess.Popen:
    return action_command(inp, {'args': ['brotli', '-d', '-c']})


@action('compress-zst', input='stream', output='stream:process')
def action_compress_zstd(inp: InputDataStream, params) -> subprocess.Popen:
    cpus = params.get('cpus')
    compression_level = params.get('compressionLevel')

    args = ['zstd']
    if cpus is not None:
        args.append(f'-T{cpus}')
    if compression_level is not None:
        args.append(f'-{compression_level}')

    return action_command(inp, {'args': args})


@unaction('compress-zst')
def action_decompress_zstd(inp: InputDataStream, params) -> subprocess.Popen:
    cpus = params.get('cpus')

    args = ['zstd', '-d']
    if cpus is not None:
        args.append(f'-T{cpus}')

    return action_command(inp, {'args': args})
