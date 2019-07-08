# Storage providers

A storage provider is server or service provider that offers a place to store files remotely. Can be a cloud storage provider (like S3 or Google Drive) or servers (like FTP or SFTP). Each provider is different and has different configurations and behaviours, but the goal of the tool is to simplify the upload of backups and the cleanup of them with simple settings.

Each storage provider has dependencies that are not installed by default. If you intend to use some of them, first check out which are their dependencies and install them. Otherwise, the tool will fail and it will require you to install the packages.

The configuration of a storage provider can be located in the [config.json file](../configuration.md#storage_1) or provided by a [secret provider](../secrets/index.md).

## List of providers

- [Google Drive](gdrive.md)
- [Amazon S3 or S3-like](s3.md)
- [Backblaze B2](b2.md)
- [FTP](ftp.md)
- [FTPS](ftp.md#fpts)
- [SFTP](sftp.md)
