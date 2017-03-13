# -*- coding:UTF-8 -*-
import json
import datetime
import sys
import ConfigParser
import paramiko
from api.cmdbuild_api import CMDBuildAPI
from action.finallogging import FinalLogger
from action.cost import cost
from action.excel import excel

reload(sys)
sys.setdefaultencoding("UTF-8")
logger = FinalLogger.getLogger()

cf = ConfigParser.ConfigParser()
excel_flag = False
update_flag = False
username = 'taddm'
password = 'taddm'
ip = '200.31.44.115'
command = 'cat /home/rmb/app/Component/ComponentRelease/Config/TProcess.cfg'

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


# 获取本币进程配置文件
def read_cfg(ip):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ip, 22, username, password, timeout=30)
        out = []
        find_command = '/usr/bin/find /home/rmb/app/Component/ComponentRelease/Config/TProcess.cfg -type f -mtime -1 |wc -l'
        try:
            find_cmd, find_cmd, find_err = ssh.exec_command(find_command, get_pty=True, timeout=30)
            config_num = int(find_cmd.readline().strip('\n').strip())
        except Exception, e:
            config_num = 0
            logger.error('%s\t执行%s命令超时:%s' % (ip, find_command, e))
        if config_num > 0:
            try:
                rc_cmd, out_cmd, err_cmd = ssh.exec_command(command, get_pty=True, timeout=30)
                lines = out_cmd.readlines()
            except Exception, e:
                lines = []
                logger.error('%s\t执行%s命令超时:%s' % (ip, command, e))
            finally:
                ssh.close()
            if lines is not None:
                TProcessList = []
                lineNum = 0
                while lineNum < len(lines):
                    thisLine = lines[lineNum]
                    if thisLine:
                        if thisLine[0] == '{':  # 默认"{"标志一个进程开始
                            TProcess = lastLine  # 默认"{"的上一个非空行是进程名
                            locals()[TProcess] = {'DisplayName': lastLine}
                            locals()[TProcess]['Description'] = locals()[TProcess]['DisplayName']
                            lineNum += 1
                            nextLine = lines[lineNum]
                            while not lines[lineNum]:
                                lineNum += 1
                            while lines[lineNum][0] != '}':
                                nextLine = lines[lineNum].strip('\n').strip('\r')
                                if nextLine != '':
                                    k, v = nextLine.split('=', 1)  # 默认第一个"="分隔属性名和值
                                    if k in ['LMNAME', 'PRTYPE']:  # 默认LMNAME, PRTYPE标识
                                        locals()[TProcess][k] = v
                                lineNum += 1
                                while not lines[lineNum]:
                                    lineNum += 1
                            TProcessList.append(locals()[TProcess])
                        lastLine = thisLine.strip('\n')
                    lineNum += 1
                # if excel_flag:
                #     excel(TProcessList, "process_read")
                return TProcessList
            else:
                return False
        else:
            logger.info('%s\t配置文件未更新' % ip)
            return False
    except Exception, e:
        logger.error('%s\t无法连接：%s' % (ip, e))
        return False


def get_cmdbuild_TProcess():
    TProcess_cmdb_list = []
    TProcess_cmdb_num = 0
    logger.info("cmdbuild本币进程数据开始采集!")
    get_cmdbuild_time = datetime.datetime.now()
    try:
        TProcess = cmdbuild_api.get_class(token, 'RuntimeProcess', cards=True)
        for i in json.loads(TProcess)['data']:
            for k, v in i.items():
                if i[k] is None:
                    i[k] = u''
            TProcess_cmdb_list.append({'Description': i['Description'],
                                       'DisplayName': i['DisplayName']})
            TProcess_cmdb_num += 1
        cost_time = cost(get_cmdbuild_time)
        logger.info("cmdbuild本币进程数据采集成功! 共%d条，耗时%d秒", TProcess_cmdb_num, cost_time)
    except Exception, e:
        logger.error("cmdbuild本币进程数据采集失败! 原因：%s", e)
    # if excel_flag:
    #     excel(TProcess_cmdb_list, "process_cmdb_read")
    return TProcess_cmdb_list


