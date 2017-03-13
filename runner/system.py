# -*- coding:UTF-8 -*-
import json
import sys
import socket
import ConfigParser
import datetime
import api.ssh_api

from action.finallogging import FinalLogger
from IPy import IP
from api.ansible_api import ansible_adhoc
from api.cmdbuild_api import CMDBuildAPI
from action.cost import cost
from action.excel import excel
from action.repeat import repeat

reload(sys)
sys.setdefaultencoding("UTF-8")

logger = FinalLogger.getLogger()
cmdbuild_api = CMDBuildAPI()

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
            excel_flag = bool(False)
    else:
        excel_flag = bool(False)
    # 获取update_flag
    if cf.get('flag', 'update_flag'):
        if cf.get('flag', 'update_flag').__contains__('True'):
            update_flag = bool(cf.get('flag', 'update_flag'))
        else:
            update_flag = bool(False)
    else:
        update_flag = bool(False)
except Exception, e:
    print e

os_fact = []
host_fact = []
host_os_fact = []
host_ip_fact = []
server_fact = []
server_host_fact = []

os_cmdb = []
host_cmdb = []
ip_cmdb = []
server_cmdb = []
host_ip_cmdb = []
host_os_cmdb = []
host_server_cmdb = []
ip_segment_cmdb = []

os_final = []
host_final = []
server_final = []
server_host_final = []
host_os_del_final = []
host_os_add_final = []
host_ip_final = []
ip_final = []

os_excel = []
host_excel = []
server_excel = []
host_os_excel = []
server_host_excel = []


