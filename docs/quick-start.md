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

Now you can use `python` and `pip` and everything will work from and install to the virtual environment. Now you can download the tool and install it:

```sh
#Download using curl...
curl -sSL https://github.com/MajorcaDevs/mdbackup/releases/latest/download/mdbackup.whl > mdbackup.whl
#...or wget
wget https://github.com/MajorcaDevs/mdbackup/releases/latest/download/mdbackup.whl
#If they don't work, go to https://github.com/MajorcaDevs/mdbackup/releases and copy the URL from the latest release

pip install mdbackup.whl

mdbackup --help
```

To check if the tool is installed properly, run the help of the tool and you should get something like [this](./arguments.md).

You can also use the [Docker container](./docker.md). But it is recommended to read the guide to get an idea.


## First configuration

> Note: this will get through getting an initial configuration for backups. To get in more detail, check out the [Configuration](./configuration.md) page.

In order to get your first backup, the tool must be configured properly. To achieve this, you will learn the core concepts used in the tool and how to use them to fit your needs.

The tool needs three folders to work:

- `config`: a folder where the configuration, and other files related to configuration, tokens or cookies are going to be stored.
- `config/steps`: a folder where the backup logic is stored in form of bash scripts.
- \*put a full path here\*: the folder, placed in some folder, where the backups are going to be stored.

The folder in where you are right now should have the following structure:

- `.venv/`
    - ...
- `config/`
    - `config.json`
    - `steps/`
        - `01.sh`
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

> Note: you can download the [JSON Schema][2] and use it to validate the structure: `"$schema": "./config.schema.json",`. You can grab it from the latest release.

> Note: you can also use `yaml` if you prefer

This configuration is really basic and tells the tool where to place the backups, which log level to use (will be very verbose, but it is OK for now) and to inject no extra environment variables.

Now we need to define the logic to create backups. We called it `steps`. A step is just a bash script (without the shebang `!#`) that do some actions to copy/backup any data, files or folders to the backup folder (referring "backup folder" to the folder where the current backup is going to be stored). The tool defines some [predefined functions](./steps/index.md#function-utilities) that are useful to make most common backup operations. Some of them requires to have installed extra CLIs or to have installed Docker. But if these functions are not used, no errors will arise.

The steps are executed following the natural order (alphanumeric order) of the names of the files. For example, `01.sh` will run before `02.sh`. It can be as many scripts as desired, or just one. It does not matter. So now we will give some contents to `01.sh` (the file shown in the tree).

```sh
backup-folder "/home/YourUser" home  #macOS users, use "/Users/YourUser"
```

This step will copy your home directory and all its contents into the backup folder using `rsync`. With one line, you will get a full backup of a folder! You can use any other folder you want just to try, this is an example. Check that the script has execution permissions for the `user`, and possible for `all`: `chmod ua+x ./steps/01.sh`.

Now try running the tool: `mdbackup`. If everything is well configured, you will have a new folder in the backups folder with the date and time of now and with your folder copied. Well, try now to make a backup again. If the folder being copied is large enough, you will notice that this time, the backup took less time than the first time. This is because the mode in which `rsync` runs checks which files have been modified and just copies these ones. The rest of unmodified files are hard-linked from the latest backup. It's an "incremental" backup!

Note that `current` folder is always present and is a soft link to the latest backup. So it's easy to access to the latest backup from the file explorer or from the command line :)

Now you have backups of whatever you want! Just configure the tool and write the right scripts to fit your needs.

> Note: it is possible that you will need to run the tool as root to access some system folders. Remember that the virtual environment is not inherited when using `sudo`. Make your own script, or checkout one of [the contrib folder][3].

## Injecting environment variables

Some of the [steps](./steps/index.md#function-utilities) have as parameters some environment variables. These can be defined in the `env` section of the json. The object must be a simple Key/Value structure. Complex structures (like objects or arrays) are not allowed.

Let's try to make a backup from a postgres database with the predefined function. Also these variables can be used natively with some postgres tools because they also understand them. For this example, `pg_dump` must be installed on the system.

First, the `env` must be changed to add the new settings:

```js
{
  "...": "...",
  "env": {
    "pghost": "localhost",
    "pguser": "postgres",
    "pgpassword": "WonderfulPassword123"
  }
}
```

Then, we will add a new step script called `02.sh` with the following contents:

```sh
backup-postgres-database "databasename"
```

The tool will read the environment variables, and inject them in the scripts environment when they are running. The key are transformed to be upper case, so you don't need to.

If everything went well, you now will have a `databasename.sql` file in the backup folder.


## Compression

What if your postgres backup takes some MB and if the file were compressed, will be a few KBs? Or what if you want to upload to a cloud storage and you want to save some bytes if possible when uploading them? *(That's an spoiler, yes)*

The tool, with the help of `tar`, `xz` and `gzip` commands, can compress whatever you want. And some of the predefined functions takes advantage of this and compress for you some of the files. The configuration for this is simple:

```json
{
  "...": "...",
  "compression": {
    "strategy": "gzip",
    "level": 7
  }
}
```

With this simple configuration, the `backup-postgres-database` and many more will output a compressed file. You can even take advantage of this by using the helper function [`compress-encrypt`](./steps/#compress-encrypt) that will run a command that must output the data to `stdout` and will compress (and encrypt [oh no, another spoiler]) it using the configuration.


## Encrypt

You already know that you can encrypt, but you don't know how yet. You need **OpenGPG 2** in order to cypher files. And as well as the compression, will be used automatically by some functions, and in the upload to storage providers.

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

> Note: the algorithm changes between distributions. Check the available in `gpg --version`. In this guide we will be using AES256.

Now the `backup-postgres-database` will be compressed and encrypted using a passphrase and `gpg`, and any of the functions that uses [`compress-encrypt`](./steps/#compress-encrypt).


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

Concerned about too much hardcoded credentials in the configuration file? Check out the [Secret backends](./secrets).


 [1]: https://brew.sh
 [2]: https://github.com/MajorcaDevs/mdbackup/releases/latest/download/config.schema.json
 [3]: https://github.com/MajorcaDevs/mdbackup/tree/master/contrib
 [4]: https://gpgtools.org
