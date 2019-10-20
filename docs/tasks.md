# Tasks

A **task** is a group of [actions](../actions) that conforms a full backup of something (generates a file or a directory in the backup path for the current run). Tasks are defined inside a *tasks definition file* that contains a group of tasks that may share something in common - like all postgres backups will be in a file. The files can be defined using `json` or `yaml` syntax, and are located in the folder `${configPath}/tasks`.


## Tasks definition file

```yaml tab="YAML syntax"
name: Good name that identifies this group of tasks (optional - file name will be used instead)
env:
  one-variable: 1
  another-variable: true
  101-variable:
    'yes': yes
    'no': no
inside: this/folder
tasks:
  - name: Task 1
    env:
      more-variables: 'yes it is'
    stopOnFail: True
    actions:
      - from-file: /etc/hosts
      - compress-gz: {}
      - to-file:
          path: hosts.gz
```

```json tab="JSON syntax"
{
  "name": "Good name that identifies this group of tasks (optional - file name will be used instead)",
  "env": {
    "one-variable": 1,
    "another-variable": true,
    "101-variable": {
      "yes": true,
      "no": false
    }
  },
  "inside": "this/folder",
  "tasks": [
    {
      "name": "Task 1",
      "env": {
        "more-variables": "yes it is"
      },
      "stopOnFail": false,
      "actions": [
        { "from-file": "/etc/hosts" },
        { "compress-gz": {} },
        {
          "to-file": {
            "path": "hosts.gz"
          }
        }
      ]
    }
  ]
}
```

One file will look like the above example. The example has all possible options that can have. Let's treat each of them.

### Name

The name of the tasks group/tasks definition file. To be able to identify each of them, a name is used. If name is not provided, then it will use the name of the file without extension as name.

### inside

If defined, then all files and directory created by output actions will be stored inside this path in the current backup path.

### env

Defines variables that can be used in actions as parameters. They can also refer to secrets using `#secret-name`.

### tasks

Defines all tasks that will be run in this file. One task contains its name and the actions to run. Optionally, it can define more variables in the `env` section. If `stopOnFail` is set to false and the task fails, it won't stop the whole backup.

The actions are defined with one item in the list by action, and to identify the action, the key of the dictionary is used:

```yaml
- action-name: parameters
- action-name: parameters
```


## Referring to secrets in `env` sections

Every time a variable has a string starting with `#`, those will be treated as secret references. When the task is going to run, the references are resolved with the real values of the secrets. The reference refers to a key path that can be found in a `envDefs` of any of the secret backends. Examples are better:

Imagine that the following secret backend config is set with this `envDefs`:

```yaml
...
    envDefs:
      postgres:
        user: 'secret/databases/postgres/pg-charizard-01#username'
        password: 'secret/databases/postgres/pg-charizard-01#password'
      encrypt-passphrase: 'secret/backups/vm-do-charizard-01/passphrase#passphrase'
...
```

So to refer to the user of postgres, this string will be used `#postgres.user`, as well as the password `#postgres.password`. For the passphrase, `#encrypt-passphrase` will be used.

This way, secrets are referred from the tasks using a key, and changing the path in the `envDefs`, will be changed in all the tasks that references the secret.


## Examples

??? Example "Simple file backup"
    ```yaml
    tasks:
      - name: File copy
        actions:
          - from-file: /path/to/the/file
          - to-file:
              path: file
    ```

??? Example "Run of a command, and the output is stored compressed in a file"
    ```yaml
    tasks:
      - name: Run a command
        actions:
          - command:
            args: [command, parameter, parameter, parameter]
          - compress-xz:
              threads: 2
          - to-file:
              path: compressed-file.xz
    ```

??? Example "Copy a folder"
    ```yaml
    tasks:
      - name: Copy a folder
        actions:
          - from-directory: /path/to/the/folder
          - to-directory:
              path: folder
              reflink: yes
    ```

??? Example "Copy a folder, archive it, compress it, encrypt it and stored it in a file"
    ```yaml
    tasks:
      - name: Do a lot of things with a folder
        actions:
          - from-directory: /path/to/a/folder
          - tar: {}
          - compress-br: {}
          - encrypt-gpg:
              passphrase: '#gpg-password'
          - to-file:
            path: folderino.tar.br.asc
    ```
