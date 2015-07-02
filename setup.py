import os
from setuptools import (
    find_packages,
    setup,
)
from setuptools.command.test import test


PACKAGE_DIR = 'src'


class PyTest(test):
    def finalize_options(self):
        test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest, sys
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='psycopg2-managed-connection',
    description='Thread-safe connection manager for psycopg2 connections.',
    version='1.0.0',
    author='Ted Kaemming, Disqus',
    author_email='ted@disqus.com',
    license='Apache License 2.0',
    setup_requires=(
        'setuptools>=8.0',
    ),
    install_requires=(
        'psycopg2~=2.6',
    ),
    packages=find_packages(PACKAGE_DIR),
    package_dir={
        '': PACKAGE_DIR,
    },
    zip_safe=False,
    cmdclass = {
        'test': PyTest,
    },
    tests_require=(
        'pytest~=2.7',
    ),
)
