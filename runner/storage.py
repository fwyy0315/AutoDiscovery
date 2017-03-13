# -*- coding:UTF-8 -*-
import json
import datetime
import sys
from api.cmdbuild_api import CMDBuildAPI
from api.storage_api import mult_ssh2_storage
from action.finallogging import FinalLogger
from action.cost import cost
from action.excel import excel

reload(sys)
sys.setdefaultencoding("UTF-8")

excel_flag = True
update_flag = False

logger = FinalLogger.getLogger()
cmdbuild_api = CMDBuildAPI()

storage_fact = []
storage_lun_fact = []

Storage_cmdb = []
Storage_lun_cmdb = []

Storage_final = []
Storage_lun_final = []

Storage_excel = []
Storage_lun_excel = []


def get_cmdbuild_storage():
    get_cmdbuild_time = datetime.datetime.now()
    logger.info("cmdbuild平台Storage数据开始采集!")
    try:
        storage_cmdb_num = 0
        Storage = cmdbuild_api.get_class(token, 'Storage', cards=True)

        for i in json.loads(Storage)['data']:
            for k, v in i.items():
                if i[k] is None:
                    i[k] = u''
            Storage_cmdb.append({'Description': i['Description'],
                                 # 'Firmware': i['Firmware'],
                                 'DevName': i['DevName'],
                                 'Series_No': i['Series_No'],
                                 'Ctlr_Frequency': i['Ctlr_Frequency'],
                                 'MANUFACTURE_Factory': i['MANUFACTURE_Factory'],
                                 'CI_modelid': i['CI_modelid'],
                                 'IP': i['IP']})
            storage_cmdb_num += 1

        cost_time = cost(get_cmdbuild_time)
        logger.info("在cmdbuild系统上找到%d条storage数据", storage_cmdb_num)
        logger.info("cmdbuild平台Storage数据采集成功! 耗时%d秒", cost_time)
        return storage_cmdb_num
    except Exception, e:
        logger.error("cmdbuild平台Storage数据采集失败! 原因：%s", e)


def get_cmdbuild_storage_lun():
    get_cmdbuild_time = datetime.datetime.now()
    logger.info("cmdbuild平台lunmapping数据开始采集!")
    try:
        storage_lun_cmdb_num = 0
        Storage = cmdbuild_api.get_class(token, 'Storage_Lun_Mapping', cards=True)

        for i in json.loads(Storage)['data']:
            for k, v in i.items():
                if i[k] is None:
                    i[k] = u''
            Storage_lun_cmdb.append({'Description': i['Description'],
                                     'LUN_Name': i['LUN_Name'],
                                     'Lun_Size': i['Lun_Size'],
                                     'Storage_Name': i['Storage_Name']})
            storage_lun_cmdb_num += 1

        cost_time = cost(get_cmdbuild_time)
        logger.info("在cmdbuild系统上找到%d条lunmapping数据", storage_lun_cmdb_num)
        logger.info("cmdbuild平台lunmapping数据采集成功! 耗时%d秒", cost_time)
        return storage_lun_cmdb_num
    except Exception, e:
        logger.error("cmdbuild平台lunmapping数据采集失败! 原因：%s", e)


