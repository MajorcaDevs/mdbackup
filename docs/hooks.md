# Hooks

Hooks are scripts that run when some event is going to happen or just happened. It is useful to define custom actions with your own scripts, including one-liner scrips. The hook is run with `sh` so scripts can be defined inlined. If a hook is not defined, won't run anything.

To define the hooks, see [hooks in the configuration](configuration.md#hooks).

The output of the script is redirected to the logger using the `DEBUG` level. If you have some issues with your hook script, set the log level to `DEBUG`.

## backup:before

- **When**: Before starting doing backups.
- **Parameters**:
    1. The folder where the backups are going to be stored during the process (will end with `.partial`).

## backup:after

- **When**: After all backups are done.
- **Parameters**:
    1. The folder where the backups are stored.

## backup:error

- **When**: When the backup process failed but before the partial folder is deleted.
- **Parameters**:
    1. The folder where the backups were being stored.
    2. Exception message.
    3. (Optional) Step name.

## backup:tasks:${tasks_name}:before

- **When**: Before starting running all tasks in a tasks definition file.
- **Parameters**:
    1. The folder where the backups are going to be stored during the process (will end with `.partial`).
    2. The name of the tasks definition.

!!! Note
    `${tasks_name}` must be the name of the tasks definition, defined in the `name` section of the file.

## backup:tasks:${tasks_name}:after

- **When**: After running all tasks in a tasks definition file.
- **Parameters**:
    1. The folder where the backups are going to be stored during the process (will end with `.partial`).
    2. The name of the tasks definition.

!!! Note
    `${tasks_name}` must be the name of the tasks definition, defined in the `name` section of the file.

## backup:tasks:${tasks_name}:error

- **When**: When one of the tasks failed running and stops the tasks run.
- **Parameters**:
    1. The exception message.
    2. The folder where the backups are going to be stored during the process (will end with `.partial`).
    3. The name of the tasks definition.

!!! Note
    `${tasks_name}` must be the name of the tasks definition, defined in the `name` section of the file.

## backup:tasks:${tasks_name}:task:${task_name}:before

- **When**: Before running a task.
- **Parameters**:
    1. The folder where the backups are going to be stored during the process.
    2. The name of the tasks definition.
    3. The name of the task.

!!! Note
    `${tasks_name}` must be the name of the tasks definition, defined in the `name` section of the file. The `${task_name}` must be the name of the task, defined in the `name` section of the task.

## backup:tasks:${tasks_name}:task:${task_name}:after

- **When**: After running a task.
- **Parameters**:
    1. The folder where the backups are going to be stored during the process.
    2. The name of the tasks definition.
    3. The name of the task.

!!! Note
    `${tasks_name}` must be the name of the tasks definition, defined in the `name` section of the file. The `${task_name}` must be the name of the task, defined in the `name` section of the task.

## backup:tasks:${tasks_name}:task:${task_name}:error

- **When**: When a task run has failed, even with `stopOnFail` is set to false.
- **Parameters**:
    1. The error message.
    2. The folder where the backups are going to be stored during the process.
    3. The name of the tasks definition.
    4. The name of the task.

!!! Note
    `${tasks_name}` must be the name of the tasks definition, defined in the `name` section of the file. The `${task_name}` must be the name of the task, defined in the `name` section of the task.

## upload:before

- **When**: Before uploading the backup to a storage provider.
- **Parameters**:
    1. The type of the provider.
    2. The path to the backups folder.

## upload:after

- **When**: After uploading the backup to a storage provider.
- **Parameters**:
    1. The type of the provider.
    2. The path to the backups folder.
    3. The path in the storage provider where the backup is stored.

## upload:error

- **When**: After uploading the backup to a storage provider but it failed.
- **Parameters**:
    1. The type of the provider.
    2. The path to the backups folder.
    3. The exception message.

## oldBackup:deleting

- **When**: Just before a backup folder is going to be deleted.
- **Parameters**:
    1. The path of the backup to be deleted.

## oldBackup:deleted

- **When**: After a backup folder was deleted.
- **Parameters**:
    1. The path of the backup deleted.

## oldBackup:error

- **When**: After a backup folder was going to be deleted, but it failed to do so.
- **Parameters**:
    1. The path of the backup to be deleted.
