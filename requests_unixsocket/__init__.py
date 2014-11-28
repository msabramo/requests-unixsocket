import requests
import sys

from .adapters import UnixAdapter

__all__ = ['monkeypatch', 'Session']

DEFAULT_SCHEME = 'http+unix://'


class Session(requests.Session):
    def __init__(self, url_scheme=DEFAULT_SCHEME, *args, **kwargs):
        super(Session, self).__init__(*args, **kwargs)
        self.mount(url_scheme, UnixAdapter())


class monkeypatch(object):
    def __init__(self, url_scheme=DEFAULT_SCHEME):
        self.session = Session()
        requests = self._get_global_requests_module()
        self.orig_requests_get = requests.get
        requests.get = self.session.get

    def _get_global_requests_module(self):
        return sys.modules['requests']

    def __enter__(self):
        return self

    def __exit__(self, *args):
        requests = self._get_global_requests_module()
        requests.get = self.orig_requests_get
