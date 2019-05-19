# File

This is a simple secrets provider. It is not suitable to use in production, but can be useful to be used in Docker containers.

Every environment variable to inject, will be read from the file specified as value. In fact, every value (which are paths) will be transformed to their values. The paths can be absolute, or relative. To resolve relative paths, you must define `basePath`.

For cloud storage providers, the backend will read json or yaml files, which must have the configuration for a backend. They must use the same structure shown in the [storage providers](../storage/index.md) section of the example json.

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
  "providers": [
    "providers/digital-ocean.json",
    "providers/gdrive.json",
    "providers/amazon.json"
  ]
}
```