# Gildata MCP Server API 接口完整参考

> 数据来源：Gildata（恒生聚源）MCP Server
> 生成日期：2026-04-10
> 接口总数：287 个（结构化 281 + 智能工具 5 + 综合问数 1）

---

## 一、A股行情与交易数据

### 1.1 实时行情

| 接口名称 | 描述 |
|----------|------|
| `AShareLiveQuote` | 获取A股实时行情，包括价量、涨跌幅、委比、市值等 |
| `AShareTickQuote` | 获取A股在指定日期的分时行情数据，包括价量及涨跌幅 |
| `IndexLiveQuote` | 获取A股指数实时行情，包括价量、涨跌幅、委比等指标 |
| `AStockIndexTickQuote` | 获取A股指数在指定日期的分时行情数据 |

### 1.2 日行情与多周期行情

| 接口名称 | 描述 |
|----------|------|
| `StockDailyQuote` | 获取A股指定日行情，包括价量、涨跌幅、换手率等指标 |
| `StockMultiPeriodQuote` | 查询A股指定周期（日/周/月/季/半年/年）的复权行情数据 |
| `IndexDailyQuote` | 获取A股指数日行情，包括价量、涨跌幅、换手率等指标 |
| `IndexRangeQuotation` | 获取A股指数在指定区间内的行情数据，如区间涨跌幅、成交额等 |
| `StockRangeQuotation` | 获取A股在指定区间内的行情数据，如涨跌幅、成交额等 |

### 1.3 技术分析

| 接口名称 | 描述 |
|----------|------|
| `StockQuoteTechIndex` | 获取股票技术指标，如MA、RSI、KDJ、BOLL、MACD等 |
| `IndexQuoteTecIndicators` | 获取指数技术指标，如MA、MACD、KDJ、BOLL等分析数据 |

### 1.4 价值分析

| 接口名称 | 描述 |
|----------|------|
| `StockValueAnalysis` | 获取A股估值指标，如PE、PB、EV、股息率等，辅助投资价值判断 |
| `ValueAnalysisComparison` | 对比公司与同行业企业的估值指标，如PE、PB、EV等 |

### 1.5 风险分析

| 接口名称 | 描述 |
|----------|------|
| `StockRiskAnalysis` | 获取股票α、β、波动率、夏普比率等风险指标，评估投资风险 |
| `StockRiskFactorReport` | 获取股票市值、波动、流动性等九大核心风险因子 |

### 1.6 资金流向

| 接口名称 | 描述 |
|----------|------|
| `AStockCashFlow` | 获取个股在指定区间内的资金流入流出情况及北向资金数据 |
| `RealStockFundFlow` | 获取个股实时资金流向数据，包括主力、散户资金净额 |
| `StockMarketCapitalFlow` | 获取沪深京市场每日资金流入流出的统计数据 |
| `IndexCapitalFlow` | 获取指数每日资金流入流出情况 |

### 1.7 融资融券

| 接口名称 | 描述 |
|----------|------|
| `StockSecuritiesMargin` | 获取个股融资融券余额、买入额、卖出量等数据，分析市场情绪 |
| `MarginTradeStats` | 获取市场融资融券余额、买入额、卖出量等统计数据 |

### 1.8 市场统计

| 接口名称 | 描述 |
|----------|------|
| `MarketLimitUpDownCount` | 获取沪深京市场实时上涨、下跌、涨停、跌停家数统计 |
| `MarketSectorTradeStats` | 获取沪深京市场成交量、成交额等成交统计数据，支持多周期查询 |
| `StockMarketTradeStats` | 获取市场成交量、成交额、成交笔数等交易统计数据 |
| `StockMarketPledgeRepoStats` | 获取沪深市场无限售股份质押率、有限售股份质押率 |

### 1.9 龙虎榜

| 接口名称 | 描述 |
|----------|------|
| `DailyStockHeroDetails` | 获取股票龙虎榜上榜明细，包括成交额、买入卖出额及上榜原因 |
| `DailyStockBoStatistics` | 获取股票龙虎榜异动时前五大买卖营业部名称及交易额数据 |
| `RangeStockHeroStatistics` | 统计股票在指定区间内龙虎榜上榜次数、买卖额等 |

### 1.10 大宗交易

| 接口名称 | 描述 |
|----------|------|
| `StockBlockTrade` | 查询股票大宗交易信息，包括成交价、折价率、营业部等 |

---

## 二、A股基本面数据

### 2.1 公司基本信息

| 接口名称 | 描述 |
|----------|------|
| `CompanyBasicInfo` | 查询上市公司基本资料，包括注册信息、行业、概念、简介等 |
| `CompanyManagement` | 查询上市公司现任董事会、监事会、高管人员信息及简历 |
| `StockBelongIndustry` | 查询上市公司在申万、证监会等主流行业分类体系中的归属 |
| `StockBelongConcept` | 查询上市公司所属概念板块及入选依据、起始时间等信息 |
| `StockBelongIndex` | 查询上市公司归属的市场指数，如沪深300、上证50等 |
| `StockShareStructure` | 查询上市公司股本结构，包括总股本、流通股、限售股及变动原因 |

