# -*- coding:UTF-8 -*-
"""
@version: v1.0
@auther: ZhangYu
@contact: zhang.yu@accenture.com
@file: get_check_conf.py
@time：2017/2/22 11:11
"""

import ConfigParser
import socket
from action.finallogging import FinalLogger

logger = FinalLogger.getLogger()


class GetCheckConf(object):
    def __init__(self):
        self.hostname = socket.gethostname()
        self.cf = ConfigParser.ConfigParser()
        self.cf.read("../conf/base.conf")
        self.sections = self.cf.items('hostname')
        self.district = None

    def get_model(self):
        self.sections = self.cf.items('hostname')
        try:
            for i in self.sections:
                if str(i[1]) == self.hostname:
                    self.district = str(i[0])

            try:
                production = self.cf.get('model', 'production')
            except:
                production = 'False'
            try:
                simulation = self.cf.get('model', 'simulation')
            except:
                simulation = 'False'

            if production == 'True':
                production_login_info = self.get_login_info('production')
            else:
                production_login_info = None
            if simulation == 'True':
                simulation_login_info = self.get_login_info('simulation')
            else:
                production_login_info = None

            conf_info = {'hostname': self.hostname,
                         'district': self.district,
                         'simulation': simulation,
                         'simulation_info': simulation_login_info,
                         'production': production,
                         'production_info': production_login_info}
            return conf_info
        except Exception, e:
            logger.error('读取配置文件失败:%s', e)
            return False

    def get_login_info(self, model):
        try:
            username = self.cf.get(model, 'username')
            password = self.cf.get(model, 'password')
            login_info = {'username': username,
                          'password': password}
            return login_info
        except Exception, e:
            logger.error('读取%s模式登录信息获取失败:%s' % (model, e))
            return False
