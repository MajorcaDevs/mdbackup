# File

This is a simple secrets provider. It is not suitable to use in production, but can be useful to be used in Docker containers.

Every environment variable to inject, will be read from the file specified as value. In fact, every value (which are paths) will be transformed to their values. The paths can be absolute, or relative. To resolve relative paths, `basePath` should be defined, if not then it will look for secrets inside the folder `secrets` on the config folder.

For cloud storage providers, the backend will read json or yaml files, which must have the configuration for a backend. They must use the same structure shown in the [storage providers](../storage/index.md) section of the example json. If an object is used instead of a string, then the path must be in the `key` attribute and the rest of the object is treated as an extension to the configuration that will be loaded from the file. So it is possible to use same credentials between different configurations, but to define specific parameters for each.

 > To be able to read `yaml` files, you must install `pyyaml`: `pip install pyyaml`

## Configuration schema

```json
{
  "env": {
    "pgpassword": "/path/to/pg-password",
    "mysqlpassword": "mysql-password"
  },
  "config": {
    "basePath": "/backups/secrets"
  },
  "storage": [
    "providers/digital-ocean.json",
    "providers/gdrive.json",
    {
      "key": "providers/amazon.json",
      "backupsPath": "/backups/server-amg-1"
    }
  ]
}
```
