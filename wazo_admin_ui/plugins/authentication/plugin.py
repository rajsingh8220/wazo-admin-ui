# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from wazo_admin_ui.helpers.plugin import create_blueprint

from .view import Login, Logout

login = create_blueprint('login', __name__)
logout = create_blueprint('logout', __name__)


class Plugin(object):

    def load(self, dependencies):
        core = dependencies['flask']

        Login.babel = core.babel_instance
        Login.register(login, route_base='/login', route_prefix='')
        core.register_blueprint(login)

        Logout.register(logout, route_base='/logout', route_prefix='')
        core.register_blueprint(logout)
