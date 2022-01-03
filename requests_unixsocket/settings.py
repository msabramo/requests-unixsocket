from collections import namedtuple

from requests.compat import urlparse, unquote


class Settings(object):
    class ParseResult(namedtuple('ParseResult', 'sockpath reqpath')):
        pass

    def __init__(self, urlparse=None):
        self.urlparse = urlparse


def default_urlparse(url):
    parsed_url = urlparse(url)
    return Settings.ParseResult(
        sockpath=unquote(parsed_url.netloc),
        reqpath=parsed_url.path + '?' + parsed_url.query,
    )


default_scheme = 'http+unix://'
default_settings = Settings(urlparse=default_urlparse)
