# -*- coding: utf-8 -*-
"""
Created on Sat Oct 24 16:07:17 2020

@author: Sun
"""

import os
import sys
sys.path.append(os.path.dirname(__file__)+'{0}..{0}..{0}'.format(os.sep))
import queue
import copy
import numpy as np
import pandas as pd
from abc import ABCMeta, abstractmethod
from qtabacktest.engine.event import OrderEvent


class Porfolio(object, metaclass=ABCMeta):
    """
    投资组合类，负责维护头寸、持仓和结算等功能
    """
    @abstractmethod
    def on_signal(self):
        raise NotImplementedError('未实现on_signal()函数！')
        
    @abstractmethod
    def on_fill(self):
        raise NotImplementedError('未实现on_fil()函数！')
        
    @abstractmethod
    def update_timeindex(self):
        raise NotImplementedError('未实现update_time()函数')
        
        
class SimulatedPortfolio(Porfolio):
    """
    投资组合类，负责维护头寸、持仓和结算等功能
    参数：
    events: queue.Queue，事件队列
    data_handler: DataHandler class，数据类实例，一般与回测模块的相同
    order_cost: Order class，交易费用类实例
    init_cash: float, 初始资金
    """
    def __init__(self, events, data_handler, order_cost=None, init_cash=1e7):
        self.events = events
        self.data_handler = data_handler
        self.symbol_list = self.data_handler.symbol_list
        self.start_date = self.data_handler.start_date.replace('-','')
        self.end_date = self.data_handler.end_date.replace('-','')
        self.order_cost = order_cost
        self.init_cash = init_cash
        #交易列表：记录详细的每一笔成交订单记录
        self.current_trades = {}  #格式:{(symbol,direction):[trade_dict,...],...}
        self.all_trades = []        
        #综合列表：综合交易和头寸持仓的信息
        self.current_composite = {}  #格式:{(symbol,direction):composite_dict,...}
        self.all_composite = []        
        #头寸列表：记录每个头寸的详细信息，同品种不同方向的算不同头寸
        self.current_positions = {}   #格式:{(symbol,direction):position_dict,...}
        self.all_positions = []
        #持仓列表：主要记录整个账户的总市值、保证金占用、可用资金、净资产等信息
        self.current_holdings = self._generate_init_holdings(self.start_date)
        self.all_holdings = []
        
        #第一个交易日标志
        self.flag_first_tradeday = True
        
        
    def _generate_init_holdings(self, dt):
        """
        生成初始持仓
        """
        holdings_dict = {'datetime':dt, #日期时间
                         'mkt_value':0.0, #持有的所有证券的总市值
                         'margin':0.0,    #持有的所有证券的保证金占用
                         'pnl':0.0,             #profit and loss，当日盈亏
                         'cash':self.init_cash, #可用资金
                         'net_asset':self.init_cash #净资产
                         }
        return holdings_dict
        
    def on_signal(self, signal_event):
        """
        交易信号响应函数，响应SIGNAL事件，触发ORDER事件
        """
        if signal_event.type != 'SIGNAL':
            return None
        
        event = OrderEvent(signal_event.strategy_id,
                           signal_event.symbol,
                           signal_event.dt,
                           signal_event.direction,
                           signal_event.action,
                           signal_event.quantity, 
                           signal_event.price,
                           signal_event.adj_price,
                           signal_event.margin_rate,
                           signal_event.multiplier,
                           signal_event.adj_factor)
        self.events.put(event)
        
    def on_fill(self, fill_event):
         """
         成交事件响应函数，响应FILL事件，完成调仓等动作
         """
         if fill_event.type != 'FILL':
             return None
         
         #注意更新顺序，不能乱
         self._update_trades_from_fill(fill_event)
         self._update_composite_from_fill(fill_event)
         self._update_positions_from_fill(fill_event)
         self._update_holdings_from_fill(fill_event)
     
    def _update_trades_from_fill(self, fill_event):
        """
        更新交易细节记录
        """
        symbol = fill_event.symbol
        direction = fill_event.direction
        action = fill_event.action
        quantity = fill_event.quantity
        multiplier = fill_event.multiplier
        margin_rate = fill_event.margin_rate
        fill_price = fill_event.fill_price
        adj_fill_price = fill_event.adj_fill_price        
        amount = fill_event.amount  #成交金额
        adj_quantity = fill_event.adj_quantity
        
        margin = amount*margin_rate  #保证金占用        
        if (direction>0 and action>0) or (direction<0 and action<0):
            #多头开仓 或 空头平仓，皆为买入
            buy_amount = amount
            sell_amount = 0.0
        elif (direction>0 and action<0) or (direction<0 and action>0):
            #多头平仓 或 空头开仓，皆为卖出
            buy_amount = 0.0
            sell_amount = amount
        else:
            raise ValueError('%s-%s.请输入正确的direction和action值' %(
                             fill_event.dt,symbol))
            
        trade_dict = {'datetime':fill_event.dt,  #日期
                      'symbol':symbol,  #证券代码
                      'direction':direction,  #方向
                      'action':action,  #动作
                      'quantity':quantity,  #成交数量
                      'price':fill_event.price,    #拟成交价
                      'fill_price':fill_price,  #成交价
                      'adj_quantity':adj_quantity,  #复权成交量
                      'adj_price':fill_event.adj_price,  #复权拟成交价
                      'adj_fill_price':adj_fill_price,  #复权成交价
                      'amount':amount,  #成交金额
                      'buy_amount':buy_amount,  #买入金额
                      'sell_amount':sell_amount,  #卖出金额
                      'margin':margin,  #保证金占用
                      'fee':fill_event.fee,  #成交费用
                      'factor':fill_event.adj_factor,  #复权因子
                      'margin_rate':margin_rate,  #保证金率
                      'multiplier':multiplier  #乘数
                      }
        key = (symbol, direction)
        if key not in self.current_trades.keys():
            self.current_trades[key] = []
        self.current_trades[key].append(trade_dict)
        
    def _update_composite_from_fill(self, fill_event):
        """
        更新综合记录
        """
        dt = fill_event.dt
        symbol = fill_event.symbol
        direction = fill_event.direction
        action = fill_event.action
        quantity = fill_event.quantity
        multiplier = fill_event.multiplier
        margin_rate = fill_event.margin_rate
        fill_price = fill_event.fill_price
        adj_fill_price = fill_event.adj_fill_price
        
        
        key = (symbol, direction)  # 头寸key，同一品种不同方向算两个头寸
        trade_dict = self.current_trades[key][-1]  #取对应最新的订单 
        if dt != trade_dict['datetime']:
            return None
        
        #复权收盘价
        adj_close = self.data_handler.get_latest_bar_value(symbol,'adj_close')
        #成交金额
        amount = trade_dict['amount']
        if key not in self.current_composite.keys():
            mkt_val_now = trade_dict['adj_quantity']*adj_close*multiplier
            margin_now = mkt_val_now*margin_rate
            composite_dict = {'datetime':dt,  #日期
                              'symbol':symbol,  #证券代码
                              'direction':direction,  #方向
                              'holdnum_now':trade_dict['quantity'],  #现持有数目
                              'holdnum_pre':0,  #昨持有数目
                              'adj_holdnum_now':trade_dict['adj_quantity'],  #复权现持有数目
                              'adj_holdnum_pre':0,  #复权昨持有数目
                              'mkt_val_now':mkt_val_now,    #现持有市值
                              'mkt_val_pre':0,  #昨持有市值
                              'buy_amount':trade_dict['buy_amount'],  #买入金额
                              'sell_amount':trade_dict['sell_amount'],  #卖出金额
                              'fee':trade_dict['fee'],  #当日费用
                              'pnl':0,  #当日盈亏
                              'margin_now':margin_now,  #现保证金占用
                              'margin_pre':0,  #昨保证金占用
                              'cost':amount,  #总成本
                              'cost_price':fill_price,  #成本价
                              'adj_cost_price':adj_fill_price, #复权成本价
                              'chg':0,  #浮动盈亏(与成本价比)
                              'chg_pct':0,  #浮盈率(与成本价比)
                              'margin_rate':margin_rate,  #保证金率
                              'multiplier':multiplier  #乘数
                              }
            self.current_composite[key] = composite_dict
        else:
            self.current_composite[key]['datetime'] = dt
            if action > 0:
                #开仓
                self.current_composite[key]['holdnum_now'] += quantity
                self.current_composite[key]['adj_holdnum_now'] += trade_dict['adj_quantity']                
                self.current_composite[key]['cost'] += trade_dict['amount']  
                self.current_composite[key]['cost_price'] = (self.current_composite[key]['cost']/
                                           (self.current_composite[key]['holdnum_now']*multiplier)) 
                self.current_composite[key]['adj_cost_price'] = (self.current_composite[key]['cost']/
                                           (self.current_composite[key]['adj_holdnum_now']*multiplier)) 
            elif action < 0:
                #平仓
                self.current_composite[key]['holdnum_now'] -= quantity
                self.current_composite[key]['adj_holdnum_now'] -= trade_dict['adj_quantity']                                
                #平仓时，成本价和复权成本价都不变，总成本减少                 
                self.current_composite[key]['cost'] = (self.current_composite[key]['holdnum_now']*
                                      self.current_composite[key]['cost_price']*multiplier)
            else:
                raise ValueError('%s-%s.请输入正确的action值' %(fill_event.dt,symbol))
            #计算现市值、现保证金占用、买入金额、卖出金额
            self.current_composite[key]['mkt_val_now'] = (adj_close*multiplier*
                                               self.current_composite[key]['adj_holdnum_now'])
            self.current_composite[key]['margin_now'] = (margin_rate*
                                                self.current_composite[key]['mkt_val_now'])
            self.current_composite[key]['buy_amount'] += trade_dict['buy_amount']
            self.current_composite[key]['sell_amount'] += trade_dict['sell_amount'] 
            self.current_composite[key]['fee'] += trade_dict['fee']
        #===========================计算每个头寸的当日盈亏======================================
        # 当日盈亏 = 卖出金额 – 买入金额 + 市值变动 - 费用
        self.current_composite[key]['pnl'] = (self.current_composite[key]['sell_amount'] - 
                                 self.current_composite[key]['buy_amount'] +
                                 direction*(self.current_composite[key]['mkt_val_now'] - 
                                            self.current_composite[key]['mkt_val_pre']) - 
                                 self.current_composite[key]['fee'])
        #注意，浮盈和浮盈率是根据成交价格计算的，不考虑成交费用
        if abs(self.current_composite[key]['holdnum_now']) < 1e-4:
            #若现持有数目为0，则不再计算浮盈，而根据之前的成本价计算浮盈率
            self.current_composite[key]['chg'] = 0
            self.current_composite[key]['chg_pct'] = direction*(adj_fill_price/
                                  self.current_composite[key]['adj_cost_price'] - 1.0)
        else:
            self.current_composite[key]['chg'] = direction*(self.current_composite[key]['mkt_val_now'] - 
                                               self.current_composite[key]['cost'])
            self.current_composite[key]['chg_pct'] = (self.current_composite[key]['chg']/
                                     self.current_composite[key]['cost'])

            
    def _update_positions_from_fill(self, fill_event):
        """
        调整头寸，同一标的不同方向算不同的头寸，允许锁仓
        """
        #根据composite综合信息，去除现持仓数目为0
        current_composite = copy.deepcopy(self.current_composite)  #深拷贝，避免修改原始数据
        for key in self.current_composite.keys():
            if abs(current_composite[key]['holdnum_now']) < 1e-4:
                current_composite.pop(key)
        self.current_positions = current_composite
            
    
    def _update_holdings_from_fill(self, fill_event):
        """
        调整持仓
        """
        #根据composite综合信息，计算出当日盈亏、净资产等指标
        total_pnl = 0
        total_mkt_val = 0
        total_margin = 0
        for key in self.current_composite.keys():            
            total_mkt_val += self.current_composite[key]['mkt_val_now']
            total_margin += self.current_composite[key]['margin_now']
            total_pnl += self.current_composite[key]['pnl']
            
            
        self.current_holdings['datetime'] = fill_event.dt 
        self.current_holdings['mkt_value'] = total_mkt_val
        self.current_holdings['margin'] = total_margin
        self.current_holdings['pnl'] = total_pnl
        self.current_holdings['net_asset'] = (self.all_holdings[-1]['net_asset'] +
                                              self.current_holdings['pnl'])
        self.current_holdings['cash'] = (self.current_holdings['net_asset'] -
                                         self.current_holdings['margin'])
        
    def update_timeindex(self, bar_event):
        """
        根据更新数据对现有持仓做调整
        """
        if bar_event.type != 'BAR':
            return None
        
        #日期时间
        dt = pd.to_datetime(bar_event.dt).strftime("%Y-%m-%d")
        
        #print('================'+dt+'=================')
        
        if self.flag_first_tradeday:
            #第一个交易日
            self.current_holdings = self._generate_init_holdings(dt)
            self.flag_first_tradeday = False
            #self._update_holdings_from_bar(bar_event)
        else:
            #注意更新顺序，不能乱
            self._update_trades_from_bar(bar_event)
            self._update_composite_from_bar(bar_event)
            self._update_positions_from_bar(bar_event)
            self._update_holdings_from_bar(bar_event)
            
        
    def _update_trades_from_bar(self, bar_event):
        """"
        根据Bar事件更新交易明细
        """
        if len(self.current_trades.keys()) > 0:
            #保存不为空的交易明细
            self.all_trades.append(copy.deepcopy(self.current_trades))
        self.current_trades = {}
        
    def _update_composite_from_bar(self, bar_event):
        """
        根据Bar事件更新综合信息
        """
        if len(self.current_composite.keys()) > 0:
            self.all_composite.append(copy.deepcopy(self.current_composite)) #保存不为空的综合信息
        
        if len(self.current_positions.keys()) > 0:
            self.current_composite = copy.deepcopy(self.current_positions)  #不包括持仓为0的品种
            dt = bar_event.dt
            for key in self.current_composite.keys():
                symbol = key[0]  #证券代码
                direction = key[1] #多空方向                    
                adj_close = self.data_handler.get_latest_bar_value(symbol,'adj_close') #复权收盘价
                self.current_composite[key]['datetime'] = dt
                self.current_composite[key]['holdnum_pre'] = (
                                            self.current_composite[key]['holdnum_now'])
                self.current_composite[key]['adj_holdnum_pre'] = (
                                            self.current_composite[key]['adj_holdnum_now'])
                self.current_composite[key]['mkt_val_pre'] = (
                                            self.current_composite[key]['mkt_val_now'])
                self.current_composite[key]['mkt_val_now'] = (adj_close*
                                            self.current_composite[key]['adj_holdnum_now']*
                                            self.current_composite[key]['multiplier'])
                self.current_composite[key]['buy_amount'] = 0
                self.current_composite[key]['sell_amount'] = 0
                self.current_composite[key]['fee'] = 0
                self.current_composite[key]['margin_pre'] = (
                                            self.current_composite[key]['margin_now'])
                self.current_composite[key]['margin_now'] = (
                                            self.current_composite[key]['mkt_val_now']*
                                            self.current_composite[key]['margin_rate'])
                # 当日盈亏 = 卖出金额 – 买入金额 + 市值变动 - 费用
                self.current_composite[key]['pnl'] = (direction*
                                           (self.current_composite[key]['mkt_val_now'] - 
                                            self.current_composite[key]['mkt_val_pre']))
                #注意，浮盈和浮盈率是根据成交价格计算的，不考虑成交费用
                self.current_composite[key]['chg'] = (direction*
                                           (self.current_composite[key]['mkt_val_now'] - 
                                            self.current_composite[key]['cost']))
                self.current_composite[key]['chg_pct'] = (self.current_composite[key]['chg']/
                                            self.current_composite[key]['cost'])
        else:
            self.current_composite = {}

    def _update_positions_from_bar(self, bar_event):
        """
        根据Bar事件更新头寸信息
        """
        if len(self.current_positions.keys()) > 0:
            self.all_positions.append(copy.deepcopy(self.current_positions)) #保存不为空的头寸信息
            
        if len(self.current_composite.keys()) > 0:
            self.current_positions = copy.deepcopy(self.current_composite)  #深拷贝
        else:
            self.current_positions = {}
            
    def _update_holdings_from_bar(self, bar_event):
        """
        根据Bar事件更新持仓信息
        """
        self.all_holdings.append(copy.deepcopy(self.current_holdings))  #保存上一个周期的holdings
        
        if len(self.current_composite.keys()) > 0:
            #根据composite综合信息，计算出当日盈亏、净资产等指标
            total_pnl = 0
            total_mkt_val = 0
            total_margin = 0
            for key in self.current_composite.keys():            
                total_mkt_val += self.current_composite[key]['mkt_val_now']
                total_margin += self.current_composite[key]['margin_now']
                total_pnl += self.current_composite[key]['pnl']
                               
            self.current_holdings['datetime'] = bar_event.dt 
            self.current_holdings['mkt_value'] = total_mkt_val
            self.current_holdings['margin'] = total_margin
            self.current_holdings['pnl'] = total_pnl
            self.current_holdings['net_asset'] = (self.all_holdings[-1]['net_asset'] +
                                                  self.current_holdings['pnl'])
            self.current_holdings['cash'] = (self.current_holdings['net_asset'] -
                                             self.current_holdings['margin'])
        else:
            self.current_holdings['datetime'] = bar_event.dt
            self.current_holdings['pnl'] = 0.0
            
    def update_portfolio_lastday(self):
        """
        保存回测中最后一天的内容
        """
        #保存不为空的交易明细
        if len(self.current_trades.keys()) > 0:            
            self.all_trades.append(copy.deepcopy(self.current_trades))
        #保存不为空的综合信息
        if len(self.current_composite.keys()) > 0:
            self.all_composite.append(copy.deepcopy(self.current_composite)) 
        #保存不为空的头寸信息
        if len(self.current_positions.keys()) > 0:
            self.all_positions.append(copy.deepcopy(self.current_positions)) 
        #保存持仓内容
        self.all_holdings.append(copy.deepcopy(self.current_holdings))
        
        
    #=================================获取信息部分=============================
    def get_trade_details(self):
        """
        获取交易细节清单
        """
        all_trades_list = []
        for trade_dict in self.all_trades:
            for key in trade_dict.keys():
                all_trades_list.extend(trade_dict[key])
                
        columns_list = ['datetime', 'symbol', 'direction', 'action', 'amount', 'fee',
                        'quantity', 'price', 'fill_price',
                        'adj_quantity', 'adj_price', 'adj_fill_price',
                        'buy_amount', 'sell_amount',
                        'margin', 'margin_rate', 'multiplier', 'factor']        
        df = pd.DataFrame(all_trades_list, columns=columns_list)
        df = df.sort_values(by=['datetime','symbol'])
        
        return df
    
    def get_trade_composite(self):
        """
        获取综合的交易信息
        """
        all_composite_list = []
        for comp_dict in self.all_composite:
            for key in comp_dict.keys():
                all_composite_list.append(comp_dict[key])
        columns_list = ['datetime', 'symbol', 'direction', 
                        'holdnum_now', 'holdnum_pre', 'adj_holdnum_now', 'adj_holdnum_pre',
                        'mkt_val_now', 'mkt_val_pre', 
                        'buy_amount', 'sell_amount', 'fee',
                        'pnl', 
                        'margin_now', 'margin_pre',
                        'cost', 'cost_price', 'adj_cost_price',
                        'chg', 'chg_pct',
                        'margin_rate', 'multiplier']
        df = pd.DataFrame(all_composite_list, columns=columns_list)
        #df = df.sort_values(by=['datetime','symbol'])
        
        return df
    
    def get_history_positions(self):
        """
        获取所有的历史头寸信息
        """
        all_positions_list = []
        for pos_dict in self.all_positions:
            for key in pos_dict.keys():
                all_positions_list.append(pos_dict[key])
        columns_list = ['datetime', 'symbol', 'direction', 
                        'holdnum_now', 'holdnum_pre', 'adj_holdnum_now', 'adj_holdnum_pre',
                        'mkt_val_now', 'mkt_val_pre', 
                        'buy_amount', 'sell_amount', 'fee',
                        'pnl', 
                        'margin_now', 'margin_pre',
                        'cost', 'cost_price', 'adj_cost_price',
                        'chg', 'chg_pct',
                        'margin_rate', 'multiplier']
        df = pd.DataFrame(all_positions_list, columns=columns_list)
        #df = df.sort_values(by=['datetime','symbol'])

        return df
    
    def get_all_holdings(self):
        """
        获取所有的持仓信息
        """
        all_holdings_list = []
        for hold_dict in self.all_holdings:
            all_holdings_list.append(hold_dict)
        columns_list = ['datetime', 'mkt_value', 'margin', 'pnl', 'cash', 'net_asset']
        df = pd.DataFrame(all_holdings_list, columns=columns_list)
        df = df.sort_values(by='datetime')

        return df
    
    def get_current_positions(self):
        """
        获取当前持仓
        """
        return self.current_positions()
    
    def get_current_holdings(self):
        """
        获取当前持仓信息
        """
        return self.current_holdings
    
    def get_net_asset(self):
        """
        获取账户净资产(实际上获得的是上一个Bar结束时的净资产)
        """
        return self.current_holdings['net_asset']













