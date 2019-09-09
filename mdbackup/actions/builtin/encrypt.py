import subprocess

from mdbackup.actions.builtin.command import action_command
from mdbackup.actions.container import action
from mdbackup.actions.ds import InputDataStream


@action('encrypt-gpg', input='stream', output='stream:process')
def action_encrypt_opengpg(inp: InputDataStream, params) -> subprocess.Popen:
    passphrase = params.get('passphrase')
    recipients: list = params.get('recipients', [])
    algorithm = params.get('algorithm')

    args = ['gpg', '--output', '-', '--batch']
    if passphrase:
        args.extend(['--passphrase', passphrase])
    for recipient in recipients:
        args.extend(['-r', recipient])
    if len(recipients) == 0:
        args.append('--symmetric')
    if algorithm is not None:
        args.extend(['--cipher-algo', algorithm])
    args.append('-')

    return action_command(inp, {'args': args})
