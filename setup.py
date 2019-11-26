import sys

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

extra_packages = []
if not sys.platform.startswith('linux'):
    extra_packages.append('xattr')

setuptools.setup(
    name="mdbackup",
    version="0.4.0-beta.4",
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
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Unix",
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Recovery Tools",
        "Topic :: Utilities",
    ],
    entry_points={
        'console_scripts': [
            'mdbackup = mdbackup.__main__:main',
        ],
    },
    include_package_data=True,
    install_requires=[
        'pyyaml',
        'jsonschema',
        *extra_packages,
    ],
)
