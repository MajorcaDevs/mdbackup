import functools


def check_b2sdk(package: str):
    try:
        import b2sdk
    except ImportError as e:
        raise ImportError(f'To use {package}, install b2sdk package: pip install b2sdk', e)


def check_boto3(package: str):
    try:
        import boto3
    except ImportError as e:
        raise ImportError(f'To use {package}, you must install boto3: pip install boto3', e)


def check_magic(package: str):
    try:
        import magic
    except ImportError as e:
        raise ImportError(f'To use {package}, you must install python-magic: pip install python-magic', e)


def check_requests(package: str):
    try:
        import requests
    except ImportError as e:
        raise ImportError(f'To use {package}, you must install requests: pip install requests', e)


def check_pydrive(package: str):
    try:
        from pydrive.auth import GoogleAuth
        from pydrive.drive import GoogleDrive, GoogleDriveFile
    except ImportError as e:
        raise ImportError(f'To use {package}, you must install PyDrive: pip install PyDrive', e)


def check_paramiko(package: str):
    try:
        from paramiko import SSHClient
    except ImportError as e:
        raise ImportError(f'To use {package}, you must install paramiko: pip install paramiko', e)


def check(package: str, *funcs):
    def check_dec(func):
        @functools.wraps(func)
        def check_dec_impl(*args, **kwargs):
            [_func(package) for _func in funcs]
            return func(*args, **kwargs)
        return check_dec_impl
    return check_dec
