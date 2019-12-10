import base64
from datetime import date
import logging

from mdbackup.actions.builtin._os_utils import _manual_pipe_boilerplate
from mdbackup.actions.builtin.command import action_ssh
from mdbackup.actions.builtin.file import action_read_file_from_ssh
from mdbackup.actions.container import action
from mdbackup.utils import raise_if_type_is_incorrect

try:
    import requests
except ModuleNotFoundError:
    requests = None


@action('mikrotik', output='stream:process')
def action_mikrotik(_, params: dict):
    logger = logging.getLogger(__name__).getChild('action_mikrotik')
    date_str = date.today().isoformat()
    backup_type = params['backupType']

    if backup_type == 'full-backup':
        file_name = f'{params["host"]}-{date_str}-full'
        args = [
            '/system',
            'backup',
            'save',
            f'name={file_name}',
        ]
        file_name += '.backup'
        logger.debug(f'Performing full backup to {file_name}')
    elif backup_type == 'scripts':
        file_name = f'{params["host"]}-{date_str}-scripts'
        args = [
            '/system',
            'script',
            'export',
            f'file={file_name}',
        ]
        file_name += '.rsc'
        logger.debug(f'Performing scripts backup to {file_name}')
    elif backup_type == 'system-config':
        file_name = f'{params["host"]}-{date_str}-sysconf'
        args = [
            '/system',
            'export',
            f'file={file_name}',
        ]
        file_name += '.rsc'
        logger.debug(f'Performing system config backup to {file_name}')
    elif backup_type == 'global-config':
        file_name = f'{params["host"]}-{date_str}-globalconf'
        args = [
            '/export',
            f'file={file_name}',
        ]
        file_name += '.rsc'
        logger.debug(f'Performing global config backup to {file_name}')
    else:
        raise ValueError(f'Unsupported backup type: {backup_type}')

    proc = action_ssh(None, {'args': args, **params})
    stdout, stderr = proc.communicate()
    stdout = stdout.decode('utf-8')[:-1]
    stderr = stderr.decode('utf-8')[:-1]
    proc.wait()
    logger.debug(f'Output of mikrotik backup {proc.returncode}\n{stdout}\n{stderr}')
    if proc.returncode != 0:
        raise ChildProcessError(f'Mikrotik backup failed:\n{stderr}')

    logger.debug('Starting scp copy of file ' + file_name)
    return action_read_file_from_ssh(_, {'path': file_name, **params})


@action('asuswrt', output='stream:file')
def action_asuswrt(_, params: dict):
    logger = logging.getLogger(__name__).getChild('action_asuswrt')
    host = params.get('host', 'router.asus.com')
    user = params['user']
    password = params['password']
    backup_type = params['backupType']
    port = params.get('port')
    secure = params.get('secure', False)
    verify = params.get('verify')

    raise_if_type_is_incorrect(host, str, 'host must be a string')
    raise_if_type_is_incorrect(user, str, 'user must be a string')
    raise_if_type_is_incorrect(password, str, 'password must be a string')
    raise_if_type_is_incorrect(port, int, 'port must be a number')
    raise_if_type_is_incorrect(secure, bool, 'secure must be boolean')
    raise_if_type_is_incorrect(verify, (bool, str), 'verify must be string or boolean')

    if requests is None:
        raise ModuleNotFoundError('requests must be installed in order to use this action')

    base_url = ('https://' if secure else 'http://') + host
    if port is not None:
        base_url += f':{port}'

    if backup_type == 'configuration':
        url = f'{base_url}/Settings_RT-AC68U.CFG?path=1&remove_passwd=0'
    elif backup_type == 'jffs':
        url = f'{base_url}/backup_jffs.tar'
    else:
        raise ValueError(f'Unsupported backup type: {backup_type}')

    s = requests.Session()
    logger.debug(f'Authenticating to router {host}')
    login_data = {
        'group_id': '',
        'action_mode': '',
        'action_script': '',
        'action_wait': '5',
        'current_page': 'Main_Login.asp',
        'next_page': 'index.asp',
        'login_authorization': base64.b64encode(f'{user}:{password}'.encode('utf-8')),
    }
    headers = {
        'Host': host,
        'User-Agent': 'mdbackup via requests (python)',
        'Referer': f'{base_url}/Main_Login.asp',
    }
    res = s.get(f'{base_url}/login.cgi', data=login_data, headers=headers, verify=verify)

    if res.status_code != 200:
        raise PermissionError(f'[{res.status_code}] Authentication failed: {res.text}')

    headers['Referer'] = f'{base_url}/Advanced_SettingBackup_Content.asp'
    res = s.get(url, headers=headers, stream=True, verify=verify)
    if res.status_code != 200:
        raise requests.RequestException(f'Could not download backup {backup_type}', response=res)

    def _pipe_to_fd(out):
        for chunk in res.iter_content(chunk_size=1024):
            out.write(chunk)
        logger.debug('Closing session...')
        res.close()
        out.close()
        s.close()

    return _manual_pipe_boilerplate(_pipe_to_fd, name='asuswrt')
