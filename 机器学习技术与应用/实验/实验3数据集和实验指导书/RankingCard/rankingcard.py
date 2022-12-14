# -*- coding:UTF-8 -*-
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import load_breast_cancer
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from sklearn.model_selection import cross_val_score


import DataPreproceing
import imblearn
from imblearn.over_sampling import SMOTE
import scikitplot as skplt
import scipy


def get_bin_data(data, a, c, bins):
    data_copy = data[[a, c]]
    # data_copy.dropna(inplace=True)
    # data_copy.sort_values(by=a, ascending=True, inplace=True)
    data_copy.loc[:, a], retbins = pd.qcut(data_copy[a], retbins=True, q=bins, duplicates='drop')

    bin_data = data_copy.groupby([a, c]).size().unstack()
    bin_data.index = np.arange(0, len(bin_data))
    # bin_data['min'] = retbins[0:-1]
    # bin_data['max'] = retbins[1:]
    min = pd.Series(retbins[0:-1], index=bin_data.index, name='min')
    max = pd.Series(retbins[1:], index=bin_data.index, name='max')
    return pd.concat([min, max, bin_data], axis=1)


def bin_merge(bin_data):
    chi2_data = pd.concat([bin_data, bin_data.iloc[:, 2:].shift(1)], axis=1)
    # print chi2_data
    chi2_p = chi2_data.apply(
        lambda x: scipy.stats.chi2_contingency([x.values[2:4], x.values[4:6]])[1], axis=1)
    # chi2_data = chi2_data.fillna(0)
    # print chi2_data
    idx = chi2_p.idxmax()
    bin_data.iloc[idx, :] = [
        np.nanmin([bin_data.iat[idx, 0], bin_data.iat[idx - 1, 0]])
        , np.nanmax([bin_data.iat[idx, 1], bin_data.iat[idx - 1, 1]])
        , np.nansum([bin_data.iat[idx, 2], bin_data.iat[idx - 1, 2]])
        , np.nansum([bin_data.iat[idx, 3], bin_data.iat[idx - 1, 3]])]
    bin_data.drop([idx - 1], inplace=True)
    bin_data.index = np.arange(0, len(bin_data))


def get_bins(data, a, c, bins, init_bins):
    bin_data = get_bin_data(data, a, c, init_bins)
    while (len(bin_data) > bins):
        bin_merge(bin_data)
    return sorted(set(bin_data["min"]).union(bin_data["max"]))


def get_woe(data, a, c, bins):
    data_copy = data[[a, c]]
    data_copy.loc[:, a] = pd.cut(data_copy[a], bins)
    woe_data = data_copy.groupby([a, c]).size().unstack()
    P = woe_data[[0, 1]]
    P = P / P.sum()
    WOE = np.log(P[0] / P[1])
    return WOE


def get_bin_dic(train):
    bins_dic = {
        "RevolvingUtilizationOfUnsecuredLines": get_bins(train, 'RevolvingUtilizationOfUnsecuredLines',
                                                         'SeriousDlqin2yrs', 9, 20)
        , "age": get_bins(train, 'age', 'SeriousDlqin2yrs', 14, 20)
        , "NumberOfTime30-59DaysPastDueNotWorse": [0, 1, 2, 13]
        , "DebtRatio": get_bins(train, 'DebtRatio', 'SeriousDlqin2yrs', 7, 20)
        , "MonthlyIncome": get_bins(train, 'MonthlyIncome', 'SeriousDlqin2yrs', 8, 20)
        , "NumberOfOpenCreditLinesAndLoans": [0, 4.626536, 5.939805, 7.228987, 8.873983, 58]
        , "NumberOfTimes90DaysLate": [0, 1, 2, 17]
        , "NumberRealEstateLoansOrLines": [0, 1, 2, 4, 54]
        , "NumberOfTime60-89DaysPastDueNotWorse": [0, 1, 2, 8]
        , "NumberOfDependents": [0, 1, 2, 3]}
    for key in bins_dic.keys():
        bins = bins_dic[key]
        bins[0], bins[-1] = -np.inf, np.inf
    return bins_dic


