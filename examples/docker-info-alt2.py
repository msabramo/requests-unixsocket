#!/usr/bin/env python

import json
from requests.compat import urlparse

from requests_unixsocket import Session, Settings


def custom_urlparse(url):
    parsed_url = urlparse(url)
    return Settings.ParseResult(
        sockpath=parsed_url.path,
        reqpath=parsed_url.fragment,
    )


session = Session(settings=Settings(urlparse=custom_urlparse))

r = session.get('http+unix://sock.localhost/var/run/docker.sock#/info')
registry_config = r.json()['RegistryConfig']
print(json.dumps(registry_config, indent=4))
