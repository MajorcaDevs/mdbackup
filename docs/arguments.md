# Arguments

The tool has some subcommands that can be used manually. By default the tool will run in complete mode which does
everything (check configuration, backup, upload and clean up).

```
usage: mdbackup [-h] [-c CONFIG] mode ...

Small but customizable utility to create backups and store them in cloud
storage providers

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to configuration folder (default: config)

subcommands:
  Selects the run mode (defaults to complete)

  mode
    complete            Checks config, does a backup, uploads the backup and
                        does cleanup
    backup              Does a backup
    upload              Upload a pending backups
    cleanup             Does cleanup of backups
    check-config        Checks configuration to catch issues
```

## `complete`

This subcommand has no extra arguments.

## `backup`

This subcommand has no extra arguments.

## `upload`

```
usage: mdbackup upload [-h] [--backup BACKUP] [-f]

optional arguments:
  -h, --help       show this help message and exit
  --backup BACKUP  Selects which backup to upload by the name of the folder
                   (which is the date of the backup)
  -f, --force      Force upload the backup even if the backup was already
                   uploaded
```

## `cleanup`

This subcommand has no extra arguments.

## `check-config`

This subcommand has no extra arguments.