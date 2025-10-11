import os
import socket

from requests.adapters import HTTPAdapter
from requests.compat import urlparse, unquote

try:
    from requests.packages import urllib3
except ImportError:
    import urllib3


def get_unix_socket(path_or_name, timeout=None, type=socket.SOCK_STREAM):
    sock = socket.socket(family=socket.AF_UNIX, type=type)
    if timeout:
        sock.settimeout(timeout)
    sock.connect(path_or_name)
    return sock


def get_sock_path_and_req_path(path):
    i = 1
    while True:
        try:
            items = path.rsplit('/', i)
            sock_path = items[0]
            rest = items[1:]
        except ValueError:
            return None, None

        if os.path.exists(sock_path):
            return sock_path, '/' + '/'.join(rest)

        # Detect abstract namespace socket, starting with `/%00`
        if '/' not in sock_path[1:] and sock_path[1:4] == '%00':
            return '\x00' + sock_path[4:], '/' + '/'.join(rest)

        if sock_path == '':
            return None, None
        i += 1


# The following was adapted from some code from docker-py
# https://github.com/docker/docker-py/blob/master/docker/transport/unixconn.py
class UnixHTTPConnection(urllib3.connection.HTTPConnection, object):

    def __init__(self, unix_socket_url, timeout=60):
        """Create an HTTP connection to a unix domain socket

        :param unix_socket_url: A URL with a scheme of 'http+unix' and the
        netloc is a percent-encoded path to a unix domain socket. E.g.:
        'http+unix://%2Ftmp%2Fprofilesvc.sock/status/pid'
        """
        super(UnixHTTPConnection, self).__init__('localhost', timeout=timeout)
        self.unix_socket_url = unix_socket_url
        self.timeout = timeout
        self.sock = None

    def __del__(self):  # base class does not have d'tor
        if self.sock:
            self.sock.close()

    def connect(self):
        path = urlparse(self.unix_socket_url).path
        socket_path, req_path = get_sock_path_and_req_path(path)
        if not socket_path:
            socket_path = urlparse(self.unix_socket_url).path
        if '\x00' not in socket_path and not os.path.exists(socket_path):
            socket_path = unquote(urlparse(self.unix_socket_url).netloc)
        self.sock = get_unix_socket(socket_path, timeout=self.timeout)


class UnixHTTPConnectionPool(urllib3.connectionpool.HTTPConnectionPool):

    def __init__(self, socket_path, timeout=60):
        super(UnixHTTPConnectionPool, self).__init__(
            'localhost', timeout=timeout)
        self.socket_path = socket_path
        self.timeout = timeout

    def _new_conn(self):
        return UnixHTTPConnection(self.socket_path, self.timeout)


class UnixAdapter(HTTPAdapter):

    def __init__(self, timeout=60, pool_connections=25, *args, **kwargs):
        super(UnixAdapter, self).__init__(*args, **kwargs)
        self.timeout = timeout
        self.pools = urllib3._collections.RecentlyUsedContainer(
            pool_connections, dispose_func=lambda p: p.close()
        )

    # Fix for requests 2.32.2+: https://github.com/psf/requests/pull/6710
    def get_connection_with_tls_context(self, request, verify, proxies=None, cert=None):
        return self.get_connection(request.url, proxies)

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

            pool = UnixHTTPConnectionPool(url, self.timeout)
            self.pools[url] = pool

        return pool

    def request_url(self, request, proxies):
        sock_path, req_path = get_sock_path_and_req_path(request.path_url)
        if req_path:
            return req_path
        else:
            return request.path_url

    def close(self):
        self.pools.clear()
