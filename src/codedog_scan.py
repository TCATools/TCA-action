# -*- encoding: utf-8 -*-
# Copyright (c) 2022 THL A29 Limited
#
# This source code file is made available under MIT License
# See LICENSE for details
# ==============================================================================

"""
TCA Action
"""

import json
import logging
import os
import stat
import sys
import subprocess
import setting

from downloadpuppy import PuppyDownloader
from pathfilter import StringMgr, PathUtil, FilterPathUtil
from cmdarg import CmdArgParser
from setting import PUPPY_DOWNLOAD_URL


logger = logging.getLogger("TCA-action")


class LoggerMgr(object):
    @staticmethod
    def setup_logger():
        """日志打印配置

        :param args:命令行参数
        :return:
        """
        # 设置日志级别和格式
        level = logging.INFO

        format_pattern = "-%(asctime)s-%(levelname)s: %(message)s"
        logging.basicConfig(level=level, format=format_pattern)


class TCAPlugin(object):
    def __init__(self):
        # 初始化日志打印
        LoggerMgr.setup_logger()
        self.status_code = 0

        # 快速扫描模式 - 用户输入参数
        self.block = self.get_param("block")
        self.label = self.get_param("label")
        if not self.label:
            self.label = "open-standard"
        if self.block in ["false", "False"]:
            self.block = False
        else:
            self.block = True
        self.from_file = self.get_param("from_file")
        self.white_paths = self.get_param("white_paths")
        self.ignore_paths = self.get_param("ignore_paths")

        # 可执行程序名称
        self.codepuppy_name = setting.PUPPY_EXE_NAME
        self.task_name = setting.PUPPY_TASK_EXE_NAME

        self.source_dir = self.get_param("source_dir")

    def get_param(self, key):
        """从环境变量获取用户配置参数"""
        env = os.getenv(f"INPUT_{key.upper()}")
        logger.info(f"get param: {key}={env}")
        return env

    def __chmod_exe(self, dir_path):
        """
        给可执行程序赋予执行权限
        :param dir_path: 可执行程序目录
        :return:
        """
        exe_paths = [
            os.path.join(dir_path, self.codepuppy_name),
            os.path.join(dir_path, self.task_name),
        ]
        for exe_path in exe_paths:
            if os.path.exists(exe_path):
                os.chmod(exe_path, stat.S_IRWXU)

    def run_quickscan(self, cur_workspace, codedog_exe, codedog_work_dir):
        input_file = self.get_quick_scan_input_file(cur_workspace, codedog_work_dir)
        if input_file:
            os.environ["TCA_QUICK_SCAN_INPUT"] = input_file

        # 扫描参数
        scan_args = [
            codedog_exe, "quickscan",
            "-s", self.source_dir,
            "-l", self.label
        ]
        logger.info("run cmd: %s", " ".join(scan_args))

        sp = subprocess.Popen(args=scan_args, cwd=codedog_work_dir)
        scan_time_out = setting.SCAN_TIMEOUT
        sp.wait(timeout=scan_time_out)

        report_path = os.getenv("TCA_QUICK_SCAN_OUTPUT")
        if report_path:
            report_path = os.path.abspath(report_path)
        else:
            report_path = os.path.join(codedog_work_dir, "tca_quick_scan_report.json")
        with open(report_path, "r") as rf:
            data = json.load(rf)
            self.status_code = data.get("error_code")

            issue_count = data.get("issue_count")
            if issue_count is not None:
                if issue_count == 0:
                    data["status"] = "pass"
                    data["text"] = "通过"
                    data["description"] = "通过"
                else:
                    data["status"] = "failed"
                    data["text"] = "不通过"
                    data["description"] = f"不通过, 待处理问题量: {issue_count}"
                    if self.block:
                        self.status_code = 1

        data_str = json.dumps(data, indent=2, ensure_ascii=False)
        logger.info(f"扫描结果:\n{data_str}")

    def get_quick_scan_input_file(self, cur_workspace, codedog_work_dir):
        """
        从from_file指定的文件中获取需要扫描的文件路径,生成quickscan的input file
        """
        scan_paths = []
        if self.from_file:
            file_path = os.path.join(cur_workspace, self.from_file)
            if not os.path.exists(file_path):
                raise Exception(f"from_file参数指定的文件不存在: {file_path}")
            with open(file_path, "r") as rf:
                file_list = rf.readlines()
            for rel_path in file_list:
                rel_path = rel_path.strip()
                if rel_path:
                    full_path = os.path.join(self.source_dir, rel_path)
                    if os.path.exists(full_path):
                        scan_paths.append(rel_path)
                    else:
                        logger.warning(f"file({rel_path}) not found: {full_path}")
            if not scan_paths:
                logger.warning("from_file文件中无待扫描文件,请检查。")
                sys.exit(-1)
        else:
            if not self.white_paths and not self.ignore_paths:  # 未指定扫描文件列表，也未设置过滤路径, 返回空（此时不生成input_file,会扫描整个代码目录）
                return None

        if self.white_paths or self.ignore_paths:  # 根据过滤路径进行过滤
            scan_paths = self.filter_paths(scan_paths)
            if not scan_paths:
                logger.info("过滤后无待扫描文件,跳过扫描。")
                sys.exit(0)

        # 将待扫描文件添加到input file中
        format_scan_paths = []
        for rel_path in scan_paths:
            format_scan_paths.append({
                "path": rel_path,
                "type": "file"
            })
        data = {
            "labels": StringMgr.str_to_list(self.label),
            "scan_path": format_scan_paths
        }
        input_file = os.path.join(codedog_work_dir, "quickscan_input_file.json")
        if os.path.exists(input_file):
            os.remove(input_file)
        with open(input_file, "w") as wf:
            json.dump(data, wf, indent=2)
        return input_file

    def filter_paths(self, scan_paths):
        """
        根据过滤路径，过滤文件列表，返回需要扫描的文件相对路径列表
        """
        if self.white_paths:
            path_include = StringMgr.str_to_list(self.white_paths)
        else:
            path_include = []
        if self.ignore_paths:
            path_exclude = StringMgr.str_to_list(self.ignore_paths)
        else:
            path_exclude = []

        if not scan_paths:  # 未指定扫描文件列表，获取目录下所有文件，再过滤
            scan_paths = PathUtil.get_dir_files(self.source_dir)

        scan_paths = FilterPathUtil(path_include, path_exclude).get_include_files(scan_paths, self.source_dir)
        return scan_paths

    def scan_source_dir(self, cur_workspace, codedog_exe, codedog_work_dir):
        """
        扫描代码
        :return:
        """
        if self.source_dir:  # 指定了代码相对路径,拼接成绝对路径
            self.source_dir = os.path.abspath(self.source_dir)
        else:  # 没有指定,默认使用当前工作空间目录
            self.source_dir = os.path.abspath(cur_workspace)

        logger.info(f"scan source_dir: {self.source_dir}")
        self.run_quickscan(cur_workspace, codedog_exe, codedog_work_dir)

    def __init_tools(self, tca_work_dir, codedog_exe):
        # 扫描参数
        scan_args = [
            codedog_exe, "quickinit",
            "-l", self.label
        ]
        logger.info("run cmd: %s", " ".join(scan_args))

        sp = subprocess.Popen(args=scan_args, cwd=tca_work_dir)
        scan_time_out = setting.SCAN_TIMEOUT
        sp.wait(timeout=scan_time_out)

    def run(self):
        args = CmdArgParser.parse_args()
        cur_workspace = os.getcwd()

        # CodeDog客户端存放目录
        plugin_dir = "/tca_action/"
        if not os.path.exists(plugin_dir):
            plugin_dir = os.path.dirname(cur_workspace)
        # 客户端安装目录
        tca_install_dir = os.path.join(plugin_dir, "lib")
        if not os.path.exists(tca_install_dir):
            os.makedirs(tca_install_dir)
        logger.info(f"tca_install_dir: {tca_install_dir}")

        zip_file_name = PUPPY_DOWNLOAD_URL.split('/')[-1]
        tca_work_dirname = os.path.splitext(zip_file_name)[0]

        tca_work_dir = os.path.join(tca_install_dir, tca_work_dirname)
        logger.info("tca_work_dir: %s" % tca_work_dir)
        codedog_exe = os.path.join(tca_work_dir, self.codepuppy_name)

        if args.command == "init":
            if os.path.exists(codedog_exe):
                logger.info(f"{codedog_exe} existis, reuse it.")
            else:
                tca_work_dir = PuppyDownloader().download_linux_client(tca_install_dir)
                self.__chmod_exe(tca_work_dir)
            self.__init_tools(tca_work_dir, codedog_exe)
        elif args.command == "scan":
            logger.info("开始扫描代码 ...")
            self.scan_source_dir(cur_workspace, codedog_exe, tca_work_dir)

            logger.info("结束.")
            if self.status_code != 0:
                logger.warning(f"status code: {self.status_code}")
                sys.exit(self.status_code)
        else:
            logger.warning(f"args need: init, scan.")


if __name__ == "__main__":
    TCAPlugin().run()
