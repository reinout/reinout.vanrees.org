from distutils.core import setup

install_requires = [
    'Jinja2',
    'Sphinx',
    'docutils',
    ]

setup(name='rvo',
      version='0.1',
      packages=['rvo'],
      install_requires=install_requires,
      entry_points={
        'console_scripts': [
            'create-weblog-pages = rvo.weblog:main',
            'create-sermonlog = rvo.sermonlog:main',
            'create-homepage = rvo.homepage:main',
            'create-sitemap = rvo.sitemap:main',
            ]},
      )
