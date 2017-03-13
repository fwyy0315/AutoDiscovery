# -*- coding:UTF-8 -*-
import json
import datetime
import sys
import ConfigParser
from action.cost import cost
from action.finallogging import FinalLogger
from action.excel import excel
from api.cmdbuild_api import CMDBuildAPI
from api.h3c_api import H3CAPI
from action.restore import restore

reload(sys)
sys.setdefaultencoding("UTF-8")

cf = ConfigParser.ConfigParser()
excel_flag = False
update_flag = False
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

start_time = datetime.datetime.now()
logger = FinalLogger.getLogger()
h3c_api = H3CAPI()

# todo：获取设备和网络清单，设备数量小于1000
device_url = '/imcrs/plat/res/device?size=1000'
device = json.loads(h3c_api.page(device_url))
netasset_url = '/imcrs/netasset/asset?assetPhyClass=3&size=1000'
netasset = json.loads(h3c_api.page(netasset_url))

netdevice_interface_h3c = []
netdevice_interface_cmdb = []
netdevice_interface_final = []
netdevice_interface_final_excel = []
interface_ip = []
interface_vlan = []


def get_h3c_netdevice_interface():
    get_h3c_time = datetime.datetime.now()
    logger.info("H3C平台网络接口数据开始采集!")
    try:
        netdevice_interface_h3c_num = 0
        for i in device['device']:
            # 循环获取接口、trunk、access信息
            interface_url = '/imcrs/plat/res/device/' + i['id'] + '/interface?size=1000'
            trunk_url = '/imcrs/vlan/trunk?devId=' + i['id'] + '&size=1000'
            access_url = '/imcrs/vlan/access?devId=' + i['id'] + '&size=1000'
            interface = json.loads(h3c_api.page(interface_url))
            trunk = json.loads(h3c_api.page(trunk_url))
            access = json.loads(h3c_api.page(access_url))

            # 判断接口与trunk、access口的ifIndex是否相同，添加Vlan信息
            # 输出主机名、端口号、vlan、对端ip、主机名+序列号、mac地址、状态
            if interface != {}:
                for x in interface['interface']:
                    if trunk:
                        interface1 = None
                        if str(trunk['trunkIf']).count('ifIndex') > 1:
                            for y in trunk['trunkIf']:
                                while y['ifIndex'] == x['ifIndex']:
                                    for k in netasset['netAsset']:
                                        while i['symbolName'] == k['deviceName']:
                                            if x['ifDescription'].count('/') > 1:
                                                r = x['ifDescription'].replace('-', '').split('/')[0].strip(
                                                    filter(str.isalpha, str(x['ifDescription'])))
                                                if k['name'].isdigit():
                                                    s = k['name']
                                                else:
                                                    s = k['relPos']
                                                if r == s:
                                                    interface1 = i['symbolName']
                                                    interface_vlan.append(
                                                        {'Description': i['symbolName'] + '_' + x['ifDescription'],
                                                         'Switch_Name': i['symbolName'] + '-' + k['serialNum'],
                                                         'Port': x['ifDescription'],
                                                         'Vlan': y['allowedVlans'],
                                                         'Use_Status': x['statusDesc'],
                                                         'code': '1'})
                                            else:
                                                if not (k['desc'].__contains__('Nexus2248 Chassis') or
                                                            k['desc'].__contains__('Nexus2348TP Chassis')):
                                                    interface1 = i['symbolName']
                                                    interface_vlan.append(
                                                        {'Description': i['symbolName'] + '_' + x['ifDescription'],
                                                         'Switch_Name': i['symbolName'] + '-' + k['serialNum'],
                                                         'Port': x['ifDescription'],
                                                         'Vlan': y['allowedVlans'],
                                                         'Use_Status': x['statusDesc'],
                                                         'code': '2'})
                                            break
                                    break
                        elif str(trunk['trunkIf']).count('ifIndex') == 1:
                            while y['ifIndex'] == x['ifIndex']:
                                for k in netasset['netAsset']:
                                    while i['symbolName'] == k['deviceName']:
                                        interface1 = i['symbolName']
                                        interface_vlan.append(
                                            {'Description': i['symbolName'] + '_' + x['ifDescription'],
                                             'Switch_Name': i['symbolName'] + '-' + k['serialNum'],
                                             'Port': x['ifDescription'],
                                             'Vlan': y['allowedVlans'],
                                             'Use_Status': x['statusDesc'],
                                             'code': '3'})
                                        break
                                break

                    if access:
                        interface2 = None
                        if interface1 is None:
                            if str(access['accessIf']).count('ifIndex') > 1:
                                for z in access['accessIf']:
                                    while z['ifIndex'] == x['ifIndex']:
                                        for k in netasset['netAsset']:
                                            while i['symbolName'] == k['deviceName']:
                                                if x['ifDescription'].count('/') > 1:
                                                    r = x['ifDescription'].replace('-', '').split('/')[0].strip(
                                                        filter(str.isalpha, str(x['ifDescription'])))
                                                    if k['name'].isdigit():
                                                        s = k['name']
                                                    else:
                                                        s = k['relPos']
                                                    if int(r) < 100:
                                                        if r == s:
                                                            interface2 = i['symbolName']
                                                            interface_vlan.append(
                                                                {'Description': i['symbolName'] + '_' + x[
                                                                    'ifDescription'],
                                                                 'Switch_Name': i['symbolName'] + '-' + k['serialNum'],
                                                                 'Port': x['ifDescription'],
                                                                 'Vlan': z['pvid'],
                                                                 'Use_Status': x['statusDesc'],
                                                                 'code': '4'})
                                                    else:
                                                        interface2 = i['symbolName']
                                                        # 当relPos>100时，序列号为主机,端口号为FEX型
                                                        if int(k['relPos']) == 1:
                                                            interface_vlan.append(
                                                                {'Description': i['symbolName'] + '_' + x[
                                                                    'ifDescription'],
                                                                 'Switch_Name': i['symbolName'] + '-' + k['serialNum'],
                                                                 'Port': x['ifDescription'],
                                                                 'Vlan': z['pvid'],
                                                                 'Use_Status': x['statusDesc'],
                                                                 'code': '5'})
                                                else:
                                                    if not (k['desc'].__contains__('Nexus2248 Chassis') or
                                                                k['desc'].__contains__('Nexus2348TP Chassis')):
                                                        interface2 = i['symbolName']
                                                        interface_vlan.append(
                                                            {'Description': i['symbolName'] + '_' + x[
                                                                'ifDescription'],
                                                             'Switch_Name': i['symbolName'] + '-' + k['serialNum'],
                                                             'Port': x['ifDescription'],
                                                             'Vlan': z['pvid'],
                                                             'Use_Status': x['statusDesc'],
                                                             'code': '6'})
                                                break
                                        break
                            elif str(access['accessIf']).count('ifIndex') == 1:
                                while z['ifIndex'] == x['ifIndex']:
                                    for k in netasset['netAsset']:
                                        while i['symbolName'] == k['deviceName']:
                                            interface2 = i['symbolName']
                                            interface_vlan.append(
                                                {'Description': i['symbolName'] + '_' + x['ifDescription'],
                                                 'Switch_Name': i['symbolName'] + '-' + k['serialNum'],
                                                 'Port': x['ifDescription'],
                                                 'Vlan': z['pvid'],
                                                 'Use_Status': x['statusDesc'],
                                                 'code': '7'
                                                 })
                                            break
                                    break

                    if interface1 is None and interface2 is None:
                        for k in netasset['netAsset']:
                            if i['symbolName'] == k['deviceName']:
                                if x['ifDescription'].count('/') > 1:
                                    r = x['ifDescription'].replace('-', '').split('/')[0].strip(
                                        filter(str.isalpha, str(x['ifDescription'])))
                                    if k['name'].isdigit():
                                        s = k['name']
                                    else:
                                        s = k['relPos']
                                    if r == s:
                                        interface_vlan.append(
                                            {'Description': i['symbolName'] + '_' + x['ifDescription'],
                                             'Switch_Name': i['symbolName'] + '-' + k['serialNum'],
                                             'Port': x['ifDescription'],
                                             'Vlan': '',
                                             'Use_Status': x['statusDesc'],
                                             'code': '8'})
                                    # todo:华为交换机 S5720-52X-PWR-SI-AC 单台有机柜号，目前规则不符合，此为定制
                                    elif k['name'].__contains__('S5720'):
                                        interface_vlan.append(
                                            {'Description': i['symbolName'] + '_' + x['ifDescription'],
                                             'Switch_Name': i['symbolName'] + '-' + k['serialNum'],
                                             'Port': x['ifDescription'],
                                             'Vlan': '',
                                             'Use_Status': x['statusDesc'],
                                             'code': '9'})
                                else:
                                    # 不包含 Nexus2248 Chassis型号
                                    if not (k['name'].__contains__('Nexus2248 Chassis') and
                                                k['name'].__contains__('Nexus2348TP Chassis')):
                                        interface_vlan.append(
                                            {'Description': i['symbolName'] + '_' + x['ifDescription'],
                                             'Switch_Name': i['symbolName'] + '-' + k['serialNum'],
                                             'Port': x['ifDescription'],
                                             'Vlan': '',
                                             'Use_Status': x['statusDesc'],
                                             'code': '10'})

        # 过滤非物理接口
        for i in interface_vlan:
            interface_port = i['Port'].lower()
            if interface_port.__contains__('ethernet') \
                    or interface_port.__contains__('fastethernet') \
                    or interface_port.__contains__('gigabitethernet') \
                    or interface_port.__contains__('flex'):
                netdevice_interface_h3c_info = {'Description': i['Description'],
                                                'Switch_Name': i['Switch_Name'],
                                                'Port': i['Port'],
                                                'Vlan': i['Vlan']}
                if i['Use_Status'] == u'Up':
                    netdevice_interface_h3c_info['Use_Status'] = u'已使用'
                else:
                    netdevice_interface_h3c_info['Use_Status'] = u'未使用'
                netdevice_interface_h3c.append(netdevice_interface_h3c_info)
                netdevice_interface_h3c_num += 1

        excel(netdevice_interface_h3c, 'netdevice_interface_h3c')
        cost_h3c_time = cost(get_h3c_time)
        logger.info("H3C平台网络接口数据采集成功! 采集%d条数据,耗时%d秒" % (netdevice_interface_h3c_num, cost_h3c_time))
    except Exception, e:
        logger.error("H3C平台网络接口数据采集失败! 原因：%s", e)


