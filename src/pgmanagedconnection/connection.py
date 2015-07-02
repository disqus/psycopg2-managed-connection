import logging
import threading
from contextlib import contextmanager

import psycopg2


logger = logging.getLogger(__name__)


class ManagedConnection(object):
    STATUS_IN_TRANSACTION = frozenset((
        psycopg2.extensions.TRANSACTION_STATUS_INERROR,
        psycopg2.extensions.TRANSACTION_STATUS_INTRANS,
    ))

    def __init__(self, dsn):
        self.dsn = dsn

        self.__connection = None

        # Barrier for when the `__connection` attribute is being modified.
        self.__connection_change_lock = threading.Lock()

        # Barrier to prevent multiple threads from utilizing the connection at
        # the same time to avoid interleaving transactions on the connection.
        self.__connection_usage_lock = threading.Lock()

    def __str__(self):
        return '%s' % (self.dsn,)

    def __repr__(self):
        return '<%s: %s (%s)>' % (
            type(self).__name__,
            self.dsn,
            self.__connection or 'closed',
        )

    @property
    def closed(self):
        with self.__connection_change_lock:
            if self.__connection is None:
                return True
            return self.__connection.closed

    @property
    def status(self):
        with self.__connection_change_lock:
            if self.__connection is None:
                return None
            return self.__connection.get_transaction_status()

    @contextmanager
    def __call__(self, close=False):
        # TODO: Support the ability to be non-blocking.
        def close_connection():
            try:
                self.__connection.close()
            except Exception as error:
                logger.info('Could not close connection: %s', error, exc_info=True)
            finally:
                with self.__connection_change_lock:
                    self.__connection = None

        with self.__connection_usage_lock:
            with self.__connection_change_lock:
                if not self.__connection or self.__connection.closed:
                    logger.debug('Connecting to %s...', self.dsn)
                    self.__connection = psycopg2.connect(self.dsn)

            try:
                yield self.__connection
            except Exception as error:
                if isinstance(error, psycopg2.Error):
                    close_connection()
                else:
                    if self.__connection.get_transaction_status() in self.STATUS_IN_TRANSACTION:
                        logger.warning('Forcing connection rollback after exception thrown in connection block: %s', error, exc_info=True)
                        self.__connection.rollback()
                raise
            else:
                # Check to make sure the client didn't leave the connection in a dirty state.
                if self.__connection.get_transaction_status() in self.STATUS_IN_TRANSACTION:
                    # We need to roll back the transaction in case the
                    # exception we raise below is caught and the manager is
                    # used again.
                    self.__connection.rollback()
                    raise RuntimeError("Did not commit or rollback open transaction before releasing connection.")

                if close:
                    close_connection()
