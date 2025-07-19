# 汇通财经黄金资讯爬虫

## 项目简介

本项目是一个专门用于抓取汇通财经网站黄金资讯的爬虫工具。能够自动获取最新的黄金相关新闻数据，包括标题、链接、发布时间、摘要等信息。

## 功能特点

- 🎯 **精准抓取**: 专门针对汇通财经黄金资讯页面优化
- 📊 **多格式输出**: 支持JSON和CSV两种数据格式
- 🔄 **智能重试**: 内置请求重试机制，提高抓取成功率
- 📝 **详细日志**: 完整的运行日志记录
- 🛡️ **反爬保护**: 模拟真实浏览器请求头，降低被封风险
- ⚡ **灵活配置**: 可选择是否获取新闻详情内容

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本使用

```python
from data_capture import GoldNewsCrawler

# 创建爬虫实例
crawler = GoldNewsCrawler()

# 运行爬虫（仅获取新闻列表）
crawler.run()
```

### 高级配置

```python
# 获取新闻详情（较慢但信息更完整）
crawler.run(
    get_details=True,    # 是否获取新闻详情
    max_details=10,      # 获取详情的新闻数量
    save_format='both'   # 保存格式: 'json', 'csv', 'both'
)
```

### 命令行运行

```bash
python data_capture.py
```

## 输出数据格式

### 新闻列表数据字段

- `title`: 新闻标题
- `url`: 新闻链接
- `time`: 发布时间
- `summary`: 新闻摘要
- `crawl_time`: 爬取时间

### 新闻详情数据字段（当get_details=True时）

- `content`: 新闻正文内容
- `publish_time`: 发布时间
- `author`: 作者信息
- `tags`: 标签信息

## 数据存储

爬取的数据会自动保存在 `gold_news_data` 目录下：

- JSON格式: `gold_news_YYYYMMDD_HHMMSS.json`
- CSV格式: `gold_news_YYYYMMDD_HHMMSS.csv`
- 日志文件: `gold_news_crawler.log`

## 配置说明

### 主要参数

- `get_details`: 是否获取新闻详情（默认False）
- `max_details`: 获取详情的新闻数量（默认5）
- `save_format`: 保存格式，可选 'json', 'csv', 'both'（默认'both'）

### 反爬策略

- 使用真实浏览器User-Agent
- 请求间隔控制
- 指数退避重试机制
- Session保持连接

## 注意事项

1. **合规使用**: 请遵守网站的robots.txt协议和使用条款
2. **频率控制**: 避免过于频繁的请求，建议设置适当的延时
3. **数据用途**: 仅用于学习和研究目的，不得用于商业用途
4. **网络环境**: 确保网络连接稳定，某些地区可能需要代理

## 故障排除

### 常见问题

1. **网络连接失败**
   - 检查网络连接
   - 尝试使用代理
   - 检查防火墙设置

2. **数据获取为空**
   - 检查目标网站是否可访问
   - 网站结构可能发生变化，需要更新解析逻辑

3. **编码问题**
   - 确保Python环境支持UTF-8编码
   - 检查系统区域设置

### 日志查看

运行日志保存在 `gold_news_crawler.log` 文件中，可以查看详细的运行信息和错误提示。

## 技术架构

- **HTTP客户端**: requests
- **HTML解析**: BeautifulSoup4
- **数据格式**: JSON, CSV
- **日志系统**: Python logging
- **编码处理**: UTF-8

## 更新日志

### v1.0.0
- 初始版本发布
- 支持黄金新闻列表抓取
- 支持新闻详情获取
- 多格式数据输出
- 完整的日志系统

## 许可证

本项目仅供学习和研究使用。使用时请遵守相关法律法规和网站使用条款。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交Issue
- 发送邮件

---

**免责声明**: 本工具仅用于技术学习和研究目的，使用者需自行承担使用风险，并遵守相关法律法规。