def ansible_facts(value):
    ansible_num = 0
    if value:
        for i in value:
            for k, v in i.items():
                if v.__contains__('unreachable'):
                    if v['msg'] == u'Authentication failure.':
                        logger.error(k + ' 密码错误，请确认！')
                    elif v['msg'] == u'Failed to connect to the host via ssh.':
                        logger.error(k + ' 无法连接，请确认！')
                elif v.__contains__('failed'):
                    if v['msg'].__contains__('No space left on device'):
                        logger.error(k + ' /home目录空间不足，请检查！')
                    elif v['msg'].__contains__('failed to resolve remote temporary'):
                        logger.error(k + ' 响应超时，请检查')
                    elif v[
                        'msg'] == u'Error: ansible requires the stdlib json or simplejson module, neither was found!':
                        other_ips.append(k)
                    elif v['msg'].__contains__('MODULE FAILURE'):
                        other_ips.append(k)
                    elif v['msg'].__contains__('Unexpected failure during module execution.'):
                        other_ips.append(k)
                    else:
                        other_ips.append(k)
                elif v.__contains__('ansible_facts'):
                    ansible_temp = v['ansible_facts']
                    ansible_num += 1
                    if ansible_temp:
                        # 数据字典
                        '''
                        ==============================================================
                        ['ansible_facts']['ansible_hostname']  # Host名
                        ['ansible_userspace_bits']  # 系统位数
                        ['ansible_bios_version']  # bios 版本
                        ['ansible_processor_vcpus']  # 虚拟CPU核心数量
                        ['ansible_processor_cores']  # 物理CPU核心数量
                        ['ansible_processor'][1].split('@')[0]  # cpu型号
                        ['ansible_processor'][1].split('@')[1].strip()  # 主频
                        ['ansible_default_ipv4']['macaddress']  # mac地址
                        ['ansible_default_ipv4']['network']  # 网段
                        ['ansible_default_ipv4']['address']  # IP地址
                        ['ansible_distribution']  # 系统系列
                        ['ansible_memtotal_mb']  # 内存
                        ['ansible_product_name']  # 产品型号
                        ['ansible_lsb']['release']  # OS 发型版本
                        ['ansible_lsb']['description']  # OS详细名称
                        ['ansible_kernel']  # 内核版本
                        ['ansible_bios_date']  # os_bois日期
                        ['ansible_processor_threads_per_core'] # 线程
                        ['ansible_interfaces'] 网络接口
                        ===============================================================
                        '''
                        if ansible_temp.__contains__('ansible_lsb'):
                            if ansible_temp['ansible_system'] == u'Linux':
                                if ansible_temp['ansible_lsb']['description'].__contains__('SUSE'):
                                    ansible_temp['ansible_lsb']['description'] = ansible_temp['ansible_lsb'][
                                        'description'].strip(' (x86_64)')

                                os_fact.append(
                                    {'Description': str(ansible_temp['ansible_lsb']['description']) + ' ' + str(
                                        ansible_temp['ansible_userspace_bits']) + 'bit',
                                     'OSNAME': ansible_temp['ansible_system']})

                                host_os_fact.append({'Host': ansible_temp['ansible_hostname'],
                                                     'OS': str(ansible_temp['ansible_lsb']['description']) + ' ' + str(
                                                         ansible_temp['ansible_userspace_bits']) + 'bit'})
                            host_fact_info = {'Description': ansible_temp['ansible_hostname'],
                                              'Mem_Size': unicode(ansible_temp['ansible_memtotal_mb']),
                                              'Keneral_Version': ansible_temp['ansible_kernel']
                                              }
                            # todo:虚拟机内存分配存在损耗,以兆为单位计算，每24.7G会存在1G的误差
                            if int(ansible_temp['ansible_memtotal_mb']) % 1024 == 0:
                                host_fact_info['Mem_Size'] = str(int(ansible_temp['ansible_memtotal_mb']) / 1024) + 'GB'
                            else:
                                host_fact_info['Mem_Size'] = str(
                                    int(ansible_temp['ansible_memtotal_mb']) / 1024 + 1) + 'GB'

                            if ansible_temp['ansible_interfaces']:
                                net_num = 0
                                for interface in ansible_temp['ansible_interfaces']:
                                    if interface.__contains__('em'):
                                        net_num += 1
                                else:
                                    if interface.__contains__('eth'):
                                        net_num += 1
                            host_fact_info['NET_Num'] = unicode(str(net_num))

                            if str(ansible_temp['ansible_product_name']).__contains__('VMware'):
                                host_fact_info['H_Type'] = '虚拟机'.decode('UTF-8')
                                # 虚拟机虚拟核数
                                host_fact_info['CPU_Num'] = unicode(ansible_temp['ansible_processor_vcpus'])
                                # 虚拟机光纤口，默认为0
                                host_fact_info['HBA_Num'] = u'0'
                                # 虚拟机CMT，默认为1
                                host_fact_info['CMT'] = u'1'
                            else:
                                host_fact_info['H_Type'] = '物理机'.decode('UTF-8')
                                # 物理机CMT
                                host_fact_info['CMT'] = unicode(str(ansible_temp['ansible_processor_threads_per_core']))
                                # 物理机物理核数
                                host_fact_info['CPU_Num'] = unicode(str(int(ansible_temp['ansible_processor_vcpus']) /
                                                                        int(ansible_temp[
                                                                                'ansible_processor_threads_per_core'])))
                                try:
                                    server_info = api.ssh_api.ssh2_sudo(ansible_temp['ansible_default_ipv4']['address'])
                                except Exception, e:
                                    logger.info(
                                        "%s\t执行sudo_ssh失败:%s" % (ansible_temp['ansible_default_ipv4']['address'], e))

                                try:
                                    if server_info:
                                        # 物理机光纤口
                                        host_fact_info['HBA_Num'] = unicode(
                                            str(server_info['HBA_Num'].strip('\n').strip('\r')))
                                        # CPU 频率以GHz为单位
                                        if ansible_temp['ansible_processor'][1].split('@')[1].__contains__('GHz'):
                                            frequency = ansible_temp['ansible_processor'][1].split('@')[1].lstrip()
                                        elif ansible_temp['ansible_processor'][1].split('@')[1].__contains__('MHz'):
                                            frequency = str('%.2f' % (
                                                float(ansible_temp['ansible_processor'][1].split('@')[1].lstrip().strip(
                                                    'MHz')) / 1000)) + 'GHz'
                                        elif ansible_temp['ansible_processor'][1].split('@')[1].__contains__('KHz'):
                                            frequency = str('%.2f' % (
                                                float(ansible_temp['ansible_processor'][1].split('@')[1].lstrip().strip(
                                                    'KHz')) / 1000 / 1000)) + 'GHz'
                                        # 物理机
                                        if not str(server_info['Series_No']).__contains__('Vmware'):
                                            server_fact.append({'Series_No': server_info['Series_No'],
                                                                'MANUFACTURE_Factory': server_info[
                                                                    'MANUFACTURE_Factory'],
                                                                'CI_modelid': server_info['CI_modelid'],
                                                                'FirmWare': server_info['FirmWare'],
                                                                'CPU_Type': unicode(' '.join(
                                                                    ansible_temp['ansible_processor'][1].split('@')[
                                                                        0].split())),
                                                                'CPU_Frequency': unicode(str(frequency)),
                                                                'CPU_Num': ansible_temp['ansible_processor_count'],
                                                                'CPU_Core_Num': int(
                                                                    ansible_temp['ansible_processor_count']) * int(
                                                                    ansible_temp['ansible_processor_cores'])
                                                                })
                                            # Server和Host关系
                                            if server_info['Series_No'] is not None:
                                                server_host_fact.append({'Series_No': server_info['Series_No'],
                                                                         'Host': ansible_temp['ansible_hostname']})

                                            if len(ansible_temp['ansible_all_ipv4_addresses']) > 1:
                                                for i in ansible_temp['ansible_all_ipv4_addresses']:
                                                    host_ip_fact.append({'Host': ansible_temp['ansible_hostname'],
                                                                         'System_Net_Config': i})
                                            else:
                                                host_ip_fact.append({'Host': ansible_temp['ansible_hostname'],
                                                                     'System_Net_Config':
                                                                         ansible_temp['ansible_all_ipv4_addresses'][0]})

                                except Exception, e:
                                    logger.info(
                                        '%s主机采集Server和IP信息异常:%s' % (ansible_temp['ansible_default_ipv4']['address'], e))
                        # todo: 部分solaris机器可以使用ansible发现
                        elif ansible_temp['ansible_system'] == u'SunOS':
                            other_ips.append(str(ansible_temp['ansible_default_ipv4']['address']))
                        host_fact.append(host_fact_info)
        logger.info("ansible成功获取了%d台主机信息" % ansible_num)


