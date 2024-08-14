#!/bin/bash

poetry install

poetry update

git config --local core.editor "vi"

/bin/bash .devcontainer/vscode_settings.sh
