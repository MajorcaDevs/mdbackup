class TaskCloudOptions:
    def __init__(self, params):
        self.__ignore = params.get('ignore', False)

    @property
    def ignore(self) -> bool:
        return self.__ignore
