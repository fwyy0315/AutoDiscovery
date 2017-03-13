# -*- coding:UTF-8 -*-
"""
@version: v1.0
@auther: ZhangYu
@contact: zhang.yu@accenture.com
@file: cmdbuild_api.py
@time：2016/7/7 10:19
"""
import json
import urllib2
from action.finallogging import FinalLogger
from api.conf_api import GetConfInfo

logger = FinalLogger.getLogger()
gci = GetConfInfo()

cmdb_conf = gci.get_cmdb_conf()
if cmdb_conf:
    username = cmdb_conf['username']
    password = cmdb_conf['password']
    CMDBuild_url = cmdb_conf['CMDBuild_url']
    data = cmdb_conf['data']
else:
    username = None
    password = None
    CMDBuild_url = None
    data = None


class CMDBuildAPI(object):
    def __init__(self):
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor)
        self.token = None
        self.response = None

    def get_token(self, url=CMDBuild_url, data=data):
        """
        获取访问token
        :param url:
        :param data:
        :return:
        """
        try:
            req = urllib2.Request(url + '/sessions')
            req.add_header('Content-Type', 'application/json;charset=UTF-8')
            response = self.opener.open(req, data).read()
            self.token = json.loads(response)['data']['_id']
            return self.token
        except urllib2.URLError, e:
            if hasattr(e, 'code'):
                logger.info(e.code)
            elif hasattr(e, 'reason'):
                logger.info(e.reason)

    def get_class(self, token, name=None, cards=False):
        """
        获取表数据
        :param token:
        :param name:
        :param cards:
        :return:
        """
        try:
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'CMDBuild-Authorization': token
            }
            if name:
                if cards:
                    req = urllib2.Request(CMDBuild_url + '/classes/' + name + '/cards', headers=headers)
                else:
                    req = urllib2.Request(CMDBuild_url + '/classes/' + name, headers=headers)
            else:
                req = urllib2.Request(CMDBuild_url + '/classes', headers=headers)
            self.response = self.opener.open(req)
            return self.response.read()
        except urllib2.URLError, e:
            if hasattr(e, 'code'):
                logger.info(e.code)
            elif hasattr(e, 'reason'):
                logger.info(e.reason)

    def get_view(self, token, name=None, cards=False):
        """
        获取视图数据
        :param token:
        :param name:
        :param cards:
        :return:
        """
        try:
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'CMDBuild-Authorization': token
            }
            if name:
                if cards:
                    req = urllib2.Request(CMDBuild_url + '/views/' + name + '/cards', headers=headers)
                else:
                    req = urllib2.Request(CMDBuild_url + '/views/' + name, headers=headers)
            else:
                req = urllib2.Request(CMDBuild_url + '/views', headers=headers)
            self.response = self.opener.open(req)
            return self.response.read()
        except urllib2.URLError, e:
            if hasattr(e, 'code'):
                logger.info(e.code)
            elif hasattr(e, 'reason'):
                logger.info(e.reason)

    def get_domain(self, token, name=None, relations=False):
        """
        获取map关系数据
        :param token:
        :param name:
        :param relations:
        :return:
        """
        try:
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'CMDBuild-Authorization': token
            }
            if name:
                if relations:
                    req = urllib2.Request(CMDBuild_url + '/domains/' + name + '/relations/' + relations,
                                          headers=headers)
                else:
                    req = urllib2.Request(CMDBuild_url + '/domains/' + name + '/relations', headers=headers)
            else:
                req = urllib2.Request(CMDBuild_url + 'domains', headers=headers)
            self.response = self.opener.open(req)
            return self.response.read()
        except urllib2.HTTPError, e:
            if hasattr(e, 'code'):
                logger.info(e.code)
            elif hasattr(e, 'reason'):
                logger.info(e.reason)

    def put_update(self, token, key):
        try:
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'CMDBuild-Authorization': token
            }
            req = urllib2.Request(CMDBuild_url + '/common/cards', data=key, headers=headers)
            req.get_method = lambda: 'PUT'
            self.response = urllib2.urlopen(req)
            return self.response.read()
        except urllib2.HTTPError, e:
            if hasattr(e, 'code'):
                logger.info(e.code)
            elif hasattr(e, 'reason'):
                logger.info(e.reason)

    def post_relation(self, token, key):
        """
        新增map表的关系
        :param token:
        :param key:
        :return:
        """
        try:
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'CMDBuild-Authorization': token
            }
            req = urllib2.Request(CMDBuild_url + '/common/relations', data=key, headers=headers)
            self.response = urllib2.urlopen(req)
            return self.response.read()
        except urllib2.HTTPError, e:
            if hasattr(e, 'code'):
                logger.info('ERROR code: ' + e.code)
            elif hasattr(e, 'reason'):
                logger.info('ERROR reason: ' + e.reason)

    def delete_relation(self, token, key):
        """
        删除map表的关系
        :param token:
        :param key:
        :return:
        """
        try:
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'CMDBuild-Authorization': token
            }
            req = urllib2.Request(CMDBuild_url + '/common/relations', data=key, headers=headers)
            req.get_method = lambda: 'DELETE'
            self.response = urllib2.urlopen(req)
            return self.response.read()
        except urllib2.HTTPError, e:
            if hasattr(e, 'code'):
                logger.info(e.code)
            elif hasattr(e, 'reason'):
                logger.info(e.reason)

    def __del__(self):
        self.opener.close()
