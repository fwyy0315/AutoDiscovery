# -*- coding:UTF-8 -*-
"""
@version: v1.0
@auther: ZhangYu
@contact: zhang.yu@accenture.com
@file: conf_api.py
@time：2017/3/7 16:19
"""
import ConfigParser
import json
from action.finallogging import FinalLogger

logger = FinalLogger.getLogger()


class GetConfInfo:
    def __init__(self):
        self.cf = ConfigParser.ConfigParser()

    def get_conf(self):
        try:
            self.cf.read("../conf/base.conf")
            return True
        except Exception, e:
            logger.error("base.conf配置文件获取失败:%s", e)
            return False

    def get_cmdb_conf(self):
        """
        获取cmdb配置文件信息
        :return:
        """
        try:
            if self.get_conf():
                username = self.cf.get('cmdbuild', 'username')
                password = self.cf.get('cmdbuild', 'password')
                cmdbuild_url = self.cf.get('cmdbuild', 'cmdbuild_url')
                data = json.dumps({"username": username, "password": password})
                return {'username': username,
                        'password': password,
                        'cmdbuild_url': cmdbuild_url,
                        'data': data}
            else:
                return False
        except Exception, e:
            logger.error("cmdbuild配置文件解析失败:%s", e)
            return False

    def get_system_conf(self):
        """
        获取system配置文件信息
        :return:
        """
        try:
            if self.get_conf():
                username = self.cf.get('system', 'username')
                password = self.cf.get('system', 'password')
                return {'username': username,
                        'password': password}
            else:
                return False
        except Exception, e:
            logger.error("system配置文件解析失败:%s", e)
            return False

    def get_h3c_conf(self):
        """
        获取h3c配置文件信息
        :return:
        """
        try:
            if self.get_conf():
                username = self.cf.get('h3c', 'username')
                password = self.cf.get('h3c', 'password')
                imc_url = self.cf.get("h3c", "imc_url")
                http_url = self.cf.get("h3c", "http_url")
                return {'username': username,
                        'password': password,
                        'imc_url': imc_url,
                        'http_url': http_url}
            else:
                return False
        except Exception, e:
            logger.error("h3c配置文件解析失败:%s", e)
            return False
