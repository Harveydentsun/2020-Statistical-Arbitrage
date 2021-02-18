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
    #print(PRICE['2016-01':'2016-02'])
    # q = PRICE.columns[0:96 + 12+5]
    # print(q, '\n', len(q))

    return PRICE

def long_short(price):

    temp = (price.iloc[:, 1:3].mean(axis=1) - price.iloc[:, 0]) > 0
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


        temp = (price.iloc[:,num:num+2].mean(axis=1)-price.iloc[:,0])>0
        temp = pd.DataFrame(temp[t[num - 2]],columns=['short_trigger'])
        BOOL = pd.concat([BOOL,temp],axis=0)

    start = len(BOOL['2006'])
    #BOOL['short_trigger'] = None
    BOOL['short_pos'] = 0

    for i in range(start,len(BOOL)):
        if bool(BOOL.iloc[i - 3:i,0].values.all()) and BOOL.iloc[i-1,1] <= 80:
                BOOL.iloc[i,1] = BOOL.iloc[i-1,1]+20
        elif ( not bool(BOOL.iloc[i - 3:i,0].values.any()) ) and (BOOL.iloc[i-1,1]>= 20):
            BOOL.iloc[i, 1] = BOOL.iloc[i-1,1] - 20
        else:
            BOOL.iloc[i, 1] = BOOL.iloc[i - 1, 1]

    BOOL['long_pos'] = 100
    BOOL.drop(BOOL.head(start).index,inplace=True)
    #print(BOOL['2016-01':'2016-02'])
    #BOOL.to_csv('exp2.csv',header=True)

    return BOOL,t

def rolling_position(short_pos,date):
    total_pos = []
    for t in date:
        days = len(short_pos[t])
        for d in range(days):
            short_far = round((d+1)/days * short_pos[t].iloc[d, 1], 2)
            short_next = round(short_pos[t].iloc[d, 1] - short_far , 2)
            long_far = round((d+1)/days * short_pos[t].iloc[d, 2], 2)
            long_next = round(short_pos[t].iloc[d, 2] - long_far ,2)
            total_pos.append([long_next,long_far,short_next,short_far])
            #short_pos[t].iloc[d, 3] = str(total_pos)

    short_pos['bal_pos'] = total_pos
    #short_pos.to_csv('Position_chg.csv')
    total_pos = np.array(total_pos)

    # short_pos['long_next'] = total_pos[:,0]
    # short_pos['long_far'] = total_pos[:, 1]
    # short_pos['short_next'] = total_pos[:, 2]
    # short_pos['short_far'] = total_pos[:, 3]
    # # short_pos.to_csv('exp.csv')
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
    data_test(price,total_pos)
main()