def ssh_facts(value):
    # ansible失败的的IP再次处理
    try:
        other_fact = api.ssh_api.mult(value)
    except Exception, e:
        logger.info("执行ssh_api失败:%s" % e)

    other_fact_num = 0
    if other_fact:
        for j in other_fact:
            if j:
                other_fact_num += 1
                try:
                    # 操作系统类型，发行版本,内核版本、位数
                    os_ansible_info = {'Description': j['OS'],
                                       'OSNAME': j['OSNAME']
                                       # 'RelaeseVersion': j['OS'],
                                       # 'Bit': j['Bit']
                                       }
                    os_fact.append(os_ansible_info)
                except Exception, e:
                    logger.info('%s主机采集OS信息异常:%s' % (j['Description'], e))

                try:
                    # 主机名，主机类型，操作系统，CPU核数, 内存, 操作系统类型、线程数、IP
                    host_fact.append({'Description': j['Description'],
                                      'CPU_Num': j['CPU_Num'],
                                      'Mem_Size': j['Mem_Size'],
                                      'CMT': j['CMT'],
                                      'H_Type': j['H_Type'],
                                      'Keneral_Version': j['Keneral_Version'],
                                      'NET_Num': j['NET_Num'],
                                      'HBA_Num': j['HBA_Num']
                                      })

                    host_os_fact.append({'Host': j['Description'],
                                         'OS': j['OS']})
                except Exception, e:
                    logger.info('%s主机采集Host信息异常:%s' % (j['Description'], e))

                try:
                    if len(j['System_Net_Config']) > 1:
                        for k in j['System_Net_Config']:
                            host_ip_fact.append({'Host': j['Description'],
                                                 'System_Net_Config': k.strip('\n')})
                    else:
                        host_ip_fact.append({'Host': j['Description'],
                                             'System_Net_Config': j['System_Net_Config'][0].strip('\n')})
                except Exception, e:
                    logger.info('%s主机采集IP信息异常:%s' % (j['Description'], e))

                try:
                    if j['H_Type'] == '物理机'.decode('UTF-8'):
                        if j['OSNAME'] == u'Solaris':
                            if j['CI_modelid'].__contains__('T'):
                                if j['Series_No']:
                                    server_fact.append({'Series_No': j['Series_No'],
                                                        'MANUFACTURE_Factory': j['MANUFACTURE_Factory'],
                                                        'CI_modelid': j['CI_modelid'],
                                                        'FirmWare': j['FirmWare'],
                                                        'CPU_Type': j['CPU_Type'],
                                                        'CPU_Frequency': j['CPU_Frequency'],
                                                        'CPU_Num': j['CPU_Phy_Num'],
                                                        'CPU_Core_Num': j['CPU_Core_Num']})
                                    if j['Series_Host']:
                                        # 判断是否是数组
                                        if isinstance(j['Series_Host'], list):
                                            for k in j['Series_Host']:
                                                server_host_fact.append({'Series_No': j['Series_No'],
                                                                         'Host': k})
                                        else:
                                            server_host_fact.append({'Series_No': j['Series_No'],
                                                                     'Host': j['Series_Host']})
                        elif j['OSNAME'] == u'AIX':
                            if j['Series_No']:
                                server_fact.append({'Series_No': j['Series_No'],
                                                    'MANUFACTURE_Factory': j['MANUFACTURE_Factory'],
                                                    'CI_modelid': j['CI_modelid'],
                                                    'FirmWare': j['FirmWare'],
                                                    'CPU_Type': j['CPU_Type'],
                                                    'CPU_Frequency': j['CPU_Frequency']})
                                server_host_fact.append({'Series_No': j['Series_No'],
                                                         'Host': j['Description']})
                        elif j['OSNAME'] == u'Linux':
                            if j['Series_No']:
                                server_fact.append({'Series_No': j['Series_No'],
                                                    'MANUFACTURE_Factory': j['MANUFACTURE_Factory'],
                                                    'CI_modelid': j['CI_modelid'],
                                                    'FirmWare': j['FirmWare'],
                                                    'CPU_Type': j['CPU_Type'],
                                                    'CPU_Frequency': j['CPU_Frequency'],
                                                    'CPU_Num': j['CPU_Phy_Num'],
                                                    'CPU_Core_Num': j['CPU_Core_Num']})
                                server_host_fact.append({'Series_No': j['Series_No'],
                                                         'Host': j['Description']})
                except Exception, e:
                    logger.info('%s主机采集Server信息异常:%s' % (j['Description'], e))
        logger.info('ssh将采集了%d台主机信息，成功了%d台主机' % (len(other_ips), other_fact_num))
    try:
        if server_fact:
            excel(repeat(server_fact), 'server_fact')
        if host_fact:
            excel(repeat(host_fact), 'host_fact')
        if os_fact:
            excel(repeat(os_fact), 'os_fact')
    except:
        pass


def get_cmdbuild_ip_segment():
    get_cmdbuild_time = datetime.datetime.now()
    logger.info("开始在cmdbuild系统中收集ip_segment数据!")
    # 获取主键、网段、网络区域、网络类型
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


