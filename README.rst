reinout.vanrees.org software
============================

Very specific too-much-hardcoded code to manage my http://reinout.vanrees.org
website.

Install everything initially with::

  $ make install

This install also adds some symlinks to the separate (and private!)
``../websitecontent/`` directory. For privacy reasons, the ansible
provision/deploy scripts and the nginx config files are in that private repo.

The actual making of the sphinx documentation is done with a ``make html``
inside the docs directory. I do this normally by calling ``makedocs`` (from my
"tools" repo, whose scripts are installed globally).



Ideas for cleaning up my weblog code
------------------------------------

From time to time people ask me how I've made my blog with sphinx. Also
because I've got the top rated answer on stackoverflow for the "weblog with
sphinx" question: http://stackoverflow.com/a/1588720/27401 .

Note: there's http://ablog.readthedocs.org/ that uses sphinx and looks quite
polished. At least it is currently very much more reusable than my code :-)

Ablog works by marking certain pages as blog posts. My code works from a
``yyyy/mm/dd/entry.txt`` structure. Ablog also seems to "take over" your
entire sphinx site instead of my code, that hardcodes itself neatly into some
corner :-)

At the "django under the hood 2015" sprint, Eric Holscher pointed me at ablog
and also gave me some other tips.

One of the not-standard-sphinx things I do is that I have a "preprocessor
script" that generates ``index.txt`` files in all the subdirectories. It also
generates a ``tags/tagname.txt`` file per tag. All of those files are just a
title and a TOC pointing at the files.

TODO items so I can do to do away with the preprocessing:

- I can have a global TOC that automatically includes everything in my weblog
  directory. Apparently there's a ``:glob:`` configuration option for TOC, so
  I probably can put ``*/*/*/*.txt`` in there and delete all my ``index.txt``
  files.

- Instead of creating ``index.txt`` and tag "input files" beforehand and letting
  Sphinx take care of the rest, I can also generate "output files". So
  programmatically insert docs and nodes (or whatever the sphinx terminology
  is) into the doctree and let sphinx render it to the output html directory!

- For this, I need an accurate list, probably inside some sphinx memory
  structure, of blog posts and tags and their links.

- My sphinx "app" registers directives and connects to two signals at the
  moment. I should enhance this with other signals like ``doctree-read`` and
  ``doctree-resolved``, I think. See ``ablog/__init__.py`` for examples. This
  could do away with the custom scripts I have to call.

  Actually... I could perhaps even use it to retain my ``index.txt``
  generation, only now I fire it from within sphinx.... :-) For this, the
  ``builder-inited`` event seems best.
