# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 17:08:46 2020

@author: Sun
"""
import os
import copy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class Performance(object):
    """
    策略收益和风险等指标的统计类
    参数：
    portfolio: 资产管理对象
    benchmark: 基准对象
    """
    def __init__(self, portfolio, benchmark=None):
        self.portfolio = portfolio
        self.benchmark = benchmark
        
    
    def get_strategy_statistics(self, ndays_year = 250, rf = 0, output=True):
        """
        统计策略各项风险指标
        参数：
        df_holdings: DataFrame, 周期为日的净资产列表，必须含有日期和净资产列
        ndays_year: int, 年交易日数
        rf: float, 无风险收益率
        output: boolean, 是否输出统计指标
        """
        df_hold = copy.deepcopy(self.portfolio.get_all_holdings())  #深拷贝，防止修改原始数据
        df_hold['return'] = df_hold['net_asset']/df_hold['net_asset'].shift(1) - 1.0
        df_hold.loc[df_hold.index[0],'return'] = 0.0
        df_hold['cum_return'] = 0.0
        df_hold['nv'] = (df_hold['return'] + 1.0).cumprod()
        df_hold['cum_return'] = df_hold['nv'] - 1.0
        
        v_return_bmk = 0
        v_annual_return_bmk = 0
        bmk_data = None
        if self.benchmark is not None:
            bmk_stat = self.benchmark.get_benchmark_statisics(ndays_year, rf)
            v_return_bmk = bmk_stat['return']
            v_annual_return_bmk = bmk_stat['annual_return']
            bmk_data = bmk_stat['data']
        
        #总交易日数
        total_days = df_hold.shape[0]
        #收益率
        v_return = df_hold.loc[df_hold.index[-1],'cum_return']
        #年化收益率
        v_annual_return = pow(1.0 + v_return, ndays_year/total_days) - 1.0
        #超额收益alpha
        v_alpha = v_annual_return - v_annual_return_bmk
        #Beta系数
        v_beta = 0.0
        if bmk_data is not None:
            df_merge = pd.merge(df_hold.set_index('datetime')[['return']],
                                bmk_data[['return']],
                                how='outer',left_index=True,right_index=True,
                                sort=True,suffixes=('_stra','_bmk')).fillna(method='ffill')
            v_beta = np.cov(df_merge['return_stra'], df_merge['return_bmk'])[0][1]/np.var(bmk_data['return'])
        #波动率
        v_std = df_hold['return'].std()
        #年化波动率
        v_annual_std = np.sqrt(ndays_year)*v_std
        #夏普率
        v_sharpe_ratio = (v_annual_return - rf)/v_annual_std
        #最大回撤
        srs_drawdown = df_hold['nv']/df_hold['nv'].cummax() - 1.0
        v_max_drawdown = srs_drawdown.min()
        #收益最大回撤比
        v_mar = 0
        if v_max_drawdown != 0:
            v_mar = v_annual_return/abs(v_max_drawdown)
        #胜率
        v_loss_days = df_hold['return'].apply(lambda x:np.nan if x<0 else 1).count() #亏损天数
        v_win_pro = (total_days - v_loss_days)/total_days
        
        
        if output:
            print('='*30)
            if self.benchmark is not None:
                print('回测开始: %s' %self.portfolio.start_date)
                print('回测结束: %s' %self.portfolio.end_date)
                print('累计收益: %.2f%%' %(v_return*100))
                print('年化收益: %.2f%%' %(v_annual_return*100))
                print('基准收益: %.2f%%' %(v_return_bmk*100))
                print('基准年化: %.2f%%' %(v_annual_return_bmk*100))
                print('超额收益: %.2f%%' %(v_alpha*100))
                print('Beta系数: %.2f' %v_beta)
                print('波动率: %.2f%%' %(v_annual_std*100))
                print('夏普率: %.2f' %v_sharpe_ratio)
                print('MAR: %.2f' %v_mar)
                print('最大回撤: %.2f%%' %abs(v_max_drawdown*100))
                print('日胜率: %.2f%%' %(v_win_pro*100))
            else:
                print('回测开始: %s' %self.portfolio.start_date)
                print('回测结束: %s' %self.portfolio.end_date)
                print('累计收益: %.2f%%' %(v_return*100))
                print('年化收益: %.2f%%' %(v_annual_return*100))
                print('波动率: %.2f%%' %(v_annual_std*100))
                print('夏普率: %.2f' %v_sharpe_ratio)
                print('MAR: %.2f' %v_mar)
                print('最大回撤: %.2f%%' %abs(v_max_drawdown*100))
                print('日胜率: %.2f%%' %(v_win_pro*100))
            print('='*30)
        
        res_dict =  {'return':v_return,
                    'annual_return':v_annual_return,
                    'alpha':v_alpha,
                    'beta':v_beta,
                    'std':v_std,
                    'annual_std':v_annual_std,
                    'sharpe_ratio':v_sharpe_ratio,
                    'max_drawdown':v_max_drawdown,
                    'win_pro':v_win_pro
                    }
        
        return res_dict
            
    def plot_strategy_curves(self,strategy_id,show=True):
        """
        画图函数
        """       
        df_hold = copy.deepcopy(self.portfolio.get_all_holdings())  #深拷贝，防止修改原始数据
        df_hold = df_hold.set_index('datetime')
        df_hold['nv'] = df_hold['net_asset']/df_hold.loc[df_hold.index[0],'net_asset'] 
        df_hold['cum_return'] = df_hold['nv'] - 1.0
        df_hold['drawdown'] = df_hold['nv']/df_hold['nv'].cummax() - 1.0
        
        if self.benchmark is not None:
            df_bmk = copy.deepcopy(self.benchmark.get_benchmark_data())
            df_bmk['nv'] = df_bmk['close']/df_bmk.loc[df_bmk.index[0],'close']
            df_bmk['cum_return'] = df_bmk['nv'] - 1.0
            df_bmk['drawdown'] = df_bmk['nv']/df_bmk['nv'].cummax() - 1.0
            
            df_merge = pd.merge(df_hold[['cum_return','drawdown']],
                                df_bmk[['cum_return','drawdown']],
                                how='outer',left_index=True,right_index=True,
                                sort=True,suffixes=('_stra','_bmk')).fillna(method='ffill')
        else:
            df_merge = df_hold.rename(columns={'cum_return':'cum_return_stra','drawdown':'drawdown_stra'})
        
        #---展示收益率曲线和最大回撤曲线---
        fig,axes = plt.subplots(2,1,sharex=True)
        ax1 = axes[0]
        ax2 = axes[1]
        id_list = np.arange(1,df_merge.shape[0]+1).tolist()
        date_list = df_merge.index.tolist()
        return_list1 = (100*df_merge['cum_return_stra']).tolist()
        drawdown_list1 = (100*df_merge['drawdown_stra']).tolist()
        
        if self.benchmark is not None:
            return_list2 = (100*df_merge['cum_return_bmk']).tolist()
            drawdown_list2 = (100*df_merge['drawdown_bmk']).tolist()
            
            #画累计收益率曲线图
            title1 = 'Cumulative Return of %s (%s - %s)' %(
                    strategy_id,self.portfolio.start_date,self.portfolio.end_date)
            p1, = ax1.plot(id_list, return_list1, color='steelblue')
            p2, = ax1.plot(id_list, return_list2, color='red')
            ax1.set_title(title1)
            ax1.set_ylabel('Cumulative Return(%)')
            ax1.legend([p1,p2],['strategy','benchmark'],
                       loc='upper left', frameon=False)
            ax1.grid(True)
            #画回撤曲线图
            title2 = 'Drawdown of %s (%s - %s)' %(
                    strategy_id,self.portfolio.start_date,self.portfolio.end_date)
            f2 = ax2.fill_between(id_list,drawdown_list2,0,facecolor='red' ,alpha=0.2)
            f1 = ax2.fill_between(id_list,drawdown_list1,0,facecolor='steelblue', alpha=1.0)            
            ax2.set_title(title2)
            ax2.set_xlabel('date')
            ax2.set_ylabel('Drawdown(%)')
            ax2.grid(True)
            ax2.set_xlim(id_list[0],id_list[-1])
            ax2.set_ylim(top=0)
            ax2.legend([f1,f2],['strategy','benchmark'],
                       loc='lower left', frameon=False)
            fig.set_size_inches(15,8)
            fig.subplots_adjust()
        else:
            #画累计收益率曲线图
            title1 = 'Cumulative Return of %s (%s - %s)' %(
                    strategy_id,self.portfolio.start_date,self.portfolio.end_date)
            ax1.plot(id_list, return_list1, color='steelblue')
            ax1.set_title(title1)
            ax1.set_ylabel('Cumulative Return(%)')
            ax1.grid(True)
            #画回撤曲线图
            title2 = 'Drawdown of %s (%s - %s)' %(
                    strategy_id,self.portfolio.start_date,self.portfolio.end_date)
            ax2.fill_between(id_list,drawdown_list1,0,facecolor='steelblue', alpha=1.0)            
            ax2.set_title(title2)
            ax2.set_xlabel('date')
            ax2.set_ylabel('Drawdown(%)')
            ax2.grid(True)
            ax2.set_xlim(id_list[0],id_list[-1])
            ax2.set_ylim(top=0)
            fig.set_size_inches(15,8)
            fig.subplots_adjust()
                  
        #若不展示，则在本地保存为图片
        if show:
            plt.show()
        else:
            fname = os.path.join(os.getcwd(),strategy_id+'.jpg')
            fig.savefig(fname, dpi=300)
            #关闭净值曲线窗口
            plt.close() 
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    