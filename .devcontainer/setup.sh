#!/bin/bash

poetry install

poetry update

git config --local core.editor "vi"
