# -*- coding:UTF-8 -*-
import json
import datetime
import sys
import ConfigParser
from api.cmdbuild_api import CMDBuildAPI
from api.h3c_api import H3CAPI
from action.finallogging import FinalLogger
from action.restore import transform
from action.cost import cost
from action.excel import excel

reload(sys)
sys.setdefaultencoding("UTF-8")

logger = FinalLogger.getLogger()
h3c_api = H3CAPI()

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


# todo：获取设备和网络清单，假设设备数小于1000
device_url = '/imcrs/plat/res/device?size=1000'
netasset_url = '/imcrs/netasset/asset?assetPhyClass=3&size=1000'

netdevice_h3c = []
netdevice_cmdb = []
netdevice_final = []
netdevice_final_excel = []


def get_h3c_netdevice():
    get_h3c_time = datetime.datetime.now()
    logger.info("H3C平台网络设备数据开始采集!")
    try:
        device = json.loads(h3c_api.page(device_url))
        netasset = json.loads(h3c_api.page(netasset_url))
        for i in device['device']:
            for j in netasset['netAsset']:
                while i['symbolName'] == j['deviceName']:
                    devicedetail_url = '/imcrs/plat/res/device/' + i['id'] + ''
                    devicedetail = json.loads(h3c_api.page(devicedetail_url))
                    # 48x1GE, 4x10GE 属于板卡，非交换机
                    if not j['model'].__contains__('Fabric Extender Module: 48x1GE, 4x10GE'):
                        netdevice_h3c_info = {'Description': i['symbolName'] + '-' + j['serialNum'],
                                              'DevName': i['symbolName'],
                                              'Manage_IP_Addr': i['ip'],
                                              'Series_No': j['serialNum'],
                                              # 'CI_modelid': ' '.join(devicedetail['typeName'].split()[1:]),
                                              'MANUFACTURE_Factory': transform(
                                                  str(devicedetail['typeName'].split()[0])),
                                              'OS_Bin': devicedetail['version']}
                        # 当网络资产中有型号信息，对网络信息进行处理获取信息，如果缺失，采用设备信息
                        if j['model']:
                            if j['model'].rstrip().__contains__(' '):
                                # 型号中包含Series关键字，则到devicedetail中获取
                                if not j['model'].__contains__('Series'):
                                    netdevice_h3c_info['CI_modelid'] = ' '.join(j['model'].split()[1:])
                                else:
                                    netdevice_h3c_info['CI_modelid'] = ' '.join(devicedetail['typeName'].split()[1:])
                            else:
                                netdevice_h3c_info['CI_modelid'] = j['model']
                        else:
                            netdevice_h3c_info['CI_modelid'] = ' '.join(devicedetail['typeName'].split()[1:])
                        # 当系统版本不存在时，从系统描述中获取OS_Version
                        if j['softVersion']:
                            netdevice_h3c_info['OS_Version'] = j['softVersion']
                        else:
                            if devicedetail['sysDescription'].__contains__('Version'):
                                for k in devicedetail['sysDescription'].split(','):
                                    if k.__contains__('Version') and not k.__contains__('Inc. Device Manager'):
                                        netdevice_h3c_info['OS_Version'] = k.split('Version ')[-1].strip()

                        netdevice_h3c.append(netdevice_h3c_info)
                    break
        get_h3c_time = cost(get_h3c_time)
        logger.info("H3C平台网络设备数据采集成功! 耗时%d秒", get_h3c_time)
    except Exception, e:
        logger.error("H3C平台网络设备数据采集失败! 原因：%s", e)


def get_cmdbuild_netdevice():
    get_cmdbuild_time = datetime.datetime.now()
    logger.info("cmdbuild平台网络设备数据开始采集!")
    try:
        NetDevice = cmdbuild_api.get_class(token, 'NetDevice', cards=True)
        for i in json.loads(NetDevice)['data']:
            for k, v in i.items():
                if i[k] is None:
                    i[k] = u''
            netdevice_cmdb_info = {'Description': i['Description'],
                                   'DevName': i['DevName'],
                                   'Manage_IP_Addr': i['Manage_IP_Addr'],
                                   'Series_No': i['Series_No'],
                                   'CI_modelid': i['CI_modelid'],
                                   'MANUFACTURE_Factory': i['MANUFACTURE_Factory'],
                                   'OS_Version': i['OS_Version'],
                                   'OS_Bin': i['OS_Bin']}
            netdevice_cmdb.append(netdevice_cmdb_info)

        cost_time = cost(get_cmdbuild_time)
        logger.info("cmdbuild平台网络设备数据采集成功! 耗时%d秒", cost_time)
    except Exception, e:
        logger.error("cmdbuild平台网络设备数据采集失败! 原因：%s", e)


