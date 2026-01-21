import os
import requests
import sys

from .adapters import UnixAdapter

DEFAULT_SCHEMES = os.getenv(
    'REQUESTS_UNIXSOCKET_URL_SCHEMES',
    'http+unix://,http://sock.local/'
).split(',')


class Session(requests.Session):
    def __init__(self, url_schemes=DEFAULT_SCHEMES, *args, **kwargs):
        super(Session, self).__init__(*args, **kwargs)
        for url_scheme in url_schemes:
            self.mount(url_scheme, UnixAdapter())


class monkeypatch(object):
    def __init__(self, url_schemes=DEFAULT_SCHEMES):
        self.session = Session(url_schemes=url_schemes)
        requests = self._get_global_requests_module()

        # Methods to replace
        self.methods = ('request', 'get', 'head', 'post',
                        'patch', 'put', 'delete', 'options')
        # Store the original methods
        self.orig_methods = dict(
            (m, requests.__dict__[m]) for m in self.methods)
        # Monkey patch
        g = globals()
        for m in self.methods:
            requests.__dict__[m] = g[m]

    def _get_global_requests_module(self):
        return sys.modules['requests']

    def __enter__(self):
        return self

    def __exit__(self, *args):
        requests = self._get_global_requests_module()
        for m in self.methods:
            requests.__dict__[m] = self.orig_methods[m]


# These are the same methods defined for the global requests object
def request(method, url, **kwargs):
    session = Session()
    return session.request(method=method, url=url, **kwargs)


def get(url, **kwargs):
    kwargs.setdefault('allow_redirects', True)
    return request('get', url, **kwargs)


def head(url, **kwargs):
    kwargs.setdefault('allow_redirects', False)
    return request('head', url, **kwargs)


def post(url, data=None, json=None, **kwargs):
    return request('post', url, data=data, json=json, **kwargs)


def patch(url, data=None, **kwargs):
    return request('patch', url, data=data, **kwargs)


def put(url, data=None, **kwargs):
    return request('put', url, data=data, **kwargs)


def delete(url, **kwargs):
    return request('delete', url, **kwargs)


def options(url, **kwargs):
    kwargs.setdefault('allow_redirects', True)
    return request('options', url, **kwargs)
