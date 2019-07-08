# Configuration

You have available under `config/config.schema.json` the JSON schema of the configuration file. You can use it like this on an app like Visual Studio Code or PyCharm:

```json
{
    "$schema": "./config.schema.json"
}
```

 > If you are going to use the `$schema`, you should download it or reference the URL of the file from the repository directly.

This allows you to auto-complete with the elements available in the configuration. But in case you cannot use an app with schema support, here's it is the (maybe not updated) list of options:

```json
{
    "backupsPath": "Path where the backups will be stored",
    "logLevel": "Log level for the app, valid values are: CRITICAL,ERROR,WARNING,INFO,DEBUG",
    "customUtilsScript": "(optional) Define an additional utilities script that will be loaded in every step script",
    "maxBackupsKept": 7,
    "env": {
      "docker": "If set, the utilities will run in a docker container instead of using native commands",
      "pgnetwork": "[Docker] Defines which network will use to connect to the database (default host)",
      "pgimage": "[Docker] Defines which image will use to run the container (default postgres)",
      "pghost": "The host of the database (default localhost)",
      "pguser": "The user to connect in the database (must exist)",
      "pgpassword": "If set, will use this as password for connecting to the database",
      "mysqlnetwork": "[Docker] Defines which network will use to connect to the database (default host)",
      "mysqlimage": "[Docker] Defines which image will use to run the container (default mariadb)",
      "mysqlhost": "127.0.0.1",
      "mysqluser": "The username to connect to the database",
      "mysqlpassword": "If defined, sets the password which will be used to connect to the database"
    },
    "secrets": {
      "secret-provider": {
        "env": {
          "pgpassword": "/path/to/pg-password",
          "mysqlpassword": "mysql-password"
        },
        "config": {
          "setting-1": "value",
          "setting-2": true
        },
        "storage": [
          "storage/digital-ocean",
          {
            "key": "storage/gdrive",
            "backupsPath": "/Backups/mbp"
          },
          "storage/amazon"
        ]
      }
    },
    "compression": {
      "strategy": "gzip|xz",
      "level": 8
    },
    "cypher": {
      "strategy": "gpg-keys|gpg-passphrase",
      "passphrase": "If using gpg-passphrase, this will be used as passphrase for the cypher",
      "keys": "If using gpg-keys, this will be used as recipients option for the gpg cypher (emails)",
      "algorithm": "Defines the algorithm to use in the cypher process, depends in the strategy (currently one of `gpg --version` cyphers)"
    },
    "storage": [
      {
        "type": "provider-type-1",
        "backupsPath": "Path in the storage provider where to store the backups",
        "maxBackupsKept": 30,
        "provider-specific-param-1": "config/client_secrets.json",
        "provider-specific-param-2": false
      },
      {
        "type": "provider-type-2",
        "backupsPath": "Path in the storage provider where to store the backups",
        "maxBackupsKept": 7,
        "provider-specific-param-1": "THIS_IS-NOT-AN-API-KEY",
        "provider-specific-param-2": "THIS_IS_NOT_AN-API-S3Cr3t",
        "provider-specific-param-3": 10
      }
    ],
    "hooks": {
      "backup:before": "echo $@",
      "backup:after": "path/to/script",
      "backup:error": "wombo combo $1 $2",
      "upload:before": "echo $@",
      "upload:after": "echo $@",
      "upload:error": "echo $@",
      "oldBackup:deleting": "echo $@",
      "oldBackup:deleted": "echo $@",
      "oldBackup:error": "echo $@"
    }
}
```

The configuration file must be located in `config/config.json`. It is recommended to put inside `config` folder other configuration files (like API tokens) or use a secret provider directly.

## backupsPath

The path where all the backups will be stored locally. It will contain all the past backups plus the in-process (if any).

When a backup is being done, it will create a `.partial` folder inside `backupsPath` and inside the folder, all the copied files and directories will be stored.

After a backup, the folder will be renamed to `YYYY-MM-DDThh:mm`, matching the time when the backup was completed.

## logLevel

Configures the log level. Every log issued to the logger that is below the configured log level will be ignored. By default is set to `INFO`. The available levels, ordered by importance, are:

- `CRITICAL`
- `ERROR`
- `WARNING`
- `INFO`
- `DEBUG`

## customUtilsScript

If defined, this script will be included using `source ${customUtilsScript}` in every [step](steps/index.md). Useful to include custom functions to your flow. The script must be compatible with `bash`.

## maxBackupsKept

Defines how many backups will be kept in the local folder. By default is set to 7. To disable the cleanup, use `0` or `null` as value of this setting.

## env

This section defines environment variables that will be available when running the steps scripts. It have some predefined (see below), but feel free to fill with any variables you want. The values must be string, int, float or bool. Lists and dictionaries will have undesired behaviours when used.

The predefined environment variables, that are used in the predefined functions for the [steps](steps/index.md) are the following:

### docker

_Optional_ If set, some of the function utilities will run in a docker container instead of using native commands.

See their [documentation](steps/index.md) to check which functions can be run inside a container.

### pgnetwork

_Docker, Optional_ Defines which network will use to connect to the PostgreSQL database server (by default `host`).

### pgimage

_Docker, Optional_ Defines which image will use to run the container to connect to PostgreSQL database server (by default `postgres`).

### pghost

