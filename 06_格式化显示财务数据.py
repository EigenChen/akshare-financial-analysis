"""
格式化显示财务数据 - 每个类目一行

将财务数据转换为更易读的格式：每个指标/科目占一行
只显示指定报告期的数据（如2024年12月31日）
"""

import akshare as ak
import pandas as pd
import os
from datetime import datetime

# 财务科目英文名到中文名的映射字典
FINANCIAL_ITEM_MAPPING = {
    # 财务指标
    '净利润': '净利润',
    '净利润同比增长率': '净利润同比增长率',
    '扣非净利润': '扣非净利润',
    '扣非净利润同比增长率': '扣非净利润同比增长率',
    '营业总收入': '营业总收入',
    '营业总收入同比增长率': '营业总收入同比增长率',
    '基本每股收益': '基本每股收益',
    '每股净资产': '每股净资产',
    '每股资本公积金': '每股资本公积金',
    '每股未分配利润': '每股未分配利润',
    '每股经营现金流': '每股经营现金流',
    '销售净利率': '销售净利率',
    '净资产收益率': '净资产收益率',
    '净资产收益率-摊薄': '净资产收益率-摊薄',
    '营业周期': '营业周期',
    '应收账款周转天数': '应收账款周转天数',
    '流动比率': '流动比率',
    '速动比率': '速动比率',
    '保守速动比率': '保守速动比率',
    '产权比率': '产权比率',
    '资产负债率': '资产负债率',
    
    # 资产负债表科目
    'CASH_DEPOSIT_PBC': '存放中央银行款项',
    'DEPOSIT_INTERBANK': '存放同业款项',
    'PRECIOUS_METAL': '贵金属',
    'LEND_FUND': '拆出资金',
    'FVTPL_FINASSET': '以公允价值计量且其变动计入当期损益的金融资产',
    'TRADE_FINASSET': '交易性金融资产',
    'APPOINT_FVTPL_FINASSET': '指定以公允价值计量且其变动计入当期损益的金融资产',
    'DERIVE_FINASSET': '衍生金融资产',
    'BUY_RESALE_FINASSET': '买入返售金融资产',
    'ACCOUNTS_RECE': '应收账款',
    'FINANCE_RECE': '应收款项融资',
    'INTEREST_RECE': '应收利息',
    'LOAN_ADVANCE': '发放贷款和垫款',
    'TRADE_FINASSET_NOTFVTPL': '交易性金融资产（非FVTPL）',
    'CREDITOR_INVEST': '债权投资',
    'OTHER_CREDITOR_INVEST': '其他债权投资',
    'OTHER_EQUITY_INVEST': '其他权益工具投资',
    'AVAILABLE_SALE_FINASSET': '可供出售金融资产',
    'HOLD_MATURITY_INVEST': '持有至到期投资',
    'INVEST_RECE': '应收投资款',
    'AMORTIZE_COST_FINASSET': '以摊余成本计量的金融资产',
    'FVTOCI_FINASSET': '以公允价值计量且其变动计入其他综合收益的金融资产',
    'HOLDSALE_ASSET': '持有待售资产',
    'LONG_EQUITY_INVEST': '长期股权投资',
    'INVEST_SUBSIDIARY': '对子公司投资',
    'INVEST_JOINT': '对合营企业投资',
    'INVEST_REALESTATE': '投资性房地产',
    'FIXED_ASSET': '固定资产',
    'CIP': '在建工程',
    'USERIGHT_ASSET': '使用权资产',
    'INTANGIBLE_ASSET': '无形资产',
    'GOODWILL': '商誉',
    'PEND_MORTGAGE_ASSET': '待处理抵债资产',
    'MORTGAGE_ASSET_IMPAIRMENT': '抵债资产减值准备',
    'NET_PENDMORTGAGE_ASSET': '待处理抵债资产净额',
    'DEFER_TAX_ASSET': '递延所得税资产',
    'LONG_PREPAID_EXPENSE': '长期待摊费用',
    'OTHER_ASSET': '其他资产',
    'ASSET_OTHER': '资产其他',
    'ASSET_BALANCE': '资产合计',
    'TOTAL_ASSETS': '资产总计',
    'LOAN_PBC': '向中央银行借款',
    'IOFI_DEPOSIT': '吸收存款',
    'BORROW_FUND': '拆入资金',
    'TRADE_FINLIAB_NOTFVTPL': '交易性金融负债（非FVTPL）',
    'FVTPL_FINLIAB': '以公允价值计量且其变动计入当期损益的金融负债',
    'TRADE_FINLIAB': '交易性金融负债',
    'APPOINT_FVTPL_FINLIAB': '指定以公允价值计量且其变动计入当期损益的金融负债',
    'DERIVE_FINLIAB': '衍生金融负债',
    'SELL_REPO_FINASSET': '卖出回购金融资产款',
    'ACCEPT_DEPOSIT': '吸收存款',
    'OUTWARD_REMIT': '汇出汇款',
    'CD_NOTE_PAYABLE': '应付债券',
    'DEPOSIT_CERTIFICATE': '存款证',
    'STAFF_SALARY_PAYABLE': '应付职工薪酬',
    'TAX_PAYABLE': '应交税费',
    'INTEREST_PAYABLE': '应付利息',
    'DIVIDEND_PAYABLE': '应付股利',
    'PREDICT_LIAB': '预计负债',
    'DEFER_TAX_LIAB': '递延所得税负债',
    'AMORTIZE_COST_FINLIAB': '以摊余成本计量的金融负债',
    'HOLDSALE_LIAB': '持有待售负债',
    'BOND_PAYABLE': '应付债券',
    'SUBBOND_PAYABLE': '应付次级债券',
    'PREFERRED_SHARES_PAYBALE': '应付优先股',
    'PERPETUAL_BOND_PAYBALE': '应付永续债',
    'LEASE_LIAB': '租赁负债',
    'OTHER_LIAB': '其他负债',
    'LIAB_OTHER': '负债其他',
    'LIAB_BALANCE': '负债合计',
    'TOTAL_LIABILITIES': '负债总计',
    'SHARE_CAPITAL': '股本',
    'OTHER_EQUITY_TOOL': '其他权益工具',
    'PREFERRED_SHARES': '优先股',
    'PERPETUAL_BOND': '永续债',
    'OTHER_EQUITY_OTHER': '其他权益其他',
    'CAPITAL_RESERVE': '资本公积',
    'INVEST_REVALUE_RESERVE': '投资重估储备',
    'TREASURY_SHARES': '库存股',
    'OTHER_COMPRE_INCOME': '其他综合收益',
    'HEDGE_RESERVE': '套期储备',
    'SURPLUS_RESERVE': '盈余公积',
    'GENERAL_RISK_RESERVE': '一般风险准备',
    'UNASSIGN_RPOFIT': '未分配利润',
    'ADVICE_ASSIGN_DIVIDEND': '建议分配股利',
    'CONVERT_DIFF': '外币报表折算差额',
    'PARENT_EQUITY_OTHER': '母公司权益其他',
    'PARENT_EQUITY_BALANCE': '母公司权益合计',
    'TOTAL_PARENT_EQUITY': '归属于母公司所有者权益合计',
    'MINORITY_EQUITY': '少数股东权益',
    'EQUITY_OTHER': '所有者权益其他',
    'EQUITY_BALANCE': '所有者权益合计',
    'TOTAL_EQUITY': '所有者权益总计',
    'LIAB_EQUITY_OTHER': '负债和所有者权益其他',
    'LIAB_EQUITY_BALANCE': '负债和所有者权益合计',
    'TOTAL_LIAB_EQUITY': '负债和所有者权益总计',
    'AGENT_BUSINESS_ASSET': '代理业务资产',
    'AGENT_BUSINESS_LIAB': '代理业务负债',
    'SHORT_FIN_PAYABLE': '短期金融负债',
    'ACCRUED_EXPENSE': '预提费用',
    'ACCOUNTS_PAYABLE': '应付账款',
    'NOTE_PAYABLE': '应付票据',
    'NOTE_RECE': '应收票据',
    
    # 资产负债表补充科目（一般企业）
    'ACCEPT_DEPOSIT_INTERBANK': '吸收存款及同业存放',
    'ADVANCE_RECEIVABLES': '预收款项',  # 预收账款
    'AGENT_TRADE_SECURITY': '代理买卖证券款',
    'AGENT_UNDERWRITE_SECURITY': '代理承销证券款',
    'AMORTIZE_COST_NCFINASSET': '以摊余成本计量的非流动金融资产',
    'AMORTIZE_COST_NCFINLIAB': '以摊余成本计量的非流动金融负债',
    'ASSIGN_CASH_DIVIDEND': '应付现金股利',
    'CONSUMPTIVE_BIOLOGICAL_ASSET': '消耗性生物资产',
    'CONTRACT_ASSET': '合同资产',
    'CONTRACT_LIAB': '合同负债',
    'CURRENT_ASSET_BALANCE': '流动资产合计',
    'CURRENT_ASSET_OTHER': '流动资产其他',
    'CURRENT_LIAB_BALANCE': '流动负债合计',
    'CURRENT_LIAB_OTHER': '流动负债其他',
    'DEFER_INCOME': '递延收益',
    'DEFER_INCOME_1YEAR': '一年内到期的递延收益',
    'DEVELOP_EXPENSE': '开发支出',
    'DIV_HOLDSALE_ASSET': '划分为持有待售的资产',
    'DIV_HOLDSALE_LIAB': '划分为持有待售的负债',
    'DIVIDEND_RECE': '应收股利',
    'EXPORT_REFUND_RECE': '应收出口退税',
    'FEE_COMMISSION_PAYABLE': '应付手续费及佣金',
    'FIN_FUND': '金融资金',
    'FIXED_ASSET_DISPOSAL': '固定资产清理',
    'FVTOCI_NCFINASSET': '以公允价值计量且其变动计入其他综合收益的非流动金融资产',
    'INSURANCE_CONTRACT_RESERVE': '保险合同准备金',
    'INTERNAL_PAYABLE': '内部应付款',
    'INTERNAL_RECE': '内部应收款',
    'INVENTORY': '存货',
    'LONG_LOAN': '长期借款',
    'LONG_PAYABLE': '长期应付款',
    'LONG_RECE': '长期应收款',
    'LONG_STAFFSALARY_PAYABLE': '长期应付职工薪酬',
    'MONETARYFUNDS': '货币资金',
    'NONCURRENT_ASSET_1YEAR': '一年内到期的非流动资产',
    'NONCURRENT_ASSET_BALANCE': '非流动资产合计',
    'NONCURRENT_ASSET_OTHER': '非流动资产其他',
    'NONCURRENT_LIAB_1YEAR': '一年内到期的非流动负债',
    'NONCURRENT_LIAB_BALANCE': '非流动负债合计',
    'NONCURRENT_LIAB_OTHER': '非流动负债其他',
    'NOTE_ACCOUNTS_PAYABLE': '应付票据及应付账款',
    'NOTE_ACCOUNTS_RECE': '应收票据及应收账款',
    'OIL_GAS_ASSET': '油气资产',
    'OTHER_CURRENT_ASSET': '其他流动资产',
    'OTHER_CURRENT_LIAB': '其他流动负债',
    'OTHER_NONCURRENT_ASSET': '其他非流动资产',
    'OTHER_NONCURRENT_FINASSET': '其他非流动金融资产',
    'OTHER_NONCURRENT_LIAB': '其他非流动负债',
    'OTHER_PAYABLE': '其他应付款',
    'OTHER_RECE': '其他应收款',
    'PREDICT_CURRENT_LIAB': '预计流动负债',
    'PREMIUM_RECE': '应收保费',
    'PREPAYMENT': '预付款项',
    'PRODUCTIVE_BIOLOGY_ASSET': '生产性生物资产',
    'PROJECT_MATERIAL': '工程物资',
    'RC_RESERVE_RECE': '应收分保合同准备金',
    'REINSURE_PAYABLE': '应付分保账款',
    'REINSURE_RECE': '应收分保账款',
    'SETTLE_EXCESS_RESERVE': '结算备付金',
    'SHORT_BOND_PAYABLE': '应付短期债券',
    'SHORT_LOAN': '短期借款',
    'SPECIAL_PAYABLE': '专项应付款',
    'SPECIAL_RESERVE': '专项储备',
    'SUBSIDY_RECE': '应收补贴款',
    'TOTAL_CURRENT_ASSETS': '流动资产总计',
    'TOTAL_CURRENT_LIAB': '流动负债总计',
    'TOTAL_NONCURRENT_ASSETS': '非流动资产总计',
    'TOTAL_NONCURRENT_LIAB': '非流动负债总计',
    'TOTAL_OTHER_PAYABLE': '其他应付款合计',
    'TOTAL_OTHER_RECE': '其他应收款合计',
    'UNCONFIRM_INVEST_LOSS': '未确认投资损失',
    
    # 利润表科目
    'TOTAL_OPERATE_INCOME': '营业总收入',
    'OPERATE_INCOME': '营业收入',
    'INTEREST_NI': '利息净收入',
    'INTEREST_INCOME': '利息收入',
    'INTEREST_EXPENSE': '利息支出',
    'EARNED_PREMIUM': '已赚保费',
    'FEE_COMMISSION_NI': '手续费及佣金净收入',
    'FEE_COMMISSION_INCOME': '手续费及佣金收入',
    'FEE_COMMISSION_EXPENSE': '手续费及佣金支出',
    'OTHER_BUSINESS_INCOME': '其他业务收入',
    'TOI_OTHER': '营业总收入其他',
    'TOTAL_OPERATE_COST': '营业总成本',
    'OPERATE_COST': '营业成本',
    'OPERATE_EXPENSE': '营业费用',
    'SURRENDER_VALUE': '退保金',
    'NET_COMPENSATE_EXPENSE': '赔付支出净额',
    'NET_CONTRACT_RESERVE': '提取保险合同准备金净额',
    'POLICY_BONUS_EXPENSE': '保单红利支出',
    'REINSURE_EXPENSE': '分保费用',
    'OTHER_BUSINESS_COST': '其他业务成本',
    'TOC_OTHER': '营业总成本其他',
    'OPERATE_TAX_ADD': '税金及附加',
    'RESEARCH_EXPENSE': '研发费用',
    'SALE_EXPENSE': '销售费用',
    'MANAGE_EXPENSE': '管理费用',
    'ME_RESEARCH_EXPENSE': '管理费用中的研发费用',
    'BUSINESS_MANAGE_EXPENSE': '业务及管理费',
    'FINANCE_EXPENSE': '财务费用',
    'FE_INTEREST_EXPENSE': '财务费用中的利息支出',
    'FE_INTEREST_INCOME': '财务费用中的利息收入',
    'ASSET_IMPAIRMENT_LOSS': '资产减值损失',
    'CREDIT_IMPAIRMENT_LOSS': '信用减值损失',
    'OTHER_BUSINESS_COST': '其他业务成本',
    'OPERATE_EXPENSE_OTHER': '营业费用其他',
    'OPERATE_EXPENSE_BALANCE': '营业费用合计',
    'OPERATE_PROFIT_OTHER': '营业利润其他',
    'OPERATE_PROFIT_BALANCE': '营业利润合计',
    'OPERATE_PROFIT': '营业利润',
    'FAIRVALUE_CHANGE_INCOME': '公允价值变动收益',
    'INVEST_INCOME': '投资收益',
    'ASSET_DISPOSAL_INCOME': '资产处置收益',
    'OTHER_INCOME': '其他收益',
    'NONBUSINESS_INCOME': '非营业性收入',
    'NONCURRENT_DISPOSAL_INCOME': '非流动资产处置收益',
    'NONBUSINESS_EXPENSE': '非营业性支出',
    'NONCURRENT_DISPOSAL_LOSS': '非流动资产处置损失',
    'EFFECT_TP_OTHER': '利润总额影响其他',
    'TOTAL_PROFIT_BALANCE': '利润总额合计',
    'TOTAL_PROFIT': '利润总额',
    'INCOME_TAX': '所得税费用',
    'EFFECT_NETPROFIT_OTHER': '净利润影响其他',
    'EFFECT_NETPROFIT_BALANCE': '净利润影响合计',
    'UNCONFIRM_INVEST_LOSS': '未确认投资损失',
    'NETPROFIT': '净利润',
    'PRECOMBINE_PROFIT': '被合并方在合并前实现的净利润',
    'CONTINUED_NETPROFIT': '持续经营净利润',
    'DISCONTINUED_NETPROFIT': '终止经营净利润',
    'PARENT_NETPROFIT': '归属于母公司所有者的净利润',
    'MINORITY_INTEREST': '少数股东损益',
    'DEDUCT_PARENT_NETPROFIT': '扣除非经常性损益后的归属于母公司所有者的净利润',
    'NETPROFIT_OTHER': '净利润其他',
    'NETPROFIT_BALANCE': '净利润合计',
    'BASIC_EPS': '基本每股收益',
    'DILUTED_EPS': '稀释每股收益',
    'OTHER_COMPRE_INCOME': '其他综合收益',
    'PARENT_OCI': '归属于母公司所有者的其他综合收益',
    'MINORITY_OCI': '归属于少数股东的其他综合收益',
    'PARENT_OCI_OTHER': '归属于母公司所有者的其他综合收益其他',
    'PARENT_OCI_BALANCE': '归属于母公司所有者的其他综合收益合计',
    'UNABLE_OCI': '不能重分类进损益的其他综合收益',
    'SETUP_PROFIT_CHANGE': '重新计量设定受益计划变动额',
    'RIGHTLAW_UNABLE_OCI': '权益法下不能转损益的其他综合收益',
    'UNABLE_OCI_OTHER': '不能重分类进损益的其他综合收益其他',
    'UNABLE_OCI_BALANCE': '不能重分类进损益的其他综合收益合计',
    'ABLE_OCI': '将重分类进损益的其他综合收益',
    'RIGHTLAW_ABLE_OCI': '权益法下可转损益的其他综合收益',
    'AFA_FAIRVALUE_CHANGE': '其他债权投资公允价值变动',
    'HMI_AFA': '金融资产重分类计入其他综合收益的金额',
    'CASHFLOW_HEDGE_VALID': '现金流量套期储备',
    'CONVERT_DIFF': '外币报表折算差额',
    'ABLE_OCI_OTHER': '将重分类进损益的其他综合收益其他',
    'ABLE_OCI_BALANCE': '将重分类进损益的其他综合收益合计',
    'OCI_OTHER': '其他综合收益其他',
    'OCI_BALANCE': '其他综合收益合计',
    'TOTAL_COMPRE_INCOME': '综合收益总额',
    'PARENT_TCI': '归属于母公司所有者的综合收益总额',
    'MINORITY_TCI': '归属于少数股东的综合收益总额',
    'PRECOMBINE_TCI': '被合并方在合并前实现的综合收益总额',
    'EFFECT_TCI_BALANCE': '综合收益总额影响合计',
    'TCI_OTHER': '综合收益总额其他',
    'TCI_BALANCE': '综合收益总额合计',
    'OTHERRIGHT_FAIRVALUE_CHANGE': '其他权益工具投资公允价值变动',
    'CREDITRISK_FAIRVALUE_CHANGE': '企业自身信用风险公允价值变动',
    'CREDITOR_FAIRVALUE_CHANGE': '其他债权投资公允价值变动',
    'FINANCE_OCI_AMT': '金融资产重分类计入其他综合收益的金额',
    'CREDITOR_IMPAIRMENT_RESERVE': '其他债权投资信用减值准备',
    'ACF_END_INCOME': '其他综合收益结转留存收益的金额',
    
    # 现金流量表科目
    'SALE_SERVICE': '销售商品、提供劳务收到的现金',
    'SALES_SERVICES': '销售商品、提供劳务收到的现金',
    'CUSTOMER_DEPOSIT_ADD': '客户存款和同业存放款项净增加额',
    'DEPOSIT_INTERBANK_ADD': '存放同业款项净增加额',
    'LOAN_PBC_ADD': '向中央银行借款净增加额',
    'OFI_BF_ADD': '向其他金融机构拆入资金净增加额',
    'RECEIVE_ORIGIC_INSURANCE': '收到原保险合同保费取得的现金',
    'RECEIVE_ORIGIC_PREMIUM': '收到原保险合同保费取得的现金',
    'RECEIVE_REINSURE_NET': '收到再保业务现金净额',
    'INSURED_INVEST_ADD': '保户储金及投资款净增加额',
    'DISPOSAL_TFA_ADD': '处置交易性金融资产净增加额',
    'INTEREST_COMMISSION_RECE': '收取利息、手续费及佣金的现金',
    'RECEIVE_INTEREST_COMMISSION': '收取利息、手续费及佣金的现金',
    'BORROW_FUND_ADD': '向其他金融机构拆入资金净增加额',
    'LOAN_ADVANCE_REDUCE': '拆入资金净减少额',
    'REPO_BUSINESS_ADD': '回购业务资金净增加额',
    'RECEIVE_TAX_REFUND': '收到的税费返还',
    'RECEIVE_OTHER_OPERATE': '收到其他与经营活动有关的现金',
    'OPERATE_INFLOW_OTHER': '经营活动现金流入小计',
    'OPERATE_INFLOW_BALANCE': '经营活动现金流入合计',
    'TOTAL_OPERATE_INFLOW': '经营活动现金流入总计',
    'BUY_SERVICE': '购买商品、接受劳务支付的现金',
    'BUY_SERVICES': '购买商品、接受劳务支付的现金',
    'LOAN_ADVANCE_ADD': '客户贷款及垫款净增加额',
    'PBC_INTERBANK_ADD': '存放中央银行和同业款项净增加额',
    'DEPOSIT_PBC_IB_ADD': '存放中央银行和同业款项净增加额',
    'ORIGIC_INSURANCE_PAY': '支付原保险合同赔付款项的现金',
    'PAY_ORIGIC_COMPENSATE': '支付原保险合同赔付款项的现金',
    'PAY_INTEREST_COMMISSION': '支付利息、手续费及佣金的现金',
    'PAY_POLICY_BONUS': '支付保单红利的现金',
    'PAY_STAFF_CASH': '支付给职工以及为职工支付的现金',
    'PAY_ALL_TAX': '支付的各项税费',
    'PAY_OTHER_OPERATE': '支付其他与经营活动有关的现金',
    'OPERATE_OUTFLOW_OTHER': '经营活动现金流出小计',
    'OPERATE_NET_CASH_FLOW': '经营活动产生的现金流量净额',
    'WITHDRAW_INVEST': '收回投资收到的现金',
    'RECEIVE_INVEST_INCOME': '取得投资收益收到的现金',
    'DISPOSAL_LONG_ASSET': '处置固定资产、无形资产和其他长期资产收回的现金净额',
    'DISPOSAL_SUBSIDIARY_OTHER': '处置子公司及其他营业单位收到的现金净额',
    'REDUCE_PLEDGE_TIMEDEPOSITS': '减少质押定期存款',
    'RECEIVE_OTHER_INVEST': '收到其他与投资活动有关的现金',
    'INVEST_INFLOW_OTHER': '投资活动现金流入小计',
    'INVEST_INFLOW_BALANCE': '投资活动现金流入合计',
    'TOTAL_INVEST_INFLOW': '投资活动现金流入总计',
    'CONSTRUCT_LONG_ASSET': '购建固定资产、无形资产和其他长期资产支付的现金',
    'INVEST_PAY_CASH': '投资支付的现金',
    'IMPAWN_LOAN_ADD': '质押贷款净增加额',
    'PLEDGE_LOAN_ADD': '质押贷款净增加额',
    'OBTAIN_SUBSIDIARY_OTHER': '取得子公司及其他营业单位支付的现金净额',
    'ADD_PLEDGE_TIMEDEPOSITS': '增加质押定期存款',
    'PAY_OTHER_INVEST': '支付其他与投资活动有关的现金',
    'INVEST_OUTFLOW_OTHER': '投资活动现金流出小计',
    'INVEST_NET_CASH_FLOW': '投资活动产生的现金流量净额',
    'ACCEPT_INVEST_CASH': '吸收投资收到的现金',
    'ACCEPT_MINORITY_INVEST_CASH': '其中：子公司吸收少数股东投资收到的现金',
    'ACCEPT_LOAN_CASH': '取得借款收到的现金',
    'ISSUE_BOND': '发行债券收到的现金',
    'RECEIVE_OTHER_FINANCE': '收到其他与筹资活动有关的现金',
    'FINANCE_INFLOW_OTHER': '筹资活动现金流入小计',
    'PAY_DEBT_CASH': '偿还债务支付的现金',
    'ASSIGN_DIVIDEND_PORFIT': '分配股利、利润或偿付利息支付的现金',
    'PAY_MINORITY_DIVIDEND': '其中：子公司支付给少数股东的股利、利润',
    'BUY_SUBSIDIARY_EQUITY': '其中：子公司支付给少数股东的股利、利润',
    'PAY_OTHER_FINANCE': '支付其他与筹资活动有关的现金',
    'FINANCE_OUTFLOW_OTHER': '筹资活动现金流出小计',
    'FINANCE_NET_CASH_FLOW': '筹资活动产生的现金流量净额',
    'RATE_CHANGE_EFFECT': '汇率变动对现金及现金等价物的影响',
    'NET_CASH_INCREASE': '现金及现金等价物净增加额',
    'BEGIN_CASH': '期初现金及现金等价物余额',
    'END_CASH': '期末现金及现金等价物余额',
    
    # 现金流量表补充科目（银行等金融机构专用）
    'DEPOSIT_IOFI_OTHER': '存放同业和其他金融机构款项其他',
    'CUSTOMER_DEPOSIT_ADD': '客户存款和同业存放款项净增加额',
    'IOFI_ADD': '同业和其他金融机构存放款项净增加额',
    'LOAN_PBC_ADD': '向中央银行借款净增加额',
    'PBC_IOFI_REDUCE': '存放中央银行款项净减少额',
    'DEPOSIT_PBC_REDUCE': '存放中央银行款项净减少额',
    'DEPOSIT_IOFI_REDUCE': '存放同业和其他金融机构款项净减少额',
    'BORROW_REPO_ADD': '拆入资金净增加额',
    'BORROW_FUND_ADD': '向其他金融机构拆入资金净增加额',
    'SELL_REPO_ADD': '卖出回购金融资产款净增加额',
    'LEND_RESALE_REDUCE': '拆出资金净减少额',
    'LEND_FUND_REDUCE': '拆出资金净减少额',
    'BUY_RESALE_REDUCE': '买入返售金融资产净减少额',
    'NET_CD': '净增加额',
    'TRADE_FINLIAB_ADD': '交易性金融负债净增加额',
    'TRADE_FINASSET_REDUCE': '交易性金融资产净减少额',
    'RECEIVE_INTEREST_COMMISSION': '收取利息、手续费及佣金的现金',
    'RECEIVE_INTEREST': '收取利息的现金',
    'RECEIVE_COMMISSION': '收取手续费的现金',
    'DISPOSAL_MORTGAGE_ASSET': '处置抵债资产收到的现金',
    'WITHDRAW_WRITEOFF_LOAN': '收回已核销贷款收到的现金',
    'RECEIVE_OTHER_OPERATE': '收到其他与经营活动有关的现金',
    'OPERATE_INFLOW_OTHER': '经营活动现金流入其他',
    'OPERATE_INFLOW_BALANCE': '经营活动现金流入合计',
    'TOTAL_OPERATE_INFLOW': '经营活动现金流入总计',
    'LOAN_ADVANCE_ADD': '客户贷款及垫款净增加额',
    'LOAN_PBC_REDUCE': '向中央银行借款净减少额',
    'PBC_IOFI_ADD': '存放中央银行款项净增加额',
    'DEPOSIT_PBC_ADD': '存放中央银行款项净增加额',
    'DEPOSIT_IOFI_ADD': '存放同业和其他金融机构款项净增加额',
    'INTERBANK_OTHER_REDUCE': '同业和其他金融机构存放款项净减少额',
    'ISSUED_CD_REDUCE': '已发行存款证净减少额',
    'LEND_RESALE_ADD': '拆出资金净增加额',
    'LEND_FUND_ADD': '拆出资金净增加额',
    'BUY_RESALE_ADD': '买入返售金融资产净增加额',
    'BORROW_REPO_REDUCE': '拆入资金净减少额',
    'BORROW_FUND_REDUCE': '向其他金融机构拆入资金净减少额',
    'SELL_REPO_REDUCE': '卖出回购金融资产款净减少额',
    'TRADE_FINASSET_ADD': '交易性金融资产净增加额',
    'TRADE_FINLIAB_REDUCE': '交易性金融负债净减少额',
    'PAY_INTEREST_COMMISSION': '支付利息、手续费及佣金的现金',
    'PAY_INTEREST': '支付利息的现金',
    'PAY_COMMISSION': '支付手续费的现金',
    'PAY_STAFF_CASH': '支付给职工以及为职工支付的现金',
    'PAY_ALL_TAX': '支付的各项税费',
    'BUY_FIN_LEASE': '购买金融租赁资产支付的现金',
    'ACCOUNTS_RECE_ADD': '应收账款净增加额',
    'PAY_OTHER_OPERATE': '支付其他与经营活动有关的现金',
    'OPERATE_OUTFLOW_OTHER': '经营活动现金流出其他',
    'OPERATE_OUTFLOW_BALANCE': '经营活动现金流出合计',
    'TOTAL_OPERATE_OUTFLOW': '经营活动现金流出总计',
    'OPERATE_NETCASH_OTHER': '经营活动产生的现金流量净额其他',
    'OPERATE_NETCASH_BALANCE': '经营活动产生的现金流量净额合计',
    'NETCASH_OPERATE': '经营活动产生的现金流量净额',
    'WITHDRAW_INVEST': '收回投资收到的现金',
    'RECEIVE_INVEST_INCOME': '取得投资收益收到的现金',
    'RECEIVE_DIVIDEND_PROFIT': '取得股利、利润收到的现金',
    'DISPOSAL_LONG_ASSET': '处置固定资产、无形资产和其他长期资产收回的现金净额',
    'DISPOSAL_SUBSIDIARY_JOINT': '处置子公司及其他营业单位收到的现金净额',
    'RECEIVE_OTHER_INVEST': '收到其他与投资活动有关的现金',
    'INVEST_INFLOW_OTHER': '投资活动现金流入其他',
    'INVEST_INFLOW_BALANCE': '投资活动现金流入合计',
    'TOTAL_INVEST_INFLOW': '投资活动现金流入总计',
    'INVEST_PAY_CASH': '投资支付的现金',
    'CONSTRUCT_LONG_ASSET': '购建固定资产、无形资产和其他长期资产支付的现金',
    'OBTAIN_SUBSIDIARY_OTHER': '取得子公司及其他营业单位支付的现金净额',
    'PAY_OTHER_INVEST': '支付其他与投资活动有关的现金',
    'INVEST_OUTFLOW_OTHER': '投资活动现金流出其他',
    'INVEST_OUTFLOW_BALANCE': '投资活动现金流出合计',
    'TOTAL_INVEST_OUTFLOW': '投资活动现金流出总计',
    'INVEST_NETCASH_OTHER': '投资活动产生的现金流量净额其他',
    'INVEST_NETCASH_BALANCE': '投资活动产生的现金流量净额合计',
    'NETCASH_INVEST': '投资活动产生的现金流量净额',
    'ISSUE_BOND': '发行债券收到的现金',
    'ISSUE_SUBBOND': '发行次级债券收到的现金',
    'ISSUE_OTHER_BOND': '发行其他债券收到的现金',
    'ACCEPT_INVEST_CASH': '吸收投资收到的现金',
    'SUBSIDIARY_ACCEPT_INVEST': '其中：子公司吸收少数股东投资收到的现金',
    'ISSUE_CD': '发行存款证收到的现金',
    'RECEIVE_ADD_EQUITY': '收到增加权益的现金',
    'RECEIVE_OTHER_FINANCE': '收到其他与筹资活动有关的现金',
    'FINANCE_INFLOW_OTHER': '筹资活动现金流入其他',
    'FINANCE_INFLOW_BALANCE': '筹资活动现金流入合计',
    'TOTAL_FINANCE_INFLOW': '筹资活动现金流入总计',
    'PAY_DEBT_CASH': '偿还债务支付的现金',
    'PAY_BOND_INTEREST': '支付债券利息的现金',
    'ISSUE_SHARES_EXPENSE': '发行股票支付的费用',
    'ASSIGN_DIVIDEND_PORFIT': '分配股利、利润或偿付利息支付的现金',
    'SUBSIDIARY_PAY_DIVIDEND': '其中：子公司支付给少数股东的股利、利润',
    'PAY_OTHER_FINANCE': '支付其他与筹资活动有关的现金',
    'FINANCE_OUTFLOW_OTHER': '筹资活动现金流出其他',
    'FINANCE_OUTFLOW_BALANCE': '筹资活动现金流出合计',
    'TOTAL_FINANCE_OUTFLOW': '筹资活动现金流出总计',
    'FINANCE_NETCASH_OTHER': '筹资活动产生的现金流量净额其他',
    'FINANCE_NETCASH_BALANCE': '筹资活动产生的现金流量净额合计',
    'NETCASH_FINANCE': '筹资活动产生的现金流量净额',
    'RATE_CHANGE_EFFECT': '汇率变动对现金及现金等价物的影响',
    'CCE_ADD_OTHER': '现金及现金等价物净增加额其他',
    'CCE_ADD_BALANCE': '现金及现金等价物净增加额合计',
    'CCE_ADD': '现金及现金等价物净增加额',
    'BEGIN_CCE': '期初现金及现金等价物余额',
    'END_CCE_OTHER': '期末现金及现金等价物余额其他',
    'END_CCE_BALANCE': '期末现金及现金等价物余额合计',
    'END_CCE': '期末现金及现金等价物余额',
    'NETPROFIT': '净利润',
    'ASSET_IMPAIRMENT': '资产减值准备',
    'PROVISION_INVEST_IMPAIRMENT': '计提投资减值准备',
    'TRANSFER_INVEST_IMPAIRMENT': '转回投资减值准备',
    'PROVISION_LOAN_IMPAIRMENT': '计提贷款减值准备',
    'OTHER_ASSET_IMPAIRMENT': '其他资产减值准备',
    'PROVISION_PREDICT_LIAB': '计提预计负债',
    'FA_IR_DEPR': '固定资产和投资性房地产折旧',
    'FIXED_ASSET_DEPR': '固定资产折旧',
    'OILGAS_BIOLOGY_DEPR': '油气资产和生物资产折旧',
    'IA_LPE_AMORTIZE': '无形资产和长期待摊费用摊销',
    'IA_AMORTIZE': '无形资产摊销',
    'LPE_AMORTIZE': '长期待摊费用摊销',
    'LONGASSET_AMORTIZE': '长期资产摊销',
    'DISPOSAL_LONGASSET_LOSS': '处置长期资产损失',
    'FA_SCRAP_LOSS': '固定资产报废损失',
    'FAIRVALUE_CHANGE_LOSS': '公允价值变动损失',
    'RECEIVE_WRITEOFF': '收回已核销',
    'INVEST_LOSS': '投资损失',
    'EXCHANGE_LOSS': '汇兑损失',
    'BOND_INTEREST_EXPENSE': '债券利息支出',
    'DEFER_TAX': '递延所得税',
    'DT_ASSET_REDUCE': '递延所得税资产减少',
    'DT_LIAB_ADD': '递延所得税负债增加',
    'INVENTORY_REDUCE': '存货减少',
    'LOAN_REDUCE': '贷款减少',
    'DEPOSIT_ADD': '存款增加',
    'LEND_ADD': '拆出资金增加',
    'FINASSET_REDUCE': '金融资产减少',
    'FINLIAB_ADD': '金融负债增加',
    'OPERATE_RECE_REDUCE': '经营性应收项目减少',
    'OPERATE_PAYABLE_ADD': '经营性应付项目增加',
    'OTHER': '其他',
    'FBOPERATE_NETCASH_OTHER': '间接法经营活动产生的现金流量净额其他',
    'FBOPERATE_NETCASH_BALANCE': '间接法经营活动产生的现金流量净额合计',
    'FBNETCASH_OPERATE': '间接法经营活动产生的现金流量净额',
    'DEBT_TRANSFER_CAPITAL': '债务转为资本',
    'CONVERT_BOND_1YEAR': '一年内到期的可转换公司债券',
    'FINLEASE_OBTAIN_FA': '融资租入固定资产',
    'UNINVOLVE_INVESTFIN_OTHER': '不涉及现金收支的投资和筹资活动其他',
    'END_CASH': '期末现金',
    'BEGIN_CASH': '期初现金',
    'END_CASH_EQUIVALENTS': '期末现金等价物',
    'BEGIN_CASH_EQUIVALENTS': '期初现金等价物',
    'FBCCE_ADD_OTHER': '间接法现金及现金等价物净增加额其他',
    'FBCCE_ADD_BALANCE': '间接法现金及现金等价物净增加额合计',
    'FBCCE_ADD': '间接法现金及现金等价物净增加额',
    'CREDIT_IMPAIRMENT_INCOME': '信用减值损失转回',
    'USERIGHT_ASSET_AMORTIZE': '使用权资产摊销',
    'NETCASH_OPERATENOTE': '经营活动产生的现金流量净额（附注）',
    'CCE_ADDNOTE': '现金及现金等价物净增加额（附注）',
}

