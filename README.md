# Backups utility

Small but customizable utility to create backups and store them in cloud storage providers.

## How to install

Download from releases the latest `wheel` package and install it. It is recommended to use a virtual environment to do that. We will show you this way.

**What do yo need?**:

  - An OS different from Windows (Windows is unsupported) :(
  - Python 3.6 or higher
  - `rsync` and `ssh` installed (on macOS they are in general installed by default, on Linux distros you may need to install them)
  - `bash` must be installed, used to run the scripts

First select a folder where all the needed files will be stored. It is important not to move (or rename) this folder after installation.

Run one of those commands. If both fail, try to install `python3-virtualenv` (debian based) or `pip3 install virtualenv` (on macOS).

```bash
python3 -m venv .venv
python3 -m virtualenv .venv
```

When you have the virtual environment created, you have to activate it. With this, you can run python commands and everything you do, will alter the virtual env, not the real one (and so, you don't need `sudo` to do things).

```bash
. .venv/bin/activate
# Download the .whl package
pip install --upgrade setuptools wheel
pip install mdbackup*.whl
```

Now you can run the utility (only if you have enabled the virtual env) with `mdbackup`. In this folder it is recommended to store the `config` and `steps` folders.

 > **Note:** to be able to use some of the cloud storage and secrets backends, you will be requested to install some packages. Go to the documentation to see what is needed.

## Documentation

Can be found at docs folder.

To make the documentation, install the requirements in `docs/requirements.txt` and run `mkdocs build --config-file=mkdocs.yaml`.
