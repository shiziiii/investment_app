#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻情感分析模块（整合版）
功能：调用大模型API分析黄金新闻的情感倾向，包含演示和测试功能
"""

import json
import hashlib
import os
import time
import re
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from openai import OpenAI
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_SECRET_KEY = "sk-zk22fff00d0d5fe4cd7a64f0f5aaac6a014687a42c264dfb";
BASE_URL = "https://api.zhizengzeng.com/v1/"

# chat with other model
def chat_completions4(query):
    client = OpenAI(api_key=API_SECRET_KEY, base_url=BASE_URL)
    resp = client.chat.completions.create(
        model="hunyuan-lite",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": query}
        ]
    )
    return resp.choices[0].message.content

class SentimentAnalyzer:
    """新闻情感分析器"""
    
    def __init__(self, cache_dir: str = "cache", cache_days: int = 7):
        """
        初始化情感分析器
        
        Args:
            cache_dir: 缓存目录
            cache_days: 缓存有效天数
        """
        self.cache_dir = cache_dir
        self.cache_days = cache_days
        
        # 确保缓存目录存在
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
        # 情感分析提示词模板
        self.sentiment_prompt_template = """
你是一个专业的金融分析师，请分析以下黄金相关新闻的情感倾向。

新闻标题：{title}
新闻内容：{content}

请从以下维度进行分析：
1. 对黄金价格的影响倾向（正面/负面/中性）
2. 情感强度（-1到1的数值，-1表示最负面，1表示最正面，0表示中性）
3. 关键影响因素和关键词
4. 分析的置信度（0到1之间）
5. 简要分析理由

请严格按照以下JSON格式返回结果，不要包含任何其他文字：
{{
    "sentiment": "positive/negative/neutral",
    "score": 0.0,
    "confidence": 0.0,
    "keywords": ["关键词1", "关键词2"],
    "reasoning": "分析理由"
}}
"""
    
    def _get_cache_key(self, title: str, content: str) -> str:
        """生成缓存键"""
        text = f"{title}_{content}"
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"sentiment_{cache_key}.json")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """检查缓存是否有效"""
        if not os.path.exists(cache_path):
            return False
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        expire_time = datetime.now() - timedelta(days=self.cache_days)
        return file_time > expire_time
    
    def _load_from_cache(self, cache_path: str) -> Optional[Dict]:
        """从缓存加载结果"""
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")
            return None
    
    def _save_to_cache(self, cache_path: str, result: Dict) -> None:
        """保存结果到缓存"""
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
    
    def _parse_sentiment_response(self, response: str) -> Dict:
        """解析大模型返回的情感分析结果"""
        try:
            # 提取JSON
            if response.strip().startswith('{') and response.strip().endswith('}'):
                json_str = response.strip()
            else:
                json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_match = re.search(r'{.*}', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    else:
                        raise ValueError("无法找到有效的JSON格式")
            
            result = json.loads(json_str)
            
            # 验证和修正数据
            required_fields = ['sentiment', 'score', 'confidence', 'keywords', 'reasoning']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"缺少必要字段: {field}")
            
            result['score'] = max(-1.0, min(1.0, float(result['score'])))
            result['confidence'] = max(0.0, min(1.0, float(result['confidence'])))
            
            if not isinstance(result['keywords'], list):
                result['keywords'] = []
            
            sentiment = str(result['sentiment']).lower()
            if sentiment not in ['positive', 'negative', 'neutral']:
                sentiment = 'neutral'
            result['sentiment'] = sentiment
            
            return result
            
        except Exception as e:
            logger.error(f"解析响应失败: {e}")
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.1,
                'keywords': [],
                'reasoning': f'解析失败: {str(e)}'
            }
    
    def analyze_single_news(self, title: str, content: str, use_cache: bool = True) -> Dict:
        """分析单条新闻的情感"""
        title = title.strip() if title else ""
        content = content.strip() if content else ""
        
        if not title and not content:
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'keywords': [],
                'reasoning': '标题和内容都为空'
            }
        
        # 检查缓存
        cache_key = self._get_cache_key(title, content)
        cache_path = self._get_cache_path(cache_key)
        
        if use_cache and self._is_cache_valid(cache_path):
            cached_result = self._load_from_cache(cache_path)
            if cached_result:
                logger.info(f"使用缓存结果: {cache_key}")
                return cached_result
        
        # 调用API分析
        prompt = self.sentiment_prompt_template.format(
            title=title,
            content=content[:1000]
        )
        
        try:
            logger.info(f"开始分析新闻情感: {title[:50]}...")
            response = chat_completions4(prompt)
            
            if response is None:
                logger.error("API返回空响应")
                return {
                    'sentiment': 'neutral',
                    'score': 0.0,
                    'confidence': 0.0,
                    'keywords': [],
                    'reasoning': 'API返回空响应',
                    'analyzed_at': datetime.now().isoformat(),
                    'cache_key': cache_key
                }
            
            result = self._parse_sentiment_response(response)
            result['analyzed_at'] = datetime.now().isoformat()
            result['cache_key'] = cache_key
            
            if use_cache:
                self._save_to_cache(cache_path, result)
            
            logger.info(f"分析完成: {result['sentiment']} ({result['score']:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"分析新闻情感时发生错误: {e}")
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'keywords': [],
                'reasoning': f'分析失败: {str(e)}',
                'analyzed_at': datetime.now().isoformat(),
                'cache_key': cache_key
            }
    
    def analyze_batch_news(self, news_list: List[Dict], max_workers: int = 3) -> List[Dict]:
        """批量分析新闻情感"""
        results = []
        total = len(news_list)
        
        logger.info(f"开始批量分析 {total} 条新闻")
        
        for i, news in enumerate(news_list, 1):
            logger.info(f"处理进度: {i}/{total}")
            
            title = news.get('title', '')
            content = news.get('content', '')
            sentiment_result = self.analyze_single_news(title, content)
            
            result = news.copy()
            result['sentiment_analysis'] = sentiment_result
            results.append(result)
            
            if i < total:
                time.sleep(1)  # 避免API调用过于频繁
        
        logger.info(f"批量分析完成，共处理 {len(results)} 条新闻")
        return results
    
    def get_sentiment_summary(self, analyzed_news: List[Dict]) -> Dict:
        """获取情感分析汇总统计"""
        if not analyzed_news:
            return {
                'total_count': 0,
                'sentiment_distribution': {},
                'average_score': 0.0,
                'average_confidence': 0.0
            }
        
        sentiments = []
        scores = []
        confidences = []
        
        for news in analyzed_news:
            sentiment_data = news.get('sentiment_analysis', {})
            if sentiment_data:
                sentiments.append(sentiment_data.get('sentiment', 'neutral'))
                scores.append(sentiment_data.get('score', 0.0))
                confidences.append(sentiment_data.get('confidence', 0.0))
        
        sentiment_counts = {}
        for sentiment in sentiments:
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            'total_count': len(analyzed_news),
            'sentiment_distribution': sentiment_counts,
            'average_score': round(avg_score, 3),
            'average_confidence': round(avg_confidence, 3),
            'score_range': {
                'min': min(scores) if scores else 0.0,
                'max': max(scores) if scores else 0.0
            }
        }

# 演示和工具函数
def find_latest_news_file():
    """查找最新的新闻数据文件"""
    # 检查gold_news_data目录
    data_dir = os.path.join(os.getcwd(), 'gold_news_data')
    if os.path.exists(data_dir):
        news_files = [f for f in os.listdir(data_dir) if f.startswith('gold_news_') and f.endswith('.json')]
        if news_files:
            news_files.sort(reverse=True)
            return os.path.join(data_dir, news_files[0])
    
    # 检查当前目录
    current_dir = os.getcwd()
    news_files = [f for f in os.listdir(current_dir) if f.startswith('gold_news_') and f.endswith('.json')]
    
    if news_files:
        news_files.sort(reverse=True)
        return news_files[0]
    
    return None

def load_json_data(file_path):
    """加载JSON数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载数据失败: {e}")
        return None

def analyze_news_sample(file_path, sample_size=5):
    """分析新闻样本"""
    print(f"正在加载新闻数据: {file_path}")
    
    news_data = load_json_data(file_path)
    if not news_data:
        print("无法加载新闻数据")
        return None
    
    print(f"共找到 {len(news_data)} 条新闻，将分析前 {sample_size} 条")
    sample_data = news_data[:sample_size]
    analyzer = SentimentAnalyzer()
    
    print("\n开始情感分析...")
    print("=" * 80)
    
    results = []
    for i, news in enumerate(sample_data, 1):
        print(f"\n[{i}/{len(sample_data)}] 分析新闻:")
        print(f"标题: {news.get('title', 'N/A')[:100]}...")
        print(f"时间: {news.get('time', 'N/A')}")
        
        sentiment_result = analyzer.analyze_single_news(
            news.get('title', ''),
            news.get('content', '')
        )
        
        print(f"情感倾向: {sentiment_result['sentiment']}")
        print(f"情感分值: {sentiment_result['score']:.3f}")
        print(f"置信度: {sentiment_result['confidence']:.3f}")
        print(f"关键词: {', '.join(sentiment_result['keywords'])}")
        print(f"分析理由: {sentiment_result['reasoning'][:150]}...")
        
        result = news.copy()
        result['sentiment_analysis'] = sentiment_result
        results.append(result)
        
        print("-" * 80)
    
    return results

def generate_summary_report(results):
    """生成汇总报告"""
    if not results:
        return
    
    analyzer = SentimentAnalyzer()
    summary = analyzer.get_sentiment_summary(results)
    
    print("\n" + "=" * 80)
    print("情感分析汇总报告")
    print("=" * 80)
    
    print(f"分析总数: {summary['total_count']} 条新闻")
    print(f"平均情感分值: {summary['average_score']:.3f}")
    print(f"平均置信度: {summary['average_confidence']:.3f}")
    
    print("\n情感分布:")
    for sentiment, count in summary['sentiment_distribution'].items():
        percentage = (count / summary['total_count']) * 100
        print(f"  {sentiment}: {count} 条 ({percentage:.1f}%)")
    
    print(f"\n分值范围: {summary['score_range']['min']:.3f} ~ {summary['score_range']['max']:.3f}")
    
    # 投资建议
    avg_score = summary['average_score']
    if avg_score > 0.3:
        market_outlook = "积极"
        investment_advice = "市场情绪偏向乐观，可考虑适当增加黄金配置"
    elif avg_score < -0.3:
        market_outlook = "消极"
        investment_advice = "市场情绪偏向悲观，建议谨慎投资或减少黄金配置"
    else:
        market_outlook = "中性"
        investment_advice = "市场情绪相对中性，建议保持现有配置并观察后续发展"
    
    print(f"\n市场情绪: {market_outlook}")
    print(f"投资建议: {investment_advice}")

def save_analysis_results(results, output_file=None):
    """保存分析结果"""
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"sentiment_analysis_results_{timestamp}.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n分析结果已保存到: {output_file}")
        return True
    except Exception as e:
        print(f"\n保存结果时发生错误: {e}")
        return False

def demo_analysis(sample_size=5):
    """演示情感分析功能"""
    print("黄金新闻情感分析演示")
    print("=" * 80)
    
    try:
        # 查找最新的新闻文件
        news_file = find_latest_news_file()
        if not news_file:
            print("未找到新闻数据文件")
            print("请确保当前目录下有以 'gold_news_' 开头的 JSON 文件")
            return False
        
        # 分析新闻样本
        results = analyze_news_sample(news_file, sample_size=sample_size)
        if not results:
            return False
        
        # 生成汇总报告
        generate_summary_report(results)
        
        # 保存结果
        save_analysis_results(results)
        
        print("\n演示完成！")
        return True
        
    except Exception as e:
        print(f"\n演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """测试基本功能"""
    analyzer = SentimentAnalyzer()
    
    test_news = [
        {
            'title': '黄金价格大涨，投资者信心增强',
            'content': '受美联储降息预期影响，黄金价格今日大幅上涨，市场情绪乐观。'
        },
        {
            'title': '黄金市场面临下行压力',
            'content': '由于美元走强和通胀担忧，黄金价格可能面临进一步下跌风险。'
        },
        {
            'title': '黄金价格保持稳定',
            'content': '黄金价格在窄幅区间内震荡，市场等待更多经济数据。'
        }
    ]
    
    print("=== 基本功能测试 ===")
    
    for i, news in enumerate(test_news, 1):
        print(f"\n测试 {i}: {news['title']}")
        result = analyzer.analyze_single_news(news['title'], news['content'])
        print(f"情感: {result['sentiment']}")
        print(f"分值: {result['score']}")
        print(f"置信度: {result['confidence']}")
        print(f"关键词: {result['keywords']}")
        print(f"理由: {result['reasoning']}")
    
    # 批量分析测试
    print("\n=== 批量分析测试 ===")
    batch_results = analyzer.analyze_batch_news(test_news)
    summary = analyzer.get_sentiment_summary(batch_results)
    
    print(f"总数: {summary['total_count']}")
    print(f"情感分布: {summary['sentiment_distribution']}")
    print(f"平均分值: {summary['average_score']}")
    print(f"平均置信度: {summary['average_confidence']}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            sample_size = int(sys.argv[2]) if len(sys.argv) > 2 else 500
            demo_analysis(sample_size)
        elif sys.argv[1] == "test":
            test_basic_functionality()
        else:
            print("用法: python sentiment_analyzer.py [demo|test] [sample_size]")
    else:
        test_basic_functionality()