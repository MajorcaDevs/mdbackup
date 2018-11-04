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
            --network=$MYSQLNETWORK \
            $MYSQLIMAGE \
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
            --network=$PGNETWORK \
            -e PGPASSWORD=$PGPASSWORD \
            -u $PGUSER \
            $PGIMAGE \
            "$@"
    else
        exec sudo -u $PGUSER "$@"
    fi
}


###############################################################################
##                              BEGIN UTILITIES                              ##
###############################################################################


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
# $GPG_PASSPHRASE -> If set this value, the backup will be encrypted using gpg and this value is the passphrase of the file
function backup-postgres-database() {
    if [[ ! -z "$GPG_PASSPHRASE" ]]; then
        __run_psql pg_dump -h $PGHOST "$1" | gpg --output "$1".sql.gpg --batch --passphrase "$GPG_PASSPHRASE" --symmetric - || return $?
    else
        __run_psql pg_dump -h $PGHOST "$1" | gzip > "$1".sql.gz || return $?
    fi
}

# $1 -> database to backup
# $GPG_PASSPHRASE -> If set this value, the backup will be encrypted using gpg and this value is the passphrase of the file
function backup-mysql-database() {
    if [[ ! -z "$GPG_PASSPHRASE" ]]; then
        __run_mysql mysqldump -h $MYSQLHOST $MYSQLPASSWORD $MYSQLUSER "$1" | gpg --output "$1".sql.gpg --batch --passphrase "$GPG_PASSPHRASE" --symmetric - || return $?
    else
        __run_mysql mysqldump -h $MYSQLHOST $MYSQLPASSWORD $MYSQLUSER "$1" | gzip > "$1".sql.gz || return $?
    fi
}