# -*- coding: utf-8 -*-
# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from flask import render_template
from flask import redirect
from flask import url_for
from flask import flash
from flask_classful import FlaskView
from flask_classful import route
from flask_login import login_required

from wazo_admin_ui.core.errors import flash_errors


class LoginRequiredView(FlaskView):
    decorators = [login_required]


class BaseView(LoginRequiredView):
    form = None
    resource = None
    service = None
    templates = {'list': None,
                 'edit': None,
                 'create': None}

    def index(self):
        try:
            result = self.service.list()
        except Exception as e:
            flash('There is a problem to list resources: {}'.format(e), 'error')
            return redirect(url_for('admin.Admin:get'))

        form = self.form()
        return render_template(self.templates['list'], form=form, result=result)

    def post(self):
        form = self.form()

        if form.validate_on_submit():
            objects = self._deserialize_post(form)
            try:
                self.service.create(*objects)
            except Exception as e:
                flash('{} has not been created: {}'.format(self.resource, e), 'error')

            flash('{} has been created'.format(self.resource), 'success')

        else:
            flash_errors(form)

        return self._redirect_for('index')

    def _deserialize_post(form):
        return (form.data,)

    def get(self, id):
        result = self.service.get(id)
        form = self._serialize_get(result)
        return render_template(self.templates['edit'], form=form, result=result)

    def _serialize_get(self, obj):
        return self.form(data=obj)

    @route('/put/<id>', methods=['POST'])
    def put(self, id):
        form = self.form()
        if form.validate_on_submit():
            objects = self._deserialize_put(id, form)
            try:
                self.service.update(*objects)
            except Exception as e:
                flash(u'{} has not been updated: {}'.format(self.resource, e), 'error')

            flash(u'{} has been updated'.format(self.resource), 'success')
            return self._redirect_for('index')

        else:
            flash_errors(form)

        return self.get(id)

    def _deserialize_put(form_id, form):
        result = form.data
        result['id'] = form_id
        return (result,)

    @route('/delete/<id>', methods=['GET'])
    def delete(self, id):
        try:
            self.service.delete(id)
        except Exception as e:
            flash(u'{} {} has not been deleted: {}'.format(self.resource, id, e), 'error')

        flash(u'{} {} has been deleted'.format(self.resource, id), 'success')
        return self._redirect_for('index')

    def _redirect_for(self, method_view):
        return redirect(url_for('{}.{}:{}'.format(self.get_route_base(),
                                                  self.__class__.__name__,
                                                  method_view)))
