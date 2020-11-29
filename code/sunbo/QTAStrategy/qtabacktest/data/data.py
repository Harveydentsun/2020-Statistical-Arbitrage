# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 16:55:09 2020

@author: Sun
"""
import os
import sys
sys.path.append(os.path.dirname(__file__)+'{0}..{0}..{0}'.format(os.sep))
import queue
import numpy as np
import pandas as pd
import sqlalchemy as sa
from datetime import datetime
from abc import ABCMeta, abstractmethod
from qtabacktest.engine.event import BarEvent


class DataHandler(object, metaclass=ABCMeta):
    """
    数据类的基类，继承自ABCMeta元类，
    只能继承和重写方法，否则报错
    """
    @abstractmethod
    def update_bars(self):
        """
        完成所有symbol列表中的bar数据更新
        """
        raise NotImplementedError('未实现update_bars()函数！')
    
    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        返回symbol最近的N个bar，若长度不足则返回所有数据
        """
        raise NotImplementedError('未实现get_latest_bars()函数')


class MyDataHandler(DataHandler):
    """
    通过.csv文件获取数据
    """
    def __init__(self, events, symbol_list, start_date, end_date=None,
                 file_name='stockprice.csv'):
        self.events = events            #事件队列
        self.symbol_list = symbol_list  #证券列表
        self.start_date = start_date    #数据开始日期        
        self.end_date = end_date        #数据截止日期             
        self.file_name = file_name        #数据文件
        
        self.symbol_data = {}  #全部证券数据，格式：{symbol_1:df1,..}
        self.latest_symbol_data = {}  #最新证券数据，格式：{symbol:[bar1,...]}
        self.flag_backtest_continue = True  #回测进行标志
        
        if self.end_date is None:
            self.end_date = datetime.today().strftime('%Y-%m-%d') 
            
        self._get_all_data()

    def _get_all_data(self):
        """
        预存全部数据
        """
        name_cov_dict = {'DATE':'datetime','OPEN':'open',
                         'HIGH':'high','LOW':'low',
                         'CLOSE':'close','VOLUME':'volume',
                         'AMOUNT':'amount'}
        df_data = pd.read_csv(r"C:\Users\harvey_sun\Desktop\QTAStrategy\qtabacktest\data\stockprice.csv")
        df_data = df_data[(df_data.DATE>=self.start_date)&(df_data.DATE<=self.end_date)]
        df_data = df_data.fillna(method='ffill')
        df_data = df_data.rename(columns=name_cov_dict).set_index('datetime',drop=False)
        df_data['ID'] = df_data.CODE.astype(str).str.rjust(6,'0') + '.' + df_data.EXCHANGE
        df_data['adj_close'] = df_data.close
        df_data['adj_factor'] = 1
        for symbol in df_data.ID:
            self.symbol_data[symbol] = df_data[df_data.ID == symbol].iterrows()
            self.latest_symbol_data[symbol] = []
        

      
    def _get_new_bar(self, symbol):
        """
        获取新的一个Bar
        """
        dt,row = next(self.symbol_data[symbol])
        return row.to_dict()
    
    def update_bars(self):
        """
        更新Bar，触发Bar事件
        """
        for symbol in self.symbol_list:
            try:
                bar = self._get_new_bar(symbol)
                bar['symbol'] = symbol
                #print(bar)
            except StopIteration:
                self.flag_backtest_continue = False
            else:
                if bar is not None:
                    self.latest_symbol_data[symbol].append(bar)
        if self.flag_backtest_continue:
            self.events.put(BarEvent(bar['datetime']))
            #print(bar['datetime'])
    
    def get_latest_bar(self, symbol):
        """
        获取指定symbol的最新Bar
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print('不存在%s的Bar数据' %symbol)
            return None
        else:
            if len(bars_list) > 0:
                return bars_list[-1]
            return None
            
    def get_latest_bar_value(self,symbol,field='close'):
        """
        获取指定symbol最新Bar的field字段值
        """
        bar = self.get_latest_bar(symbol)
        v = np.nan
        if bar is not None:
            v = bar.get(field,np.nan)
        return v
        
    def get_latest_bar_datetime(self,symbol):
        """
        获取最新Bar的datetime
        """
        return self.get_latest_bar_value(symbol,'datetime')
    
    def get_latest_bars(self, symbol, N=1):
        """
        获取指定symbol最近的N个Bar，N=-1取目前所能看到的数据
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print('不存在%s的Bar数据' %symbol)
            return None
        else:
            if N == -1:
                return bars_list
            elif N > 0:
                return bars_list[-N:]
            else:
                print('请输入正确的周期数目 N')
                return None
        
    def get_latest_bars_values(self, symbol ,field='close', N=1):
        """
        获取指定symbol的field字段序列，N=-1取目前所能看到的数据
        """
        bars_list = self.get_latest_bars(symbol, N)
        values_list = None
        if bars_list is not None:
            values_list = [bar.get(field,np.nan) for bar in bars_list]
        return values_list











                           

