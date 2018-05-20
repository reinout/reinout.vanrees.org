install: install_symlinks install_python


install_symlinks: etc docs/copyover docs/source	rvo/templates/layout.html

etc:
	ln -s ../websitecontent/etc etc

docs/copyover:
	ln -s ../../websitecontent/copyover docs/copyover

docs/source:
	ln -s ../../websitecontent/source docs/source

rvo/templates/layout.html:
	ln -s ../../../websitecontent/source/_templates/layout.html rvo/templates/


install_python:
	pipenv install -e .
	mkdir -p var/log


# Make the docs
docs:
