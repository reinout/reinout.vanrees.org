install: install_symlinks install_python


install_symlinks: docs/copyover docs/source	rvo/templates/layout.html

docs/copyover:
	ln -s ~/SynologyDrive/notes/websitecontent/copyover docs/copyover

docs/source:
	ln -s ~/SynologyDrive/notes/websitecontent/source docs/source

rvo/templates/layout.html:
	ln -s ~/SynologyDrive/notes/websitecontent/source/_templates/layout.html rvo/templates/


install_python:
	pipenv install -e .
	mkdir -p var/log


# Make the docs
docs:
