import socket

from requests.adapters import HTTPAdapter
from requests.compat import urlparse, unquote

try:
    import http.client as httplib
except ImportError:
    import httplib

try:
    from requests.packages import urllib3
except ImportError:
    import urllib3


# The following was adapted from some code from docker-py
# https://github.com/docker/docker-py/blob/master/docker/transport/unixconn.py
class UnixHTTPConnection(httplib.HTTPConnection, object):

    def __init__(self, unix_socket_url):
        """Create an HTTP connection to a unix domain socket

        :param unix_socket_url: A URL with a scheme of 'http+unix' and the
        netloc is a percent-encoded path to a unix domain socket. E.g.:
        'http+unix://%2Ftmp%2Fprofilesvc.sock/status/pid'
        """
        super(UnixHTTPConnection, self).__init__('localhost')
        self.unix_socket_url = unix_socket_url
        self.sock = None

    def __del__(self):  # base class does not have d'tor
        if self.sock:
            self.sock.close()

    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        socket_path = unquote(urlparse(self.unix_socket_url).netloc)
        sock.connect(socket_path)
        self.sock = sock


class UnixHTTPConnectionPool(urllib3.connectionpool.HTTPConnectionPool):

    def __init__(self, socket_path):
        super(UnixHTTPConnectionPool, self).__init__('localhost')
        self.socket_path = socket_path

    def _new_conn(self):
        return UnixHTTPConnection(self.socket_path)


class UnixAdapter(HTTPAdapter):

    def __init__(self, pool_connections=25, *args, **kwargs):
        super(UnixAdapter, self).__init__(*args, **kwargs)
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

            pool = UnixHTTPConnectionPool(url)
            self.pools[url] = pool

        return pool

    def request_url(self, request, proxies):
        return request.path_url

    def close(self):
        self.pools.clear()
