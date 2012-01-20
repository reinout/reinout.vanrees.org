"""Script to create index, date and tag pages.
"""
# import datetime
# import os
# import sys
# import time

# from docutils.core import publish_parts
# from docutils.writers.html4css1 import Writer
from jinja2 import Environment
from jinja2 import PackageLoader

from rvo.weblog import utf8_open

jinja_env = Environment(loader=PackageLoader('rvo', 'templates'))


def conditional_write(filename, new):
    old = open(filename, 'r').read()
    if new != old:
        utf8_open(filename, 'w').write(new)
        print '.',


class Homepage(object):
    """Represents the homepage"""

    template = jinja_env.get_template('homepage.html')
    outfile = 'build/html/index.html'

    def __init__(self):
        pass

    def write(self):
        """Write out homepage"""
        conditional_write(self.outfile, self.content)

    @property
    def content(self):
        """Return rendered template, filled with content"""
        return self.template.render(weblogsnippet=self.weblogsnippet)

    @property
    def weblogsnippet(self):
        return utf8_open('build/html/weblog/snippet.html').read()


def main():
    homepage = Homepage()
    homepage.write()
