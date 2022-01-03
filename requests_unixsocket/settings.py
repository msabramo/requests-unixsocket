from collections import namedtuple

from requests.compat import urlparse, unquote


class Settings(object):
    class ParseResult(namedtuple('ParseResult', 'sockpath reqpath')):
        pass

    def __init__(self, urlparse=None):
        self.urlparse = urlparse


def default_urlparse(url):
    parsed_url = urlparse(url)
    reqpath = parsed_url.path
    if parsed_url.query:
        reqpath += '?' + parsed_url.query
    return Settings.ParseResult(
        sockpath=unquote(parsed_url.netloc),
        reqpath=reqpath,
    )


default_scheme = 'http+unix://'
default_settings = Settings(urlparse=default_urlparse)
