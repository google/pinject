# Makefile
# Author: Huan LI https://github.com/huan

SOURCE_GLOB=$(wildcard bin/*.py pinject/*.py tests/*.py)

.PHONY: all
all : clean lint

.PHONY: clean
clean:
	rm -fv dist/*

.PHONY: install
install:
	pip install -r requirements_dev.txt

.PHONY: lint
lint: pylint pycodestyle flake8 mypy

.PHONY: pylint
pylint:
	pylint $(SOURCE_GLOB)

.PHONY: pycodestyle
pycodestyle:
	pycodestyle --statistics --count $(SOURCE_GLOB)

.PHONY: flake8
flake8:
	flake8 $(SOURCE_GLOB)

.PHONY: mypy
mypy:
	MYPYPATH=stubs/ mypy \
		$(SOURCE_GLOB)

.PHONY: pytest
pytest:
	PYTHONPATH=. pytest pinject/ tests/

.PHONY: test
test: pytest

.PHONY: pack
pack:
	python3 setup.py sdist bdist_wheel

.PHONY: publish-test
publish-test:
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

.PHONY: publish
publish:
	twine upload dist/*

.PHONY: version-patch
version-patch:
	echo 'bump patch version'
