build:
	rm -rf ./dist
	python3 -m pip install --upgrade build
	python3 -m build

release:
	python3 -m pip install --upgrade twine
	python3 -m twine upload -u __token__ dist/*
