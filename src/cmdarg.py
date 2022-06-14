# -*- encoding: utf-8 -*-
# Copyright (c) 2022 THL A29 Limited
#
# This source code file is made available under MIT License
# See LICENSE for details
# ==============================================================================

""" 命令行参数解析类
"""

import argparse
import logging

logger = logging.getLogger(__name__)


class CmdArgParser(object):
    """
    命令行参数解析
    """
    @staticmethod
    def parse_args():
        """解析命令行参数

        :return:
        """
        argparser = argparse.ArgumentParser(add_help=True)
        subparsers = argparser.add_subparsers(dest='command', help="Commands")

        # scan命令
        subparsers.add_parser('scan', help="执行分析")

        # init命令
        subparsers.add_parser('init', help="初始化")

        return argparser.parse_args()
