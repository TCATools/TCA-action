# -*- encoding: utf-8 -*-
# Copyright (c) 2022 THL A29 Limited
#
# This source code file is made available under MIT License
# See LICENSE for details
# ==============================================================================
""" 文件服务器接口
"""

import logging
from httpclient import HttpClient


logger = logging.getLogger(__name__)


class FileServer(object):
    def __init__(self):
        self._headers = {
            "Content-type": "application/json"
        }

    def download_file(self, file_url, filepath):
        """
        从文件服务器下载文件到指定地址
        :param file_url: 需要下载的文件的url
        :param filepath: 下载后的文件路径
        :return: 下载成功,返回filepath;否则返回None
        """
        # logger.info(f"file_url: {file_url}")
        data = HttpClient.request(file_url, headers=self._headers, method="GET")
        with open(filepath, "wb") as wf:
            wf.write(data)
        return filepath
