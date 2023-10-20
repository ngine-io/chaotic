clean:
	rm -rf *.egg-info
	rm -rf *.dist-info
	rm -rf dist
	rm -rf build
	find -name '__pycache__' -exec rm -fr {} || true \;

build: clean
	python3 setup.py sdist bdist_wheel

test-release:
	twine upload --repository testpypi dist/*

release:
	twine upload dist/*

test:
	tox

update:
	pip-compile -U --no-header --no-annotate --strip-extras --resolver backtracking
	pip-sync