### 2.2 财务数据

| 接口名称 | 描述 |
|----------|------|
| `FinancialStatement` | 获取上市公司历史财务报表，支持合并/母公司、累计/单季数据 |
| `FinancialAnalysis` | 获取上市公司财务分析指标，涵盖盈利能力、偿债能力、成长能力、每股指标、营运能力等 |
| `FinancialDataComparison` | 对比公司与同行业企业的财务数据，如营收、利润、资产等 |
| `FinancialRatioComparison` | 对比公司与同行业企业的财务比率，如ROE、毛利率、净利率等 |
| `MainOperIncData` | 查询上市公司主营业务收入、成本、利润的分产品/行业/地区构成 |

### 2.3 财报披露

| 接口名称 | 描述 |
|----------|------|
| `FinanceReportDisclosure` | 查询上市公司定期报告的预计及实际披露时间，跟踪披露进度 |
| `PerformanceExpress` | 获取上市公司业绩快报数据，包括营收、利润等初步财务指标 |
| `PerformanceForecast` | 获取上市公司业绩预告数据，包括净利润预期、增速等 |
| `AShareFinancialAnnouncementText` | 获取A股公司财务报告公告原文内容 |
| `AShareFinancialReportReview` | 获取A股公司财报业绩点评文本，涵盖业绩概览、盈利预测等 |

### 2.4 分红与股权

| 接口名称 | 描述 |
|----------|------|
| `BonusStock` | 查询上市公司分红记录、方案，支持多股批量查询及时间区间筛选 |
| `ShareholderNum` | 查询上市公司股东户数、户均持股数及变动情况，分析股权集中度 |
| `Top10ShareHolders` | 查询上市公司前十大股东持股信息，包括持股量及比例 |
| `Top10FloatShareHolders` | 查询上市公司前十大流通股股东持股信息，包括持股数量及比例 |

### 2.5 一致预期与评级

| 接口名称 | 描述 |
|----------|------|
| `ConsensusExpectation` | 获取上市公司未来三年盈利预测数据，如营收、净利润等 |
| `ConsensusExpectationDetail` | 获取各券商对A股的盈利预测明细数据，包括营收、净利润及EPS等 |
| `InstitutionalRating` | 获取上市公司机构评级次数、评级分数及机构家数 |

### 2.6 员工与薪酬

| 接口名称 | 描述 |
|----------|------|
| `EmployeeComposition` | 查询上市公司员工按职称、学历、年龄等分类的构成情况 |
| `NumberOfEmployeesAndSalary` | 查询上市公司员工人数、薪酬总额、人均薪酬等数据 |

### 2.7 供应商与客户

| 接口名称 | 描述 |
|----------|------|
| `ProcurementAndSales` | 查询上市公司前五大供应商、客户及采购、销售占比 |
| `HoldShareCompany` | 查询上市公司控股、参股公司信息，包括参控比例、财务数据等 |
| `HoldingSecuritiesAssets` | 查询上市公司持有的证券资产明细，包括股票、基金等 |

---

## 三、A股新闻与舆情

### 3.1 新闻舆情

| 接口名称 | 描述 |
|----------|------|
| `StockNewslist` | 查询股票相关舆情，支持按情感类型、证券代码筛选 |
| `NewsInfoList` | 检索全网舆情，支持按关键词、来源、情感类型筛选 |
| `NewsPublicOpinionList` | 检索全网新闻舆情，支持多条件筛选 |
| `IndustryNewsFlash` | 获取特定行业公众号推送的产业快讯资讯 |
| `IndustryNewslist` | 查询行业舆情，支持按行业类型、情感类型筛选 |
| `MacroNewslist` | 查询宏观舆情，支持按区域、情感类型筛选经济预测及事件 |
| `MarketNewslist` | 查询市场舆情，支持按市场类型筛选 |
| `OrganizationNewslist` | 查询机构相关舆情，支持按机构名称、情感类型筛选 |
| `SecurityNewslist` | 查询债券相关舆情，支持按情感类型、证券代码筛选风险信息 |

### 3.2 公告与披露

| 接口名称 | 描述 |
|----------|------|
| `AShareAnnouncement` | 检索A股上市公司公告，支持多条件筛选 |
| `ShareholdersMeeting` | 查询上市公司股东大会信息，包括议案内容、登记日、召开时间及决议 |

### 3.3 互动与研究

