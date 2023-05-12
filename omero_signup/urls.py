#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.urls import re_path
from . import views


urlpatterns = [

    # index 'home page' of the websignup app
    re_path(r'^$', views.WebSignupView.as_view(), name="signup_index"),
]