class VIXDataHandler(DataHandler):
    """
    通过.csv文件获取数据
    """
    def __init__(self, events, symbol_list, start_date, end_date=None,
                 file_name='CT_Data.csv'):
        self.events = events            #事件队列
        self.symbol_list = symbol_list  #证券列表
        self.start_date = start_date    #数据开始日期        
        self.end_date = end_date        #数据截止日期             
        self.file_name = file_name        #数据文件
        
        self.symbol_data = {}  #全部证券数据，格式：{symbol_1:df1,..}
        self.latest_symbol_data = {}  #最新证券数据，格式：{symbol:[bar1,...]}
        self.flag_backtest_continue = True  #回测进行标志
        
        if self.end_date is None:
            self.end_date = datetime.today().strftime('%Y-%m-%d') 
            
        self._get_all_data()

    def _get_all_data(self):
        """
        预存全部数据
        """
        name_cov_dict = {'Date':'datetime'}
        df_data = pd.read_csv(r"C:\Users\harvey_sun\VIX_output.csv")
        df_data.Date = df_data.Date.apply(lambda x:pd.to_datetime(x).strftime("%Y-%m-%d"))
        data_columns = [x for x in df_data.columns if x[-3:]!='POS']
        data_columns = [x for x in df_data.columns if x[:2]=='UX' or x=='Date']
        df_data = df_data[data_columns]
        df_data = df_data.dropna(axis=0,how='all')
        df_data = df_data[(df_data.Date>=self.start_date)&(df_data.Date<=self.end_date)].sort_values("Date",ascending=True)
        df_data = df_data.dropna(axis=1,how='all')
        df_data = df_data.fillna(0)
        df_data = df_data.rename(columns=name_cov_dict).set_index('datetime',drop=False)
        for symbol in df_data.columns:
            if symbol == 'datetime':
                continue
            symbol_data = df_data[[symbol]].rename({symbol:"close"},axis=1)
            symbol_data = symbol_data.dropna(axis=0,how='all')
            symbol_data['datetime'] = symbol_data.index
            symbol_data['adj_close'] = symbol_data.close
            symbol_data['adj_factor'] = 1
            self.symbol_data[symbol] = symbol_data.iterrows()
            self.latest_symbol_data[symbol] = []
        

      
    def _get_new_bar(self, symbol):
        """
        获取新的一个Bar
        """
        dt,row = next(self.symbol_data[symbol])
        return row.to_dict()
    
    def update_bars(self):
        """
        更新Bar，触发Bar事件
        """
        for symbol in self.symbol_list:
            try:
                bar = self._get_new_bar(symbol)
                bar['symbol'] = symbol
                #print(bar)
            except StopIteration:
                self.flag_backtest_continue = False
            else:
                if bar is not None:
                    self.latest_symbol_data[symbol].append(bar)
        if self.flag_backtest_continue:
            self.events.put(BarEvent(bar['datetime']))
            #print(bar['datetime'])
    
    def get_latest_bar(self, symbol):
        """
        获取指定symbol的最新Bar
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print('不存在%s的Bar数据' %symbol)
            return None
        else:
            if len(bars_list) > 0:
                return bars_list[-1]
            return None
            
    def get_latest_bar_value(self,symbol,field='close'):
        """
        获取指定symbol最新Bar的field字段值
        """
        bar = self.get_latest_bar(symbol)
        v = np.nan
        if bar is not None:
            v = bar.get(field,np.nan)
        return v
        
    def get_latest_bar_datetime(self,symbol):
        """
        获取最新Bar的datetime
        """
        return self.get_latest_bar_value(symbol,'datetime')
    
    def get_latest_bars(self, symbol, N=1):
        """
        获取指定symbol最近的N个Bar，N=-1取目前所能看到的数据
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print('不存在%s的Bar数据' %symbol)
            return None
        else:
            if N == -1:
                return bars_list
            elif N > 0:
                return bars_list[-N:]
            else:
                print('请输入正确的周期数目 N')
                return None
        
    def get_latest_bars_values(self, symbol ,field='close', N=1):
        """
        获取指定symbol的field字段序列，N=-1取目前所能看到的数据
        """
        bars_list = self.get_latest_bars(symbol, N)
        values_list = None
        if bars_list is not None:
            values_list = [bar.get(field,np.nan) for bar in bars_list]
        return values_list


    
if __name__ == '__main__':
    events = queue.Queue()
    #symbol_list = ['000001.XSHE','600519.XSHG','600000.XSHG']
    symbol_list = list(pd.read_csv(r"C:\Users\harvey_sun\VIX_output.csv").columns[1:-11])
    start_date = '2007-01-01'
    end_date = '2020-09-30'
    
    dh = VIXDataHandler(events,symbol_list,start_date,end_date)
    
    for i in range(5):
        dh.update_bars()
        
    bars = dh.get_latest_bars(symbol_list[0], N=5)
    print(bars)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    