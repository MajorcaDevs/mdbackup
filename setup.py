import sys

import setuptools

version = '0.4.4-beta.4'

with open("README.md", "r") as fh:
    long_description = fh.read()

extra_packages = []
if not sys.platform.startswith('linux'):
    extra_packages.append('xattr')

classifiers = [
    "Intended Audience :: System Administrators",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Operating System :: MacOS :: MacOS X",
    "Operating System :: Unix",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Topic :: System :: Recovery Tools",
    "Topic :: Utilities",
]

if '-alpha.' in version:
    classifiers.append('Development Status :: 3 - Alpha')
elif '-beta.' in version:
    classifiers.append('Development Status :: 4 - Beta')
else:
    classifiers.append('Development Status :: 5 - Production/Stable')

setuptools.setup(
    name="mdbackup",
    version=version,
    author="majorcadevs (melchor9000 & amgxv)",
    author_email="melchor9000@gmail.com",
    description="Small but customizable utility to create backups and store them in cloud storage providers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/majorcadevs/mdbackup",
    packages=setuptools.find_packages(
        include=('mdbackup', 'mdbackup.*'),
        exclude=('tests', 'tests.*'),
    ),
    classifiers=classifiers,
    entry_points={
        'console_scripts': [
            'mdbackup = mdbackup.__main__:main',
        ],
    },
    include_package_data=True,
    install_requires=[
        'pyyaml ~= 6.0.0',
        'jsonschema ~= 4.14.0',
        *extra_packages,
    ],
    extras_require={
        'b2': [
            'b2sdk ~= 1.7',
            'python-magic ~= 0.4',
        ],
        'gdrive': [
            'pydrive ~= 1.3',
            'python-magic ~= 0.4',
        ],
        's3': [
            'boto3 ~= 1.24',
            'python-magic ~= 0.4',
        ],
        'sftp': [
            'paramiko ~= 2.11',
        ],
        'vault': [
            'requests ~= 2.28',
        ],
    },
)