| 接口名称 | 描述 |
|----------|------|
| `InteractivePlatformReport` | 获取上市公司在交易所互动平台的投资者问答记录 |
| `CorporateResearchViewpoints` | 获取研报中对公司盈利、市场份额、产品等维度的分析观点 |
| `ResearchReport` | 查询券商研报，支持按机构、作者、行业、评级等条件精准筛选 |
| `InstitutionInvestigation` | 查询上市公司机构调研记录，包括机构、日期、内容及人员 |

---

## 四、A股股权与增减持

### 4.1 股权变动

| 接口名称 | 描述 |
|----------|------|
| `StockPledge` | 查询上市公司股权质押信息，包括质押方、数量、起止日期等 |
| `ShareholdingChangePlan` | 查询上市公司股东增减持计划，包括数量、时间、进度等 |
| `RestrictedStockLifting` | 查询上市公司限售股解禁信息，包括数量、日期等 |
| `StockRepurchase` | 查询上市公司股票回购计划及执行进度 |

### 4.2 融资发行

| 接口名称 | 描述 |
|----------|------|
| `IpoIssuanceInfo` | 查询上市公司IPO发行信息，包括价格、中签率、主承销商及募资额 |
| `StockShareIssuance` | 查询上市公司增发股票的核心指标、资金信息及关键日期 |
| `StockSharePlacement` | 查询上市公司配股信息，包括配股比例、价格、募集资金及关键日期 |
| `ConvertibleBondIssue` | 查询上市公司可转债发行信息、认购条款及关键日期 |

### 4.3 激励与持股

| 接口名称 | 描述 |
|----------|------|
| `StockIncentive` | 查询上市公司股权激励计划，包括激励总数、行权价格等 |
| `StockEmpOwnershipPlan` | 查询上市公司员工持股计划详情，包括规模、参与人等 |
| `ExecutiveHoldingsAndComp` | 查询上市公司高管持股数量、报酬及变动情况 |

### 4.4 停复牌

| 接口名称 | 描述 |
|----------|------|
| `StockHaltResume` | 查询股票停复牌信息，包括日期、天数、原因等详细记录 |

---

## 五、行业与板块

### 5.1 行业数据

| 接口名称 | 描述 |
|----------|------|
| `IndustryDailyQuote` | 获取行业在指定日期的日行情数据，包括收盘价、成交量及涨跌幅 |
| `IndustryRangeQuote` | 获取行业在指定区间内的行情数据，如涨跌幅、成交额等 |
| `IndustryIndexLiveQuote` | 获取行业指数实时行情，包括最新价、涨跌幅、量比、委比等 |
| `IndustryIndexTickQuote` | 获取申万、证监会行业指数在指定日期的分时行情走势 |
| `IndustryCapitalFlow` | 获取行业在指定区间内的资金流入流出情况 |
| `IndustryRealSectorFundFlow` | 获取指定板块的实时资金流向数据，包括主力、散户资金净额等 |
| `IndustryFinancialAnalysis` | 获取A股行业财务分析指标，涵盖盈利能力、偿债能力、成长能力等 |
| `IndustryConstituentStocks` | 获取行业板块成分股列表及权重，支持多行业分类查询 |
| `IndustrySectorConstituentRank` | 获取板块成分股并按涨跌幅、换手率等指标进行排序 |
| `IndustryAnalysisViewpoints` | 获取研报中对行业趋势、竞争格局、政策等的分析观点 |

### 5.2 概念板块

| 接口名称 | 描述 |
|----------|------|
| `ConceptConstituentStocks` | 获取概念板块成分股列表及对应证券代码 |
| `ConceptCapitalFlow` | 获取概念在指定区间内的资金流入流出情况 |
| `ConceptDailyIndexQuote` | 获取概念板块指数在指定日期的日行情数据，反映板块市场动态 |
| `ConceptIndexLiveQuote` | 获取概念板块指数实时行情，包括价量、涨跌幅、委比等 |
| `ConceptIndexTickQuote` | 获取概念板块指数在指定日期的分时行情数据及走势 |
| `ConceptRangeIndexQuote` | 获取概念板块指数在指定区间内的行情数据及波动情况 |
| `ConceptSectorConstituentRank` | 获取板块成分股并按涨跌幅、换手率等指标排序 |

### 5.3 板块排序与资金流

| 接口名称 | 描述 |
|----------|------|
| `SectorRank` | 获取板块列表并按涨跌幅、换手率等指标排序，支持多板块类型 |
| `SectorFundFlowRank` | 按资金流向指标对板块进行排序，支持主力、散户资金分析 |
| `RealSectorFundFlow` | 获取指定概念或地域板块的实时资金流向数据 |
| `MarketFundFlowRank` | 按资金流向指标对市场成分股进行排序，支持多维度分析 |
| `MarketSectorConstituentRank` | 获取市场板块成分股列表，支持按涨跌幅、成交额等指标排序 |
| `MarketPerformanceComparison` | 对比公司与同行业企业的市场表现，如涨跌幅、成交额等 |

---

## 六、基金数据

