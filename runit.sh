#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 -prompt \"your prompt here\""
  exit 1
}

if [[ $# -ne 2 || "$1" != "-prompt" || -z "$2" ]]; then
  usage
fi

PROMPT="$2"

printf '\n'

curl -sS -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  --data "$(jq -n --arg prompt "$PROMPT" '{prompt: $prompt}')" \
  | jq -r '.result.content[0].text'

printf '\n'
