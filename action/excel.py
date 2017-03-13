# -*- coding:UTF-8 -*-
from xlwt import Workbook
import datetime

"""
将json文件内容转换为xls文件，生成在~/AutoDiscovery/static/目录中
"""


def excel(data, name):
    book = Workbook()
    title_info = []
    for i in data:
        for k, v in i.items():
            title_info.append(k)
    title = list(set(title_info))
    if len(data) < 65535:
        excel = book.add_sheet(name, cell_overwrite_ok=True)
        for x in range(len(title)):
            excel.write(0, x, title[x].decode('UTF-8'))

        for i in range(len(data)):
            for j in range(len(data[i])):
                excel.write(i + 1, j, data[i][title[j]])
    else:
        page = len(data) / 65535
        for k in range(1, page + 2):
            excel = book.add_sheet(name + '_' + str(k), cell_overwrite_ok=True)
            for x in range(len(title)):
                excel.write(0, x, title[x].decode('UTF-8'))
            if k < page + 1:
                for i in range(65535 * (k - 1), 65535 * k):
                    for j in title:
                        excel.write(i - 65535 * (k - 1) + 1, j, data[i][title[j]])
            else:
                for i in range(65535 * k, len(data)):
                    for j in title:
                        excel.write(i - 65535 * k + 1, j, data[i][title[j]])

    date = datetime.datetime.now().strftime('%Y%m%d')
    book.save('../static/' + name + '.' + date + '.xls')
