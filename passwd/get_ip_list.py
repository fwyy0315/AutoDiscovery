# -*- coding:UTF-8 -*-
"""
@version: v1.0
@auther: ZhangYu
@contact: zhang.yu@accenture.com
@file: get_ip_list.py
@time：2017/2/20 16:40
"""
import datetime
import json
import sys
from action.cost import cost
from api.cmdbuild_api import CMDBuildAPI
from action.finallogging import FinalLogger
from passwd.get_check_conf import GetCheckConf
from IPy import IP

reload(sys)
sys.setdefaultencoding("UTF-8")

logger = FinalLogger.getLogger()
cmdbuild_api = CMDBuildAPI()
getconf = GetCheckConf()

ip_segment_cmdb = []
host_ip_cmdb = []
black_ip = []


class GetIPList(object):
    def get_cmdbuild_ip_segment(self, token):
        """
        获取CMDB的IP网段
        :return:主键、网段、网络区域、网络类型
        """
        get_cmdbuild_time = datetime.datetime.now()
        logger.info("开始在cmdbuild系统中收集ip_segment数据!")

        try:
            ip_segment_cmdb_num = 0
            ip_segment = cmdbuild_api.get_class(token, 'IP_Segment', cards=True)
            for i in json.loads(ip_segment)['data']:
                ip_segment_cmdb_info = {}
                if i['Description']:
                    ip_segment_cmdb_info['Description'] = i['Description'].rstrip()
                if i['IP_Segment']:
                    ip_segment_cmdb_info['IP_Segment'] = i['IP_Segment'].rstrip()
                if i['IP_district']:
                    ip_segment_cmdb_info['IP_district'] = i['IP_district'].rstrip()
                else:
                    ip_segment_cmdb_info['IP_district'] = None
                if i['Network_Type']:
                    ip_segment_cmdb_info['Network_Type'] = i['Network_Type'].rstrip()
                else:
                    ip_segment_cmdb_info['Network_Type'] = None
                if i['IPusage']:
                    ip_segment_cmdb_info['IPusage'] = i['IPusage'].rstrip()
                else:
                    ip_segment_cmdb_info['IPusage'] = None
                ip_segment_cmdb.append(ip_segment_cmdb_info)
                ip_segment_cmdb_num += 1
            logger.info("在cmdbuild系统上找到%d条ip_segment数据", ip_segment_cmdb_num)
            cost_time = cost(get_cmdbuild_time)
            logger.info("收集数据成功，耗时%d s", cost_time)
            return ip_segment_cmdb_num
        except Exception, e:
            logger.error("收集数据失败，报错内容：%s", e)

    def get_cmdbuild_host_ip(self, token):
        """
        获取与HOST关联的IP
        :return: 采集到的IP数量
        """
        get_cmdbuild_time = datetime.datetime.now()
        logger.info("开始在cmdbuild系统中收集host和ip关系数据!")
        try:
            host_ip_cmdb_num = 0
            relation_host_ip = cmdbuild_api.get_view(token, 'view_host_ip', cards=True)
            relation_host_ip_temp = json.loads(relation_host_ip)
            for i in relation_host_ip_temp:
                if str(relation_host_ip_temp[i]['Type']).__contains__('Perm IP'):
                    host_ip_cmdb_info = {'Host': relation_host_ip_temp[i]['Host'].strip('\n'),
                                         'System_Net_Config': relation_host_ip_temp[i]['IP'].strip('\n'),
                                         'Type': relation_host_ip_temp[i]['Type'].strip('\n')}
                    if relation_host_ip_temp[i]['OS']:
                        host_ip_cmdb_info['OS'] = relation_host_ip_temp[i]['OS'].strip('\n')
                    else:
                        host_ip_cmdb_info['OS'] = None
                    host_ip_cmdb.append(host_ip_cmdb_info)
                    host_ip_cmdb_num += 1
            logger.info("采集到%d条host和ip关系数据", host_ip_cmdb_num)
            cost_time = cost(get_cmdbuild_time)
            logger.info("cmdbuild平台host和ip关系采集成功! 耗时%d秒", cost_time)
            return host_ip_cmdb_num
        except Exception, e:
            logger.error("cmdbuild平台host和ip关系采集失败! 原因：%s", e)

    def get_ip_district(self):
        ip_district_production = []
        ip_district_simulation = []

        for i in ip_segment_cmdb:
            if i['Network_Type'] == u'服务网络':
                if i['IP_district']:
                    # 内网环境
                    if self.conf_info['district'] == 'intranet':
                        if self.conf_info['production'] == 'True':
                            if str(i['IP_district'].split('-')[0].strip()) == u'业务网' and \
                                            str(i['IP_district'].split('-')[1].strip()) == u'生产域' and not (
                                            str(i['IP_district'].split('-')[2].strip()) == u'用户接入区（广域网区）' or str(
                                        i['IP_district'].split('-')[2].strip()) == u'设备互联'):
                                ip_district_production.append(str(i['IP_Segment']))
                        if self.conf_info['simulation'] == 'True':
                            if not (str(i['IPusage'].strip()) == u'模拟域虚拟服务器管理' or str(
                                    i['IPusage'].strip()) == u'模拟信息区基础服务系统前置/应用服务器'):
                                if str(i['IP_district'].split('-')[0].strip()) == u'业务网' and \
                                                str(i['IP_district'].split('-')[1].strip()) == u'模拟域' and not (
                                                        str(i['IP_district'].split('-')[2].strip()) == u'设备互联' or str(
                                                    i['IP_district'].split('-')[2].strip()) == u'培训系统' or str(
                                                i['IP_district'].split('-')[2].strip()) == u'UAT环境' or str(
                                            i['IP_district'].split('-')[2].strip()) == u'模拟、培训和UAT服务器后端管理网段'):
                                    ip_district_simulation.append(str(i['IP_Segment']))
                    # 外网环境
                    elif self.conf_info['district'] == 'internet':
                        if self.conf_info['production'] == 'True':
                            if str(i['IP_district'].split('-')[0].strip()) == '互联网' and \
                                            str(i['IP_district'].split('-')[1].strip()) == u'生产域' and not (
                                        str(i['IP_district'].split('-')[2].strip()) == u'设备互联'):
                                ip_district_production.append(str(i['IP_Segment']))
                        if self.conf_info['simulation'] == 'True':
                            if str(i['IP_district'].split('-')[0].strip()) == '互联网' and \
                                            str(i['IP_district'].split('-')[1].strip()) == u'模拟域' and not (
                                            str(i['IP_district'].split('-')[2].strip()) == u'设备互联' or str(
                                        i['IP_district'].split('-')[2].strip()) == u'UAT环境'):
                                ip_district_simulation.append(str(i['IP_Segment']))
        ip_district = {'ip_district_production': ip_district_production,
                       'ip_district_simulation': ip_district_simulation}
        return ip_district

    def get_check_ip(self, conf_info):
        """
        获取符合采集网段且host关联的IP
        """
        ips = []
        win_ips = []
        get_check_time = datetime.datetime.now()
        ips_num = 0
        win_ips_num = 0
        self.conf_info = conf_info
        if self.conf_info['production'] == "True":
            ip_district = self.get_ip_district()['ip_district_production']
        elif self.conf_info['simulation'] == "True":
            ip_district = self.get_ip_district()['ip_district_simulation']

        for i in host_ip_cmdb:
            if not i['System_Net_Config'].__contains__('/'):
                for j in ip_district:
                    if self.verify_ip(i['System_Net_Config']):
                        if i['System_Net_Config'] in IP(j):
                            if i['OS']:
                                if not (i['OS'].__contains__('windows') or i['OS'].__contains__('Windows')):
                                    # IP 不在黑名单中
                                    if str(i['System_Net_Config']) not in black_ip:
                                        ips.append(str(i['System_Net_Config']))
                                        ips_num += 1
                                else:
                                    win_ips.append(str(i['System_Net_Config']))
                                    win_ips_num += 1
        cost_time = cost(get_check_time)
        logger.info("采集Host耗时%d秒" % (cost_time))
        return ips

    def verify_ip(self, ip):
        """
        判断IP是否合规
        """
        try:
            IP(ip)
            return True
        except Exception as e:
            logger.error('%s\tIP不合规，请检查：e' % (ip, e))
            return False
