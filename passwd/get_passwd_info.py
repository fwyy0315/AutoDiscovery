# -*- coding:UTF-8 -*-
"""
@version:v1.0
@auther: ZhangYu
@contact: zhang.yu@accenture.com
@file: get_passwd_info.py
@time：2017/2/14 10:09
"""
import ConfigParser
import time
import datetime
import paramiko
from action.finallogging import FinalLogger
from passwd.get_check_conf import GetCheckConf

logger = FinalLogger.getLogger()
gcc = GetCheckConf()


class CollectPastPassword(object):
    def __init__(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.passwd_info = []

    def get_connect(self, ip):
        """
        连接受管机
        :return:
        """
        self.ip = ip
        try:
            self.ssh.connect(self.ip, 22, "taddm", "taddm", timeout=10)
            logger.info('%s\t 连接成功' % self.ip)
            return True
        except Exception, e:
            logger.error('%s\t 连接失败:%s' % (self.ip, e))
            return False

    def get_type(self):
        """
        判断操作系统
        :return:
        """
        try:
            rc, out, err = self.ssh.exec_command('uname', timeout=10)
            self.osname = out.readline().strip('\n')
            return self.osname
        except Exception, e:
            logger.error('%s\t 执行uname命令:%s' % (self.ip, e))
            return False

    def get_homename(self):
        """
        获取主机名
        :return:
        """
        try:
            rc, out, err = self.ssh.exec_command('hostname', timeout=10)
            self.hostname = out.readline().strip('\n')
            return self.hostname
        except Exception, e:
            logger.error('%s\t 执行hostname命令:%s' % (self.ip, e))
            return False

    def get_past_day(self, type):
        """
        获取各个操作系统的过期时间
        :param type:
        :return:
        """
        try:
            cf = ConfigParser.ConfigParser()
            cf.read("../conf/base.conf")
            if type == 'AIX':
                maxday = cf.get('collectpastpassword', 'aix')
            elif type == 'SunOS':
                maxday = cf.get('collectpastpassword', 'solaris')
            return maxday
        except Exception, e:
            logger.error('获取失效时间报错' % e)
            return False

    def get_config(self, conf):
        """
        获取账号信息
        :return:
        """
        try:
            accounts = []
            file = open(conf)
            line = file.readline()
            while line:
                if not line.__contains__('#'):
                    accounts.append({'osuser': line.split('|')[0],
                                     'usergroup': line.split('|')[1],
                                     'contactgroup': line.split('|')[2]})
                line = file.readline()
            return accounts
        except Exception, e:
            logger.error('配置文件读取失败:%s' % e)
            return False
        finally:
            file.close()

    def get_aix_passwd_time(self, accounts):
        """
        循环获取账号的最后更新时间
        :return:
        """
        account_info = []
        command = "/usr/local/bin/sudo /usr/bin/cat /etc/security/passwd"
        try:
            rc_cmd, out_cmd, err_cmd = self.ssh.exec_command(command, timeout=10)
            password = out_cmd.readlines()
        except Exception, e:
            logger.error('%s\t执行%s\t命令失败:%s' % (self.ip, command, e))
            return False
        if password:
            for i in accounts:
                for j in password:
                    if j:
                        if j.split(':')[0] == i['osuser']:
                            j_index = password.index(j)
                            if password[j_index + 2].split()[0] == 'lastupdate':
                                last_update_time = password[j_index + 2].split()[2]
                                account_update_time = time.strftime('%Y-%m-%d %H:%M:%S',
                                                                    time.localtime(float(last_update_time)))
                                account_info.append({'osuser': i['osuser'],
                                                     'usergroup': i['usergroup'],
                                                     'contactgroup': i['contactgroup'],
                                                     'account_update_time': account_update_time})

        return account_info

    def get_solaris_passwd_time(self, accounts):
        """
        循环获取账号的最后更新时间
        :return:
        """
        account_info = []
        command = "/usr/sfw/bin/sudo /usr/bin/cat /etc/shadow"
        try:
            rc_cmd, out_cmd, err_cmd = self.ssh.exec_command(command, timeout=10)
            password = out_cmd.readlines()
            for i in accounts:
                for j in password:
                    if j.__contains__(str(i['osuser'])):
                        if j.split(':')[4]:
                            account_update_time = time.strftime(
                                '%Y-%m-%d %H:%M:%S',
                                time.localtime((float(j.split(':')[2]) + float(j.split(':')[4])) * 86400))
                        else:
                            account_update_time = time.strftime('%Y-%m-%d %H:%M:%S',
                                                                time.localtime(float(j.split(':')[2]) * 86400))

                        account_info.append({'osuser': i['osuser'],
                                             'usergroup': i['usergroup'],
                                             'contactgroup': i['contactgroup'],
                                             'account_update_time': account_update_time})
        except Exception, e:
            logger.error('%s\t执行%s\t命令失败:%s' % (self.ip, command, e))
            return False
        return account_info

    def get_system_time(self):
        """
        获取受管机时间 2017-02-14 13:47:39
        :return:
        """
        command = 'date +"%Y-%m-%d %H:%M:%S"'
        try:
            rc_cmd, out_cmd, err_cmd = self.ssh.exec_command(command, timeout=10)
            system_time = out_cmd.readline().strip('\n')
            return system_time
        except Exception, e:
            logger.error('%s\t执行%s\t命令失败:%s' % (self.ip, command, e))
            return False

    def compare_time(self, password_time, system_time, maxday):
        """
        比较时间
        :return:
        """
        try:
            for i in password_time:
                d1 = datetime.datetime.strptime(i['account_update_time'], '%Y-%m-%d %H:%M:%S')
                d2 = datetime.datetime.strptime(system_time, '%Y-%m-%d %H:%M:%S')
                last_date = str(i['account_update_time']).split()[0]
                delta = d2 - d1
                self.passwd_info.append({
                    'Description': str(self.hostname) + '-' + str(self.ip) + '-' + str(i['osuser']),
                    'HostName': str(self.hostname),
                    'IP': str(self.ip),
                    'UserName': i['osuser'],
                    'UpdateTime': last_date,
                    'Expired': str(int(maxday) - delta.days)
                })
                if delta.days - int(maxday) >= 0:
                    print "%s\t%s\t%s密码最后修改时间:%s\t密码过期:%d天" % (
                        str(self.hostname), self.ip, i['osuser'], last_date, (int(maxday) - delta.days))
                elif 10 >= delta.days - int(maxday) > 0:
                    print "%s\t%s\t%s密码最后修改时间:%s\t密码10天内将过期，还有%d天" % (
                        str(self.hostname), self.ip, i['osuser'], last_date, (int(maxday) - delta.days))
                elif 20 >= delta.days - int(maxday) > 10:
                    print "%s\t%s\t%s密码最后修改时间:%s\t密码20天内将过期，还有%d天" % (
                        str(self.hostname), self.ip, i['osuser'], last_date, (int(maxday) - delta.days))
                elif 30 >= delta.days - int(maxday) > 20:
                    print "%s\t%s\t%s密码最后修改时间:%s\t密码30天内将过期，还有%d天" % (
                        str(self.hostname), self.ip, i['osuser'], last_date, (int(maxday) - delta.days))
            return self.passwd_info
        except Exception, e:
            logger.error('比较时间失败' % e)

    def __del__(self):
        self.ssh.close()
