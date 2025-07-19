# 黄金投资智能分析系统

## 项目简介

本项目是一个基于AI的黄金投资分析系统，集成了新闻爬虫、情感分析、实时金价获取、数据可视化和智能投资建议等功能。通过分析黄金相关新闻的情感倾向，结合实时金价数据，为投资者提供专业的市场分析和投资建议。

## 核心功能

- 🎯 **新闻爬虫**: 自动抓取汇通财经等网站的黄金资讯
- 🧠 **AI情感分析**: 基于大模型的新闻情感分析和市场情绪评估
- 💰 **实时金价**: 多源金价数据获取和价格趋势分析
- 📊 **数据可视化**: 丰富的交互式图表和数据展示
- 🎯 **投资建议**: 基于情感分析的智能投资建议引擎
- 🌐 **Web界面**: 基于Streamlit的现代化Web应用界面

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 环境配置

1. 创建并配置环境变量文件 `.env`：
```bash
API_SECRET_KEY=your_api_key_here
BASE_URL=https://api.zhizengzeng.com/v1/
MODEL_NAME=hunyuan-lite
```

2. 安装依赖包：
```bash
pip install -r requirements.txt
```

### 启动Web应用

```bash
streamlit run streamlit_app.py
```

### 模块化使用

#### 新闻爬虫
```python
from data_capture import GoldNewsCrawler

crawler = GoldNewsCrawler()
crawler.run(get_details=True, max_details=10)
```

#### 情感分析
```python
from sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer()
result = analyzer.analyze_single_news(title, content)
```

#### 实时金价
```python
from gold_price_fetcher import GoldPriceFetcher

fetcher = GoldPriceFetcher()
price = fetcher.get_current_gold_price()
```

## 系统架构

### 技术栈

- **后端框架**: Python 3.8+
- **Web框架**: Streamlit
- **AI模型**: 混元-lite (通过OpenAI API)
- **数据处理**: pandas, numpy
- **可视化**: plotly, matplotlib, wordcloud
- **HTTP客户端**: requests
- **HTML解析**: BeautifulSoup4

### 模块结构

```
investment_app/
├── streamlit_app.py         # Web应用主界面
├── sentiment_analyzer.py    # 情感分析模块
├── data_visualizer.py       # 数据可视化模块
├── investment_advisor.py    # 投资建议引擎
├── gold_price_fetcher.py    # 金价获取模块
├── data_capture.py          # 新闻爬虫模块
├── api.py                   # AI API调用接口
├── config.py               # 配置管理
├── utils.py                # 工具函数
├── requirements.txt        # 依赖包列表
└── .env                    # 环境变量配置
```

## 数据格式

### 情感分析结果

```json
{
  "sentiment": "positive/negative/neutral",
  "score": 0.75,
  "confidence": 0.85,
  "keywords": ["黄金", "上涨", "利好"],
  "reasoning": "分析理由"
}
```

### 金价数据

```json
{
  "price_usd": 2050.30,
  "price_cny": 14762.16,
  "change_24h": 15.20,
  "change_percent_24h": 0.75,
  "source": "数据源",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 功能特性

### 🧠 AI情感分析
- 基于大模型的专业金融新闻情感分析
- 支持情感极性识别（积极/消极/中性）
- 提供情感强度评分（-1到1）
- 智能关键词提取和分析理由生成
- 置信度评估和缓存机制

### 📊 数据可视化
- 情感分布饼图
- 情感时间线散点图
- 新闻数量统计
- 置信度分布分析
- 情感热力图
- 关键词云图

### 💰 实时金价
- 多源金价数据获取
- 24小时价格变化追踪
- 美元/人民币双币种显示
- 价格趋势分析

### 🎯 智能投资建议
- 基于情感分析的投资建议
- 市场情绪指标计算
- 风险评估和预警
- 多维度分析报告

## 配置说明

### 环境变量配置

在 `.env` 文件中配置以下参数：

```bash
# AI API配置
API_SECRET_KEY=your_openai_api_key
BASE_URL=https://api.zhizengzeng.com/v1/
MODEL_NAME=hunyuan-lite

# 应用配置
APP_TITLE=黄金投资情感分析系统
CACHE_EXPIRE_DAYS=7
MAX_NEWS_DISPLAY=20
```

### 主要参数

- `API_SECRET_KEY`: AI模型API密钥
- `BASE_URL`: API服务地址
- `MODEL_NAME`: 使用的AI模型名称
- `CACHE_EXPIRE_DAYS`: 缓存过期天数
- `MAX_NEWS_DISPLAY`: 最大显示新闻数量

## 使用指南

### Web界面功能

1. **📊 数据概览**
   - 查看最新的情感分析结果
   - 核心指标展示（总数、平均分值、置信度）
   - 市场情绪总体评估

2. **📈 可视化分析**
   - 情感分布饼图：查看积极/消极/中性新闻比例
   - 情感时间线：观察情感变化趋势
   - 关键词云图：识别热点话题

3. **💰 实时金价**
   - 当前金价显示（美元/人民币）
   - 24小时涨跌幅
   - 价格变化趋势

4. **🎯 投资建议**
   - 基于情感分析的投资建议
   - 风险评估和市场预警
   - 详细分析报告

## 故障排除

### 常见问题

1. **API调用失败**
   - 检查 `.env` 文件中的API密钥配置
   - 确认API服务地址可访问
   - 查看 `app.log` 日志文件

2. **数据加载失败**
   - 确保 `gold_news_data` 目录存在
   - 检查数据文件格式是否正确
   - 运行新闻爬虫获取最新数据

3. **可视化显示异常**
   - 检查数据格式是否符合要求
   - 确认所需的Python包已安装
   - 清除浏览器缓存重新加载

4. **金价获取失败**
   - 检查网络连接
   - 确认金价API服务可用
   - 查看错误日志信息

### 日志文件

- `app.log`: 应用运行日志
- `gold_news_crawler.log`: 新闻爬虫日志
- Streamlit控制台输出: Web应用运行状态

## 更新日志

### v2.0.0 (当前版本)
- ✅ 完整的AI情感分析系统
- ✅ 实时金价获取功能
- ✅ 丰富的数据可视化组件
- ✅ 智能投资建议引擎
- ✅ 现代化Web界面
- ✅ 模块化架构设计
- ✅ 完善的错误处理和日志系统

### v1.0.0
- 基础新闻爬虫功能
- 新闻数据抓取和存储
- 多格式数据输出

## 性能指标

- **响应时间**: 单条新闻分析 < 3秒
- **准确率**: 情感分析准确率 > 80%
- **并发处理**: 支持批量新闻分析
- **缓存效率**: 避免重复分析，提升性能

## 注意事项

1. **API使用**: 需要有效的AI模型API密钥
2. **数据合规**: 遵守新闻网站的使用条款
3. **投资风险**: 分析结果仅供参考，投资需谨慎
4. **网络依赖**: 需要稳定的网络连接

## 许可证

本项目采用 MIT 许可证。仅供学习和研究使用，不得用于商业目的。

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进项目：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

**免责声明**: 本系统提供的分析结果和投资建议仅供参考，不构成投资建议。投资有风险，决策需谨慎。使用者需自行承担使用风险，并遵守相关法律法规。