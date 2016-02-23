psycopg2-managed-connection
###########################

|pypi|

This package includes a managed connection for psycopg2_ that provides
thread-safe exclusive access to an underlying ``psycopg2.connection`` object.

This allows many threads to share the same connection instance (avoiding the
TCP and process startup cost associated with establishing a new PostgreSQL
connection) and ensures that threads do not release the connection with a
transaction still in progress -- either due to developer error, or an unhandled
exception while a thread is interacting with the database.

``ManagedConnection`` also will ensure that a connection that is closed upon
entering the managed context will be opened.

Installation
============

This package is released on PyPI_ as ``psycopg2-managed-connection`` and can be
installed via pip_:

.. code:: bash

    $ pip install psycopg2-managed-connection

Usage
=====

Creating a Managed Connection
-----------------------------

.. code:: python

    >>> from pgmanagedconnection import ManagedConnection
    >>>
    >>> dsn = 'postgres:///postgres'  # a libpq connection string
    >>> manager = ManagedConnection(dsn)
    >>> manager
    <ManagedConnection: postgres:///postgres (closed)>

Making Queries
--------------

.. code:: python

    >>> with manager() as connection:
    ...     cursor = connection.cursor()
    ...     cursor.execute('SELECT 1')
    ...     cursor.fetchone()
    ...     connection.commit()
    (1,)

Dealing with Uncommitted Transactions
-------------------------------------

Leaving a transaction open when exiting the context manager will lead to a
``RuntimeError``. This also results in any open transactions implicitly being
rolled back.

.. code:: python

    >>> with manager() as connection:
    ...    cursor = connection.cursor()
    ...    cursor.execute('SELECT 1')
    Traceback (most recent call last):
        ...
    RuntimeError: Did not commit or rollback open transaction before releasing connection.

Dealing with Errors
-------------------

The currently open transaction will be rolled back if an unhandled exception is
encountered.

.. code:: python

    >>> import psycopg2
    >>> with manager() as connection:
    ...    cursor = connection.cursor()
    ...    cursor.execute('SELECT 1')
    ...    assert manager.status is psycopg2.extensions.TRANSACTION_STATUS_INTRANS
    ...    raise NotImplementedError()
    Traceback (most recent call last):
        ...
    NotImplementedError
    >>> manager.status is psycopg2.extensions.TRANSACTION_STATUS_IDLE
    True

Development
===========

Testing
-------

The test suite can be run with ``make test``. This will run the test suite using
the version used by your local ``python`` command. You can force usage of ``python3``
by running ``make test3``.

It assumes a running and accessible PostgreSQL server. The connection details
are deferred to the underlying ``libpq`` implementation, and default values can
be specified using `libpq environment variables`_.

tox_ is also supported as a test runner (if installed.)

Testing with Docker
~~~~~~~~~~~~~~~~~~~

.. code:: bash

    $ export PGPORT=5432
    $ docker run -dp $PGPORT:5432 postgres
    $ PGUSER=postgres make test

If using boot2docker_, the ``PGHOST`` environment variable will also need to be
set to the virtual machine IP address.

.. code:: bash

    $ PGUSER=postgres PGHOST=$(boot2docker ip) make test


.. _PyPI: https://pypi.python.org/pypi/psycopg2-managed-connection
.. _`libpq environment variables`: http://www.postgresql.org/docs/9.3/static/libpq-envars.html
.. _boot2docker: https://github.com/boot2docker/boot2docker
.. _pip: https://pypi.python.org/pypi/pip
.. _psycopg2: https://pypi.python.org/pypi/psycopg2/
.. _tox: https://pypi.python.org/pypi/tox

.. |pypi| image:: https://img.shields.io/pypi/v/psycopg2-managed-connection.svg?style=flat-square&label=latest%20version
    :target: https://pypi.python.org/pypi/psycopg2-managed-connection
    :alt: Latest version released on PyPi