### 6.1 基金基本信息

| 接口名称 | 描述 |
|----------|------|
| `FundBasicInfoReport` | 查询基金基础信息，包括分类、托管人、业绩基准、运作方式等 |
| `FundRateReport` | 查询基金申购、赎回、管理、托管等费率信息 |
| `FundAnnouncement` | 检索基金公告，支持多条件筛选 |
| `FundNewsList` | 查询基金相关舆情，支持按情感类型、证券代码筛选新闻内容 |
| `FundAwardsReport` | 查询基金历年获奖记录，包括奖项名称、颁奖机构等详情 |
| `FundDividendHistoryReport` | 查询基金历史分红记录，包括除息日、派现比例等 |

### 6.2 基金业绩与风险

| 接口名称 | 描述 |
|----------|------|
| `FundNetTrendReport` | 获取基金在指定区间内的累计收益率走势数据 |
| `FundNetValuePeriodReport` | 获取基金在自然月、季、年度的收益率数据，支持多基对比 |
| `NetFundUnitValueReport` | 获取场外基金历史净值数据，包括单位净值、累计净值、日增长率 |
| `StageIncreaseReport` | 获取基金在指定时间区间的收益率及同类排名 |
| `FundIncomeRiskReport` | 获取基金夏普比率、最大回撤等风险收益指标及排名 |
| `FundDynamicRetracementReport` | 获取基金在指定区间内的动态回撤数据，支持单基查询与多基对比 |
| `FundProfitabilityProbabilityReport` | 获取基金在不同持有期下的盈利概率数据 |
| `FundProfitLossRatioReport` | 获取基金日、月收益率盈利与亏损占比数据，分析业绩稳定性 |

### 6.3 基金持仓

| 接口名称 | 描述 |
|----------|------|
| `ShareholdingDetailReport` | 获取基金持仓股票明细，包括市值、占比、行业等 |
| `StockConcentrationReport` | 获取基金前五大重仓股占净值比等持股集中度数据 |
| `StockTurnoverRateReport` | 获取基金各报告期持股换手率，反映基金经理交易活跃度 |
| `FundIndustryDistributionReport` | 获取基金在申万、中信等行业分类下的持仓占比，分析配置结构 |
| `IndustryConcentrationReport` | 获取基金在申万、中信等行业分类下的持仓集中度 |
| `CurrentShareStyleReport` | 获取基金在价值、成长、大盘、小盘等风格上的持仓占比 |
| `FundMarketValueAndValuation` | 获取基金持仓股票总市值、PE、PB、股息率等估值指标 |
| `FundHoldingProfitabilityReport` | 获取基金持仓股票的EPS、ROE、盈利质量等盈利能力指标 |
| `DebtDetailsReport` | 获取基金前五大重仓债券及可转债明细，包括市值、评级等 |
| `FundDebtConcentration` | 获取基金前五大重仓债券占净值比等持债集中度数据 |
| `BondDistributionReport` | 获取基金债券持仓按一级、二级分类的占比分布 |
| `HolderStructureNewReport` | 查询基金持有人户数、机构与个人持有占比等结构信息 |
| `FOFAssetDistReport` | 获取基金资产在股票、债券、现金等类别中的分布及占比 |
| `FOFFundPositionReport` | 查询基金持有的其他基金明细，包括市值、占比、基金经理等 |
| `FOFFundTypeReport` | 获取基金持有其他基金的分类占比数据，分析资产配置 |
| `FundConcentrationReport` | 获取基金持有其他基金的集中度数据，如前五大占比 |

### 6.4 基金规模与资产

| 接口名称 | 描述 |
|----------|------|
| `FundAssetSizeReport` | 查询基金资产规模、份额变动及申赎情况，分析资金流动趋势 |

### 6.5 基金经理

