
- [0.0 inbox](#00-inbox)
  - [目标](#目标)
- [wiki](#wiki)
- [Economy](#economy)
- [1.0 编程基础](#10-编程基础)
- [2.0 数据股票数据](#20-数据股票数据)
- [3.0 交易](#30-交易)
- [因子库](#因子库)
  - [因子机器学习](#因子机器学习)
    - [人工智能与量化交易](#人工智能与量化交易)
    - [nlp分析财报](#nlp分析财报)
- [投机](#投机)
  - [估值赛道选择](#估值赛道选择)
  - [Bank rate](#bank-rate)
  - [\[\[Weight\]\]](#weight)
  - [\[\[entropy\]\]](#entropy)
  - [\[\[Signal\_Noise\]\]](#signal_noise)
  - [交易类型](#交易类型)
- [构建数据库](#构建数据库)
  - [每日更新股票数据](#每日更新股票数据)
- [择时策略(Timing strategy)](#择时策略timing-strategy)
- [选股策略框架](#选股策略框架)
- [实盘交易](#实盘交易)
- [阿尔法模型](#阿尔法模型)
- [多因子](#多因子)
- [交易成本模型](#交易成本模型)
- [投资组合构建模型](#投资组合构建模型)
- [风险控制 risk](#风险控制-risk)
- [名人 people list](#名人-people-list)
- [论文/期刊](#论文期刊)
- [历史](#历史)
  - [问了1000人：什么是量化投资最重要的事？](#问了1000人什么是量化投资最重要的事)
  - [增值税(value added tax)](#增值税value-added-tax)
  - [量化扫盲 ：什么是过度拟合？](#量化扫盲-什么是过度拟合)
  - [最大回撤 Maximum Drawdown](#最大回撤-maximum-drawdown)
  - [什么是回溯测试？](#什么是回溯测试)
- [how to find trading strategies](#how-to-find-trading-strategies)
  - [找信号定策略，什么是信号？](#找信号定策略什么是信号)
  - [启发](#启发)
    - [增强信号的方法](#增强信号的方法)
- [Quantitative investment 量化投资](#quantitative-investment-量化投资)
  - [quant roadmap](#quant-roadmap)
  - [quantitative vs tradition](#quantitative-vs-tradition)
- [timeline](#timeline)
- [因子](#因子)
- [people](#people)
- [books](#books)
- [bussion](#bussion)
- [keyworld](#keyworld)
  - [keywords](#keywords)
  - [quants lib](#quants-lib)
  - [books](#books-1)
    - [看论文有没有？](#看论文有没有)
    - [参考](#参考)

# 0.0 inbox

* akshare
* 国内quant数据下载: www.tushare.pro

#flashcards/Economy
经济实现财富增长或进行投资操作的三种不同路径或核心策略
?
• 积累 (Accumulation): 在经济中，指通过持续储蓄、投资或再投资，逐步增加财富、资本或资产的过程。
• 杠杆 (Leverage): 在经济（尤其金融）中，指利用借入的资金或固定成本来放大投资回报（同时也放大风险）的策略。
• 证券 (Securities): 在经济中，指代表某种所有权（如股票）或债权（如债券）的、可以在市场上交易的金融工具或凭证。
<!--SR:!2025-10-22,22,150-->


我推荐书籍、论文、研报和量化网站这4个渠道，这些都极其适合作为量化萌新的因子库来源，关键大部分还都是免费的~就连量化大神们最开始的时候，除了骨骼清奇、天赋异禀的之外，也没有谁一上来就开挂的，初期也是得乖乖学习，关键这个时候不是先追求数量，而是先追求质量，建立正确的因子认知非常重要。这个时候最好不要“东一榔头，西一棒槌”的碎片化学习，要成体系化学习，那最体系的莫过于书籍了，这里推荐两本经典书籍

* 《量化投资策略：如何实现超额收益Alpha》
* 《投资策略实战分析：华尔街股市经典策略20年推演》
* 《101 Formulaic Alphas》
* 《151 Trading Strategies》


* 多因子投资
  * [Pool Factor](https://www.investopedia.com/terms/p/poolfactor.asp)
  * [factor_values](https://www.joinquant.com/help/api/help#factor_values)
  * [因子数据库](https://qsdoc.readthedocs.io/zh_CN/latest/因子数据库.html)
    * [Quant工具箱](https://www.zhihu.com/column/c_1108780156726054912)
    * [聚宽单因子分析工具](https://github.com/JoinQuant/jqfactor_analyzer)
    * [github 因子](https://github.com/search?q=因子)
    * https://bigquant.com
    * Deep Learning for Financial Applications : A Survey

* 专家在哪？如何吃掉专家的资金？   --- caoz
  * 哪些人权重高？ 银行家
  * 币圈交易所的人自己下场做，知道每个人的挂单数据，怎么可能不赚钱？
  * 银行家，资金操盘手怎么想的？
  * 斯坦福的人 很多都在做搬运的钱。数学高手都在做。全在新加坡
  * 你要想明白钱在哪里？如何抢

[[Economies_of_scale]]

## 目标

* 因子库
* 因子开发理论
* [用机器学习](#因子机器学习)
* 风险控制
* 资金池
* 动手写交易系统

# wiki
* [Category:Applied_mathematics](https://en.wikipedia.org/wiki/Category:Applied_mathematics)
  * [Category:Mathematical_finance](https://en.wikipedia.org/wiki/Category:Mathematical_finance)
    * [Category:Algorithmic_trading](https://en.wikipedia.org/wiki/Category:Algorithmic_trading)

* [Category:Algorithms](https://en.wikipedia.org/wiki/Category:Algorithms)
  * [Category:Machine_learning](https://en.wikipedia.org/wiki/Category:Machine_learning)
    * [Category:Cluster_analysis](https://en.wikipedia.org/wiki/Category:Cluster_analysis)
    * [Lasso_(statistics)](https://en.wikipedia.org/wiki/Lasso_(statistics))
    * [Elastic_net_regularization](https://en.wikipedia.org/wiki/Elastic_net_regularization)
    * [Random_forest](https://en.wikipedia.org/wiki/Random_forest)
    * [Dimensionality_reduction](https://en.wikipedia.org/wiki/Dimensionality_reduction)
# Economy
* [Category:Economy](https://en.wikipedia.org/wiki/Category:Economy)
  * [Category:Behavioral_finance](https://en.wikipedia.org/wiki/Category:Behavioral_finance)
  * [Category:Investment](https://en.wikipedia.org/wiki/Category:Investment)
    * [Factor_investing](https://en.wikipedia.org/wiki/Factor_investing)
    * [Category:Financial_markets](https://en.wikipedia.org/wiki/Category:Financial_markets)
      * [Global_Industry_Classification_Standard](https://en.wikipedia.org/wiki/Global_Industry_Classification_Standard)

      * [Stock_split](https://en.wikipedia.org/wiki/Stock_split)
      * [[Ex-Right]]
      * [[adjust]]
      * 有时间自己整几千个因子跑个lasso筛选，都比石川啥的强
    


# 1.0 编程基础

* [python](https://www.tutorialspoint.com/python/index.htm) 
* [pandas](https://www.tutorialspoint.com/python_pandas/index.htm)

# 2.0 数据股票数据

* 美股数据
  * https://polygon.io/dashboard

* refence
  * https://zhuanlan.zhihu.com/p/219931158
  * https://www.zhihu.com/search?type=content&q=%E9%87%8F%E5%8C%96%20%E6%95%B0%E6%8D%AE


# 3.0 交易




# 因子库

![](https://mmbiz.qpic.cn/mmbiz_png/C0CfiaC7SNgCYRibcWqCrU814r5sZuW6UqVJPiaGgk2vmvcicl2Kxa52PkglZVhBcnDnhBJO8ibe9KpO6OVujQkm6hA/640?wxfrom=5&wx_lazy=1&wx_co=1)

## 因子机器学习


* 机器学习模型有LASSO，Elastic Net，Random Forest（随机森林），Neural Networks（神经网络）
    * LASSO和Elastic Net相对于脊回归来说，是改善多元线性回归模型的多重共线性，实现降维（Dimension Deduction）的进阶版。
    * Lasso全称是The Least Absolute Shrinkage and Selection Operator。LASSO  有时间自己整几千个因子跑个lasso筛选，都比石川啥的强  theory name:Regression Shrinkage and Selection via the Lasso


### 人工智能与量化交易

<Neural Network-based Automatic Factor Construction>这篇文章，核心是2点：

1、First, we pre-traina neural network with a technical indicator MA as prior knowledge. Thepre-training performance has been well illustrated in Tables 2 and 3, and wecan pre-train this factor with 93.92% accuracy.
用某个技术指标（或者技术因子）作为y，pre-train网络，目的是让网络接近这个技术因子.

2、Second, we trainthe neural network by maximizing IC defined in formula (14). During thebackpropagation, the neural network has been changed, and the output factorvalue changes also. This process has been shown in Figure 6. Because we use theIC to serve as an objective function and the mechanism of back-propagation isgradient descent, the newly constructed factors will have higher IC than theinitialized factor.
得到1的pre-train网络后，用横截面rank-IC作为y，再对网络进行训练，目的是打败原来的技术因子。

我的看法：
这篇文章用了预训练的思想，可能这种想法对于金融科班出身的朋友来说有点隔靴挠痒的味道，但是事实上预训练的方法在非常多的人工智能（原谅我用这个词）任务上大放异彩，所以我认为还是一个非常值得尝试的方向。

### nlp分析财报

# 投机

* 理性
* trend
* input output model
* people Emotion and think processing

<<股票大作手操盘术>> p 118

## 估值赛道选择

1.估值 valuation:market value  ->future value ->Consensus value
2.风险risk:公司是否倒闭 ,goods not sell
3.资产capital权重   weight sort =model 
    1. 线性回归linear regression (statistics)
    2.因子 factor weight
    3.反馈分析 feedback to analyze

2019-09-15

* 估值：手机多少钱
* 风险：手机是否好转手
* 资产权重：做对比：模型跑一遍，线性回归、反馈、因子

* 估值 产品 成本
* 风险 二手出货风险
* 分散

1. market value  ->future value ->Consensus value
2. 公司是否倒闭,goods not sell  
3. weight sort

refence: 《投资要义》


## Bank rate

贴现率(Bank rate)是指将未来支付改变为现值所使用的利率


## [[Weight]]

Don't not having weight find excuse
多元投资理论
选top25-35=普通人选择。
选top1=资本压在最有决策上。
符合数据模型
entropy 

排序组合权重没有做过所以

https://www.youtube.com/watch?v=WfejdXi0VqI

## [[entropy]]
## [[Signal_Noise]]

## 交易类型 
 

* 交易model

趋势交易 、对冲交易 、波段交易 、高频交易、日内交易、支撑位阻力位交易 、K线交易、放量交易、突破交易 、反向交易

* risk model

* model odel(grow model)


* 回测 ：多年经验的浓缩验证
* 出入场指标：通过行业历史数据获取最优平均出入场核心指标。
* nlp舆情：分析系统+财报分析
* 因子：递归原因






# 构建数据库



## 每日更新股票数据




# 择时策略(Timing strategy)

# 选股策略框架

# 实盘交易



# 阿尔法模型

# 多因子

# 交易成本模型

# 投资组合构建模型

# 风险控制 risk


# 名人 people list

# 论文/期刊

# 历史

以叙事的方式，时间、空间、变量

## 问了1000人：什么是量化投资最重要的事？



* 因子：指标 信号
* 速度
* 系统:构建自己的系统
* 风险
* 风险收益高性价比


## 增值税(value added tax)

由消费者承担的一种税收成本增值税( Value- added Tax):一种销售税,是消费者承担的税费,属累退税,是基于商品或服务的增值而征税的一种间接税,增值税征收通常包括生产、流通或消费过程中的各个环节,是基于增值额或价差为计税依据的中性税种。

又比如说,你在一家电子产品专营店里看中了一台价值1万元的电脑但是要把电脑拿走,你除了需要支付这1万元以外,还需要支付1700元的增值税。消费者为获得商品必须额外支付增值税,因此,

## 量化扫盲 ：什么是过度拟合？

创建模型后,跑出来的数据不在预测范围内.


简要说明：拟合是优化策略的重要方法，但是过度拟合会使策略在回溯测试阶段优异的表现无法在发布后的实盘阶段复现。

过度拟合是一个非常重要的概念，描述了策略的在未来不能延续其在回溯测试阶段的优良表现的风险。
这个概念比较专业，但是理解之后对挑选策略有很大的帮助，所以我们还是尝试用通俗的语言介绍一下。
先解释一下什么是“拟合”。
一个策略，确定了基本的投资框架和交易规则之后，还需要进行细调和优化，进一步提高收益并降低波动，这个细调优化的过程，就是“拟合”。


参数调优是拟合的主要方法之一，例如把“上穿20日均线买入”改成“上穿25日均线买入”，或是把“亏损15%止损”改成“亏损10%止损”，如果回溯测试中有更好的表现，则保留新的参数设置，否则恢复原来的参数。
所以，拟合是优化策略的一个重要手段。



那么什么是过度拟合？
顾名思义，过度拟合就是拟合得过分了，老祖宗说“过犹不及”，是很有智慧的。


过度拟合的后果，就是策略失去了通用性，虽然能在回溯时段拟合出非常漂亮的收益曲线，在其他时间段就不灵了。
为了帮助理解，我们做个类比……
追女生有很多技巧，比如常请女生吃饭，时不时送点小礼物等等。


但是，如果对着同一个女生进行“过度拟合”总结出来的泡妞技巧，换了别的女生很可能就没效果了。比如这个女生喜欢川菜和动漫周边，追别的女生你也请吃川菜，也送动漫周边，效果肯定大打折扣，这就是过度拟合。
然而，判断过度拟合是个大难题，全世界都没有好的办法。


为了帮助大家更理性的挑选策略，我们在这个方面进行了一些前沿的探索，基于人工智能深度学习，我们可以对策略进行过度拟合的风险判断。分成“低风险”、“较低风险”、“较高风险”、“高风险”四挡，风险越低越好。
如前所述，对策略过度拟合的风险评估目前属于前沿的探索，存在误判的可能。
▍使用技巧：策略发布后，是在现实环境中计算调仓的，不存在过度拟合的风险，所以发布后的收益更有说服力

今天先分享到这里，后续我还会分享，

## 最大回撤 Maximum Drawdown

最大回撤:可能发生的最大损失幅度


简要说明：最大回撤是衡量策略风险的重要指标，可理解为可能发生的最大亏损幅度，其值等于策略收益曲线上，高点到后期最低点的回撤幅度的最大值。

衡量一个策略风险控制能力，最大回撤是最常用的指标，描述了投资者可能面临的最大亏损。
最大回撤的数值越小越好，越大说明风险越大。

最大回撤如何计算呢？简单的说，就是从任一高点到其后续最低点的下跌幅度的最大值。说起来很拗口，举个例子就明白了。
下图是一个简化版的策略收益曲线图（纵轴是收益，横轴是时间），它的最大回撤是从C点到F点。后面有详细的解释……

1. 找到图中的局部高点：有A、C、E、G、I五个点；
2. 找到局部高点对应的后续最低点，分别是A→F、C→F、E→F、G→H、I→J。注意A对应的后续最低点是F，而不是B，因为F比B点更低。同样，C点的后续低点也是F，而不是D点，因为F比D点更低。
3. 找出局部高点到后续最低点的最大跌幅，比较之后，显然是C→F的跌幅是最大的，按照定义，最大回撤就是C到F的下跌幅度。
下图是公募一哥王亚伟执掌华夏大盘时的净值走势，可以看出，最大回撤是45%。

理论上，最大回撤可以理解为可能发生的最大亏损幅度，所以回撤幅度超出前期最大回撤时，很有可能策略已经失效了。
使用技巧：如果策略在存在过度拟合的情况，策略发布之后，回撤幅度会很快超过发布之前的最大回撤。


## 什么是回溯测试？

历史回溯测试，也称为“回溯测试”，是用来测试一个策略的盈利能力和风险属性的方法。其工作原理是，把某段时间的全市场历史行情数据喂给被测试策略，并让其在一个模拟交易环境中自动运行，最后根据策略的交易记录对策略进行评估。

历史回溯测试是量化投资的一大杀器，是用股票市场的历史行情数据对策略进行测试，也称为回溯测试。

回溯测试的核心原理，简单的说，就是用真实的历史行情数据，构造出一个模拟的交易环境（回溯环境），让策略在其中运行。策略像时空穿越一样，回到历史上的某个时间节点，重头开始运行一遍。

然后，根据策略输出的交易记录，评估策略的盈利能力、风险控制能力和其他相关指标。

为什么说回溯测试是量化投资的“大杀器”呢？

因为它使我们摆脱了时间的限制，快速评估策略，然后根据评估结果进一步优化策略的算法规则，再通过回溯测试评估优化后的策略，然后再优化……

这个过程可以持续地、高效地迭代下去。很难想象没有回溯测试，在实盘中完成这个迭代优化的过程需要多久的时间。

回溯测试大大提高了策略开发和优化的效率，但是随之也带来了两个问题。一个是未来函数，另一个是过度拟合，这两个问题都会导致策略在现实环境中不同程度的失效。

未来函数，就是在时空穿越的时候把后来发生的信息也一起带回去了。

这个问题在我们的计算平台上已经得到了彻底的解决，我们在回溯环境上构造了一个信息过滤网，滤除掉了所有来自未来的信息，从源头上保证了策略在回溯时不受任何未来信息的干扰。

过度拟合这个概念稍微复杂一些，我们在另一篇文章《什么是过度拟合》单独介绍，感兴趣的可到历史文章中翻阅。

今天先分享到这里，后续我还会分享，
扫盲贴 ：什么是白马策略？
扫盲贴 ：什么是量化投资？

扫盲贴：白马策略的受益是怎么计算的
扫盲贴 ：如何挑选策略？
感兴趣的同学请关注我吧


# [how to find trading strategies](https://www.youtube.com/watch?v=a1cW91n6fvw&t=105s)

## 找信号定策略，什么是信号？
* 市场太大，我们时间少，找niche

*  出现A，有多少概率出现B
*  反复出现，但不可能不经常
*  精准医疗（数据行业颗粒度做细）
*  市场有效性
  * 市场有效价格也变，股价是货币现象
  * 供需才是关键
    * 比特币涨是人想要比特币，而不是美金
    * 股票涨，人想要股价而不是美元
  * 需求不一定是理性的存在即合理。
    * 比如情绪、技术、机器、新闻对决策者的影响。 
* 信号本质上就是对供需关系在时间、空间上变化的预测

## 启发

* 新兴市场：虚拟货币
* 散户扎堆的市场：中小盘股、个股、虚拟货币


### 增强信号的方法

* 精准量化
* 信号组合
* 标的组合






# Quantitative investment 量化投资

* what Quantitative investment
* why
* how

## quant roadmap

![](http://xcy-1251434521.cos.ap-chengdu.myqcloud.com/picture/quant_lordmap.jpeg)

## quantitative vs tradition

- | quantitative | tradition
--|--|--
people | James Simons | Warren Buffett
analysis method | model | knowledge + wisdom
cycle | short | long
targets | many | few
Risk | Risk control system | wisdom




# timeline
 
* 20世纪 50-60年代：资本资产定阶模型（CAMP）
* 20世纪 70-80年代：齐全定价模型，套利定价理论（APT）
* 20世纪 80-90年代：VaR模型、行为金融学
* 20世纪 90年代-现代：非线性科学

# 因子

* 量化研报


# people

* 西蒙斯James Simons
* Peter Lynch
* ray dalio
* Warren Buffett
* Steve Cohen 
* George Soros

# books

* 《Statistical Arbitrage》 - 安德鲁·波尔（Andrew Pole）
* The Man Who Solved the Market 詹姆斯.西蒙斯
* $《期权、期货及其他衍生产品》
* $ 金融数学 金融工程引论
* 《波动率交易：期权量化交易员指南》
* 《波动率微笑：宽客大师教你建模》
* 《主动投资组合管理：创造高收益并控制风险的量化投资方法》
* 《定价未来：撼动华尔街的量化金融史》
* 《对冲之王：华尔街量化投资传奇》
* 《高频交易员》
* 《宽客人生》
* 《赌金者》
* 《大空头》
* 量化投资 策略与技术
* 《算法交易与套利交易》
* 《打开量化投资的黑箱》
* 《解读量化投资》
* 《量化投资策略 - 如何实现超额收益 Alpha》
* 《金融计量学 - 从出击到高级建模技术》


https://www.zhihu.com/question/54727745/answer/762919447
 

# bussion

* 西蒙斯 文艺复兴科技有限责任公司 Renaissance Technologies LLC


# keyworld

* K 线图 k-line diagram
* quant 宽客
* Quantitative investment 量化投资
	* 量化选股
	* 量化择时
	* 套利交易
	* 算法交易
	* 资产配置
	* 风险控制
	* 预测模型
* 算法交易 Algorithmic trading
* 高頻交易（英語：high-frequency trading，HFT） 
* Statistical Arbitrage 统计套利
* 统计套利策略中的概念
	* 时间序列分析（Time Series Analysis）
	* 自回归和协整分析（AutoRegression and Co-integration）
	* 波动率建模（Volatility modeling）
	* 主成分分析（Principal Components Analysis）
	* 模式发现技术（Pattern finding techniques）
	* 机器学习技术（Machine Learning techniques）
	* 有效边界分析（Efficient frontier analysis）
* 统计套利策略的类型
	* 市场中性套利（Market Neutral Arbitrage）
	* 跨资产类别套利（Cross Asset Arbitrage）
	* 跨市场套利（Cross Market Arbitrage）
	* ETF 套利（ETF Arbitrage）
* Effient-market hypothesis EMH 有效市场假说
* 深度学习估值算法
* 金融keyworld
	* 无风险资产 A(t)
	* 风险资产S(t)
	* 风险证券
	* 头寸
	* 多头
	* 空头
	* 资产组合V(t)
	* 收益率
	    * 简单收益率K(s,t)
		* 对数收益率k
		* 超额收益率 
	* 随机性
	* 价格的正性
	* 可分性、流动性
	* 卖空
	* 偿付能力
	* 离散单位价格
	* 无套利原则
* 股票与衍生品
	* 远期合约
		* 交割日 delivery date
		* 远期价格 forward price
		* 回报 payoff
		* 持有成本 carrying cost
	* 期权C(t)
		* 看涨期权 call option
		* 看跌期权 put option
		* 期权价格计算
		* 降低风险
	* 期货
		* 期货价格n T
		* 初始保证金
		* 期货合约与远期合约的区别
* 货币时间价值
	* 利息(interest):r
	* 本金：P
	* 单利(simpleinterest)
		* 总收益 V(t)=(1+tr)p
		* 收益率 k(s,t)
		* 现值 V(0)=V(t)(1+rt)	
	* 按期复合
    * 复利
* 货币市场
	* 货币市场 ---- 无风险资产
* 债券分类
	* 零息债券
	* 附息债券
* 货币市场账户

* 股票价格动态
	* 股票价格S(t)
	* 价格变动树		

* 二叉树模型
* 风险度量
* VaR: value at risk 风险假制度/在险价值 jp摩根提出
	* 历史模拟法
	* 协方差矩阵法
	* 模特卡罗模拟法



## keywords

Algorithm qunant

## quants lib

* [awesome-quants](https://github.com/wilsonfreitas/awesome-quant)
* [quants国内](https://github.com/thuquant/awesome-quant)
* [c++quantlib](https://github.com/lballabio/QuantLib)
* [30天掌握量化交易](https://github.com/Rockyzsu/stock)
* [Zipline,Pythonic Algorithmic Trading Library](https://github.com/quantopian/zipline)
* https://www.quantlib.org/
* https://github.com/microsoft/QuantumKatas
* https://github.com/QUANTAXIS/QUANTAXIS
* https://github.com/vnpy/vnpy

## books


* 人肉<技术<资本周转价值
* people list
    * 瑞达里奥
    * 查理芒格
    * 贝索斯

* factor
    * information entropy
    * source 溯源
    * hacker
    * hack people list
    * 回测
    * work memory 3-5 -> attention
    * people growth factor rate
    * Emotion
    * rate
    * classifcation
    * science rate
    * industry
    * data log
    * Emotion model
    * people knowledge model
    * crawler monitor model

* algorithm
    - 模糊数学
    - 拓扑数学
    - 常量数学→变量数学 必然数学→概率数学 清晰数学→模糊数学
    - 实分析：​Real Analysis -- by H. Royden and P. Fitzpatrick。
    - 高等概率论：华裔数学家钟开莱写的A Course in Probability Theory
    - 凸优化：​Convex optimization​ -- by S. Boyd and L. Vandenberghe，斯坦福大神Boyd的名作，目前应用最广泛的凸优化教材。经典度四颗半★★★★☆
    - 图论：Graph Theory with Applications -- by J. A. Bondy and U. S. R. Murty，图论神作。一本1976年出版的书，我在Abebooks淘了一本。这两位作者的续作GTM系列的Graph Theory个人不推荐，已经变成了一本厚厚的工具书。
    - 组合数学中的概率方法：Probabilistic Method -- by N. Alon and J. H. 
    - 信息论：​Elements of Information Theory -- by T. M. Cover and J. A. Thomas，
    - 数学分析：Understanding Analysis -- by Stephen Abbott，内容是单变量数学分析。读完感叹这位就是个写书的天才。当年曾经觉得这位出的每本书我都要买，但是过去这么久，他却依然只出过这一本书。墙裂推荐这本书作为数学分析的入门教材，墙裂不推荐用Baby Rudin做教材。
    - 随机分析：Stochastic Calculus for Finance II (Continuous-Time Models) -- by Steven Shreve，学习随机分析的不二选择。经典度五颗星★★★★★
    - 统计学习：千万不要选择Pattern Recognition and Machine Learning (PRML) 做为入门书，那是本劝退书。这本An Introduction to Statistical Learning: with Applications in R -- by Gareth James, Daniela Witten, Trevor Hastie, Robert Tibshirani经典中经典之作。从头一气读到尾，让你根本停不下来。作为第一本入门书，更是尤为重要。我目前还没发现第二本能达到这种效果的机器学习类书籍，即使是它们的加难版，由本书的第三、第四作者斯坦福两位大神写的Elements of Statistical Learning也是味同嚼蜡。经典度五颗星★★★★★
    - 流形上的微积分


* 《经济学原理》
* API：
    * buyer：input memory
* reference
    * 哈佛 小林
        *  https://www.youtube.com/watch?v=xnIYIpXKvNM
    - https://www.bilibili.com/video/BV1L4411F7cs?p=2
    - https://www.vnpy.com/
    - vn.py全实战进阶

### 看论文有没有？

有用的。论文太多，需要验证方法论

* quantpedia.com
>市场有价值的论文做回策 $500/month

* SSRN

金融数据、交易、论文

* Arxiv.org

金融数据、交易、论文



* 其他渠道
  * podcast
  * 视频youtube



劳务型收入和资产型收入
•劳务型收入：用时间和劳动量换钱
•资产型收入：靠配置资源挣



劳务型收入的局限
•上限很明显，没那么多高薪岗位
•无法积累
•无法传承
• 只有一个客


财富最大的作用
•独立性，不是更高的回报率和挥金如士的生活
• 只关注于你感兴趣的事情
•自由就是终极选择



你头脑中是否出现过以下破局之法？
•创业
•股票、比特币
•穿越回14年，买房
•突然继承了大笔的遗产
•中彩票
•婚姻改变命


资产型收入：并不完美的彼岸
•巨大的尾部风险
• 海量的沉默的失败者
•过程不连续，选择比努力更重要
• 试错的成



并不存在一劳永逸的财富自由
•自由从来不是免费的
•赚钱系统也需要维护
• 只有你能捍卫的东西才属于


跨与不跨，这是一个问题
•不甘心，躺不平
•进化的淘汰
•责任的驱动
•必过一关，人总要逐渐趋向于高





逐步积累的逻辑
•不对称机会，损失有限，收益无上限。
•多次尝试，彩票逻辑。
•慢且上限低



杠杆的逻辑

* 高资产
* 高负债
* 高现金流


证券化的逻辑
•未来现金流兑现到现在
• 上限高但成功率低
•大量的商业故事造成扭



分解步骤，练级打怪，拉平难度曲线
劳务型阶段：打工人小老板/个体户
资产型阶段：买房＞做交易创


进击的打工人- 成为超级个体
在公司做到中高层管理者之前，别以为自己怀才不遇。
成为有人愿意付费咨询的行业专家。
做好本职工作，积累经验和上下游资源。
个体户/小老板是打工人的终极形态。
小老板并不是资本家，赚的还是劳务型收入。


卖出一小步-不要肤浅的理解商业
看商业杂志学不会经营企业。
天才的路径很难复制。
顺序非常重要，不要做反了。
找到自己的能力点，我是谁，我有什么资源，我擅长什么，万丈高楼由此而起。




别冒进
每个阶段沉淀下来作为下一个阶段的台阶每把都 all in，死是必然的



初识资产-顺序一定不要搞错
不懂不碰，要经历过周期才有更深的理解资产配置是一个实践过程（绿色木材谬误）
避风港（保险+彩票）
拒绝的定



对和自己当年一样的人的建议
•选一个有上升期的公司。
•提升自己的知识体系。
•广结善缘，多学习新模式

投资, 最有价值的人、资源驱动，投资是睡后收入，抽象层级最大, 全球历史的人
为什么投资是最容易 最有效 最有规模的赚钱方式？
* 投资是最有价值的人、资源驱动，投资是睡后收入，抽象层级最大
* 因为1个人再牛逼都不可能比全球历史的人都强。


### 参考

* https://qlearn.apachecn.org/#/
* [炼数成金 - 量化投资](https://www.bilibili.com/video/BV1qx41137m6?p=5&spm_id_from=pageDriver)

