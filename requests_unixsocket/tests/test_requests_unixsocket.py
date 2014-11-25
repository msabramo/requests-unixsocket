#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for requests_unixsocket"""

import multiprocessing
import os
import uuid

import pytest
import requests
import waitress

from requests_unixsocket import UnixAdapter


@pytest.fixture
def wsgiapp():
    def _wsgiapp(environ, start_response):
        start_response(
            '200 OK',
            [('X-Transport', 'unix domain socket'),
             ('X-Socket-Path', environ['SERVER_PORT']),
             ('X-Requested-Path', environ['PATH_INFO'])])
        return ['Hello world!']

    return _wsgiapp


@pytest.fixture
def usock_process(wsgiapp):
    class UnixSocketServerProcess(multiprocessing.Process):
        def __init__(self, *args, **kwargs):
            super(UnixSocketServerProcess, self).__init__(*args, **kwargs)
            self.unix_socket = self.get_tempfile_name()

        def get_tempfile_name(self):
            # I'd rather use tempfile.NamedTemporaryFile but IDNA limits
            # the hostname to 63 characters and we'll get a "InvalidURL:
            # URL has an invalid label" error if we exceed that.
            args = (os.stat(__file__).st_ino,
                    os.getpid(),
                    uuid.uuid4().hex[-8:])
            return '/tmp/test_requests.%s_%s_%s' % args

        def run(self):
            waitress.serve(wsgiapp, unix_socket=self.unix_socket)

    return UnixSocketServerProcess()


def test_unix_domain_adapter_ok(usock_process):
    from requests.compat import quote_plus

    usock_process.start()

    try:
        session = requests.Session()
        session.mount('http+unix://', UnixAdapter())
        urlencoded_socket_name = quote_plus(usock_process.unix_socket)
        url = 'http+unix://%s/path/to/page' % urlencoded_socket_name
        r = session.get(url)
        assert r.status_code == 200
        assert r.headers['server'] == 'waitress'
        assert r.headers['X-Transport'] == 'unix domain socket'
        assert r.headers['X-Requested-Path'] == '/path/to/page'
        assert r.headers['X-Socket-Path'] == usock_process.unix_socket
        assert isinstance(r.connection, UnixAdapter)
        assert r.url == url
        assert r.text == 'Hello world!'
    finally:
        usock_process.terminate()


def test_unix_domain_adapter_connection_error():
    session = requests.Session()
    session.mount('http+unix://', UnixAdapter())

    with pytest.raises(requests.ConnectionError):
        session.get('http+unix://socket_does_not_exist/path/to/page')
