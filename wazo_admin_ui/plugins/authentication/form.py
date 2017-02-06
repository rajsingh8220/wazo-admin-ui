# -*- coding: utf-8 -*-
# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from flask_wtf import FlaskForm
from requests.exceptions import HTTPError
from wtforms.fields import PasswordField, StringField, SubmitField
from wtforms.validators import InputRequired

from wazo_admin_ui.core.auth import AuthClient
from wazo_admin_ui.core.user import UserUI


class LoginForm(FlaskForm):

    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Submit')

    def validate(self):
        super(LoginForm, self).validate()
        try:
            response = AuthClient(username=self.username.data,
                                  password=self.password.data).token.new('xivo_admin', expiration=3600)
        except HTTPError:
            return False

        user_uuid = response.get('xivo_user_uuid')
        token = response.get('token')
        if not token:
            return False

        self.user = UserUI(token, user_uuid)
        return True
