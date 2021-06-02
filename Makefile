install: uninstall clean build
	sudo pip install dist/*
clean:
	rm -rf build/ dist/ fiml.egg-info
	rm -rf **/__pycache__/
uninstall:
	yes | sudo pip uninstall fiml
build:
	python setup.py bdist_wheel