def get_cmdb_netdevice_interface():
    get_cmdbuild_time = datetime.datetime.now()
    logger.info("cmdbuild网络接口数据开始采集!")
    netdevice_interface_cmdb_num = 0
    try:
        # 通过cmdbuild接口数据采集数据
        # 'Description', 'Switch_Name', 'Port', 'Vlan', 'IP_Addr'
        switch_ports_netdevice = cmdbuild_api.get_class(token, 'Switch_Ports', cards=True)
        if switch_ports_netdevice:
            for i in json.loads(switch_ports_netdevice)['data']:
                netdevice_interface_cmdb_info = {'Description': i['Description'],
                                                 'Switch_Name': i['Switch_Name'],
                                                 'Port': i['Port']}
                if i['Vlan'] is None:
                    netdevice_interface_cmdb_info['Vlan'] = ''
                else:
                    netdevice_interface_cmdb_info['Vlan'] = i['Vlan']
                if i['Use_Status'] is None:
                    netdevice_interface_cmdb_info['Use_Status'] = ''
                else:
                    netdevice_interface_cmdb_info['Use_Status'] = i['Use_Status']
                netdevice_interface_cmdb.append(netdevice_interface_cmdb_info)
                netdevice_interface_cmdb_num += 1

        # print netdevice_interface_cmdb
        excel(netdevice_interface_cmdb, 'netdevice_interface_cmdb')

        cost_cmdbuild_time = cost(get_cmdbuild_time)
        logger.info("cmdbuild网络接口数据采集成功! 采集%d条数据,耗时%d秒" % (netdevice_interface_cmdb_num, cost_cmdbuild_time))
    except Exception, e:
        logger.error("cmdbuild网络接口数据采集失败! 原因：%s", e)


