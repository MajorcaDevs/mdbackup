# Hooks

Hooks are scripts that run when some action is going to happen or just happened. It is useful to define custom actions with your own scripts, including one-liner scrips. The hook is parsed like usual command with arguments, but runs without a shell. The input data is sent through `stdin` as json. If a hook is not defined, won't run anything.

To define the hooks, see [hooks in the configuration](configuration.md#hooks).

The output of the script is redirected to the logger using the `DEBUG` level. If you have some issues with your hook script, set the log level to `DEBUG`.

## backup:pre

- **When**: Before starting doing backups.
- **Object**:
    1. `path`: The folder where the backups are going to be stored during the process (will end with `.partial`).

## backup:post

- **When**: After all backups are done.
- **Object**:
    1. `path`: The folder where the backups are stored.
    2. `created`: an object/dict with keys being the name of each tasks file and their values a list of output files and folders.

## backup:error

- **When**: When the backup process failed but before the partial folder is deleted.
- **Object**:
    1. `path`: The folder where the backups were being stored (just before being deleted).
    2. `message`: Exception message.
    3. `stepName`: (Optional) Step name.

## backup:tasks:pre

- **When**: Before starting running all tasks for a tasks definition file.
- **Object**:
    1. `path`: The folder where the backups are going to be stored during the process (will end with `.partial`).
    2. `tasksName`: The name of the tasks definition.

!!! Note
    This runs for each tasks definition file found. If you want to run something for a specific tasks file, filter by the `tasksName`.

## backup:tasks:post

- **When**: After running all tasks for a tasks definition file.
- **Object**:
    1. `path`: The folder where the backups are going to be stored during the process (will end with `.partial`).
    2. `tasksName`: The name of the tasks definition.
    3. `created`: a list of created files and folders.

!!! Note
    This runs for each tasks definition file found. If you want to run something for a specific tasks file, filter by the `tasksName`.

## backup:tasks:error

- **When**: When one of the tasks failed running and stops the tasks run.
- **Object**:
    1. `message`: The exception message.
    2. `path`: The folder where the backups are going to be stored during the process (will end with `.partial`).
    3. `tasksName`: The name of the tasks definition.

!!! Note
    This runs for each tasks definition file found. If you want to run something for a specific tasks file, filter by the `tasksName`.

## backup:tasks:task:pre

- **When**: Before running a task of a tasks definition.
- **Object**:
    1. `path`: The folder where the backups are going to be stored during the process.
    2. `previousPath`: If any, the path to the previous backup for this task.
    3. `tasksName`: The name of the tasks definition.
    4. `task`: The name of the task.

!!! Note
    This runs for each task that runs the tool.

## backup:tasks:task:post

- **When**: After running a task.
- **Object**:
    1. `path`: The folder where the backups are going to be stored during the process.
    2. `previousPath`: If any, the path to the previous backup for this task.
    3. `tasksName`: The name of the tasks definition.
    4. `task`: The name of the task.
    5. `result`: Path to the file or folder created by the task.

!!! Note
    This runs for each task that runs the tool.

## backup:tasks:${tasks_name}:task:${task_name}:error

- **When**: When a task run has failed, even with `stopOnFail` is set to false.
- **Object**:
    1. `message`: The error message.
    2. `path`: The folder where the backups are going to be stored during the process.
    3. `previousPath`: If any, the path to the previous backup for this task.
    4. `tasksName`: The name of the tasks definition.
    5. `task`: The name of the task.

!!! Note
    This runs for each task that runs the tool.

## upload:pre

- **When**: Before uploading the backup to a storage provider.
- **Object**:
    1. `type`: The type of the provider.
    2. `localPath`: The path to the backup folder (in the local machine).
    3. `remoteBackupsPath`: The path to the cloud backups folder.
    4. `files`: A list of files to upload.

## upload:post

- **When**: After uploading the backup to a storage provider.
- **Object**:
    1. `type`: The type of the provider.
    2. `localPath`: The path to the backup folder (in the local machine).
    3. `remoteBackupsPath`: The path to the cloud backups folder.
    4. `remotePath`: The path where the backups is stored in the cloud.

## upload:error

- **When**: After uploading the backup to a storage provider but it failed.
- **Object**:
    1. `type`: The type of the provider.
    2. `localPath`: The path to the backup folder (in the local machine).
    3. `remoteBackupsPath`: The path to the cloud backups folder.
    4. `remotePath`: (Optional) The path where the backups is stored in the cloud.
    5. `item`: (Optional) The item that was being uploaded.
    6. `message`: The message of the error.

## backup:cleanup:local:pre

- **When**: Just before a backup folder is going to be deleted from the local machine.
- **Object**:
    1. `path`: The path of the backup to be deleted.

## backup:cleanup:local:post

- **When**: After a backup folder is deleted from the local machine.
- **Object**:
    1. `path`: The path of the backup deleted.

## backup:cleanup:local:error

- **When**: After a backup folder was going to be deleted, but it failed to do so.
- **Object**:
    1. `path`: The path of the backup to be deleted.
    2. `message`: The message of the error.

## backup:cleanup:cloud:pre

- **When**: Just before a backup folder is going to be deleted from a cloud storage.
- **Object**:
    1. `path`: The path of the backup to be deleted.
    2. `type`: The type of the cloud storage.
    3. `backupsPath`: The backups path in the cloud storage.

## backup:cleanup:cloud:post

- **When**: After a backup folder is deleted from the cloud storage.
- **Object**:
    1. `path`: The path of the backup deleted.
    2. `type`: The type of the cloud storage.
    3. `backupsPath`: The backups path in the cloud storage.

## backup:cleanup:cloud:error

- **When**: After a backup folder was going to be deleted, but it failed to do so.
- **Object**:
    1. `type`: The type of the cloud storage.
    2. `backupsPath`: The backups path in the cloud storage.
    3. `message`: The message of the error.
