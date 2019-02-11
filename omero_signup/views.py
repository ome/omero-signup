#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
import string

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader as template_loader
from django.template import RequestContext as Context
from django.views.generic import View
from django.core.urlresolvers import reverse

import omero
from omero.gateway import BlitzGateway
from omero.model import (
    ExperimenterI,
    ExperimenterGroupI,
    PermissionsI,
)
from omero.rtypes import (
    rbool,
    rstring,
)
from omeroweb.decorators import (
    login_required,
    parse_url,
)
from omero_version import (
    build_year,
    omero_version,
)

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
        GET simply returns the login page
        """
        r = self.handle_logged_in(request, **kwargs)
        if r:
            return r
        return self.handle_not_logged_in(request)

    def handle_logged_in(self, request, **kwargs):
        """
        Already logged in, redirect to main webclient
        """
        # Abuse the @login_required decorateor since it contains the
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
            except:
                url = reverse("webindex")
            return HttpResponseRedirect(url)

    def handle_not_logged_in(self, request, error=None, form=None):
        """
        Signup form
        """
        if form is None:
            form = self.form_class()
        context = {
            'version': omero_version,
            'build_year': build_year,
            'error': error,
            'form': form
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

        if form.is_valid():
            user = dict(
                firstname=form.cleaned_data['firstname'],
                lastname=form.cleaned_data['lastname'],
                institution=form.cleaned_data['institution'],
                email=form.cleaned_data['email'],
            )
            self.create_account(user)

            context = {
                'version': omero_version,
                'build_year': build_year,
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
        adminc = BlitzGateway(
            host=signup_settings.SIGNUP_HOST,
            port=signup_settings.SIGNUP_PORT,
            username=signup_settings.SIGNUP_ADMIN_USERNAME,
            passwd=signup_settings.SIGNUP_ADMIN_PASSWORD,
            secure=True)
        if not adminc.connect():
            raise Exception('Failed to create account '
                            '(unable to obtain admin connection)')
        admin = adminc.getAdminService()
        group = self._get_or_create_group(admin, user)
        uid, login, passwd = self._create_user(admin, user, group)
        self._email_user(adminc.c, user['email'], uid, login, passwd)
        return uid, login, passwd

    def _get_new_login(self, admin, user):
        omename = '%s%s' % (user['firstname'], user['lastname'])
        try:
            admin.lookupExperimenter(omename)
            logger.debug('Username already exists: %s' % omename)
        except omero.ApiUsageException as e:
            if e.message.startswith('No such experimenter'):
                return omename
        n = 0
        while n < 99:
            n += 1
            checkname = '%s%d' % (omename, n)
            try:
                admin.lookupExperimenter(checkname)
                logger.debug('Username already exists: %s' % checkname)
            except omero.ApiUsageException as e:
                if e.message.startswith('No such experimenter'):
                    return checkname

    def _get_or_create_group(self, admin, user):
        groupname = signup_settings.SIGNUP_GROUP_NAME
        try:
            return admin.lookupGroup(groupname)
        except omero.ApiUsageException as e:
            if e.message.startswith('No such group'):
                pass
        g = ExperimenterGroupI()
        g.name = rstring(groupname)
        g.details.permissions = PermissionsI(
            signup_settings.SIGNUP_GROUP_PERMS)
        g.ldap = rbool(False)
        logger.info('Creating new signup group: %s', groupname)
        admin.createGroup(g)
        return admin.lookupGroup(groupname)

    def _create_user(self, admin, user, group):
        login = self._get_new_login(admin, user)
        passwd = ''.join(random.choice(
            string.ascii_letters + string.digits) for n in xrange(12))

        e = ExperimenterI()
        e.firstName = rstring(user['firstname'])
        e.lastName = rstring(user['lastname'])
        e.email = rstring(user['email'])
        e.institution = rstring(user['institution'])
        e.omeName = rstring(login)
        e.ldap = rbool(False)

        usergroup = ExperimenterGroupI(
            admin.getSecurityRoles().userGroupId, False)
        logger.info('Creating new signup user: %s', login)
        uid = admin.createExperimenterWithPassword(
            e, rstring(passwd), group, [usergroup])

        return uid, login, passwd

    def _email_user(self, client, email, uid, login, passwd):
        req = omero.cmd.SendEmailRequest(
            subject=signup_settings.SIGNUP_EMAIL_SUBJECT.format(
                username=login, password=passwd),
            body=signup_settings.SIGNUP_EMAIL_BODY,
            userIds=[uid],
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
