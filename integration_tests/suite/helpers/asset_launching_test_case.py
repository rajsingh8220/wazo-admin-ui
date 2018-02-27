# Copyright 2017-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from xivo_test_helpers.asset_launching_test_case import AssetLaunchingTestCase

from .pages.browser import RemoteBrowser
from .pages.page import Page


class AdminUIAssetLaunchingTestCase(AssetLaunchingTestCase):

    service = 'admin-ui'

    @classmethod
    def setUpClass(cls):
        super(AdminUIAssetLaunchingTestCase, cls).setUpClass()
        try:
            cls.browser = cls.setup_browser()
            cls.browser.start()
        except Exception:
            super(AdminUIAssetLaunchingTestCase, cls).tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.stop()
        super(AdminUIAssetLaunchingTestCase, cls).tearDownClass()

    @classmethod
    def setup_browser(cls):
        username = 'xivo-auth-mock-doesnt-care-about-username'
        password = 'xivo-auth-mock-doesnt-care-about-password'
        Page.CONFIG['base_url'] = 'https://admin-ui:9296'

        browser_port = cls.service_port(4444, 'browser')
        remote_url = 'http://localhost:{port}/wd/hub'.format(port=browser_port)
        browser = RemoteBrowser(remote_url, username, password)
        return browser
