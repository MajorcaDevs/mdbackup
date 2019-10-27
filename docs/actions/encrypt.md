# Actions: Encrypt

## `encrypt-gpg`

**Input**: stream

**Output**: stream

**Unaction**: yes

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `passphrase` | `str` | Defines a passphrase that will be used to decrypt the data | Yes |
| `recipients` | `List[str]` | List of emails that will be able to decrypt the data | Yes |
| `cipherAlgorithm` | `str` | Changes the cypher algorithm | Yes |
| `compressAlgorithm` | `str` | Changes the compress algorithm | Yes |

At least one recipient must be defined. If no recipients are defined, a passphrase must be provided. Both can be defined.

**Description**

Encrypts the data using `gpg` (gpg 2) command. If recipients are defined, then the users that own that keys will be able to decrypt the data. If passphrase is defined, then this passphrase will be used to encrypt the data. Both can be defined so if a user owns a key and is able to decrypt the data, the passphrase will be asked as well. The cipher and compress valid algorithms can be queried by issuing the command `gpg --version`. By default the compress algorithm is `uncompressed`.

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
