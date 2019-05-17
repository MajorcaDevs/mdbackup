# Backups utility

Small but customizable utility to create backups and store them in cloud storage providers.

## How to install

Download from releases the latest `wheel` package and install it. It is recommended to use a virtual environment to do that. We will show you this way.

**What do yo need?**:
  - An OS different from Windows (Windows is unsupported) :(
  - Python 3.6 or higher
  - `rsync` and `ssh` installed (on macOS they are in general installed by default, on Linux distros you may need to install them)
  - `bash` must be installed, used to run the scripts

First select a folder where all the needed files will be stored. It is important not to move (or rename) this folder after installation.

Run one of those commands. If both fail, try to install `python3-virtualenv` (debian based) or `pip3 install virtualenv` (on macOS).

```bash
python3 -m venv .venv
python3 -m virtualenv .venv
```

When you have the virtual environment created, you have to activate it. With this, you can run python commands and everything you do, will alter the virtual env, not the real one (and so, you don't need `sudo` to do things).

```bash
. .venv/bin/activate
# Download the .whl package
pip install --upgrade setuptools wheel
pip install mdbackup*.whl
```

Now you can run the utility (only if you have enabled the virtual env) with `mdbackup`. In this folder it is recommended to store the `config` and `steps` folders.

 > **Note:** to be able to use some of the cloud storages and secrets backends, you will be requested to install some packages.
 > 
 > This is a list of the optional dependencies:
 >  1. `python-magic` (every cloud storage provider needs this) - requires to have installed `libmagic` (C library)
 >  2. `boto3` for S3 cloud storage provider
 >  3. `b2blaze` for BackBlaze cloud storage provider
 >  4. `PyDrive` for Google Drive cloud storage provider
 >  5. `requests` for Vault secrets backend
 >  6. `pyyaml` (optional) for File secrets backend

## Creating the configuration

You have available under `config/config.schema.json` the JSON schema of the configuration file. You can use it like this on an app like Visual Studio Code or PyCharm:

```json
{
    "$schema": "./config.schema.json"
}
```

This allows you to auto-complete with the elements available in the configuration. But in case you cannot use an app with schema support, here's it is the (maybe not updated) list of options:

```json
{
    "backupsPath": "Path where the backups will be stored",
    "logLevel": "Log level for the app, valid values are: CRITICAL,ERROR,WARNING,INFO,DEBUG",
    "customUtilsScript": "(optional) Define an additional utilities script that will be loaded in every step script",
    "maxBackupsKept": 7, //If not defined, by default are 7 backups to keep
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
    "secrets": { //Instead of hardcoding the passwords in the config file, you can get the values from a secret backend
      "file": { //Files that contains the values
        "env": {
          "pgpassword": "/path/to/pg-password", //Absolute path
          "mysqlpassword": "mysql-password" //Relative path
        },
        "config": {
          "basePath": "/backups/secrets" //Optional if all paths are absolute, mandatory if any path is relative
        },
        "providers": [
          "providers/digital-ocean.json", //Must be paths to json files.
          "providers/gdrive.json",        //The files must have the same structure as the provider type.
          "providers/amazon.json"         //See below (in providers section) for the structure of each type.
        ]
      },
      "vault": { //Vault: https://www.vaultproject.io/
        "env": {
          "pguser": "secret/backups/env/pg#user", //First the path (without v1 and initial /), then the key inside the secret
          "pgpassword": "secret/backups/env/pg#password",
          "mysqluser": "secret/backups/env/mysql#user",
          "mysqlpassword": "secret/backups/env/mysql#password"
        },
        "config": {
          "apiBaseUrl": "http://localhost:8200", //API base url
          "roleId": "56c90891-83d5-81da-ac71-02ad8ed7fbfe", //Role ID
          "secretId": "9d261dc7-1bef-5759-6c72-63d57e58ffec", //Secret ID
          "cert": "Path to a certificate bundle or false to disable TLS certificate validation"
        },
        "providers": [
          "secret/backups/providers/digital-ocean", //The secret must have the same structure as the provider type.
          "secret/backups/providers/gdrive",        //See below (in providers section) for the structure of each type.
          "secret/backups/providers/amazon"
        ]
      }
    },
    "compression": {
      "strategy": "gzip|xz",
      "level": 8 //Compression level from 0 to 9
    },
    "cypher": {
      "strategy": "gpg-keys|gpg-passphrase",
      "passphrase": "If using gpg-passphrase, this will be used as passphrase for the cypher",
      "keys": "If using gpg-keys, this will be used as recipients option for the gpg cypher (emails)",
      "algorithm": "Defines the algorithm to use in the cypher process, depends in the strategy (currently one of `gpg --version` cyphers)"
    },
    "providers": [
        {
            "type": "gdrive",
            "backupsPath": "Path in Google Drive where the backups will be located",
            "clientSecrets": "config/client_secrets.json",
            "authTokens": "config/auth_tokens.json"
        },
        {
            "type": "s3",
            "backupsPath": "Path in S3 where the backups will be located",
            "region": "Region of the S3 storage",
            "endpoint": "Endpoint (if not set, uses Amazon S3 endpoint)",
            "accessKeyId": "Access Key ID",
            "accessSecretKey": "Access Secret Key",
            "bucket": "Name of the bucket"
        },
        {
            "type": "b2",
            "backupsPath": "Path in B2 where the backups will be located",
            "keyId": "B2 Key ID",
            "appKey": "B2 Application Key",
            "bucket": "Name of the bucket",
            "password": "(optional) Protects files with passwords"
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

 > If you are going to use the `$schema`, you should download it or reference the URL of the file from the repository directly.

The configuration file must be located in `config/config.json`. It is recommended to put inside `config` folder other configuration files (like API tokens).

### env
This section defines environment variables that will be available when running the steps scripts. It have some predefined (shown before), but you can define whatever more you want.

### Cloud Storage Providers

#### Google Drive `gdrive`

 > In order to use this provider, you must install `PyDrive` and `python-magic`: `pip install PyDrive python-magic`

In case of Google Drive, to gather the `client_secrets.json`, you should get them from the [Google Developer's Console][1], going to _Credentials_ and creating one new _OAuth 2.0 Client IDs_. Every one of them have a download icon, this will download that file.

The `auth_tokens.json` is created when a user logs in. To do that, run the utility manually and (in some point) it will ask you to go to an URL. Here is where you log in with an account and, at the end, Google will give you a token. Copy and paste it into the terminal. Now you will see the files uploading to Google Drive.

The `backupsFolder` **must exist** before running the utility.

#### S3-like `s3`

 > In order to use this provider, you must install `boto3` and `python-magic`: `pip install boto3 python-magic`
 
You can use any S3 compatible cloud storage provider to store the beckups. Fill correctly every parameter of the provider and let the magic happen.

The `backupsPath` in S3 is like a prefix for the file keys. It is recommended to put something here to easily organise the backups from the rest of files in the bucket. The initial slash `/` is removed when uploading the files.

The content type of the files will be guessed and set in the metadata when uploading.

#### BackBlaze `b2`

 > In order to use this provider, you must install `b2blaze` and `python-magic`: `pip install b2blaze python-magic`

The `backupsPath` in S3 is like a prefix for the file keys. It is recommended to put something here to easily organise the backups from the rest of files in the bucket. The initial slash `/` is removed when uploading the files.

The content type of the files will be guessed and set in the metadata when uploading.

### Secrets backends

To improve security, some of the configuration can be retrieved from a secrets backend. To be more precise, some environment variable can be added and cloud providers can also be added from the backends.

 > Google Cloud storage provider should not be used from any secrets backend as it is useless (the backends cannot write data for security reasons)

#### File

This is a simple secrets backend. It is not suitable to use in production, but can be useful to be used in Docker containers.

Every environment variable to inject, will be read from the file specified as value. In fact, every value (which are paths) will be transformed to their values. The paths can be absolute, or relative. To resolve relative paths, you must define `basePath`.

For cloud storage providers, the backend will read json or yaml files, which must have the configuration for a backend. They must use the same structure shown in the providers section of the example json.

 > To be able to read `yaml` files, you must install `pyyaml`: `pip install pyyaml`

#### Vault

Production-ready secrets backend, really useful to have credentials stored in a centralized server, but retrievable from any client in a network.

 > In order to use Vault backend, you must install `requests`: `pip install requests`

Currently, it only supports KV backend for reading secrets.

Environment variables are replaced by their values from the path in the KV. As every path in the KV storage is Key-Value, you must define which key should get to obtain the value. `secrets/backups/env/postgres#user` will retrieve the path `secrets/backups/env/postgres` and key `user`. If the key is not set, will use `vaule` by default.

For cloud storage providers, the KV in the path should contain the same structure as expected in the provider configuration (as seen in the example json). In this case, no key must be defined, it will take the whole path as configuration. 


### Hooks

Hooks are scripts that run when some event is going to happen or just happened. Is useful to define extend the tool with your custom scripts, including one-liner scrips. The hook is run with `sh` so scripts can be defined inlined. If a hook is not defined, won't run anything.

The output of the script is redirected to the logger using the `DEBUG` level. If you have some troubles with your hook script, set the log level to `DEBUG`.

## Creating your first steps

The steps are kept in `steps` folder and must be shell scripts. They will be run in alphabetical order one by one, but these scripts are not full scripts. The utility prepares the script with some environment variables and some functions that will be available in the step script. By default, there's some functions (described later) available, but you can add new functions by defining your own script and adding its path to `customUtilsScript` setting.

A simple step script that copies the content of a folder will be this:

`01 - web.sh`

```bash
backup-folder "/var/web/" web || exit $?
```

You can define as many steps as you wish. The idea is to keep every step as simple as possible to simplify debugging.

### Predefined utility functions

`compress-encrypt`:
 - **Description**: Executes a command and the output it generates, will apply the compression and encription strategies, based on the configuration.
 - **Parameters**:
     1. Command to run that will output something
     2. Base file name that will be created
 - **Example**: `compress-encrypt "cat /dev/random" "random.bin"`

`backup-folder`:
  - **Description**: Copies a folder to another that will be inside the backup folder, using `rsync`.
  - **Parameters**:
     1. Source path of the backup
     2. Name of the folder where will be stored the copy of the source inside the backup folder
     3. **Extra arguments** will be passed to `rsync`
  - **Example**: `backup-folder "/var/www/html" my-web` will copy the contents of `/var/www/html` into the folder `.../web`

`backup-remote-folder`:
  - **Description**: Copies a remote folder to a local folder placed inside the backup folder. Uses `rsync` and `ssh`.

    To make it work, the server that is doing the backup with the user that will do the backups (in general, `root`) must create a pair of public/private keys for ssh (`ssh-keygen -f ~/.ssh/id_rsa -q -P ""` for example). If you already have one, you don't need to create one if your key has no passphrase. When the key is generated, you can copy the public key (`cat ~/.ssh/id_rsa.pub`) and paste it inside the `~/.ssh/authorized_keys` file of the remote server using the same user (generally `root`).
  - **Parameters**:
     1. Domain or IP of the remote server
     2. Source path of the backup
     3. Name of the folder where will be stored the copy of the source inside the backup folder
     4. **Extra arguments** will be passed to `rsync`
  - **Example**: `backup-remote-folder '10.10.10.254' "/var/lib/unifi/backup/autobackup/" unifi` will copy the contents of `/var/lib/unifi/backup/autobackup/` from the server `10.10.10.254` to the local directory `unifi`.

`backup-postgres-database`:
  - **Description**: Makes a backup of a database in PostgreSQL. By default uses the tools installed in the system, but if `docker` is define in the settings, it will use a docker container. Uses the configured compress and cypher strategies to create the backup.
  - **Parameters**:
     1. Database to backup
  - **Environment variables**:
     - `pgnetwork`: (Docker only) Defines in which network the container will be attached. Default is `host`.
     - `pgimage`: (Docker only) Defines which image will be used to run the container. Default is `postgres`.
     - `pghost`: Defines the host where the database is located. Default `localhost`.
     - `pguser`: Defines the user from who the connection will be made. Must be an existing user in the OS. Defaults to `postgres`.
     - `pgpassword`: If set, this password will be used to connect to the database.
  - **Example**: `backup-postgres-database "postgres"` Will copy the database `postgres` into a compressed (and maybe encrypted) sql script named the same as the database.

`backup-mysql-database`:
  - **Description**: Makes a backup of a database in MySQL/MariaDB. By default uses the tools installed in the system, but if `docker` is define in the settings, it will use a docker container. Uses the configured compress and cypher strategies to create the backup.
  - **Parameters**:
     1. Database to backup
  - **Environment variables**:
     - `mysqlnetwork`: (Docker only) Defines in which network the container will be attached. Default is `host`.
     - `mysqlimage`: (Docker only) Defines which image will be used to run the container. Default is `mariadb`.
     - `mysqlhost`: Defines the host where the database is located. Default `localhost`.
     - `mysqluser`: Defines the user from who the connection will be made. Defaults to user that runs the utility.
     - `mysqlpassword`: If set, this password will be used to connect to the database.
  - **Example**: `backup-mysql-database "wordpress"` Will copy the database `wordpress` into a compressed (and maybe encrypted) sql script named the same as the database.

`backup-docker-volume`:
  - **Description**: Makes a backup (in a `.tar` file) of a Docker volume given its name. Uses the configured compress and cypher strategies to create the backup.
  - **Parameters**:
    1. Name of the volume to backup
  - **Example**: `backup-docker-volume "wordpress-content"`

`backup-docker-volume-physically`:
  - **Description**: Makes a backup of a Docker volume given its name copying the folder given in `docker volume inspect` json.
  - **Parameters**:
    1. Name of the volume to backup
  - **Example**: `backup-docker-volume-physically "wordpress-content"`

`backup-file`:
  - **Description**: Makes a backup of a file. Compares with the previous backup to avoid a copy and hard-link with the previous one, or copies it if there are differences.
  - **Parameters**:
    1. File to backup
    2. (optional) Folder where to put the file when copying
  - **Example**: `backup-file /etc/ssh/sshd sys-config/etc/ssh`

`backup-file-encrypted`:
  - **Description**: Makes a backup of a file and compress and encrypts it using the configuration in strategies defined. Compares with the previous backup to avoid a copy and hard-link with the previous one, or copies it if there are differences.
  - **Parameters**:
    1. File to backup
    2. (optional) Folder where to put the file when copying
  - **Example**: `backup-file-encrypted /etc/ssh/sshd sys-config/etc/ssh`

`backup-mikrotik`:
  - **Description**: Makes a backup of a Mikrotik device via SSH. The files will be stored in the device and then downloaded into local.
  - **Parameters**:
    1. User of the mikrotik device
    2. Host of the mikrotik device
    3. (Optional) Port to the SSH of the device - by default 22
  - **Environment variables**:
    - `MIKROTIKDIR`: (Optional) Folder where to store the backups in local
    - `MIKROTIKSSHKEY`: (Either) Will use this SSH Identity Key to connect to the device
    - `MIKROTIKPASS` -> (Either) Will use this password to connect to the device (requires `sshpass`)
    - `MIKROTIKFULLBACKUP` -> (Optional) If set, will do a full backup
    - `MIKROTIKEXPORTSCRIPTS` -> (Optional) If set, will do a scripts backup
    - `MIKROTIKEXPORTSYSTEMCONFIG` -> (Optional) If set, will do a system config backup
    - `MIKROTIKEXPORTGLOBALCONFIG` -> (Optional) If set, will do a global config backup
  - **Example**: `backup-mikrotik "mdbackup" "192.168.1.1" 2222`


## Arguments

The tool has a few arguments, in general you won't use them, but to test some parts, could be really useful.

```
usage: mdbackup [-h] [-c CONFIG] [--backup-only] [--upload-current-only]
                [--cleanup-only]

Small but customizable utility to create backups and store them in cloud
storage providers

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to configuration (default: config/config.json)
  --backup-only         Only does the backup actions
  --upload-current-only
                        Only uploads the last backup
  --cleanup-only        Only does the backup cleanup
```


## Automating running of backups

In this section, systemd and cron ways are going to be explained. systemd is the preferred way in case your system has it.

 > It is supposed you already have configured the environment and it works.

For both ways, download the file [automated-script.sh][2] in some place. In this example, the same folder, where the _venv_, configuration and steps are located, is going to be used.

```bash
curl -sSL https://github.com/MajorcaDevs/mdbackup/raw/master/contrib/automated-script.sh > automated-script.sh
chmod +x automated-script.sh
```

### systemd

For systemd, you need to download [backups.service][3] and [backups.timer][4], copy them to `/etc/systemd/system` and enable the timer.

```
sudo bash -c "curl -sSL https://github.com/MajorcaDevs/mdbackup/raw/master/contrib/backups.service > /etc/systemd/system/backups.service"
sudo bash -c "curl -sSL https://github.com/MajorcaDevs/mdbackup/raw/master/contrib/backups.timer > /etc/systemd/system/backups.timer"
sudo nano /etc/systemd/system/backups.service #Modify the path to the script !!
sudo nano /etc/systemd/system/backups.timer #Check when the timer is going to fire !!
sudo systemctl enable backups.timer
sudo systemctl start backups.timer
nano automated-script.sh #Modify the path of CONFIG_FOLDER
```

You **must** modify the path to the script in the `backups.service` and the `CONFIG_FOLDER` in the `automated-script.sh`. It is recommended to check if you like when the timer is going to fire (by default is every night at 1am).

### crontab

For crontab, you need to edit the `root`s crontab and add a new entry. Also modify the `automated-script.sh` file to remove the comment in the last line to have logs visible in the same folder where the configuration and steps are placed. An example of crontab entry could be:

```
0 1 * * * /backups/tool/automated-script.sh
```

  [1]: https://console.developers.google.com/apis/credentials
  [2]: https://github.com/MajorcaDevs/mdbackup/raw/master/contrib/automated-script.sh
  [3]: https://github.com/MajorcaDevs/mdbackup/raw/master/contrib/backups.service
  [4]: https://github.com/MajorcaDevs/mdbackup/raw/master/contrib/backups.timer
