# Quick start guide

> `mdbackup` is tested under Linux and macOS, but it should work on any platform where Python has support and has `bash`, except for Windows.

Before installing the tool, make sure to have installed at least `rsync` and `bash`. Most Linux distributions have  both installed, some only `bash`. On macOS, both come installed by default. Also check that Python 3.6 or higher is installed (use [`brew`] on macOS for that).

In this guide, a virtual environment will be used to install and use the tool. It is not recommended to install it directly in the system.

First prepare the virtual environment. You can use `venv` or `virtualenv`, but the first will be used.

```sh
python -m venv .venv
python -m virtualenv .venv
```

> Note: `python` here it is referred to the python 3 executable. In some platforms will be `python3`.

Once the environment is created, we must "activate" it:

```sh
. .venv/bin/activate
```

!!! Info
    It may be good idea to upgrade some basic packages after enabling the virtual environment: `pip install --upgrade pip setuptools wheel`

Now you can use `python` and `pip` and everything will work from and install to the virtual environment. Now you can download the tool and install it:

```sh
#Install using pip
pip install mdbackup

#You can also install the tool using the wheel package from GitHub:
#Check the latest release at https://github.com/MajorcaDevs/mdbackup/releases

mdbackup --help
```

To check if the tool is installed properly, run the help of the tool and you should get something like [this](./arguments.md).

You can also use the [Docker container](./docker.md). But it is recommended to read the guide to get an idea.


## First configuration

> Note: this will get through getting an initial configuration for backups. To get in more detail, check out the [Configuration](./configuration.md) page.

In order to get your first backup, the tool must be configured properly. To achieve this, you will learn the core concepts used in the tool and how to use them to fit your needs.

The tool needs three folders to work:

- `config`: a folder where the configuration, and other files related to configuration, tokens or cookies are going to be stored.
- `config/tasks`: a folder where the backup logic is stored in form of yaml or json files.
- \*put a full path here\*: the folder, placed in some folder, where the backups are going to be stored.

The folder in where you are right now should have the following structure:

- `.venv/`
    - ...
- `config/`
    - `config.json`
    - `tasks/`
        - `01.yaml`
- `mdbackup.whl`

And the third folder, it does not matter where is placed, but it will be used soon to store backups. It can be a network storage, an external drive or a partition in some local drive. It is recommended to store them outside the root partition (`/`), if possible.

Did you notice the `config.json`? This file holds the [configuration](./configuration.md) of the tool. Write in it the following:

```json
{
  "backupsPath": "/the/path/to/the/folder/where/the/backups/are/going/to/be/stored",
  "logLevel": "DEBUG",
  "env": {}
}
```

!!! Note
    You can download the [JSON Schema][2] and use it to validate the structure: `"$schema": "./config.schema.json",`. You can grab it from the latest release.

!!! Note "yaml is an option"
    You can also use `yaml` for configuration and tasks file, if you prefer.

This configuration is really basic and tells the tool where to place the backups, which log level to use (will be very verbose, but it is OK for now) and to inject no extra environment variables.

Now we need to define the logic to create backups. We use the term [tasks](../tasks) to refer a group of [actions](../actions) that will run in order to backup something. Tasks can be grouped in a tasks definition file and stored in a json or yaml file inside the `config/tasks` folder. An action is just something that accepts an input and some parameters and transforms the input to something else, but it can be also something that writes the input to a file or a folder, or a source of data that does not receive any input and writes data as output.

The steps are executed following the natural order (alphanumeric order) of the names of the files. For example, `01.json` will run before `02.json`. It can be as many files as desired, or just one. It does not matter. So now we will give some contents to `01.yaml` (the file shown in the tree).

```yaml tab="YAML syntax"
name: 'test'
tasks:
  - name: Backup home
    actions:
      - from-directory: /home/user  #macOS users, use "/Users/YourUser"
      - to-directory:
          path: home
```

