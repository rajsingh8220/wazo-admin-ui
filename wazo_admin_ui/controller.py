# -*- coding: utf-8 -*-
# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging

from wazo_admin_ui.core import plugin_manager
from wazo_admin_ui.core.ui import CoreUI

logger = logging.getLogger(__name__)


class Controller(object):

    def __init__(self, config):
        self.ui_core = CoreUI(config)
        self._load_plugins(config)

    def run(self):
        logger.info('wazo-admin-ui starting...')
        try:
            self.ui_core.run()
        finally:
            logger.info('wazo-admin-ui stopping...')

    def _load_plugins(self, global_config):
        load_args = [{
            'config': global_config,
            'flask': self.ui_core.get_app(),
        }]
        plugin_manager.load_plugins(global_config['enabled_plugins'], load_args)
