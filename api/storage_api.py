# -*- coding:utf-8 -*-
import sys
import paramiko
import multiprocessing
import ConfigParser
from action.finallogging import FinalLogger

reload(sys)
sys.setdefaultencoding("UTF-8")

logger = FinalLogger.getLogger()

cf = ConfigParser.ConfigParser()
cf.read("../conf/base.conf")
username = cf.get('storage', 'username')
password = cf.get('storage', 'password')


def ssh2_storage(ip):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        storage_fact = []
        storage_lun_fact = []
        storage_info = {}
        ssh.connect(ip, 22, username, password, timeout=5)
        try:
            rc_cmd, out_cmd, err_cmd = ssh.exec_command('sysconfig -a', timeout=5)
            out = out_cmd.readlines()
        except Exception, e:
            logger.error('sysconfig -a 执行失败:%s', e)
            out = []
        ssh.close()
        if out:
            storage_info['MANUFACTURE_Factory'] = out[0].split()[0]
            if storage_info['MANUFACTURE_Factory'] == 'NetApp':
                for i in out:
                    if i.__contains__('System Serial Number:'):
                        storage_info['DevName'] = i.split()[-1].strip('(').strip(')').strip()
                        storage_info['Series_No'] = i.split()[-2].strip()
                    elif i.__contains__('Model Name:'):
                        storage_info['CI_modelid'] = i.split()[-1]
                    elif i.__contains__('Processor type:'):
                        if i.split()[-1].__contains__('GHz'):
                            storage_info['Ctlr_Frequency'] = unicode(str(int(float(i.split()[-1].strip('GHz')) * 1000)))
                        elif i.split()[-1].__contains__('MHz'):
                            storage_info['Ctlr_Frequency'] = unicode(str(int(float(i.split()[-1].strip('MHz')))))
                            # while i.__contains__('Firmware Version:'):
                            #     storage_info['Firmware'] = i.split()[-1]
                            #     break
                storage_info['IP'] = unicode(ip)
                storage_info['Description'] = storage_info['DevName'] + '_' + storage_info['Series_No']

                storage_fact.append(storage_info)

        ssh.connect(ip, 22, username, password, timeout=5)
        try:
            rc_cmd, out_cmd, err_cmd = ssh.exec_command('lun show', timeout=5)
            out = out_cmd.readlines()
        except Exception, e:
            logger.error('lun show 执行失败:%s', e)
            out = []
        ssh.close()
        if out:
            for i in out:
                lun_temp = i.split()
                storage_lun_info = {'Description': lun_temp[0] + '_' + storage_info['DevName'],
                                    'LUN_Name': lun_temp[0],
                                    'Lun_Size': lun_temp[1],
                                    'Storage_Name': storage_info['Description']}
                storage_lun_fact.append(storage_lun_info)

        storage_dict = {'storage_fact': storage_fact, 'storage_lun_fact': storage_lun_fact}
        return storage_dict
    except Exception, e:
        logger.error('%s\tError:%s' % (ip, e))


def mult_ssh2_storage(ips, processes=8):
    pool = multiprocessing.Pool(processes=processes)
    return pool.map(ssh2_storage, ips)
