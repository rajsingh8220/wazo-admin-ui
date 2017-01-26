# -*- coding: utf-8 -*-
# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging

from flask import redirect
from flask import url_for
from flask.helpers import flash

from requests.exceptions import ConnectionError


logger = logging.getLogger(__name__)


def configure_error_handlers(app):

    @app.errorhandler(401)
    def page_unauthorized(error):
        return _flash_and_redirect(error)

    @app.errorhandler(403)
    def page_forbidden(error):
        return _flash_and_redirect(error)

    @app.errorhandler(404)
    def page_not_found(error):
        return _flash_and_redirect(error)

    @app.errorhandler(ConnectionError)
    def connection_error(error):
        logger.exception(ConnectionError)
        return _flash_and_redirect(error)

    @app.errorhandler(Exception)
    def exception_handler(error):
        logger.exception(Exception)
        return _flash_and_redirect(error)

    def _flash_and_redirect(error):
        flash(str(error), 'error')
        return redirect(url_for('index.Index:get'))


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'error')
