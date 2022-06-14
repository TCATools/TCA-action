# -*- encoding: utf-8 -*-
# Copyright (c) 2022 THL A29 Limited
#
# This source code file is made available under MIT License
# See LICENSE for details
# ==============================================================================
"""
puppy下载类
"""

import os
import logging


from fileserver import FileServer
from ziplib import ZipMgr
from setting import PUPPY_DOWNLOAD_URL

logger = logging.getLogger(__name__)


class PuppyDownloader(object):
    def __init__(self):
        self._file_server = FileServer()

    def common_download(self, url, dest_dir, zip_file_name):
        dest_file_path = os.path.join(dest_dir, zip_file_name)
        download_path = self._file_server.download_file(url, dest_file_path)
        if download_path:
            logger.info("下载成功: %s" % download_path)
            unzip_dir = ZipMgr().unzip_file(download_path, dest_dir)
            logger.info(f"unzip to dir: {unzip_dir}")
            # 删除压缩包
            logger.info("解压后删除压缩包: %s" % download_path)
            os.remove(download_path)
            return unzip_dir
        else:
            logger.error("%s 下载失败!" % url)
            return None

    def download_linux_client(self, dest_dir):
        zip_file_name = PUPPY_DOWNLOAD_URL.split('/')[-1]
        return self.common_download(PUPPY_DOWNLOAD_URL, dest_dir, zip_file_name)