def get_chinese_name(english_name):
    """
    获取财务科目的中文名称
    
    参数:
        english_name: 英文科目名
    
    返回:
        中文科目名，如果找不到则返回None（表示没有中文映射）
    """
    # 如果已经是中文，直接返回
    if english_name in FINANCIAL_ITEM_MAPPING:
        return FINANCIAL_ITEM_MAPPING[english_name]
    
    # 尝试匹配（不区分大小写）
    for key, value in FINANCIAL_ITEM_MAPPING.items():
        if key.upper() == english_name.upper():
            return value
    
    # 如果找不到，返回None（表示没有中文映射）
    return None

def convert_to_yi(value):
    """
    将数值从元转换为亿
    
    参数:
        value: 原始数值（元）
    
    返回:
        转换后的数值（亿），保留2位小数
    """
    try:
        num_value = float(value)
        return round(num_value / 100000000, 2)  # 除以1亿，保留2位小数
    except (ValueError, TypeError):
        return value  # 如果不是数值，返回原值

def format_financial_data_transpose(df, report_date="2024-12-31", is_financial_indicator=False):
    """
    将财务数据转置为"每个类目一行"的格式
    
    参数:
        df: 原始数据框
        report_date: 报告期，如 "2024-12-31"
        is_financial_indicator: 是否为财务指标数据（财务指标的科目本身就是中文）
    
    返回:
        转置后的数据框，每行一个指标/科目
    """
    if df is None or df.empty:
        return None
    
    # 查找报告期列
    date_col = None
    for col in df.columns:
        if '报告期' in col or 'REPORT_DATE' in col:
            date_col = col
            break
    
    if date_col is None:
        print("⚠ 未找到报告期列")
        return None
    
    # 筛选指定报告期的数据
    # 尝试多种日期格式匹配
    date_str = report_date.replace('-', '')
    filtered_df = df[
        df[date_col].astype(str).str.contains(date_str, na=False) |
        df[date_col].astype(str).str.contains(report_date, na=False)
    ]
    
    if filtered_df.empty:
        # 显示可用的报告期
        available_dates = df[date_col].unique()
        print(f"⚠ 未找到 {report_date} 的数据")
        print(f"可用报告期（最新5个）：{list(available_dates[-5:])}")
        # 使用最新的年报数据（12-31）
        filtered_df = df[df[date_col].astype(str).str.contains('12-31', na=False)]
        if not filtered_df.empty:
            filtered_df = filtered_df.iloc[[-1]]  # 取最新的
            print(f"使用最新年报数据: {filtered_df[date_col].iloc[0]}")
        else:
            filtered_df = df.iloc[[-1]]  # 取最后一行
            print(f"使用最新数据: {filtered_df[date_col].iloc[0]}")
    
    if filtered_df.empty:
        return None
    
    # 取第一行（如果有多行）
    row_data = filtered_df.iloc[0]
    actual_date = row_data[date_col]
    
    # 转置：每列（除了报告期）变成一行
    result_data = []
    for col in df.columns:
        if col != date_col:
            value = row_data[col]
            # 跳过空值或技术性列
            if pd.notna(value) and str(value) != 'False' and str(value) != 'nan':
                # 转换为亿单位
                value_yi = convert_to_yi(value)
                
                if is_financial_indicator:
                    # 财务指标的科目本身就是中文，不需要中文科目列
                    result_data.append({
                        '科目': col,
                        '数值(亿)': value_yi
                    })
                else:
                    # 其他报表需要中文科目列
                    chinese_name = get_chinese_name(col)
                    # 如果没有中文映射，显示"-"
                    if chinese_name is None or chinese_name == col:
                        chinese_name = "-"
                    result_data.append({
                        '科目': col,
                        '中文科目': chinese_name,
                        '数值(亿)': value_yi
                    })
    
    result_df = pd.DataFrame(result_data)
    return result_df

