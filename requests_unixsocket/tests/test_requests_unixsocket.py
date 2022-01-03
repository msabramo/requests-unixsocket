#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for requests_unixsocket"""

import logging
import os
import stat

import pytest
import requests
from requests.compat import urlparse

from requests_unixsocket import monkeypatch, Session, Settings, UnixAdapter
from requests_unixsocket.testutils import UnixSocketServerThread


logger = logging.getLogger(__name__)


def is_socket(path):
    try:
        mode = os.stat(path).st_mode
        return stat.S_ISSOCK(mode)
    except OSError:
        return False


def get_sock_prefix(path):
    """Keep going up directory tree until we find a socket"""

    sockpath = path
    reqpath_parts = []

    while not is_socket(sockpath):
        sockpath, tail = os.path.split(sockpath)
        reqpath_parts.append(tail)

    return Settings.ParseResult(
        sockpath=sockpath,
        reqpath='/' + os.path.join(*reversed(reqpath_parts)),
    )


alt_settings_1 = Settings(
    urlparse=lambda url: get_sock_prefix(urlparse(url).path),
)


def test_use_UnixAdapter_directly():
    """Test using UnixAdapter directly, because
    https://github.com/httpie/httpie-unixsocket does this
    """
    adapter = UnixAdapter()
    prepared_request = requests.Request(
        method='GET',
        url='http+unix://%2Fvar%2Frun%2Fdocker.sock/info',
    ).prepare()
    url = adapter.request_url(request=prepared_request, proxies=None)
    assert url == '/info'


def test_unix_domain_adapter_ok():
    with UnixSocketServerThread() as usock_thread:
        session = Session('http+unix://')
        urlencoded_usock = requests.compat.quote_plus(usock_thread.usock)
        url = 'http+unix://%s/path/to/page' % urlencoded_usock

        for method in ['get', 'post', 'head', 'patch', 'put', 'delete',
                       'options']:
            logger.debug('Calling session.%s(%r) ...', method, url)
            r = getattr(session, method)(url)
            logger.debug(
                'Received response: %r with text: %r and headers: %r',
                r, r.text, r.headers)
            assert r.status_code == 200
            assert r.headers['server'] == 'waitress'
            assert r.headers['X-Transport'] == 'unix domain socket'
            assert r.headers['X-Requested-Path'] == '/path/to/page'
            assert r.headers['X-Socket-Path'] == usock_thread.usock
            assert isinstance(r.connection, UnixAdapter)
            assert r.url.lower() == url.lower()
            if method == 'head':
                assert r.text == ''
            else:
                assert r.text == 'Hello world!'


def test_unix_domain_adapter_alt_settings_1_ok():
    with UnixSocketServerThread() as usock_thread:
        session = Session(
            url_scheme='http+unix://',
            settings=alt_settings_1,
        )
        url = 'http+unix://localhost%s/path/to/page' % usock_thread.usock

        for method in ['get', 'post', 'head', 'patch', 'put', 'delete',
                       'options']:
            logger.debug('Calling session.%s(%r) ...', method, url)
            r = getattr(session, method)(url)
            logger.debug(
                'Received response: %r with text: %r and headers: %r',
                r, r.text, r.headers)
            assert r.status_code == 200
            assert r.headers['server'] == 'waitress'
            assert r.headers['X-Transport'] == 'unix domain socket'
            assert r.headers['X-Requested-Path'] == '/path/to/page'
            assert r.headers['X-Socket-Path'] == usock_thread.usock
            assert isinstance(r.connection, UnixAdapter)
            assert r.url.lower() == url.lower()
            if method == 'head':
                assert r.text == ''
            else:
                assert r.text == 'Hello world!'