def import_netdevice():
    import_netdevice_time = datetime.datetime.now()
    logger.info("网络设备数据开始比较!")

    update_netdevice_num = 0
    add_netdevice_num = 0
    try:
        if netdevice_h3c and netdevice_cmdb:
            for i in netdevice_h3c:
                import_temp = None
                for j in netdevice_cmdb:
                    if j['DevName'] and i['Series_No'] and j['Series_No']:
                        while i['Series_No'].upper() == j['Series_No'].upper():
                            import_temp = i['Series_No']
                            if cmp(i, j) != 0:
                                netdevice_final.append(
                                    {'Description': j['Description'],
                                     'DevName': i['DevName'],
                                     'Manage_IP_Addr': i['Manage_IP_Addr'],
                                     'Series_No': i['Series_No'],
                                     'CI_modelid': i['CI_modelid'],
                                     'MANUFACTURE_Factory': i['MANUFACTURE_Factory'],
                                     'OS_Version': i['OS_Version'],
                                     'OS_Bin': i['OS_Bin']})
                                if excel_flag:
                                    netdevice_final_excel.append({'Description': j['Description'],
                                                                  'DevName': j['DevName'],
                                                                  'Manage_IP_Addr': j['Manage_IP_Addr'],
                                                                  'Series_No': j['Series_No'],
                                                                  'CI_modelid': j['CI_modelid'],
                                                                  'MANUFACTURE_Factory': j[
                                                                      'MANUFACTURE_Factory'],
                                                                  'OS_Version': j['OS_Version'],
                                                                  'OS_Bin': j['OS_Bin'],
                                                                  'Status': 'O'})
                                    netdevice_final_excel.append({'Description': j['Description'],
                                                                  'DevName': i['DevName'],
                                                                  'Manage_IP_Addr': i['Manage_IP_Addr'],
                                                                  'Series_No': i['Series_No'],
                                                                  'CI_modelid': i['CI_modelid'],
                                                                  'MANUFACTURE_Factory': i[
                                                                      'MANUFACTURE_Factory'],
                                                                  'OS_Version': i['OS_Version'],
                                                                  'OS_Bin': i['OS_Bin'],
                                                                  'Status': 'U'})
                                update_netdevice_num += 1
                            break

                if import_temp is None:
                    add_netdevice_num += 1
                    netdevice_final.append(i)
                    if excel_flag:
                        netdevice_final_excel.append({'Description': i['Description'],
                                                      'DevName': i['DevName'],
                                                      'Manage_IP_Addr': i['Manage_IP_Addr'],
                                                      'Series_No': i['Series_No'],
                                                      'CI_modelid': i['CI_modelid'],
                                                      'MANUFACTURE_Factory': i[
                                                          'MANUFACTURE_Factory'],
                                                      'OS_Version': i['OS_Version'],
                                                      'OS_Bin': i['OS_Bin'],
                                                      'Status': 'A'})

            logger.info("需要更新%d条，新增%d条！", update_netdevice_num, add_netdevice_num)

            if excel_flag:
                excel(netdevice_final_excel, 'netdevice')
            if update_flag:
                if update_netdevice_num != 0 or add_netdevice_num != 0:
                    netdevice_dict = {"NetDevice": netdevice_final}
                    cmdbuild_api = CMDBuildAPI()
                    token = cmdbuild_api.get_token()
                    update_result = cmdbuild_api.put_update(token, json.dumps(netdevice_dict))
                    # print update_result.decode("UTF-8")
                    excel(netdevice_final, 'netdevice')
                    cost_time = cost(import_netdevice_time)
                    logger.info("更新数据成功! 耗时%d秒", cost_time)
                    logger.info("cmdbuild平台更新返回结果：%s", update_result)
                else:
                    cost_time = cost(import_netdevice_time)
                    logger.info("两边数据一致，无需更新! 耗时%d秒", cost_time)
        elif not netdevice_h3c:
            logger.info("H3C平台没有获取数据!")
        elif not netdevice_cmdb:
            logger.info("cmdbuild没有获取数据!")
    except Exception, e:
        logger.info("更新数据失败！原因:%s", e)


if __name__ == "__main__":
    cmdbuild_api = CMDBuildAPI()
    token = cmdbuild_api.get_token()
    if token:
        get_cmdbuild_netdevice()
        get_h3c_netdevice()
        import_netdevice()
