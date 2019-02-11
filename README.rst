.. image:: https://travis-ci.org/openmicroscopy/omero-signup.svg?branch=master
    :target: https://travis-ci.org/openmicroscopy/omero-webtest


OMERO.signup
============
OMERO.web app to allow anyone to signup for an OMERO account.


Requirements
============

* OMERO.web 5.4 or newer.


Installation
============

This section assumes that an OMERO.web is already installed.

::

    $ python setup.py install

Required configuration:

::

    $ bin/omero config append omero.web.apps '"omero_signup"'

    $ bin/omero config set omero.web.signup.host omero.example.org
    $ bin/omero config set omero.web.signup.admin.user omero-admin
    $ bin/omero config set omero.web.signup.admin.password omero-password
    $ bin/omero config set omero.web.signup.group.name user-group-name


Optional configuration:

::

    $ bin/omero config set omero.web.signup.port 4064
    $ bin/omero config set omero.web.signup.group.perms rw----
    $ bin/omero config set omero.web.signup.email.subject ...
    $ bin/omero config set omero.web.signup.email.body ...

``omero.web.signup.email.body`` should include template strings ``{username}`` and ``{password}`` that will be substituted with the created user's username and password.


License
-------

OMERO.webtest is released under the AGPL.

Copyright
---------

2019, The Open Microscopy Environment
