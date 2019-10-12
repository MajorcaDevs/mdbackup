# Actions

An action is a unit of work inside a backup that does one thing. An action can receive data or a folder and/or can produce data or a folder. Depending on the type of input and output, an action can be _initial_, _transformer_ or _final_. By combining actions, a backup can be done (that is, a [task](#)).

An **initial action** is an action that does not receive anything as input and produces an output. These actions must be the first to appear in the task pipeline.

A **transformer action** is an action that receives something as input and applies some transformation on it to produce a different output. These actions must appear in between the task pipeline.

A **final action** is an action taht receives something as input and do not produce an output (for the pipeline). These actions must appear last in the task pipeline. Note that final actions in general produces a file or a folder in the backup folder.

!!! Info "Initial and final actions"
    An action can be initial and final. For example, copy a file or a folder to the backup folder is both initial and final action. If using these kind of actions can only appear one action in a task pipeline.

!!! Info "Initial or transformer actions"
    For example, `command`, `ssh` and `docker` actions can be either an initial or transformer actions, it just depends if the command to run needs an input from another source or not. For example the command `echo hello world` don't need an input, but `cat` needs one.

Not yet mentioned, but **unactions** also exist. Think of *unactions* as a reversed action. If an action is to compress some data, its *unaction* will be decompress the data. *unactions* are like actions in all senses, but the behaviour is to revert an action (in general used in restores).


## Builtin actions

There is a list of builtin actions that can be used to create the tasks pipelines or to create new actions by using these as base actions. The actions are grouped by category. See the list here:

- [Archive](./archive)
- [Command](./command)
- [Compress](./compress)
- [Database](./database)
- [Directory](./directory)
- [Encrypt](./encrypt)
- [File](./file)
- [Network](./network)


## Implementing actions

In python, an action (and *unaction*) is just a function that receives two arguments and returns something. An initial action will receive `None` and the parameters as arguments and should return a data stream or a `DirEntry` iterator. A transformer action will receive a data stream or a `DirEntry` iterator (depending on the expected input) and the parameters as arguments and will return a data stream or a `DirEntry` iterator. A final action will receive a data stream or a `DirEntry` iterator and must return the relative path of the file or folder that the action has created. An action can use another action internally to make a composition of actions.

!!! Info "`DirEntry`"
    Is a data structure used internally to represent a entry of a folder. The object is defined like this:

    ```python
    class DirEntry:
        type: str
        path: Path
        stats: os.stat_result
        stream: Optional[io.IOBase]
        link_content: Optional[str]
        real_path: Optional[Path]

        def __init__(self, _type: str, path: Path, stats, stream=None, link_content=None, real_path=None, **kwargs):
            pass
    ```

In actions, a **data stream** means a `io.FileIO`, `io.BufferedIOBase` or `io.TextIOBase` object that has a file descriptor associated to the stream, or a `subprocess.Popen` object with `PIPE` mode set to `stdout` and `stderr`. Currently, the *file descriptor*-thing is important because they are used to be used in external processes efficently (without using internal pipes). `mdbackup` checks if a data stream is invalid and raises an error for it.

On the other hand, the `DirEntry` iterator is implemented using a generator function that returns `DirEntry` objects for each entry found in the folder. The type of a entry can be `dir`, `symlink` or `file`. A file will have the `stream` attribute filled pointing to the contents of the file.
A symlink will have the `link_content` attribute set with the contents of the symlink. In all types, the `path` must be filled with a relative path to the entry, as well as `stats`, requiring `st_mode`, `st_uid`, `st_gid`, `st_mtime`, `st_size` properties to be filled.

??? Example "Example of initial action"
    ```python
    def action_read_file(_, params: dict) -> io.FileIO:
        return open(params['path'], 'rb', buffering=0)
    ```

??? Example "Example of transform action"
    ```python
    def action_compress_gzip(inp: InputDataStream, params) -> subprocess.Popen:
        compression_level = params.get('compressionLevel')

        args = ['gzip', '-c']
        if compression_level is not None:
            args.append(f'-{compression_level}')

        # Composition of actions: using command action to create the compress-gzip action
        return action_command(inp, {'args': args})

    def action_example_of_dir_entry(inp, params):
        for entry in inp:
            if entry.type == 'file':
                entry.path = Path(str(entry.path) + '.bak')
            yield entry
    ```

??? Example "Example of final action"
    ```python
    def action_write_file(inp: InputDataStream, params):
        # The _backup_path parameter is internal, and can be used freely
        full_path = Path(params['_backup_path']) / Path(params['path'])

        file_object = open(full_path, 'wb', buffering=0)
        chunk_size = params.get('chunkSize', 1024 * 8)
        data = inp.read(chunk_size)
        while data is not None and len(data) != 0:
            file_object.write(data)
            data = inp.read(chunk_size)
        file_object.close()

        return full_path
    ```


## Registring actions

Using the `register_action` function, an action (and its *unaction* counterpart) will be registered in the system and could be used in the tasks. There is also a quick way to register actions and *unactions* which is using the `action` and `unaction` decorators. For user-defined actions, those functions will be received in the function called when registering from a module.

### `register_action`

The function registers an action into the actions container in order to be used when running tasks.

| Argument | Type | Description | Optional | Default |
|----------|------|-------------|----------|---------|
| `identifier` | `str` | Defines the identifier to be used to refer the action in the yaml files | No | |
| `action` | `callable` | The function that implements the action | No | |
| `unaction` | `callable` | The function that implements the *unaction* | Yes | `None` |
| `expected_input` | `Optional[str]` | The expected input for the action | Yes | `None` |
| `output` | `Optional[str]` | The output for the action | Yes | `None` |

The supported values for `expected_input` are: `stream` or `directory`.

The supported values for `output` are: `stream` `stream:file`, `stream:process`, `stream:pipe` (only if using `os.pipe()` fds) or `directory`.

### `action`

Decorator for actions that will register them automatically (once the module that contains the implementation is loaded). Is a shortcut for `register_action` and allows in-place registration of actions.

| Argument | Type | Description | Optional | Default |
|----------|------|-------------|----------|---------|
| `identifier` | `str` | Defines the identifier to be used to refer the action in the yaml files | No | |
| `input` | `Optional[str]` | The expected input for the action | Yes | `None` |
| `output` | `Optional[str]` | The output for the action | Yes | `None` |
| `unaction` | `callable` | The function that implements the *unaction* (use it only if `@unaction()` won't be used) | Yes | `None` |

!!! Note "Parameters"
    `input` is the same as `expected_input` from the `register_action`. All parameters expect the same as in `register_action`.

### `unaction`

Decorator for *unactions* that will register them automatically (once the module that contains the implementation is loaded). Is a shortcut for `register_action` and allows in-place registration of *unactions* once its action counterpart is registered.

| Argument | Type | Description | Optional | Default |
|----------|------|-------------|----------|---------|
| `identifier` | `str` | Defines the identifier to be used to refer the action in the yaml files | No | |

!!! Warning
    An *unaction* can be registered after the action has been registered. If the order is inverted, the *unaction* register will fail.


## Creating user-defined actions

As mentioned in the [configuration](../configuration), the user-defined actions must be modules that can be loaded from python using the `import` syntax. The value in the configuration was `module#function` where `module` is the module to import and `function` is the name of the callable object that will register all actions.

The function (or callable object) will receive some keyword arguments (aka `kwargs`) with the `register_action` function and `action` and `unaction` decorators to be used quickly without the need to import them. You can also import them directly by importing the module `mdbackup.actions.container`. The function will also receive `get_action` and `get_unaction` that retrieves the implementation for the action/*unaction* for the given identifier (the first parameter of both functions). And lastly, the *kwarg* `dir_entry` will be passed with the class `DirEntry` if needed.

The function must register all actions by either using the function or the decorator. If anything fails, your function should raise an exception to notify the failure, and put some `debug` logs will also help.

```python
def register_my_actions(action, unaction, get_action, **kwargs):
    action_ssh = get_action('ssh')

    @action('my-read-file', output='stream:file')
    def action_read_file(_, params: dict):
        return open(params['path'], 'rb', buffering=0)

    @action('pi-copy', output='stream:process')
    def action_pi_copy(_, params: dict):
        return action_ssh(_, {
            'host': 'pi',
            'user': 'pi',
            'password': 'raspberrypi',
            'knownHostsPolicy': 'ignore',  # You should never do this
            'args': ['bash', '-c', f'if [[ -f "{params["path"]}" ]]; then cat "{params["path"]}"; else cd "{params["path"]}"; tar -c .; fi']
        })
```
