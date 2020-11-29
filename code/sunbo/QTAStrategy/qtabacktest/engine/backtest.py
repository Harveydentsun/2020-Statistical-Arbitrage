# -*- coding: utf-8 -*-
"""
Created on Fri Oct 23 09:53:46 2020

@author: Sun
"""

import os
import sys
sys.path.append(os.path.dirname(__file__)+'{0}..{0}..{0}'.format(os.sep))
import queue
import pandas as pd
from qtabacktest.data.data import VIXDataHandler
from qtabacktest.engine.common import OrderCost
from qtabacktest.engine.portfolio import SimulatedPortfolio
from qtabacktest.engine.execution import SimulatedExecution
from qtabacktest.engine.performance import Performance
from qtabacktest.engine.benchmark import Benchmark
from qtabacktest.strategy.double_ma_strategy import DoubleMovingAverageStrategy


class Backtest(object):
    """
    回测类，整个回测框架的入口
    参数：
    symbol_list: list，股票池，证券列表；
    start_date: str，开始日期，形如‘2019-01-01’
    end_date: str，结束日期，形如‘2019-10-22’
    freq: str，周期，D-日线，W-周线，M-月线，Y-年线，MIN-分钟线
    init_cash: float，初始资金
    order_cost_dict:Dict of Order class, 各个证券类型的交易费率
    strategy：Strategy class，策略类实例
    data_handler: Data class，获取数据所使用的数据类实例
    """
    def __init__(self, symbol_list, start_date, end_date,
                 strategy_cls, strategy_params={},
                 benchmark_code=None,freq='D', init_cash=1e7, 
                 order_cost_dict=None, 
                 data_handler=None,
                 portfolio=None,
                 execution=None,
                 performance=None):
        self.events = queue.Queue()  #FIFO队列，用来管理事件        
        self.symbol_list = symbol_list
        self.start_date = start_date
        self.end_date = end_date
        self.strategy_cls = strategy_cls
        self.strategy_params = strategy_params
        self.freq = freq
        self.init_cash = init_cash
        self.benchmark_code = benchmark_code
        self.order_cost_dict = order_cost_dict
               
        self.data_handler = data_handler
        self.portfolio = portfolio
        self.execution = execution
        self.performance = performance
        self.benchmark = None
        
        
        #生成实例
        self._generate_instances()
       
        
    def _generate_instances(self):
        """
        生成实例和初始化
        """
        #数据实例
        if self.data_handler is None:
            self.data_handler = VIXDataHandler(self.events, 
                                self.symbol_list, self.start_date, self.end_date)
        #组合实例    
        if self.portfolio is None:
            self.portfolio = SimulatedPortfolio(self.events, self.data_handler)
        #执行实例    
        if self.execution is None:
            self.execution = SimulatedExecution(self.events, self.portfolio,
                                                self.order_cost_dict)        
        #基准类
        if self.benchmark_code is not None:
            self.benchmark = Benchmark(self.benchmark_code,
                                       self.start_date, self.end_date)        
        #性能统计实例
        if self.performance is None:
            self.performance = Performance(self.portfolio, self.benchmark)
        
        #策略类实例
        self.strategy_params['events'] = self.events
        self.strategy_params['data'] = self.data_handler
        self.strategy_params['portfolio'] = self.portfolio
        self.strategy = self.strategy_cls(**self.strategy_params)
        
        #交易费用字典实例    
        if self.order_cost_dict is None:
            self.order_cost_dict = {'STOCK':OrderCost(),
                                    'FUTURE':OrderCost(),
                                    'INDEX':OrderCost(),
                                    'OTHERS':OrderCost()}
               
       
    def run(self):
        """
        执行回测
        """  
        while True:
            if self.data_handler.flag_backtest_continue:
                self.data_handler.update_bars()
            else:
                print('update_bars结束！')
                self.portfolio.update_portfolio_lastday()
                break
       
            #处理事件
            while True:
                try:
                    event = self.events.get(block=False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'BAR':
#                           #触发Bar事件                            
                            self.strategy.on_bar(event)
                            #不能在策略的on_bar之前，否则会有未来信息
                            self.portfolio.update_timeindex(event) 
                        elif event.type == 'SIGNAL':
                            #触发Signal事件
                            #print(event)
                            self.portfolio.on_signal(event)
                        elif event.type == 'ORDER':
                            #触发Order事件
                            #print(event)
                            self.execution.on_order(event)
                        elif event.type == 'FILL':
                            #触发Fill事件
                            print(event)
                            self.portfolio.on_fill(event)
                    
    def get_trade_details(self):
        return self.portfolio.get_trade_details()
    
    def get_trade_composite(self):
        return self.portfolio.get_trade_composite()
    
    def get_history_positions(self):
        return self.portfolio.get_history_positions()
    
    def get_all_holdings(self):
        return self.portfolio.get_all_holdings()
    
    def get_benchmark_data(self):
        benchmark_data = None
        if self.benchmark is not None:
            benchmark_data = self.benchmark.get_benchmark_data()
        return benchmark_data
    
    def output_strategy_statistics(self):
        return self.performance.get_strategy_statistics()
    
    def plot_strategy_curves(self,show=True):
        self.performance.plot_strategy_curves(self.strategy.strategy_id,show)
   
       
       
       
       
       
       
       
       
       
       
       
       
       
       
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        