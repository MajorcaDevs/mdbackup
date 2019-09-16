# Actions: Database

## `postgres-database`

**Input**: Nothing

**Output**: stream

**Parameters**:

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `database` | `str` | Database to connect to and make a backup | No |
| `user` | `str` | User for the database connection | Yes |
| `password` | `str` | Password for the database connection | Yes |
| `host` | `str` | Hostname of the psql server | Yes |
| `port` | `int` | Port of the server | Yes |
| `docker` | `bool` | If set to `true`, will use a container instead of native tools | Yes |
| `runAs` | `str` | If running outside docker, runs the command with `sudo` as the user provided | Yes |
| `image` | `str` | Changes the image to be used in the container | Yes |

When `docker` is `true`, accepts any of the parameters of the [docker](../command#docker) action, except for `args` and `command` which is set automatically by this action.

**Description**

Uses `pg_dump` to make a full backup of a PostgreSQL database into a SQL file. By default uses the local unix socket to connect to the server, but it can be changed by setting the `host` parameter. By default, the tool runs as the current user, but it can be changed by setting the `runAs` parameter to the desired user (useful for unix socket connections). This action requires to have installed `pg_dump` on the host, but to avoid this, docker can be used instead. When using docker, the backup will be done in a container based on the `postgres:alpine` image.

!!! Warning
    If not using docker, `pg_dump` must be installed on the host.

    If using docker, docker must be installed on the host and the user running the backups must have access to the docker socket.

!!! Example
    Simple backup of a database.

    ```yaml
    - name: postgres database task example
      actions:
        - postgres-database:
            database: 'app-database'
        - compress-gz: {}
        - to-file:
            path: 'app-database.sql.gz'
    ```

!!! Example
    Backup using docker to make a backup.

    ```yaml
    - name: postgres database using docker task example
      actions:
        - postgres-database:
            database: 'app-database'
            docker: true
            user: postgres # by default uses this user (just to clarify)
            password: V3ryP0w3rf()lP4ssw0rd # better if secrets is used for this :)
            network: dbs
        - compress-gz: {}
        - to-file:
            path: 'app-database.sql.gz'
    ```


## `mysql-database`

**Input**: Nothing

**Output**: stream

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `host` | `str` | Hostname of the mysql/mariadb server | No |
| `database` | `str` | Database to connect to and make a backup | No |
| `user` | `str` | User for the database connection | Yes |
| `password` | `str` | Password for the database connection | Yes |
| `port` | `int` | Port of the server | Yes |
| `docker` | `bool` | If set to `true`, will use a container instead of native tools | Yes |
| `image` | `str` | Changes the image to be used in the container | Yes |

When `docker` is `true`, accepts any of the parameters of the [docker](../command#docker) action, except for `args` and `command` which is set automatically by this action.

**Description**

Uses `mysqldump` to make a full backup of a MySQL/MariaDB database into a SQL file. By default, uses the current user as login user for the database connection. This action requires to have installed `mysqldump` on the host, but docker can be used to run the tool inside a container. By default uses `mariadb:alpine` image.

!!! Warning
    If not using docker, `mysqldump` must be installed on the host.

    If using docker, docker must be installed on the host and the user running the backups must have access to the docker socket.

!!! Example
    Simple backup of a database.

    ```yaml
    - name: mysql database task example
      actions:
        - mysql-database:
            host: '127.0.0.1'
            user: 'backups'
            password: 'B4ck()psV3ryP0w3rf()lP4ssw0rd' # better if secrets is used for this :)
            database: 'app-database'
        - compress-gz: {}
        - to-file:
            path: 'app-database.sql.gz'
    ```

!!! Example
    Backup using docker to make a backup.

    ```yaml
    - name: mysql database using docker task example
      actions:
        - mysql-database:
            docker: true
            host: '127.0.0.1'
            user: 'backups'
            password: 'B4ck()psV3ryP0w3rf()lP4ssw0rd' # better if secrets is used for this :)
            database: 'app-database'
            image: mysql:alpine
        - compress-gz: {}
        - to-file:
            path: 'app-database.sql.gz'
    ```


## `influxdb`

**Input**: Nothing

**Output**: Nothing

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `host` | `str` | Host:Port to the influxdb server | No |
| `to` | `str` | Folder where to place the backup inside the backup folder | No |
| `database` | `str` | Database to backup (if not set, will backup all databases) | Yes |
| `retention` | `str` | Retention policy for the backup (uses all by default) | Yes |
| `shard` | `str` | If `retention` is defined, will backup the selected shard (by ID) | Yes |
| `start` | `str` | Include all points starting with the specified timestamp ([RFC3339 format][1]) | Yes |
| `end` | `str` | Exclude all points after the specified timestamp ([RFC3339 format][1]) | Yes |
| `docker` | `bool` | If set to `true`, will use a container instead of native tools | Yes |
| `image` | `str` | Changes the image to be used in the container | Yes |

When `docker` is `true`, accepts any of the parameters of the [docker](../command#docker) action, except for `args` and `command` which is set automatically by this action.

**Description**

Uses `influxd` to make a backup of one or all databases into a folder located in the current backup folder. The action requires `influxd` to be installed in the host, or instead docker can be used. Using docker, the `influxdb:alpine` image will be used by default. See <a href="https://docs.influxdata.com/influxdb/v1.7/administration/backup_and_restore/#backup" target="_blank" rel="noreferer">Backup up and restoring in InfluxDB OSS (external)</a> for more details for the parameters.

!!! Warning
    If not using docker, `influxd` must be installed on the host.

    If using docker, docker must be installed on the host and the user running the backups must have access to the docker socket.

!!! Info
    The backups uses the new backup format, which is compatible with the enterprise version of influxdb (`-portable`).

!!! Example
    Simple backup of a database.

    ```yaml
    - name: influxdb database task example
      actions:
        - influxdb:
            to: 'influxdb/netdata'
            host: '127.0.0.1:8088'
            database: 'graphite'
    ```


  [1]: https://www.ietf.org/rfc/rfc3339.txt