```json tab="JSON syntax"
{
  "name": "test",
  "tasks": [
    {
      "name": "Backup home",
      "actions": [
        { "from-directory": "/home/user" },
        {
          "to-directory": {
            "path": "home"
          }
        }
      ]
    }
  ]
}
```

This task will copy your home directory and all its contents into the backup folder. You can use any other folder you want just to try, this is an example.

Now try running the tool: `mdbackup`. If everything is well configured, you will have a new folder in the backups folder with the date and time of now and with your folder copied. Well, try now to make a backup again. If the folder being copied is large enough, you will notice that this time, the backup took less time than the first time. This is because the action `to-directory` takes into account the previous backup and will try to do an incremental backup: if the file to copy already exists in the previous backup and has not been modified since the last time, then it will do a `hard-link` instead of a copy. This trick only works for some of the actions, check their documentation to know what are the ones doing this.

Note that `current` folder is always present and is a soft link to the latest backup. So it's easy to access to the latest backup from the file explorer or from the command line :)

Now you have backups of whatever you want! Just configure the tool and write the right scripts to fit your needs.

!!! Warning "SuperUser rights may be needed"
    It is possible that you will need to run the tool as root to access some system folders. Remember that the virtual environment is not inherited when using `sudo`. Make your own script, or checkout one of [the contrib folder][3].

## Injecting environment variables

[Actions](../actions) receive parameters to be able to do their job. These parameters can be defined previously in `env` sections either in the config file, in the tasks definition file or inside a task. The value of a variable can refer to a secret, which is identified by using a `#` hashtag at the begining of the string. Secrets won't be covered in the quick start, but is good to know :)

Let's try to make a backup from a postgres database with the predefined action. For this example, `pg_dump` must be installed on the system.

Time to add a new tasks file called `02.yaml` with the following contents:

```yaml tab="YAML syntax"
name: PostgreSQL example
env:
  host: localhost
  user: postgres
  password: WonderfulPassword123
tasks:
  - name: Postgres task example
    actions:
      - postgres-database:
          database: test1
      - to-file:
          path: test1.sql
  - name: Postgres task example 2
    actions:
      - postgres-database:
          database: test2
      - to-file:
          path: test2.sql
```

```json tab="JSON syntax"
{
  "name": "PostgreSQL example",
  "env": {
    "host": "localhost",
    "user": "postgres",
    "password": "WonderfulPassword123"
  },
  "tasks": [
    {
      "name": "Postgres task example",
      "actions": [
        {
          "postgres-database": {
            "database": "test1"
          }
        },
        {
          "to-file": {
            "path": "test1.sql"
          }
        }
      ]
    },
    {
      "name": "Postgres task example 2",
      "actions": [
        {
          "postgres-database": {
            "database": "test2"
          }
        },
        {
          "to-file": {
            "path": "test2.sql"
          }
        }
      ]
    }
  ]
}
```

The tool will read the environment variables, and inject them in the actions parameters.

But wait, there's more: you can even place `${VARIABLE}` tokens in the parameters or other variables inside `env` sections to refer to real environment variables or variables on `env`s. This example will try to access to the database using the user running the tool:

```yaml tab="YAML syntax"
name: PostgreSQL example
env:
  host: localhost
  user: ${USER}
tasks:
  - name: Postgres task example
    actions:
      - postgres-database:
          database: test1
      - to-file:
          path: test1.sql
  - name: Postgres task example 2
    actions:
      - postgres-database:
          database: test2
      - to-file:
          path: test2.sql
```

```json tab="JSON syntax"
{
  "name": "PostgreSQL example",
  "env": {
    "host": "localhost",
    "user": "${USER}"
  },
  "tasks": [
    {
      "name": "Postgres task example",
      "actions": [
        {
          "postgres-database": {
            "database": "test1"
          }
        },
        {
          "to-file": {
            "path": "test1.sql"
          }
        }
      ]
    },
    {
      "name": "Postgres task example 2",
      "actions": [
        {
          "postgres-database": {
            "database": "test2"
          }
        },
        {
          "to-file": {
            "path": "test2.sql"
          }
        }
      ]
    }
  ]
}
```


