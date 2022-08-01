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
from redline import RedLine


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
        self.url_list = {}
        self.fail_msg = []  # 未通过红线指标的提示信息
        self.pass_msg = []  # 已通过红线指标的提示信息

        # 判断是否快速扫描模式
        self.quick_scan = self.get_param("quick_scan")
        if self.quick_scan in ["false", "False"]:
            self.quick_scan = False
        else:
            self.quick_scan = True

        # 快速扫描模式 - 用户输入参数
        self.block = self.get_param("block")
        self.label = self.get_param("label")
        if not self.label:
            self.label = "open_source_check"
        if self.block in ["false", "False"]:
            self.block = False
        else:
            self.block = True
        self.from_file = self.get_param("from_file")
        self.white_paths = self.get_param("white_paths")
        self.ignore_paths = self.get_param("ignore_paths")

        # 完整扫描模式 - 用户输入参数
        self.scheme_id = self.get_param("scheme_id")
        self.languages = self.get_param("language")
        self.total_scan = self.get_param("total_scan")
        self.compare_branch = self.get_param("compare_branch")
        # 超时时间
        self.timeout = self.get_param("timeout")
        # 与服务端通信参数
        self.token = self.get_param("token")
        self.server_ip = self.get_param("server_ip")
        self.org_sid = self.get_param("org_sid")
        self.team_name = self.get_param("team_name")

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

            if self.status_code == 0:  # 正常执行完成，才判断问题量
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
            else:  # 执行异常，如果设置了不block，修改错误码为0，不阻塞流程
                if not self.block:
                    logger.warning(f"param block=false, reset status code({self.status_code}) to 0.")
                    self.status_code = 0

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

    def check_pass(self, scan_result, quality_data):
        """
        scan_result 中的 urls 结构 demo
        "urls": {
            "proj_overview": "",     # 概览页
            "scan_history": "",  # 扫描历史页
            "issues_new": "",  # 本次新增问题
            "issues_fixed": "",  # 本次关闭问题
            "issues_total": "",  # 存量问题
            "cc_worse_files": "",  # 圈复杂度恶化文件数
            "cc_result": "",  # 圈复杂度结果页
            "duplicate_result": "",  # 重复代码结果页
            "cloc_result": ""  # 代码统计结果页
        }
        """
        urls = scan_result.get("urls", {})
        issues_new = urls.get("issues_new", "None")
        issues_total = urls.get("issues_total", "None")
        cc_worse_files = urls.get("cc_worse_files", "None")
        cc_result = urls.get("cc_result", "None")
        duplicate_result = urls.get("duplicate_result", "None")

        metric_keys = {
            "incr_fatal": {"name": "新增问题量(级别:致命)", "url": issues_new},
            "incr_error": {"name": "新增问题量(级别:致命+错误)", "url": issues_new},
            "incr_warning": {"name": "新增问题量(级别:致命+错误+警告)", "url": issues_new},
            "incr_info": {"name": "新增问题量(级别:致命+错误+警告+提示)", "url": issues_new},
            "total_fatal": {"name": "存量问题量(级别:致命)", "url": issues_total},
            "total_error": {"name": "存量问题量(级别:致命+错误)", "url": issues_total},
            "total_warning": {"name": "存量问题量(级别:致命+错误+警告)", "url": issues_total},
            "total_info": {"name": "存量问题量(级别:致命+错误+警告+提示)", "url": issues_total},
            "worse_cc_file_num": {"name": "圈复杂度恶化文件数", "url": cc_worse_files},
            "over_cc_sum": {"name": "超标圈复杂度总数", "url": cc_result},
            "cc_func_average": {"name": "代码平均圈复杂度", "url": cc_result},
            "over_cc_func_count": {"name": "圈复杂度超标方法数", "url": cc_result},
            "diff_over_cc_func_count": {"name": "变更圈复杂度超标方法数", "url": cc_result},
            "over_cc_func_average": {"name": "超标方法平均圈复杂度", "url": cc_result},
            "duplicate_rate": {"name": "代码重复率", "url": duplicate_result}
        }
        for key_id, info in metric_keys.items():
            expected_value = self.get_param(key_id)
            if expected_value is None:
                continue
            if key_id in ["cc_func_average", "over_cc_func_average"]:
                expected_value = float(expected_value)
            else:
                expected_value = int(expected_value)
            is_pass, actual_value = RedLine().check(key_id, expected_value, quality_data)
            if is_pass is not None:
                display_name = metric_keys[key_id]['name']
                url = metric_keys[key_id]['url']
                if is_pass:
                    self.pass_msg.append(f"[pass] {display_name} {key_id} = {actual_value}, 符合: <= {expected_value}")
                else:
                    fail_msg = f"[fail] {display_name} {key_id} = {actual_value}, 不符合: <= {expected_value}"
                    if actual_value is None:
                        fail_msg += ", 数据为空,请检查对应的检查项是否未开启"
                    else:
                        fail_msg += f", 查看详情: {url}"
                    self.fail_msg.append(fail_msg)

    def gen_status_file(self, status, text, url, desc, scan_result=None):
        """
        生成结果文件
        :param status:
        :param text:
        :param url:
        :param desc:
        :param scan_result:
        :return:
        """
        if status == "cancel":
            status = "success"
            text = "跳过本次扫描"

        scan_report = {}
        quality_data = None
        # 先对scan_result判空,否则会异常: TypeError: argument of type 'NoneType' is not iterable
        if scan_result:
            scan_report = scan_result.get("scan_report")
            # 获取质量红线数据
            quality_data = RedLine().get_readline_data(scan_result)
            # 判断红线指标
            if quality_data:
                self.check_pass(scan_result, quality_data)

        redline_msg = ""
        if self.pass_msg:
            pass_msg = "\n" + "\n".join(self.pass_msg)
            redline_msg += pass_msg

        if self.fail_msg:
            status = "failure"
            fail_msg = "\n" + "\n".join(self.fail_msg)
            redline_msg += fail_msg

        status_map = {"success": "通过", "failure": "不通过", "error": "执行异常"}
        code_map = {"success": 0, "failure": 1, "error": 2}
        self.status_code = code_map[status]

        result = {
            "status": status,
            "status_code": self.status_code,
            "text": text,
            "url": url,
            "description": desc,
            "redline_msg": redline_msg,
            "scan_report": scan_report,
            "metrics": quality_data,
        }

        result_msg = "\n"
        result_msg += "*" * 100
        result_msg += "\n检查结果: %s。" % status_map[status]
        if redline_msg:
            result_msg += "\n质量红线:%s" % redline_msg
        result_msg += "\n%s" % ("*" * 100)
        logger.info(result_msg)

        # 将结果输出到工作空间下的json文件,供后续步骤使用
        workspace = os.getcwd()
        codedog_report_file = os.path.join(workspace, "codedog_report.json")
        if os.path.exists(codedog_report_file):
            os.remove(codedog_report_file)
        with open(codedog_report_file, "wb") as fp:
            fp.write(str.encode(json.dumps(result, indent=2, ensure_ascii=False)))

        if self.status_code != 0 and not self.block:  # 如果参数设置为不阻塞，返回码重置为0
            logger.warning(f"param block=false, reset status code({self.status_code}) to 0.")
            self.status_code = 0

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

    def run_localscan(self, codedog_exe, codedog_work_dir):
        # 扫描参数
        scan_args = [
            codedog_exe, "localscan",
            "-s", self.source_dir
        ]
        if self.token:
            scan_args.extend(["-t", self.token])
            # 通过环境变量设置文件服务器token
            os.environ["FILE_SERVER_TOKEN"] = self.token
        if self.server_ip:
            server_url = f"http://{self.server_ip}/server/main/"
            file_server_url = f"http://{self.server_ip}/server/files/"
            # 通过环境变量设置文件服务器url
            os.environ["FILE_SERVER_URL"] = file_server_url
            scan_args.extend(["--server", server_url])
        if self.org_sid:
            scan_args.extend(["--org-sid", self.org_sid])
        if self.team_name:
            scan_args.extend(["--team-name", self.team_name])
        if self.languages:
            scan_args.extend(["--language", self.languages])
        if self.total_scan and self.total_scan in ["True", "true"]:
            scan_args.extend(["--total"])
        if self.scheme_id:
            scan_args.extend(['--ref-scheme-id', self.scheme_id])
        if self.compare_branch:
            scan_args.extend(["--compare-branch", self.compare_branch])

        # 启动扫描进程
        try:
            # fix bug - 参数需要为str类型的list,不能包含int
            scan_args = [str(item) for item in scan_args]

            print_cmd_args = []
            for item in scan_args:
                if self.token == item:
                    print_cmd_args.append("****")
                else:
                    print_cmd_args.append(item)
            logger.info("run cmd: %s", " ".join(print_cmd_args))

            sp = subprocess.Popen(args=scan_args, cwd=codedog_work_dir)
            if self.timeout:
                scan_time_out = self.timeout * 3600
            else:
                scan_time_out = setting.SCAN_TIMEOUT
            logger.info("超时时间设置为: %s 小时" % (scan_time_out / 3600))
            sp.wait(timeout=scan_time_out)
        except Exception as err:
            self.gen_status_file(status="error", text="扫描异常", url=None, desc=str(err))
            raise err

        result_file = os.path.join(codedog_work_dir, "scan_status.json")
        if os.path.exists(result_file):
            with open(result_file, "r", encoding="utf-8") as rf:
                result_json = json.load(rf)
            self.gen_status_file(
                status=result_json["status"],
                text=result_json["text"],
                url=result_json["url"],
                desc=result_json["description"],
                scan_result=result_json,
            )
        else:
            logger.warning("启动失败,未生成结果文件: %s" % result_file)
            self.gen_status_file(
                status="error",
                text="启动失败",
                url=None,
                desc="启动失败,未生成结果文件: %s" % result_file,
            )

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
        if self.quick_scan:
            self.run_quickscan(cur_workspace, codedog_exe, codedog_work_dir)
        else:
            self.run_localscan(codedog_exe, codedog_work_dir)

    def run(self):
        args = CmdArgParser.parse_args()
        cur_workspace = os.getcwd()

        # 插件存放目录
        plugin_dir = "/tca_action/"
        if not os.path.exists(plugin_dir):
            plugin_dir = os.path.dirname(cur_workspace)

        # 客户端安装目录
        tca_install_dir = os.path.join(plugin_dir, "lib")
        if not os.path.exists(tca_install_dir):
            os.makedirs(tca_install_dir)
        logger.info(f"tca_install_dir: {tca_install_dir}")

        # 默认客户端工作目录，如果存在，直接复用；否则重新下载
        tca_work_dir = os.path.join(tca_install_dir, "tca-client")

        if os.path.exists(tca_work_dir):  # 使用默认的tca-client目录(把客户端提前打包内置在docker中)
            logger.info("tca_work_dir: %s" % tca_work_dir)
            logger.info(f"{tca_work_dir} existis, reuse it.")
        else:  # 使用从下载url提取的目录，比如：tca-client-v20220629.1-x86_64-linux
            zip_file_name = PUPPY_DOWNLOAD_URL.split('/')[-1]
            tca_work_dirname = os.path.splitext(zip_file_name)[0]
            tca_work_dir = os.path.join(tca_install_dir, tca_work_dirname)
            logger.info("tca_work_dir: %s" % tca_work_dir)
            if os.path.exists(tca_work_dir):
                logger.info(f"{tca_work_dir} exists, reuse it.")
            else:  # 重新下载
                tca_work_dir = PuppyDownloader().download_linux_client(tca_install_dir)
                self.__chmod_exe(tca_work_dir)

        codedog_exe = os.path.join(tca_work_dir, self.codepuppy_name)
        if args.command == "scan":
            if self.quick_scan:
                self.__init_tools(tca_work_dir, codedog_exe)
            else:
                logger.info(f"It is not quick scan, skip initing tools.")

            logger.info("开始扫描代码 ...")
            self.scan_source_dir(cur_workspace, codedog_exe, tca_work_dir)

            logger.info("结束.")
            if self.status_code != 0:
                logger.warning(f"status code: {self.status_code}")
                sys.exit(self.status_code)
        else:
            logger.warning(f"args need: scan.")


if __name__ == "__main__":
    TCAPlugin().run()
