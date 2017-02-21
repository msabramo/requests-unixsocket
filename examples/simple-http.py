#!/usr/bin/env python

import sys

import requests_unixsocket

session = requests_unixsocket.Session()

url = sys.argv[1]
res = session.get(url)
print(res.text)
