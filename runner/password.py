# -*- coding:UTF-8 -*-
"""
@version: v1.0
@auther: ZhangYu
@contact: zhang.yu@accenture.com
@file: password.py
@time：2017/2/24 14:02
"""
import ConfigParser
import multiprocessing
import json
import datetime
from action.cost import cost
from action.excel import excel
from action.finallogging import FinalLogger
from api.cmdbuild_api import CMDBuildAPI
from passwd.get_ip_list import GetIPList
from passwd.get_check_conf import GetCheckConf
from passwd.get_passwd_info import CollectPastPassword

ctp = CollectPastPassword()
cmdbuild_api = CMDBuildAPI()
logger = FinalLogger.getLogger()
token = cmdbuild_api.get_token()
gil = GetIPList()
gcc = GetCheckConf()
lastpasswd_cmdb = []
lastpasswd_final = []


excel_flag = False
update_flag = False

cf = ConfigParser.ConfigParser()
try:
    cf.read("../conf/base.conf")
    # 获取excel_flag
    if cf.get('flag', 'excel_flag'):
        if cf.get('flag', 'excel_flag').__contains__('True'):
            excel_flag = bool(cf.get('flag', 'excel_flag'))
        else:
            excel_flag = bool()
    else:
        excel_flag = bool()
    # 获取update_flag
    if cf.get('flag', 'update_flag'):
        if cf.get('flag', 'update_flag').__contains__('True'):
            update_flag = bool(cf.get('flag', 'update_flag'))
        else:
            update_flag = bool()
    else:
        update_flag = bool()
except Exception, e:
    print e


def get_passwd_info(ip):
    try:
        if ctp.get_connect(ip):
            if ctp.get_type() == 'AIX' and ctp.get_homename():
                aix_accounts = ctp.get_config('../conf/aix.conf')
                if aix_accounts:
                    ctp.compare_time(ctp.get_aix_passwd_time(aix_accounts), ctp.get_system_time(),
                                     ctp.get_past_day('AIX'))
            elif ctp.get_type() == 'SunOS' and ctp.get_homename():
                solaris_accounts = ctp.get_config('../conf/solaris.conf')
                if solaris_accounts:
                    ctp.compare_time(ctp.get_solaris_passwd_time(solaris_accounts), ctp.get_system_time(),
                                     ctp.get_past_day('SunOS'))
        return ctp.passwd_info
    except Exception, e:
        logger.error('采集信息失败:%s' % e)


def get_cmdbuild_lastpasswd():
    get_cmdbuild_time = datetime.datetime.now()
    logger.info("cmdbuild平台网络设备数据开始采集!")
    try:
        LastPasswd = cmdbuild_api.get_class(token, 'LastPasswd', cards=True)
        for i in json.loads(LastPasswd)['data']:
            for k, v in i.items():
                if i[k] is None:
                    i[k] = u''
            lastpasswd_cmdb_info = {
                'Description': i['Description'],
                'HostName': i['HostName'],
                'IP': i['IP'],
                'UserName': i['UserName'],
                'UpdateTime': i['UpdateTime'],
                'Expired': i['Expired']
            }
            lastpasswd_cmdb.append(lastpasswd_cmdb_info)
        cost_time = cost(get_cmdbuild_time)
        logger.info("lastpasswd数据采集成功! 耗时%d秒", cost_time)
    except Exception, e:
        logger.error("lastpasswd数据采集失败! 原因：%s", e)


def compare_lastpasswd():
    import_time = datetime.datetime.now()
    logger.info("Host和OS关系数据开始比较!")
    try:
        update_lastpasswd_num = 0
        add_lastpasswd_num = 0
        if lastpasswd_cmdb:
            for k in lastpasswd_fact:
                if k:
                    lastpasswd_temp = None
                    for i in k:
                        for j in lastpasswd_cmdb:
                            if i and j:
                                while i['Description'] == j['Description']:
                                    lastpasswd_temp = i['Description']
                                    if cmp(i, j) != 0:
                                        lastpasswd_final.append(i)
                                        update_lastpasswd_num += 1
                                    break

                        if lastpasswd_temp is None:
                            lastpasswd_final.append(i)
                            add_lastpasswd_num += 1
        else:
            for k in lastpasswd_fact:
                if k:
                    for i in k:
                        lastpasswd_final.append(i)
                        add_lastpasswd_num += 1

        logger.info("Host和OS关系数据比较结束！修改%d条数据，新增%d条数据" % (update_lastpasswd_num, add_lastpasswd_num))

        if update_lastpasswd_num != 0 or add_lastpasswd_num != 0:
            lastpasswd_final_dict = {'LastPasswd': lastpasswd_final}
            print lastpasswd_final_dict
            if update_flag:
                result = cmdbuild_api.put_update(token, json.dumps(lastpasswd_final_dict))
                logger.info("cmdbuild返回结果：" + result)
                cost_os_time = cost(import_time)
                logger.info("导入数据成功! 耗时%d秒", cost_os_time)
            # if excel_flag:
            #     excel(lastpasswd_final_dict,lastpasswd_final)
        else:
            cost_os_time = cost(import_time)
            logger.info("两边数据一致! 耗时%d秒", cost_os_time)
    except Exception, e:
        logger.error("Host和OS关系数据比较失败，报错内容：%s", e)


def mult(ips, processes=multiprocessing.cpu_count() * 8):
    pool = multiprocessing.Pool(processes=processes)
    return pool.map(get_passwd_info, ips)


if token:
    if gil.get_cmdbuild_ip_segment(token) > 0 and gil.get_cmdbuild_host_ip(token) > 0:
        conf_info = gcc.get_model()

        # print conf_info
        # print gil.get_check_ip(conf_info)
        # print len(gil.get_check_ip(conf_info))
        # ip_list = ['199.31.178.24', '199.31.177.160']
        lastpasswd_fact = mult(gil.get_check_ip(conf_info))
        # lastpasswd_fact = mult(ip_list)
        get_cmdbuild_lastpasswd()
        compare_lastpasswd()

