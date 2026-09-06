#!/usr/bin/env bash
set -euo pipefail

source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
source_file="$source_dir/a.sh"
python_bin="${NATURE_TEST_PYTHON:-$HOME/.local/share/llama-agent/venv/bin/python}"
if [ ! -x "$python_bin" ]; then python_bin=$(command -v python3); fi
work_dir=$(mktemp -d /tmp/nature-source-acceptance.XXXXXX)
trap 'rm -rf "$work_dir"' EXIT
bash -n "$source_file"
mkdir -p "$work_dir/home"

sed -n \
    '/<<'\''AGENTEOF'\''$/,/^AGENTEOF$/p' \
    "$source_file" |
    sed '1d;$d' >"$work_dir/llama-agent"

sed -n \
    '/<<'\''PYTESTEOF'\''$/,/^PYTESTEOF$/p' \
    "$source_file" |
    sed '1d;$d' >"$work_dir/acceptance.py"

test -s "$work_dir/llama-agent"
test -s "$work_dir/acceptance.py"
"$python_bin" -m py_compile "$work_dir/llama-agent"
HOME="$work_dir/home" "$python_bin" "$work_dir/acceptance.py" "$work_dir/llama-agent"