def get_and_display_financial_indicator(symbol, report_date="2024-12-31"):
    """
    获取并格式化显示财务指标
    
    参数:
        symbol: 股票代码
        report_date: 报告期，如 "2024-12-31"
    """
    print("=" * 80)
    print(f"获取股票 {symbol} 的财务指标数据（{report_date}）")
    print("=" * 80)
    
    # 去掉交易所后缀
    symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
    
    try:
        financial_data = ak.stock_financial_abstract_ths(symbol=symbol_clean)
        
        if financial_data is None or financial_data.empty:
            print("✗ 未获取到数据")
            return None
        
        print(f"\n✓ 成功获取财务指标数据（原始数据 {financial_data.shape}）")
        
        # 格式化显示（财务指标的科目本身就是中文，不需要中文科目列）
        formatted_data = format_financial_data_transpose(financial_data, report_date, is_financial_indicator=True)
        
        if formatted_data is not None and not formatted_data.empty:
            print(f"\n{'='*80}")
            print(f"格式化后的财务指标数据（{report_date}）")
            print(f"{'='*80}\n")
            print(formatted_data.to_string(index=False))
            print(f"\n共 {len(formatted_data)} 个指标")
            print(f"注：数值单位已转换为'亿'")
        else:
            print("⚠ 格式化后数据为空")
        
        return formatted_data
        
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_and_display_balance_sheet(symbol, report_date="2024-12-31"):
    """
    获取并格式化显示资产负债表
    
    参数:
        symbol: 股票代码
        report_date: 报告期，如 "2024-12-31"
    """
    print("\n" + "=" * 80)
    print(f"获取股票 {symbol} 的资产负债表（{report_date}）")
    print("=" * 80)
    
    # 确保有交易所后缀
    symbol_with_suffix = symbol
    if '.' not in symbol:
        if symbol.startswith(('000', '001', '002', '300')):
            symbol_with_suffix = symbol + '.SZ'
        elif symbol.startswith(('600', '601', '603', '605', '688')):
            symbol_with_suffix = symbol + '.SH'
        else:
            symbol_with_suffix = symbol + '.SZ'
    
    try:
        balance_sheet = ak.stock_balance_sheet_by_report_em(symbol=symbol_with_suffix)
        
        if balance_sheet is None or balance_sheet.empty:
            print("✗ 未获取到数据")
            return None
        
        print(f"\n✓ 成功获取资产负债表（原始数据 {balance_sheet.shape}）")
        
        # 查找报告期列
        date_col = None
        for col in balance_sheet.columns:
            if 'REPORT_DATE' in col or '报告期' in col:
                date_col = col
                break
        
        if date_col is None:
            print("⚠ 未找到报告期列")
            return None
        
        # 筛选指定报告期
        date_str = report_date.replace('-', '')
        filtered = balance_sheet[
            balance_sheet[date_col].astype(str).str.contains(date_str, na=False) |
            balance_sheet[date_col].astype(str).str.contains(report_date, na=False)
        ]
        
        if filtered.empty:
            print(f"⚠ 未找到 {report_date} 的数据，使用最新年报数据")
            filtered = balance_sheet[
                balance_sheet[date_col].astype(str).str.contains('12-31', na=False)
            ]
            if not filtered.empty:
                filtered = filtered.iloc[[-1]]
            else:
                filtered = balance_sheet.iloc[[-1]]
        
        if not filtered.empty:
            row_data = filtered.iloc[0]
            actual_date = row_data[date_col]
            
            # 转置：每列变成一行（排除技术性列）
            result_data = []
            exclude_cols = [date_col, 'SECUCODE', 'SECURITY_CODE', 'SECURITY_NAME_ABBR', 
                          'ORG_CODE', 'ORG_TYPE', 'REPORT_TYPE', 'REPORT_DATE_NAME',
                          'SECURITY_TYPE_CODE', 'NOTICE_DATE', 'UPDATE_DATE', 'CURRENCY',
                          'OPINION_TYPE', 'OSOPINION_TYPE', 'LISTING_STATE']
            
            for col in balance_sheet.columns:
                if col not in exclude_cols:
                    value = row_data[col]
                    # 只显示有值的列，排除_YOY列（同比增长列）
                    if pd.notna(value) and '_YOY' not in col:
                        # 尝试转换为数值，如果是数值且不为0，或者不是数值类型
                        try:
                            num_value = float(value)
                            if num_value != 0:
                                # 转换为亿单位
                                value_yi = convert_to_yi(value)
                                # 获取中文名
                                chinese_name = get_chinese_name(col)
                                # 如果没有中文映射，显示"-"
                                if chinese_name is None or chinese_name == col:
                                    chinese_name = "-"
                                result_data.append({
                                    '科目': col,
                                    '中文科目': chinese_name,
                                    '数值(亿)': value_yi
                                })
                        except:
                            if str(value) not in ['False', 'nan', 'None', '']:
                                # 非数值类型，不转换单位
                                chinese_name = get_chinese_name(col)
                                # 如果没有中文映射，显示"-"
                                if chinese_name is None or chinese_name == col:
                                    chinese_name = "-"
                                result_data.append({
                                    '科目': col,
                                    '中文科目': chinese_name,
                                    '数值(亿)': value
                                })
            
            result_df = pd.DataFrame(result_data)
            
            print(f"\n{'='*80}")
            print(f"格式化后的资产负债表（{actual_date}）")
            print(f"{'='*80}\n")
            print(result_df.to_string(index=False))
            print(f"\n共 {len(result_df)} 个科目")
            print(f"注：数值单位已转换为'亿'")
            return result_df
        else:
            return None
        
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_and_display_profit_statement(symbol, report_date="2024-12-31"):
    """
    获取并格式化显示利润表
    
    参数:
        symbol: 股票代码
        report_date: 报告期，如 "2024-12-31"
    """
    print("\n" + "=" * 80)
    print(f"获取股票 {symbol} 的利润表（{report_date}）")
    print("=" * 80)
    
    # 确保有交易所后缀
    symbol_with_suffix = symbol
    if '.' not in symbol:
        if symbol.startswith(('000', '001', '002', '300')):
            symbol_with_suffix = symbol + '.SZ'
        elif symbol.startswith(('600', '601', '603', '605', '688')):
            symbol_with_suffix = symbol + '.SH'
        else:
            symbol_with_suffix = symbol + '.SZ'
    
    try:
        profit = ak.stock_profit_sheet_by_report_em(symbol=symbol_with_suffix)
        
        if profit is None or profit.empty:
            print("✗ 未获取到数据")
            return None
        
        print(f"\n✓ 成功获取利润表（原始数据 {profit.shape}）")
        
        # 查找报告期列
        date_col = None
        for col in profit.columns:
            if 'REPORT_DATE' in col or '报告期' in col:
                date_col = col
                break
        
        if date_col is None:
            print("⚠ 未找到报告期列")
            return None
        
        # 筛选指定报告期
        date_str = report_date.replace('-', '')
        filtered = profit[
            profit[date_col].astype(str).str.contains(date_str, na=False) |
            profit[date_col].astype(str).str.contains(report_date, na=False)
        ]
        
        if filtered.empty:
            print(f"⚠ 未找到 {report_date} 的数据，使用最新年报数据")
            filtered = profit[
                profit[date_col].astype(str).str.contains('12-31', na=False)
            ]
            if not filtered.empty:
                filtered = filtered.iloc[[-1]]
            else:
                filtered = profit.iloc[[-1]]
        
        if not filtered.empty:
            row_data = filtered.iloc[0]
            actual_date = row_data[date_col]
            
            # 转置显示
            result_data = []
            exclude_cols = [date_col, 'SECUCODE', 'SECURITY_CODE', 'SECURITY_NAME_ABBR', 
                          'ORG_CODE', 'ORG_TYPE', 'REPORT_TYPE', 'REPORT_DATE_NAME',
                          'SECURITY_TYPE_CODE', 'NOTICE_DATE', 'UPDATE_DATE', 'CURRENCY',
                          'OPINION_TYPE', 'OSOPINION_TYPE', 'LISTING_STATE']
            
            for col in profit.columns:
                if col not in exclude_cols:
                    value = row_data[col]
                    if pd.notna(value) and '_YOY' not in col:
                        try:
                            num_value = float(value)
                            if num_value != 0:
                                # 转换为亿单位
                                value_yi = convert_to_yi(value)
                                # 获取中文名
                                chinese_name = get_chinese_name(col)
                                # 如果没有中文映射，显示"-"
                                if chinese_name is None or chinese_name == col:
                                    chinese_name = "-"
                                result_data.append({
                                    '科目': col,
                                    '中文科目': chinese_name,
                                    '数值(亿)': value_yi
                                })
                        except:
                            if str(value) not in ['False', 'nan', 'None', '']:
                                # 非数值类型，不转换单位
                                chinese_name = get_chinese_name(col)
                                # 如果没有中文映射，显示"-"
                                if chinese_name is None or chinese_name == col:
                                    chinese_name = "-"
                                result_data.append({
                                    '科目': col,
                                    '中文科目': chinese_name,
                                    '数值(亿)': value
                                })
            
            result_df = pd.DataFrame(result_data)
            
            print(f"\n{'='*80}")
            print(f"格式化后的利润表（{actual_date}）")
            print(f"{'='*80}\n")
            print(result_df.to_string(index=False))
            print(f"\n共 {len(result_df)} 个科目")
            print(f"注：数值单位已转换为'亿'")
            return result_df
        else:
            return None
        
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_and_display_cash_flow(symbol, report_date="2024-12-31"):
    """
    获取并格式化显示现金流量表
    
    参数:
        symbol: 股票代码
        report_date: 报告期，如 "2024-12-31"
    """
    print("\n" + "=" * 80)
    print(f"获取股票 {symbol} 的现金流量表（{report_date}）")
    print("=" * 80)
    
    # 确保有交易所后缀
    symbol_with_suffix = symbol
    if '.' not in symbol:
        if symbol.startswith(('000', '001', '002', '300')):
            symbol_with_suffix = symbol + '.SZ'
        elif symbol.startswith(('600', '601', '603', '605', '688')):
            symbol_with_suffix = symbol + '.SH'
        else:
            symbol_with_suffix = symbol + '.SZ'
    
    try:
        cash_flow = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol_with_suffix)
        
        if cash_flow is None or cash_flow.empty:
            print("✗ 未获取到数据")
            return None
        
        print(f"\n✓ 成功获取现金流量表（原始数据 {cash_flow.shape}）")
        
        # 查找报告期列
        date_col = None
        for col in cash_flow.columns:
            if 'REPORT_DATE' in col or '报告期' in col:
                date_col = col
                break
        
        if date_col is None:
            print("⚠ 未找到报告期列")
            return None
        
        # 筛选指定报告期
        date_str = report_date.replace('-', '')
        filtered = cash_flow[
            cash_flow[date_col].astype(str).str.contains(date_str, na=False) |
            cash_flow[date_col].astype(str).str.contains(report_date, na=False)
        ]
        
        if filtered.empty:
            print(f"⚠ 未找到 {report_date} 的数据，使用最新年报数据")
            filtered = cash_flow[
                cash_flow[date_col].astype(str).str.contains('12-31', na=False)
            ]
            if not filtered.empty:
                filtered = filtered.iloc[[-1]]
            else:
                filtered = cash_flow.iloc[[-1]]
        
        if not filtered.empty:
            row_data = filtered.iloc[0]
            actual_date = row_data[date_col]
            
            # 转置显示
            result_data = []
            exclude_cols = [date_col, 'SECUCODE', 'SECURITY_CODE', 'SECURITY_NAME_ABBR', 
                          'ORG_CODE', 'ORG_TYPE', 'REPORT_TYPE', 'REPORT_DATE_NAME',
                          'SECURITY_TYPE_CODE', 'NOTICE_DATE', 'UPDATE_DATE', 'CURRENCY',
                          'OPINION_TYPE', 'OSOPINION_TYPE', 'LISTING_STATE']
            
            for col in cash_flow.columns:
                if col not in exclude_cols:
                    value = row_data[col]
                    if pd.notna(value) and '_YOY' not in col:
                        try:
                            num_value = float(value)
                            if num_value != 0:
                                # 转换为亿单位
                                value_yi = convert_to_yi(value)
                                # 获取中文名
                                chinese_name = get_chinese_name(col)
                                # 如果没有中文映射，显示"-"
                                if chinese_name is None or chinese_name == col:
                                    chinese_name = "-"
                                result_data.append({
                                    '科目': col,
                                    '中文科目': chinese_name,
                                    '数值(亿)': value_yi
                                })
                        except:
                            if str(value) not in ['False', 'nan', 'None', '']:
                                # 非数值类型，不转换单位
                                chinese_name = get_chinese_name(col)
                                # 如果没有中文映射，显示"-"
                                if chinese_name is None or chinese_name == col:
                                    chinese_name = "-"
                                result_data.append({
                                    '科目': col,
                                    '中文科目': chinese_name,
                                    '数值(亿)': value
                                })
            
            result_df = pd.DataFrame(result_data)
            
            print(f"\n{'='*80}")
            print(f"格式化后的现金流量表（{actual_date}）")
            print(f"{'='*80}\n")
            print(result_df.to_string(index=False))
            print(f"\n共 {len(result_df)} 个科目")
            print(f"注：数值单位已转换为'亿'")
            return result_df
        else:
            return None
        
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_to_excel(symbol, financial_data, balance_sheet, profit_statement, cash_flow, report_date, output_dir="output"):
    """
    将财务数据保存到Excel文件
    
    参数:
        symbol: 股票代码
        financial_data: 财务指标数据（DataFrame）
        balance_sheet: 资产负债表数据（DataFrame）
        profit_statement: 利润表数据（DataFrame）
        cash_flow: 现金流量表数据（DataFrame）
        report_date: 报告期
        output_dir: 输出目录
    """
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 生成文件名
    symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
    date_str = report_date.replace('-', '')
    filename = f"{symbol_clean}_{date_str}_财务数据.xlsx"
    filepath = os.path.join(output_dir, filename)
    
    try:
        # 创建Excel写入器
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # 保存财务指标
            if financial_data is not None and not financial_data.empty:
                financial_data.to_excel(writer, sheet_name='财务指标', index=False)
                print(f"✓ 财务指标已保存到 sheet: 财务指标")
            
            # 保存资产负债表
            if balance_sheet is not None and not balance_sheet.empty:
                balance_sheet.to_excel(writer, sheet_name='资产负债表', index=False)
                print(f"✓ 资产负债表已保存到 sheet: 资产负债表")
            
            # 保存利润表
            if profit_statement is not None and not profit_statement.empty:
                profit_statement.to_excel(writer, sheet_name='利润表', index=False)
                print(f"✓ 利润表已保存到 sheet: 利润表")
            
            # 保存现金流量表
            if cash_flow is not None and not cash_flow.empty:
                cash_flow.to_excel(writer, sheet_name='现金流量表', index=False)
                print(f"✓ 现金流量表已保存到 sheet: 现金流量表")
        
        print(f"\n{'='*80}")
        print(f"✓ 所有数据已成功保存到: {filepath}")
        print(f"{'='*80}")
        return filepath
        
    except Exception as e:
        print(f"\n✗ 保存Excel文件失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    # 示例：获取平安银行（000001）的财务数据
    symbol = "603486"
    report_date = "2015-12-31"  # 可以修改为其他日期，如 "2023-12-31"
    
    print("提示：本示例使用平安银行（600519）作为演示")
    print(f"显示 {report_date} 的数据\n")
    
    # 1. 财务指标
    financial = get_and_display_financial_indicator(symbol, report_date)
    
    # 2. 资产负债表
    balance = get_and_display_balance_sheet(symbol, report_date)
    
    # 3. 利润表
    profit = get_and_display_profit_statement(symbol, report_date)
    
    # 4. 现金流量表
    cash_flow = get_and_display_cash_flow(symbol, report_date)
    
    print("\n" + "=" * 80)
    print("说明：")
    print("1. 数据已转换为'每个类目一行'的格式，便于查看")
    print("2. 如果指定的报告期不存在，会显示最新的年报数据")
    print("3. 可以修改 report_date 参数查看其他年份的数据")
    print("=" * 80)
    
    # 5. 保存到Excel
    print("\n" + "=" * 80)
    print("正在保存数据到Excel文件...")
    print("=" * 80)
    save_to_excel(symbol, financial, balance, profit, cash_flow, report_date)

if __name__ == "__main__":
    main()

