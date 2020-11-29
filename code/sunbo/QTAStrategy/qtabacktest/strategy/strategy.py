# -*- coding: utf-8 -*-
"""
Created on Fri Oct 23 15:08:08 2020

@author: Sun
"""

from abc import ABCMeta, abstractmethod
from qtabacktest.engine.event import SignalEvent


class Strategy(object, metaclass=ABCMeta):
    """
    策略类
    """
    @abstractmethod
    def on_bar(self):
        """
        策略类的核心函数，主要用于响应DataHandler的BAR事件
        """
        raise NotImplementedError('未实现on_bar()函数！')
    
    def order_quantity(self, symbol, dt, quantity, direction_str, price, adj_factor,                       
                       margin_rate=1.0, multiplier=1.0,
                       strategy_id='', signal_type=None):
        """
        按股数下单
        参数：
        symbol: str，证券代码
        dt: str，日期时间
        quantity: int, 股票数目，正数表示买入，负数表示卖出        
        direction_str：str，long-多头，short-空头
        price: float, 拟成交价格, 在execution加入滑点后才是真正的成交价格
        adj_factor: float, 复权因子
        margin_rate: float, 保证金率, 数值范围:(0,1.0]
        multiplier: float, 合约乘数
        strategy_id: str, 策略id
        signal_type: str, 表示该信号的含义，无实际的计算作用
        """
        if direction_str.lower() == 'long':
            direction = 1
            if quantity > 0:
                #多头买入 - 方向：+1，动作：+1(开仓)
                action = 1                
            elif quantity < 0:
                #多头卖出 - 方向：+1，动作：-1(平仓)
                action = -1
        elif direction_str.lower() == 'short':
            direction = -1
            if quantity > 0:
                #空头买入 - 方向：-1，动作：-1(平仓)
                action = -1
            elif quantity < 0:
                #空头卖出 - 方向：-1，动作：+1(开仓)
                action = 1
        else:
            raise ValueError('请输入正确的下单参数！')
            
        adj_price = price*adj_factor        
        signal_event = SignalEvent(strategy_id, symbol, dt,
                                   direction, action, abs(quantity), 
                                   price=price, adj_price=adj_price,
                                   margin_rate=margin_rate, multiplier=multiplier,
                                   adj_factor=adj_factor, signal_type=signal_type)       
        self.events.put(signal_event)
        
        
        
        
        
        
        
        
        