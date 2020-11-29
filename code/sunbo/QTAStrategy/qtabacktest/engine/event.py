# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 11:21:11 2020

@author: Sun
"""

class Event(object):
    """
    事件类的基类
    """
    pass


class BarEvent(Event):
    """
    Bar事件，收到新Bar时触发该事件
    """
    def __init__(self, dt=None):
        self.type = 'BAR'
        self.dt = dt     #日期时间
        

class SignalEvent(Event):
    """
    信号事件，由策略类触发该事件
    """
    def __init__(self, strategy_id, symbol, dt,
                 direction, action, quantity, 
                 price=None, adj_price=None,
                 margin_rate=1.0, multiplier=1.0,
                 adj_factor=None, signal_type=None):
        self.type = 'SIGNAL'
        self.strategy_id = strategy_id   #策略id
        self.symbol = symbol             #证券代码
        self.dt = dt                     #日期时间
        self.direction = direction       #方向，1-多头，-1-空头
        self.action = action             #动作，1-开仓，-1-平仓
        self.quantity = quantity         #数量
        self.price = price               #价格
        self.adj_price = adj_price       #复权价格
        self.margin_rate = margin_rate   #保证金率，0~1.0，股票默认是1.0
        self.multiplier = multiplier     #合约乘数，股票默认是1.0，IF默认300        
        self.adj_factor = adj_factor     #复权因子        
        self.signal_type = signal_type   #型号类型
        
    def __str__(self):
        return 'SignalEvent:[{}],数量:{},方向:{},动作:{},日期:{}'.format(
                self.symbol,self.quantity,self.direction,self.action,self.dt)
        
        
class OrderEvent(Event):
    """
    订单事件，由组合类触发该事件
    """        
    def __init__(self, strategy_id, symbol, dt,
                 direction, action, quantity, 
                 price=None, adj_price=None,
                 margin_rate=1.0, multiplier=1.0,
                 adj_factor=None, order_type='MKT'):
        self.type = 'ORDER'
        self.strategy_id = strategy_id   #策略id
        self.symbol = symbol             #证券代码
        self.dt = dt                     #日期时间
        self.direction = direction       #方向，1-多头，-1-空头
        self.action = action             #动作，1-开仓，-1-平仓
        self.quantity = quantity         #数量
        self.price = price               #价格
        self.adj_price = adj_price       #复权价格
        self.margin_rate = margin_rate   #保证金率，0~1.0，股票默认是1.0
        self.multiplier = multiplier     #合约乘数，股票默认是1.0，IF默认300       
        self.adj_factor = adj_factor     #复权因子        
        self.order_type = order_type     #订单类型,MKT-市价单，LIMIT-限价单
        
    def __str__(self):
        return 'OrderEvent:[{}],数量:{},方向:{},动作:{},日期:{}'.format(
                self.symbol,self.quantity,self.direction,self.action,self.dt)
        
class FillEvent(Event):
    """
    订单成交事件，由订单执行类触发该事件
    """        
    def __init__(self, strategy_id, symbol, dt, exchange,
                 direction, action, quantity, adj_quantity,
                 price, adj_price,
                 fill_price, adj_fill_price,
                 amount, fee, 
                 margin_rate, multiplier,
                 adj_factor, fill_type=None):
        self.type = 'FILL'
        self.strategy_id = strategy_id   #策略id
        self.symbol = symbol             #证券代码
        self.dt = dt                     #日期时间
        self.exchane = exchange          #交易所
        self.direction = direction       #方向，1-多头，-1-空头
        self.action = action             #动作，1-开仓，-1-平仓
        self.quantity = quantity         #数量
        self.adj_quantity = adj_quantity #复权数量
        self.price = price               #申报价格
        self.adj_price = adj_price       #复权价格
        self.fill_price = fill_price     #成交价格
        self.adj_fill_price = adj_fill_price     #复权成交价格
        self.amount = amount  #成交金额
        self.fee = fee     #手续费等费用
        self.margin_rate = margin_rate   #保证金率，0~1.0，股票默认是1.0
        self.multiplier = multiplier     #合约乘数，股票默认是1.0，IF默认300       
        self.adj_factor = adj_factor     #复权因子        
        self.fill_type = fill_type     #订单类型   
        
    def __str__(self):
        return 'FILLEvent:[{}],数量:{},方向:{},动作:{},日期:{}\n成交价:{},费用:{}'.format(
                self.symbol,self.quantity,self.direction,self.action,self.dt,
                self.fill_price, self.fee)        
        
        
        
        
        
        
        
        
        
        
        
        
        