def get_woe_dic(train, bin_dic):
    woe_dic = {}
    for key in bin_dic.keys():
        bins = bin_dic[key]
        woe = get_woe(train, key, 'SeriousDlqin2yrs', bins)
        woe_dic[key] = woe
    return woe_dic


def get_score_card(s1, odd1, s2, odd2, lr, woe_dic, colunms):
    B = (s2 - s1) * np.log(odd2 / odd1)
    A = s1 + B * np.log(odd1)
    print (A, B)
    base_score = A - B * lr.intercept_
    print ('base_score', base_score)
    for i, key in enumerate(colunms):
        score = woe_dic[key] * (-B * lr.coef_[0][i])
        print (i, key, score)


def get_iv(bin_data):
    P = bin_data[[0, 1]]
    P = P / P.sum()
    WOE = np.log(P[0] / P[1])
    IV = (P[0] - P[1]) * WOE
    return IV.sum()


def plot_iv(data, a, c, init_bins):
    bin_data = get_bin_data(data, a, c, init_bins)
    # print bin_data
    ivs = []
    bins = []
    ivs.append(get_iv(bin_data))
    bins.append(len(bin_data))
    while (len(bin_data) > 2):
        bin_merge(bin_data)
        ivs.append(get_iv(bin_data))
        bins.append(len(bin_data))
    plt.plot(bins, ivs)
    plt.xticks(bins)
    plt.ylabel(a)
    plt.show()


def rankingcard_step1():
    df = pd.read_csv('rankingcard.csv', index_col=0)
    # 1.??????
    df.drop_duplicates(inplace=True)
    # 2.???????????????
    # ???????????????????????????
    DataPreproceing.fill_mean(df['NumberOfDependents'].values, copy=False)
    # ???????????????????????????
    df.iloc[:, df.columns != 'SeriousDlqin2yrs'] = DataPreproceing.fill_rfr(
        df.iloc[:, df.columns != 'SeriousDlqin2yrs'].values,
        df['SeriousDlqin2yrs'].values)
    df.to_csv('rankingcard_1.csv', index=False)


def rankingcard_step2():
    # ???????????????????????????
    df = pd.read_csv('rankingcard_1.csv')
    print (df.describe([0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99]).T)
    df = df[df['age'] > 0]
    df = df[df['NumberOfTimes90DaysLate'] < 90]
    df.to_csv('rankingcard_2.csv', index=False)


def rankingcard_step3():
    # ???????????????????????????????????????
    df = pd.read_csv('rankingcard_2.csv')
    X = df.iloc[:, df.columns != 'SeriousDlqin2yrs']
    y = df.iloc[:, df.columns == 'SeriousDlqin2yrs']
    smote = SMOTE(random_state=0)
    X, y = smote.fit_sample(X, y)
    # ???????????????????????????
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=100)
    train = pd.concat([pd.DataFrame(y_train), pd.DataFrame(X_train)], axis=1)
    test = pd.concat([pd.DataFrame(y_test), pd.DataFrame(X_test)], axis=1)
    train.columns = df.columns
    test.columns = df.columns
    train.to_csv('rankingcard_train.csv', index=False)
    test.to_csv('rankingcard_test.csv', index=False)


def rankingcard_step4():
    train = pd.read_csv('rankingcard_train.csv')
    cols = ['RevolvingUtilizationOfUnsecuredLines', 'age', 'DebtRatio', 'MonthlyIncome']
    for col in cols:
        plot_iv(train, col, 'SeriousDlqin2yrs', 20)


def rankingcard_step5():
    train = pd.read_csv('rankingcard_train.csv')
    test = pd.read_csv('rankingcard_test.csv')
    bin_dic = get_bin_dic(train)
    woe_dic = get_woe_dic(train, bin_dic)
    for key in bin_dic.keys():
        bins = bin_dic[key]
        woe = woe_dic[key]
        train[key] = pd.cut(train[key], bins).map(woe)
        test[key] = pd.cut(test[key], bins).map(woe)
    X_train = train.loc[:, train.columns != 'SeriousDlqin2yrs']
    y_train = train['SeriousDlqin2yrs']
    X_test = test.loc[:, test.columns != 'SeriousDlqin2yrs']
    y_test = test['SeriousDlqin2yrs']
    lr = LogisticRegression(penalty='l2', C=100, solver='newton-cg', max_iter=25)
    lr.fit(X_train, y_train)
    print (lr.score(X_test, y_test))
    vali_proba_df = pd.DataFrame(lr.predict_proba(X_test))
    skplt.metrics.plot_roc(y_test, vali_proba_df,
                           plot_micro=False, figsize=(6, 6),
                           plot_macro=False)
    plt.show()
    get_score_card(600, 1.0 / 60, 620, 1.0 / 30, lr, woe_dic, X_train.columns)


