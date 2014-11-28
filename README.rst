requests-unixsocket
===================

.. image:: https://travis-ci.org/msabramo/requests-unixsocket.svg?branch=master
    :target: https://travis-ci.org/msabramo/requests-unixsocket

Use `requests <http://docs.python-requests.org/>`_ to talk HTTP via a UNIX domain socket

Usage
-----

Explicit
++++++++

You can use it by instantiating a special ``Session`` object:

.. code-block:: python

    import requests_unixsocket

    session = requests_unixsocket.Session('http+unix://')

    # Access /tmp/profilesvc.sock
    r = session.get('http+unix://%2Ftmp%2Fprofilesvc.sock/path/to/page')
    assert r.status_code == 200

Implicit (monkeypatching)
+++++++++++++++++++++++++

.. code-block:: python

    import requests_unixsocket

    with requests_unixsocket.monkeypatch('http+unix://'):
        # Access /tmp/profilesvc.sock
        r = requests.get('http+unix://%2Ftmp%2Fprofilesvc.sock/path/to/page')
        assert r.status_code == 200
