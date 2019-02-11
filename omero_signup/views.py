#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf import settings
from django.template import loader as template_loader
from django.utils.http import urlencode

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext as Context
from django.shortcuts import render
from django.views import generic
from django.views.generic import View

from omeroweb.decorators import (
    ConnCleaningHttpResponse,
    login_required,
    parse_url,
)
from django.core.urlresolvers import reverse

from omero_version import build_year
from omero_version import omero_version
from omeroweb.webgateway import views as webgateway_views

from omeroweb.webclient.decorators import login_required, render_response

from .forms import SignupForm

from cStringIO import StringIO

import logging
import omero
from omero.rtypes import rstring
import omero.gateway
import random


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
        logger.error('WebSignupView kwargs: %s', kwargs)
        logger.debug('WebSignupView kwargs: %s', kwargs)
        print('WebSignupView kwargs: %s', kwargs)
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
            firstname = form.cleaned_data['firstname']
            lastname = form.cleaned_data['lastname']
            institution = form.cleaned_data['institution']
            email = form.cleaned_data['email']

            print 'firstname:%s lastname:%s institution:%s email:%s' % (
                firstname, lastname, institution, email)

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
