import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def dataprocess(filein1,filein2):
    # 数据清洗：去掉VIX期货合约持仓量数据、空行数据
    PRICE = pd.read_excel(filein1, sheet_name='PRICE')
    VIX = pd.read_excel(filein2)

    PRICE = PRICE.set_index('Date'); VIX = VIX.set_index('Date')

    PRICE = PRICE[PRICE.columns.drop(list(PRICE.filter(regex='_POS')))]
    PRICE.dropna(axis=0,how='all',inplace= True)

    PRICE.insert(0, 'VIX', VIX['VIX'])

    return PRICE

def long_short(price):
    # 空头触发条件
    temp = pd.DataFrame(data = None,columns=['short_trigger'])
    temp['short_trigger'] = (price.iloc[:, 1:4].mean(axis=1) - price.iloc[:, 0]) > 0

    # 多头触发条件
    temp2 = pd.DataFrame(data = None,columns=['signal'])
    temp2['signal'] = (price.iloc[:, 3] - price.iloc[:, 1])-(price.iloc[:, 7]-price.iloc[:, 4])

    if not price.iloc[:, 7].isnull:
        temp2[temp2['signal'] > 0.2] = 0
        temp2[(temp2['signal'] <= 0.2) & (temp2['signal'] >= -0.2)] = 0.5
        temp2[temp2['signal'] < -0.2] = 1
    else:
        temp2['signal'] = 'NAN'

    temp['signal'] = temp2['2006-12']
    BOOL = pd.DataFrame(temp['2006-12'],columns=['short_trigger'])

    t = []
    for y in range(2007,2020):
        for m in range(1,13):
            if m < 10:
                t.append(str(y)+'-0'+str(m))
            else:
                t.append(str(y)+'-'+str(m))
    for m in range(1,11):
        if m != 10:
            t.append('2020'+'-0'+str(m))
        else:
            t.append('2020'+'-'+str(m))
    # print(price.iloc[:,111:111+2]['2016-02'])
    # a = price.iloc[:, 111:111 + 2].mean(axis=1)
    # b =  a - price.iloc[:, 0]
    # print(price.iloc[:, 0]['2016-02'],'\n',a['2016-02'],'\n',b['2016-02'])
    for num in range(2,price.columns.size-7):
        # 空头触发记录
        temp = (price.iloc[:,num:num+3].mean(axis=1)-price.iloc[:,0])>0
        temp = pd.DataFrame(temp[t[num - 2]],columns=['short_trigger'])
        # 多头触发记录
        temp2 = pd.DataFrame(data=None, columns=['signal'])

        temp2['signal'] = (price.iloc[:, num+2] - price.iloc[:, num]) - (price.iloc[:, num+6] - price.iloc[:, num+3])

        temp2[temp2['signal'] > 0.2] = 0
        temp2[(temp2['signal'] <= 0.2)&(temp2['signal'] >= -0.2)] = 0.5
        temp2[temp2['signal'] < -0.2] = 1


        temp['signal'] = temp2[t[num - 2]]
        BOOL = pd.concat([BOOL, temp], axis=0)
    # BOOL.to_csv('what.csv')

    start = len(BOOL['2006'])
    #BOOL['short_trigger'] = None
    BOOL['short_pos'] = 0; BOOL['long_pos'] = 75

    for i in range(start,len(BOOL)):
        if bool(BOOL.iloc[i - 3:i,0].values.all()) and BOOL.iloc[i-1,2] <= 50:
                BOOL.iloc[i,2] = BOOL.iloc[i-1,2]+25
        elif ( not bool(BOOL.iloc[i - 3:i,0].values.any()) ) and (BOOL.iloc[i-1,2]>= 25):
            BOOL.iloc[i, 2] = BOOL.iloc[i-1,2] - 25
        else:
            BOOL.iloc[i, 2] = BOOL.iloc[i - 1, 2]
        BOOL.iloc[i, 3] = 75 + 25 * BOOL.iloc[i-5:i,1].sum()/5


    BOOL.drop(BOOL.head(start).index,inplace=True)
    #print(BOOL['2016-01':'2016-02'])
    #BOOL.to_csv('what.csv',header=True)

    return BOOL,t

def rolling_position(short_pos,date):
    total_pos = []
    for t in date:
        days = len(short_pos[t])
        for d in range(days):
            short_4 = round((d+1)/days * short_pos[t].iloc[d, 2] / 3, 2)
            short_3 = round( short_pos[t].iloc[d, 2] / 3, 2)
            short_2 = short_3
            short_1 = short_pos[t].iloc[d, 2] - (short_2 + short_3 + short_4)

            long_7 = round((d + 1) / days * short_pos[t].iloc[d, 3] / 3, 2)
            long_6 = round(short_pos[t].iloc[d, 3] / 3, 2)
            long_5 = long_6
            long_4 = short_pos[t].iloc[d, 3] - (long_5 + long_6 + long_7)

            total_pos.append([long_4, long_5, long_6, long_7, short_1, short_2, short_3, short_4])
            #short_pos[t].iloc[d, 3] = str(total_pos)

    short_pos['bal_pos'] = total_pos
    #short_pos.to_csv('Position_chg.csv')
    total_pos = np.array(total_pos)

    short_pos['long_4'] = total_pos[:,0]
    short_pos['long_5'] = total_pos[:, 1]
    short_pos['long_6'] = total_pos[:, 2]
    short_pos['long_7'] = total_pos[:, 3]
    short_pos['short_1'] = total_pos[:, 4]
    short_pos['short_2'] = total_pos[:, 5]
    short_pos['short_3'] = total_pos[:, 6]
    short_pos['short_4'] = total_pos[:, 7]
    short_pos.to_csv('exp_adv.csv')
    #
    # plt.subplot(2,2,1)
    #
    # short_pos['long_next']['2008'].plot(); plt.ylabel('long_next')
    # plt.subplot(2, 2, 2)
    # short_pos['long_far']['2008'].plot(); plt.ylabel('long_far')
    # plt.subplot(2, 2, 3)
    # short_pos['short_next']['2008'].plot(); plt.ylabel('short_next')
    # plt.subplot(2, 2, 4)
    # short_pos['short_far']['2008'].plot(); plt.ylabel('short_far')
    #
    # plt.show()

    return total_pos

    #print(short_pos['bal_pos'].values[:,1])
def data_test(price, position):

    return

def main():
    filein1 = 'CT_DATA.xlsx'; filein2 = '市场波动率指数(VIX).xls'
    price = dataprocess(filein1,filein2)
    short_pos,date = long_short(price)
    total_pos=rolling_position(short_pos,date)
    #data_test(price,total_pos)
main()