| 接口名称 | 描述 |
|----------|------|
| `FundManagerInfoReport` | 查询基金经理个人背景、从业年限、管理规模、代表产品等 |
| `FundHistoryManagerReport` | 查询基金历任基金经理信息，包括任职时长、业绩等数据 |
| `FundManagerExperienceReport` | 获取基金经理在历任公司的任职履历，包括职务、任职时长等 |
| `FundManagerScaleReport` | 查询基金经理管理总规模及按类型细分规模数据 |
| `FundManagerImageReport` | 获取基金经理多维能力评分与排名，涵盖盈利能力、风控能力等 |
| `FundManagerViewPointReport` | 查询基金经理在各报告期的投资策略、运作分析及市场展望等观点 |
| `FundManagerAwardsReport` | 查询基金经理历年获奖记录，包括奖项名称、颁奖机构等 |
| `FundManagerCumulativeReturn` | 获取基金经理在指定区间内的累计收益及日收益率曲线 |
| `FundManagerStageRevenueReport` | 获取基金经理在指定时间区间的收益表现及排名 |
| `FundManagerStageRevenueRank` | 获取基金经理在指定类别和时间区间内的收益率及排名 |
| `FundManagerRevenueStatisReport` | 获取基金经理在自然月、季、年度的收益表现及同类排名 |
| `FundManagerRiskReturnReport` | 获取基金经理在指定区间内的风险收益指标及同类排名 |
| `ManagerProductsIncome` | 查询基金经理历任产品的任期收益、年化收益等数据 |
| `FundManagerPositionDetailReport` | 获取基金经理持仓股票明细，包括市值、占比、行业等 |
| `FundManagerStockConcentrationReport` | 获取基金经理前十大重仓股占比等持股集中度数据 |
| `FundManagerIndustryFixedReport` | 获取基金经理在指定报告期的行业配置比重，分析投资偏好 |
| `FundManagerIndustryRegularReport` | 获取基金经理在指定报告期的行业持仓集中度，评估风险分散能力 |
| `FundManagerConceptPositionReport` | 获取基金经理重仓股概念持仓详情，包括规模、占比及排名数据 |
| `FundManagerAssetDistReport` | 获取基金经理在股票、债券、现金等资产上的配置比例 |
| `FundManagerTurnoverRateReport` | 查询基金经理在报告期内的半年度、年度换手率数据 |
| `FundManagerBondHoldingsDetail` | 获取基金经理持仓债券明细，包括市值、评级、持仓变动及占比 |
| `FundManagerBondConcentrationReport` | 获取基金经理持仓债券的集中度数据，分析重仓债券分布特征 |
| `FundManagerBondDistributionReport` | 获取基金经理在国债、企业债等券种上的配置比例数据 |
| `FundManagerFundPositionReport` | 查询基金经理持仓股票被其管理的其他基金共同持有的情况 |

### 6.6 基金公司

| 接口名称 | 描述 |
|----------|------|
| `FundCompanyFund` | 获取基金公司旗下基金列表 |
| `FundCompanyMajorhs` | 获取基金公司主要股东及持股比例 |
| `FundCompanyFinanceReport` | 获取基金公司营业收入、净利润、资产等核心财务数据 |
| `FundCompanyStageRevenue` | 获取基金公司固定时间周期内的收益表现及同类排名 |
| `FundCompanyTeamStability` | 获取基金公司经理人数及近一年变动情况及不同管理年限的人数分布等信息 |

### 6.7 场内基金

| 接口名称 | 描述 |
|----------|------|
| `FundIntradayDailyQuote` | 获取场内基金在指定交易日的行情数据，包括价量、涨跌幅、换手率等 |
| `FundIntradayCapitalFlow` | 获取场内基金每日资金流入流出及大单净买入情况 |

### 6.8 智能选基

| 接口名称 | 描述 |
|----------|------|
| `FundMultipleFactorFilter` | 智能筛选基金，支持收益率、回撤、行业、基金经理等多维度 |

---

## 七、债券数据

### 7.1 债券基本信息

| 接口名称 | 描述 |
|----------|------|
| `CreditBondBaseInfo` | 查询债券基本信息，包括发行、评级、付息、行权等要素 |
| `BasicInfoBondIssuer` | 查询发债主体基本资料，包括注册信息、行业、存续债券等 |
| `DefaultBondList` | 查询违约债券清单，支持按时间、发行人、类型等多维筛选 |
| `BondAnnouncement` | 检索债券市场公告，支持多条件筛选，涵盖评级、兑付等类型 |

### 7.2 债券行情

| 接口名称 | 描述 |
|----------|------|
| `BondDailyClosingQuotes` | 获取债券在指定日期的收盘行情，包括价量、到期收益率及久期 |
| `DebtValuation` | 获取债券中债估值数据，支持单日查询及时间序列拉取 |
| `MostActiveRateBondQuotation` | 获取利率债各期限最活跃券的收益率及涨跌情况，反映市场风向 |

### 7.3 债券评级

| 接口名称 | 描述 |
|----------|------|
| `BondRatingOverview` | 查询债券的债项、发行人、担保人评级信息，支持多维度筛选 |
| `BondRatingChange` | 查询债券债项评级变动记录，支持多维度筛选 |
| `BondIssuerRatingChange` | 查询发债主体评级变动记录，支持按企业性质、评级机构等筛选 |
| `GuarantorRatingChange` | 查询担保人评级变动记录，支持多维度筛选 |
| `CCDCImpliedRatingChange` | 查询债券中债隐含评级变动记录，支持多维度筛选 |
| `BondIssuerFirstDefault` | 查询发债主体首次违约记录，包括违约日期、行业等 |

### 7.4 发债公司财务

| 接口名称 | 描述 |
|----------|------|
| `BondFinancialAnalysis` | 获取发债公司财务分析指标，如盈利能力、偿债能力等 |
| `FinancialStatements` | 获取发债公司历史财务报表数据，覆盖三表主要科目 |
| `BondMainOperIncData` | 查询发债公司主营业务收入、成本、利润的分产品/行业/地区构成 |

