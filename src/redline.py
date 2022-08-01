# -*- encoding: utf-8 -*-
# Copyright (c) 2022 THL A29 Limited
#
# This source code file is made available under MIT License
# See LICENSE for details
# ==============================================================================

"""
质量红线类,输出各项指标数据,供质量红线判断
"""

import logging

logger = logging.getLogger(__name__)


class RedLine(object):
    """
    检查结果是否通过
    """

    def get_readline_data(self, result_json):
        """
        获取红线数据
        """
        if not result_json:
            return None

        lintscan_data = self.get_lintscan_data(result_json)

        # 获取质量红线数据,如果执行失败,无法判断红线,红线数据置空
        if result_json["status"] == "error":
            return None
        else:
            return self.get_pass_data(result_json, lintscan_data)

    def get_lintscan_data(self, result_json):
        """
        统计代码检查扫描结果,按照问题级别统计
        :param scan_report:
        :return: lintscan_severity_data 各个级别的问题量
        """
        # 严重级别
        severity_levels = ["fatal", "error", "warning", "info"]

        # 初始化各个严重级别的结果统计
        lintscan_severity_data = {
            "incr": {"fatal": None, "error": None, "warning": None, "info": None},
            "total": {"fatal": None, "error": None, "warning": None, "info": None},
        }

        if "scan_report" in result_json:
            scan_report = result_json["scan_report"]
            if scan_report:
                lintscan_report = scan_report["lintscan"]
                if lintscan_report:
                    # 统计增量问题量
                    if "active_severity_detail" in lintscan_report["current_scan"]:
                        active_severity_detail = lintscan_report["current_scan"]["active_severity_detail"]
                        for sev_name in severity_levels:
                            if sev_name in active_severity_detail:
                                lintscan_severity_data["incr"][sev_name] = active_severity_detail[sev_name]

                    # 统计存量问题量
                    if "severity_detail" in lintscan_report["total"]:
                        severity_detail = lintscan_report["total"]["severity_detail"]
                        for sev_name in severity_levels:
                            if sev_name in severity_detail:
                                if "active" in severity_detail[sev_name]:
                                    lintscan_severity_data["total"][sev_name] = severity_detail[sev_name]["active"]
        return lintscan_severity_data

    def get_pass_data(self, result_json, lintscan_severity_data):
        """
        获取各个级别及以上的问题数据,作为质量红线的判断依据
        :param scan_report: dict, 扫描结果
        :param lintscan_severity_data: dict, 代码检查各严重级别统计结果
        :return: quality_data (质量红线判断依据)
        """
        # 代码检查判断数据
        lint_scan_pass_data = {  # 代码检查红线数据
            "incr": {
                "fatal": lintscan_severity_data["incr"]["fatal"],
                "error": lintscan_severity_data["incr"]["fatal"] +
                         lintscan_severity_data["incr"]["error"],
                "warning": lintscan_severity_data["incr"]["fatal"] +
                           lintscan_severity_data["incr"]["error"] +
                           lintscan_severity_data["incr"]["warning"],
                "info": lintscan_severity_data["incr"]["fatal"] +
                        lintscan_severity_data["incr"]["error"] +
                        lintscan_severity_data["incr"]["warning"] +
                        lintscan_severity_data["incr"]["info"],
            },
            "total": {
                "fatal": lintscan_severity_data["total"]["fatal"],
                "error": lintscan_severity_data["total"]["fatal"] +
                         lintscan_severity_data["total"]["error"],
                "warning": lintscan_severity_data["total"]["fatal"] +
                           lintscan_severity_data["total"]["error"] +
                           lintscan_severity_data["total"]["warning"],
                "info": lintscan_severity_data["total"]["fatal"] +
                        lintscan_severity_data["total"]["error"] +
                        lintscan_severity_data["total"]["warning"] +
                        lintscan_severity_data["total"]["info"],
            },
        }
        # 超标圈复杂度总数
        over_cc_sum = None
        # 代码平均圈复杂度
        cc_func_average = None
        # 圈复杂度超标方法数
        over_cc_func_count = None
        # 变更圈复杂度超标方法数
        diff_over_cc_func_count = None
        # 超标方法平均圈复杂度
        over_cc_func_average = None
        # 圈复杂度恶化文件数
        worse_cc_file_num = None
        # 代码重复率
        duplicate_rate = None
        if "scan_report" in result_json:
            scan_report = result_json["scan_report"]
            if scan_report:
                cc_scan_report = scan_report["cyclomaticcomplexityscan"]
                duplicate_scan_report = scan_report["duplicatescan"]
                if cc_scan_report:
                    if cc_scan_report["custom_summary"]:
                        over_cc_sum = cc_scan_report["custom_summary"]["over_cc_sum"]
                        cc_func_average = cc_scan_report["custom_summary"]["cc_func_average"]
                        over_cc_func_count = cc_scan_report["custom_summary"]["over_cc_func_count"]
                        diff_over_cc_func_count = cc_scan_report["custom_summary"]["diff_over_cc_func_count"]
                        over_cc_func_average = cc_scan_report["custom_summary"]["over_cc_func_average"]
                    else:
                        over_cc_sum = cc_scan_report["default_summary"]["over_cc_sum"]
                        cc_func_average = cc_scan_report["default_summary"]["cc_func_average"]
                        over_cc_func_count = cc_scan_report["default_summary"]["over_cc_func_count"]
                        diff_over_cc_func_count = cc_scan_report["default_summary"]["diff_over_cc_func_count"]
                        over_cc_func_average = cc_scan_report["default_summary"]["over_cc_func_average"]
                    worse_cc_file_num = cc_scan_report.get("worse_cc_file_num", 0)
                    # 原始数据小数部分比较长,取小数点后3位
                    cc_func_average = round(cc_func_average, 3)
                    over_cc_func_average = round(over_cc_func_average, 3)
                if duplicate_scan_report:
                    duplicate_rate = duplicate_scan_report["duplicate_rate"]

        # 质量红线判断数据
        quality_data = {
            "incr_fatal": {"value": lint_scan_pass_data["incr"]["fatal"]},
            "incr_error": {"value": lint_scan_pass_data["incr"]["error"]},
            "incr_warning": {"value": lint_scan_pass_data["incr"]["warning"]},
            "incr_info": {"value": lint_scan_pass_data["incr"]["info"]},
            "total_fatal": {"value": lint_scan_pass_data["total"]["fatal"]},
            "total_error": {"value": lint_scan_pass_data["total"]["error"]},
            "total_warning": {"value": lint_scan_pass_data["total"]["warning"]},
            "total_info": {"value": lint_scan_pass_data["total"]["info"]},
            "worse_cc_file_num": {"value": worse_cc_file_num},
            "over_cc_sum": {"value": over_cc_sum},
            "cc_func_average": {"value": cc_func_average},
            "over_cc_func_count": {"value": over_cc_func_count},
            "diff_over_cc_func_count": {"value": diff_over_cc_func_count},
            "over_cc_func_average": {"value": over_cc_func_average},
            "duplicate_rate": {"value": duplicate_rate},
        }

        return quality_data

    def check(self, key, expected_value, quality_data):
        """
        判断红线指标是否满足（小于等于）预期值
        """
        is_pass = None
        actual_value = None
        if expected_value is not None:
            actual_value = quality_data.get(key, {}).get("value")
            if actual_value is None:
                is_pass = False  # 未获取到数据，可能是没有开启对应的检查项
            else:
                if actual_value <= expected_value:
                    is_pass = True
                else:
                    is_pass = False
        return is_pass, actual_value