def import_storage(ips):
    storage_dict = mult_ssh2_storage(ips)
    for i in storage_dict:
        storage_fact.append(i['storage_fact'])
        storage_lun_fact.append(i['storage_lun_fact'])
    import_time = datetime.datetime.now()
    logger.info("Storage数据开始比较!")
    try:
        update_storage_num = 0
        add_storage_num = 0
        for i in storage_fact:
            storage_temp = None
            for j in Storage_cmdb:
                if i[0]['Series_No'] and j['Series_No']:
                    while i[0]['Series_No'].upper() == j['Series_No'].upper():
                        storage_temp = i[0]['Series_No']
                        if cmp(i[0], j) != 0:
                            Storage_final.append({'Description': j['Description'],
                                                  # 'Firmware': i['Firmware'],
                                                  'DevName': i[0]['DevName'],
                                                  'Series_No': i[0]['Series_No'],
                                                  'Ctlr_Frequency': i[0]['Ctlr_Frequency'],
                                                  'MANUFACTURE_Factory': i[0]['MANUFACTURE_Factory'],
                                                  'CI_modelid': i[0]['CI_modelid'],
                                                  'IP': i[0]['IP']})
                            j['status'] = 'O'
                            Storage_excel.append(j)
                            i[0]['status'] = 'A'
                            Storage_excel.append(i[0])
                            update_storage_num += 1
                        break

            if storage_temp is None:
                Storage_final.append(i[0])
                i[0]['status'] = 'A'
                Storage_excel.append(i[0])
                add_storage_num += 1

        logger.info("Storage数据比较结束！修改%d条，新增%d条", update_storage_num, add_storage_num)

        if update_flag:
            if update_storage_num != 0 or add_storage_num != 0:
                storage_dict = {"Storage": Storage_final}
                update_result = cmdbuild_api.put_update(token, json.dumps(storage_dict))
                cost_os_time = cost(import_time)
                logger.info("导入数据成功! 耗时%d秒", cost_os_time)
                logger.info("cmdbuild返回结果：" + update_result)
            else:
                cost_os_time = cost(import_time)
                logger.info("两边数据一致! 耗时%d秒", cost_os_time)

        if excel_flag:
            if Storage_excel:
                excel(Storage_excel, 'Storage')

    except Exception, e:
        logger.error("Storage数据比较失败，报错内容：%s", e)

    import_time = datetime.datetime.now()
    logger.info("Storage_Lun_Mapping数据开始比较!")
    try:
        update_storage_lun_num = 0
        add_storage_lun_num = 0
        for i in storage_lun_fact:
            for k in range(len(i)):
                storage_lun_temp = None
                for j in Storage_lun_cmdb:
                    if i[k]['Description'] and j['Description']:
                        while i[k]['Description'].upper() == j['Description'].upper():
                            storage_lun_temp = i[k]['Description']
                            if cmp(i[k], j) != 0:
                                Storage_lun_final.append({'Description': j['Description'],
                                                          'LUN_Name': i[k]['LUN_Name'],
                                                          'Lun_Size': i[k]['Lun_Size'],
                                                          'Storage_Name': i[k]['Storage_Name']})
                                j['status'] = 'O'
                                Storage_lun_excel.append(i[k])
                                i[k]['status'] = 'U'
                                Storage_lun_excel.append(i[k])
                                update_storage_lun_num += 1

                            break

                if storage_lun_temp is None:
                    Storage_lun_final.append(i[k])
                    i[k]['status'] = 'A'
                    Storage_lun_excel.append(i[k])
                    add_storage_lun_num += 1

        logger.info("Storage_Lun_Mapping数据比较结束！修改%d条，新增%d条", update_storage_lun_num, add_storage_lun_num)

        if update_flag:
            if update_storage_lun_num != 0 or add_storage_lun_num != 0:
                storage_lun_dict = {"Storage_Lun_Mapping": Storage_lun_final}
                # print storage_lun_dict
                update_result = cmdbuild_api.put_update(token, json.dumps(storage_lun_dict))
                cost_os_time = cost(import_time)
                logger.info("导入数据成功! 耗时%d秒", cost_os_time)
                logger.info("cmdbuild返回结果：" + update_result)
            else:
                cost_os_time = cost(import_time)
                logger.info("两边数据一致! 耗时%d秒", cost_os_time)
        if excel_flag:
            if Storage_lun_excel:
                excel(Storage_lun_excel, 'Storage_lun')

    except Exception, e:
        logger.error("Storage_Lun_Mapping数据比较失败，报错内容：%s", e)


if __name__ == '__main__':
    token = cmdbuild_api.get_token()
    if token:
        if get_cmdbuild_storage() > 0 and get_cmdbuild_storage_lun() > 0:
            ips = ['200.31.129.7', '200.31.129.8']
            import_storage(ips)
    else:
        logger.error("获取token失败，请检查cmdbuild系统接口")