### 7.5 债券特殊数据

| 接口名称 | 描述 |
|----------|------|
| `BondRealtyPaymentDetail` | 查询发债房企境内债券付息明细及付息压力相关数据 |
| `MarketIssueStatByBondType` | 统计债券发行量，支持按类型、期限、评级等维度筛选 |
| `InterestRateDebtViewpoints` | 获取研报中对利率债基本面、政策、资金面等的分析观点 |

---

## 八、港股数据

### 8.1 港股基本信息

| 接口名称 | 描述 |
|----------|------|
| `HKCompanyBasicInfo` | 获取香港上市公司基本资料，包括注册信息、行业、简介等 |
| `HKStockBelongConcept` | 查询香港上市公司所属概念板块及入选时间等信息 |
| `HKCorpRptDiscDate` | 查询港股公司定期报告的预计及实际披露时间，跟踪合规情况 |

### 8.2 港股行情

| 接口名称 | 描述 |
|----------|------|
| `HShareLiveQuote` | 获取港股实时行情，包括价量、涨跌幅、委比等关键指标 |
| `HShareTickQuote` | 获取港股在指定日期的分时行情数据，如价量、涨跌幅等 |
| `HKStockDailyQuotes` | 获取港股在指定日期的日行情数据，包括开盘价、收盘价及成交额 |
| `HKMulCycleStockQuote` | 获取港股的日周月年K线行情数据，如涨跌幅、成交额等 |
| `HKRangeStockQuote` | 获取港股在指定区间内的行情数据，如涨跌幅、成交额等 |
| `HKStockHaltResume` | 查询港股在指定区间内的停复牌记录，包括停复牌日期、停牌天数及停牌原因 |

### 8.3 港股指数

| 接口名称 | 描述 |
|----------|------|
| `HKStockIndexLiveQuote` | 获取港股指数实时行情，包括价量、涨跌幅、量比等 |
| `HKStockIndexTickQuote` | 获取港股指数在指定日期的分时行情数据，追踪盘中走势 |
| `HKDailyIndexQuote` | 获取港股指数在指定日期的日行情数据，涵盖涨跌幅、成交量等 |
| `HKRangeIndexQuote` | 获取港股指数在指定区间内的行情数据，如涨跌幅、成交额等 |

### 8.4 港股分析

| 接口名称 | 描述 |
|----------|------|
| `HKStockTechInds` | 获取港股技术指标，如MA、KDJ、RSI、BOLL等 |
| `HKStockValueAnalysis` | 获取港股估值指标，如PE、PB、PS、股息率等 |

### 8.5 港股财务

| 接口名称 | 描述 |
|----------|------|
| `HKFinancialStatement` | 获取港股公司历史财务报表数据，覆盖三大报表全层级科目 |
| `HKMainOperIncData` | 查询港股公司主营业务收入、成本、利润的分产品/行业/地区构成 |

### 8.6 港股其他

| 接口名称 | 描述 |
|----------|------|
| `HKStockAnnouncement` | 检索港股上市公司公告，支持多条件筛选 |
| `HKStockRepurchase` | 查询港股上市公司的股份回购明细 |
| `HKStockIrregularities` | 获取香港证监会和港交所处罚的港股违规事项信息 |
| `HSGTTradeStats` | 获取北向、南向资金成交额、成交笔数等跨境交易统计数据 |

---

## 九、美股数据

| 接口名称 | 描述 |
|----------|------|
| `USCompanyBasicInfo` | 获取美股公司基本资料，包括注册与办公地址、成立日期、注册资本、所属行业、公司业务简介等 |
| `USFinancialStatement` | 获取美股公司历史财务报表，支持单季、累计数据查询 |
| `USMainOperIncData` | 查询美股按行业、产品或地区划分的主营收入构成 |
| `USStockDailyQuotes` | 获取美股在指定日期的日行情数据，包括收盘价、成交量及涨跌幅 |
| `USStockRangeQuotation` | 获取美股在指定区间内的行情数据，如涨跌幅、成交额等 |
| `USStockTechInds` | 获取美股技术指标，如MA、KDJ、RSI、BOLL等，辅助技术面分析 |
| `USValuationMetrics` | 获取美股估值指标，如PE、PB、PS、PCF等，支持多公司对比 |

---

## 十、指数数据

| 接口名称 | 描述 |
|----------|------|
| `IndexConstituentStocks` | 查询指数成分股列表及权重，支持多指数对比及动态追踪 |
| `IndexConstituentIndustryDist` | 获取指数成分股在申万、中信等行业分类下的分布及权重 |
| `IndexConstituentConceptDist` | 获取指数成分股在不同概念下的分布及权重 |

---

## 十一、宏观与行业经济

### 11.1 宏观数据

