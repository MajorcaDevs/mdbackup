# Actions: Command

## `command`

**Input**: Nothing or stream

**Output**: stream

**Unaction**:

Yes, but to make it work, you need to defined the reverse command. To do so, just define a new section called `reverse` with `args` or `command` (see example below). If trying to do a restore with no `reverse.args` nor `reverse.command` will result in a failure.

**Parameters**

Can be a `str` or an object. The string will be interpreted as a sh-like command, the object with the folliwing structure:

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `args` | `List[str]` | List of arguments (including the program) to run | Yes |
| `command` | `str` | sh-like command string to run | Yes |
| `env` | `Dict[str, str]` | Additional environment variables to set when running the program | Yes |

**Description**

Executes the command that produces an output, and may receive an input. The command can be defined by either using `args` or `command` parameter. If needed, the command can run with extra environment variables defined in the `env` parameter. The current working directory will be the backup path. The parameter can also be a string, in this case will be interpreted as `command` parameter.

!!! Example "Example of command as initial action"
    Does a backup of a partition and then compresses it.

    ```yaml
    - name: command task example
      actions:
        - command: 'cat /dev/mmcblk0p2'
        - compress-xz: {}
        - to-file:
            path: 'full-backup.gz'
    ```

!!! Example "Example of command as transform action"
    Does a backup of a file transforming all instances of `A` to `a` (using `sed`).

    ```yaml
    - name: command task example 2
      actions:
        - from-file: '/path/to/a/file/to/backup.txt'
        - command: 'sed -i "s/A/a/g"'
        - to-file:
            path: 'transformed-backup.txt'
    ```

!!! Example "Example of command with `reverse`"
    Does a backup of some program that exports its data using a CLI tool, but also defining how to restore the data.

    ```yaml
    - name: command task example 3
      actions:
        - command:
            command: 'tool-cli export -'
            reverse:
              command: 'tool-cli import -'
        - compress-zst: {}
        - to-file:
            path: 'tool-data.zst'
    ```


## `ssh`

**Input**: Nothing or stream

**Output**: stream

**Unaction**: See [command](#command) *unaction* section.

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `args` | `List[str]` | List of arguments (including the program) to run | Yes |
| `command` | `str` | sh-like command string to run | Yes |
| `host` | `str` | Hostname to connect to via ssh | No |
| `user` | `str` | Username for the ssh session | Yes |
| `password` | `str` | Password, if required | Yes |
| `port` | `int` | Port of the ssh server | Yes |
| `knownHostsPolicy` | `str` | If set to `ignore`, will ignore any unknown hosts error | Yes |
| `forwardAgent` | `bool` | If set to `true`, will forward the local ssh agent | Yes |
| `identityFile` | `str` | If defined, this identity file will be used | Yes |
| `configFile` | `str` | Defines a custom config file to be used | Yes |

!!! Warning "Use of password in ssh"
    It is not recommended to use the password authentication method with ssh in scripts like this. If you need the password method, ensure the host (where `mdbackup` runs) has installed `sshpass`.

    A properly authentication using ssh is made by configuring an `ssh-agent` before running `mdbackup` with the keys preloaded so the tool can run without issues.

**Description**

Executes the command through ssh, in another host, which must produce an output and it may receive some input. The command can be defined by either using `args` or `command` parameter. The current working directory will be the backup path.

!!! Example
    Does a backup of a file from another server.

    ```yaml
    - name: ssh task example
      actions:
        - ssh:
            host: pi
            user: pi
            identityFile: /path/to/the/pi/identity/file
            args: [ 'cat', '/etc/motd' ]
        - to-file:
            path: 'pi-motd'
    ```


## `docker`

**Input**: Nothing or stream

**Output**: stream

**Unaction**: See [command](#command) *unaction* section.

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `args` | `List[str]` | List of arguments (including the program) to run | Yes |
| `command` | `str` | sh-like command string to run | Yes |
| `image` | `str` | The image to use to run the container | No |
| `env` | `Union[Dict[str, str], List[str]]` | Additional environment variables to set when running the program | Yes |
| `volumes` | `List[str]` | List of volumes defined as `host-path:container-path` or `volume:container-path` | Yes |
| `user` | `Union[str, int]` | UID or user name from which the container will run | Yes |
| `group` | `Union[str, int]` | GID or group name from which the container will run | Yes |
| `network` | `str` | Network to attach to (default is `host`) | Yes |
| `workdir` | `str` | Changes the WorkDir of the container | Yes |
| `pull` | `bool` | Pulls the image before running the container (it can also be used to update the image) | Yes |

**Description**

Executes the command inside a Docker container, in the same host, which must produce an output and it may receive some input. The command can be defined by either using `args` or `command` parameter. If needed, the command can run with extra environment variables defined in the `env` parameter. The `volumes` list uses the same syntax as in docker container run [-v argument][1]. If `pull` is set to true, then the image will be pulled always, and will stop all the pipeline until the image has been pulled.

!!! Example
    Does a backup of a file from a volume.

    ```yaml
    - name: ssh task example
      actions:
        - docker:
            args: [ 'cat', '/data/some/file' ]
            image: alpine
            volumes:
              - my-volume:/data
        - to-file:
            path: 'some-data-from-a-volume.bin'
    ```


 [1]: https://docs.docker.com/storage/volumes/#start-a-container-with-a-volume