def get_local_hostname():
    hostname = socket.gethostname()
    try:
        cf = ConfigParser.ConfigParser()
        cf.read("../conf/base.conf")
        sections = cf.items('hostname')
        for i in sections:
            if str(i[1]) == hostname:
                district = str(i[0])
        try:
            production = cf.get('model', 'production')
        except Exception:
            production = 'False'
        try:
            simulation = cf.get('model', 'simulation')
        except Exception:
            simulation = 'False'
        ip_district = []

        for i in ip_segment_cmdb:
            if i['Network_Type'] == u'服务网络':
                if i['IP_district']:
                    # 内网模拟环境和开发
                    if district == 'developer' or district == 'passwd':
                        if str(i['IP_district'].split('-')[1].strip()) == u'模拟域' and not (
                                            str(i['IP_district'].split('-')[2].strip()) == u'用户接入区（广域网区）' or str(
                                        i['IP_district'].split('-')[2].strip()) == u'设备互联' or str(
                                    i['IP_district'].split('-')[2].strip()) == u'UAT环境'):
                            ip_district.append(str(i['IP_Segment']))
                    # 内网生产环境
                    elif district == 'intranet':
                        if production == 'True':
                            if str(i['IP_district'].split('-')[0].strip()) == u'业务网' and \
                                            str(i['IP_district'].split('-')[1].strip()) == u'生产域' and not (
                                            str(i['IP_district'].split('-')[2].strip()) == u'用户接入区（广域网区）' or str(
                                        i['IP_district'].split('-')[2].strip()) == u'设备互联'):
                                ip_district.append(str(i['IP_Segment']))
                        if simulation == 'True':
                            if not (str(i['IPusage'].strip()) == u'模拟域虚拟服务器管理' or str(
                                    i['IPusage'].strip()) == u'模拟信息区基础服务系统前置/应用服务器'):
                                if str(i['IP_district'].split('-')[0].strip()) == u'业务网' and \
                                                str(i['IP_district'].split('-')[1].strip()) == u'模拟域' and not (
                                                        str(i['IP_district'].split('-')[2].strip()) == u'设备互联' or str(
                                                    i['IP_district'].split('-')[2].strip()) == u'培训系统' or str(
                                                i['IP_district'].split('-')[2].strip()) == u'UAT环境' or str(
                                            i['IP_district'].split('-')[2].strip()) == u'模拟、培训和UAT服务器后端管理网段'):
                                    ip_district.append(str(i['IP_Segment']))
                    # 外网生产环境
                    elif district == 'internet':
                        if production == 'True':
                            if str(i['IP_district'].split('-')[0].strip()) == '互联网' and \
                                            str(i['IP_district'].split('-')[1].strip()) == u'生产域' and not (
                                        str(i['IP_district'].split('-')[2].strip()) == u'设备互联'):
                                ip_district.append(str(i['IP_Segment']))
                        if simulation == 'True':
                            if str(i['IP_district'].split('-')[0].strip()) == '互联网' and \
                                            str(i['IP_district'].split('-')[1].strip()) == u'模拟域' and not (
                                            str(i['IP_district'].split('-')[2].strip()) == u'设备互联' or str(
                                        i['IP_district'].split('-')[2].strip()) == u'UAT环境'):
                                ip_district.append(str(i['IP_Segment']))

        return ip_district
    except Exception, e:
        logger.error('读取配置文件失败:%s', e)
        return False


def get_cmdbuild_host_ip():
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


def verify_ip(ip):
    """
    判断IP是否合规
    """
    try:
        IP(ip)
        return True
    except Exception as e:
        logger.error('%s\tIP不合规，请检查：e' % (ip, e))
        return False


def get_check_ip():
    """
    获取符合采集网段且host关联的IP
    """
    get_check_time = datetime.datetime.now()
    ips_num = 0
    win_ips_num = 0
    for i in host_ip_cmdb:
        if not i['System_Net_Config'].__contains__('/'):
            for j in get_local_hostname():
                if verify_ip(i['System_Net_Config']):
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


def get_cmdbuild_os():
    """
    获取操作系统的主键、版本、位数
    :return: 采集到的操作系统数量
    """
    get_cmdbuild_time = datetime.datetime.now()
    logger.info("开始在cmdbuild系统中收集os数据!")
    try:
        os_cmdb_num = 0
        os = cmdbuild_api.get_class(token, 'OS', cards=True)
        for i in json.loads(os)['data']:
            os_cmdb_info = {}
            if i['Description']:
                os_cmdb_info['Description'] = i['Description'].rstrip()
            if i['OSNAME']:
                os_cmdb_info['OSNAME'] = i['OSNAME'].rstrip()
            # if i['Bit']:
            #     os_cmdb_info['Bit'] = i['Bit'].rstrip()
            # else:
            #     os_cmdb_info['Bit'] = None

            os_cmdb.append(os_cmdb_info)
            os_cmdb_num += 1

        logger.info("在cmdbuild系统上找到%d条操作系统数据", os_cmdb_num)
        cost_time = cost(get_cmdbuild_time)
        logger.info("收集数据成功，耗时%d s", cost_time)
        return os_cmdb_num
    except Exception, e:
        logger.error("收集数据失败，报错内容：%s", e)


