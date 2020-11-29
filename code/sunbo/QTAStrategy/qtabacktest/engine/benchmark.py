# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 16:30:37 2020

@author: Sun
"""

import os
import sys
sys.path.append(os.path.dirname(__file__)+'{0}..{0}..{0}'.format(os.sep))
import copy
import numpy as np
import pandas as pd
import sqlalchemy as sa
from datetime import datetime
from qtabacktest.data.datutils import read_db_config

class Benchmark(object):
    """
    基准类，输出基准相关信息
    
    """
    def __init__(self, benchmark_code, start_date,
                 end_date=datetime.today().strftime('%Y-%m-%d')):
        self.benchmark_code = benchmark_code
        self.start_date = start_date
        self.end_date = end_date
        
        self.benchmark_data = self.load_benchmark_data(self.benchmark_code, 
                                                  self.start_date, self.end_date)
        
        
    def load_benchmark_data(self, benchmark_code, start_date, 
                            end_date=datetime.today().strftime('%Y-%m-%d')):
        """
        读取指数数据
        """
        name_cov_dict = {'Date':'datetime',benchmark_code:'close'}
        df_data = pd.read_csv(r"C:\Users\harvey_sun\VIX_output.csv")
        df_data.Date = df_data.Date.apply(lambda x:pd.to_datetime(x).strftime("%Y-%m-%d"))
        df_data = df_data[['Date',benchmark_code]]
        df_data = df_data[(df_data.Date>=self.start_date)&(df_data.Date<=self.end_date)].sort_values("Date",ascending=True)
        df_data = df_data.dropna(axis=1,how='all')
        df_data = df_data.fillna(method='ffill')
        df_data = df_data.rename(columns=name_cov_dict).set_index('datetime',drop=False)
         
        return df_data
    
    def get_benchmark_data(self):
        """
        获取指数数据
        """
        return self.benchmark_data
    
    def get_benchmark_statisics(self,ndays_year = 250, rf = 0):
        """
        获取基准的统计值
        """
        df_bmk = copy.deepcopy(self.benchmark_data)
        df_bmk['return'] = df_bmk['close']/df_bmk['close'].shift(1) - 1.0
        df_bmk.loc[df_bmk.index[0],'return'] = 0.0
        df_bmk['cum_return'] = 0.0
        df_bmk['nv'] = (df_bmk['return'] + 1.0).cumprod()
        df_bmk['cum_return'] = df_bmk['nv'] - 1.0
        
        #总交易日数
        total_days = df_bmk.shape[0]
        #收益率
        v_return = df_bmk.loc[df_bmk.index[-1],'cum_return']
        #年化收益率
        v_annual_return = pow(1.0 + v_return, ndays_year/total_days) - 1.0
        #波动率
        v_std = df_bmk['return'].std()
        #年化波动率
        v_annual_std = np.sqrt(ndays_year)*v_std
        #夏普率
        v_sharpe_ratio = (v_annual_return - rf)/v_annual_std
        #最大回撤
        df_bmk['drawdown'] = df_bmk['nv']/df_bmk['nv'].cummax() - 1.0
        v_max_drawdown = df_bmk['drawdown'].min()
        #胜率
        v_loss_days = df_bmk['return'].apply(lambda x:np.nan if x<0 else 1).count() #亏损天数
        v_win_pro = (total_days - v_loss_days)/total_days
        
        res_dict = {'return':v_return,
                    'annual_return':v_annual_return,
                    'std':v_std,
                    'annual_std':v_annual_std,
                    'sharpe_ratio':v_sharpe_ratio,
                    'max_drawdown':v_max_drawdown,
                    'win_pro':v_win_pro,
                    'data':df_bmk.loc[:,['nv','return','cum_return','drawdown']]}
        
        return res_dict
    
    
if __name__ == '__main__':
    bmk = Benchmark('VIX', '2018-01-01 00:00:00', '2019-10-30 00:00:00')
    df = bmk.get_benchmark_statisics()
    
    
    
    