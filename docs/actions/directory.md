# Actions: Directory

## `from-directory`

**Input**: Nothing

**Output**: directory

**Unaction**: Yes (Only works when using `dictionary` parameter - if using a `string` as parameter the restore will fail).

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `path` | `str` | Path to the directory to read | No |
| `followSymlinks` | `bool` | Follow symbolic links | Yes |

Also a string is accepted as parameter, in this case will be converted to the `path` parameter and `followSymlinks` will be `false`.

**Description**

Reads the contents of the folder to be used in another action. By default, the symlinks are left intact, but if `followSymlinks` is set to `true` then they will be followed and the resolved entry will be read instead.

!!! Example
    Read the folder contents, then archive and compress it into a file.

    ```yaml
    - name: from-directory task example
      actions:
        - from-directory: /var/lib/docker
        - tar: yes
        - compress-gz: {}
        - to-file:
            path: 'dockerino.tar.gz'
    ```


## `from-physical-docker-volume`

**Input**: Nothing

**Output**: directory

**Unaction**: Yes (Only works when using `dictionary` parameter - if using a `string` as parameter the restore will fail).

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `volume` | `str` | Name of the volume to backup | No |
| `followSymlinks` | `bool` | Follow symbolic links | Yes |

Also a string is accepted as parameter, in this case will be converted to the `volume` parameter and `followSymlinks` will be `false`.

**Description**

Determines which is the path to the folder of the desired volume (using `docker volume inspect VOLUME_NAME --format {{.Mountpoint}}` command), and then calls the [`from-directory`](#from-directory) action to perform the read. The path is set automatically to the resolved path from the command.

!!! Warning
    Requires docker to run this action. The user running the backups must have access to the docker socket. Only `local` volume type is supported.

!!! Example
    Read the volume folder contents, then archive and compress it into a file.

    ```yaml
    - name: from-physical-docker-directory task example
      actions:
        - from-physical-docker-directory: docker-volume-name
        - tar: yes
        - compress-gz: {}
        - to-file:
            path: 'dockerino-volumino.tar.gz'
    ```


## `to-directory`

**Input**: directory

**Output**: Nothing

**Unaction**: Yes

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `path` | `str` | Folder to place the folder contents into this path inside the backup folder | No |
| `parents` | `bool` | Create parent folders if they do not exist (when creating the output folder) | Yes |
| `preserveStats` | `Union[bool, str]` | Preserve some or all of the stats of the entry (see description) | Yes |

Also accepts the same parameters of [`copy-file`](../file#copy-file) action, but with the `from` and `to` filled by this action. These settings only apply when a file is being written.

**Description**

Writes the full contents of the folder into the folder defined in `path` (which will be inside the backup folder). The stats of the entries can be preserved in several ways by defining the `preserveStats` property. By default is set to `utime` (see table below for all options). To combine multiple options, use `,` to split them (`chmod,chown,utime`). Writing a file uses the [`copy-file`](../file#copy-file) action, which by default will try to reduce copies if the same file exists in the previous backup and no modification is detected (that is why `preserveStats` is `utime` by default). Can be disabled by setting `forceCopy` to `true`.

| Preserve Stats value | Meaning | Requires root? |
|----------------------|---------|----------------|
| `true` | Preserves all stats | Probably yes |
| `false` | Does not preserve any stats | No |
| `chmod` | Only changes the permissions of the entry | Probably yes |
| `chown` | Changes the UID and GID of the entry | Yes |
| `utime` | Changes the access and modified times | No, if can modify the files |
| `xattrs` | Preserves the extended attributes of the entries | Yes |

!!! Example
    Copy a folder (the explicit way).

    ```yaml
    - name: to-directory task example
      actions:
        - from-directory: /folder/to/copy
        - to-directory:
            path: x-folder
            preserveStats: chmod,chown,utime
            reflink: true
    ```

## `copy-directory`

**Input**: Nothing

**Output**: Nothing

**Unaction**: Yes

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `from` | `str` | `path` parameter for [`from-directory`](#from-directory) action | No |
| `to` | `str` | `path` parameter for [`to-directory`](#from-directory) action | No |

All supported parameters from [`from-directory`](#from-directory) and [`to-directory`](#from-directory) actions are supported. The `path` for both actions are filled from this action parameters (see above table).

**Description**

Shortcut for the example of [`to-directory`](#from-directory). Copies a directory from somewhere to the backup folder using the same functionallity.

!!! Example
    Copy a folder (the good way).

    ```yaml
    - name: copy-directory task example
      actions:
        - copy-directory:
            from: /folder/to/copy
            to: x-folder
            preserveStats: chmod,chown,utime
            reflink: true
    ```