def get_cmdbuild_host():
    """
    1.获取HOST的主键(主机名)、所在主机、所在集群、主机类型、操作系统、CPU数量(虚拟机线程数)、内存、CMT(每核管理的线程)、当前内核版本、
      网口数量、光纤口数据量
    2.获取HOST和OS的关系
    :return: 采集到的HOST数量
    """
    get_cmdbuild_time = datetime.datetime.now()
    logger.info("开始在cmdbuild系统中收集host数据!")
    try:
        host_cmdb_num = 0
        host = cmdbuild_api.get_class(token, 'Host', cards=True)
        for i in json.loads(host)['data']:
            host_cmdb.append(
                {'Description': i['Description'],
                 'H_Type': i['H_Type'],
                 'CPU_Num': i['CPU_Num'],
                 'Mem_Size': i['Mem_Size'],
                 'CMT': i['CMT'],
                 'Keneral_Version': i['Keneral_Version'],
                 'NET_Num': i['NET_Num'],
                 'HBA_Num': i['HBA_Num']})
            if i['OS']:
                host_os_cmdb.append({'Host': i['Description'].rstrip('\n'),
                                     'OS': i['OS'].rstrip('\n')})
            host_cmdb_num += 1
        logger.info("采集到%d条数据", host_cmdb_num)
        cost_time = cost(get_cmdbuild_time)
        logger.info("cmdbuild平台Host数据采集成功! 耗时%d秒", cost_time)
        return host_cmdb_num
    except Exception, e:
        logger.error("cmdbuild平台Host数据采集失败! 原因：%s", e)


def get_cmdbuild_server():
    """
    1.获取服务器主键、设备名、序列号、厂商、型号、主板微码、CPU型号、CPU频率、CPU数量、CPU总核心数
    :return: 采集到的服务器数量
    """
    get_cmdbuild_time = datetime.datetime.now()
    logger.info("开始在cmdbuild系统中收集server数据!")
    try:
        server_cmdb_num = 0
        server = cmdbuild_api.get_class(token, 'Server', cards=True)
        for i in json.loads(server)['data']:
            if not i['MANUFACTURE_Factory'] == "IBM":
                # 非AIX 服务器信息
                server_cmdb.append(
                    {'Description': i['Description'],
                     'DevName': i['DevName'],
                     'Series_No': i['Series_No'],
                     'MANUFACTURE_Factory': i['MANUFACTURE_Factory'],
                     'CI_modelid': i['CI_modelid'],
                     'FirmWare': i['FirmWare'],
                     'CPU_Type': i['CPU_Type'],
                     'CPU_Frequency': i['CPU_Frequency'],
                     'CPU_Num': i['CPU_Num'],
                     'CPU_Core_Num': i['CPU_Core_Num']})
                server_cmdb_num += 1
            else:
                # AIX 服务器信息
                server_cmdb.append(
                    {'Description': i['Description'],
                     'DevName': i['DevName'],
                     'Series_No': i['Series_No'],
                     'MANUFACTURE_Factory': i['MANUFACTURE_Factory'],
                     'CI_modelid': i['CI_modelid'],
                     'FirmWare': i['FirmWare'],
                     'CPU_Type': i['CPU_Type'],
                     'CPU_Frequency': i['CPU_Frequency']})

        logger.info("在cmdbuild系统上找到%d条数据", server_cmdb_num)
        cost_time = cost(get_cmdbuild_time)
        logger.info("收集server数据成功，耗时%d s", cost_time)
        return server_cmdb_num
    except Exception, e:
        logger.error("收集server数据失败，报错内容：%s", e)


def get_cmdbuild_all_ip():
    """
    获取所有的IP
    """
    get_cmdbuild_time = datetime.datetime.now()
    logger.info("开始在cmdbuild平台中采集已登记的ip关系数据!")
    try:
        ip_num_cmdb = 0
        result_all_ip = cmdbuild_api.get_class(token, 'System_Net_Config', cards=True)

        all_ip = json.loads(result_all_ip)
        for i in all_ip['data']:
            ip_cmdb.append(i['Description'])
            ip_num_cmdb += 1
        logger.info("采集到%d条已登记的ip数据", ip_num_cmdb)
        cost_time = cost(get_cmdbuild_time)
        logger.info("cmdbuild平台已登记的ip采集成功! 耗时%d秒", cost_time)
    except Exception, e:
        logger.error("cmdbuild平台已登记的ip采集失败! 原因：%s", e)


def get_cmdbuild_host_server():
    get_cmdbuild_time = datetime.datetime.now()
    logger.info("开始在cmdbuild系统中收集host和server关系数据!")
    try:
        host_server_cmdb_num = 0
        relation_host_server = json.loads(cmdbuild_api.get_view(token, 'view_host_server', cards=True))
        for i in relation_host_server:
            host_server_cmdb_info = {}
            if relation_host_server[i]['Server']:
                host_server_cmdb_info['Server'] = relation_host_server[i]['Server'].strip('\n')
            else:
                host_server_cmdb_info['Server'] = None
            if relation_host_server[i]['Host']:
                host_server_cmdb_info['Host'] = relation_host_server[i]['Host'].strip('\n')
            else:
                host_server_cmdb_info['Host'] = None
            if relation_host_server[i]['Series_No']:
                host_server_cmdb_info['Series_No'] = relation_host_server[i]['Series_No'].strip('\n')
            else:
                host_server_cmdb_info['Series_No'] = None
            host_server_cmdb.append(host_server_cmdb_info)
            host_server_cmdb_num += 1
        logger.info("采集到%d条host和server关系数据", host_server_cmdb_num)
        cost_time = cost(get_cmdbuild_time)
        logger.info("cmdbuild平台host和server关系采集成功! 耗时%d秒", cost_time)
        return host_server_cmdb_num
    except Exception, e:
        logger.error("cmdbuild平台host和server关系采集失败! 原因：%s", e)


