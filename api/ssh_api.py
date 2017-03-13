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
username = cf.get('system', 'username')
password = cf.get('system', 'password')

sudo_username = cf.get('system_sudo', 'username')
sudo_password = cf.get('system_sudo', 'password')


def ssh2_sudo(ip):
    cmd_host_info = {}
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, 22, sudo_username, sudo_password, timeout=10)

        out_serial = []
        try:
            dmidecode_command = '/usr/bin/sudo /usr/sbin/dmidecode |grep "System Information" -A 6'
            rc_cmd, out_cmd, err_cmd = ssh.exec_command(dmidecode_command, get_pty=True, timeout=10)
            out_serial = out_cmd.readlines()
        except Exception, e:
            logger.error('%s\t执行命令%s\t报错:%s' % (ip, dmidecode_command, e))
        if out_serial:
            for i in out_serial:
                if i.__contains__('Manufacturer'):
                    cmd_host_info['MANUFACTURE_Factory'] = i.split(':')[1].strip('\r\n').split()[0]
                elif i.__contains__('Product Name'):
                    cmd_host_info['CI_modelid'] = i.split(':')[1].strip('\r\n').strip()
                elif i.__contains__('Serial Number'):
                    cmd_host_info['Series_No'] = i.split(':')[1].strip('\r\n').strip()
                # todo:微码方法暂时无法获得
                cmd_host_info['FirmWare'] = None
        else:
            cmd_host_info['MANUFACTURE_Factory'] = None
            cmd_host_info['CI_modelid'] = None
            cmd_host_info['Series_No'] = None
            cmd_host_info['FirmWare'] = None

        out_fibre = []
        try:
            rc_cmd, out_cmd, err_cmd = ssh.exec_command('/sbin/lspci |grep -i fibre |sort -u |wc -l', get_pty=True,
                                                        timeout=10)
            out_fibre = out_cmd.readline()
        except Exception, e:
            logger.error('%s\t执行命令%s报错:%s' % (ip, '/sbin/lspci |grep -i fibre |sort -u |wc -l', e))

        if out_fibre:
            cmd_host_info['HBA_Num'] = out_fibre
        ssh.close()
    except Exception, e:
        logger.error('%s\t连接超时:%s' % (ip, e))
    return cmd_host_info


