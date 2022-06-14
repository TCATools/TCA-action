# -*- encoding: utf-8 -*-
# Copyright (c) 2022 THL A29 Limited
#
# This source code file is made available under MIT License
# See LICENSE for details
# ==============================================================================

""" http request
"""

import sys
import json
import ssl
import logging

from urllib.request import Request, urlopen


logger = logging.getLogger(__name__)


class HttpClient(object):
    @staticmethod
    def request(url, headers, param=None, body=None, method="POST"):
        """

        :param url:
        :param headers:
        :param param:
        :param body:
        :param method:
        :return:
        """
        if param:
            url += "?" + param
        if body:
            body = json.dumps(body)
            if sys.version_info.major == 3:
                body = body.encode("utf-8")
        req = Request(url=url, data=body, headers=headers)
        req.get_method = lambda: method.upper()
        context = ssl._create_unverified_context()
        result = urlopen(req, context=context).read()
        return result
