import socket

from requests.adapters import HTTPAdapter
from requests.compat import unquote

try:
    from requests.packages import urllib3
    from requests.packages.urllib3.util import parse_url
except ImportError:
    import urllib3
    from urllib3.util import parse_url


# The following was adapted from some code from docker-py
# https://github.com/docker/docker-py/blob/master/docker/transport/unixconn.py
class UnixHTTPConnection(urllib3.connection.HTTPConnection):

    def __init__(self, unix_socket_url, timeout=60):
        """Create an HTTP connection to a unix domain socket

        :param unix_socket_url: A URL with a scheme of 'http+unix' and the
        netloc is a percent-encoded path to a unix domain socket. E.g.:
        'http+unix://%2Ftmp%2Fprofilesvc.sock/status/pid'
        """
        super().__init__('localhost', timeout=timeout)
        self.unix_socket_url = unix_socket_url
        self.timeout = timeout
        self.sock = None

    def __del__(self):  # base class does not have d'tor
        if self.sock:
            self.sock.close()

    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        socket_path = unquote(parse_url(self.unix_socket_url).host)
        sock.connect(socket_path)
        self.sock = sock

    def __str__(self):
        return (
            f"{type(self).__name__}("
            f"unix_socket_url={self.unix_socket_url!r}, "
            f"timeout={self.timeout!r}"
            ")"
        )


class UnixHTTPConnectionPool(urllib3.connectionpool.HTTPConnectionPool):

    def __init__(self, socket_path, timeout=60):
        super().__init__('localhost', timeout=timeout)
        self.socket_path = socket_path
        self.timeout = timeout

    def _new_conn(self):
        return UnixHTTPConnection(self.socket_path, self.timeout)

    def __str__(self):
        return (
            f"{type(self).__name__}("
            f"socket_path={self.socket_path!r}, "
            f"timeout={self.timeout!r}"
            ")"
        )


class UnixAdapter(HTTPAdapter):

    def __init__(self, timeout=60, pool_connections=25, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = timeout
        self.pools = urllib3._collections.RecentlyUsedContainer(
            pool_connections, dispose_func=lambda p: p.close()
        )

    # Fix for requests 2.32.2+: https://github.com/psf/requests/pull/6710
    def get_connection_with_tls_context(self, request, verify, proxies=None, cert=None):
        return self.get_connection(request.url, proxies)

    def get_connection(self, url, proxies=None):
        proxies = proxies or {}
        proxy = proxies.get(parse_url(url).scheme.lower())

        if proxy:
            raise ValueError('%s does not support specifying proxies'
                             % self.__class__.__name__)

        with self.pools.lock:
            pool = self.pools.get(url)
            if pool:
                return pool

            pool = UnixHTTPConnectionPool(url, self.timeout)
            self.pools[url] = pool

        return pool

    def request_url(self, request, proxies):
        return request.path_url

    def close(self):
        self.pools.clear()
