# FTP

FTP is a protocol to transfer files between computers over the network, but it's not encrypted. It's quite common protocol used by many hostings and easy to install in servers.

To use a FTP server to store the backups remotely, at least the `host` must be defined. This setting can also contain the port of the server. The username and password can be provided to use them to connect to the server.

The `backupPath` must exist in the server, and the user must have write permissions on it. Take into account that if the user is "`chroot`ed", the path will be different from the real path in the server.

## FTPS

FTPS is FTP over SSL/TLS that adds a layer of security over the FTP protocol.

Is an extension of the FTP provider, that adds the SSL/TLS layer, and uses the same settings as in the FTP plus two new ones.

If custom certificate chains are being used, `keyFile` and `certFile` probably will be needed. The certificate chain file allows the tool to identify the server properly and allow it to be used. If client certificate is needed, `keyFile` can be defined and must point to a private key file. Currently both files must exist in the file system, and certificates cannot be stored in base64 in the configuration. They can be stored in `config` folder is desired.

## Dependencies

No extra python packages are required to use this provider. Uses `ftplib`, which is bundled in Python.

## Configuration schema

```json
{
  "type": "ftp",
  "backupsPath": "Path in the FTP where the backups will be located",
  "maxBackupsKept": "Indicates how many backups to keep in this storage, or set to null to keep them all",
  "host": "Host (with or without the port) where the FTP server is located",
  "user": "(optional) User to connect to the FTP server",
  "password": "(optional) Password for the user",
  "acct":  "(optional) Account information for the user"
}
```

```json
{
  "type": "ftps",
  "backupsPath": "Path in the FTPS where the backups will be located",
  "maxBackupsKept": "Indicates how many backups to keep in this storage, or set to null to keep them all",
  "host": "Host (with or without the port) where the FTPS server is located",
  "user": "(optional) User to connect to the FTPS server",
  "password": "(optional) Password for the user",
  "acct":  "(optional) Account information for the user",
  "keyFile": "(optional) If needed, define a custom key file",
  "certFile": "(optional) If needed, define a custom certificate file"
}
```
