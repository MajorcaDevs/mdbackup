from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from mdbackup.tasks.task import Task
from mdbackup.utils import read_data_file


class Tasks:
    def __init__(self, path: Union[Path, str, bytes]):
        if not isinstance(path, Path):
            path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f'"{path}" must exist')
        if not path.is_file():
            raise IsADirectoryError(f'"{path}" must be a file')

        parsed_tasks = read_data_file(path)
        if parsed_tasks is None:
            raise NotImplementedError(f'Cannot read this type of config file: {self.__file.parts[-1]}')

        self.__path = path
        self.__file_name = Path(path).name
        self.__parse(parsed_tasks, path)

    def __parse(self, tasks: Dict[str, Any], path: Path):
        self.__name = tasks.get('name', '.'.join(path.name.split('.')[:-1]))
        self.__inside_folder = tasks.get('inside')
        self.__env = tasks.get('env', {})
        self.__tasks = []

        for task, i in zip(tasks['tasks'], range(len(tasks['tasks']))):
            try:
                self.__tasks.append(Task(task))
            except KeyError as e:
                task_name = task.get('name', f'#{i}')
                raise KeyError(f'{e.args[0]} - on task {task_name}')

        task_names = list(map(lambda task: task.name, self.__tasks))
        for task_name in task_names:
            if task_names.count(task_name) > 1:
                raise ValueError(f'Task name "{task_name}" is repeated, tasks cannot have duplicated names')

    @property
    def file_name(self) -> str:
        return self.__file_name

    @property
    def name(self) -> str:
        return self.__name

    @property
    def inside_folder(self) -> Optional[str]:
        return self.__inside_folder

    @property
    def env(self) -> Dict[str, Any]:
        return self.__env

    @property
    def tasks(self) -> List[Task]:
        return self.__tasks
