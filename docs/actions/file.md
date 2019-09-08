# Actions: File

## `from-file`

**Input**: Nothing

**Output**: stream

**Parameters**

Expects a path as string or an object like `{ path: '/path/to/file' }`.

**Description**

Initial action that opens a file to be read from the next actions. The user running the backups must be able to read the file.

!!! Example
    Simple copy (the bad way).

    ```yaml
    - name: from file task example
      actions:
        - from-file: '/path/to/a/file.txt'
        - to-file:
          path: 'file.txt'
    ```


## `from-file-ssh`

**Input**: Nothing

**Output**: stream

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `host` | `str` | Hostname of the host which has an ssh | No |
| `path` | `str` | Path to the remote file to copy | No |
| `user` | `str` | User to be used in the connection | Yes |
| `password` | `str` | Password for the authentication | Yes |
| `port` | `int` | Port of the ssh server | Yes |
| `identityFile` | `str` | Path to an identity file which will be used for authentication | Yes |
| `configFile` | `str` | Path to a ssh client configuration file | Yes |
| `knownHostsPolicy` | `str` | If set to `true`, will ignore unknown hosts errors | Yes |

!!! Warning "Use of password in ssh"
    It is not recommended to use the password authentication method with ssh in scripts like this. If you need the password method, ensure the host (where `mdbackup` runs) has installed `sshpass`.

**Description**

Reads a file from the remote server using `scp`, and the output can be used in other actions as if it were a regular file in the same machine.

!!! Example
    Simple copy using `scp`.

    ```yaml
    - name: from file ssh task example
      actions:
        - from-file-ssh:
            path: '/path/to/a/file/in/the/remote/server/file.txt'
            host: 'my-server'
            identityFile: '/root/.ssh/id_rsa'
        - to-file:
            path: 'file.txt'
    ```


## `to-file`

**Input**: stream

**Output**: Nothing

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `path` | `str` | Path where the file will be written, inside the backup folder | No |
| `mkdirParents` | `bool` | If the path contains some folders and this parameter is set to `true`, then will create the folders | Yes |
| `chunkSize` | `int` | Changes the chunk size to be used internally while reading the data to write (default 8KiB = 8192) | Yes |

**Description**

Writes the data stream into a file, reading chunks of `chunkSize` bytes until end of the stream.

!!! Example
    Simple copy (the bad way), but a bit different.

    ```yaml
    - name: from file task example
      actions:
        - from-file: '/path/to/a/file.txt'
        - to-file:
            path: 'file.txt'
            chunkSize: 65536
    ```


## `copy-file`

**Input**: Nothing

**Output**: Nothing

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `from` | `str` | Path to the file to be copied | No |
| `to` | `str` | Path to where the file will be copied inside the backup folder | No |
| `mkdirParents` | `bool` | If the path contains some folders and this parameter is set to `true`, then will create the folders | Yes |
| `preserveStats` | `Union[bool, str]` | Preserve some or all of the stats of the entry (see [this](../directory#to-directory)) | Yes |
| `forceCopy` | `bool` | If set to `true`, then it will always copy the file and will not try to clone it from a previous backup | Yes |
| `reflink` | `bool` | If set to `true` it will try to make copy of the original file using *Copy on Write* (if the file system supports this - [see `clone-file`](#clone-file)) | Yes |
| `chunkSize` | `int` | The same as in [`to-file`](#to-file) | Yes |

**Description**

Copies a file to the backup folder. It is an optimized version in which the previous backup file is checked in order to clone it (which is faster). In order to make this work, the file must have the `utime` at least in the `preserveStats` parameter (the default). The action will check the modified time of the previous backup version and if they both match, then it will use `clone-file` action. If the modification time is different or `forceCopy` is `true`, then it will make a normal copy using `to-file` action. If the `clone-file` action fails, it will try to make a normal copy using `to-file` action.

!!! Example
    Optimized copy (the right way).

    ```yaml
    - name: copy file task example
      actions:
        - copy-file:
            from: '/path/to/a/file.txt'
            to: 'file.txt'
            preserveStats: True
            reflink: True  # in btrfs, this will make a really fast copy
            chunkSize: 65536
    ```


## `clone-file`

**Input**: Nothing

**Output**: Nothing

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `from` | `str` | Path to the file to be copied | No |
| `to` | `str` | Path to where the file will be copied inside the backup folder | No |
| `mkdirParents` | `bool` | If the path contains some folders and this parameter is set to `true`, then will create the folders | Yes |
| `preserveStats` | `Union[bool, str]` | Preserve some or all of the stats of the entry (see [this](../directory#to-directory)) | Yes |
| `reflink` | `bool` | If set to `true` it will try to make copy of the original file using *Copy on Write* (if the file system supports this) | Yes |

**Description**

Does a "clone" of a file. By default, does a *hard-link* between both files. But if `reflink` is set to `true`, then it will try to make a light copy using [*Copy on Write*][1] (if the file system supports that - only available on Linux). If the CoW fails, then a *hard-link* will be done as fallback.

!!! Warning "About hard-links and CoW"
    For both to work, `from` and `to` paths must be under the same partition. Cross partition hard-links are impossible, as well as CoW copies.

!!! Example
    Clone a file.

    ```yaml
    - name: clone file task example
      actions:
        - clone-file:
            from: '/path/to/a/file.txt'
            to: 'file.txt'
            preserveStats: True
            reflink: True  # in btrfs, this will make a really fast copy
    ```

  [1]: https://en.wikipedia.org/wiki/Copy-on-write
