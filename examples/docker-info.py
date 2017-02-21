#!/usr/bin/env python

import json

import requests_unixsocket

session = requests_unixsocket.Session()

r = session.get('http+unix://%2Fvar%2Frun%2Fdocker.sock/info')
registry_config = r.json()['RegistryConfig']
print(json.dumps(registry_config, indent=4))
