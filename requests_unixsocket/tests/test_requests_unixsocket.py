#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for requests_unixsocket"""

import logging
import os
import threading
import time
import uuid

import pytest
import requests
import waitress

import requests_unixsocket


logger = logging.getLogger(__name__)


class KillThread(threading.Thread):
    def __init__(self, server, *args, **kwargs):
        super(KillThread, self).__init__(*args, **kwargs)
        self.server = server

    def run(self):
        time.sleep(1)
        logger.debug('Sleeping')
        self.server._map.clear()


class WSGIApp:
    server = None

    def __call__(self, environ, start_response):
        logger.debug('WSGIApp.__call__: Invoked for %s', environ['PATH_INFO'])
        logger.debug('WSGIApp.__call__: environ = %r', environ)
        status_text = '200 OK'
        response_headers = [
            ('X-Transport', 'unix domain socket'),
            ('X-Socket-Path', environ['SERVER_PORT']),
            ('X-Requested-Path', environ['PATH_INFO'])]
        body_bytes = b'Hello world!'
        start_response(status_text, response_headers)
        logger.debug(
            'WSGIApp.__call__: Responding with '
            'status_text = %r; '
            'response_headers = %r; '
            'body_bytes = %r',
            status_text, response_headers, body_bytes)
        return [body_bytes]


class UnixSocketServerThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(UnixSocketServerThread, self).__init__(*args, **kwargs)
        self.usock = self.get_tempfile_name()
        self.server = None
        self.server_ready_event = threading.Event()

    def get_tempfile_name(self):
        # I'd rather use tempfile.NamedTemporaryFile but IDNA limits
        # the hostname to 63 characters and we'll get a "InvalidURL:
        # URL has an invalid label" error if we exceed that.
        args = (os.stat(__file__).st_ino, os.getpid(), uuid.uuid4().hex[-8:])
        return '/tmp/test_requests.%s_%s_%s' % args

    def run(self):
        logger.debug('Call waitress.serve in %r ...', self)
        wsgi_app = WSGIApp()
        server = waitress.create_server(wsgi_app, unix_socket=self.usock)
        wsgi_app.server = server
        self.server = server
        self.server_ready_event.set()
        server.run()

    def __enter__(self):
        logger.debug('Starting %r ...' % self)
        self.start()
        logger.debug('Started %r.', self)
        self.server_ready_event.wait()
        return self

    def __exit__(self, *args):
        self.server_ready_event.wait()
        if self.server:
            KillThread(self.server).start()


def test_unix_domain_adapter_ok():
    with UnixSocketServerThread() as usock_process:
        session = requests_unixsocket.Session('http+unix://')
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
        assert isinstance(r.connection, requests_unixsocket.UnixAdapter)
        assert r.url == url
        assert r.text == 'Hello world!'


def test_unix_domain_adapter_connection_error():
    session = requests_unixsocket.Session('http+unix://')

    with pytest.raises(requests.ConnectionError):
        session.get('http+unix://socket_does_not_exist/path/to/page')


def test_unix_domain_adapter_connection_proxies_error():
    session = requests_unixsocket.Session('http+unix://')

    with pytest.raises(ValueError) as excinfo:
        session.get('http+unix://socket_does_not_exist/path/to/page',
                    proxies={"http": "http://10.10.1.10:1080"})
    assert ('UnixAdapter does not support specifying proxies'
            in str(excinfo.value))


def test_unix_domain_adapter_monkeypatch():
    with UnixSocketServerThread() as usock_process:
        with requests_unixsocket.monkeypatch('http+unix://'):
            urlencoded_usock = requests.compat.quote_plus(usock_process.usock)
            url = 'http+unix://%s/path/to/page' % urlencoded_usock
            logger.debug('Calling requests.get(%r) ...', url)
            r = requests.get(url)
            logger.debug(
                'Received response: %r with text: %r and headers: %r',
                r, r.text, r.headers)
            assert r.status_code == 200
            assert r.headers['server'] == 'waitress'
            assert r.headers['X-Transport'] == 'unix domain socket'
            assert r.headers['X-Requested-Path'] == '/path/to/page'
            assert r.headers['X-Socket-Path'] == usock_process.usock
            assert isinstance(r.connection, requests_unixsocket.UnixAdapter)
            assert r.url == url
            assert r.text == 'Hello world!'

        with pytest.raises(requests.exceptions.InvalidSchema):
            requests.get(url)
