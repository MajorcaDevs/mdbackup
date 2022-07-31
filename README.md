---
hide:
  - toc
---

# Backups utility

[![PyPI version](https://img.shields.io/pypi/v/mdbackup) ![PyPI downloads](https://img.shields.io/pypi/dw/mdbackup)](https://pypi.org/project/mdbackup/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/MajorcaDevs/mdbackup.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/MajorcaDevs/mdbackup/context:python)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/MajorcaDevs/mdbackup.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/MajorcaDevs/mdbackup/alerts/)
[![Build Status](https://jenkins.majorcadevs.com/buildStatus/icon?job=mdbackup2%2Fmaster&subject=master%20build)](https://jenkins.majorcadevs.com/job/mdbackup2/job/master/)
[![Build Status](https://jenkins.majorcadevs.com/buildStatus/icon?job=mdbackup2%2Fdev&subject=dev%20build)](https://jenkins.majorcadevs.com/job/mdbackup2/job/dev/)

Small but customizable utility to create backups and store them in cloud storage providers.

## How to install

Download from releases the latest `wheel` package and install it. It is recommended to use a virtual environment to do that. We will show you this way.

**What do yo need?**:

  - Any OS with Python support and POSIX-like (e.g.: Linux, macOS, *BSD...)
  - Python 3.6 or higher

First select a folder where all the needed files will be stored. It is important not to move (or rename) this folder after installation.

Run one of those commands. If both fail, try to install `python3-virtualenv` (debian based) or `pip3 install virtualenv` (on macOS).

```bash
python3 -m venv .venv
python3 -m virtualenv .venv
```

When you have the virtual environment created, you have to activate it. With this, you can run python commands and everything you do, will alter the virtual env, not the real one (and so, you don't need `sudo` to do things).

```bash
. .venv/bin/activate
pip install --upgrade setuptools wheel

pip install mdbackup
```

Now you can run the utility (only if you have enabled the virtual env) with `mdbackup`. In this folder it is recommended to store the `config` folder.

 > **Note:** to be able to use some of the cloud storage and secrets backends, you will be requested to install some packages. Go to the documentation to see what is needed.

## Documentation

Can be found at [mdbackup.majorcadevs.com](https://mdbackup.majorcadevs.com/) or at the docs folder.

To make the documentation, install the requirements in `docs/requirements.txt` and run `mkdocs serve`.
