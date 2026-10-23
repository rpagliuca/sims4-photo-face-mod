.PHONY: test test-python test-node build build-ts4script install-dev pack-papelao

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

# Coleção de caras de papelão que vem com o mod (as PNGs ficam versionadas;
# para redesenhá-las: python3 packages/cardboard_faces/gerar.py packages/cardboard_faces/png)
pack-papelao:
	cd companion && node src/index.js pack \
	  --dir ../packages/cardboard_faces/png \
	  --template ../packages/casp_template/base.package \
	  --output ../build/dist/PhotoFace_Papelao.package \
	  --manifest ../build/dist/photo_manifest_papelao.json
