#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 University of Dundee.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

from django import forms


logger = logging.getLogger(__name__)


def _string_not_white_space(value):
    value = value.strip()
    if not value:
        raise forms.ValidationError('Field must not be empty')
    wordchars = [c for c in value if c.isalpha()]
    if not wordchars:
        raise forms.ValidationError(
            'At least one alphabetical character required')
    return value


#################################################################
# Non-model Form

class SignupForm(forms.Form):

    firstname = forms.CharField(
        max_length=50, widget=forms.TextInput(attrs={
            'size': 22, 'autofocus': 'autofocus'}))

    lastname = forms.CharField(
        max_length=50, widget=forms.TextInput(attrs={'size': 22}))

    institution = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={'size': 22}))

    email = forms.EmailField(
        max_length=100, widget=forms.TextInput(attrs={
            'size': 22}))

    def clean_firstname(self):
        return _string_not_white_space(self.cleaned_data['firstname'])

    def clean_lastname(self):
        return _string_not_white_space(self.cleaned_data['lastname'])

    def clean_institution(self):
        return _string_not_white_space(self.cleaned_data['institution'])