def import_TProcess(TProcessList, TProcess_cmdb_list):
    TProcess_final = []
    TProcess_final_excel = []
    update_TProcess_num = 0
    add_TProcess_num = 0
    logger.info("本币进程数据开始比较!")
    import_time = datetime.datetime.now()
    try:
        for i in TProcessList:
            if i['PRTYPE'] != '12':
                import_temp = None
                for j in TProcess_cmdb_list:
                    if i['DisplayName'].strip().upper() == j['DisplayName'].strip().upper():  # 去掉CMDB中进程名的回车、空格等
                        import_temp = j['Description']
                        if i['DisplayName'] != j['DisplayName']:
                            TProcess_final.append({'Description': j['Description'],
                                                   'DisplayName': i['DisplayName']})
                            if excel_flag:
                                TProcess_final_excel.append({'Description': j['Description'],
                                                             'DisplayName': j['DisplayName'],
                                                             'PRTYPE': i['PRTYPE'],
                                                             'Status': 'O'})
                                TProcess_final_excel.append({'Description': j['Description'],
                                                             'DisplayName': i['DisplayName'],
                                                             'PRTYPE': i['PRTYPE'],
                                                             'Status': 'U'})
                            update_TProcess_num += 1
                            break

                if import_temp is None:
                    add_TProcess_num += 1
                    TProcess_final.append({'Description': i['Description'],
                                           'DisplayName': i['DisplayName']})
                    if excel_flag:
                        TProcess_final_excel.append({'Description': i['Description'],
                                                     'DisplayName': i['DisplayName'],
                                                     'PRTYPE': i['PRTYPE'],
                                                     'Status': 'A'})
        logger.info("需要更新%d条，新增%d条！", update_TProcess_num, add_TProcess_num)

        if excel_flag:
            excel(TProcess_final_excel, 'TProcess_final')
        if update_flag:
            if update_TProcess_num != 0 or add_TProcess_num != 0:
                TProcess_dict = {"RuntimeProcess": TProcess_final}
                update_result = cmdbuild_api.put_update(token, json.dumps(TProcess_dict))
                cost_time = cost(import_time)
                logger.info("更新数据成功! 耗时%d秒", cost_time)
                logger.info("cmdbuild平台更新返回结果：%s", update_result)
            else:
                cost_time = cost(import_time)
                logger.info("两边数据一致，无需更新! 耗时%d秒", cost_time)
    except Exception, e:
        logger.info("更新数据失败！原因:%s", e)


def read_bb_ip(confPath):
    cf = ConfigParser.ConfigParser()
    cf.read(confPath)
    bb_ip_list = []
    for i in cf.sections():
        bb_ip = {}
        for j in cf.options(i):
            bb_ip[j.upper()] = cf.get(i, j)
        bb_ip_list.append(bb_ip)
    # if excel_flag:
    #     excel(bb_ip_list, "bb_ip_read")
    return bb_ip_list


def get_process_ip(TProcessList, bb_ip_list):
    process_ip_list = []
    for i in TProcessList:
        if i['PRTYPE'] != '12':
            for j in bb_ip_list:
                if i['LMNAME'] == j['LMNAME']:
                    for ip in j.values():
                        if ip != j['LMNAME']:
                            process_ip_list.append({'Description': i['Description'],
                                                    'DisplayName': i['DisplayName'],
                                                    'IP': ip})
                    break
    # if excel_flag:
    #     excel(process_ip_list, "process_ip_read")
    return process_ip_list


