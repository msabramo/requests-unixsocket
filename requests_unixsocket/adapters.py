import socket

from requests.adapters import HTTPAdapter
from requests.compat import urlparse

try:
    import http.client as httplib
except ImportError:
    import httplib

try:
    from requests.packages import urllib3
except ImportError:
    import urllib3

from .settings import default_settings

# The following was adapted from some code from docker-py
# https://github.com/docker/docker-py/blob/master/docker/transport/unixconn.py
class UnixHTTPConnection(httplib.HTTPConnection, object):

    def __init__(self, url, timeout=60, settings=None):
        """Create an HTTP connection to a unix domain socket"""
        super(UnixHTTPConnection, self).__init__('localhost', timeout=timeout)
        self.url = url
        self.timeout = timeout
        self.settings = settings
        self.sock = None

    def __del__(self):  # base class does not have d'tor
        if self.sock:
            self.sock.close()

    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sockpath = self.settings.urlparse(self.url).sockpath
        sock.connect(sockpath)
        self.sock = sock


class UnixHTTPConnectionPool(urllib3.connectionpool.HTTPConnectionPool):

    def __init__(self, socket_path, timeout=60, settings=None):
        super(UnixHTTPConnectionPool, self).__init__(
            'localhost', timeout=timeout)
        self.socket_path = socket_path
        self.timeout = timeout
        self.settings = settings

    def _new_conn(self):
        return UnixHTTPConnection(
            url=self.socket_path,
            timeout=self.timeout,
            settings=self.settings,
        )


class UnixAdapter(HTTPAdapter):
    def __init__(self, timeout=60, pool_connections=25,
                 settings=None,
                 *args, **kwargs):
        super(UnixAdapter, self).__init__(*args, **kwargs)
        self.settings = settings or default_settings
        self.timeout = timeout
        self.pools = urllib3._collections.RecentlyUsedContainer(
            pool_connections, dispose_func=lambda p: p.close()
        )

    def get_connection(self, url, proxies=None):
        proxies = proxies or {}
        proxy = proxies.get(urlparse(url.lower()).scheme)

        if proxy:
            raise ValueError('%s does not support specifying proxies'
                             % self.__class__.__name__)

        with self.pools.lock:
            pool = self.pools.get(url)
            if pool:
                return pool

            pool = UnixHTTPConnectionPool(
                socket_path=url,
                settings=self.settings,
                timeout=self.timeout,
            )
            self.pools[url] = pool

        return pool

    def request_url(self, request, proxies):
        return self.settings.urlparse(request.url).reqpath

    def close(self):
        self.pools.clear()
