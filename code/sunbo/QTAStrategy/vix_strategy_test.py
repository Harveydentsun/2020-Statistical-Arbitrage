# -*- coding: utf-8 -*-
"""
Created on Mon Nov  2 00:42:34 2020

@author: sun
"""
import pandas as pd
from qtabacktest.engine.backtest import Backtest
from qtabacktest.engine.common import OrderCost,ZeroOrderCost
from qtabacktest.strategy.vix_strategy import VIXStrategy

#回测起止日期
start_date = '2007-01-01'
end_date = '2020-09-30'
#策略和参数
strategy_cls = VIXStrategy
#基准代码
benchmark_code = 'SPX500'
#证券列表
symbol_list = list(pd.read_csv(r"C:\Users\harvey_sun\VIX_output.csv").columns[1:-11])

#费率字典
# order_cost_dict = {'STOCK':OrderCost(open_slippage=0.000025, close_slippage=0.000025),
#                     'FUTURE':OrderCost(open_slippage=0.000025, close_slippage=0.000025),
#                     'INDEX':OrderCost(open_slippage=0.000025, close_slippage=0.000025),
#                     'OTHERS':OrderCost(open_slippage=0.000025, close_slippage=0.000025)} 

# order_cost_dict = {'STOCK':OrderCost(open_slippage=0, close_slippage=0),
#                     'FUTURE':OrderCost(open_slippage=0, close_slippage=0),
#                     'INDEX':OrderCost(open_slippage=0, close_slippage=0),
#                     'OTHERS':OrderCost(open_slippage=0, close_slippage=0)} 

#费率字典
order_cost_dict = {'STOCK':ZeroOrderCost(),
                  'FUTURE':ZeroOrderCost(),
                  'INDEX':ZeroOrderCost(),
                  'OTHERS':ZeroOrderCost()} 

#费率字典
#order_cost_dict = {'STOCK':OrderCost(),
#                   'FUTURE':OrderCost(),
#                   'INDEX':OrderCost(),
#                   'OTHERS':OrderCost()} 

#新建回测
bkt = Backtest(symbol_list, start_date, end_date,strategy_cls,
               benchmark_code = benchmark_code,
               order_cost_dict = order_cost_dict)
#回测开始
bkt.run() 
#输出策略统计指标
res = bkt.output_strategy_statistics()
#输出收益曲线
bkt.plot_strategy_curves(show=True)
#获取交易细节、持仓等信息
df_details = bkt.get_trade_details() 
df_composite = bkt.get_trade_composite()
df_positions = bkt.get_history_positions()
df_holdings = bkt.get_all_holdings()
#df_benchmark = bkt.get_benchmark_data()
#保存表格
#df_details.to_excel('df_details.xls')
#df_positions.to_excel('df_positions.xls')
#df_holdings.to_excel('df_holdings.xls')

    