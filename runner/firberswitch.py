# -*- coding:UTF-8 -*-
import json
import datetime
import sys

from api.cmdbuild_api import CMDBuildAPI
from action.finallogging import FinalLogger
from api.fiberswitch_api import mult_ssh2_fiberswitch
from action.cost import cost
from action.excel import excel

reload(sys)
sys.setdefaultencoding("UTF-8")

logger = FinalLogger.getLogger()

excel_flag = False
update_flag = True

logger = FinalLogger.getLogger()
cmdbuild_api = CMDBuildAPI()

firberswitch_fact = []
firberswitch_port_fact = []

firberswitch_cmdb = []
firberswitch_port_cmdb = []

firberswitch_final = []
firberswitch_port_final = []

firberswitch_excel = []
firberswitch_port_excel = []


def get_cmdbuild_firberswitch():
    get_cmdbuild_time = datetime.datetime.now()
    logger.info("cmdbuild平台FC_Switch数据开始采集!")
    try:
        firberswitch_cmdb_num = 0
        fc_switch = cmdbuild_api.get_class(token, 'FC_Switch', cards=True)
        for i in json.loads(fc_switch)['data']:
            for k, v in i.items():
                if i[k] is None:
                    i[k] = u''
            # 存储设备-光纤交换机
            if i['AppType'] == u'\u5149\u7ea4\u4ea4\u6362\u673a':
                firberswitch_cmdb.append({'Description': i['Description'],
                                          'WWNN': i['WWNN'],
                                          # 'AppType': i['AppType'],
                                          'DevName': i['DevName'],
                                          'Series_No': i['Series_No'],
                                          'Total_Ports': i['Total_Ports'],
                                          'Ports_Enabled': i['Ports_Enabled'],
                                          'Ports_Used': i['Ports_Used'],
                                          'Speed_Support': i['Speed_Support'],
                                          # 'MANUFACTURE_Factory': i['MANUFACTURE_Factory'],
                                          # 'Speed_Support': i['Speed_Support'],
                                          # 'CI_modelid': i['CI_modelid'],
                                          'Fabric_OS': i['Fabric_OS'],
                                          'IP': i['IP']})
                firberswitch_cmdb_num += 1

        cost_time = cost(get_cmdbuild_time)
        logger.info("在cmdbuild系统上找到%d条FirberSwitch数据", firberswitch_cmdb_num)
        logger.info("cmdbuild平台FC_Switch数据采集成功! 耗时%d秒", cost_time)
        return firberswitch_cmdb_num
    except Exception, e:
        logger.error("cmdbuild平台FC_Switch数据采集失败! 原因：%s", e)


def get_cmdbuild_firberswitch_port():
    get_cmdbuild_time = datetime.datetime.now()
    logger.info("cmdbuild平台FC_Switch_Port数据开始采集!")
    try:
        firberswitch_port_cmdb_num = 0
        fc_switch_port = cmdbuild_api.get_class(token, 'FC_Switch_Port', cards=True)
        for i in json.loads(fc_switch_port)['data']:
            for k, v in i.items():
                if i[k] is None:
                    i[k] = u''

            firberswitch_port_cmdb.append({'Description': i['Description'],
                                           'FCSwitch_Name': i['FCSwitch_Name'],
                                           'Slot': i['Slot'],
                                           'Port': i['Port'],
                                           'Domain_Index': i['Domain_Index'],
                                           'Speed': i['Speed'],
                                           'FC_Switch_Port_State': i['FC_Switch_Port_State'],
                                           # 'Host_HBA': i['Host_HBA'],
                                           'Host_HBA_WWPN': i['Host_HBA_WWPN']})
            firberswitch_port_cmdb_num += 1

        cost_time = cost(get_cmdbuild_time)
        logger.info("在cmdbuild系统上找到%d条FC_Switch_Port数据", firberswitch_port_cmdb_num)
        logger.info("cmdbuild平台FC_Switch_Port数据采集成功! 耗时%d秒", cost_time)
        return firberswitch_port_cmdb_num
    except Exception, e:
        logger.error("cmdbuild平台FC_Switch_Port数据采集失败! 原因：%s", e)


