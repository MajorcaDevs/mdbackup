# Arguments

The tool has a few arguments, in general you may not use them, but to test some parts, could be really useful.

```
usage: mdbackup [-h] [-c CONFIG] [--backup-only] [--upload-current-only]
                [--cleanup-only]

Small but customizable utility to create backups and store them in cloud
storage providers

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to configuration (default: config/config.json)
  --backup-only         Only does the backup actions
  --upload-current-only
                        Only uploads the last backup
  --cleanup-only        Only does the backup cleanup
```