# SeriousDlqin2yrs                        149391 non-null int64
# RevolvingUtilizationOfUnsecuredLines    149391 non-null float64   ??????>1???  3321
# age                                     149391 non-null int64     ??????0
# NumberOfTime30-59DaysPastDueNotWorse    149391 non-null int64     ?????? 98???96
# DebtRatio                               149391 non-null float64   ?????? >3??? 27858
# MonthlyIncome                           120170 non-null float64
# NumberOfOpenCreditLinesAndLoans         149391 non-null int64
# NumberOfTimes90DaysLate                 149391 non-null int64     ?????? 98???96
# NumberRealEstateLoansOrLines            149391 non-null int64     ??????
# NumberOfTime60-89DaysPastDueNotWorse    149391 non-null int64     ?????? 98???96
# NumberOfDependents                      145563 non-null float64

def rankingcard():
    rankingcard_step1()
    rankingcard_step2()
    rankingcard_step3()
    rankingcard_step4()
    rankingcard_step5()
    df = pd.read_csv("rankingcard.csv", index_col=0)
    df_copy = df.copy()
    df_copy.dropna(inplace=True)
    X = df_copy.loc[:, df_copy.columns != 'SeriousDlqin2yrs']
    y = df_copy['SeriousDlqin2yrs']
    rfr = RandomForestRegressor(n_estimators=100)
    score = cross_val_score(rfr, X, y, cv=5).mean()
    print (len(df_copy), score)

    df.drop_duplicates(inplace=True)
    DataPreproceing.fill_constant(df['NumberOfDependents'].values, fill_value=1, copy=False)
    print (len(df))
    df.drop(index=df[df['age'] == 0].index, inplace=True)
    print (len(df))
    df.drop(index=df[df['NumberOfTime30-59DaysPastDueNotWorse'] > 95].index, inplace=True)
    df.drop(index=df[df['NumberOfTime60-89DaysPastDueNotWorse'] > 95].index, inplace=True)
    df.drop(index=df[df['NumberOfTimes90DaysLate'] > 95].index, inplace=True)
    print (len(df))
    df.drop(index=df[df['RevolvingUtilizationOfUnsecuredLines'] > 3].index, inplace=True)
    print (len(df))
    # df.drop(index=df[df['DebtRatio'] > 3].index, inplace=True)
    # print len(df)

    a = df['DebtRatio']
    print (a.count())
    print (a.value_counts())
    print (a[(a > 20) & (a < 8500)].describe([0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99]))
    a = a[a > 1].sort_values().values
    print (df.ix[(a > 20) & (a < 50000), 'SeriousDlqin2yrs'].value_counts())
    print (len(a))
    # x = ruoul[ruoul > 1.5].sort_values().values
    # # print ruoul[ruoul > 1.5].describe()
    plt.plot(a[(a > 1) & (a < 10)])
    # plt.hist(a, alpha=0.4)
    # print df['RevolvingUtilizationOfUnsecuredLines'].index
    # print df['RevolvingUtilizationOfUnsecuredLines']
    # plt.bar(df['RevolvingUtilizationOfUnsecuredLines'].index, df['RevolvingUtilizationOfUnsecuredLines'])
    plt.show()

    # X = df.loc[:, df.columns != 'SeriousDlqin2yrs']
    # y = df['SeriousDlqin2yrs']
    # DataPreproceing.fill_random_forest(X, y, 'MonthlyIncome', copy=False)
    # rfr = RandomForestRegressor(n_estimators=100)
    # score = cross_val_score(rfr, X, y, cv=5).mean()
    # print len(df), score


if __name__ == '__main__':
    rankingcard()