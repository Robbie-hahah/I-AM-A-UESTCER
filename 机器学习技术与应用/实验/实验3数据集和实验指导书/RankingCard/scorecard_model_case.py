# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 23:03:47 2019
@author: dell
"""

'''
SeriousDlqin2yrs 出现 90 天或更长时间的逾期行为（即定义好坏客户）
RevolvingUtilizationOfUnsecuredLines 贷款以及信用卡可用额度与总额度比例
age 借款人借款年龄
NumberOfTime30-59DaysPastDueNotWorse 过去两年内出现35-59天逾期但是没有发展得更坏的次数
DebtRatio 每月偿还债务，赡养费，生活费用除以月总收入
MonthlyIncome 月收入
NumberOfOpenCreditLinesAndLoans 开放式贷款和信贷数量
NumberOfTimes90DaysLate 过去两年内出现90天逾期或更坏的次数
NumberRealEstateLoansOrLines 抵押贷款和房地产贷款数量，包括房屋净值信贷额度
NumberOfTime60-89DaysPastDueNotWorse 过去两年内出现60-89天逾期但是没有发展得更坏的次数
NumberOfDependents 家庭中不包括自身的家属人数（配偶，子女等）
'''

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression as LR
import matplotlib.pyplot as plt
import seaborn as sns

data = pd.read_csv(r"rankingcard.csv", index_col=0)

# In[]:
# 1.1、特征类型 Column Types
print("特征样本数量: ")
print(data.dtypes.value_counts())

# In[]:
# 1.2、重复值
print("重复项按特征统计: ")
print(data[data.duplicated()].count())
# 去除重复项
nodup = data[-data.duplicated()]
print(len(nodup))
# 去除重复项
print(len(data.drop_duplicates()))
# 重复项
print(len(data) - len(nodup))

data.drop_duplicates(inplace=True)
print(data.info())  # Int64Index: 149391 entries, 1 to 150000

# 重设索引
data = data.reset_index(drop=True)
# data.index = range(data.shape[0])
print(data.info())  # RangeIndex: 149391 entries, 0 to 149390


# In[]:
# 1.3、缺失值 Examine Missing Values
# Function to calculate missing values by column# Funct
def missing_values_table(df):
    # Total missing values
    mis_val = df.isnull().sum()

    # Percentage of missing values
    mis_val_percent = 100 * mis_val / len(df)

    # Make a table with the results
    mis_val_table = pd.concat([mis_val, mis_val_percent], axis=1)

    # Rename the columns
    mis_val_table_ren_columns = mis_val_table.rename(
        columns={0: 'Missing Values', 1: '% of Total Values'})

    # Sort the table by percentage of missing descending
    mis_val_table_ren_columns = mis_val_table_ren_columns[
        mis_val_table_ren_columns.iloc[:, 1] != 0].sort_values(
        '% of Total Values', ascending=False).round(1)

    # Print some summary information
    print("Your selected dataframe has " + str(df.shape[1]) + " columns.\n"
                                                              "There are " + str(mis_val_table_ren_columns.shape[0]) +
          " columns that have missing values.")

    # Return the dataframe with missing information
    return mis_val_table_ren_columns


# Missing values statistics
missing_values = missing_values_table(data)
missing_values.head(20)

# In[]:
# 1.3.1、填充家庭人数 NumberOfDependents（不太重要的，就用均值填充）
data['NumberOfDependents'].fillna(data['NumberOfDependents'].mean(), inplace=True)


# from sklearn.preprocessing import Imputer
# imp = Imputer(missing_values='NaN', strategy='mean', axis=0)
# data['NumberOfDependents'] = imp.fit_transform(data[['NumberOfDependents']].values)

# In[]:
# 1.3.2、填充月收入（随机森林）
def fill_missing_rf(X, y, to_fill):
    """
    使用随机森林填补一个特征的缺失值的函数
    参数：
    X：要填补的特征矩阵
    y：完整的，没有缺失值的标签
    to_fill：字符串，要填补的那一列的名称
    """

    # 构建我们的新特征矩阵和新标签
    df = X.copy()
    fill = df.loc[:, to_fill]
    df = pd.concat([df.loc[:, df.columns != to_fill], pd.DataFrame(y)], axis=1)

    # 找出我们的训练集和测试集
    Ytrain = fill[fill.notnull()]
    Ytest = fill[fill.isnull()]
    Xtrain = df.iloc[Ytrain.index, :]
    Xtest = df.iloc[Ytest.index, :]

    # 用随机森林回归来填补缺失值
    from sklearn.ensemble import RandomForestRegressor as rfr
    rfr = rfr(n_estimators=100)  # random_state=0,n_estimators=200,max_depth=3,n_jobs=-1
    rfr = rfr.fit(Xtrain, Ytrain)
    Ypredict = rfr.predict(Xtest)

    return Ypredict


# In[]:
X = data.iloc[:, 1:]
y = data["SeriousDlqin2yrs"]  # y = data.iloc[:,0]
X.shape  # (149391, 10)
y_pred = fill_missing_rf(X, y, "MonthlyIncome")

# 通过以下代码检验数据是否数量相同
temp_b = (y_pred.shape == data.loc[data.loc[:, "MonthlyIncome"].isnull(), "MonthlyIncome"].shape)
# 确认我们的结果合理之后，我们就可以将数据覆盖了
if temp_b:
    data.loc[data.loc[:, "MonthlyIncome"].isnull(), "MonthlyIncome"] = y_pred

data.info()

# In[]:
# 1.4、异常值检测： 描述性统计
# data.describe()
temp_desc = data.describe([0.01, 0.1, 0.25, .5, .75, .9, .99]).T
print(temp_desc[['min', 'max']])
temp_desc.to_csv("temp_desc.csv")

# In[]:
# 直方图、箱线图：
'''
v_feat = data.ix[:,1:].columns
f, axes = plt.subplots(10,2, figsize=(20, 28*2))
for i, cn in enumerate(data[v_feat]):
    print(i, cn)
    sns.distplot(data[cn], bins=100, color='green', ax=axes[i][0])
#    sns.distplot(data[cn][data["SeriousDlqin2yrs"] == 1], bins=100, color='red', ax=axes[i][0])
#    sns.distplot(data[cn][data["SeriousDlqin2yrs"] == 0], bins=100, color='blue', ax=axes[i][0])
    axes[i][0].set_title('histogram of feature: ' + str(cn))
    axes[i][0].set_xlabel('')

    sns.boxplot(y=cn, data=data, ax=axes[i][1])
    axes[i][1].set_title('box of feature: ' + str(cn))
    axes[i][1].set_ylabel('')
'''
# In[]:
# 1.4.1、可用额度比值特征分布
f, axes = plt.subplots(2, 2, figsize=(16, 13))
sns.distplot(data['RevolvingUtilizationOfUnsecuredLines'], bins=100, color='green', ax=axes[0][0])
axes[0][0].set_title('histogram of feature: ' + str('RevolvingUtilizationOfUnsecuredLines'))
axes[0][0].set_xlabel('')

sns.boxplot(y='RevolvingUtilizationOfUnsecuredLines', data=data, ax=axes[0][1])
axes[0][1].set_title('box of feature: ' + str('RevolvingUtilizationOfUnsecuredLines'))
axes[0][1].set_ylabel('')

sns.distplot(data['RevolvingUtilizationOfUnsecuredLines'][data["SeriousDlqin2yrs"] == 1], bins=100, color='red',
             ax=axes[1][0])
sns.distplot(data['age'][data["SeriousDlqin2yrs"] == 0], bins=100, color='blue', ax=axes[1][0])
axes[1][0].set_title('histogram of feature: ' + str('RevolvingUtilizationOfUnsecuredLines'))
axes[1][0].set_xlabel('')

sns.boxplot(x='SeriousDlqin2yrs', y='RevolvingUtilizationOfUnsecuredLines', data=data, ax=axes[1][1])
axes[1][1].set_title('box of feature: ' + str('RevolvingUtilizationOfUnsecuredLines'))
axes[1][1].set_ylabel('')
# In[]:
# 1.4.2、年龄分布
f, axes = plt.subplots(2, 2, figsize=(16, 13))
sns.distplot(data['age'], bins=100, color='green', ax=axes[0][0])
axes[0][0].set_title('histogram of feature: ' + str('age'))
axes[0][0].set_xlabel('')

sns.boxplot(y='age', data=data, ax=axes[0][1])
axes[0][1].set_title('box of feature: ' + str('age'))
axes[0][1].set_ylabel('')

sns.distplot(data['age'][data["SeriousDlqin2yrs"] == 1], bins=100, color='red', ax=axes[1][0])
sns.distplot(data['age'][data["SeriousDlqin2yrs"] == 0], bins=100, color='blue', ax=axes[1][0])
axes[1][0].set_title('histogram of feature: ' + str('age'))
axes[1][0].set_xlabel('')

sns.boxplot(x='SeriousDlqin2yrs', y='age', data=data, ax=axes[1][1])
axes[1][1].set_title('box of feature: ' + str('age'))
axes[1][1].set_ylabel('')
# In[]:
# 1.4.3、逾期30-59天 | 60-89天 | 90天笔数分布：
f, [[ax1, ax2], [ax3, ax4], [ax5, ax6]] = plt.subplots(3, 2, figsize=(15, 15))
sns.distplot(data['NumberOfTime30-59DaysPastDueNotWorse'], ax=ax1)
sns.boxplot(y='NumberOfTime30-59DaysPastDueNotWorse', data=data, ax=ax2)
sns.distplot(data['NumberOfTime60-89DaysPastDueNotWorse'], ax=ax3)
sns.boxplot(y='NumberOfTime60-89DaysPastDueNotWorse', data=data, ax=ax4)
sns.distplot(data['NumberOfTimes90DaysLate'], ax=ax5)
sns.boxplot(y='NumberOfTimes90DaysLate', data=data, ax=ax6)
plt.show()

# In[]:
# 1.4.4、负债率特征分布
f, axes = plt.subplots(2, 2, figsize=(16, 13))
sns.distplot(data['DebtRatio'], bins=100, color='green', ax=axes[0][0])
axes[0][0].set_title('histogram of feature: ' + str('DebtRatio'))
axes[0][0].set_xlabel('')

sns.boxplot(y='DebtRatio', data=data, ax=axes[0][1])
axes[0][1].set_title('box of feature: ' + str('DebtRatio'))
axes[0][1].set_ylabel('')

sns.distplot(data['DebtRatio'][data["SeriousDlqin2yrs"] == 1], bins=100, color='red', ax=axes[1][0])
sns.distplot(data['DebtRatio'][data["SeriousDlqin2yrs"] == 0], bins=100, color='blue', ax=axes[1][0])
axes[1][0].set_title('histogram of feature: ' + str('DebtRatio'))
axes[1][0].set_xlabel('')

sns.boxplot(x='SeriousDlqin2yrs', y='DebtRatio', data=data, ax=axes[1][1])
axes[1][1].set_title('box of feature: ' + str('DebtRatio'))
axes[1][1].set_ylabel('')
# In[]:
# 1.4.5、信贷数量特征分布
f, axes = plt.subplots(2, 2, figsize=(16, 13))
sns.distplot(data['NumberOfOpenCreditLinesAndLoans'], bins=100, color='green', ax=axes[0][0])
axes[0][0].set_title('histogram of feature: ' + str('NumberOfOpenCreditLinesAndLoans'))
axes[0][0].set_xlabel('')

sns.boxplot(y='NumberOfOpenCreditLinesAndLoans', data=data, ax=axes[0][1])
axes[0][1].set_title('box of feature: ' + str('NumberOfOpenCreditLinesAndLoans'))
axes[0][1].set_ylabel('')

sns.distplot(data['NumberOfOpenCreditLinesAndLoans'][data["SeriousDlqin2yrs"] == 1], bins=100, color='red',
             ax=axes[1][0])
sns.distplot(data['NumberOfOpenCreditLinesAndLoans'][data["SeriousDlqin2yrs"] == 0], bins=100, color='blue',
             ax=axes[1][0])
axes[1][0].set_title('histogram of feature: ' + str('NumberOfOpenCreditLinesAndLoans'))
axes[1][0].set_xlabel('')

sns.boxplot(x='SeriousDlqin2yrs', y='NumberOfOpenCreditLinesAndLoans', data=data, ax=axes[1][1])
axes[1][1].set_title('box of feature: ' + str('NumberOfOpenCreditLinesAndLoans'))
axes[1][1].set_ylabel('')
# In[]:
# 1.4.6、固定资产贷款数量
f, axes = plt.subplots(2, 2, figsize=(16, 13))
sns.distplot(data['NumberRealEstateLoansOrLines'], bins=100, color='green', ax=axes[0][0])
axes[0][0].set_title('histogram of feature: ' + str('NumberRealEstateLoansOrLines'))
axes[0][0].set_xlabel('')

sns.boxplot(y='NumberRealEstateLoansOrLines', data=data, ax=axes[0][1])
axes[0][1].set_title('box of feature: ' + str('NumberRealEstateLoansOrLines'))
axes[0][1].set_ylabel('')

sns.distplot(data['NumberRealEstateLoansOrLines'][data["SeriousDlqin2yrs"] == 1], bins=100, color='red', ax=axes[1][0])
sns.distplot(data['NumberRealEstateLoansOrLines'][data["SeriousDlqin2yrs"] == 0], bins=100, color='blue', ax=axes[1][0])
axes[1][0].set_title('histogram of feature: ' + str('NumberRealEstateLoansOrLines'))
axes[1][0].set_xlabel('')

sns.boxplot(x='SeriousDlqin2yrs', y='NumberRealEstateLoansOrLines', data=data, ax=axes[1][1])
axes[1][1].set_title('box of feature: ' + str('NumberRealEstateLoansOrLines'))
axes[1][1].set_ylabel('')
# In[]:
# 1.4.7、家属数量分布
f, axes = plt.subplots(2, 2, figsize=(16, 13))
sns.distplot(data['NumberOfDependents'], bins=100, color='green', ax=axes[0][0])
axes[0][0].set_title('histogram of feature: ' + str('NumberOfDependents'))
axes[0][0].set_xlabel('')

sns.boxplot(y='NumberOfDependents', data=data, ax=axes[0][1])
axes[0][1].set_title('box of feature: ' + str('NumberOfDependents'))
axes[0][1].set_ylabel('')

sns.distplot(data['NumberOfDependents'][data["SeriousDlqin2yrs"] == 1], bins=100, color='red', ax=axes[1][0])
sns.distplot(data['NumberOfDependents'][data["SeriousDlqin2yrs"] == 0], bins=100, color='blue', ax=axes[1][0])
axes[1][0].set_title('histogram of feature: ' + str('NumberOfDependents'))
axes[1][0].set_xlabel('')

sns.boxplot(x='SeriousDlqin2yrs', y='NumberOfDependents', data=data, ax=axes[1][1])
axes[1][1].set_title('box of feature: ' + str('NumberOfDependents'))
axes[1][1].set_ylabel('')
# In[]:
# 1.4.8、月收入分布
f, axes = plt.subplots(2, 2, figsize=(16, 13))
sns.distplot(data['MonthlyIncome'], bins=100, color='green', ax=axes[0][0])
axes[0][0].set_title('histogram of feature: ' + str('MonthlyIncome'))
axes[0][0].set_xlabel('')

sns.boxplot(y='MonthlyIncome', data=data, ax=axes[0][1])
axes[0][1].set_title('box of feature: ' + str('MonthlyIncome'))
axes[0][1].set_ylabel('')

sns.distplot(data['MonthlyIncome'][data["SeriousDlqin2yrs"] == 1], bins=100, color='red', ax=axes[1][0])
sns.distplot(data['MonthlyIncome'][data["SeriousDlqin2yrs"] == 0], bins=100, color='blue', ax=axes[1][0])
axes[1][0].set_title('histogram of feature: ' + str('MonthlyIncome'))
axes[1][0].set_xlabel('')

sns.boxplot(x='SeriousDlqin2yrs', y='MonthlyIncome', data=data, ax=axes[1][1])
axes[1][1].set_title('box of feature: ' + str('MonthlyIncome'))
axes[1][1].set_ylabel('')

# In[]:
# 异常值也被我们观察到，年龄的最小值居然有0，这不符合银行的业务需求，即便是儿童账户也要至少8岁，我们可以
# 查看一下年龄为0的人有多少
(data["age"] == 0).sum()
# 发现只有一个人年龄为0，可以判断这肯定是录入失误造成的，可以当成是缺失值来处理，直接删除掉这个样本
data = data[data["age"] != 0]

"""
另外，有三个指标看起来很奇怪：
"NumberOfTime30-59DaysPastDueNotWorse"
"NumberOfTime60-89DaysPastDueNotWorse"
"NumberOfTimes90DaysLate"
这三个指标分别是“过去两年内出现35-59天逾期但是没有发展的更坏的次数”，“过去两年内出现60-89天逾期但是没
有发展的更坏的次数”,“过去两年内出现90天逾期的次数”。这三个指标，在99%的分布的时候依然是2，最大值却是
98，看起来非常奇怪。一个人在过去两年内逾期35~59天98次，一年6个60天，两年内逾期98次这是怎么算出来的？
我们可以去咨询业务人员，请教他们这个逾期次数是如何计算的。如果这个指标是正常的，那这些两年内逾期了98次的
客户，应该都是坏客户。在我们无法询问他们情况下，我们查看一下有多少个样本存在这种异常：
"""
print(data['NumberOfTime30-59DaysPastDueNotWorse'].value_counts())
print(data['NumberOfTime60-89DaysPastDueNotWorse'].value_counts())
print(data['NumberOfTimes90DaysLate'].value_counts())

# 有225个样本存在这样的情况，并且这些样本，我们观察一下，标签并不都是1，他们并不都是坏客户。因此，我们基
# 本可以判断，这些样本是某种异常，应该把它们删除。
print(data.loc[data['NumberOfTime30-59DaysPastDueNotWorse'] >= 90, 'SeriousDlqin2yrs'].value_counts())
print(data.loc[data['NumberOfTime60-89DaysPastDueNotWorse'] >= 90, 'SeriousDlqin2yrs'].value_counts())
print(data.loc[data['NumberOfTimes90DaysLate'] >= 90, 'SeriousDlqin2yrs'].value_counts())

# 删除异常值
data = data[data.loc[:, "NumberOfTime30-59DaysPastDueNotWorse"] < 90]
data = data[data.loc[:, "NumberOfTime60-89DaysPastDueNotWorse"] < 90]
data = data[data.loc[:, "NumberOfTimes90DaysLate"] < 90]
# 一定要恢复索引
data.index = range(data.shape[0])
data.info()

# In[]:
# 1.5、为什么不统一量纲，也不标准化数据分布？
'''
一旦我们将数据统一量纲，或者标准化了之后，数据大小和范围都会改变，统计结果是漂亮了，但是对于业务人员
来说，他们完全无法理解，标准化后的年龄在0.00328~0.00467之间为一档是什么含义。并且，新客户填写的信
息，天生就是量纲不统一的，我们的确可以将所有的信息录入之后，统一进行标准化，然后导入算法计算，但是最
终落到业务人员手上去判断的时候，他们会完全不理解为什么录入的信息变成了一串统计上很美但实际上根本看不
懂的数字。由于业务要求，在制作评分卡的时候，我们要尽量保持数据的原貌，年龄就是8~110的数字，收入就是
大于0，最大值可以无限的数字，即便量纲不统一，我们也不对数据进行标准化处理。
'''

# In[]:
# 1.6、样本不均衡：
print(data.shape)  # (150000, 11)
print(data.info())

print('No Default', round(len(data[data.SeriousDlqin2yrs == 0]) / len(data) * 100, 2), "% of the dataset")
print('Default', round(len(data[data.SeriousDlqin2yrs == 1]) / len(data) * 100, 2), "% of the dataset")

# 查看目标列Y的情况
print(data.groupby('SeriousDlqin2yrs').size())
print(data['SeriousDlqin2yrs'].value_counts())

# 目标变量Y分布可视化
fig, axs = plt.subplots(1, 2, figsize=(14, 7))

sns.countplot(x='SeriousDlqin2yrs', data=data, ax=axs[0])  # 柱状图
axs[0].set_title("Frequency of each TARGET")

data['SeriousDlqin2yrs'].value_counts().plot(x=None, y=None, kind='pie', ax=axs[1], autopct='%1.2f%%')  # 饼图
axs[1].set_title("Percentage of each TARGET")
plt.show()

# In[]:
# 1.7、上采样：
import imblearn
from imblearn.over_sampling import SMOTE

X_temp = data.iloc[:, 1:]
y_temp = data["SeriousDlqin2yrs"]  # y = data.iloc[:,0]

sm = SMOTE(random_state=42)  # 实例化
X, y = sm.fit_sample(X_temp, y_temp)

n_sample_ = X.shape[0]  # 278584
pd.Series(y).value_counts()
n_1_sample = pd.Series(y).value_counts()[1]
n_0_sample = pd.Series(y).value_counts()[0]
print('样本个数：{}; 1占{:.2%}; 0占{:.2%}'.format(n_sample_, n_1_sample / n_sample_, n_0_sample / n_sample_))
# 样本个数：278584; 1占50.00%; 0占50.00%

# In[]:
# 上采样之后，切分训练集、测试集； 保存 前期处理 结果
from sklearn.model_selection import train_test_split

X = pd.DataFrame(X)
y = pd.DataFrame(y)

X_train, X_vali, Y_train, Y_vali = train_test_split(X, y, test_size=0.3, random_state=420)
model_data = pd.concat([Y_train, X_train], axis=1)  # 训练数据构建模型
model_data.index = range(model_data.shape[0])
model_data.columns = data.columns

vali_data = pd.concat([Y_vali, X_vali], axis=1)  # 验证集
vali_data.index = range(vali_data.shape[0])
vali_data.columns = data.columns

n_sample_ = len(Y_train)
n_1_sample = Y_train.iloc[:, 0].value_counts()[1]
n_0_sample = Y_train.iloc[:, 0].value_counts()[0]
print('样本个数：{}; 1占{:.2%}; 0占{:.2%}'.format(n_sample_, n_1_sample / n_sample_, n_0_sample / n_sample_))

n_sample_ = len(Y_vali)
n_1_sample = Y_vali.iloc[:, 0].value_counts()[1]
n_0_sample = Y_vali.iloc[:, 0].value_counts()[0]
print('样本个数：{}; 1占{:.2%}; 0占{:.2%}'.format(n_sample_, n_1_sample / n_sample_, n_0_sample / n_sample_))

print(model_data.shape)  # (195008, 11)
print(vali_data.shape)  # (83576, 11)
model_data.to_csv(r"model_data.csv") # 训练数据
vali_data.to_csv(r"vali_data.csv") # 验证数据
# In[]:
model_data = pd.read_csv(r"model_data.csv")
vali_data = pd.read_csv("vali_data.csv")
print(model_data.shape)  # (195008, 12)
print(vali_data.shape)  # (83576, 12)
model_data.drop('Unnamed: 0', inplace=True, axis=1)
vali_data.drop('Unnamed: 0', inplace=True, axis=1)
print(model_data.shape)  # (195008, 11)
print(vali_data.shape)  # (83576, 11)

# In[]
# 1.8、分箱：
# 1.8.1、按照 等频 对需要分箱的列进行分箱
model_data["qcut"], updown = pd.qcut(model_data["age"], retbins=True, q=20)  # 等频分箱
"""
pd.qcut，基于分位数的分箱函数，本质是将连续型变量离散化
只能够处理一维数据。返回箱子的上限和下限
参数q： 要分箱的个数
参数retbins=True： 返回箱子上下限数组
"""
# 在这里时让model_data新添加一列叫做“分箱”，这一列其实就是每个样本所对应的箱子
print(model_data["qcut"].value_counts())
# 所有箱子的上限和下限
print(updown)

# In[]:
# 1.8.2、统计每个分箱中0和1的数量（这里使用了数据透视表的功能groupby）
coount_y0 = model_data[model_data["SeriousDlqin2yrs"] == 0].groupby(by="qcut").count()["SeriousDlqin2yrs"]
coount_y1 = model_data[model_data["SeriousDlqin2yrs"] == 1].groupby(by="qcut").count()["SeriousDlqin2yrs"]

# num_bins值分别为每个区间的上界，下界，0出现的次数，1出现的次数
num_bins = [*zip(updown, updown[1:], coount_y0, coount_y1)]
# 注意zip会按照最短列来进行结合
print(num_bins)

# In[]：
# 1.8.3、确保每个箱中都有0和1 （看不懂）
for i in range(20):  # 20个箱子
    # 如果第一个组没有包含正样本或负样本，向后合并
    if 0 in num_bins[0][2:]:
        num_bins[0:2] = [(
            num_bins[0][0],
            num_bins[1][1],
            num_bins[0][2] + num_bins[1][2],
            num_bins[0][3] + num_bins[1][3])]
        continue

    """
    合并了之后，第一行的组是否一定有两种样本了呢？不一定
    如果原本的第一组和第二组都没有包含正样本，或者都没有包含负样本，那即便合并之后，第一行的组也还是没有
    包含两种样本
    所以我们在每次合并完毕之后，还需要再检查，第一组是否已经包含了两种样本
    这里使用continue跳出了本次循环，开始下一次循环，所以回到了最开始的for i in range(20), 让i+1
    这就跳过了下面的代码，又从头开始检查，第一组是否包含了两种样本
    如果第一组中依然没有包含两种样本，则if通过，继续合并，每合并一次就会循环检查一次，最多合并20次
    如果第一组中已经包含两种样本，则if不通过，就开始执行下面的代码
    """
    # 已经确认第一组中肯定包含两种样本了，如果其他组没有包含两种样本，就向前合并
    # 此时的num_bins已经被上面的代码处理过，可能被合并过，也可能没有被合并
    # 但无论如何，我们要在num_bins中遍历，所以写成in range(len(num_bins))
    for i in range(len(num_bins)):
        if 0 in num_bins[i][2:]:
            num_bins[i - 1:i + 1] = [(
                num_bins[i - 1][0],
                num_bins[i][1],
                num_bins[i - 1][2] + num_bins[i][2],
                num_bins[i - 1][3] + num_bins[i][3])]
        break
        # 如果对第一组和对后面所有组的判断中，都没有进入if去合并，则提前结束所有的循环
    else:
        break

    """
    这个break，只有在if被满足的条件下才会被触发
    也就是说，只有发生了合并，才会打断for i in range(len(num_bins))这个循环
    为什么要打断这个循环？因为我们是在range(len(num_bins))中遍历
    但合并发生后，len(num_bins)发生了改变，但循环却不会重新开始
    举个例子，本来num_bins是5组，for i in range(len(num_bins))在第一次运行的时候就等于for i in 
    range(5)
    range中输入的变量会被转换为数字，不会跟着num_bins的变化而变化，所以i会永远在[0,1,2,3,4]中遍历
    进行合并后，num_bins变成了4组，已经不存在=4的索引了，但i却依然会取到4，循环就会报错
    因此在这里，一旦if被触发，即一旦合并发生，我们就让循环被破坏，使用break跳出当前循环
    循环就会回到最开始的for i in range(20)中
    此时判断第一组是否有两种标签的代码不会被触发，但for i in range(len(num_bins))却会被重新运行
    这样就更新了i的取值，循环就不会报错了
    """


# In[]:
# 1.8.4、计算WOE和BAD RATE
# BAD RATE是一个箱中，坏的样本占一个箱子里边所有样本数的比例 (bad/total)
# 而bad%是一个箱中的坏样本占整个特征中的坏样本的比例
def get_woe(num_bins):
    # 通过 num_bins 数据计算 woe
    columns = ["min", "max", "count_0", "count_1"]
    df = pd.DataFrame(num_bins, columns=columns)

    df["total"] = df.count_0 + df.count_1  # 一个箱子当中所有的样本数： 按列相加
    df["percentage"] = df.total / df.total.sum()  # 一个箱子里的样本数，占所有样本的比例
    df["bad_rate"] = df.count_1 / df.total  # 一个箱子坏样本的数量占一个箱子里边所有样本数的比例
    df["good%"] = df.count_0 / df.count_0.sum()
    df["bad%"] = df.count_1 / df.count_1.sum()
    df["woe"] = np.log(df["good%"] / df["bad%"])
    return df


# 计算IV值
def get_iv(df):
    rate = df["good%"] - df["bad%"]
    iv = np.sum(rate * df.woe)
    return iv


# In[]:
# 1.8.5、卡方检验，合并箱体，画出IV曲线
num_bins_ = num_bins.copy()

import matplotlib.pyplot as plt
import scipy

IV = []
axisx = []
PV = []

while len(num_bins_) > 2:  # 大于设置的最低分箱个数
    pvs = []
    # 获取 num_bins_两两之间的卡方检验的置信度（或卡方值）
    for i in range(len(num_bins_) - 1):
        x1 = num_bins_[i][2:]
        x2 = num_bins_[i + 1][2:]
        # 0 返回 chi2 值，1 返回 p 值。
        pv = scipy.stats.chi2_contingency([x1, x2])[1]  # p值
        # chi2 = scipy.stats.chi2_contingency([x1,x2])[0] # 计算卡方值
        pvs.append(pv)

    # 通过 卡方p值 进行处理。 合并 卡方p值 最大的两组
    i = pvs.index(max(pvs))
    num_bins_[i:i + 2] = [(
        num_bins_[i][0],
        num_bins_[i + 1][1],
        num_bins_[i][2] + num_bins_[i + 1][2],
        num_bins_[i][3] + num_bins_[i + 1][3])]

    bins_df = get_woe(num_bins_)
    axisx.append(len(num_bins_))
    IV.append(get_iv(bins_df))
    PV.append(max(pvs))  # 卡方p值

plt.figure()
plt.plot(axisx, IV)
# plt.plot(axisx,PV)
plt.xticks(axisx)
plt.xlabel("number of box")
plt.ylabel("IV")
plt.show()
# 选择转折点处，也就是下坠最快的折线点，6→5折线点最陡峭，所以这里对于age来说选择箱数为6
# In[]:
import scipy

num_bins_ = num_bins.copy()
x1 = num_bins_[0][2:]  # (0:4243, 1:6052)
x2 = num_bins_[0 + 1][2:]  # (0:3571, 1:5635)
# 0 返回 chi2 值，1 返回 p 值。
pv = scipy.stats.chi2_contingency([x1, x2])[1]  # p值 0.0005943767678537757
chi2 = scipy.stats.chi2_contingency([x1, x2])[0]  # 计算卡方值 11.793506471136046


# In[]:
# 1.8.6、合并箱体 函数：
def get_bin(num_bins_, n):
    while len(num_bins_) > n:
        pvs = []
        for i in range(len(num_bins_) - 1):
            x1 = num_bins_[i][2:]
            x2 = num_bins_[i + 1][2:]
            pv = scipy.stats.chi2_contingency([x1, x2])[1]
            # chi2 = scipy.stats.chi2_contingency([x1,x2])[0]
            pvs.append(pv)

        i = pvs.index(max(pvs))
        num_bins_[i:i + 2] = [(
            num_bins_[i][0],
            num_bins_[i + 1][1],
            num_bins_[i][2] + num_bins_[i + 1][2],
            num_bins_[i][3] + num_bins_[i + 1][3])]
    return num_bins_


afterbins = num_bins.copy()
get_bin(afterbins, 6)

# In[]:
# 希望每组的bad_rate相差越大越好；
# woe差异越大越好，应该具有单调性，随着箱的增加，要么由正到负，要么由负到正，只能有一个转折过程；
# 如果woe值大小变化是有两个转折，比如呈现w型，证明分箱过程有问题
# num_bins保留的信息越多越好
bins_df = get_woe(afterbins)
print(bins_df)


# In[]:
# 1.8.6、将选取最佳分箱个数的过程包装为函数 （所有功能函数）
def graphforbestbin(DF, X, Y, n=5, q=20, graph=True):
    '''
    自动最优分箱函数，基于卡方检验的分箱
    参数：
    DF: 需要输入的数据
    X: 需要分箱的列名
    Y: 分箱数据对应的标签 Y 列名
    n: 保留分箱个数
    q: 初始分箱的个数
    graph: 是否要画出IV图像
    区间为前开后闭 (]
    '''

    DF = DF[[X, Y]].copy()

    DF["qcut"], bins = pd.qcut(DF[X], retbins=True, q=q, duplicates="drop")
    coount_y0 = DF.loc[DF[Y] == 0].groupby(by="qcut").count()[Y]
    coount_y1 = DF.loc[DF[Y] == 1].groupby(by="qcut").count()[Y]
    num_bins = [*zip(bins, bins[1:], coount_y0, coount_y1)]

    for i in range(q):
        if 0 in num_bins[0][2:]:
            num_bins[0:2] = [(
                num_bins[0][0],
                num_bins[1][1],
                num_bins[0][2] + num_bins[1][2],
                num_bins[0][3] + num_bins[1][3])]
            continue

        for i in range(len(num_bins)):
            if 0 in num_bins[i][2:]:
                num_bins[i - 1:i + 1] = [(
                    num_bins[i - 1][0],
                    num_bins[i][1],
                    num_bins[i - 1][2] + num_bins[i][2],
                    num_bins[i - 1][3] + num_bins[i][3])]
                break
        else:
            break

    def get_woe(num_bins):
        columns = ["min", "max", "count_0", "count_1"]
        df = pd.DataFrame(num_bins, columns=columns)
        df["total"] = df.count_0 + df.count_1
        df["percentage"] = df.total / df.total.sum()
        df["bad_rate"] = df.count_1 / df.total
        df["good%"] = df.count_0 / df.count_0.sum()
        df["bad%"] = df.count_1 / df.count_1.sum()
        df["woe"] = np.log(df["good%"] / df["bad%"])
        return df

    def get_iv(df):
        rate = df["good%"] - df["bad%"]
        iv = np.sum(rate * df.woe)
        return iv

    IV = []
    axisx = []
    while len(num_bins) > n:
        pvs = []
        for i in range(len(num_bins) - 1):
            x1 = num_bins[i][2:]
            x2 = num_bins[i + 1][2:]
            pv = scipy.stats.chi2_contingency([x1, x2])[1]
            pvs.append(pv)

        i = pvs.index(max(pvs))
        num_bins[i:i + 2] = [(
            num_bins[i][0],
            num_bins[i + 1][1],
            num_bins[i][2] + num_bins[i + 1][2],
            num_bins[i][3] + num_bins[i + 1][3])]

        bins_df = pd.DataFrame(get_woe(num_bins))
        axisx.append(len(num_bins))
        IV.append(get_iv(bins_df))

    if graph:
        plt.figure()
        plt.plot(axisx, IV)
        plt.xticks(axisx)
        plt.xlabel("number of box")
        plt.ylabel("IV")
        plt.show()
    return bins_df


# In[]:
# 测试：
# print(model_data.columns)
# for i in model_data.columns[1:-1]:
#    print(i)
#    graphforbestbin(model_data,i,"SeriousDlqin2yrs",n=2,q=20)

# In[]:
auto_col_bins = {"RevolvingUtilizationOfUnsecuredLines": 6,
                 "age": 6,
                 "DebtRatio": 4,
                 "MonthlyIncome": 3,
                 "NumberOfOpenCreditLinesAndLoans": 5}

# 不能使用自动分箱的变量
hand_bins = {"NumberOfTime30-59DaysPastDueNotWorse": [0, 1, 2, 13]
    , "NumberOfTimes90DaysLate": [0, 1, 2, 17]
    , "NumberRealEstateLoansOrLines": [0, 1, 2, 4, 54]
    , "NumberOfTime60-89DaysPastDueNotWorse": [0, 1, 2, 8]
    , "NumberOfDependents": [0, 1, 2, 3]}

# 保证区间覆盖使用 np.inf替换最大值，用-np.inf替换最小值
# 原因：比如一些新的值出现，例如家庭人数为30，以前没出现过，改成范围为极大值之后，这些新值就都能分到箱里边了
hand_bins = {k: [-np.inf, *v[:-1], np.inf] for k, v in hand_bins.items()}

# In[]:
bins_of_col = {}
# 生成自动分箱的分箱区间和分箱后的 IV 值
for col in auto_col_bins:
    print(col)
    bins_df_temp = graphforbestbin(model_data, col
                                   , "SeriousDlqin2yrs"
                                   , n=auto_col_bins[col]
                                   # 使用字典的性质来取出每个特征所对应的箱的数量
                                   , q=20
                                   , graph=True)
    bins_list = sorted(set(bins_df_temp["min"]).union(bins_df_temp["max"]))
    # 保证区间覆盖使用 np.inf 替换最大值 -np.inf 替换最小值
    bins_list[0], bins_list[-1] = -np.inf, np.inf
    bins_of_col[col] = bins_list

# 合并手动分箱数据
bins_of_col.update(hand_bins)
bins_of_col

# In[]:
# 测试
# 函数pd.cut，可以根据已知的分箱间隔把数据分箱
# 参数为 pd.cut(数据，以列表表示的分箱间隔)
data = model_data[["age", "SeriousDlqin2yrs"]].copy()
data["cut"] = pd.cut(data["age"], bins_of_col['age'])

# 将数据按分箱结果聚合，并取出其中的标签值
data.groupby("cut")["SeriousDlqin2yrs"].value_counts()

# 使用unstack()来将树状结构变成表状结构
bins_df = data.groupby("cut")["SeriousDlqin2yrs"].value_counts().unstack()
woe = bins_df["woe"] = np.log((bins_df[0] / bins_df[0].sum()) / (bins_df[1] / bins_df[1].sum()))
print(woe)


# In[]:
# 单独计算出woe： 因为测试集映射数据时使用的是训练集的WOE值（测试集不能使用Y值的）
def get_woe(data, col, y, bins):
    df = data[[col, y]].copy()
    df["cut"] = pd.cut(df[col], bins)
    bins_df = df.groupby("cut")[y].value_counts().unstack()
    woe = bins_df["woe"] = np.log((bins_df[0] / bins_df[0].sum()) / (bins_df[1] / bins_df[1].sum()))
    return woe


# 将所有特征的WOE存储到字典当中
woeall = {}
for col in bins_of_col:
    woeall[col] = get_woe(model_data, col, "SeriousDlqin2yrs", bins_of_col[col])

woeall

# In[]:
# 训练集 WOE数据 映射：
model_woe = pd.DataFrame(index=model_data.index)

# 将原数据分箱后，按箱的结果把WOE结构用map函数映射到数据中
# model_woe["age"] = pd.cut(model_data["age"],bins_of_col["age"]).map(woeall["age"])

# 对所有特征操作可以写成：
for col in bins_of_col:
    model_woe[col] = pd.cut(model_data[col], bins_of_col[col]).map(woeall[col])

# 将标签补充到数据中
model_woe["SeriousDlqin2yrs"] = model_data["SeriousDlqin2yrs"]
# 这就是我们的建模数据了
model_woe.to_csv(r"model_woe.csv")

# In[]:
# 测试集 WOE数据 映射：
vali_woe = pd.DataFrame(index=vali_data.index)
# 只能用训练集的WOE， 不能重新计算测试集WOE， 因为测试集是没有Y值的（测试集Y值是最后评分用）
for col in bins_of_col:
    vali_woe[col] = pd.cut(vali_data[col], bins_of_col[col]).map(woeall[col])

vali_woe["SeriousDlqin2yrs"] = vali_data["SeriousDlqin2yrs"]
# 这就是我们的建模数据了
vali_woe.to_csv(r"vali_woe.csv")

# In[]:
# 建模：
train_X = model_woe.iloc[:, :-1]
train_y = model_woe.iloc[:, -1]

text_X = vali_woe.iloc[:, :-1]
text_y = vali_woe.iloc[:, -1]

lr = LR().fit(train_X, train_y)
lr.score(text_X, text_y)  # 0.8656671771800517

# In[]:
c_1 = np.linspace(0.01, 1, 20)
score = []
for i in c_1:  # 先c_1大范围，再c_2小范围
    lr = LR(solver='liblinear', C=i).fit(train_X, train_y)
    score.append(lr.score(text_X, text_y))
plt.figure()
plt.plot(c_1, score)
plt.show()
print(max(score), c_1[score.index(max(score))])
print(lr.n_iter_)  # 6

c_2 = np.linspace(0.01, 0.2, 20)
score = []
for i in c_2:  # 先c_1大范围，再c_2小范围： 最高点在0.06
    lr = LR(solver='liblinear', C=i).fit(train_X, train_y)
    score.append(lr.score(text_X, text_y))
plt.figure()
plt.plot(c_2, score)
plt.show()
print(max(score), c_2[score.index(max(score))])
print(lr.n_iter_)  # 6

# In[]:
score = []
iter_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
for i in iter_list:
    lr = LR(solver='liblinear', C=0.06, max_iter=i).fit(train_X, train_y)
    score.append(lr.score(text_X, text_y))

plt.figure()
plt.plot(iter_list, score)
plt.show()
print(max(score), iter_list[score.index(max(score))])  # 0.8656911074949747 7
print(lr.n_iter_)  # 7 收敛了就不迭代了。

# In[]:
lr = LR(solver='liblinear', C=0.05, max_iter=7).fit(train_X, train_y)
print(lr.score(text_X, text_y))
print(lr.n_iter_)  # 7

lr = LR(solver='liblinear', C=0.05).fit(train_X, train_y)
print(lr.score(text_X, text_y))
print(lr.n_iter_)  # 7

# In[]:
import scikitplot as skplt

vali_proba_df = pd.DataFrame(lr.predict_proba(text_X))
skplt.metrics.plot_roc(text_y, vali_proba_df,
                       plot_micro=False, figsize=(6, 6),
                       plot_macro=False)

B = 20 / np.log(2)
A = 600 + B * np.log(1 / 60)

B, A

# In[62]:


base_score = A - B * lr.intercept_
base_score

score_age = woeall["age"] * (-B * lr.coef_[0][0])
score_age

# In[74]:


file = "ScoreData.csv"
# score_data.to_csv(r"D:\study\Mr.huang\pingfenka\score_data")
# file = 'scoredata.csv'

# open是用来打开文件的python命令，第一个参数是文件的路径+文件名，如果你的文件是放在根目录下，则你只需要文件名就好
# 第二个参数是打开文件后的用途，"w"表示用于写入，通常使用的是"r"，表示打开来阅读
# 首先写入基准分数
# 之后使用循环，每次生成一组score_age类似的分档和分数，不断写入文件之中

with open(file, "w") as fdata:
    fdata.write("base_score,{}\n".format(base_score))

for i, col in enumerate(X.columns):
    score = woeall[col] * (-B * lr.coef_[0][i])
    score.name = "Score"
    score.index.name = col
    score.to_csv(file, header=True, mode="a")