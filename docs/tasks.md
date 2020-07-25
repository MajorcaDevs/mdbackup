# Tasks

A **task** is a group of [actions](../actions) that conforms a full backup of something (generates a file or a directory in the backup path for the current run). Tasks are defined inside a *tasks definition file* that contains a group of tasks that may share something in common - like all postgres backups will be in a file. The files can be defined using `json` or `yaml` syntax, and are located in the folder `${configPath}/tasks`.


## Tasks definition file

=== "YAML syntax"

    ```yaml
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
        cloud:
          ignore: false
    ```

=== "JSON syntax"

    ```json
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
          ],
          "cloud": {
            "ignore": false
          }
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

Defines variables that can be used in actions as parameters. They can also refer to secrets using `#secret-name`. If a variable matches with a key of a parameter for an action, this will be used as default value if the parameter is not defined in the action. These variables can be referenced inside a string by using `${VARIABLE_NAME}`.

### tasks

Defines all tasks that will be run in this file. One task contains its name and the actions to run. Optionally, it can define more variables in the `env` section. If `stopOnFail` is set to false and the task fails, it won't stop the whole backup. The `cloud` section is optional, and at the moment allows to ignore a task result to be uploaded.

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


## Environment variables in parameters

In the action parameters and the `env` sections, environment variables anv variables defined in `env` sections can be referred to customize even further the tasks. To reference a environment variable, just use it as `${ENV_VAR}` in a string and it will be converted into its value. If a variable cannot be found, it will replace the token with an empty string (just delete the variable token). Variables in `env` sections can reference another variables in the same section because variable substitution is done just before running a task.

!!! Warning "`env` sections and variable substitution"
    Strings and numbers are the only types supported for the variable substitution, any other type of variable will ignore it and a warning will be writen in the logs. When referencing variables from the same `env` section, order is important.


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

??? Example "Referrencing environment variables"
    ```yaml
    tasks:
      - name: do stuff
        env:
          var1: yes
          var2: maybe ${var1}  # This should be defined after var1
        actions:
          - from-directory: '${HOME}/files'
          - tar: {}
          - compress-br: {}
          - to-file:
              path: ${var2}.tar.br

