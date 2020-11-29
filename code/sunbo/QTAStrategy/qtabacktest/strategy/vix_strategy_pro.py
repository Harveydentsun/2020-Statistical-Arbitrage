# -*- coding: utf-8 -*-
"""
Created on Mon Nov  2 00:42:34 2020

@author: sun
"""
import os
import sys
sys.path.append(os.path.dirname(__file__)+'{0}..{0}..{0}'.format(os.sep))
import queue
import numpy as np
import pandas as pd
from qtabacktest.strategy.strategy import Strategy
from qtabacktest.engine.event import SignalEvent


class VIXStrategy(Strategy):
    """
    参数：
    events(必须): queue.Queue，事件队列
    data(必须): DataHandler class，数据类实例，一般与回测模块的相同
    portfolio(必须): Portfolio class，组合类实例，用来获取当前组合信息和资金情况。
    """
    def __init__(self, filepath=r"C:\Users\harvey_sun\VIX_output.csv", events=None, data=None, portfolio=None):
        self.strategy_id = 'VIXStrategy'
        self.events = events
        self.data = data
        self.portfolio = portfolio
        self.symbol_list = self.data.symbol_list

        self.position_list = self._generate_position(pd.read_csv(filepath))
        
        self.position = {}
        
        self.margin_rate = 0.5
        self.trade_times = 1  #多次交易
        
    def _generate_position(self,data):
        data.Date = pd.to_datetime(data.Date).apply(lambda x:x.strftime("%Y-%m-%d"))
        data2 = pd.read_csv(r"C:\Users\harvey_sun\position_adv.csv")
        data2.Date = data2.Date.apply(lambda x:pd.to_datetime(x).strftime("%Y-%m-%d"))
        data = data[data.Date>='2007-01-03']
        data2 = data2[data2.Date>='2007-01-03']
        data = data.set_index("Date")
        data2 = data2.set_index("Date")
        position = pd.DataFrame(columns=['pos'])
        for t in data.index:
            con = self._get_trade_contract(data,t)
            first = con[con<=1].idxmax()
            second= con[con<=2].idxmax()
            third = con[con<=3].idxmax()
            fourth = con[con<=4].idxmax()
            fifth = con[con<=5].idxmax()
            sixth = con[con<=6].idxmax()
            seventh = con[con<=7].idxmax()
            pos = {first:-data2.loc[t,'short_1'],
                   second:-data2.loc[t,'short_2'],
                   third:-data2.loc[t,'short_3'],
                   fourth:data2.loc[t,'long_4']-data2.loc[t,'short_4'],
                   fifth:data2.loc[t,'long_5'],
                   sixth:data2.loc[t,'long_6'],
                   seventh:data2.loc[t,'long_7']}
            position.loc[t,'pos'] = [pos]
        position.index.name = 'Date'
        return position
        
    
    def _get_trade_contract(self,data,t):
        contract = data.loc[t].dropna()
        contract = contract[[x for x in contract.index if x[:2]=='UX']]
        month = {
            "F":1,
            "G":2,
            "H":3,
            "J":4,
            "K":5,
            "M":6,
            "N":7,
            "Q":8,
            "U":9,
            "V":10,
            "X":11,
            "Z":12,
        }
        contract_month = [month[x[2]] for x in contract.index]
        contract_year = [int(x[-2:])+ int(t[:2])*100 if len(x)==5 else (int(x[-1:])+ int(t[:3])*10+10 if x[-1]!=t[3] else int(x[-1:])+ int(t[:3])*10) for x in contract.index]
        contract_length = (np.array(contract_year)-int(t[:4]))*12 + np.array(contract_month)-int(t[5:7])
        contract_info = pd.Series(contract_length,index=contract.index)
        return contract_info
        
    def on_bar(self, event):
        """
        响应BAR事件，触发SIGNAL事件
        """
        if event.type != 'BAR':
            return None
        
        amount = self.portfolio.get_net_asset()
        dt = pd.to_datetime(event.dt).strftime("%Y-%m-%d")
        if dt <= '2007-01-03':
            return None
        holding_post = self.position_list.loc[dt,'pos'][0]
        while len(self.position) > 0:
            ((symbol,direction),quantity) = self.position.popitem()
    
            bar_dict = self.data.get_latest_bar(symbol)
            v_close = bar_dict['close']
            if direction == 1:
                long_quantity = quantity
                sell_quantity = long_quantity/self.trade_times
                for i in range(self.trade_times):        
                    self.order_quantity(symbol, dt, -sell_quantity, 'long', v_close, 1,                       
                                        margin_rate=self.margin_rate, multiplier=1.0,
                                        strategy_id=self.strategy_id, signal_type='L_C')                           
                    print('>>> {} - 卖出[{}] {} 股,多头平仓'.format(dt,symbol,sell_quantity))
            else:
                short_quantity = quantity
                buy_quantity = short_quantity/self.trade_times
                for i in range(self.trade_times):        
                    self.order_quantity(symbol, dt, buy_quantity, 'short', v_close, 1,                       
                                        margin_rate=self.margin_rate, multiplier=1.0,
                                        strategy_id=self.strategy_id, signal_type='S_C')                           
                    print('>>> {} - 买入[{}] {} 股,空头平仓'.format(dt,symbol,buy_quantity))

        for symbol in holding_post:
            if abs(holding_post[symbol]) < 1e-4:
                continue
            elif holding_post[symbol] > 0:                
                key = (symbol,1)
                bar_dict = self.data.get_latest_bar(symbol)
                v_close = bar_dict['close']
                long_quantity = int(amount/100*holding_post[symbol]/v_close)
                buy_quantity = long_quantity/self.trade_times
                for i in range(self.trade_times):        
                    self.order_quantity(symbol, dt, buy_quantity, 'long', v_close, 1,                       
                                        margin_rate=self.margin_rate, multiplier=1.0,
                                        strategy_id=self.strategy_id, signal_type='L_O')
                    if key not in self.position.keys():                            
                        self.position[key] = buy_quantity
                    else:
                        self.position[key] += buy_quantity
                    print('>>> {} - 买入[{}] {} 股,多头开仓'.format(dt,symbol,buy_quantity))
            else:                
                key = (symbol,-1)
                bar_dict = self.data.get_latest_bar(symbol)
                v_close = bar_dict['close']
                short_quantity = int(amount/100*abs(holding_post[symbol])/v_close)
                sell_quantity = short_quantity/self.trade_times
                for i in range(self.trade_times):        
                    self.order_quantity(symbol, dt, -sell_quantity, 'short', v_close, 1,                       
                                        margin_rate=self.margin_rate, multiplier=1.0,
                                        strategy_id=self.strategy_id, signal_type='S_O')
                    if key not in self.position.keys():                            
                        self.position[key] = sell_quantity
                    else:
                        self.position[key] += sell_quantity
                    print('>>> {} - 卖出[{}] {} 股,空头开仓'.format(dt,symbol,sell_quantity))
