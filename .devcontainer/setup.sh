#!/bin/bash

sudo apt update
sudo apt install -y graphviz xdg-utils

poetry install
poetry update
poetry self add poetry-plugin-shell
poetry self add poetry-plugin-export

git config --local core.editor "vi"

/bin/bash .devcontainer/vscode_settings.sh

echo "export OTEL_SDK_DISABLED=true" >> ~/.bashrc
