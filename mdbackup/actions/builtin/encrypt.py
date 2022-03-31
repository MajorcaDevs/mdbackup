import os
import subprocess

from mdbackup.actions.builtin.command import action_command
from mdbackup.actions.container import action, unaction
from mdbackup.actions.ds import InputDataStream
from mdbackup.utils import raise_if_type_is_incorrect


def _configure_passphrase(args, opts, passphrase):
    read_fd, write_fd = os.pipe()
    with os.fdopen(write_fd, 'wb', buffering=0, closefd=True) as write_stream:
        write_stream.write(passphrase.encode('utf-8'))
        write_stream.write(b'\n\n')
    args.extend(['--passphrase-fd', str(read_fd)])
    opts['_pass_fds'] = (read_fd,)


@action('encrypt-gpg', input='stream', output='stream:process')
def action_encrypt_opengpg(inp: InputDataStream, params) -> subprocess.Popen:
    passphrase = params.get('passphrase')
    recipients: list = params.get('recipients', [])
    algorithm = params.get('cipherAlgorithm', params.get('cypherAlgorithm'))
    compress = params.get('compressAlgorithm', None)

    raise_if_type_is_incorrect(passphrase, str, 'passphrase must be a string')
    raise_if_type_is_incorrect(recipients, list, 'recipients must be a list of strings')
    raise_if_type_is_incorrect(algorithm, str, 'cipherAlgorithm must be a string')
    raise_if_type_is_incorrect(compress, str, 'compressAlgorithm must be a string')

    opts = {}
    args = ['gpg', '--output', '-', '--batch']
    if passphrase:
        _configure_passphrase(args, opts, passphrase)
    for recipient in recipients:
        raise_if_type_is_incorrect(recipient, str, f'recipient {recipient} is not a string')
        args.extend(['-r', recipient])
    if len(recipients) == 0:
        args.append('--symmetric')
    if algorithm is not None:
        args.extend(['--cipher-algo', algorithm])
    if isinstance(compress, str):
        args.extend(['--compress-algo', compress])
    else:
        args.extend(['--compress-algo', 'uncompressed'])
    args.append('-')

    return action_command(inp, {**opts, 'args': args})


@unaction('encrypt-gpg')
def action_decrypt_opengpg(inp: InputDataStream, params) -> subprocess.Popen:
    passphrase = params.get('passphrase')
    recipients: list = params.get('recipients', [])

    raise_if_type_is_incorrect(passphrase, str, 'passphrase must be a string')
    raise_if_type_is_incorrect(recipients, list, 'recipients must be a list of strings')

    opts = {}
    args = ['gpg', '--output', '-', '--batch', '-d']
    if passphrase:
        _configure_passphrase(args, opts, passphrase)
    for recipient in recipients:
        raise_if_type_is_incorrect(recipient, str, f'recipient {recipient} is not a string')
        args.extend(['-r', recipient])
    args.append('-')

    return action_command(inp, {**opts, 'args': args})
