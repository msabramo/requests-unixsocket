import requests

from .adapters import UnixAdapter

__all__ = ['monkeypatch', 'Session', 'UnixAdapter']

DEFAULT_SCHEME = 'http+unix://'


class Session(requests.Session):
    def __init__(self, url_scheme=DEFAULT_SCHEME, *args, **kwargs):
        super(Session, self).__init__(*args, **kwargs)
        self.mount(url_scheme, UnixAdapter())


class monkeypatch(object):
    def __init__(self, url_scheme=DEFAULT_SCHEME):
        self.session = Session()
        self.orig_requests_get = requests.get
        requests.get = self.session.get

    def __enter__(self):
        return self

    def __exit__(self, *args):
        requests.get = self.orig_requests_get
