# -*- coding:utf-8 -*-
import logging.handlers
import datetime

"""
日志输出方法
"""


class FinalLogger:
    def __init__(self):
        pass

    logger = None
    date = datetime.datetime.now().strftime('%Y%m%d')
    levels = {"n": logging.NOTSET,
              "d": logging.DEBUG,
              "i": logging.INFO,
              "w": logging.WARN,
              "e": logging.ERROR,
              "c": logging.CRITICAL}

    log_level = "d"
    log_file = "../log/AutoDiscovery." + date + ".log"
    log_max_byte = 10 * 1024 * 1024
    log_backup_count = 5

    @staticmethod
    def getLogger():
        if FinalLogger.logger is not None:
            return FinalLogger.logger

        FinalLogger.logger = logging.Logger("loggingmodule.FinalLogger")
        log_handler = logging.handlers.RotatingFileHandler(filename=FinalLogger.log_file,
                                                           maxBytes=FinalLogger.log_max_byte,
                                                           backupCount=FinalLogger.log_backup_count)
        log_fmt = logging.Formatter("[%(levelname)s][%(funcName)s][%(asctime)s]%(message)s")
        log_handler.setFormatter(log_fmt)
        FinalLogger.logger.addHandler(log_handler)
        FinalLogger.logger.setLevel(FinalLogger.levels.get(FinalLogger.log_level))
        return FinalLogger.logger
