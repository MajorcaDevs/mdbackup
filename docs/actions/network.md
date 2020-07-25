# Actions: Network

> Network refers here to network devices like switches, routers, NAS...

!!! warn "Custom CAs in requests"
    By default, the `mdbackup` tool uses the stock Mozilla's CA bundle instead of the system one. If your system has configured custom CA's and want to use them, set this environment variable (Debian/Ubuntu):

    ```sh
    export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    ```

    [See this answer](https://stackoverflow.com/questions/31448854/how-to-force-requests-use-the-certificates-on-my-ubuntu-system#comment78596389_37447847) from StackOverflow...

## `asuswrt`

**Input**: Nothing

**Output**: stream

**Unaction**: No

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `host` | `str` | IP (or hostname) of the Asus router | No |
| `port` | `int` | Port where the http server is listening | Yes |
| `user` | `str` | Router's user | No |
| `password` | `str` | Router's password | No |
| `backupType` | `str` | Type of the backup: `configuration` or `jffs` | No |
| `secure` | `bool` | If set to true, will use `https` instead of `http` | Yes |
| `verify` | `bool | str` | [See this](https://2.python-requests.org/en/master/user/advanced/#ssl-cert-verification) | Yes |

**Description**

Does a backup from an AsusWRT router through its web admin panel. The file is downloaded and piped to the next action.

!!! Warning
    When doing this action, the router cannot have an active session open. The login from the tool can fail if an active session is still open elsewhere.

!!! Warning "requests package required"
    In order to use this action, the `requests` package must be installed manually.

!!! Example
    Backup the jffs partition.

    ```yaml
    - name: asuswrt task example
      actions:
        - asuswrt:
            host: 192.168.1.1
            user: admin
            password: 'WhatPassword?'
            backupType: jffs
        - compress-gz: {}
        - to-file:
            path: 'router/jffs.tar.gz'
    ```

!!! Example
    Backup the configuration.

    ```yaml
    - name: asuswrt task example
      actions:
        - asuswrt:
            host: 192.168.1.1
            user: admin
            password: 'WhatPassword?'
            backupType: configuration
        - to-file:
            path: 'router/asus.cnf'
    ```

!!! Example
    Backup with self-signed certificate and using HTTPS, but not verifying the certificate

    ```yaml
    - name: asuswrt task example
      actions:
        - asuswrt:
            host: 192.168.1.1
            user: admin
            password: 'WhatPassword?'
            backupType: configuration
            secure: true
            verify: false
        - to-file:
            path: 'router/asus.cnf'
    ```


## `mikrotik`

**Input**: Nothing

**Output**: stream

**Unaction**: No

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `backupType` | `str` | Type of the backup (see description) | Yes |

It also accepts any of the parameters of [`ssh`](../command#ssh) and [`from-file-ssh`](../file#from-file-ssh).

!!! Note "Important parameters"
    Even though not all parameters are listed, required parameters are `host`, `user` and either `password` or `identityFile`.

**Description**

Does a backup of a Mikrotik device with RouterOS. The type of backup can be `full-backup`, `scripts`, `system-config` or `global-config`. The action first runs the command to make the backup and then runs the action [`from-file-ssh`](../file#from-file-ssh) which will download the file from the device.

!!! Warning
    The action writes files into the device storage but it does not remove them. They can be removed using a post task hook.

!!! Example
    Full backup of the device.

    ```yaml
    - name: mikrotik task example
      actions:
        - mikrotik:
            host: 192.168.15.1
            user: admin
            password: 'WhatPassword?'
            backupType: full-backup
        - to-file:
            path: 'router/full.backup'
    ```
