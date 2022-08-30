# Vault

[Vault][1] is a production-ready secrets backend, really useful to have credentials stored in a centralized server, but retrievable from any client in a network.

!!! Warning "Dependency"
    In order to use Vault backend, install with: `pip install mdbackup[vault]`.

Currently, it only supports KV backend for reading secrets.

Environment variables are replaced by their values from the path in the KV. As every path in the KV storage is Key-Value, you must define which key should get to obtain the value. `secrets/backups/env/postgres#user` will retrieve the path `secrets/backups/env/postgres` and key `user`. If the key is not set, will use `value` by default.

For cloud storage providers, the KV in the path should contain the same structure as expected in the [storage provider](../storage/index.md) configuration. In this case, no key must be defined, it will take the whole path as configuration. If an object is used instead of a string, then the key path must be in the `key` attribute and the rest of the object is treated as an extension to the configuration that will be loaded from Vault. So it is possible to use same credentials between different configurations and servers, but to define specific parameters for each.

## Configuration schema

```json
{
  "envDefs": {
    "pg": {
      "user": "secret/backups/env/pg#user",
      "password": "secret/backups/env/pg#password"
    },
    "mysql": {
      "user": "secret/backups/env/mysql#user",
      "password": "secret/backups/env/mysql#password"
    }
  },
  "config": {
    "apiBaseUrl": "http://localhost:8200",
    "roleId": "56c90891-83d5-81da-ac71-02ad8ed7fbfe",
    "secretId": "9d261dc7-1bef-5759-6c72-63d57e58ffec",
    "cert": "Path to a certificate bundle or false to disable TLS certificate validation"
  },
  "storage": [
    {
      "key": "secret/backups/providers/digital-ocean",
      "backupsPath": "/backups/pi"
    },
    "secret/backups/providers/gdrive",
    "secret/backups/providers/amazon"
  ]
}
```


[1]: https://www.vaultproject.io