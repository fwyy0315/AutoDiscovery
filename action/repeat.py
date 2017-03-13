# -*- coding:utf-8 -*-

"""
数组去重
"""


def repeat(data):
    result = []
    for i in data:
        if i not in result:
            result.append(i)
    return result
