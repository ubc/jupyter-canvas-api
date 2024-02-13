#!/bin/bash
set -eo pipefail

BASE_DIR="${BASE_DIR:-/mnt/efs}"
DEFAULT_JNOTE_HOME="$BASE_DIR/${JNOTE_COURSE_CODE,,}"
DEFAULT_JNOTE_SNAP="$BASE_DIR/${JNOTE_COURSE_CODE,,}-snap"
DEFAULT_JNOTE_INTSNAP="$BASE_DIR/${JNOTE_COURSE_CODE,,}-internal"

export JNOTE_HOME="${JNOTE_HOME:-$DEFAULT_JNOTE_HOME}"
export JNOTE_SNAP="${JNOTE_SNAP:-$DEFAULT_JNOTE_SNAP}"
export JNOTE_INTSNAP="${JNOTE_INTSNAP:-$DEFAULT_JNOTE_INTSNAP}"

mkdir -p $JNOTE_HOME $JNOTE_SNAP $JNOTE_INTSNAP
chmod 777 $JNOTE_HOME $JNOTE_SNAP $JNOTE_INTSNAP

exec "$@"
