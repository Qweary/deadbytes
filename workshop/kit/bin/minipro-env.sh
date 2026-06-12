# minipro-env.sh — set MINIPRO_HOME to the kit's BUNDLED device-database dir.
#
# Source this (it is not executed standalone): `start.sh` sources it on the
# GUI/shell path, and a facilitator can `source` it before a raw manual minipro
# command so the bundled infoic.xml / logicic.xml are found with no setup:
#
#     source workshop/kit/bin/minipro-env.sh
#     minipro -p AT45DB041E[Page264]@SOIC8 -c code -r out.bin
#
# Why this is needed: the bundled minipro (commit fd6b56af) has its device DB
# compiled to point at /usr/local/share/minipro, which does not exist on a clean
# attendee machine, so chip profiling fails with a misleading "reclip" error.
# MINIPRO_HOME REPLACES that compiled path (it is not a fallback): when set,
# minipro loads XML ONLY from $MINIPRO_HOME/<name>, so pointing it at the bundled
# dir both supplies the DB and correctly shadows any stale system copy.
#
# CWD-SHADOW GOTCHA: minipro checks a bare ./logicic.xml in the CURRENT directory
# BEFORE $MINIPRO_HOME, so MINIPRO_HOME must be ABSOLUTE — a relative path could
# be silently shadowed by a stray XML in whatever cwd the command runs from.
#
# PATH-RELATIVE BY DESIGN: the share dir is resolved from THIS snippet's own
# location (kit/bin/ -> kit/share/minipro), so it works from any clone location.
# DEFAULT, DON'T OVERRIDE: only set MINIPRO_HOME if the attendee has not already
# set their own. Degrades cleanly (leaves it unset) if the share dir is absent.

# Resolve this snippet's own path. Under bash (the launcher and the documented
# `source` lane) BASH_SOURCE[0] is this file even when sourced; fall back to ${0}
# for other shells, and tolerate set -u by defaulting both to empty. If we cannot
# resolve a directory we simply do nothing (MINIPRO_HOME stays as-is).
_MINIPRO_ENV_SRC="${BASH_SOURCE:-${0:-}}"
if [ -n "$_MINIPRO_ENV_SRC" ]; then
    _MINIPRO_ENV_DIR="$(cd "$(dirname "$_MINIPRO_ENV_SRC")" 2>/dev/null && pwd)"
    _MINIPRO_SHARE="${_MINIPRO_ENV_DIR}/../share/minipro"
    # Only set if the attendee has not set their own AND the bundled dir exists.
    if [ -z "${MINIPRO_HOME:-}" ] && [ -n "$_MINIPRO_ENV_DIR" ] && [ -d "$_MINIPRO_SHARE" ]; then
        MINIPRO_HOME="$(cd "$_MINIPRO_SHARE" && pwd)"
        export MINIPRO_HOME
    fi
    unset _MINIPRO_ENV_DIR _MINIPRO_SHARE
fi
unset _MINIPRO_ENV_SRC
