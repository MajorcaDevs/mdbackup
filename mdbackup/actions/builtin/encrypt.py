import subprocess

from mdbackup.actions.builtin.command import action_command
from mdbackup.actions.container import action, unaction
from mdbackup.actions.ds import InputDataStream
from mdbackup.utils import raise_if_type_is_incorrect


@action('encrypt-gpg', input='stream', output='stream:process')
def action_encrypt_opengpg(inp: InputDataStream, params) -> subprocess.Popen:
    passphrase = params.get('passphrase')
    recipients: list = params.get('recipients', [])
    algorithm = params.get('cipherAlgorithm')
    compress = params.get('compressAlgorithm', False)

    raise_if_type_is_incorrect(passphrase, str, 'passphrase must be a string')
    raise_if_type_is_incorrect(recipients, list, 'recipients must be a list of strings')
    raise_if_type_is_incorrect(algorithm, str, 'cipherAlgorithm must be a string')
    raise_if_type_is_incorrect(compress, str, 'compressAlgorithm must be a string')

    args = ['gpg', '--output', '-', '--batch']
    if passphrase:
        args.extend(['--passphrase', passphrase])
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

    return action_command(inp, {'args': args})


@unaction('encrypt-gpg')
def action_decrypt_opengpg(inp: InputDataStream, params) -> subprocess.Popen:
    passphrase = params.get('passphrase')
    recipients: list = params.get('recipients', [])

    raise_if_type_is_incorrect(passphrase, str, 'passphrase must be a string')
    raise_if_type_is_incorrect(recipients, list, 'recipients must be a list of strings')

    args = ['gpg', '--output', '-', '--batch', '-d']
    if passphrase:
        args.extend(['--passphrase', passphrase])
    for recipient in recipients:
        raise_if_type_is_incorrect(recipient, str, f'recipient {recipient} is not a string')
        args.extend(['-r', recipient])
    args.append('-')

    return action_command(inp, {'args': args})
