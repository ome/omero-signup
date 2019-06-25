#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
import string
from datetime import datetime
from uuid import uuid4

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader as template_loader
from django.template import RequestContext as Context
from django.utils.encoding import smart_str
from django.views.generic import View
from django.core.urlresolvers import reverse

import omero
from omeroweb.decorators import (
    login_required,
    parse_url,
)
from omero_version import (
    build_year,
    omero_version,
)

from omeroweb.webclient.webclient_gateway import OmeroWebGateway
from .forms import SignupForm
import signup_settings


logger = logging.getLogger(__name__)


class WebSignupView(View):
    """
    Webclient Signup
    """

    form_class = SignupForm
    useragent = 'OMERO.signup'

    def get(self, request, **kwargs):
        """
        Return the signup page if user is not signed in
        """
        r = self.handle_logged_in(request, **kwargs)
        if r:
            return r
        return self.handle_not_logged_in(request)

    def handle_logged_in(self, request, **kwargs):
        """
        If logged in redirect to main webclient, otherwise return None
        """
        # Abuse the @login_required decorator since it contains the
        # methods to check for an existing session
        check = login_required()

        # Copied from
        # https://github.com/openmicroscopy/openmicroscopy/blob/v5.4.10/components/tools/OmeroWeb/omeroweb/decorators.py#L448
        conn = kwargs.get('conn', None)
        server_id = kwargs.get('server_id', None)
        if conn is None:
            try:
                conn = check.get_connection(server_id, request)
            except Exception:
                conn = None
        if conn is not None:
            logger.error('Logged in')
            try:
                url = parse_url(settings.LOGIN_REDIRECT)
            except Exception:
                url = reverse("webindex")
            return HttpResponseRedirect(url)

    def handle_not_logged_in(self, request, error=None, form=None):
        """
        Signup form
        """

        # Store id in session to prevent forum resubmission
        requestid = str(uuid4())
        request.session['requestid'] = requestid

        if form is None:
            form = self.form_class()
        context = {
            'version': omero_version,
            'build_year': build_year,
            'error': error,
            'form': form,
            'requestid': requestid,
            'helpmessage': signup_settings.SIGNUP_HELP_MESSAGE,
        }
        if hasattr(settings, 'LOGIN_LOGO'):
            context['LOGIN_LOGO'] = settings.LOGIN_LOGO

        t = template_loader.get_template('signup/index.html')
        c = Context(request, context)
        rsp = t.render(c)
        return HttpResponse(rsp)

    def post(self, request):
        """
        Creates a new account
        """
        error = None
        form = self.form_class(request.POST.copy())

        session_requestid = request.session.pop('requestid', None)
        post_requestid = request.POST.get('requestid')
        if not session_requestid or session_requestid != post_requestid:
            error = 'Invalid requestid: %s' % post_requestid

        if not error and form.is_valid():
            user = dict(
                firstname=form.cleaned_data['firstname'],
                lastname=form.cleaned_data['lastname'],
                institution=form.cleaned_data['institution'],
                email=form.cleaned_data['email'],
            )
            omeuser = self.create_account(user)

            context = {
                'version': omero_version,
                'build_year': build_year,
                'username': omeuser['login'],
                'password': omeuser['password'],
                'email': omeuser['email'],
                'helpmessage': signup_settings.SIGNUP_HELP_MESSAGE,
            }
            if hasattr(settings, 'LOGIN_LOGO'):
                context['LOGIN_LOGO'] = settings.LOGIN_LOGO
            t = template_loader.get_template('signup/acknowledge.html')
            c = Context(request, context)
            rsp = t.render(c)
            return HttpResponse(rsp)
        else:
            return self.handle_not_logged_in(request, error, form)

    def create_account(self, user):
        """
        Create a new user account using the default OMERO.server
        """
        signup_host, signup_port, _ = settings.SERVER_LIST[0]
        adminc = OmeroWebGateway(
            host=signup_host,
            port=signup_port,
            username=signup_settings.SIGNUP_ADMIN_USERNAME,
            passwd=signup_settings.SIGNUP_ADMIN_PASSWORD,
            secure=True)
        if not adminc.connect():
            raise Exception('Failed to create account '
                            '(unable to obtain admin connection)')
        gid = self._get_or_create_group(adminc, user)
        omeuser = self._create_user(adminc, user, gid)
        if signup_settings.SIGNUP_EMAIL_ENABLED:
            self._email_user(adminc.c, omeuser)
            omeuser['password'] = None
        return omeuser

    def _get_new_login(self, adminc, user):
        omename = '%s%s' % (user['firstname'], user['lastname'])
        omename = ''.join(c for c in omename if c.isalnum())
        e = adminc.getObject('Experimenter', attributes={'omeName': omename})
        if not e:
            return omename

        n = 0
        while n < 99:
            n += 1
            checkname = '%s%d' % (omename, n)
            e = adminc.getObject(
                'Experimenter', attributes={'omeName': checkname})
            if not e:
                return checkname

        raise Exception('Failed to generate username after %d attempts' % n)

    def _get_or_create_group(self, adminc, user):
        groupname = signup_settings.SIGNUP_GROUP_NAME
        if signup_settings.SIGNUP_GROUP_NAME_TEMPLATETIME:
            groupname = datetime.now().strftime(groupname)
        g = adminc.getObject(
            'ExperimenterGroup', attributes={'name': groupname})
        if g:
            gid = g.id
        else:
            logger.info('Creating new signup group: %s %s', groupname,
                        signup_settings.SIGNUP_GROUP_PERMS)
            # Parent methods BlitzGateway.createGroup is easier to use than
            # the child method
            gid = super(OmeroWebGateway, adminc).createGroup(
                name=groupname, perms=signup_settings.SIGNUP_GROUP_PERMS)
        return gid

    def _create_user(self, adminc, user, groupid):
        """
        Automatically converts Django form strings to whatever OMERO needs.
        https://github.com/openmicroscopy/openmicroscopy/blob/v5.5.0/components/tools/OmeroWeb/omeroweb/custom_forms.py#L63
        """
        def _convert_unicode(s):
            return str(smart_str(s))

        omeuser = dict((k, _convert_unicode(v)) for (k, v) in user.items())
        omeuser['login'] = _convert_unicode(self._get_new_login(adminc, user))
        omeuser['password'] = ''.join(random.choice(
            string.ascii_letters + string.digits) for n in xrange(12))

        logger.info('Creating new signup user: %s group: %d', omeuser, groupid)
        omeuser['uid'] = adminc.createExperimenter(
            omeName=omeuser['login'],
            firstName=omeuser['firstname'],
            lastName=omeuser['lastname'],
            email=omeuser['email'],
            isAdmin=False,
            isActive=True,
            defaultGroupId=groupid,
            otherGroupIds=[],
            password=omeuser['password'],
            institution=omeuser['institution']
        )
        return omeuser

    def _email_user(self, client, omeuser):
        body = signup_settings.SIGNUP_EMAIL_BODY.replace('\\n', '\n').format(
            username=omeuser['login'], password=omeuser['password'])
        req = omero.cmd.SendEmailRequest(
            subject=signup_settings.SIGNUP_EMAIL_SUBJECT,
            body=body,
            userIds=[omeuser['uid']],
            groupIds=[],
            everyone=False,
            inactive=True)
        cb = client.submit(req, loops=10, ms=500,
                           failonerror=True, failontimeout=True)
        try:
            rsp = cb.getResponse()
            if rsp.invalidemails:
                raise Exception('Invalid email: %s' % rsp.invalidemails)
        finally:
            cb.close(True)