_Optional_ The host of the PostgreSQL database server (by default `localhost`).

### pguser

_Optional_ The user to connect to the PostgreSQL server (by default `postgres`).

### pgpassword

_Optional_ If set, will use this as password for connecting to the PostgreSQL server.

### mysqlnetwork

_Docker, Optional_ Defines which network will use to connect to the MySQL/MariaDB database (by default `host`).

### mysqlimage

_Docker, Optional_ Defines which image will use to run the container to connect to the MySQL/MariaDB (default `mariadb`).

### mysqlhost

_Optional_ The host of the MySQL/MariaDB database server (by default `127.0.0.1`).

### mysqluser

_Mandatory_ The username to connect to the MySQL/MariaDB server.

### mysqlpassword

_Mandatory_ If defined, sets the password which will be used to connect to the MySQL/MariaDB server.

### mikrotikdir

_Optional_ Folder name pattern where to store the backups in local for a Mikrotik backup. By default will use `mikrotik-${host}`, where host is the host of the Mikrotik device.

### mikrotiksshkey

_Optional_ If set, will use this SSH Identity Key to connect to the Mikrotik devices.

### mikrotikpass

_Optional_ If set, will use this password to connect to the Mikrotik device (**requires** to have installed `sshpass`).

### mikrotikfullbackup

If set, will do a full backup of the Mikrotik devices.

### mikrotikexportscripts

If set, will do a scripts backup of the Mikrotik devices.

### mikrotikexportsystemconfig

If set, will do a system config backup of the Mikrotik devices.

### mikrotikexportglobalconfig

If set, will do a global config backup of the Mikrotik devices.


## secrets

Defines all secrets providers available to run the tool. Can obtain values for environment and storage providers from the secret providers in runtime, improving security by having in different places all the secrets. It is optional, but it is recommended to use any secret provider.

Every type of secret provider is defined inside the `secrets` section, where the key of the object is the type, and the object contains the configuration of the provider and what to inject from it.

### config

The configuration section contains provider-specific configuration which allows the provider to work. See [secret providers](secrets/index.md) documentation to see the available providers and their configuration.

### env

The environment section defines which environment variables will be populated from the secret provider. The key, like in the [env](#env) section, is the environment variable, and the value is a provider-specific url/path/identifier that tells the provider where to look for the value.

### storage

The storage section defines [storage provider configurations](#storage_1) that will be grabbed from the secret provider. Each value of the list is a (secret) provider-specific url/path/identifier that tells the provider where to look for the configuration. The value must have the same structure of the configuration of the storage provider.

## compression

If defined, some function utilities for the [steps](steps/index.md) will generate a compressed file using the configuration defined in this setting. Also, if the backups are uploaded to a storage provider, folders will be compressed using this configuration.

Can be used with or without [cyphering](#cypher).

### strategy

The strategy defines which compression algorithm is going to be used. Currently, the algorithms supported are `gzip` (which requires `gzip` to be installed) and `xz` (which requires `xz` to be installed).

In general, a lot of Linux distributions includes these commands, as well as in macOS. But it's worth to check their existence before using them.

### level

The compression level. Higher values indicates better but slower compressions. Values accepted for `gzip` are from 1 to 9. Values accepted for `xz` are from 0 to 9 (by default is 6, 7-9 are not recommended).

## cypher

If defined, some function utilities for the [steps](steps/index.md) will generate a encrypted file using the configuration defined in this setting. Also, if the backups are uploaded to a storage provider, folders will be encrypted using this configuration.

Can be used with or without [compression](#compression).

### strategy

Defines which strategy to use to encrypt the data. Currently the supported cypher strategies are:

- `gpg-passphrase` - Uses a passphrase to encrypt and decrypt the data (requires `gpg2`). The `passphrase` setting will be used as passphrase.
- `gpg-keys` - Uses the keys associated to the list of emails to encrypt the data (requires `gpg2`). The `keys` list will be used as recipients/emails list that will be used to protect the data. The people in the list will be able to decrypt the data and no one else. **Recommended over passphrase**.

### algorithm

If defined, will use this algorithm to encrypt the data. The supported algorithms and the default algorithm can be found in `gpg --version` `gpg2 --version`.

## storage

If defined, the last backup will be uploaded to the configured [storage providers](storage/index.md). Each provider must define the `type`, the `backupsPath` and `maxBackupsKept`, as well as the provider specific configuration. Unknown types will be ignored.

### type

Defines the type of the storage provider for the entry. The list of [storage providers](storage/index.md) can be found in the 'Storage providers' section.

### backupsPath

Path in the storage provider where to save the backups. Is the same concept as the [`backupsPath`](#backupspath) from above.

 > Some providers need this folder to exist, while others no. If possible, try to ensure that the folder is created before uploading any backup.

### maxBackupsKept

Defines how many backups will be kept in the storage provider. If set to `0` or `null` will not clean anything. There's no default value for this, so a value must be always provided.

## hooks

Hooks run a script or program when something is going to happen or just happened. Can be useful to trigger some post-action things, to send messages through Slack or to manipulate the output of a backup.

Each key defines the hook type, and their values is the script, program or one-line script that will be run in when the hook is triggered. The hooks run on a `sh` shell, so hooks like `echo $@` will work out of the box.

See [hooks](hooks.md) section.
