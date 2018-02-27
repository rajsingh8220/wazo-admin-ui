# Copyright 2017-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging
import os

from datetime import timedelta

import requests
from requests.exceptions import HTTPError

from cheroot import wsgi
from flask import Flask
from flask import request, session, url_for
from flask_babel import Babel
from flask_menu import Menu
from flask_session import Session
from flask_login import LoginManager
from pkg_resources import iter_entry_points, resource_filename, resource_isdir
from werkzeug.contrib.fixers import ProxyFix

from xivo import http_helpers
from xivo.http_helpers import ReverseProxied

from .auth import AuthClient
from .errors import configure_error_handlers
from .user import UserUI

TRANSLATION_DIRECTORY = 'translations'
BABEL_DEFAULT_LOCALE = 'en'

logger = logging.getLogger(__name__)
app = Flask('wazo_admin_ui')


class Server():

    def __init__(self, global_config):
        self.config = global_config['https']
        http_helpers.add_logger(app, logger)

        app.after_request(http_helpers.log_request_hide_token)

        app.secret_key = os.urandom(24)
        app.permanent_session_lifetime = timedelta(seconds=global_config['session_lifetime'])
        AuthClient.set_config(global_config['auth'])
        app.config['confd'] = global_config.get('confd', {})
        app.config['call_logd'] = global_config.get('call_logd', {})
        app.config['plugind'] = global_config.get('plugind', {})
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 megabytes

        if global_config['debug']:
            app.jinja_env.auto_reload = True
            app.config['TEMPLATES_AUTO_RELOAD'] = True

        configure_error_handlers(app)
        self._override_url_for()
        self._configure_jinja()
        self._configure_login()
        self._configure_menu()
        self._configure_session(global_config['session_file_dir'])
        self._configure_babel(global_config['enabled_plugins'])

    def get_app(self):
        return app

    def run(self):
        bind_addr = (self.config['listen'], self.config['port'])

        wsgi_app = ReverseProxied(ProxyFix(wsgi.WSGIPathInfoDispatcher({'/': app})))
        self.server = wsgi.WSGIServer(bind_addr=bind_addr,
                                      wsgi_app=wsgi_app)
        self.server.ssl_adapter = http_helpers.ssl_adapter(self.config['certificate'],
                                                           self.config['private_key'])
        logger.debug('WSGIServer starting... uid: %s, listen: %s:%s', os.getuid(), bind_addr[0], bind_addr[1])
        for route in http_helpers.list_routes(app):
            logger.debug(route)

        try:
            self.server.start()
        except KeyboardInterrupt:
            self.server.stop()

    def stop(self):
        if self.server:
            self.server.stop()

    def _override_url_for(self):
        def url_for_allow_empty_endpoint(endpoint, **values):
            if not endpoint:
                return ''
            return url_for(endpoint, **values)

        @app.context_processor
        def override_url_for():
            return dict(url_for=url_for_allow_empty_endpoint)

    def _configure_jinja(self):
        app.jinja_env.trim_blocks = True
        app.jinja_env.add_extension('jinja2.ext.do')

    def _configure_login(self):
        login_manager = LoginManager()
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_token(token):
            try:
                response = AuthClient().token.get(token)
            except HTTPError:
                return None
            except requests.ConnectionError:
                logger.warning('Wazo authentication server connection error')
                return None
            token = response.get('token')
            if not token:
                return None
            return UserUI(token, response.get('auth_id'))

    def _configure_menu(self):
        menu = Menu()
        menu.init_app(app)

    def _configure_babel(self, enabled_plugins):
        babel = Babel()
        babel.init_app(app)
        app.config['BABEL_DEFAULT_LOCALE'] = BABEL_DEFAULT_LOCALE
        app.config['BABEL_TRANSLATION_DIRECTORIES'] = ';'.join(self._get_translation_directories(enabled_plugins))

        @babel.localeselector
        def get_locale():
            if not session.get('language'):
                translations = set([locale.language for locale in babel.list_translations()])
                translations.add(BABEL_DEFAULT_LOCALE)

                session['language'] = request.accept_languages.best_match(translations)

            return session['language']

    def _get_translation_directories(self, enabled_plugins):
        main_translation_directory = 'translations'
        result = [main_translation_directory]
        entry_points = (e for e in iter_entry_points(group='wazo_admin_ui.plugins')
                        if e.name in enabled_plugins)
        for ep in entry_points:
            if resource_isdir(ep.module_name, TRANSLATION_DIRECTORY):
                result.append(resource_filename(ep.module_name, TRANSLATION_DIRECTORY))
        return result

    def _configure_session(self, session_file_dir):
        app.config['SESSION_FILE_DIR'] = session_file_dir
        app.config['SESSION_TYPE'] = 'filesystem'
        flask_session = Session()
        flask_session.init_app(app)
