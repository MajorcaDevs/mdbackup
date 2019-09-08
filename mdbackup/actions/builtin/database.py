import logging
from pathlib import Path

from mdbackup.actions.builtin.command import action_command, action_docker
from mdbackup.actions.container import action


def action_psql_command(_, params: dict):
    docker = params.get('docker', False)
    run_as = params.get('runAs')
    if 'command' in params:
        del params['command']

    if docker:
        params['image'] = params.get('image', 'postgres:alpine')
        return action_docker(None, params)
    elif run_as is not None:
        params['args'] = ['sudo', '-u', run_as] + params['args']
        return action_command(None, params)
    else:
        return action_command(None, params)


@action('postgres-database', output='stream:process')
def action_pgdump(_, params: dict):
    pg_user = params.get('user', 'postgres')
    pg_pass = params.get('password')
    pg_host = params.get('host')
    pg_port = params.get('port')
    database = params['database']
    args = ['pg_dump', '-w']

    if pg_host is not None:
        url = f'postgresql://{pg_user}'
        if pg_pass is not None:
            url += f':{pg_pass}'
        url += f'@{pg_host}'
        if pg_port is not None:
            url += f':{str(pg_port)}'
        url += f'/{database}'
        args.append(f'--dbname={url}')
    else:
        if pg_port is not None:
            args.extend(['-p', str(pg_port)])
        args.append(database)

    params['args'] = args
    return action_psql_command(None, params)


def action_mysql_command(_, params: dict):
    docker = params.get('docker', False)
    if 'command' in params:
        del params['command']

    if docker:
        params['image'] = params.get('image', 'mariadb:alpine')
        return action_docker(None, params)
    else:
        return action_command(None, params)


@action('mysql-database', output='stream:process')
def action_mysqldump(_, params: dict):
    host = params['host']
    user = params.get('user')
    password = params.get('password')
    database = params['database']
    port = params.get('port')

    args = ['mysqldump', '-h', host]
    if user is not None:
        args.extend(['-u', user])
    if password is not None:
        params['env'] = {'MYSQL_PWD': password}
        # args.append(f'-p{password}')
    if port is not None:
        args.extend(['--port', str(port)])

    args.append(database)
    params['args'] = args
    return action_mysql_command(None, params)


def action_influxd_command(_, params: dict):
    docker = params.get('docker', False)
    if 'command' in params:
        del params['command']

    if docker:
        params['image'] = params.get('image', 'influxdb:alpine')
        return action_docker(None, params)
    else:
        return action_command(None, params)


@action('influxdb')
def action_influxdb_backup(_, params: dict):
    logger = logging.getLogger(__name__).getChild('action_influxdb_backup')
    to = params['to']
    host = params.get('host')
    database = params.get('database')
    retention = params.get('retention')
    shard = params.get('shard')
    start = params.get('start')
    end = params.get('end')
    backup_path = Path(params['_backup_path'])

    args = ['influxd', 'backup', '-portable']
    if host is not None:
        args.extend(['-host', host])
    if database is not None:
        args.extend(['-database', database])
    if retention is not None:
        args.extend(['-retention', retention])
        if shard is not None:
            args.extend(['-shard', str(shard)])
    if start is not None:
        args.extend(['-start', start])
    if end is not None:
        args.extend(['-end', end])

    args.append(backup_path / to)

    (backup_path / to).mkdir(0o755, parents=True, exit_ok=True)
    proc = action_influxd_command(_, params)
    stdout, stderr = proc.communicate()
    proc.wait()

    logger.debug('influxdb backup has ended, that\'s the output:\n' + stdout.decode('utf-8')[:-1])
    if proc.returncode != 0:
        logger.error(f'Backup failed, process ended with exit code {proc.returncode}')
        raise ChildProcessError(stderr.decode('utf-8')[:-1])
