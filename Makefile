# Exit upon error
.SHELLFLAGS = -e

install: install_symlinks install_python install_npm style

clean:
	rm -rf node_modules .venv docs/build

install_symlinks: docs/copyover docs/source rvo/templates/layout.html

docs/copyover:
	ln -s ~/zelf/websitecontent/copyover docs/copyover

docs/source:
	ln -s ~/zelf/websitecontent/source docs/source

rvo/templates/layout.html:
	ln -s ~/zelf/websitecontent/source/_templates/layout.html rvo/templates/

install_python:
	uv sync
	mkdir -p var/log

install_npm: node_modules/.bin/tailwindcss
	npm install .

style: docs/source/_static/vanrees.css

docs/source/_static/vanrees.css: docs/source/_static/input.css rvo/templates/*.html
	node_modules/.bin/tailwindcss -i docs/source/_static/input.css -o docs/source/_static/vanrees.css


# Make the docs
docs:
