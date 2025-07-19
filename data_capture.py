#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汇通财经黄金资讯爬虫
目标网站：https://gold.fx678.com/news/goldnews.html
功能：抓取黄金相关新闻数据
"""

import requests
import json
import time
import csv
from datetime import datetime
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gold_news_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GoldNewsCrawler:
    """汇通财经黄金资讯爬虫类"""
    
    def __init__(self):
        """初始化爬虫"""
        self.base_url = "https://gold.fx678.com"
        self.news_url = "https://gold.fx678.com/goldNews/hj?p=1"
        self.session = requests.Session()
        
        # 设置请求头，模拟浏览器访问
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(self.headers)
        
        # 创建数据存储目录
        self.data_dir = "gold_news_data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def get_page_content(self, url, max_retries=3):
        """获取页面内容"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                response.encoding = 'utf-8'
                return response.text
            except requests.RequestException as e:
                logger.warning(f"第{attempt + 1}次请求失败: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    logger.error(f"获取页面内容失败: {url}")
                    return None
    
    def parse_news_list(self, html_content):
        """解析新闻列表"""
        soup = BeautifulSoup(html_content, 'lxml')
        news_items = []
        
        # 查找所有包含新闻链接的元素
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href')
            title = link.get_text(strip=True)
            
            # 过滤有效的新闻链接
            if (href and title and ('/content/' in href or 'gold.fx678.com/content/' in href)):
                
                # 构建完整URL
                full_url = urljoin(self.base_url, href)
                
                # 查找时间信息
                time_info = self.extract_time_info(link)
                
                news_item = {
                    'title': title,
                    'url': full_url,
                    'time': time_info,
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 避免重复
                if not any(item['url'] == full_url for item in news_items):
                    news_items.append(news_item)
        
        return news_items
    
    def extract_time_info(self, link_element):
        """提取时间信息"""
        # 查找父级元素中的时间信息
        parent = link_element.parent
        for _ in range(3):  # 向上查找3级父元素
            if parent:
                time_elements = parent.find_all(['span', 'div', 'time'], 
                                               class_=re.compile(r'time|date', re.I))
                for time_elem in time_elements:
                    time_text = time_elem.get_text(strip=True)
                    if time_text and re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}', time_text):
                        return time_text
                parent = parent.parent
            else:
                break
        
        # 从URL中提取时间信息
        url = link_element.get('href', '')
        time_match = re.search(r'(\d{8})', url)
        if time_match:
            date_str = time_match.group(1)
            try:
                formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                return formatted_date
            except:
                pass
        
        return ''
    

    
    def get_news_detail(self, news_url):
        """获取新闻详情"""
        html_content = self.get_page_content(news_url)
        if not html_content:
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 提取新闻详情
        detail = {
            'url': news_url,
            'title': '',
            'content': '',
            'publish_time': '',
            'author': '',
            'tags': []
        }
        
        # 提取标题 - 针对汇通网的特定选择器
        title_selectors = [
            ['h1', 'h2'],
            ['.title', '.headline', '.news-title'],
            ['[class*="title"]', '[class*="headline"]']
        ]
        
        for selectors in title_selectors:
            if isinstance(selectors[0], str) and selectors[0].startswith(('.', '[')):
                title_elem = soup.select_one(','.join(selectors))
            else:
                title_elem = soup.find(selectors, class_=re.compile(r'title|headline', re.I))
                if not title_elem:
                    title_elem = soup.find(selectors)
            
            if title_elem:
                title = title_elem.get_text(strip=True)
                # 移除网站名称后缀
                title = re.sub(r'-[^-]*汇通网.*$', '', title)
                title = re.sub(r'-[^-]*黄金.*$', '', title)
                detail['title'] = title
                break
        
        # 提取正文内容 - 针对汇通网的特定选择器
        content_selectors = [
            '.nyl_main',  # 汇通网新闻主要内容区域
            '.content, .article-content, .news-content, .text-content',
            '[class*="content"], [class*="article"], [class*="text"]',
            'article, .article, #article',
            '.main-content, .post-content, .entry-content'
        ]
        
        content_text = ''
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # 移除不需要的元素
                for unwanted in content_elem(["script", "style", "nav", "header", "footer", 
                                             ".ad", ".advertisement", ".related", ".share", 
                                             ".comment", ".sidebar", ".social"]):
                    unwanted.decompose()
                
                # 移除包含特定关键词的元素
                for elem in content_elem.find_all(class_=re.compile(r'ad|advertisement|share|related|comment', re.I)):
                    elem.decompose()
                
                content_text = content_elem.get_text(strip=True)
                # 清理内容
                content_text = re.sub(r'\s+', ' ', content_text)
                content_text = re.sub(r'[\r\n]+', '\n', content_text)
                
                # 过滤太短或包含广告关键词的内容
                if len(content_text) > 200 and not any(keyword in content_text.lower() for keyword in ['广告', 'ad', '推广', '点击查看']):
                    break
                content_text = ''
        
        # 如果没有找到合适的内容容器，尝试提取所有段落
        if not content_text or len(content_text) < 200:
            paragraphs = soup.find_all('p')
            content_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 20 and not re.search(r'版权|转载|来源|责任编辑|免责声明', text):
                    content_parts.append(text)
            content_text = '\n\n'.join(content_parts)
        
        detail['content'] = content_text
        
        # 提取发布时间 - 针对汇通网的选择器
        time_selectors = [
            '.nyl_article',  # 汇通网文章信息区域
            '[class*="time"], [class*="date"], [class*="publish"]',
            'time, .time, .date, .publish-time, .post-time',
            '[id*="time"], [id*="date"]'
        ]
        
        for selector in time_selectors:
            time_elem = soup.select_one(selector)
            if time_elem:
                time_text = time_elem.get_text(strip=True)
                # 提取时间信息
                time_match = re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', time_text)
                if time_match:
                    detail['publish_time'] = time_match.group()
                elif time_text and re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}', time_text):
                    detail['publish_time'] = time_text
                    break
        
        # 提取作者信息 - 针对汇通网的选择器
        author_selectors = [
            '.nyl_article',  # 汇通网文章信息区域
            '.author, .writer, .by-author',
            '[class*="author"], [class*="writer"]'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author_text = author_elem.get_text(strip=True)
                # 提取作者名称（通常在时间之前）
                author_match = re.search(r'^([^\d]+)', author_text)
                if author_match:
                    detail['author'] = author_match.group(1).strip()
                elif author_text and len(author_text) < 50:
                    detail['author'] = author_text
                    break
        
        return detail
    
    def save_to_json(self, data, filename=None):
        """保存数据到JSON文件"""
        if filename is None:
            filename = f"gold_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已保存到: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存JSON文件失败: {e}")
            return None
    
    def save_to_csv(self, data, filename=None):
        """保存数据到CSV文件"""
        if not data:
            return None
        
        if filename is None:
            filename = f"gold_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            logger.info(f"数据已保存到: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存CSV文件失败: {e}")
            return None
    
    def crawl_news_list(self):
        """爬取新闻列表"""
        logger.info("开始爬取黄金新闻列表...")
        
        html_content = self.get_page_content(self.news_url)
        if not html_content:
            logger.error("无法获取新闻列表页面")
            return []
        
        news_items = self.parse_news_list(html_content)
        logger.info(f"成功获取 {len(news_items)} 条新闻")
        
        return news_items
    
    def get_next_page_url(self, current_url, page_num):
        """构建下一页的URL"""
        # 汇通网的翻页URL模式：https://gold.fx678.com/goldNews/hj?p=页数
        if 'goldNews/hj' in current_url:
            # 第一页: https://gold.fx678.com/goldNews/hj?p=1
            # 第二页: https://gold.fx678.com/goldNews/hj?p=2
            base_url = "https://gold.fx678.com/goldNews/hj"
            return f"{base_url}?p={page_num}"
        return None
    
    def crawl_multiple_pages(self, target_count=500):
        """爬取多页新闻直到达到目标数量"""
        all_news = []
        page_num = 1
        
        logger.info(f"开始爬取多页新闻，目标收集 {target_count} 条新闻...")
        
        while len(all_news) < target_count:
            logger.info(f"正在爬取第 {page_num} 页...")
            
            # 构建当前页面URL
            current_url = self.get_next_page_url(self.news_url, page_num)
            if not current_url:
                logger.warning(f"无法构建第 {page_num} 页的URL")
                break
            
            # 获取当前页面内容
            html_content = self.get_page_content(current_url)
            if not html_content:
                logger.warning(f"无法获取第 {page_num} 页内容")
                break
            
            # 解析当前页面的新闻列表
            page_news = self.parse_news_list(html_content)
            if not page_news:
                logger.warning(f"第 {page_num} 页没有找到新闻")
                break
            
            # 过滤重复新闻
            new_items = []
            for news in page_news:
                if not any(existing['url'] == news['url'] for existing in all_news):
                    new_items.append(news)
            
            all_news.extend(new_items)
            logger.info(f"第 {page_num} 页获取到 {len(new_items)} 条新闻，累计 {len(all_news)} 条")
            
            page_num += 1
            
            # 添加延时，避免请求过于频繁
            time.sleep(2)
        
        # 如果超过目标数量，截取到目标数量
        if len(all_news) > target_count:
            all_news = all_news[:target_count]
        
        logger.info(f"多页爬取完成，共获取 {len(all_news)} 条新闻")
        return all_news
    
    def crawl_with_details(self, max_details=5, target_count=50):
        """爬取新闻列表并获取详情"""
        # 先爬取足够数量的新闻列表
        if target_count > 11:  # 如果目标数量大于单页数量，使用多页爬取
            news_list = self.crawl_multiple_pages(target_count)
        else:
            news_list = self.crawl_news_list()
        
        if not news_list:
            return []
        
        # 获取指定数量新闻的详情
        detailed_news = []
        detail_count = min(max_details, len(news_list))
        
        for i, news in enumerate(news_list[:detail_count]):
            logger.info(f"正在获取第 {i+1} 条新闻详情: {news['title'][:50]}...")
            
            detail = self.get_news_detail(news['url'])
            if detail:
                # 保留原始标题，只更新详情内容
                original_title = news['title']
                news.update(detail)
                # 如果详情页标题为空或者是通用标题，保留原始标题
                if not detail.get('title') or detail.get('title') in ['黄金频道', '汇通财经', '']:
                    news['title'] = original_title
                detailed_news.append(news)
            else:
                # 即使没有获取到详情，也保留基本信息
                news['content'] = ''
                news['publish_time'] = ''
                news['author'] = ''
                news['tags'] = []
                detailed_news.append(news)
            
            # 添加延时，避免请求过于频繁
            time.sleep(1)
        
        # 添加剩余的新闻（不获取详情）
        for news in news_list[detail_count:]:
            news['content'] = ''
            news['publish_time'] = ''
            news['author'] = ''
            news['tags'] = []
            detailed_news.append(news)
        
        return detailed_news
    
    def run(self, get_details=False, max_details=5, target_count=500, save_format='both'):
        """运行爬虫"""
        try:
            logger.info("=" * 50)
            logger.info("汇通财经黄金资讯爬虫启动")
            logger.info("=" * 50)
            
            if get_details:
                data = self.crawl_with_details(max_details, target_count)
            else:
                if target_count > 11:  # 如果目标数量大于单页数量，使用多页爬取
                    data = self.crawl_multiple_pages(target_count)
                else:
                    data = self.crawl_news_list()
            
            if not data:
                logger.warning("未获取到任何数据")
                return
            
            # 保存数据
            if save_format in ['json', 'both']:
                self.save_to_json(data)
            
            if save_format in ['csv', 'both']:
                self.save_to_csv(data)
            
            # 打印部分结果
            logger.info("\n" + "=" * 30 + " 爬取结果预览 " + "=" * 30)
            for i, item in enumerate(data[:3]):
                logger.info(f"\n第 {i+1} 条新闻:")
                logger.info(f"标题: {item['title']}")
                logger.info(f"链接: {item['url']}")
                logger.info(f"时间: {item.get('time', '未知')}")
            
            logger.info(f"\n总共获取 {len(data)} 条新闻数据")
            logger.info("爬虫运行完成！")
            
        except Exception as e:
            logger.error(f"爬虫运行出错: {e}")
            raise

def main():
    """主函数"""
    crawler = GoldNewsCrawler()
    
    # 运行爬虫
    # get_details=True: 获取新闻详情（较慢但信息完整）
    # get_details=False: 只获取新闻列表（较快）
    # max_details: 获取详情的新闻数量
    # target_count: 目标收集的新闻总数
    # save_format: 保存格式 ('json', 'csv', 'both')
    
    crawler.run(
        get_details=True,   # 启用内容抓取
        max_details=500,     # 获取前100条新闻的详细内容
        target_count=500,    # 目标收集100条新闻
        save_format='both'
    )

if __name__ == "__main__":
    main()