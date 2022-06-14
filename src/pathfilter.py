# -*- encoding: utf-8 -*-
# Copyright (c) 2022 THL A29 Limited
#
# This source code file is made available under MIT License
# See LICENSE for details
# ==============================================================================

"""
根据增量条件和过滤路径过滤,获取实际需要分析的文件路径列表
"""

import os
import re
import logging

logger = logging.getLogger(__name__)


class StringMgr(object):
    @staticmethod
    def str_to_list(str_data, sep_list=(',', ';')):
        reg_pattern = "[%s]" % ''.join(sep_list)
        return list(set([item.strip() for item in re.split(reg_pattern, str_data) if item.strip()]))


class PathUtil(object):
    @staticmethod
    def get_dir_files(root_dir, want_suffix=""):
        files = set()
        for dirpath, dirs, filenames in os.walk(root_dir):
            for f in filenames:
                if f.lower().endswith(want_suffix):
                    fullpath = os.path.join(dirpath, f)
                    files.add(fullpath)
        full_paths = list(files)
        rel_paths = [os.path.relpath(path, root_dir) for path in full_paths]
        return rel_paths


class RegexCompiler(object):
    @staticmethod
    def compile_regex(regex_exp_list):
        regex_exp = "|".join(regex_exp_list)
        try:
            return re.compile(regex_exp)
        except Exception as err:
            err_msg = "过滤路径(%s)格式有误,将导致过滤不生效: %s" % (regex_exp_list, str(err))
            logger.error(err_msg)
            return None


class FilterPathUtil(object):
    def __init__(self, path_include, path_exclude):
        self.__include_regex = None
        self.__exclude_regex = None

        if path_include:
            self.__include_regex = RegexCompiler.compile_regex(path_include)

        if path_exclude:
            self.__exclude_regex = RegexCompiler.compile_regex(path_exclude)

    def should_filter_path(self, rel_path):
        rel_path = rel_path.replace(os.sep, '/')
        if self.__exclude_regex:
            if self.__exclude_regex.fullmatch(rel_path):
                return True
        if self.__include_regex:
            if not self.__include_regex.fullmatch(rel_path):
                return True
        return False

    def get_include_files(self, rel_paths, root_dir):
        wanted_rel_paths = []
        for rel_path in rel_paths:
            full_path = os.path.join(root_dir, rel_path)
            if os.path.exists(full_path):  # 判断文件是否存在,过滤掉软链接
                if not self.should_filter_path(rel_path):
                    rel_path = rel_path.replace('\\', '/')
                    wanted_rel_paths.append(rel_path)

        # use_time = time.time() - total_start_time
        logger.info(f"[文件数]过滤前：{len(rel_paths)}，过滤后：{len(wanted_rel_paths)}")

        return wanted_rel_paths
