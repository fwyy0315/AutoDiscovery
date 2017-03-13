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
username = cf.get('firberswitch', 'username')
password = cf.get('firberswitch', 'password')


def ssh2_fiberswitch(ip):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        fiberswitch_fact = {}

        fiberswitch_port_fact_info = []
        ssh.connect(ip, 22, username, password, timeout=5)

        try:
            rc_cmd, out_cmd, err_cmd = ssh.exec_command('chassisshow', timeout=5)
            out = out_cmd.readlines()
        except Exception, e:
            logger.error('chassisshow 执行失败:%s', e)
            out = []
        if out:
            for i in out:
                if i.__contains__('Chassis Factory Serial Num:'):
                    fiberswitch_fact['Series_No'] = i.split()[-1]

        try:
            rc_cmd, out_cmd, err_cmd = ssh.exec_command('switchshow', timeout=5)
            out = out_cmd.readlines()
        except Exception, e:
            logger.error('switchshow 执行失败:%s', e)
            out = []

        if out:
            for i in out:
                if i.__contains__('switchName'):
                    fiberswitch_fact['DevName'] = i.split(':')[1].split()[-1]
                elif i.__contains__('switchWwn'):
                    fiberswitch_fact['WWNN'] = i.split()[-1]

            for i in out:
                while i.__contains__('='):
                    port_total_num = out.index(i) - 1
                    break
            if out[port_total_num].__contains__('Slot'):
                slot_index = out[port_total_num].split().index('Slot')
            if out[port_total_num].__contains__('Port'):
                port_index = out[port_total_num].split().index('Port')
            if out[port_total_num].__contains__('Speed'):
                speed_index = out[port_total_num].split().index('Speed')
            if out[port_total_num].__contains__('State'):
                state_index = out[port_total_num].split().index('State')
            if out[port_total_num].__contains__('Index'):
                index_index = out[port_total_num].split().index('Index')

            ports_used_num = 0
            ports_enabled_num = 0
            total_ports_num = 0
            fiberswitch_fact['Speed_Support'] = 'N0'

            # 判断是否有槽位号
            if out[port_total_num].__contains__('Slot'):
                for i in out[port_total_num + 2:]:
                    fiberswitch_port_fact = {}
                    port_temp = i.split()
                    fiberswitch_port_fact['Slot'] = port_temp[slot_index]
                    fiberswitch_port_fact['Port'] = port_temp[port_index]
                    fiberswitch_port_fact['Speed'] = port_temp[speed_index]
                    if [int(s) for s in fiberswitch_port_fact['Speed'] if s.isdigit()] > \
                            [int(s) for s in fiberswitch_fact['Speed_Support'] if s.isdigit()]:
                        fiberswitch_fact['Speed_Support'] = fiberswitch_port_fact['Speed']
                    fiberswitch_port_fact['FC_Switch_Port_State'] = port_temp[state_index]
                    fiberswitch_port_fact['Domain_Index'] = port_temp[index_index]
                    if port_temp[state_index] == 'Online':
                        if i.__contains__('F-Port'):
                            f_port_index = port_temp.index('F-Port')
                            fiberswitch_port_fact['Host_HBA_WWPN'] = port_temp[f_port_index + 1]
                            total_ports_num += 1
                            ports_used_num += 1
                        elif i.__contains__('E-Port'):
                            e_port_index = port_temp.index('E-Port')
                            if port_temp[e_port_index + 1].__contains__(':'):
                                fiberswitch_port_fact['Host_HBA_WWPN'] = port_temp[e_port_index + 1]
                            else:
                                fiberswitch_port_fact['Host_HBA_WWPN'] = u''
                            total_ports_num += 1
                            ports_used_num += 1
                    else:
                        fiberswitch_port_fact['Host_HBA_WWPN'] = u''
                        total_ports_num += 1
                        ports_enabled_num += 1
                    fiberswitch_port_fact['Description'] = unicode(
                        fiberswitch_fact['DevName'] + '_' + fiberswitch_port_fact['Slot'] + '_' + fiberswitch_port_fact[
                            'Port'])
                    fiberswitch_port_fact['FCSwitch_Name'] = unicode(
                        fiberswitch_fact['DevName'] + '_' + fiberswitch_fact['Series_No'])
                    # print fiberswitch_port_fact
                    fiberswitch_port_fact_info.append(fiberswitch_port_fact)
            else:
                for i in out[port_total_num:]:
                    fiberswitch_port_fact = {}
                    port_temp = i.split()
                    fiberswitch_port_fact['Port'] = port_temp[port_index]
                    fiberswitch_port_fact['Speed'] = port_temp[speed_index]
                    if [int(s) for s in fiberswitch_port_fact['Speed'] if s.isdigit()] > \
                            [int(s) for s in fiberswitch_fact['Speed_Support'] if s.isdigit()]:
                        fiberswitch_fact['Speed_Support'] = fiberswitch_port_fact['Speed']
                    fiberswitch_port_fact['FC_Switch_Port_State'] = port_temp[state_index]
                    fiberswitch_port_fact['Domain_Index'] = port_temp[port_index]
                    if port_temp[state_index] == 'Online':
                        if i.__contains__('F-Port'):
                            f_port_index = port_temp.index('F-Port')
                            fiberswitch_port_fact['Host_HBA_WWPN'] = port_temp[f_port_index + 1]
                            total_ports_num += 1
                            ports_used_num += 1
                        elif i.__contains__('E-Port'):
                            e_port_index = port_temp.index('E-Port')
                            fiberswitch_port_fact['Host_HBA_WWPN'] = port_temp[e_port_index + 1]
                            total_ports_num += 1
                            ports_used_num += 1
                    else:
                        fiberswitch_port_fact['Host_HBA_WWPN'] = u''
                        total_ports_num += 1
                        ports_enabled_num += 1
                    fiberswitch_port_fact['Description'] = unicode(
                        fiberswitch_fact['DevName'] + '_' + fiberswitch_port_fact['Port'])
                    fiberswitch_port_fact['FCSwitch_Name'] = unicode(
                        fiberswitch_fact['DevName'] + '_' + fiberswitch_fact['Series_No'])
                    fiberswitch_port_fact_info.append(fiberswitch_port_fact)
                    # print fiberswitch_port_fact
            # print fiberswitch_port_fact_info
            fiberswitch_fact['Description'] = unicode(
                fiberswitch_fact['DevName'] + '_' + fiberswitch_fact['Series_No'])
            fiberswitch_fact['Total_Ports'] = total_ports_num
            fiberswitch_fact['Ports_Enabled'] = ports_enabled_num
            fiberswitch_fact['Ports_Used'] = ports_used_num

            try:
                rc_cmd, out_cmd, err_cmd = ssh.exec_command('firmwareshow', timeout=5)
                out = out_cmd.readlines()
            except Exception, e:
                logger.error('firmwareshow 执行失败:%s', e)
                out = []
            if out:
                if out[0].__contains__('Appl'):
                    Appl_index = out[0].split().index('Appl')
                for i in out:
                    if out[0].__contains__('Status'):
                        if i.__contains__('FOS') and i.__contains__('ACTIVE'):
                            fiberswitch_fact['Fabric_OS'] = i.split()[Appl_index + 1]
                    else:
                        if i.__contains__('FOS'):
                            fiberswitch_fact['Fabric_OS'] = i.split()[Appl_index + 1]

            fiberswitch_fact['IP'] = ip
            print fiberswitch_fact
            fiberswitch_dict = {'firberswitch_fact': fiberswitch_fact,
                                'firberswitch_port_fact': fiberswitch_port_fact_info}
            return fiberswitch_dict
    except Exception, e:
        logger.error('%s\tError:%s' % (ip, e))


def mult_ssh2_fiberswitch(ips, processes=8):
    pool = multiprocessing.Pool(processes=processes)
    return pool.map(ssh2_fiberswitch, ips)
