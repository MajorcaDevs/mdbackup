# Actions: Compress

## `compress-xz`

**Input**: stream

**Output**: stream

**Unaction**: yes

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `compressionLevel` | `ìnt` | Compression level from 0 to 9 (default 6) | Yes |
| `extraCompression` | `bool` | Enables the extra compression mode (`-e`) | Yes |
| `cpus` | `int` | Uses this amount of cores to compress the data | Yes |

**Description**

Compresses the input stream using `xz` utility. If the compression level increases, more resources will be used to compress and more compressed the file should result (it may not compress any further if increasing it to 9). The extra compression mode uses even more resources to try to compress more (it does not affect decompression).

This compression algorithm uses huge amount of CPU and the result is usually better than the rest of algorithms listed here, but it may not be worth the CPU usage with the result if the files are text.

!!! Warning
    Requires `xz` to be installed in the system. In most distros it is included by default. On macOS, you should install it via `brew install xz`.

!!! Example
    Compresses a file using `xz`

    ```yaml
    - name: xz task example
      actions:
        - from-file: '/big/compressible/file'
        - compress-xz:
            compressionLevel: 7
            extraCompression: true
            cpus: 4
        - to-file:
            path: 'compressed-file.xz'
    ```


## `compress-gz`

**Input**: stream

**Output**: stream

**Unaction**: yes

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `compressionLevel` | `ìnt` | Compression level from 1 to 9 (default 6) | Yes |

**Description**

Compresses the input stream using `gzip` utility. If the compression level increases, more resources will be used to compress and more compressed the file should result (it may not compress any further if increasing it to 9).

This compression algorithm is rather fast and good-balanced in resources consumption. It may not be really good compressing binary files.

!!! Warning
    Requires `gzip` to be installed in the system. In most distros and in macOS it is included by default.

!!! Example
    Compresses a file using `gzip`

    ```yaml
    - name: gzip task example
      actions:
        - from-file: '/big/compressible/file'
        - compress-gz:
            compressionLevel: 7
        - to-file:
            path: 'compressed-file.gz'
    ```


## `compress-bz2`

**Input**: stream

**Output**: stream

**Unaction**: yes

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `compressionLevel` | `ìnt` | Compression level from 1 to 9 (default 6) | Yes |

**Description**

Compresses the input stream using `bzip2` utility. If the compression level increases, more resources will be used to compress and more compressed the file should result (it may not compress any further if increasing it to 9).

This compression algorithm is rather fast and good-balanced in resources consumption (is similar to `gzip`).

!!! Warning
    Requires `bzip2` to be installed in the system. In most distros and in macOS it is included by default.

!!! Example
    Compresses a file using `bzip2`

    ```yaml
    - name: bz task example
      actions:
        - from-file: '/big/compressible/file'
        - compress-bz2:
            compressionLevel: 7
        - to-file:
            path: 'compressed-file.bz2'
    ```


## `compress-br`

**Input**: stream

**Output**: stream

**Unaction**: yes

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `compressionLevel` | `ìnt` | Compression level from 1 to 9 (default 6) | Yes |

**Description**

Compresses the input stream using `brotli` utility. If the compression level increases, more resources will be used to compress and more compressed the file should result (it may not compress any further if increasing it to 9).

This compression algorithm is fast and good-balanced in resources consumption. Can be used as a fast compression algorithm for text and binary files.

!!! Warning
    Requires `brotli` to be installed in the system. On Debian-based distros use `apt install brotli`, on Arch-based distros use `pacman -S brotli`, on macOS use `brew install brotli`.

!!! Example
    Compresses a file using `brotli`

    ```yaml
    - name: br task example
      actions:
        - from-file: '/big/compressible/file'
        - compress-br:
            compressionLevel: 7
        - to-file:
            path: 'compressed-file.br'
    ```


## `compress-zst`

**Input**: stream

**Output**: stream

**Unaction**: yes

**Parameters**

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `compressionLevel` | `ìnt` | Compression level from 1 to 19 (default 3) | Yes |
| `cpus` | `int` | Uses this amount of cores to compress the data | Yes |

**Description**

Compresses the input stream using `zstd` utility. If the compression level increases, more resources will be used to compress and more compressed the file should result (it may not compress any further if increasing it to 19).

This compression algorithm is blazing fast and good in compression (similar to `xz` but faster). Can be used as a fast compression algorithm for text and binary files.

!!! Warning
    Requires `zstd` to be installed in the system. On Debian-based distros use `apt install zstd`, on Arch-based distros use `pacman -S zstd`, on macOS use `brew install zstd`.

!!! Example
    Compresses a file using `zstd`

    ```yaml
    - name: zst task example
      actions:
        - from-file: '/big/compressible/file'
        - compress-zst:
            compressionLevel: 7
        - to-file:
            path: 'compressed-file.zst'
    ```