If everything went well, you now will have a `test1.sql` and `test2.sql` files in the backup folder.

!!! Info "YAML is better for tasks"
    Check the YAML and JSON syntax in the examples for the tasks... We think that YAML is better for writing tasks, lesser to write and easier to understand.


## Compression

What if your postgres backup takes some MB and you think "what if the file were compressed, will be a few KBs?" You can add a compress action in the middle of the actions to compress the output. See the example:

```yaml
...
    actions:
      - postgres-database:
          database: test1
      - compress-gz: {}  #Compress using `gzip` (the command)
      - to-file:
          path: test1.sql.gz
...
```

The [`compress-gz`](../actions/compress#compress-gz) action receives data as input and compresses it using `gzip` command. And that's how you compress some data.

In addition, when uploading folders to a storage provider, they automatically are archived into a `tar` file. If you want to save some bits, you can also compress them by adding the following configuration in the configuration file:

```json
{
  "...": "...",
  "compression": {
    "strategy": "gzip",
    "level": 7
  }
}
```


## Encrypt

You need **OpenGPG 2** in order to cypher files. And as well as the compression, will be used automatically to upload to storage providers.

Most Linux distributions have installed `gpg` tools, but you must check the version. On macOS, install [GPGTools][4].

There's two ways to encrypt data, in this guide will be using the passphrase. Here is a configuration example:

```json
{
  "...": "...",
  "cypher": {
    "strategy": "gpg-passphrase",
    "passphrase": "ThisIsAPassphrase321",
    "algorithm": "AES256"
  }
}
```

But, if instead what you want is to encrypt a file in a task, there is an action for you:

```yaml
...
    actions:
      - postgres-database:
          database: test1
      - encrypt-gpg:
          passphrase: AVeryPowerfulPassw0rd:)
      - to-file:
          path: test1.sql.asc
...
```

The [`encrypt-gpg`](../actions/encrypt#encrypt-gpg) action will use `gpg` to encrypt the input data. You may even compress and encrypt the data in a task (preferible in this order):

```yaml
...
    actions:
      - postgres-database:
          database: test1
      - compress-gz: {}
      - encrypt-gpg:
          passphrase: AVeryPowerfulPassw0rd:)
      - to-file:
          path: test1.sql.asc
...
```


!!! Note
    The algorithm changes between distributions. Check the available in `gpg --version`. In this guide we will be using AES256.


## Upload to the cloud

Well, you can also use an FTP server for this, but it's cool to say *"TO THE CLOUD"*.

If desired, the backups can be uploaded to what we call "storage provider". It can be a FTP or SFTP server, or a Cloud Storage (like S3 or Google Drive). This is run after the backup is done, and can be uploaded to one or more storage providers. Also to speed up the upload, the folders are written into a `tar` file, compressed (if configured) and encrypted (if configured).

> It is recommended to, at least, configure the compression in order to save some storage at the cloud.

There are many [storage providers](./storage) to choose. In the guid will be using a FTP server to quickly show how to upload files. *Also because this is the only storage provider that does not need to install any extra packages.*

This is the configuration for the FTP:

```json
{
  "...": "...",
  "storage": [
    {
      "type": "ftp",
      "backupsPath": "/backups",
      "host": "ftp.local",
      "user": "anonymous"
    }
  ]
}
```

This will upload the files to the FTP server `ftp.local`, in the folder `/backups` using the `anonymous` user and no password.


## The end

There's more to learn about the tool, but this is a rather good introduction to it. Take a look to the other sections of this documentation to learn and discover new stuff of the tool.

Concerned about too much hardcoded credentials in the configuration file? Check out the [Secret backends](../secrets).


 [1]: https://brew.sh
 [2]: https://github.com/MajorcaDevs/mdbackup/releases/latest/download/config.schema.json
 [3]: https://github.com/MajorcaDevs/mdbackup/tree/master/contrib
 [4]: https://gpgtools.org
