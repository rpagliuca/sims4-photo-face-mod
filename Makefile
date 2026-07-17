.PHONY: test test-python test-node build build-ts4script install-dev

install-dev:
	pip install -r requirements-dev.txt
	cd companion && npm install

test: test-python test-node

test-python:
	pytest -q

test-node:
	cd companion && npm test

build: build-ts4script

build-ts4script:
	python build/build_ts4script.py
