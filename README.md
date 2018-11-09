# Backups utility

Small but customizable utility to create backups and store them in cloud storage providers.

## How to install

Download from releases the latest `wheel` package and install it. It is recommended to use a virtual environment to do that. We will show you this way.

**What do yo need?**:
  - An OS different from Windows (Windows is unsupported) :(
  - Python 3.6 or higher
  - `rsync` and `ssh` installed (on macOS is in general installed by default, on Linux distros you may install them)

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

## Creating the configuration

You have available under `config/config.schema.json` the JSON schema of the configuration file. You can use it like this on an app like Visual Studio code:

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
        "gpg_passphrase": "If set, it will cypher everything with GPG and this value will be used as passphrase",
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
    "providers": [
        {
            "type": "gdrive",
            "backupsPath": "Path in Google Drive where the backups will be located",
            "clientSecrets": "config/client_secrets.json",
            "authTokens": "config/auth_tokens.json"
        }
    ]
}
```

 > If you are going to use the `$schema`, you should download it or reference the URL of the file from the repository directly.

The configuration file must be located in `config/config.json`. It is recommended to put inside `config` folder other configuration files (as API tokens).

### env
This section defines environment variables that will be available when running the steps scripts. It have some predefined (shown before), but you can define whatever more you want.

### Google Drive provider `gdrive`
In case of Google Drive, to gather the `client_secrets.json`, you should get them from the [Google Developer's Console][1], going to _Credentials_ and creating one new _OAuth 2.0 Client IDs_. Every one of them have a download icon, this will download that file.

The `auth_tokens.json` is created when a user logs in. To do that, run the utility manually and (in some point) it will ask you to go to an URL. Here is where you log in with an account and, at the end, Google will give you a token. Copy and paste it into the terminal. Now you will see the files uploading to Google Drive.

The `backupsFolder` **must exist** before running the utility.

## Creating your first steps

The steps are kept in `steps` folder and must be shell scripts. They will be run in alphabetical order one by one, but these scripts are not full scripts. The utility prepares the script with some environment variables and some functions that will be available in the step script. By default, there's some functions (described later) available, but you can add new functions by defining your own script and adding its path to `customUtilsScript` setting.

A simple step script that copies the content of a folder will be this:

`01 - web.sh`

```bash
backup-folder "/var/web/" web || exit $?
```

You can define as many steps as you wish. The idea is to keep every step as simple as possible to simplify debugging.

### Predefined utility functions

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
  - **Description**: Makes a backup of a database in PostgreSQL. By default uses the tools installed in the system, but if `docker` is define in the settings, it will use a docker container. If `gpg_passphrase` is set, the file will be encrypted using GPG and that value as passphrase.
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
  - **Description**: Makes a backup of a database in MySQL/MariaDB. By default uses the tools installed in the system, but if `docker` is define in the settings, it will use a docker container. If `gpg_passphrase` is set, the file will be encrypted using GPG and that value as passphrase.
  - **Parameters**:
     1. Database to backup
  - **Environment variables**:
     - `mysqlnetwork`: (Docker only) Defines in which network the container will be attached. Default is `host`.
     - `mysqlimage`: (Docker only) Defines which image will be used to run the container. Default is `mariadb`.
     - `mysqlhost`: Defines the host where the database is located. Default `localhost`.
     - `mysqluser`: Defines the user from who the connection will be made. Defaults to user that runs the utility.
     - `mysqlpassword`: If set, this password will be used to connect to the database.
  - **Example**: `backup-mysql-database "wordpress"` Will copy the database `wordpress` into a compressed (and maybe encrypted) sql script named the same as the database.

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
