from setuptools import setup

PACKAGE = 'AddMultipleChildren'
VERSION = '0.3'

setup(name=PACKAGE,
      version=VERSION,
      packages=['addMultipleChildren'],
      entry_points={'trac.plugins': '%s = addMultipleChildren' % PACKAGE},
      package_data={'addMultipleChildren': ['templates/*.html',
                                            'htdocs/css/*.css',
                                            'htdocs/images/*']},
)
