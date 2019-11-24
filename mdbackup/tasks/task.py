from typing import Any, Dict, List

from mdbackup.tasks.task_cloud_options import TaskCloudOptions


class Task:
    def __init__(self, task: dict):
        self.__name = task['name']
        self.__env = task.get('env', {})
        self.__actions = task['actions']
        self.__stop_on_fail = task.get('stopOnFail', True)
        self.__cloud = TaskCloudOptions(task.get('cloud', {}))

    @property
    def name(self) -> str:
        return self.__name

    @property
    def env(self):
        return self.__env

    @property
    def actions(self) -> List[Dict[str, Any]]:
        return self.__actions

    @property
    def stop_on_fail(self) -> bool:
        return self.__stop_on_fail

    @property
    def cloud(self) -> TaskCloudOptions:
        return self.__cloud