| 接口名称 | 描述 |
|----------|------|
| `MacroIndustryEDB` | 查询中国宏观、行业经济、国际宏观等经济指标数据 |
| `MacroeconomicAnalysisViewpoints` | 获取研报中对GDP、CPI、PMI、政策等宏观维度的分析观点 |
| `RegionalEconomicData` | 查询城投区域经济、财政、债务等指标，支持多级行政区划 |
| `RegionalUrbanInvestmentData` | 查询城投平台风险评级、债务、财务等明细数据 |

### 11.2 政策与会议

| 接口名称 | 描述 |
|----------|------|
| `PolicyMeetingsList` | 查询国内经济金融领域政策会议动态及内容，解析政策逻辑 |
| `OfficialSpeechEventList` | 查询国内外重要官员讲话及活动信息 |
| `LawsRegulations` | 查询法律法规信息，支持按类型、关键词筛选 |

---

## 十二、工商与法律

### 12.1 工商信息

| 接口名称 | 描述 |
|----------|------|
| `CompanyArchives` | 查询工商企业工商基本信息，包括法人、注册资金、社保人数等 |
| `ExecutivesInfo` | 查询工商企业董事会、监事会、高管人员信息及任职时间 |
| `BusinessInfoChange` | 查询工商企业工商变更记录，包括高管变动、注册资本变更等 |
| `CorporateEquityPledge` | 查询工商企业股东股权质押信息，包括质押方、数量、日期等 |
| `ExternalGuarantee` | 查询企业作为担保人的对外担保信息，包括担保金额、对象及期限 |
| `BankCreditInfo` | 查询企业银行授信总额、已使用额度及授信机构明细 |
| `AdministrativeLicenseInfo` | 查询企业行政许可信息，包括许可文件、有效期等 |
| `PatentAnnualStatistics` | 查询企业历年专利申请、公布数量及增长率 |
| `Tendering` | 查询上市公司参与的招投标项目信息，包括金额、机构等 |
| `AbnormalOperationInfo` | 查询企业经营异常记录，包括列入原因、移除情况等 |
| `SeriousViolationInfo` | 查询工商企业因严重违法被列入失信名单的记录及移除情况 |

### 12.2 法律诉讼

| 接口名称 | 描述 |
|----------|------|
| `CaseInfoList` | 查询企业法院立案信息，包括案号、当事人、法院等 |
| `CourtAnnounce` | 查询企业法院公告信息，包括公告类型、法院名称等详情 |
| `CourtSession` | 查询企业开庭公告信息，包括案号、案由、当事人、法院等 |
| `Judgement` | 查询企业相关裁判文书信息，包括案由、法院、审理程序及判决结果 |
| `StockSuitArbitration` | 查询上市公司诉讼仲裁案件信息，包括案由、涉案金额及最新进展 |
| `RegulatoryPenaltyList` | 查询企业监管处罚信息，包括处罚类型、原因、机构及金额 |
| `StockViolationPenalty` | 查询上市公司违规处罚事件，包括原因、处罚机构等 |
| `Executee` | 查询企业被执行人信息，包括立案时间、执行标的及案件状态 |
| `DishonestPersonList` | 查询企业失信被执行人信息，包括立案时间、执行法院等 |
| `LimitHighConsume` | 查询企业及相关人员被限制高消费的信息及执行法院等 |

### 12.3 税务

| 接口名称 | 描述 |
|----------|------|
| `MajorTaxViolationInfo` | 查询企业重大税收违法信息，包括违法事实、处罚依据等 |
| `TaxAbnormalEnterpriseInfo` | 查询企业被认定为纳税非正常户的相关信息，包括欠税金额及原因 |
| `TaxArrearsAnnouncement` | 查询工商企业欠税信息，包括税种、金额、税务机关等 |

---

## 十三、理财与信托

### 13.1 理财产品

| 接口名称 | 描述 |
|----------|------|
| `ProductBasicInfoList` | 获取理财产品基本信息，包括分类、规模、收益基准等 |
| `FinancialProductFilter` | 按多条件筛选理财产品，返回产品明细、风险等级及收益指标 |
| `WealthProdFilterStats` | 对筛选出的理财产品进行求和、平均、计数等统计 |
| `NewWealthProdDetail` | 获取新发银行理财产品明细，支持按机构、风险等级筛选 |
| `WealthProductAnnouncement` | 检索理财产品公告，支持多条件筛选 |
| `NewProdStats` | 统计新发银行理财产品个数、规模、平均业绩基准等 |
| `NewProdTimeSeriesByType` | 统计新发理财产品按类别的时间序列数据及规模占比 |

### 13.2 理财产品分析

