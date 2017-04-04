# -*- coding: utf-8 -*-
# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import unittest
from mock import Mock
from marshmallow import fields, pre_dump
from flask_wtf import FlaskForm
from wtforms.fields import TextField, FormField, FieldList

from hamcrest import (assert_that,
                      contains,
                      contains_inanyorder,
                      empty,
                      equal_to,
                      has_entries,
                      has_properties,
                      instance_of,
                      is_not)

from ..mallow import BaseSchema, BaseAggregatorSchema, extract_form_fields


class Resource1Schema(BaseSchema):

    class Meta:
        fields = ('attribute1', 'attribute2')


class Resource2Schema(BaseSchema):

    attribute1 = fields.String(attribute='attribute3')
    attribute4 = fields.String(default='default_value4')


class ResourceFormSchema(BaseSchema):
    _main_resource = 'resource1'

    resource1 = fields.Nested(Resource1Schema)
    resource2 = fields.Nested(Resource2Schema)

    @pre_dump
    def add_envelope(self, data):
        return {'resource1': data,
                'resource2': data}


class TestBaseSchema(unittest.TestCase):

    def setUp(self):
        self.schema = ResourceFormSchema

    def test_get_attribute(self):
        form = Mock(FlaskForm,
                    attribute1=Mock(data='value1', raw_data=['value1']),
                    attribute2=Mock(data='value2', raw_data=['value2']),
                    attribute3=Mock(data='value3', raw_data=['value3']))

        resources = self.schema().dump(form).data

        assert_that(resources, has_entries(resource1=has_entries(attribute1='value1',
                                                                 attribute2='value2'),
                                           resource2=has_entries(attribute1='value3',
                                                                 attribute4='default_value4')))

    def test_get_attribute_with_empty_string(self):
        form = Mock(FlaskForm,
                    attribute1=Mock(data='', raw_data=['']),
                    attribute2=Mock(data='value2', raw_data=['value2']))

        resources = self.schema().dump(form).data

        assert_that(resources, has_entries(resource1=has_entries(attribute1=None)))

    def test_get_attribute_with_no_raw_data(self):
        form = Mock(FlaskForm,
                    attribute1=Mock(data='', raw_data=[]),
                    attribute2=Mock(data='value2', raw_data=['value2']))

        resources = self.schema().dump(form).data

        assert_that(resources, has_entries(resource1=is_not(has_entries(attribute1=None))))

    def test_get_attribute_with_attribute_FormField(self):
        form = Mock(FlaskForm,
                    attribute1=Mock(FormField, data='value1'),
                    attribute2=Mock(data='value2', raw_data=['value2']))

        resources = self.schema().dump(form).data

        assert_that(resources, has_entries(resource1=has_entries(attribute1='value1')))

    def test_get_attribute_with_attribute_FieldList(self):
        form = Mock(FlaskForm,
                    attribute1=Mock(FieldList, data='value1'),
                    attribute2=Mock(data='value2', raw_data=['value2']))

        resources = self.schema().dump(form).data

        assert_that(resources, has_entries(resource1=has_entries(attribute1='value1')))

    def test_populate_form_errors(self):
        form = Mock(FlaskForm,
                    attribute1=Mock(errors=[]),
                    attribute2=Mock(errors=[]),
                    attribute3=Mock(errors=[]),
                    attribute4=Mock(errors=[]))

        resources_errors = {'resource1': {'attribute1': 'error1',
                                          'attribute2': 'error2'},
                            'resource2': {'attribute1': 'error3',
                                          'attribute4': 'error4'}}
        form = self.schema().populate_form_errors(form, resources_errors)

        assert_that(form, has_properties(
            attribute1=has_properties(errors=contains('error1')),
            attribute2=has_properties(errors=contains('error2')),
            attribute3=has_properties(errors=contains('error3')),
            attribute4=has_properties(errors=contains('error4')),
        ))

    def test_populate_form_errors_when_errors_is_initialize_with_tuple(self):
        form = Mock(FlaskForm,
                    attribute1=Mock(errors=tuple()))

        resources_errors = {'resource1': {'attribute1': 'error1'}}
        form = self.schema().populate_form_errors(form, resources_errors)

        assert_that(form, has_properties(
            attribute1=has_properties(errors=instance_of(list))
        ))

    def test_add_main_resource_id(self):
        form = Mock(FlaskForm,
                    attribute1=Mock(data='value1', raw_data=['value1']),
                    attribute2=Mock(data='value2', raw_data=['value2']))

        resources = self.schema(context={'resource_id': 54}).dump(form).data

        assert_that(resources, has_entries(resource1=has_entries(id=54)))

    def test_add_main_resource_id_when_uuid(self):
        form = Mock(FlaskForm,
                    attribute1=Mock(data='value1', raw_data=['value1']),
                    attribute2=Mock(data='value2', raw_data=['value2']))

        resources = self.schema(context={'resource_id': '1234-abcde'}).dump(form).data

        assert_that(resources, has_entries(resource1=has_entries(uuid='1234-abcde')))

    def test_get_main_exten(self):
        extensions = [{'exten': '1234'}, {'exten': '5678'}]

        main_exten = self.schema().get_main_exten(extensions)

        assert_that(main_exten, equal_to('1234'))

    def test_on_bind_field_set_allow_none_true(self):
        resources = {'resource1': {'attribute1': None}}

        _, errors = self.schema().load(resources)

        assert_that(errors, empty())


class AggregatorSchema(BaseAggregatorSchema):

    class Meta:
        fields = ('resource1', 'resource2')


class TestBaseAggregatorSchema(unittest.TestCase):

    def test_add_envelope(self):
        form = 'form'

        result = AggregatorSchema().add_envelope(form)

        assert_that(result, equal_to({'resource1': form,
                                      'resource2': form}))

    def test_add_envelope_with_fields_list(self):
        class AggregatorSchemaList(BaseAggregatorSchema):
            resourcesn = fields.List(fields.String())

        form = Mock(FlaskForm,
                    resourcesn=Mock(FieldList, data=['value1', 'value2']))

        result = AggregatorSchemaList().add_envelope(form)

        assert_that(result, equal_to({'resourcesn': ['value1', 'value2']}))


class TestExtractFormFields(unittest.TestCase):

    def test_extract_form_fields(self):

        class Form(FlaskForm):
            name = TextField('name')
            description = TextField('description')

        result = extract_form_fields(Form)
        assert_that(result, contains_inanyorder('name', 'description'))

    def test_extract_form_fields_with_submit_field(self):

        class Form(FlaskForm):
            name = TextField('name')
            submit = TextField('submit')

        result = extract_form_fields(Form)
        assert_that(result, contains('name'))
