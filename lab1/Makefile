# Makefile for COMP 412 Lab 1
# ILOC Front End

SHELL := /bin/bash
PYTHON := python3

.PHONY: all clean build

all: build

clean:
	@rm -rf __pycache__ 2>/dev/null || true
	@rm -f *.pyc 2>/dev/null || true
	@rm -f .*.swp 2>/dev/null || true
	@rm -f *~ 2>/dev/null || true
	@rm -f 412fe 2>/dev/null || true

build:
	@echo '#!/bin/bash' > 412fe
	@echo 'exec python3 "$(PWD)/main.py" "$$@"' >> 412fe
	@chmod a+x 412fe
	@dos2unix 412fe 2>/dev/null || sed -i 's/\r$$//' 412fe
	@chmod a+x *.py 2>/dev/null || true
