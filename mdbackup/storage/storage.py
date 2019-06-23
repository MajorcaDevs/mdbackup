# Small but customizable utility to create backups and store them in
# cloud storage providers
# Copyright (C) 2018  Melchor Alejo Garau Madrigal
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, List


class AbstractStorage(ABC):
    @abstractmethod
    def list_directory(self, path: Union[str, Path]) -> List[str]:
        pass

    @abstractmethod
    def create_folder(self, name: str, parent: Union[Path, str] = None) -> str:
        pass

    @abstractmethod
    def upload(self, path: Path, parent: Union[Path, str, Path] = None):
        pass

    @abstractmethod
    def delete(self, path: Union[Path, str]):
        pass
