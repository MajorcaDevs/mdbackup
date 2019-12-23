# SFTP

> SSH File Transfer Protocol

[SFTP][2] is a protocol that works over [SSH][1] to transfer and manage files over the network. Is not the same as FTP or FTPS, but its similar. Most servers have enabled the SFTP mode if they have a SSH server. [OpenSSH][3] implementation have the SFTP module and can be enabled if desired.

In order to connect to a SFTP server and use it as provider, the `host` and `user` must be defined, and use one of the following authentication methods.

The `backupPath` must exist in the server, and the user must have write permissions on it.

The authentication is attempted using the following order:

- If `privateKey` or `privateKeyFile` is defined, then this method will be used. If the private key is cyphered, use `password` as the passphrase of the key.
- If `allowAgent` is true, then will use the SSH Agent to connect to the server.
- Any key found in `~/.ssh`.
- If the `password` is defined, then the classic username/password login will be used (discouraged).

The known-hosts list is loaded by default from the default location `~/.ssh/known_hosts`. If `hostKeysFilePath` is defined, then this file will be used instead. If `enableHostKeys` is set to false, then no known-hosts will be loaded.

The `knownHostsPolicy` will set the policy that will be used when the SSH connection is set, but the host is being checked as a known or not-known host. The following policies are allowed:

- `reject` will close the connection if the host is not-known (default behaviour).
- `auto-add` will add to the list of known-hosts if the host is not-known.
- `ignore` will print a warning if the host is not-known.

**Note**: if the `knownHostsPolicy` is `auto-add` and `hostKeysFilePath` is defined, then the new host will be saved into the file.

## Dependencies

In order to use SFTP, you must install the following python packages:

- `paramiko`

## Configuration schema

```json
{
  "type": "sftp",
  "backupsPath": "Path in the SFTP where the backups will be located",
  "maxBackupsKept": "Indicates how many backups to keep in this storage, or set to null to keep them all",
  "host": "Host where the SFTP server is located",
  "port": "(optional) Port of the SFTP server (by default 22)",
  "user": "User to connect to the SFTP server",
  "password": "(optional) Password for the user",
  "privateKey": "(optional) Private Key in base64",
  "privateKeyPath": "(optional) Private Key file path",
  "allowAgent": "(optional) if true, then the connection will interact with the SSH Agent, false if this behaviour is not desired (false by default)",
  "compress": "(optional) if true, then the connection is compressed (false by default)",
  "knownHostsPolicy": "(optional) Changes the Known Hosts Policy. 'reject' will reject any connection to a server that is not known (default behaviour), 'auto-add' will add to the known-hosts list this server, 'ignore' will print a warning but it will let you connect.",
  "hostKeysFilePath": "(optional) Path to the known-hosts file",
  "enableHostKeys": "(optional) If set to false, it won't load any known-hosts file (by default is true)"
}
```


[1]: https://en.wikipedia.org/wiki/Secure_Shell
[2]: https://en.wikipedia.org/wiki/SSH_File_Transfer_Protocol
[3]: https://en.wikipedia.org/wiki/OpenSSH