def test_unix_domain_adapter_url_with_query_params():
    with UnixSocketServerThread() as usock_thread:
        session = Session('http+unix://')
        urlencoded_usock = requests.compat.quote_plus(usock_thread.usock)
        url = ('http+unix://%s'
               '/containers/nginx/logs?timestamp=true' % urlencoded_usock)

        for method in ['get', 'post', 'head', 'patch', 'put', 'delete',
                       'options']:
            logger.debug('Calling session.%s(%r) ...', method, url)
            r = getattr(session, method)(url)
            logger.debug(
                'Received response: %r with text: %r and headers: %r',
                r, r.text, r.headers)
            assert r.status_code == 200
            assert r.headers['server'] == 'waitress'
            assert r.headers['X-Transport'] == 'unix domain socket'
            assert r.headers['X-Requested-Path'] == '/containers/nginx/logs'
            assert r.headers['X-Requested-Query-String'] == 'timestamp=true'
            assert r.headers['X-Socket-Path'] == usock_thread.usock
            assert isinstance(r.connection, UnixAdapter)
            assert r.url.lower() == url.lower()
            if method == 'head':
                assert r.text == ''
            else:
                assert r.text == 'Hello world!'


def test_unix_domain_adapter_url_with_fragment():
    with UnixSocketServerThread() as usock_thread:
        session = Session('http+unix://')
        urlencoded_usock = requests.compat.quote_plus(usock_thread.usock)
        url = ('http+unix://%s'
               '/containers/nginx/logs#some-fragment' % urlencoded_usock)

        for method in ['get', 'post', 'head', 'patch', 'put', 'delete',
                       'options']:
            logger.debug('Calling session.%s(%r) ...', method, url)
            r = getattr(session, method)(url)
            logger.debug(
                'Received response: %r with text: %r and headers: %r',
                r, r.text, r.headers)
            assert r.status_code == 200
            assert r.headers['server'] == 'waitress'
            assert r.headers['X-Transport'] == 'unix domain socket'
            assert r.headers['X-Requested-Path'] == '/containers/nginx/logs'
            assert r.headers['X-Socket-Path'] == usock_thread.usock
            assert isinstance(r.connection, UnixAdapter)
            assert r.url.lower() == url.lower()
            if method == 'head':
                assert r.text == ''
            else:
                assert r.text == 'Hello world!'


def test_unix_domain_adapter_connection_error():
    session = Session('http+unix://')

    for method in ['get', 'post', 'head', 'patch', 'put', 'delete', 'options']:
        with pytest.raises(requests.ConnectionError):
            getattr(session, method)(
                'http+unix://socket_does_not_exist/path/to/page')


def test_unix_domain_adapter_connection_proxies_error():
    session = Session('http+unix://')

    for method in ['get', 'post', 'head', 'patch', 'put', 'delete', 'options']:
        with pytest.raises(ValueError) as excinfo:
            getattr(session, method)(
                'http+unix://socket_does_not_exist/path/to/page',
                proxies={"http+unix": "http://10.10.1.10:1080"})
        assert ('UnixAdapter does not support specifying proxies'
                in str(excinfo.value))


def test_unix_domain_adapter_monkeypatch():
    with UnixSocketServerThread() as usock_thread:
        with monkeypatch('http+unix://'):
            urlencoded_usock = requests.compat.quote_plus(usock_thread.usock)
            url = 'http+unix://%s/path/to/page' % urlencoded_usock

            for method in ['get', 'post', 'head', 'patch', 'put', 'delete',
                           'options']:
                logger.debug('Calling session.%s(%r) ...', method, url)
                r = getattr(requests, method)(url)
                logger.debug(
                    'Received response: %r with text: %r and headers: %r',
                    r, r.text, r.headers)
                assert r.status_code == 200
                assert r.headers['server'] == 'waitress'
                assert r.headers['X-Transport'] == 'unix domain socket'
                assert r.headers['X-Requested-Path'] == '/path/to/page'
                assert r.headers['X-Socket-Path'] == usock_thread.usock
                assert isinstance(r.connection,
                                  UnixAdapter)
                assert r.url.lower() == url.lower()
                if method == 'head':
                    assert r.text == ''
                else:
                    assert r.text == 'Hello world!'

    for method in ['get', 'post', 'head', 'patch', 'put', 'delete', 'options']:
        with pytest.raises(requests.exceptions.InvalidSchema):
            getattr(requests, method)(url)