def compare_os():
    import_time = datetime.datetime.now()
    logger.info("OS数据开始比较!")
    try:
        update_os_num = 0
        add_os_num = 0
        # 字典去重
        for i in [dict(t) for t in set(tuple(d.items()) for d in os_fact)]:
            os_temp = None
            for j in os_cmdb:
                if i['Description'] and j['Description']:
                    while i['Description'] == j['Description']:
                        os_temp = i['Description']
                        if cmp(i, j) != 0:
                            os_final.append({'Description': j['Description'],
                                             'OSNAME': i['OSNAME'],
                                             # 'RelaeseVersion': i['RelaeseVersion'],
                                             # 'Bit': i['Bit']
                                             })
                            j['status'] = 'O'
                            os_excel.append(j)
                            i['status'] = 'U'
                            os_excel.append(i)
                            update_os_num += 1
                        break

            if os_temp is None:
                os_final.append(i)
                i['status'] = 'A'
                os_excel.append(i)
                add_os_num += 1

        logger.info("OS数据比较结束！修改%d条，新增%d条", update_os_num, add_os_num)

        if update_flag:
            if update_os_num != 0 or add_os_num != 0:
                os_dict = {"OS": os_final}
                update_result = cmdbuild_api.put_update(token, json.dumps(os_dict))
                cost_os_time = cost(import_time)
                logger.info("导入数据成功! 耗时%d秒", cost_os_time)
                logger.info("cmdbuild返回结果：" + update_result)
            else:
                cost_os_time = cost(import_time)
                logger.info("两边数据一致! 耗时%d秒", cost_os_time)

        if excel_flag:
            if os_excel:
                excel(repeat(os_excel), 'OS')
    except Exception, e:
        logger.error("操作系统数据比较失败，报错内容：%s", e)


def compare_host():
    # todo: 检查的主机能否确定是在线
    import_time = datetime.datetime.now()
    logger.info("Host数据开始比较!")
    try:
        update_host_num = 0
        add_host_num = 0
        for i in host_fact:
            host_temp = None
            for j in host_cmdb:
                if i['Description'] and j['Description']:
                    while i['Description'].upper() == j['Description'].upper().strip().strip('\n'):
                        host_temp = i['Description']
                        if cmp(i, j) != 0:
                            try:
                                host_final.append({'Description': j['Description'],
                                                   'H_Type': i['H_Type'],
                                                   'CPU_Num': str(i['CPU_Num']),
                                                   'Mem_Size': str(i['Mem_Size']),
                                                   'CMT': str(i['CMT']),
                                                   'Keneral_Version': i['Keneral_Version'],
                                                   'NET_Num': i['NET_Num'],
                                                   'HBA_Num': i['HBA_Num'].strip('\r\n')})
                                j['status'] = 'O'
                                host_excel.append(j)
                                i['status'] = 'U'
                                host_excel.append(i)
                                update_host_num += 1
                            except:
                                pass
                        break

            if host_temp is None:
                try:
                    host_final.append({'Description': i['Description'],
                                       'H_Type': i['H_Type'],
                                       'CPU_Num': str(i['CPU_Num']),
                                       'Mem_Size': str(i['Mem_Size']),
                                       'CMT': str(i['CMT']),
                                       'Keneral_Version': i['Keneral_Version'],
                                       'NET_Num': i['NET_Num'],
                                       'HBA_Num': i['HBA_Num']})
                    i['status'] = 'A'
                    host_excel.append(i)
                    add_host_num += 1
                except:
                    pass
        logger.info("Host数据比较结束！修改%d条Host信息，新增%d条Host信息", update_host_num, add_host_num)

        if update_flag:
            if update_host_num != 0 or add_host_num != 0:
                host_dict = {"Host": host_final}
                update_result = cmdbuild_api.put_update(token, json.dumps(host_dict))
                # print json.dumps(host_dict)
                cost_os_time = cost(import_time)
                logger.info("导入数据成功! 耗时%d秒", cost_os_time)
                logger.info("cmdbuild返回结果：" + update_result)
            else:
                cost_os_time = cost(import_time)
                logger.info("两边数据一致! 耗时%d秒", cost_os_time)

        if excel_flag:
            if host_excel:
                excel(repeat(host_excel), 'Host')

    except Exception, e:
        logger.error("Host数据比较失败，报错内容：%s", e)


def compare_host_os():
    import_time = datetime.datetime.now()
    logger.info("Host和OS关系数据开始比较!")
    try:
        update_host_os_num = 0
        add_host_os_num = 0
        for i in host_os_fact:
            host_os_temp = None
            for j in host_os_cmdb:
                if i and j:
                    while i['Host'].upper() == j['Host'].upper().strip().strip('\n'):
                        host_os_temp = i['Host']
                        if i['OS'] != j['OS']:
                            host_os_del_final.append(j)
                            host_os_excel.append({'Host': j['Host'],
                                                  'OS': j['OS'],
                                                  'Status': 'D'})
                            host_os_del_final.append({'Host': j['Host'],
                                                      'OS': i['OS']})
                            host_os_excel.append({'Host': j['Host'],
                                                  'OS': i['OS'],
                                                  'Status': 'U'})
                            update_host_os_num += 1
                        break

            if host_os_temp is None:
                host_os_add_final.append(i)
                host_os_excel.append({'Host': i['Host'],
                                      'OS': i['OS'],
                                      'Status': 'A'})
                add_host_os_num += 1

        logger.info("Host和OS关系数据比较结束！修改%d条数据，新增%d条数据", update_host_os_num, add_host_os_num)

        if update_flag:
            if update_host_os_num != 0 or add_host_os_num != 0:
                host_os_del_dict = {"Host_To_OS": host_os_del_final}
                # print host_os_del_dict
                host_os_add_dict = {"Host_To_OS": host_os_add_final}
                # print host_os_add_dict
                delete_result = cmdbuild_api.delete_relation(token, json.dumps(host_os_del_dict))
                logger.info("cmdbuild返回结果：" + delete_result)
                add_result = cmdbuild_api.post_relation(token, json.dumps(host_os_add_dict))
                logger.info("cmdbuild返回结果：" + add_result)
                cost_os_time = cost(import_time)
                logger.info("导入数据成功! 耗时%d秒", cost_os_time)
            else:
                cost_os_time = cost(import_time)
                logger.info("两边数据一致! 耗时%d秒", cost_os_time)
        if excel_flag:
            if host_os_excel:
                excel(repeat(host_os_excel), 'Host_OS')
    except Exception, e:
        logger.error("Host和OS关系数据比较失败，报错内容：%s", e)


