# Google Drive

[Google Drive][2] is a cloud storage for all your files, like your USB or external hard-drive where you store stuff, but in the cloud.

To be able to use Google Drive as storage provider, You will need the `client_secrets.json`. You should get them from the [Google Developer's Console][1], by going to _Credentials_ and creating a new _OAuth 2.0 Client IDs_ or using an existing one. Every OAuth 2.0 entry have a download icon, this will download that file. The file must be stored somewhere in the local file system (for example, in the `config` folder). The only drawback is that the JSON cannot be stored in-place, inside the configuration.

The `auth_tokens.json` is created when a user logs in. You must use a path accessible from the tool to write the file. If the file does not exist, run the utility manually and (in some point) it will ask you to go to an URL. Here is where you log in with an account and Google will give you a token. Copy and paste it into the terminal. Now you will see the files uploading to Google Drive and the auth tokens file created.

The `backupsFolder` **must exist** before running the tool.

## Dependencies

In order to use Google Drive, you must install mdbackup with `pip install mdbackup[gdrive]`.

## Configuration schema

```json
{
  "type": "gdrive",
  "backupsPath": "Path in Google Drive where the backups will be located",
  "maxBackupsKept": "Indicates how many backups to keep in this storage, or set to null to keep them all",
  "clientSecrets": "config/client_secrets.json",
  "authTokens": "config/auth_tokens.json"
}
```

[1]: https://console.developers.google.com/apis/credentials
[2]: https://drive.google.com
