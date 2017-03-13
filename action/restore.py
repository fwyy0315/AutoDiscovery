# -*- coding:UTF-8 -*-

"""
网络接口简写和全写翻译表
网络设备厂商
"""

restore_dict = {'Ethernet': ['E'], 'FastEthernet': ['F', 'FA', 'FEX'],
                'GigabitEthernet': ['G', 'GE'], 'Ten-GigabitEthernet': ['TG']}


def restore(data):
    temp = None
    for i in restore_dict:
        if data:
            for j in restore_dict[i]:
                if filter(str.isalpha, data.upper()) == j.upper():
                    temp = data.upper().replace(j.upper(), i)
        else:
            return data

    if temp is not None:
        return temp
    else:
        return data


transform_dict = {'Huawei': ['huawei', 'HUAWEI'], 'Cisco': ['cisco', 'CISCO'], 'H3C': ['h3c']}


def transform(data):
    temp = None
    for i in transform_dict:
        if data:
            for j in transform_dict[i]:
                if filter(str.isalpha, data.upper()) == j.upper():
                    temp = data.upper().replace(j.upper(), i)
        else:
            return data

    if temp is not None:
        return temp
    else:
        return data
