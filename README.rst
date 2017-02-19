requests-unixsocket
===================

.. image:: https://badge.fury.io/py/requests-unixsocket.svg
    :target: https://badge.fury.io/py/requests-unixsocket
    :alt: Latest Version on PyPI
    
.. image:: https://travis-ci.org/msabramo/requests-unixsocket.svg?branch=master
    :target: https://travis-ci.org/msabramo/requests-unixsocket

Use `requests <http://docs.python-requests.org/>`_ to talk HTTP via a UNIX domain socket

Usage
-----

Explicit
++++++++

You can use it by instantiating a special ``Session`` object:

.. code-block:: python

    import json

    import requests_unixsocket

    session = requests_unixsocket.Session()

    r = session.get('http+unix://%2Fvar%2Frun%2Fdocker.sock/info')
    registry_config = r.json()['RegistryConfig']
    print(json.dumps(registry_config, indent=4))


Implicit (monkeypatching)
+++++++++++++++++++++++++

Monkeypatching allows you to use the functionality in this module, while making
minimal changes to your code. Note that in the above example we had to
instantiate a special ``requests_unixsocket.Session`` object and call the
``get`` method on that object. Calling ``requests.get(url)`` (the easiest way
to use requests and probably very common), would not work. But we can make it
work by doing monkeypatching.

You can monkeypatch globally:

.. code-block:: python

    import requests_unixsocket

    requests_unixsocket.monkeypatch()

    r = requests.get('http+unix://%2Fvar%2Frun%2Fdocker.sock/info')
    assert r.status_code == 200

or you can do it temporarily using a context manager:

.. code-block:: python

    import requests_unixsocket

    with requests_unixsocket.monkeypatch():
        r = requests.get('http+unix://%2Fvar%2Frun%2Fdocker.sock/info')
        assert r.status_code == 200
