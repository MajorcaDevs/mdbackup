import itertools
import re
import sys
from typing import Optional, Union


class Version:
    major: int
    minor: int
    patch: int
    extra: Optional[str]

    def __init__(
        self,
        version_string: Union[str, int],
        minor: Optional[int] = None,
        patch: Optional[int] = None,
        extra: Optional[str] = None,
    ):
        super(Version, self).__init__()
        if isinstance(version_string, str):
            match = re.match(r'v?(\d+)\.(\d+)\.(\d+)(?:-(.+))?', version_string)
            self.major = int(match[1])
            self.minor = int(match[2])
            self.patch = int(match[3])
            self.extra = match.group(4)
        else:
            self.major = int(version_string)
            self.minor = int(minor)
            self.patch = int(patch)
            self.extra = extra

    def __str__(self):
        if self.extra:
            return f'{self.major}.{self.minor}.{self.patch}-{self.extra}'
        return f'{self.major}.{self.minor}.{self.patch}'

    def __repr__(self):
        return f'Version({self})'

    def __compare_extra(self, other: 'Version'):
        if self.extra is None and other.extra is None:
            return 0
        if self.extra is None and other.extra is not None:
            return 1
        if self.extra is not None and other.extra is None:
            return -1
        if self.extra < other.extra:
            return -1
        if self.extra == other.extra:
            return 0
        if self.extra > other.extra:
            return 1

    def __lt__(self, other):
        if isinstance(other, Version):
            return (
                    self.major < other.major or
                    (self.major == other.major and self.minor < other.minor) or
                    (self.major == other.major and self.minor == other.minor and self.patch < other.patch) or
                    (self.major == other.major and self.minor == other.minor and self.patch == other.patch and
                     self.__compare_extra(other) <= 0)
            )

        raise TypeError('Expected other to be a Version object')

    def __eq__(self, other):
        if isinstance(other, Version):
            return (self.major == other.major and self.minor == other.minor and self.patch == other.patch and
                    self.__compare_extra(other) == 0)

    def __hash__(self):
        return str(self).__hash__()


versions = [Version(line[:-1]) for line in sys.stdin]
versions.sort()
grouped_versions = [(version, Version(version.major, version.minor, 0)) for version in versions]
grouped_versions = {key: [v for v, _ in values]
                    for key, values in itertools.groupby(grouped_versions, key=lambda x: x[1])}
final_versions = [next(iter(sorted(grouped_versions[key], reverse=True))) for key in sorted(grouped_versions.keys())]
[print(str(final_version)) for final_version in final_versions]
