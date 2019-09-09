# Actions: Archive

## `tar`

**Input**: directory

**Output**: stream

**Parameters**

ignored (you can pass whatever you want 🙃)

**Description**

Archives a directory into a `tar` file. Only files, symbolic links and directories are stored, the rest are ignored.

!!! Example
    Compresses a folder using `tar` as archive.

    ```yaml
    - name: tar task example
      actions:
        - from-directory:
            path: '/some/where'
        - tar:
        - compress-gzip: {}
        - to-file:
            path: 'compressed-folder.tar.gz'
    ```
