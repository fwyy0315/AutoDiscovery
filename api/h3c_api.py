# -*- coding:UTF-8 -*-
"""
@version: v1.0
@auther: ZhangYu
@contact: zhang.yu@accenture.com
@file: cmdbuild_api.py
@time：2016/4/30 9:19
"""
import urllib2
from action.finallogging import FinalLogger
from api.conf_api import GetConfInfo

logger = FinalLogger.getLogger()
gci = GetConfInfo()
h3c_conf = gci.get_h3c_conf()

if h3c_conf:
    username = h3c_conf['username']
    password = h3c_conf['password']
    imc_url = h3c_conf['imc_url']
    http_url = h3c_conf['http_url']


class H3CAPI(object):
    """
    iMC 平台是开放的 SOA 架构平台，Web Services 则是 SOA 体系和核心。目前在三种主流的 Web Services 实现方案中，因为 REST 模式的
    Web Services 与复杂的 SOAP 和 XML-RPC 对比来讲明显的更加简洁，越来越多的 Web 服务开始采用 REST 风格设计和实现。
    模拟环境接口文档地址：http://199.31.165.81:8080/imcrs/userguide/rest/index.html
    """

    def __init__(self):
        self.authhandler = urllib2.HTTPDigestAuthHandler()
        self.authhandler.add_password("iMC RESTful Web Services", imc_url, username, password)

    def page(self, api_url):
        try:
            opener = urllib2.build_opener(self.authhandler)
            urllib2.install_opener(opener)
            pagehandle = urllib2.Request(http_url + imc_url + api_url)
            pagehandle.add_header('Accept', 'application/json')
            result = urllib2.urlopen(pagehandle).read()
            return result
        except Exception, e:
            logger.error("访问" + http_url + imc_url + api_url + " 失败:%s", e)
            return False

    def __del__(self):
        self.authhandler.close()