def import_netdevice_interface():
    logger.info("网络接口数据开始比较!")
    try:
        update_netdevice_interface_num = 0
        add_netdevice_interface_num = 0
        if netdevice_interface_cmdb and netdevice_interface_h3c:
            for i in netdevice_interface_h3c:
                compare_temp = None
                for j in netdevice_interface_cmdb:
                    # 机器名和端口相同时
                    # ethernet、fastethernet、gigabitethernet输出值
                    if i['Switch_Name'] and j['Switch_Name']:
                        while i['Switch_Name'].upper() == j['Switch_Name'].upper() and i['Port'] == restore(
                                str(j['Port'])):
                            compare_temp = i['Description']
                            if i['Port'] and i['Port'] != 'FastEthernet0' and i['Port'] != 'FastEthernet1':
                                if cmp(i, j) != 0:
                                    netdevice_interface_final_info = {'Description': j['Description'],
                                                                      'Switch_Name': i['Switch_Name'],
                                                                      'Port': i['Port'],
                                                                      'Vlan': i['Vlan'],
                                                                      'Use_Status': i['Use_Status']}
                                    if j['Use_Status'] == u'待下线':
                                        netdevice_interface_final_info['Use_Status'] = j['Use_Status']
                                        if cmp(netdevice_interface_final_info, j):
                                            netdevice_interface_final.append(netdevice_interface_final_info)
                                    else:
                                        netdevice_interface_final_info['Use_Status'] = i['Use_Status']
                                        netdevice_interface_final.append(netdevice_interface_final_info)
                                    update_netdevice_interface_num += 1
                                    if excel_flag:
                                        netdevice_interface_final_info_old = {'Description': j['Description'],
                                                                              'Switch_Name': j['Switch_Name'],
                                                                              'Port': j['Port'],
                                                                              'Vlan': j['Vlan'],
                                                                              'Use_Status': j['Use_Status'],
                                                                              'status': 'O'
                                                                              }
                                        # print netdevice_interface_final_info_old
                                        netdevice_interface_final_info_update = {'Description': j['Description'],
                                                                                 'Switch_Name': i['Switch_Name'],
                                                                                 'Port': i['Port'],
                                                                                 'Vlan': i['Vlan'],
                                                                                 'status': 'U'
                                                                                 }
                                        if j['Use_Status'] == u'待下线':
                                            netdevice_interface_final_info_update['Use_Status'] = j['Use_Status']
                                            if cmp(netdevice_interface_final_info, j):
                                                netdevice_interface_final_excel.append(
                                                    netdevice_interface_final_info_old)
                                                netdevice_interface_final_excel.append(
                                                    netdevice_interface_final_info_update)
                                        else:
                                            netdevice_interface_final_info_update['Use_Status'] = i['Use_Status']
                                            netdevice_interface_final_excel.append(netdevice_interface_final_info_old)
                                            netdevice_interface_final_excel.append(netdevice_interface_final_info_update)
                                        # print netdevice_interface_final_info_update


                            break

                # 如果无法匹配，新增数据
                # ethernet、fastethernet、gigabitethernet输出值
                if compare_temp is None:
                    if i['Port'] and i['Port'] != 'FastEthernet0' and i['Port'] != 'FastEthernet1':
                        netdevice_interface_final.append(i)
                        add_netdevice_interface_num += 1
                        if excel_flag:
                            netdevice_interface_final_info_add = {'Description': i['Description'],
                                                                  'Switch_Name': i['Switch_Name'],
                                                                  'Port': i['Port'],
                                                                  'Vlan': i['Vlan'],
                                                                  'Use_Status': i['Use_Status'],
                                                                  'status': 'A'
                                                                  }
                            netdevice_interface_final_excel.append(netdevice_interface_final_info_add)

            logger.info("需要更新%d条，新增%d条", update_netdevice_interface_num, add_netdevice_interface_num)

            if excel_flag:
                if netdevice_interface_final_excel:
                    excel(netdevice_interface_final_excel, 'netdevice_interface')

            if update_flag:
                import_time = datetime.datetime.now()
                if update_netdevice_interface_num != 0 or add_netdevice_interface_num != 0:
                    netdevice_dict = {"Switch_Ports": netdevice_interface_final}
                    # print json.dumps(netdevice_dict)
                    logger.info("开始导入数据")
                    update_result = cmdbuild_api.put_update(token, json.dumps(netdevice_dict))
                    cost_time = cost(import_time)
                    logger.info("导入数据成功! 耗时%d秒", cost_time)
                    logger.info("cmdbuild返回结果：" + update_result)
                else:
                    cost_time = cost(import_time)
                    logger.info("两边数据一致! 耗时%d秒", cost_time)
        elif not netdevice_interface_h3c:
            logger.info("H3C平台采集无数据!")
        elif not netdevice_interface_cmdb:
            logger.info("cmdbuild平台采集无数据!")
    except Exception, e:
        logger.error("导入数据失败! 原因:%s", e)


if __name__ == '__main__':
    cmdbuild_api = CMDBuildAPI()
    token = cmdbuild_api.get_token()
    if token:
        get_cmdb_netdevice_interface()
        get_h3c_netdevice_interface()
        import_netdevice_interface()
