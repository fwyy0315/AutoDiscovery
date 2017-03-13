# -*- coding:UTF-8 -*-
import datetime

"""return 消耗的时间"""


def cost(start_time):
    end_time = datetime.datetime.now()
    cost_time = (end_time - start_time).seconds
    return cost_time