def compare_host_ip():
    # 主机名，主机类型，操作系统，CPU核数，内存，操作系统类型、线程数、IP
    # 主机名、IP
    # todo:只检查缺少的，进行新增
    import_time = datetime.datetime.now()
    logger.info("主机和IP关系数据开始比较!")
    try:
        ip_add_num = 0
        host_ip_update_num = 0
        host_ip_add_num = 0
        for i in host_ip_fact:
            host_ip_temp = None
            host_ips = []
            host_info = {}
            # 获取CMDB中主机对应HOST
            for j in host_ip_cmdb:
                if i['Host'].upper() == j['Host'].upper().strip().strip('\n'):
                    host_ip_temp = i['Host']
                    host_ips.append(j['System_Net_Config'].split('/')[0])
                    host_info['Host'] = j['Host']
                    host_info['System_Net_Config'] = host_ips

            if host_info != {}:
                # 当查询的IP不在CMDB的IP集之中，新增IP和HOST关系
                if not str(i['System_Net_Config']).__contains__('169.254.'):
                    if i['System_Net_Config'] not in host_info['System_Net_Config']:
                        host_ip_final.append({'Host': host_info['Host'],
                                              'System_Net_Config': i['System_Net_Config']})
                        host_ip_update_num += 1

            if host_ip_temp is None:
                # todo: 主机名录入有大小写区别
                if not str(i['System_Net_Config']).__contains__('169.254.'):
                    host_ip_final.append({'Host': i['Host'],
                                          'System_Net_Config': i['System_Net_Config']})
                    host_ip_add_num += 1

        logger.info("Host和IP数据比较结束！修改%d条数据,新增%d条数据", host_ip_update_num, host_ip_add_num)

        for i in host_ip_final:
            if str(i['System_Net_Config']) not in ip_cmdb:
                # 169.254.0.0/20 为服务器私有IP
                if not str(i['System_Net_Config']).__contains__('169.254.'):
                    ip_final.append({'Description': i['System_Net_Config'], 'Usage_Status': u'已使用'})
                    ip_add_num += 1
        logger.info("IP数据比较结束！需要新增%d条IP地址", ip_add_num)
        if update_flag:
            if ip_add_num != 0:
                ip_dict = {"System_Net_Config": ip_final}
                # print ip_dict
                update_result = cmdbuild_api.put_update(token, json.dumps(ip_dict))
                logger.info("cmdbuild返回结果：" + update_result)

            if host_ip_update_num != 0 or host_ip_add_num != 0:
                host_ip_dict = {"Host_Uses_IP": host_ip_final}
                # print host_ip_dict
                post_result = cmdbuild_api.post_relation(token, json.dumps(host_ip_dict))
                logger.info("cmdbuild返回结果：" + post_result)
                cost_os_time = cost(import_time)
                logger.info("导入数据成功! 耗时%d秒", cost_os_time)
            else:
                cost_os_time = cost(import_time)
                logger.info("两边数据一致! 耗时%d秒", cost_os_time)

        if excel_flag:
            if ip_final:
                excel(repeat(ip_final), 'IP')
            if host_ip_final:
                excel(repeat(host_ip_final), 'Host_IP')

    except Exception, e:
        logger.error("Host和IP关系数据比较失败，报错内容：%s", e)


