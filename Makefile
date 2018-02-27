SHELL := /bin/bash

ut: export PYTHONPATH=./src:$PYTHONPATH
ut:
	pytest