class SSH2(object):
    def __init__(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def get_connect(self):
        try:
            self.ssh.connect(self.ip, 22, username, password, timeout=10)
            logger.info('%s\t 连接成功' % self.ip)
            return True
        except Exception, e:
            logger.error('%s\t 连接失败:%s' % (self.ip, e))
            return False

    def get_type(self):
        try:
            rc_type, out_type, err_type = self.ssh.exec_command('uname', timeout=10)
            self.osname = out_type.readline().strip('\n')
            return self.osname
        except Exception, e:
            logger.error('%s\t 执行uname命令:%s' % (self.ip, e))
            return False

    def get_linux(self):
        cmd_host_info = {}
        linux_command = {'Description': 'uname -n',
                         'H_Type': 'dmesg |grep -i virtual |grep VMware |wc -l',
                         'CPU_Phy_Num': 'cat /proc/cpuinfo |grep "physical id" |sort -u |wc -l',
                         'Mem_Size': 'cat /proc/meminfo |grep MemTotal',
                         'CPU_Num': 'cat /proc/cpuinfo |grep processor |sort -u |wc -l',
                         'OS': 'lsb_release -d',
                         'Keneral_Version': 'uname -r',
                         'Bit': 'getconf LONG_BIT',
                         'HBA_Num': '/sbin/lspci |grep -i fibre |sort -u |wc -l',
                         'CPU_Type': 'cat /proc/cpuinfo |grep "model name" |sort -u',
                         'NET_Num': '/sbin/lspci |grep Ethernet |wc -l',
                         'CPU_Core_Num': 'cat /proc/cpuinfo |grep "cpu cores" |sort -u |awk \'{print $4}\''
                         }
        for k, v in linux_command.iteritems():
            try:
                rc_cmd, out_cmd, err_cmd = self.ssh.exec_command(v, timeout=10)
                cmd_host_info[k] = out_cmd.readline().strip('\n')
            except Exception, e:
                logger.error('%s\t执行%s\t命令失败:%s' % (self.ip, v, e))

        # 操作系统类型
        cmd_host_info['OSNAME'] = self.osname

        # 操作系统版本
        cmd_host_info['OS'] = ' '.join(cmd_host_info['OS'].split()[1:]) + ' ' + cmd_host_info['Bit'] + 'bit'

        # 内存数
        if int(cmd_host_info['Mem_Size'].split()[1]) % (1024 * 1024) == 0:
            cmd_host_info['Mem_Size'] = unicode(str(int(cmd_host_info['Mem_Size'].split()[1]) / 1024 / 1024) + 'GB')
        else:
            cmd_host_info['Mem_Size'] = unicode(str(int(cmd_host_info['Mem_Size'].split()[1]) / 1024 / 1024 + 1) + 'GB')

        # 网卡
        cmd_host_info['NET_Num'] = unicode(cmd_host_info['NET_Num'].split()[-1])

        # 光纤口
        cmd_host_info['HBA_Num'] = unicode(cmd_host_info['HBA_Num'].split()[-1])

        # ip
        ip_command = "/sbin/ifconfig -a |grep inet |grep -v 127.0.0.1 |grep -v 0.0.0.0 |grep -v inet6 " \
                     "|awk '{print $2}'|tr -d 'addr:'"
        try:
            rc_cmd_ip, out_cmd_ip, err_cmd_ip = self.ssh.exec_command(ip_command, timeout=10)
            cmd_host_info['System_Net_Config'] = out_cmd_ip.readlines()
        except Exception, e:
            logger.error('%s\t执行%s\t命令超时:%s' % (self.ip, ip_command, e))

        # CPU型号
        cmd_host_info['CPU_Type'] = ' '.join(cmd_host_info['CPU_Type'].split()[3:-2])

        # CPU频率
        cmd_host_info['CPU_Frequency'] = cmd_host_info['CPU_Type'].split()[-1]
        if cmd_host_info['CPU_Frequency'].__contains__('GHz'):
            cmd_host_info['CPU_Frequency'] = str('%.2f' % (float(cmd_host_info['CPU_Frequency'].strip('GHz')))) + 'GHz'
        elif cmd_host_info['CPU_Frequency'].__contains__('MHz'):
            cmd_host_info['CPU_Frequency'] = str(
                '%.2f' % (float(cmd_host_info['CPU_Frequency'].strip('MHz')) / 1000)) + 'GHz'
        elif cmd_host_info['CPU_Frequency'].__contains__('KHz'):
            cmd_host_info['CPU_Frequency'] = str(
                '%.2f' % (float(cmd_host_info['CPU_Frequency'].strip('KHz')) / 1000 ** 2)) + 'GHz'
        else:
            cmd_host_info['CPU_Frequency'] = None

        # 主机类型
        if cmd_host_info['H_Type'] is not None:
            # 当主机为虚拟机时，CMT默认为1，当主机为物理机时，CMT等于总线程数/物理核数/单核core数
            if int(cmd_host_info['H_Type']) > 0:
                cmd_host_info['H_Type'] = u'虚拟机'
                # 线程
                cmd_host_info['CMT'] = u'1'
                # CPU数量
                cmd_host_info['CPU_Num'] = cmd_host_info['CPU_Num'].split()[-1]
            else:
                cmd_host_info['H_Type'] = u'物理机'

                # 获取server信息，序列号、型号、厂商
                dmidecode_command = '/usr/bin/sudo /usr/sbin/dmidecode |grep "System Information" -A 6'
                try:
                    rc_cmd, out_cmd, err_cmd = self.ssh.exec_command(dmidecode_command, timeout=10)
                    dmidecode_out = out_cmd.readlines()
                except Exception, e:
                    logger.error('%s\t执行%s\t命令超时:%s' % (self.ip, dmidecode_command, e))
                    dmidecode_out = []
                if dmidecode_out:
                    for i in dmidecode_out:
                        if i.__contains__('Manufacturer'):
                            cmd_host_info['MANUFACTURE_Factory'] = i.split(':')[1].strip('\r\n').split()[0]
                        elif i.__contains__('Product Name'):
                            cmd_host_info['CI_modelid'] = i.split(':')[1].strip('\r\n').strip()
                        elif i.__contains__('Serial Number'):
                            cmd_host_info['Series_No'] = i.split(':')[1].strip('\r\n').strip()
                        # todo:微码方法暂时无法获得
                        cmd_host_info['FirmWare'] = None
                else:
                    cmd_host_info['MANUFACTURE_Factory'] = None
                    cmd_host_info['CI_modelid'] = None
                    cmd_host_info['Series_No'] = None
                    cmd_host_info['FirmWare'] = None

                # 单核core数量
                cmd_host_info['CPU_Core_Num'] = cmd_host_info['CPU_Core_Num'].split()[-1]

                # 物理核心数量
                cmd_host_info['CPU_Phy_Num'] = cmd_host_info['CPU_Phy_Num'].split()[-1]

                # CMT(每个核心管理的线程数)
                # CMT = 总线程数/core核心数/物理CPU个数
                if int(cmd_host_info['CPU_Num']) != 0 and int(cmd_host_info['CPU_Core_Num']) != 0 and int(
                        cmd_host_info['CPU_Phy_Num']) != 0:
                    cmd_host_info['CMT'] = str(int(cmd_host_info['CPU_Num']) / int(cmd_host_info['CPU_Core_Num']) / int(
                        cmd_host_info['CPU_Phy_Num']))

                # CPU数量
                # 总core数量
                if int(cmd_host_info['CPU_Core_Num']) != 0 and int(cmd_host_info['CPU_Phy_Num']) != 0:
                    cmd_host_info['CPU_Num'] = int(cmd_host_info['CPU_Core_Num']) * int(cmd_host_info['CPU_Phy_Num'])
                    cmd_host_info['CPU_Core_Num'] = cmd_host_info['CPU_Num']
        return cmd_host_info

    def get_aix(self):
        cmd_host_info = {}
        aix_command = {'Description': 'uname -n',
                       'H_Type': 'lparstat -i |grep Type',
                       'CPU_Num': '/usr/sbin/lsdev -Cc processor |wc -l',
                       'Mem_Size': 'prtconf |grep "Good Memory Size"',
                       'CMT': '/usr/sbin/lsattr -El `/usr/sbin/lsdev -Cc processor |head -1 |awk -F \' \' \'{print $1}\'` -a smt_threads',
                       'Bit': '/usr/sbin/prtconf |grep "Kernel Type" ',
                       'Keneral_Version': 'oslevel -s',
                       'Series_No': 'prtconf |grep "Machine Serial Number"',
                       'NET_Num': 'lsdev -Cc adapter |grep ent|grep -v fcs |grep -v vscsi |wc -l',
                       'HBA_Num': 'lsdev -Cc adapter |grep fcs|wc -l'
                       }
        for k, v in aix_command.iteritems():
            try:
                rc_cmd, out_cmd, err_cmd = self.ssh.exec_command(v, timeout=10)
                cmd_host_info[k] = out_cmd.readline().strip('\n')
            except Exception, e:
                logger.error('%s\t执行%s\t命令失败:%s' % (self.ip, v, e))
        # 操作系统类型
        cmd_host_info['OSNAME'] = self.osname

        # 操作系统版本
        cmd_host_info['OS'] = self.osname + ' ' + cmd_host_info['Keneral_Version'] + ' ' + \
                              cmd_host_info['Bit'].split()[2].split('-')[0] + 'bit'

        # 内存数
        if int(cmd_host_info['Mem_Size'].split()[-2]) % 1024 == 0:
            cmd_host_info['Mem_Size'] = str(int(cmd_host_info['Mem_Size'].split()[-2]) / 1024) + 'GB'
        else:
            cmd_host_info['Mem_Size'] = str(int(cmd_host_info['Mem_Size'].split()[-2]) / 1024 + 1) + 'GB'

        # 位数
        cmd_host_info['Bit'] = cmd_host_info['Bit'].split()[2].split('-')[0]

        # ip
        ip_command = 'ifconfig -a |grep inet |grep -v inet6 |grep -v 127.0.0.1 |grep -v 0.0.0.0 |awk \'{print $2}\''
        rc_cmd_ip, out_cmd_ip, err_cmd_ip = self.ssh.exec_command(ip_command, timeout=10)
        cmd_host_info['System_Net_Config'] = out_cmd_ip.readlines()

        # 序列号
        cmd_host_info['Series_No'] = cmd_host_info['Series_No'].split()[-1]

        # 网卡
        cmd_host_info['NET_Num'] = unicode(cmd_host_info['NET_Num'].split()[-1])

        # 光纤口
        cmd_host_info['HBA_Num'] = unicode(cmd_host_info['HBA_Num'].split()[-1])

        # 厂商
        cmd_host_info['MANUFACTURE_Factory'] = u'IBM'

        # 主机类型
        if str(cmd_host_info['H_Type'].split()[2]).__contains__('Shared'):
            cmd_host_info['H_Type'] = '虚拟机'.decode('UTF-8')
            # CPU核数
            cmd_host_info['CPU_Num'] = unicode(
                str(int(cmd_host_info['CPU_Num'].split()[0]) * int(cmd_host_info['CMT'].split()[1])))
            # SMT线程数
            cmd_host_info['CMT'] = u'1'
        else:
            cmd_host_info['H_Type'] = '物理机'.decode('UTF-8')
            # CPU核数
            cmd_host_info['CPU_Num'] = cmd_host_info['CPU_Num'].split()[0]

            # SMT线程数
            cmd_host_info['CMT'] = cmd_host_info['CMT'].split()[1]

            try:
                rc_cmd, out_cmd, err_cmd = self.ssh.exec_command('/usr/sbin/prtconf', get_pty=True, timeout=10)
                prtconf_out = out_cmd.readlines()
            except Exception, e:
                logger.error('%s\t执行%s\t命令失败:%s' % (self.ip, '/usr/sbin/prtconf', e))
                prtconf_out = []

            if prtconf_out:
                for i in prtconf_out:
                    if i.strip('\n').split(':')[0] == 'Processor Implementation Mode':
                        cmd_host_info['CPU_Type'] = i.strip('\n').split(':')[1].split('\r')[0].strip()
                    if i.strip('\n').split(':')[0] == 'Processor Clock Speed':
                        if i.strip('\n').split(':')[1].__contains__('MHz'):
                            cmd_host_info['CPU_Frequency'] = str(
                                '%.2f' % (float(i.strip('\n').split(':')[1].split()[0]) / 1000)) + 'GHz'
                        elif i.strip('\n').split(':')[1].__contains__('KHz'):
                            cmd_host_info['CPU_Frequency'] = str(
                                '%.2f' % (float(i.strip('\n').split(':')[1].split()[0]) / 1000 ** 2)) + 'GHz'
                        elif i.strip('\n').split(':')[1].__contains__('GHz'):
                            cmd_host_info['CPU_Frequency'] = str(
                                '%.2f' % (float(i.strip('\n').split(':')[1].split()[0]))) + 'GHz'
                        else:
                            cmd_host_info['CPU_Frequency'] = None
                    if i.strip('\n').split(':')[0] == 'Firmware Version':
                        cmd_host_info['FirmWare'] = i.strip('\n').split(':')[1].split(',')[1].strip('\r')
                    if i.strip('\n').split(':')[0] == 'System Model':
                        cmd_host_info['CI_modelid'] = i.strip('\n').split(':')[1].split(',')[1].strip('\r')
            else:
                cmd_host_info['CPU_Type'] = None
                cmd_host_info['CPU_Frequency'] = None
                cmd_host_info['CI_modelid'] = None
                cmd_host_info['FirmWare'] = None
        return cmd_host_info

    def get_solaris(self):
        """
        获取solaris主机的信息：
        :return: cmd_host_info(dict)
        1.T系列物理机：主机名、型号、内存、CPU数量、OS位数、内核版本、CMT、ip、网卡、光纤卡、CPU物理个数、CPU总核心数、
        主板微码、厂商、CPU型号
        2.虚拟机，逻辑分区，X和V系列物理机：主机名、型号、内存、CPU数量、OS位数、内核版本、CPU、CMT、ip、网卡、光纤卡
        """
        cmd_host_info = {}
        sunos_command = {'Description': 'uname -n',
                         'CI_modelid': '/usr/sbin/prtdiag -v |grep "System Configuration"',
                         'Mem_Size': '/usr/sbin/prtconf |grep "Memory size"',
                         'CPU_Num': '/usr/sbin/psrinfo | wc -l',
                         'Bit': 'isainfo -b',
                         'OS': 'cat /etc/release |grep Solaris',
                         'Keneral_Version': 'showrev |grep "Kernel version"',
                         'CPU_Core_Num': '/usr/bin/kstat cpu_info |grep core_id  |grep -v p|sort -u |wc -l',
                         }
        for k, v in sunos_command.iteritems():
            try:
                rc_cmd, out_cmd, err_cmd = self.ssh.exec_command(v, timeout=10)
                cmd_host_info[k] = out_cmd.readline().strip('\n')
            except Exception, e:
                logger.error('%s\t执行%s\t命令失败:%s' % (self.ip, v, e))
        # 主机型号
        cmd_host_info['CI_modelid'] = cmd_host_info['CI_modelid'].split()[-1]

        # 操作系统类型
        cmd_host_info['OSNAME'] = u'Solaris'

        # 操作系统版本
        cmd_host_info['OS'] = (' '.join(cmd_host_info['OS'].split()[:-3]).strip('Oracle')).lstrip() + '.' + \
                              cmd_host_info['OS'].split()[-2].split('_')[1].lstrip('u').rstrip('wos') + ' ' + \
                              cmd_host_info['Bit'] + 'bit'

        # 内核版本
        cmd_host_info['Keneral_Version'] = cmd_host_info['Keneral_Version'].split('_')[-1]

        # CPU总核心数
        cmd_host_info['CPU_Core_Num'] = cmd_host_info['CPU_Core_Num'].split()[-1]

        # 内存数
        if int(cmd_host_info['Mem_Size'].split()[-2]) % 1024 == 0:
            cmd_host_info['Mem_Size'] = str(int(cmd_host_info['Mem_Size'].split()[-2]) / 1024) + 'GB'
        else:
            cmd_host_info['Mem_Size'] = str(int(cmd_host_info['Mem_Size'].split()[-2]) / 1024 + 1) + 'GB'

        # 位数
        cmd_host_info['Bit'] = cmd_host_info['Bit']

        # ip
        ip_command = '/sbin/ifconfig -a |grep inet |grep -v inet6 |grep -v 127.0.0.1 |grep -v 0.0.0.0 ' \
                     '|awk \'{print $2}\' '
        rc_cmd_ip, out_cmd_ip, err_cmd_ip = self.ssh.exec_command(ip_command, timeout=10)
        cmd_host_info['System_Net_Config'] = out_cmd_ip.readlines()

        # 网卡
        # todo：网卡信息收集需要配置sudo
        net_command = '/usr/sfw/bin/sudo /sbin/dladm show-dev |wc -l'
        try:
            rc_cmd_net, out_cmd_net, err_cmd_net = self.ssh.exec_command(net_command, timeout=10)
            cmd_host_info['NET_Num'] = unicode(out_cmd_net.readline().strip().strip('\n'))
        except Exception, e:
            logger.error('%s\t 执行%s\t命令超时:%s' % (self.ip, net_command, e))
            cmd_host_info['NET_Num'] = None

        # 光纤卡
        hba_command = '/usr/sbin/fcinfo hba-port |grep -i serial |wc -l'
        try:
            rc_cmd_hba, out_cmd_hba, err_cmd_hba = self.ssh.exec_command(hba_command, timeout=10)
            cmd_host_info['HBA_Num'] = unicode(out_cmd_hba.readline().strip().strip('\n'))
        except Exception, e:
            logger.error('%s\t 执行fcinfo hba-port命令超时:%s' % (self.ip, e))
            cmd_host_info['HBA_Num'] = None

        # 主机类型、CPU核数、序列号
        # 虚拟机
        if cmd_host_info['CI_modelid'].__contains__('Platform'):
            cmd_host_info['H_Type'] = '虚拟机'.decode('UTF-8')
            # CPU_Num 虚拟机等于线程数
            cmd_host_info['CPU_Num'] = cmd_host_info['CPU_Num'].split()[-1]
            # CMT 虚拟机默认为1
            cmd_host_info['CMT'] = u'1'

        # todo:X和V系列默认物理机，无法查询序列号，T系列能查询序列号为物理机
        elif cmd_host_info['CI_modelid'].__contains__('V') or cmd_host_info['CI_modelid'].__contains__('X'):
            cmd_host_info['H_Type'] = '物理机'.decode('UTF-8')
            # CMT X和V系列 CMT等于线程数除以Core数
            cmd_host_info['CMT'] = int(cmd_host_info['CPU_Num'].split()[-1]) / int(
                cmd_host_info['CPU_Core_Num'])
            cmd_host_info['CMT'] = unicode(str(cmd_host_info['CMT']))

            # CPU_Num
            cmd_host_info['CPU_Num'] = cmd_host_info['CPU_Core_Num']
        elif cmd_host_info['CI_modelid'].__contains__('T'):
            try:
                rc_cmd, out_cmd, err_cmd = self.ssh.exec_command('/usr/sbin/prtdiag -v |tail -3', timeout=10)
                cmd_host_type = out_cmd.readlines()
            except Exception, e:
                cmd_host_type = []
                logger.error('%s\t执行%s\t命令失败:%s' % (self.ip, '/usr/sbin/prtdiag -v |tail -3', e))

            if cmd_host_type:
                if cmd_host_type[0].__contains__("Chassis Serial Number"):
                    cmd_host_info['Series_No'] = cmd_host_type[-1].strip('\n')
                else:
                    cmd_host_info['Series_No'] = None
            else:
                cmd_host_info['Series_No'] = None

            if cmd_host_info['Series_No'] is not None:
                cmd_host_info['H_Type'] = '物理机'.decode('UTF-8')
                cmd_host_info['CMT'] = int(cmd_host_info['CPU_Num'].split()[-1]) / int(
                    cmd_host_info['CPU_Core_Num'])
                # CMT等于线程数除以核心数
                # CPU_Num
                cmd_host_info['CPU_Num'] = cmd_host_info['CPU_Core_Num'].split()[-1]

                # 获取逻辑主机所在服务器
                out_ldm = []
                try:
                    rc_cmd, out_cmd, err_cmd = self.ssh.exec_command('/usr/sfw/bin/sudo /usr/sbin/ldm ls',
                                                                     get_pty=True,
                                                                     timeout=10)
                    out_ldm = out_cmd.readlines()
                except Exception, e:
                    logger.error('%s\t 执行/usr/sfw/bin/sudo /usr/sbin/ldm ls\t命令超时:%s' % (self.ip, e))

                # 集群信息
                core = 0
                if out_ldm:
                    server_host = []
                    for i in out_ldm:
                        if i.split()[0] != 'second' and i.split()[0] != 'primary' and i.split()[0] != 'NAME':
                            server_host.append(i.split()[0])
                        if i.split()[0] != 'NAME':
                            if i.split()[4].isdigit():
                                # core等于所有分区的VCPU总和
                                core += int(i.split()[4])
                    server_host.append(cmd_host_info['Description'])
                    # solaris 虚拟分区主机名
                    cmd_host_info['Series_Host'] = server_host
                else:
                    cmd_host_info['Series_Host'] = cmd_host_info['Description']

                sunos_server = {'CPU_Type': '/usr/bin/kstat cpu_info |grep brand |sort -u',
                                'CPU_Frequency': '/usr/bin/kstat cpu_info |grep clock_MHz  |sort -u',
                                'FirmWare': '/usr/sbin/prtdiag -v |grep Firmware'
                                }
                for k, v in sunos_server.iteritems():
                    try:
                        rc_cmd, out_cmd, err_cmd = self.ssh.exec_command(v, timeout=10)
                        cmd_host_info[k] = out_cmd.readline().strip('\n')
                    except Exception, e:
                        logger.error('%s\t执行%s\t命令失败:%s' % (self.ip, v, e))
                cmd_host_info['CPU_Type'] = cmd_host_info['CPU_Type'].split()[-1].strip()
                cmd_host_info['CPU_Phy_Num'] = int(cmd_host_info['CI_modelid'].split('-')[-1])
                # 总核心数
                if core != 0:
                    CPU_Core_Num = core / cmd_host_info['CMT']
                    cmd_host_info['CPU_Core_Num'] = unicode(str(CPU_Core_Num))
                # CPU主频
                if cmd_host_info['CPU_Frequency'].__contains__('MHz'):
                    cmd_host_info['CPU_Frequency'] = str(
                        '%.2f' % (float(cmd_host_info['CPU_Frequency'].split()[-1]) / 1000)) + 'GHz'
                elif cmd_host_info['CPU_Frequency'].__contains__('KHz'):
                    cmd_host_info['CPU_Frequency'] = str(
                        '%.2f' % (float(cmd_host_info['CPU_Frequency'].split()[-1]) / 1000 * 1000)) + 'KHz'
                elif cmd_host_info['CPU_Frequency'].__contains__('GHz'):
                    cmd_host_info['CPU_Frequency'] = str(
                        '%.2f' % (float(cmd_host_info['CPU_Frequency'].split()[-1]))) + 'GHz'
                else:
                    cmd_host_info['CPU_Frequency'] = cmd_host_info['CPU_Frequency'].split()[-1]
                cmd_host_info['FirmWare'] = cmd_host_info['FirmWare'].split()[3]
                cmd_host_info['MANUFACTURE_Factory'] = u'ORACLE'
                # CMT type转化为unicode，之前计算type为int
                cmd_host_info['CMT'] = unicode(str(cmd_host_info['CMT']))
            else:
                cmd_host_info['H_Type'] = '虚拟机'.decode('UTF-8')
                # CPU_Num
                cmd_host_info['CPU_Num'] = cmd_host_info['CPU_Num'].split()[-1]
                # CMT
                cmd_host_info['CMT'] = u'1'
        return cmd_host_info

    def get_info(self, ip):
        self.ip = ip
        if self.get_connect():
            if self.get_type():
                if self.get_type() == 'Linux':
                    self.fact_info = self.get_linux()
                elif self.get_type() == 'AIX':
                    self.fact_info = self.get_aix()
                elif self.get_type() == 'SunOS':
                    self.fact_info = self.get_solaris()
            return self.fact_info

    def __del__(self):
        self.ssh.close()


ssh2 = SSH2()


def get_fact_info(ip):
    try:
        return ssh2.get_info(ip)
    except Exception, e:
        logger.error('%s\t采集信息失败:%s' % (ip, e))
        return None


def mult(ips, processes=multiprocessing.cpu_count() * 20):
    """
    多线程执行
    :param ips:
    :param processes:
    :return:
    """
    pool = multiprocessing.Pool(processes=processes)
    return pool.map(get_fact_info, ips)
