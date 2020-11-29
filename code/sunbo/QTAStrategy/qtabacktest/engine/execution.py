# -*- coding: utf-8 -*-
"""
Created on Sat Oct 24 18:34:45 2020

@author: Sun
"""

import os
import sys
sys.path.append(os.path.dirname(__file__)+'{0}..{0}..{0}'.format(os.sep))
import queue
import numpy as np
import pandas as pd
from abc import ABCMeta, abstractmethod
from qtabacktest.engine.event import FillEvent
from qtabacktest.engine.common import OrderCost


class Execution(object, metaclass=ABCMeta):
    """
    订单执行类，负责处理订单，计算滑点、费率等
    """
    @abstractmethod
    def on_order(self):
        raise NotImplementedError('未实现on_order()函数！')
        
        
class SimulatedExecution(Execution):
    """
    订单执行类，模拟交易所成交情况，负责处理订单，计算滑点、费率等
    参数：
    events: queue.Queue，事件队列
    """
    def __init__(self, events, portfolio, order_cost_dict=None):
        self.events = events
        self.portfolio = portfolio  #组合管理，做订单检查
        self.order_cost_dict = order_cost_dict
        #费率字典实例    
        if self.order_cost_dict is None:
            self.order_cost_dict = {'STOCK':OrderCost(),
                                    'FUTURE':OrderCost(),
                                    'INDEX':OrderCost(),
                                    'OTHERS':OrderCost()}
            
    def get_symbol_type(self, symbol):
        """
        获取证券类型，返回值为：STOCK,FUTURE,INDEX,OTHERS
        """
        #采用正则表达式匹配
        return 'STOCK'
        
    def on_order(self, event):
        """
        订单处理函数，响应ORDER事件，触发FILL事件
        """
        if event.type != 'ORDER':
            return None
        
        # 订单的价格和数量
        symbol = event.symbol  #证券代码
        dt = event.dt  #日期时间
        direction = event.direction  #方向
        action = event.action  #动作
        price = event.price  #申报价格
        quantity = event.quantity  #申报数量
        multiplier = event.multiplier  #合约乘数
        adj_factor = event.adj_factor  #复权因子
        exchange = event.symbol.split('.')[-1]  #交易所
        
        if adj_factor is None:
            raise ValueError('%s - %s. 请输入正确的复权因子adj_factor' %(symbol, dt))
        
        #判断证券类别，选择对应的费率、滑点等
        symbol_type = self.get_symbol_type(symbol)
        order_cost = self.order_cost_dict[symbol_type] 
        
        #注意事项：
        #1.开仓时，可以按照原始的成交价和数量计算成交金额，也可以按照后复权的成交价和数量计算成交金额
        #2.平仓时，由于在开仓到平仓的这段时间可能出现分红送股等除权除息的情况，因此，只能按照后复权的情况处理
        #3.因此，全部在后台换算成后复权的价格和数量才能保证收益率准确
        #开仓
        min_commission = order_cost.min_commission
        if action > 0: 
            open_slippage = order_cost.open_slippage
            if event.direction > 0:
                fill_price = price * (1.0 + open_slippage)  #多头开仓，买入
            else:
                fill_price = price * (1.0 - open_slippage)  #空头开仓，卖出           
            adj_fill_price = fill_price*adj_factor  #复权成交价                                    
            adj_quantity = quantity/adj_factor  #复权成交数量
            amount = fill_price*quantity*multiplier  #成交金额
            fee_commission = amount * order_cost.open_commission
            fee_tax = amount * order_cost.open_tax
            if fee_commission < min_commission:
                fee_commission = min_commission  #最低佣金要求
            fee = fee_commission + fee_tax          
        elif action < 0: #平仓
            #查询现有组合是否有足够的平仓数量
            key = (symbol, direction)
            holdnum_now = self.portfolio.current_positions.get(key,{}).get('holdnum_now',0)
            if quantity > holdnum_now:
                print('({} , {})可平仓数目不足, 现有：{}, 拟平仓: {}'.format(
                        symbol, direction, holdnum_now, quantity))
                return None
            else:
                adj_holdnum_now = self.portfolio.current_positions[key]['adj_holdnum_now']
                adj_quantity = (quantity/holdnum_now)*adj_holdnum_now #换算出对应的复权成交数量
                
            close_slippage = order_cost.close_slippage
            if event.direction > 0:
                fill_price = price * (1.0 - close_slippage)  #多头平仓，卖出
            else:
                fill_price = price * (1.0 + close_slippage)  #空头平仓，买入
            adj_fill_price = fill_price*adj_factor  #复权成交价
            amount = adj_fill_price*adj_quantity*multiplier  #成交金额 
            fee_commission = amount * order_cost.close_commission
            fee_tax = amount * order_cost.close_tax
            if fee_commission < min_commission:
                fee_commission = min_commission  #最低佣金要求
            fee = fee_commission + fee_tax
        else:
            raise ValueError('请输入正确的开平仓动作action')
            

        #创建FLL事件实例
        fill_event = FillEvent(event.strategy_id,
                               symbol,
                               dt,
                               exchange,
                               direction,
                               action,
                               quantity, 
                               adj_quantity,
                               price,
                               event.adj_price,
                               fill_price,
                               adj_fill_price,
                               amount,
                               fee, 
                               event.margin_rate,
                               multiplier,
                               adj_factor,
                               event.order_type)
        #将FILL事件加入队列
        self.events.put(fill_event)
    

    
    
    
    
    
    
    
    
    
    
    
    
    