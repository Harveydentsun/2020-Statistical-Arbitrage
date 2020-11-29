# -*- coding: utf-8 -*-
"""
Created on Sat Oct 24 16:43:17 2020

@author: Sun
"""

"""
该模块记录通用参数
"""

class OrderCost(object):
    """
    订单交易费率和滑点设置
    """
    def __init__(self ,open_commission=0.0003, close_commission=0.0003,
                 open_tax=0.0, close_tax=0.001,
                 open_slippage=0.0, close_slippage=0.0,
                 min_commission=5):
        self.open_commission = open_commission    #开仓费率，股票默认是3%%
        self.close_commission = close_commission  #平仓费率，股票默认是3%%
        self.open_tax = open_tax                  #开仓税金，股票默认是0
        self.close_tax = close_tax                #平仓税金，股票默认是0.1%
        self.open_slippage = open_slippage        #开仓滑点，股票默认是0
        self.close_slippage = close_slippage      #平仓滑点，股票默认是0
        self.min_commission = min_commission      #最低佣金，股票默认5元
        
        
class ZeroOrderCost(object):
    """
    订单交易费率和滑点全为0
    """
    def __init__(self):
        self.open_commission = 0.0   #开仓费率
        self.close_commission = 0.0  #平仓费率
        self.open_tax = 0.0          #开仓税金
        self.close_tax = 0.0         #平仓税金
        self.open_slippage = 0.0     #开仓滑点
        self.close_slippage = 0.0    #平仓滑点
        self.min_commission = 0.0    #最低佣金
        
        
        
        
        