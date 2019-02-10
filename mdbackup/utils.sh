# Small but customizable utility to create backups and store them in
# cloud storage providers
# Copyright (C) 2018  Melchor Alejo Garau Madrigal
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

###############################################################################
##                       BEGIN UTILITIES FOR UTILITES                        ##
###############################################################################

[[ -z "$MYSQLNETWORK" ]] && export MYSQLNETWORK='host'
[[ -z "$MYSQLIMAGE" ]] && export MYSQLIMAGE='mariadb'
[[ -z "$MYSQLHOST" ]] && export MYSQLHOST='localhost'
[[ ! -z "$MYSQLPASSWORD" ]] && export MYSQLPASSWORD="-p$MYSQLPASSWORD"
[[ ! -z "$MYSQLUSER" ]] && export MYSQLUSER="-u $MYSQLUSER"
function __run_mysql() {
    if [[ ! -z "$DOCKER" ]]; then
        exec docker container run \
            --rm \
            -i \
            --network=${MYSQLNETWORK} \
            ${MYSQLIMAGE} \
            "$@"
    else
        exec "$@"
    fi
}

[[ -z "$PGNETWORK" ]] && export PGNETWORK='host'
[[ -z "$PGUSER" ]] && export PGUSER='postgres'
[[ -z "$PGIMAGE" ]] && export PGIMAGE='postgres'
[[ -z "$PGHOST" ]] && export PGHOST='localhost'
function __run_psql() {
    if [[ ! -z "$DOCKER" ]]; then
        exec docker container run \
            --rm \
            -i \
            --network=${PGNETWORK} \
            -e PGPASSWORD=${PGPASSWORD} \
            -u ${PGUSER} \
            ${PGIMAGE} \
            "$@"
    else
        exec sudo -u ${PGUSER} "$@"
    fi
}

function __gpg_common_extra_args() {
    local extra_args=""
    if [[ ! -z "$CYPHER_ALGORITHM" ]]; then
        extra_args="$extra_args --cypher-algo $CYPHER_ALGORITHM"
    fi
    echo ${extra_args}
}

function __gpg_passphrase() {
    local extra_args=$(__gpg_common_extra_args)
    echo gpg --output - --batch --passphrase \"${CYPHER_PASSPHRASE}\" --symmetric ${extra_args} -
}

function __gpg_recipients() {
    printf "%s %s" "gpg --output - --encrypt" "$(__gpg_common_extra_args)"
    while read email; do
        printf " -r \"%s\"" "$email"
    done < <(echo ${CYPHER_KEYS} | tr ' ' '\n')
    echo " -"
}

function __gzip() {
    echo "gzip -$COMPRESSION_LEVEL"
}

function __xz() {
    echo "xz -z -T 0 -$COMPRESSION_LEVEL -c -"
}


###############################################################################
##                              BEGIN UTILITIES                              ##
###############################################################################


# $1 -> Command that generates an output
# $2 -> Filename
# $COMPRESSION_STRATEGY -> gzip or xz will compress the output, empty to not to compress
# $COMPRESSION_LEVEL -> Level of compression
# $CYPHER_STRATEGY -> gpg-keys or gpg-passphrase will cypher the output, empty to not to cypher
# $CYPHER_KEYS -> Encrypt the copy using keys from recipient keys (emaisl in GPG)
# $CYPHER_PASSPHRASE -> Encrypt the copy using a passphrase
function compress-encrypt() {
    local final_cmd="$1"
    local extension=""

    if [[ -z "$1" ]]; then
        echo "Command is empty"
        return 1
    fi

    if [[ -z "$2" ]]; then
        echo "Filename is empty"
        return 2
    fi

    case "$COMPRESSION_STRATEGY" in
        "gzip" )
            final_cmd="$final_cmd | $(__gzip)"
            extension=".gz"
            ;;
        "xz" )
            final_cmd="$final_cmd | $(__xz)"
            extension=".xz"
            ;;
    esac

    case "$CYPHER_STRATEGY" in
        "gpg-keys" )
            final_cmd="$final_cmd | $(__gpg_recipients)"
            extension="${extension}.asc"
            ;;
        "gpg-passphrase" )
            final_cmd="$final_cmd | $(__gpg_passphrase)"
            extension="${extension}.asc"
            ;;
    esac

    eval "${final_cmd} > \"${2}${extension}\""
    return $?
}

