#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for requests_unixsocket"""

import logging

import pytest
import requests

import requests_unixsocket
from requests_unixsocket.testutils import UnixSocketServerThread


logger = logging.getLogger(__name__)


def test_unix_domain_adapter_ok():
    with UnixSocketServerThread() as usock_thread:
        session = requests_unixsocket.Session('http+unix://')
        urlencoded_usock = requests.compat.quote_plus(usock_thread.usock)
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
        assert r.headers['X-Socket-Path'] == usock_thread.usock
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
    with UnixSocketServerThread() as usock_thread:
        with requests_unixsocket.monkeypatch('http+unix://'):
            urlencoded_usock = requests.compat.quote_plus(usock_thread.usock)
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
            assert r.headers['X-Socket-Path'] == usock_thread.usock
            assert isinstance(r.connection, requests_unixsocket.UnixAdapter)
            assert r.url == url
            assert r.text == 'Hello world!'

        with pytest.raises(requests.exceptions.InvalidSchema):
            requests.get(url)
