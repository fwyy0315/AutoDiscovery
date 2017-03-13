# -*- coding:UTF-8 -*-
"""
@version: v1.0
@auther: ZhangYu
@contact: zhang.yu@accenture.com
@file: ansible_api.py
@time：2017/3/6 15:56
"""
import sys
import multiprocessing

from ansible.plugins.callback import CallbackBase
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from action.finallogging import FinalLogger
from api.conf_api import GetConfInfo

reload(sys)
sys.setdefaultencoding("UTF-8")

logger = FinalLogger.getLogger()
gci = GetConfInfo()

system_conf = gci.get_system_conf()
if system_conf:
    ansible_username = system_conf['username']
    ansible_password = system_conf['password']


class ResultCallback(CallbackBase, ):
    """
    获取ansible执行结果，封装在ansible_facts_info数组中
    """

    def __init__(self, *args, **kwargs):
        super(ResultCallback, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    # extract just the actual error message from the exception text
    def v2_runner_on_unreachable(self, result):
        host = result._host
        self.host_unreachable[result._host.get_name()] = result
        ansible_facts_info.append({host.name: result._result})

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host
        self.host_unreachable[result._host.get_name()] = result
        ansible_facts_info.append({host.name: result._result})

    def v2_runner_on_ok(self, result, **kwargs):
        """Print a json representation of the result

        This method could store the result in an instance attribute for retrieval later
        """
        host = result._host
        ansible_facts_info.append({host.name: result._result})


class Options(object):
    """
    添加ansible的配置信息
    """

    def __init__(self):
        self.connection = "smart"
        self.forks = multiprocessing.cpu_count() * 50
        self.check = False
        self.host_key_checking = False

    def __getattr__(self, name):
        return None


options = Options()
# 用来加载解析yaml文件或JSON内容,并且支持vault的解密
loader = DataLoader()
# 管理变量的类,包括主机,组,扩展等变量,之前版本是在 inventory 中的
variable_manager = VariableManager()
resultcallback = ResultCallback()

ansible_facts_info = []


def ansible_adhoc(ips):
    logger.info("ansible需要采集%d个IP" % (len(ips)))
    inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=ips)
    # 根据 inventory 加载对应变量
    variable_manager.set_inventory(inventory)
    # 增加外部变量
    variable_manager.extra_vars = {"ansible_ssh_user": ansible_username, "ansible_ssh_pass": ansible_password}
    play_source = {"name": "Ansible Ad-Hoc", "hosts": ips, "gather_facts": "no",
                   "tasks": [{"action": {"module": "setup", "args": ""}}]}
    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
    tqm = None
    try:
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            options=options,
            passwords=None,
            stdout_callback=resultcallback,
            run_tree=False,
        )
        tqm.run(play)
        return ansible_facts_info
    finally:
        if tqm is not None:
            tqm.cleanup()