| 接口名称 | 描述 |
|----------|------|
| `ProductPerformance` | 获取理财产品收益率、排名、超基准收益等业绩数据 |
| `ProductReturnRiskIndicator` | 获取理财产品夏普比率、最大回撤、标准差等风险收益指标 |
| `ProductWinRatePerformance` | 获取理财产品历史盈利概率及平均收益率，支持多持有期 |
| `ProductPositionFeature` | 获取理财产品大类资产持仓市值及占比 |
| `ProductAssetAllocDetail` | 查询理财产品持有的股票、债券、基金等资产明细及占比 |

### 13.3 代销与管理人

| 接口名称 | 描述 |
|----------|------|
| `AgentOrgOverview` | 统计代销机构代销各管理人产品的个数、规模及分类情况 |
| `AgentOrgRanking` | 获取代销机构在各类理财产品上的代销规模、个数排名 |
| `MgrAgentOrgAnalysis` | 统计管理人产品在各代销机构的代销情况，支持分类查询 |
| `MgrProdCategoryStats` | 统计管理人旗下产品按类型、风险、期限等分类的规模与数量 |
| `MgrRanking` | 获取银行理财管理人在各类产品上的规模、收益排名及统计数据 |

---

## 十四、房地产

| 接口名称 | 描述 |
|----------|------|
| `ListPropertyThreeRedLine` | 获取上市房企"三道红线"指标及档位评估结果 |

---

## 十五、委托理财

| 接口名称 | 描述 |
|----------|------|
| `ListedCorpEntrustFinDetail` | 查询上市公司购买理财产品的详细明细，包括金额、期限等 |
| `ListedCorpEntrustFinTotal` | 统计上市公司购买理财产品的个数、金额及分类汇总 |

---

## 十六、新三板

| 接口名称 | 描述 |
|----------|------|
| `NewThirdBoardAnnouncement` | 检索新三板挂牌公司公告，支持多条件筛选 |

---

## 十七、期权数据

| 接口名称 | 描述 |
|----------|------|
| `DailyRiskMetricsReport` | 获取期权合约的Delta、Gamma、Vega等每日风险指标，评估价格敏感度 |

---

## 十八、组合模拟

| 接口名称 | 描述 |
|----------|------|
| `PortfolioBuild` | 执行模拟组合建仓操作，返回组合ID及调仓结果 |
| `PortfolioPositionQuery` | 查询模拟组合在指定日期的持仓明细，包括证券代码、权重及市值等 |
| `PortfolioIndicatorQuery` | 查询模拟组合的业绩、风险、收益等指标数据 |
| `PortfolioRebalance` | 执行模拟组合的调仓或再平衡操作，更新持仓权重 |
| `TradeFlowQuery` | 查询模拟组合在指定区间内的交易流水明细 |

---

## 十九、机构投资者

| 接口名称 | 描述 |
|----------|------|
| `InstitutionInvestor` | 查询上市公司机构股东持股信息，包括持股数量、比例及机构类型 |

---

## 二十、智能工具接口（mcp__gildata-tools）

| 接口名称 | 描述 |
|----------|------|
| `FinQuery` | 金融结构化数据查询，覆盖股票、基金、债券、指数、行情、理财、期权等结构化数据 |
| `FinancialResearchReport` | 研报智能问答，解析自然语言提问，获取研报中宏观行业、公司、基金、市场趋势等专业信息 |
| `MacroIndustryData` | 宏观经济与行业经济智能数据定位获取，覆盖中国宏观、行业经济、地方宏观及全球多经济体指标 |
| `SmartFundSelection` | 智能选基，支持多维条件筛选基金（含ETF），支持业绩、风险、持仓、基金经理等多维度 |
| `SmartStockSelection` | 智能选股，支持多维条件筛选股票、上市公司、板块、指数，支持财务、行情、技术指标组合筛选 |

---

## 二十一、综合问数接口（mcp__gildata-finquery）

| 接口名称 | 描述 |
|----------|------|
| `FinGeneralQuery` | 金融综合问数，基于恒生聚源金融数据库，覆盖股票、基金、债券、指数、行情、理财、期权等全品类金融数据 |

---

## 二十二、全量数据接口（mcp__gildata-api）

| 接口名称 | 描述 |
|----------|------|
| `FinRagApi` | 金融数据全量API，基于恒生聚源金融数据库，覆盖股票、基金、债券、指数、行情、理财、期权等金融产品数据，支持宏观行业经济数据、研报、工商信息查询 |

---

## 附录：已封装使用情况

| 类别 | 已封装数量 | 总可用数量 | 封装率 |
|------|-----------|-----------|--------|
| 市场分析师 | 5 | ~15 | 33% |
| 基本面分析师 | 8 | ~25 | 32% |
| 新闻分析师 | 5 | ~15 | 33% |
| 社交媒体分析师 | 3 | ~5 | 60% |
| **合计** | **22** | **287** | **8%** |

> 注：大量接口（债券、基金、港股、美股、理财、法律诉讼、组合模拟等）尚未在当前系统中使用，可根据需求逐步接入。
