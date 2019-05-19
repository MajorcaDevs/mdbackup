# Steps

To make backups, some shell scripts must be create inside the `steps` folder, located in the current working directory `cwd`. They will be run in alphabetical order one by one, but these scripts are not full scripts. The tool prepares the script with some environment variables (based on the configuration, the [env](../configuration.md#env) section and the injected env from the [secret providers](../secrets/index.md)) and some functions that will be available inside the step script. By default, there's some [functions](#function-utilities) available, but you can add new functions by defining your own script and adding its path to `customUtilsScript` setting.

A simple step script that copies the content of a folder will be this:

`01 - web.sh`

```bash
backup-folder "/var/web/" web || exit $?
```

You can define as many steps as you wish. The idea is to keep every step as simple as possible to simplify debugging.

If the `logLevel` is set to `DEBUG` it will log all the output of the scripts. If set to `INFO` part of the output will be logged.

## Function utilities

The steps runs with some function utilities defined that can be used to simplify the backup task. All functions receives parameters via arguments or via environment variables. The environment variables in general are defined by the tool through the configuration and secret providers, but can be overridden in the same script (take care when doing this).

> The environment variables declared in each function must be defined in lowercase in the configuration. Some of the environment variables are defined automatically, it is not a good idea to override them.

### `compress-encrypt`
- **Description**: Executes a command and the output it generates, will apply the compression and encrypt strategies, based on the configuration. If no of them are defined, then the input and output will be the same (won't do anything).
- **Parameters**:
    1. Command to run that will output something
    2. Base file name that will be created
- **Environment variables**:
    - `COMPRESSION_STRATEGY`: Defined by the [compression configuration](../configuration.md#strategy).
    - `COMPRESSION_LEVEL`: Defined by the [compression configuration](../configuration.md#level).
    - `CYPHER_STRATEGY`: Defined by the [cypher configuration](../configuration.md#strategy_1).
    - `CYPHER_KEYS`: Defined by the [cypher configuration](../configuration.md#strategy_1).
    - `CYPHER_PASSPHRASE`: Defined by the [cypher configuration](../configuration.md#strategy_1).
- **Example**: `compress-encrypt "cat /dev/random" "random.bin"`
- **Requirements**:
    - If using the compression strategy `gzip`, `gzip` and `tar` must be installed on the system.
    - If using the compression strategy `xz`, `xz` and `tar` must be installed on the system.
    - If using any cypher strategy, `gpg` (v2.x.x series) must be installed on the system.
    - The receivers used in the `keys` setting must have been imported previously.

### `backup-folder`
- **Description**: Copies a folder to another that will be inside the backup folder, using `rsync`.
- **Parameters**:
    1. Source path of the backup
    2. Name of the folder where will be stored the copy of the source inside the backup folder
    3. **Extra arguments** will be passed to `rsync`
- **Example**: `backup-folder "/var/www/html" my-web` will copy the contents of `/var/www/html` into the folder `.../my-web`.
- **Requirements**:
    - `rsync` must be installed on the system.
    - Uses 

### `backup-remote-folder`
- **Description**: Copies a remote folder to a local folder placed inside the backup folder. Uses `rsync` and `ssh`.

    To make it work, the server that is doing the backup with the user that will do the backups (in general, `root`) must create a pair of public/private keys for ssh (`ssh-keygen -f ~/.ssh/id_rsa -q -P ""` for example). If you already have one, you don't need to create one if your key has no passphrase. When the key is generated, you can copy the public key (`cat ~/.ssh/id_rsa.pub`) and paste it inside the `~/.ssh/authorized_keys` file of the remote server using the same user (generally `root`).

- **Parameters**:
    1. Domain or IP of the remote server
    2. Source path of the backup
    3. Name of the folder where will be stored the copy of the source inside the backup folder
    4. **Extra arguments** will be passed to `rsync`
- **Example**: `backup-remote-folder '10.10.10.254' "/var/lib/unifi/backup/autobackup/" unifi` will copy the contents of `/var/lib/unifi/backup/autobackup/` from the server `10.10.10.254` to the local directory `unifi`.
- **Requirements**:
    - `rsync` must be installed on the system.
    - `ssh` (the client) must be installed on the system.

### `backup-postgres-database`
- **Description**: Makes a backup of a database in PostgreSQL. By default uses the tools installed in the system, but if `docker` is define in the settings, it will use a docker container. Uses the configured compress and cypher strategies to create the backup.
- **Parameters**:
    1. Database to backup
- **Environment variables**:
    - `PGNETWORK`: (Docker only) Defines in which network the container will be attached. Default is `host`.
    - `PGIMAGE`: (Docker only) Defines which image will be used to run the container. Default is `postgres`.
    - `PGHOST`: Defines the host where the database is located. Default `localhost`.
    - `PGUSER`: Defines the user from who the connection will be made. Must be an existing user in the OS. Defaults to `postgres`.
    - `PGPASSWORD`: If set, this password will be used to connect to the database.
- **Example**: `backup-postgres-database "postgres"` Will copy the database `postgres` into a compressed (and maybe encrypted) sql script named the same as the database.
- **Requirements**:
    - If using *Docker*, docker must be installed, and the image must exist. The image must have `pg_dump` installed. The image will be pulled automatically if it is not in the system, but it won't be updated. You can use a [hook](../hooks.md) to do it.
    - If not using *Docker*, `pg_dump` must be installed on the system.
    - Uses [compress-encrypt](#compress-encrypt) internally.

### `backup-mysql-database`
- **Description**: Makes a backup of a database in MySQL/MariaDB. By default uses the tools installed in the system, but if `docker` is define in the settings, it will use a docker container. Uses the configured compress and cypher strategies to create the backup.
- **Parameters**:
    1. Database to backup
- **Environment variables**:
    - `MYSQLNETWORK`: (Docker only) Defines in which network the container will be attached. Default is `host`.
    - `MYSQLIMAGE`: (Docker only) Defines which image will be used to run the container. Default is `mariadb`.
    - `MYSQLHOST`: Defines the host where the database is located. Default `localhost`.
    - `MYSQLUSER`: Defines the user from who the connection will be made. Defaults to user that runs the utility.
    - `MYSQLPASSWORD`: If set, this password will be used to connect to the database.
- **Example**: `backup-mysql-database "wordpress"` Will copy the database `wordpress` into a compressed (and maybe encrypted) sql script named the same as the database.
- **Requirements**:
    - If using *Docker*, docker must be installed, and the image must exist. The image must have `mysqldump` installed and be compatible with the MySQL/MariaDB server. The image will be pulled automatically if it is not in the system, but it won't be updated. You can use a [hook](../hooks.md) to do it.
    - If not using *Docker*, `mysqldump` must be installed on the system and be compatible with the MySQL/MariaDB server.
    - Uses [compress-encrypt](#compress-encrypt) internally.

### `backup-docker-volume`
- **Description**: Makes a backup (in a `.tar` file) of a Docker volume given its name. Uses the configured compress and cypher strategies to create the backup.
- **Parameters**:
    1. Name of the volume to backup
- **Example**: `backup-docker-volume "wordpress-content"`
- **Requirements**:
    - Requires *docker* to be installed and running. Uses `alpine` image to make the copy. The image is pulled automatically, but not updated. To update it, [hooks](../hooks.md) can be used to, or run `docker image pull alpine` before any volume backup.
    - Uses [compress-encrypt](#compress-encrypt) internally.

### `backup-docker-volume-physically`
- **Description**: Makes a backup of a Docker volume given its name copying the folder given in `docker volume inspect` json.
- **Parameters**:
    1. Name of the volume to backup
- **Example**: `backup-docker-volume-physically "wordpress-content"`
    - Requires *docker* to be installed and running.
    - The volume must use the `local` storage, and must be accessible by the tool.
    - Uses [backup-folder](#backup-folder) internally.

### `backup-file`
- **Description**: Makes a backup of a file. Compares with the previous backup to avoid a copy and hard-link with the previous one, or copies it if there are differences..
- **Parameters**:
    1. File to backup
    2. (optional) Folder where to put the file when copying
- **Example**: `backup-file /etc/ssh/sshd sys-config/etc/ssh`

### `backup-file-encrypted`
- **Description**: Makes a backup of a file and compress and encrypts it using the configuration in strategies defined. Compares with the previous backup to avoid a copy and hard-link with the previous one, or copies it if there are differences.
- **Parameters**:
    1. File to backup
    2. (optional) Folder where to put the file when copying
- **Example**: `backup-file-encrypted /etc/ssh/sshd sys-config/etc/ssh`
- **Requirements**:
    - Uses [compress-encrypt](#compress-encrypt) internally.

### `backup-mikrotik`
- **Description**: Makes a backup of a Mikrotik device via SSH. The files will be stored in the device and then downloaded into the local backups folder. To connect to the device, `mikrotiksshkey` or `mikrotikpass` must be defined in order to work.
- **Parameters**:
    1. User of the mikrotik device
    2. Host of the mikrotik device
    3. (Optional) Port to the SSH of the device - by default 22
- **Environment variables**:
    - `MIKROTIKDIR`: (Optional) Folder where to store the backups in local.
    - `MIKROTIKSSHKEY`: (Either) Will use this SSH Identity Key to connect to the device.
    - `MIKROTIKPASS`: (Either) Will use this password to connect to the device (requires `sshpass`).
    - `MIKROTIKFULLBACKUP`: (Optional) If set, will do a full backup.
    - `MIKROTIKEXPORTSCRIPTS`: (Optional) If set, will do a scripts backup.
    - `MIKROTIKEXPORTSYSTEMCONFIG`: (Optional) If set, will do a system config backup.
    - `MIKROTIKEXPORTGLOBALCONFIG`: (Optional) If set, will do a global config backup.
- **Example**: `backup-mikrotik "mdbackup" "192.168.1.1" 2222`
