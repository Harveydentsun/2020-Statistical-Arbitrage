# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 16:25:28 2020

@author: Sun
"""
import os
import configparser

def read_db_config(ini_file='database.ini', section='LOCAL'):
    """
    读取服务器配置参数
    """  
    #采用绝对路径的方式读取文件，避免解析器工作路径切换的影响
    ini_path = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(ini_path, ini_file)
    if not os.path.exists(config_file):
        raise IOError('不存在服务器参数配置文件[%s]' %config_file)
        
    config = configparser.ConfigParser()
    config.read(config_file, encoding='utf-8')  
    db_config = {}
    if section in config.sections():
        db_config = dict(config._sections[section])
    else:
        print('不存在section：' + section)
                
    return db_config

if __name__ == '__main__':
    config = read_db_config()