# $1 -> Source of the backup
# $2 -> Name of the destination folder in the backup
# ... extra arguments are passed to rsync
function backup-folder() {
    if [[ ! -d "$1" && ! -f "$1" ]]; then
        echo "Source '$1' does not exist"
        return 1
    fi

    SRC="$1"
    DST_PARTIAL="./.$2.partial"
    DST="$2"
    shift
    shift

    rsync \
        --acls \
        --xattrs \
        --owner \
        --group \
        --times \
        --recursive \
        --links \
        --delete \
        --delete-excluded \
        --partial-dir=".partial" \
        --link-dest="../../current/$DST" \
        "$@" \
        "$SRC" "$DST_PARTIAL" || return $?
    mv "$DST_PARTIAL" "./$DST" || return $?
}

# $1 -> IP of the other host
# $1 -> Source folder on the remote host
# $2 -> Name of the destination folder in the backup
# ... extra arguments are passed to rsync
function backup-remote-folder() {
    IP="$1"
    SRC="$2"
    DST="$3"
    shift
    shift
    shift
    #https://www.digitalocean.com/community/tutorials/how-to-copy-files-with-rsync-over-ssh
    rsync -avz "$@" \
        --recursive \
        --delete \
        --delete-excluded \
        --partial-dir=".partial" \
        --link-dest="../../current/$DST" \
        -e "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" \
        "$IP:$SRC" "$DST" || return $?
}

# $1 -> database to backup
# See compress-encrypt...
function backup-postgres-database() {
    compress-encrypt "__run_psql pg_dump -h $PGHOST \"$1\"" "$1.sql" || return $?
}

# $1 -> database to backup
# See compress-encrypt...
function backup-mysql-database() {
    compress-encrypt "__run_mysql mysqldump -h $MYSQLHOST $MYSQLPASSWORD $MYSQLUSER \"$1\"" "$1.sql" || return $?
}

# $1 -> volume to backup
# See compress-encrypt...
function backup-docker-volume() {
    compress-encrypt "docker container run --rm -i -v \"$1\":/backup alpine tar -c -C /backup ." "$1.tar" || return $?
}

# $1 -> volume to backup
# See backup-folder...
function backup-docker-volume-physically() {
    if docker volume inspect "$1" > /dev/null; then
        local dst=$(docker volume inspect "$1" --format "{{.Mountpoint}}")
        backup-folder "$dst" "$1" || return $?
    else
        echo "Volume '$1' does not exist"
        return 1
    fi
}

# $1 -> file to backup
# $2 -> (optional) folder where to write the file
function backup-file() {
    local old="../current/$2/$(basename "$1")"
    local new="./$2/$(basename "$1")"
    if [[ ! -d "./$2" ]]; then
        mkdir -p "./$2" || return $?
    fi

    if [[ ! -f "$old" ]] || ! cmp -s "$old" "$1" ; then
        cp -a "$1" "$new" || return $?
    else
        ln "$old" "$new" || return $?
    fi
}

# $1 -> file to backup
# $2 -> (optional) folder where to write the file
# See compress-encrypt
function backup-file-encrypted() {
    local old="../current/$2/$(basename "$1")"
    local new="./$2/$(basename "$1")"
    if [[ ! -d "./$2" ]]; then
        mkdir -p "./$2" || return $?
    fi

    compress-encrypt "cat '$1'" "$new~" || return $?

    if [[ ! -f "$old" ]] || ! cmp -s "$old" "$new~" ; then
        mv "$new~" "$new" || return $?
    else
        ln "$old" "$new" || return $?
        rm "$new~" || return $?
    fi
}
