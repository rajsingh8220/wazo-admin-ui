# -*- coding: utf-8 -*-
# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging
import requests

from flask import url_for, render_template, redirect, session
from flask_babel import Locale, get_locale
from flask_classful import FlaskView
from flask_login import login_user, logout_user, current_user
from wazo_admin_ui.core.auth import AuthClient

from .form import LoginForm

logger = logging.getLogger(__name__)


class Login(FlaskView):

    babel = None

    def get(self):
        return self._login()

    def post(self):
        return self._login()

    def _login(self):
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.Dashboard:get'))

        form = LoginForm()
        form.language.choices = self._build_language_list()
        if form.validate_on_submit():
            session['language'] = form.language.data
            login_user(form.user)
            return redirect(url_for('dashboard.Dashboard:get'))

        return render_template('authentication/login.html', form=form)

    def _build_language_list(self):
        default_locale = Locale.parse(self.babel.app.config['BABEL_DEFAULT_LOCALE'])
        session_locale = get_locale()
        first_choice = (session_locale.language, session_locale.language_name)

        choices = set(((l.language, l.language_name) for l in self.babel.list_translations()))
        choices.add(first_choice)
        choices.add((default_locale.language, default_locale.language_name))
        choices.remove(first_choice)

        return [first_choice] + list(choices)


class Logout(FlaskView):

    def get(self):
        token = current_user.get_id()
        logout_user()
        try:
            AuthClient(host='fsa').token.revoke(token)
        except requests.HTTPError as e:
            logger.warning('Error with Wazo authentication server: %(error)s', error=e.message)
        except requests.ConnectionError:
            logger.warning('Wazo authentication server connection error: Unable to revoke token')
        return redirect(url_for('index.Index:get'))