def get_cmdbuild_process_ip(TProcess_cmdb_list):
    process_ip_cmdb = {}
    process_ip_cmdb_num = 0
    logger.info("cmdbuild本币进程与ip关系数据开始采集!")
    get_cmdbuild_time = datetime.datetime.now()
    try:
        process_ip_relation = json.loads(cmdbuild_api.get_domain(token, 'Process_RunsOn_IP'))['data']
        for i in process_ip_relation:
            for k, v in i.items():
                if k == '_destinationDescription':
                    Description = i[k]
                    for j in TProcess_cmdb_list:
                        if Description == j['Description']:
                            DisplayName = j['DisplayName']
                            break
                if k == '_sourceDescription':
                    ip = i[k]
            try:
                process_ip_cmdb[Description]
            except KeyError:
                process_ip_cmdb[Description] = {}
                process_ip_cmdb[Description]['Description'] = Description
                process_ip_cmdb[Description]['DisplayName'] = DisplayName
                process_ip_cmdb[Description]['ips'] = []
            process_ip_cmdb[Description]['ips'].append(ip)
            process_ip_cmdb_num += 1
        cost_time = cost(get_cmdbuild_time)
        logger.info("cmdbuild本币进程和ip关系采集成功! 共%d条，耗时%d秒", process_ip_cmdb_num, cost_time)
    except Exception, e:
        logger.error("cmdbuild平台本币进程和ip关系采集失败! 原因：%s", e)
    process_ip_cmdb_list = process_ip_cmdb.values()
    # if excel_flag:
    # excel(process_ip_cmdb_list, "process_ip_cmdb_read")
    return process_ip_cmdb_list


def import_process_ip(process_ip_list, process_ip_cmdb_list):
    process_ip_final = []
    process_ip_final_excel = []
    update_process_ip_num = 0
    add_process_ip_num = 0
    logger.info("进程和IP关系数据开始更新!")
    import_time = datetime.datetime.now()
    try:
        for i in process_ip_list:
            import_temp = None
            for j in process_ip_cmdb_list:
                if i['DisplayName'].strip().upper() == j['DisplayName'].strip('*').upper():  # 去掉CMDB中进程名的回车、空格等
                    import_temp = i['DisplayName']
                    if i['IP'] not in j['ips']:
                        process_ip_final.append({'进程': j['Description'],
                                                 'IP地址': i['IP']})
                        if excel_flag:
                            process_ip_final_excel.append({'进程': j['Description'],
                                                           'IP地址': i['IP'],
                                                           'Status': 'U'})
                        update_process_ip_num += 1
                    break
            if import_temp is None:
                process_ip_final.append({'进程': i['Description'],
                                         'IP地址': i['IP']})
                if excel_flag:
                    process_ip_final_excel.append({'进程': i['Description'],
                                                   'IP地址': i['IP'],
                                                   'Status': 'A'})
                add_process_ip_num += 1
        logger.info("需要更新%d条，新增%d条！", update_process_ip_num, add_process_ip_num)

        if excel_flag:
            excel(process_ip_final_excel, 'process_ip_final')
        if update_flag:
            if add_process_ip_num != 0:
                process_ip_dict = {"Process_RunsOn_IP": process_ip_final}
                update_result = cmdbuild_api.post_relation(token, json.dumps(process_ip_dict))
                cost_os_time = cost(import_time)
                logger.info("更新数据成功! 耗时%d秒", cost_os_time)
                logger.info("cmdbuild返回结果：" + update_result)
            else:
                cost_os_time = cost(import_time)
                logger.info("两边数据一致，无需更新! 耗时%d秒", cost_os_time)
    except Exception, e:
        logger.info("更新数据失败！原因:%s", e)


if __name__ == "__main__":
    cmdbuild_api = CMDBuildAPI()
    token = cmdbuild_api.get_token()
    if token:
        if read_cfg(ip):
            TProcessList = read_cfg(ip)
            TProcess_cmdb_list = get_cmdbuild_TProcess()
            import_TProcess(TProcessList, TProcess_cmdb_list)
            bb_ip_list = read_bb_ip("../conf/bb_ip.conf")
            process_ip_list = get_process_ip(TProcessList, bb_ip_list)
            process_ip_cmdb_list = get_cmdbuild_process_ip(TProcess_cmdb_list)
            import_process_ip(process_ip_list, process_ip_cmdb_list)
