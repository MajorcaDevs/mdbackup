#!/usr/bin/env sh

CONFIG_FOLDER="/backups/tool"

cd $CONFIG_FOLDER
. .venv/bin/activate
mdbackups >> mdbackups.log 2>> mdbackups.error.log