def import_firberswitch(ips):
    firberswitch_dict = mult_ssh2_fiberswitch(ips)
    for i in firberswitch_dict:
        firberswitch_fact.append(i['firberswitch_fact'])
        firberswitch_port_fact.append(i['firberswitch_port_fact'])
    try:
        import_time = datetime.datetime.now()
        logger.info("FirberSwitch数据开始比较!")
        update_firberswitch_num = 0
        add_firberswitch_num = 0
        # print firberswitch_fact
        for i in firberswitch_fact:
            firberswitch_temp = None
            for j in firberswitch_cmdb:
                if i['Series_No'] and j['Series_No']:
                    while i['Series_No'].upper() == j['Series_No'].upper():
                        firberswitch_temp = i['Series_No']
                        if cmp(i, j) != 0:
                            firberswitch_final.append({'Description': i['Description'],
                                                       'WWNN': i['WWNN'],
                                                       # 'AppType': i['AppType'],
                                                       'DevName': i['DevName'],
                                                       'Series_No': i['Series_No'],
                                                       'Total_Ports': i['Total_Ports'],
                                                       'Ports_Enabled': i['Ports_Enabled'],
                                                       'Ports_Used': i['Ports_Used'],
                                                       'Speed_Support': i['Speed_Support'],
                                                       # 'MANUFACTURE_Factory': i['MANUFACTURE_Factory'],
                                                       # 'Speed_Support': i['Speed_Support'],
                                                       # 'CI_modelid': i['CI_modelid'],
                                                       'Fabric_OS': i['Fabric_OS'],
                                                       'IP': i['IP']})
                            j['status'] = 'O'
                            firberswitch_excel.append(j)
                            i['status'] = 'U'
                            firberswitch_excel.append(i)
                            update_firberswitch_num += 1
                        break

            if firberswitch_temp is None:
                firberswitch_final.append(i)
                i['status'] = 'A'
                firberswitch_excel.append(i)
                add_firberswitch_num += 1

        logger.info("FirberSwitch数据比较结束！修改%d条，新增%d条", update_firberswitch_num, add_firberswitch_num)

        if update_flag:
            if update_firberswitch_num != 0 or add_firberswitch_num != 0:
                firberswitch_dict = {"FC_Switch": firberswitch_final}
                update_result = cmdbuild_api.put_update(token, json.dumps(firberswitch_dict))
                cost_os_time = cost(import_time)
                logger.info("导入数据成功! 耗时%d秒", cost_os_time)
                logger.info("cmdbuild返回结果：" + update_result)
            else:
                cost_os_time = cost(import_time)
                logger.info("两边数据一致! 耗时%d秒", cost_os_time)

        if excel_flag:
            if firberswitch_excel:
                excel(firberswitch_excel, 'FC_Switch')

    except Exception, e:
        logger.error("FirberSwitch数据比较失败，报错内容：%s", e)

    try:
        import_time = datetime.datetime.now()
        logger.info("FirberSwitch数据开始比较!")
        update_firberswitch_port_num = 0
        add_firberswitch_port_num = 0

        for i in firberswitch_port_fact:
            # print i
            for k in range(len(i)):
                firberswitch_port_temp = None
                # print i[k]
                for j in firberswitch_port_cmdb:
                    if i[k]['Description'] and j['Description']:
                        while i[k]['Description'].upper() == j['Description'].upper():
                            firberswitch_port_temp = i[k]['FCSwitch_Name']
                            if cmp(i[k], j) != 0:
                                print i[k]
                                print j
                                firberswitch_port_info = {'Description': j['Description'],
                                                          'FCSwitch_Name': i[k]['FCSwitch_Name'],
                                                          'Slot': i[k]['Slot'],
                                                          'Port': i[k]['Port'],
                                                          'Domain_Index': i[k]['Domain_Index'],
                                                          'Speed': i[k]['Speed'],
                                                          'FC_Switch_Port_State': i[k]['FC_Switch_Port_State']}
                                if i[k].__contains__('Host_HBA_WWPN'):
                                    firberswitch_port_info['Host_HBA_WWPN'] = i[k]['Host_HBA_WWPN']
                                else:
                                    firberswitch_port_info['Host_HBA_WWPN'] = u''
                                firberswitch_port_final.append(firberswitch_port_info)
                                j['status'] = 'O'
                                firberswitch_port_excel.append(j)
                                i[k]['status'] = 'U'
                                firberswitch_port_excel.append(i[k])
                                update_firberswitch_port_num += 1
                            break

                if firberswitch_port_temp is None:
                    firberswitch_port_final.append(i[k])
                    i[k]['status'] = 'A'
                    firberswitch_port_excel.append(i[k])
                    add_firberswitch_port_num += 1

        logger.info("FirberSwitch_Port数据比较结束！修改%d条，新增%d条", update_firberswitch_port_num, add_firberswitch_port_num)

        if update_flag:
            if update_firberswitch_port_num != 0 or add_firberswitch_port_num != 0:
                firberswitch_port_dict = {"FC_Switch_Port": firberswitch_port_final}
                update_result = cmdbuild_api.put_update(token, json.dumps(firberswitch_port_dict))
                cost_os_time = cost(import_time)
                logger.info("导入数据成功! 耗时%d秒", cost_os_time)
                logger.info("cmdbuild返回结果：" + update_result)
            else:
                cost_os_time = cost(import_time)
                logger.info("两边数据一致! 耗时%d秒", cost_os_time)

        if excel_flag:
            if firberswitch_port_excel:
                excel(firberswitch_port_excel, 'FC_Switch_Port')

    except Exception, e:
        logger.error("FirberSwitch_Port数据比较失败，报错内容：%s", e)


if __name__ == '__main__':
    token = cmdbuild_api.get_token()
    if token:
        if get_cmdbuild_firberswitch() > 0 and get_cmdbuild_firberswitch_port() > 0:
            ips = ['200.31.129.130']
            import_firberswitch(ips)
    else:
        logger.error("获取token失败，请检查cmdbuild系统接口")
