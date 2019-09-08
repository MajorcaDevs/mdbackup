# Actions: Encrypt

## `encrypt-gpg`

**Input**: stream

**Output**: stream

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `passphrase` | `str` | Defines a passphrase that will be used to decrypt the data | Yes |
| `recipients` | `List[str]` | List of emails that will be able to decrypt the data | Yes |
| `algorithm` | `str` | Changes the cypher algorithm | Yes |

At least one recipient must be defined. If no recipients are defined, a passphrase must be provided. Both can be defined.

**Description**

Encrypts the data using `gpg` (gpg 2) command. If recipients are defined, then the users that own that keys will be able to decrypt the data. If passphrase is defined, then this passphrase will be used to encrypt the data. Both can be defined so if a user owns a key and is able to decrypt the data, the passphrase will be asked as well.

!!! Warning
    The recipient keys must be imported previously. The action will not import any key.

!!! Example
    Cypher a database backup

    ```yaml
    - name: encrypt gpg task example
      actions:
        - postgres-database:
            database: 'example'
        - encrypt-gpg:
            passphrase: mdbackup
            recipients: [ user1@email.com, user2@email.com ]
        - to-file:
            path: 'example.sql.asc'
    ```
