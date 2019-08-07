.. image:: https://travis-ci.org/ome/omero-signup.svg?branch=master
    :target: https://travis-ci.org/ome/omero-signup


OMERO.signup
============
OMERO.web app to allow anyone to signup for an OMERO account.

Generated usernames are formed from the alphanumeric unicode characters in a user's first and last names, with a numeric suffix if the username already exists.
If OMERO.web is configured to connect ot multiple OMERO servers the user account will be created on the default one.


Requirements
------------

* OMERO.web 5.4 or newer.


Installation
------------

This section assumes that an OMERO.web is already installed.

::

    $ python setup.py install
    $ omero config append omero.web.apps '"omero_signup"'

Required configuration settings:

- ``omero.web.signup.admin.user``: OMERO admin username, must have permission to create groups and users
- ``omero.web.signup.admin.password``: Password for OMERO admin username
- ``omero.web.signup.group.name``: Default group for new users, will be created if it doesn't exist


Optional configuration settings:

- ``omero.web.signup.group.templatetime``: If ``True`` expand ``omero.web.signup.group.name`` using ``strftime`` to enable time-based groups, default disabled
- ``omero.web.signup.group.perms``: Permissions on default group for new users if it doesn't exist

These configuration settings are untested due to the difficulty of configuring email on a test server:

- ``omero.web.signup.email.enabled``: If ``True`` send emails to new users with their username and password instead of displaying the password, default disabled
- ``omero.web.signup.email.subject``: Email subject for new-user emails
- ``omero.web.signup.email.body``: Email body for new-user emails.
  It should include template strings ``{username}`` and ``{password}`` that will be substituted with the created user's username and password.

Example:

::

    $ omero config get
    omero.web.apps=["omero_signup"]
    omero.web.signup.admin.password=root-password
    omero.web.signup.admin.user=root
    omero.web.signup.group.name=testgroup-%Y-%m
    omero.web.signup.group.templatetime=true
    omero.web.signup.host=localhost


Restart OMERO.web in the usual way.

::

    $ omero web restart


New users will be able to sign-up for an account at http://omero.web.host/signup.


Release process
---------------

Use `bumpversion
<https://pypi.org/project/bump2version/>`_ to increment the version, commit and tag the repo.

::

    $ bumpversion patch
    $ git push origin master
    $ git push --tags


License
-------

OMERO.signup is released under the AGPL.

Copyright
---------

2019, The Open Microscopy Environment