def compare_server():
    # 主机名，主机类型，操作系统，CPU核数，内存，操作系统类型、线程数、IP
    # 主机名、IP
    # todo:只检查缺少的，进行新增
    import_time = datetime.datetime.now()
    logger.info("Server数据开始比较!")
    try:
        server_update_num = 0
        server_add_num = 0
        for i in server_fact:
            server_temp = None
            for j in server_cmdb:
                if i['Series_No'] and j['Series_No']:
                    if i['Series_No'].upper() == j['Series_No'].upper().strip().strip('\n'):
                        server_temp = i['Series_No']
                        i['Description'] = j['Description']
                        i['DevName'] = j['DevName']
                        if not i['MANUFACTURE_Factory'] == 'IBM':
                            if cmp(i, j) != 0:
                                try:
                                    server_final.append({'Description': j['Description'],
                                                         'DevName': i['DevName'],
                                                         'Series_No': i['Series_No'],
                                                         'MANUFACTURE_Factory': i['MANUFACTURE_Factory'],
                                                         'CI_modelid': i['CI_modelid'],
                                                         'FirmWare': i['FirmWare'],
                                                         'CPU_Type': i['CPU_Type'],
                                                         'CPU_Frequency': i['CPU_Frequency'],
                                                         'CPU_Num': i['CPU_Num'],
                                                         'CPU_Core_Num': i['CPU_Core_Num']})
                                    j['status'] = 'O'
                                    server_excel.append(j)
                                    i['status'] = 'U'
                                    server_excel.append(i)
                                    server_update_num += 1
                                except:
                                    pass
                        else:
                            # todo: AIX拿不到服务器CPU核数和物理核心数
                            k = {'Description': j['Description'],
                                 'DevName': j['DevName'],
                                 'Series_No': j['Series_No'],
                                 'MANUFACTURE_Factory': j['MANUFACTURE_Factory'],
                                 'CI_modelid': j['CI_modelid'],
                                 'FirmWare': j['FirmWare'],
                                 'CPU_Type': j['CPU_Type'],
                                 'CPU_Frequency': j['CPU_Frequency']}
                            if cmp(i, k) != 0:
                                try:
                                    server_final.append({'Description': k['Description'],
                                                         'DevName': i['DevName'],
                                                         'Series_No': i['Series_No'],
                                                         'MANUFACTURE_Factory': i['MANUFACTURE_Factory'],
                                                         'CI_modelid': i['CI_modelid'],
                                                         'FirmWare': i['FirmWare'],
                                                         'CPU_Type': i['CPU_Type'],
                                                         'CPU_Frequency': i['CPU_Frequency']})
                                    k['status'] = 'O'
                                    server_excel.append(k)
                                    i['status'] = 'U'
                                    server_excel.append(i)
                                    server_update_num += 1
                                except:
                                    pass

            if server_temp is None:
                # todo: 新增主键，无法查询到设备名，以序列号为准
                if i['Series_No']:
                    i['Description'] = i['Series_No']
                    i['DevName'] = None
                    server_final.append(i)
                    i['status'] = 'A'
                    server_excel.append(i)
                    server_add_num += 1

        logger.info("Server数据比较结束！修改%d条数据,新增%d条数据", server_update_num, server_add_num)

        if update_flag:
            if server_update_num != 0 or server_add_num != 0:
                server_dict = {"Server": server_final}
                # print server_dict
                update_result = cmdbuild_api.put_update(token, json.dumps(server_dict))
                cost_server_time = cost(import_time)
                logger.info("导入数据成功! 耗时%d秒", cost_server_time)
                logger.info("cmdbuild返回结果：" + update_result)
            else:
                cost_server_time = cost(import_time)
                logger.info("两边数据一致! 耗时%d秒", cost_server_time)

        if excel_flag:
            if server_excel:
                excel(repeat(server_excel), 'Server')

    except Exception, e:
        logger.error("Server数据比较失败，报错内容：%s", e)


def compare_host_server():
    # todo:只检查存在序列号的服务器
    import_time = datetime.datetime.now()
    logger.info("Host和Server关系数据开始比较!")
    try:
        host_server_add_num = 0
        for i in server_host_fact:
            # 'Series_No','Host'
            server_host_info = []
            for j in host_server_cmdb:
                if j.__contains__('Server'):
                    if j['Server']:
                        if i['Series_No'] and j['Series_No']:
                            if i['Series_No'].upper() == j['Series_No'].upper():
                                i['Server'] = j['Server']
                                server_host_info.append(j['Host'])

            if i['Host'] not in server_host_info:
                try:
                    server_host_final.append({'Server': i['Server'],
                                              'Host': i['Host']})
                    server_host_excel.append({'Server': i['Server'],
                                              'Host': i['Host'],
                                              'status': 'A'})
                    host_server_add_num += 1
                except:
                    pass

        logger.info("Host和Server关系数据比较结束！新增%d条数据", host_server_add_num)

        if update_flag:
            if host_server_add_num != 0:
                server_host_dict = {"Host_To_Server": server_host_final}
                # print server_host_dict
                post_result = cmdbuild_api.post_relation(token, json.dumps(server_host_dict))
                logger.info("cmdbuild返回结果：" + post_result)
                cost_os_time = cost(import_time)
                logger.info("导入数据成功! 耗时%d秒", cost_os_time)
            else:
                cost_os_time = cost(import_time)
                logger.info("两边数据一致! 耗时%d秒", cost_os_time)

        if excel_flag:
            if server_host_excel:
                excel(repeat(server_host_excel), 'Server_Host')
    except Exception, e:
        logger.error("Host和Server数据比较失败，报错内容：%s", e)


if __name__ == '__main__':

    token = cmdbuild_api.get_token()

    if token:
        # 黑名单：堡垒机不连接
        black_ip = ['200.31.131.164', '200.31.131.165', '200.31.131.8']

        ips = []

        other_ips = []

        win_ips = []

        if get_cmdbuild_ip_segment() > 0 and get_cmdbuild_host_ip() > 0:
            get_check_ip()

            if get_cmdbuild_os() > 0 and get_cmdbuild_host() > 0 and get_cmdbuild_server() > 0 and get_cmdbuild_host_server() > 0:
                get_cmdbuild_all_ip()
                ansible_facts_info = ansible_adhoc(list(set(ips)))
                ansible_facts(ansible_facts_info)
                ssh_facts(other_ips)
                compare_os()
                compare_host()
                compare_host_os()
                compare_host_ip()
                compare_server()
                compare_host_server()
