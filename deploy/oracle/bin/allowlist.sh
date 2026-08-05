#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

usage() {
  die "Usage: $0 list | add EMAIL | remove EMAIL"
}

normalize_list() {
  awk -F, '
    {
      separator = ""
      for (index = 1; index <= NF; index += 1) {
        entry = tolower($index)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", entry)
        if (entry != "" && !seen[entry]++) {
          printf "%s%s", separator, entry
          separator = ","
        }
      }
    }
  '
}

normalize_email() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

validate_email() {
  printf '%s' "$1" | grep -Eq '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}$' \
    || die "EMAIL must be a complete address using common email characters."
}

require_root
[ "$#" -ge 1 ] || usage
load_env

action=$1
current=$(printf '%s' "${REGISTRATION_EMAIL_ALLOWLIST:-}" | normalize_list)

case "$action" in
  list)
    [ "$#" -eq 1 ] || usage
    if [ -z "$current" ]; then
      log "No registration emails are allowlisted."
    else
      printf '%s\n' "$current" | tr ',' '\n'
    fi
    ;;
  add)
    [ "$#" -eq 2 ] || usage
    email=$(normalize_email "$2")
    validate_email "$email"
    case ",$current," in
      *",$email,"*) log "$email is already allowlisted." ;;
      *)
        updated=${current:+$current,}$email
        replace_env_value REGISTRATION_EMAIL_ALLOWLIST "$updated"
        log "Added $email to the registration allowlist."
        log "Run 'systemctl reload chooseyourtube' to apply the change."
        ;;
    esac
    ;;
  remove)
    [ "$#" -eq 2 ] || usage
    email=$(normalize_email "$2")
    validate_email "$email"
    updated=$(
      printf '%s' "$current" | awk -F, -v target="$email" '
        {
          separator = ""
          for (index = 1; index <= NF; index += 1) {
            if ($index != "" && $index != target) {
              printf "%s%s", separator, $index
              separator = ","
            }
          }
        }
      '
    )
    [ "$updated" != "$current" ] || die "$email is not allowlisted."
    if [ -z "$updated" ] \
      && [ "${REGISTRATION_ENABLED:-true}" = "true" ] \
      && [ "${REGISTRATION_ALLOWLIST_REQUIRED:-false}" = "true" ]; then
      die "Disable registration before removing the final allowlisted email."
    fi
    replace_env_value REGISTRATION_EMAIL_ALLOWLIST "$updated"
    log "Removed $email from the registration allowlist."
    log "Run 'systemctl reload chooseyourtube' to apply the change."
    ;;
  *) usage ;;
esac
