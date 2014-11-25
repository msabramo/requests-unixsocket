#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for requests_unixsocket"""

import logging
import multiprocessing
import os
import sys
import threading
import time
import uuid

import pytest
import requests
import waitress

from requests_unixsocket import UnixAdapter


logger = logging.getLogger(__name__)


class KillThread(threading.Thread):
    def __init__(self, server, *args, **kwargs):
        super(KillThread, self).__init__(*args, **kwargs)
        self.server = server

    def run(self):
        time.sleep(1)
        sys.stdout.write('*** Sleeping ***\n')
        self.server._map.clear()


def wsgiapp(server):
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    def _wsgiapp(environ, start_response):
        start_response(
            '200 OK',
            [('X-Transport', 'unix domain socket'),
             ('X-Socket-Path', environ['SERVER_PORT']),
             ('X-Requested-Path', environ['PATH_INFO'])])

        if environ.get('HTTP_X_SERVER_EXIT'):
            logger.debug(
                'Received poison pill. Server (pid %d) exiting',
                os.getpid())
            print(
                'Received poison pill. Server (pid %d) exiting'
                % os.getpid())

            KillThread(server).start()
            return [b'Received poison pill. Server (pid %d) exiting'
                    % os.getpid()]

        return [b'Hello world!']

    return _wsgiapp


class UnixSocketServerProcess(multiprocessing.Process):
    def __init__(self, *args, **kwargs):
        super(UnixSocketServerProcess, self).__init__(*args, **kwargs)
        self.usock = self.get_tempfile_name()

    def get_tempfile_name(self):
        # I'd rather use tempfile.NamedTemporaryFile but IDNA limits
        # the hostname to 63 characters and we'll get a "InvalidURL:
        # URL has an invalid label" error if we exceed that.
        args = (os.stat(__file__).st_ino, os.getpid(), uuid.uuid4().hex[-8:])
        return '/tmp/test_requests.%s_%s_%s' % args

    def run(self):
        logger.debug('Call waitress.serve in %r (pid %d) ...', self, self.pid)
        server = waitress.create_server(wsgiapp(None), unix_socket=self.usock)
        server.application = wsgiapp(server)
        server.run()
        # waitress.serve(wsgiapp(waitress), unix_socket=self.usock)

    def __enter__(self):
        logger.debug('Starting %r ...' % self)
        self.start()
        logger.debug('Started %r (pid %d)...', self, self.pid)
        return self

    def __exit__(self, *args):
        if False:
            logger.debug('Terminating %r (pid %d) ...', self, self.pid)
            self.terminate()
            logger.debug('Terminated %r (pid %d) ...', self, self.pid)


def test_unix_domain_adapter_ok():
    with UnixSocketServerProcess() as usock_process:
        session = requests.Session()
        session.mount('http+unix://', UnixAdapter())
        urlencoded_usock = requests.compat.quote_plus(usock_process.usock)
        url = 'http+unix://%s/path/to/page' % urlencoded_usock
        logger.debug('Calling session.get(%r) ...', url)
        r = session.get(url)
        logger.debug(
            'Received response: %r with text: %r and headers: %r',
            r, r.text, r.headers)
        assert r.status_code == 200
        assert r.headers['server'] == 'waitress'
        assert r.headers['X-Transport'] == 'unix domain socket'
        assert r.headers['X-Requested-Path'] == '/path/to/page'
        assert r.headers['X-Socket-Path'] == usock_process.usock
        assert isinstance(r.connection, UnixAdapter)
        assert r.url == url
        assert r.text == 'Hello world!'

        r = session.get(url, headers={'X-Server-Exit': 'Die die die'})
        assert r.status_code == 200


def test_unix_domain_adapter_connection_error():
    session = requests.Session()
    session.mount('http+unix://', UnixAdapter())

    with pytest.raises(requests.ConnectionError):
        session.get('http+unix://socket_does_not_exist/path/to/page')


def test_unix_domain_adapter_connection_proxies_error():
    session = requests.Session()
    session.mount('http+unix://', UnixAdapter())

    with pytest.raises(ValueError) as excinfo:
        session.get('http+unix://socket_does_not_exist/path/to/page',
                    proxies={"http": "http://10.10.1.10:1080"})
    assert ('UnixAdapter does not support specifying proxies'
            in str(excinfo.value))
