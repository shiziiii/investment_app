# -*- coding: utf-8 -*-
"""
黄金价格数据获取模块
支持实时金价和历史金价数据获取
"""

import requests
import json
import time
from datetime import datetime, timedelta
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import os
import re
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GoldPriceData:
    """金价数据结构"""
    timestamp: datetime
    price_usd: float  # 美元价格
    price_cny: float  # 人民币价格
    change_24h: float  # 24小时变化
    change_percent_24h: float  # 24小时变化百分比
    volume: Optional[float] = None  # 交易量
    market_cap: Optional[float] = None  # 市值
    source: str = "unknown"  # 数据源

class GoldPriceFetcher:
    """黄金价格数据获取器"""
    
    def __init__(self):
        """初始化价格获取器"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        # 缓存目录
        self.cache_dir = "cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_current_gold_price(self) -> Optional[GoldPriceData]:
        """获取当前实时金价"""
        try:
            # 尝试多个数据源
            price_data = self._fetch_from_huilvbiao() or self._fetch_from_metals_api() or self._fetch_from_backup_source()
            
            if price_data:
                # 缓存当前价格
                self._cache_current_price(price_data)
                return price_data
            else:
                # 如果所有API都失败，尝试从缓存读取
                return self._load_cached_price()
                
        except Exception as e:
            logger.error(f"获取实时金价失败: {e}")
            return self._load_cached_price()
    
    def _fetch_from_coinapi(self) -> Optional[GoldPriceData]:
        """从金投网爬取金价数据"""
        try:
            # 爬取金投网的黄金价格页面
            url = "https://quote.cngold.org/gjs/swhj_zghj.html"
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找价格表格
                price_table = soup.find('table', class_='quote_table')
                if not price_table:
                    price_table = soup.find('table', {'id': 'quote_table'})
                
                if price_table:
                    rows = price_table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 4 and '上海黄金' in cells[0].get_text():
                            # 提取价格信息
                            current_price = float(cells[1].get_text().strip())
                            change_text = cells[2].get_text().strip()
                            change_24h = float(change_text) if change_text and change_text != '--' else 0
                            
                            change_percent_text = cells[3].get_text().strip().replace('%', '')
                            change_percent = float(change_percent_text) if change_percent_text and change_percent_text != '--' else 0
                            
                            # 转换为美元价格 (假设当前价格是人民币/克)
                            price_usd = (current_price * 31.1035) / 7.2  # 克转盎司，人民币转美元
                            
                            return GoldPriceData(
                                timestamp=datetime.now(),
                                price_usd=price_usd,
                                price_cny=current_price * 31.1035,  # 转换为人民币/盎司
                                change_24h=change_24h,
                                change_percent_24h=change_percent,
                                source="金投网(cngold.org)"
                            )
        except Exception as e:
            logger.warning(f"从金投网获取数据失败: {e}")
            return None
    
    def _fetch_from_huilvbiao(self) -> Optional[GoldPriceData]:
        """从汇率表网站获取实时金价数据"""
        try:
            # 获取实时金价数据
            url = "https://www.huilvbiao.com/api/gold_indexApi"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            content = response.text
            
            # 优先解析hq_str_gds_AUTD变量（国内黄金价格，人民币/克）
            autd_match = re.search(r'hq_str_gds_AUTD="([^"]+)"', content)
            if autd_match:
                autd_data = autd_match.group(1).split(',')
                if len(autd_data) >= 4:
                    try:
                        current_price_cny_per_gram = float(autd_data[0])  # 当前价格（人民币/克）
                        prev_close_cny_per_gram = float(autd_data[2]) if autd_data[2] else current_price_cny_per_gram  # 昨收盘价
                        
                        # 计算变化量和变化百分比
                        change_24h_cny_per_gram = current_price_cny_per_gram - prev_close_cny_per_gram
                        change_percent = (change_24h_cny_per_gram / prev_close_cny_per_gram) * 100 if prev_close_cny_per_gram != 0 else 0
                        
                        # 转换为美元价格：人民币/克 -> 美元/盎司
                        price_usd = (current_price_cny_per_gram * 31.1035) / 7.2  # 克转盎司，人民币转美元
                        change_24h_usd = (change_24h_cny_per_gram * 31.1035) / 7.2  # 变化量也要转换
                        
                        return GoldPriceData(
                            timestamp=datetime.now(),
                            price_usd=round(price_usd, 2),
                            price_cny=round(current_price_cny_per_gram, 2),
                            change_24h=round(change_24h_usd, 2),
                            change_percent_24h=round(change_percent, 2),
                            source="汇率表-国内金价(huilvbiao.com)"
                        )
                    except (ValueError, IndexError) as e:
                        logger.warning(f"解析AUTD数据失败: {e}")
            
            # 备用：解析hq_str_hf_GC变量（纽约黄金期货，美元/盎司）
            gc_match = re.search(r'hq_str_hf_GC="([^"]+)"', content)
            if gc_match:
                gc_data = gc_match.group(1).split(',')
                if len(gc_data) >= 4:
                    try:
                        current_price_usd = float(gc_data[0])  # 当前价格（美元/盎司）
                        prev_close_usd = float(gc_data[2]) if gc_data[2] else current_price_usd  # 昨收盘价
                        
                        # 计算美元价格的变化
                        change_24h_usd = current_price_usd - prev_close_usd
                        change_percent_usd = (change_24h_usd / prev_close_usd) * 100 if prev_close_usd != 0 else 0
                        
                        # 转换为人民币价格（美元/盎司 -> 人民币/克）
                        price_cny = (current_price_usd * 7.2) / 31.1035  # 美元转人民币，盎司转克
                        
                        return GoldPriceData(
                            timestamp=datetime.now(),
                            price_usd=round(current_price_usd, 2),
                            price_cny=round(price_cny, 2),
                            change_24h=round(change_24h_usd, 2),
                            change_percent_24h=round(change_percent_usd, 2),
                            source="汇率表-纽约金价(huilvbiao.com)"
                        )
                    except (ValueError, IndexError) as e:
                        logger.warning(f"解析GC数据失败: {e}")
            
            logger.warning("未找到有效的金价数据")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取汇率表数据请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"获取汇率表数据时发生未知错误: {e}")
            return None
    
    def _fetch_from_metals_api(self) -> Optional[GoldPriceData]:
        """从汇率表网站爬取金价数据"""
        try:
            # 爬取汇率表网站的黄金价格
            url = "https://www.huilvbiao.com/gold/"
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找金价数据
                gold_price_div = soup.find('div', class_='gold-price')
                if not gold_price_div:
                    gold_price_div = soup.find('div', {'id': 'gold_price'})
                
                if gold_price_div:
                    # 提取价格信息
                    price_span = gold_price_div.find('span', class_='price')
                    if price_span:
                        price_text = price_span.get_text().strip()
                        # 使用正则表达式提取数字
                        price_match = re.search(r'([0-9]+\.?[0-9]*)', price_text)
                        if price_match:
                            current_price = float(price_match.group(1))
                            
                            # 查找变化信息
                            change_span = gold_price_div.find('span', class_='change')
                            change_24h = 0
                            change_percent = 0
                            
                            if change_span:
                                change_text = change_span.get_text().strip()
                                change_match = re.search(r'([+-]?[0-9]+\.?[0-9]*)', change_text)
                                if change_match:
                                    change_24h = float(change_match.group(1))
                                    change_percent = (change_24h / current_price) * 100 if current_price != 0 else 0
                            
                            return GoldPriceData(
                                timestamp=datetime.now(),
                                price_usd=current_price,
                                price_cny=current_price * 7.2,
                                change_24h=change_24h,
                                change_percent_24h=change_percent,
                                source="汇率表(huilvbiao.com)"
                            )
        except Exception as e:
            logger.warning(f"从汇率表网站获取数据失败: {e}")
            return None
    
    def _fetch_from_backup_source(self) -> Optional[GoldPriceData]:
        """备用数据源 - 模拟数据"""
        try:
            # 如果所有API都失败，返回模拟数据
            logger.info("使用模拟金价数据")
            
            # 基础价格 + 随机波动
            import random
            base_price = 2650.0  # 基础金价
            variation = random.uniform(-50, 50)  # 随机波动
            price_usd = base_price + variation
            
            change_24h = random.uniform(-30, 30)
            change_percent = (change_24h / price_usd) * 100
            
            return GoldPriceData(
                timestamp=datetime.now(),
                price_usd=price_usd,
                price_cny=price_usd * 7.2,
                change_24h=change_24h,
                change_percent_24h=change_percent,
                source="模拟数据"
            )
        except Exception as e:
            logger.error(f"生成模拟数据失败: {e}")
            return None
    
    def get_historical_prices(self, days: int = 30) -> List[GoldPriceData]:
        """获取历史金价数据"""
        try:
            # 尝试从缓存加载历史数据
            cached_data = self._load_cached_historical_data(days)
            if cached_data:
                return cached_data
            
            # 尝试从汇率表网站获取历史数据
            historical_data = self._fetch_historical_from_huilvbiao(days)
            
            if historical_data and len(historical_data) > 0:
                logger.info(f"从汇率表网站获取了{len(historical_data)}天的历史数据")
                # 缓存数据
                self._cache_historical_data(historical_data)
                return historical_data
            
            # 如果缓存没有，生成模拟历史数据
            return self._generate_mock_historical_data(days)
            
        except Exception as e:
            logger.error(f"获取历史金价失败: {e}")
            return self._generate_mock_historical_data(days)
    
    def _fetch_historical_from_huilvbiao(self, days: int = 30) -> List[GoldPriceData]:
        """
        从汇率表网站获取历史金价数据
        
        Args:
            days: 获取多少天的历史数据
            
        Returns:
            包含历史价格数据的列表
        """
        try:
            # 获取K线历史数据
            url = "https://www.huilvbiao.com/api/gold_autd_kline"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if not isinstance(data, list):
                logger.error("历史数据格式不正确")
                return []
            
            # 限制返回的数据量
            limited_data = data[:days] if len(data) > days else data
            
            historical_prices = []
            for item in limited_data:
                try:
                    # 解析每一条历史数据
                    # 数据格式: {"close": 775.2, "date_time": 1753027200000, "day": "2025/07/21", "high": 776.3, "low": 774.7, "open": 775.5, "price": 775.2, "volume": 1232, "change": 1.72, "amplitude": 1.5999756}
                    
                    timestamp_ms = item.get('date_time', 0)
                    if timestamp_ms:
                        # 转换时间戳（毫秒）为datetime
                        date = datetime.fromtimestamp(timestamp_ms / 1000)
                    else:
                        # 如果没有时间戳，尝试解析day字段
                        day_str = item.get('day', '')
                        if day_str:
                            date = datetime.strptime(day_str, '%Y/%m/%d')
                        else:
                            continue
                    
                    price = float(item.get('close', item.get('price', 0)))
                    if price <= 0:
                        continue
                    
                    # 转换为美元价格（假设原始数据是人民币/克）
                    price_usd = (price * 31.1035) / 7.2  # 克转盎司，人民币转美元
                    price_cny = price * 31.1035  # 克转盎司，保持人民币
                    
                    change = float(item.get('change', 0))
                    change_percent = (change / price) * 100 if price != 0 else 0
                    
                    historical_prices.append(GoldPriceData(
                        timestamp=date,
                        price_usd=round(price_usd, 2),
                        price_cny=round(price_cny, 2),
                        change_24h=change,
                        change_percent_24h=change_percent,
                        volume=float(item.get('volume', 0)),
                        source='汇率表(huilvbiao.com)'
                    ))
                    
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"解析历史数据项失败: {e}")
                    continue
            
            # 按日期排序（最新的在前）
            historical_prices.sort(key=lambda x: x.timestamp, reverse=True)
            
            logger.info(f"成功获取{len(historical_prices)}条历史金价数据")
            return historical_prices
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取历史数据请求失败: {e}")
            return []
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"解析历史数据失败: {e}")
            return []
        except Exception as e:
            logger.error(f"获取历史数据时发生未知错误: {e}")
            return []
    
    def _generate_mock_historical_data(self, days: int) -> List[GoldPriceData]:
        """生成模拟历史数据"""
        import random
        
        historical_data = []
        base_price = 2650.0
        current_price = base_price
        
        for i in range(days):
            # 模拟价格波动
            daily_change = random.uniform(-2, 2)  # 每日变化百分比
            current_price *= (1 + daily_change / 100)
            
            change_24h = random.uniform(-30, 30)
            change_percent = (change_24h / current_price) * 100
            
            timestamp = datetime.now() - timedelta(days=days-i-1)
            
            historical_data.append(GoldPriceData(
                timestamp=timestamp,
                price_usd=current_price,
                price_cny=current_price * 7.2,
                change_24h=change_24h,
                change_percent_24h=change_percent,
                source="模拟历史数据"
            ))
        
        # 缓存历史数据
        self._cache_historical_data(historical_data)
        return historical_data
    
    def _cache_current_price(self, price_data: GoldPriceData):
        """缓存当前价格"""
        try:
            cache_file = os.path.join(self.cache_dir, "current_gold_price.json")
            data = {
                'timestamp': price_data.timestamp.isoformat(),
                'price_usd': price_data.price_usd,
                'price_cny': price_data.price_cny,
                'change_24h': price_data.change_24h,
                'change_percent_24h': price_data.change_percent_24h,
                'source': price_data.source
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.warning(f"缓存当前价格失败: {e}")
    
    def _load_cached_price(self) -> Optional[GoldPriceData]:
        """从缓存加载价格"""
        try:
            cache_file = os.path.join(self.cache_dir, "current_gold_price.json")
            
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查缓存是否过期（超过5分钟）
                cached_time = datetime.fromisoformat(data['timestamp'])
                if datetime.now() - cached_time < timedelta(minutes=5):
                    return GoldPriceData(
                        timestamp=cached_time,
                        price_usd=data['price_usd'],
                        price_cny=data['price_cny'],
                        change_24h=data['change_24h'],
                        change_percent_24h=data['change_percent_24h'],
                        source=data['source'] + " (缓存)"
                    )
        except Exception as e:
            logger.warning(f"加载缓存价格失败: {e}")
        
        return None
    
    def _cache_historical_data(self, historical_data: List[GoldPriceData]):
        """缓存历史数据"""
        try:
            cache_file = os.path.join(self.cache_dir, "historical_gold_prices.json")
            data = []
            
            for price in historical_data:
                data.append({
                    'timestamp': price.timestamp.isoformat(),
                    'price_usd': price.price_usd,
                    'price_cny': price.price_cny,
                    'change_24h': price.change_24h,
                    'change_percent_24h': price.change_percent_24h,
                    'source': price.source
                })
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.warning(f"缓存历史数据失败: {e}")
    
    def _load_cached_historical_data(self, days: int) -> Optional[List[GoldPriceData]]:
        """从缓存加载历史数据"""
        try:
            cache_file = os.path.join(self.cache_dir, "historical_gold_prices.json")
            
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查缓存是否过期（超过1小时）
                if data:
                    latest_time = datetime.fromisoformat(data[-1]['timestamp'])
                    if datetime.now() - latest_time < timedelta(hours=1):
                        historical_data = []
                        for item in data[-days:]:  # 取最近的days天数据
                            historical_data.append(GoldPriceData(
                                timestamp=datetime.fromisoformat(item['timestamp']),
                                price_usd=item['price_usd'],
                                price_cny=item['price_cny'],
                                change_24h=item['change_24h'],
                                change_percent_24h=item['change_percent_24h'],
                                source=item['source'] + " (缓存)"
                            ))
                        return historical_data
        except Exception as e:
            logger.warning(f"加载缓存历史数据失败: {e}")
        
        return None
    
    def get_price_statistics(self, historical_data: List[GoldPriceData]) -> Dict:
        """计算价格统计信息"""
        if not historical_data:
            return {}
        
        prices = [data.price_usd for data in historical_data]
        
        return {
            'current_price': prices[-1] if prices else 0,
            'highest_price': max(prices) if prices else 0,
            'lowest_price': min(prices) if prices else 0,
            'average_price': sum(prices) / len(prices) if prices else 0,
            'price_range': max(prices) - min(prices) if prices else 0,
            'volatility': self._calculate_volatility(prices),
            'trend': self._calculate_trend(prices)
        }
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """计算价格波动率"""
        if len(prices) < 2:
            return 0
        
        import statistics
        return statistics.stdev(prices)
    
    def _calculate_trend(self, prices: List[float]) -> str:
        """计算价格趋势"""
        if len(prices) < 2:
            return "无趋势"
        
        # 简单的趋势计算：比较前半段和后半段的平均价格
        mid = len(prices) // 2
        first_half_avg = sum(prices[:mid]) / mid if mid > 0 else 0
        second_half_avg = sum(prices[mid:]) / (len(prices) - mid) if len(prices) - mid > 0 else 0
        
        if second_half_avg > first_half_avg * 1.02:  # 上涨超过2%
            return "上升趋势"
        elif second_half_avg < first_half_avg * 0.98:  # 下跌超过2%
            return "下降趋势"
        else:
            return "横盘整理"

# 创建全局实例
gold_price_fetcher = GoldPriceFetcher()

if __name__ == "__main__":
    # 测试代码
    fetcher = GoldPriceFetcher()
    
    print("获取当前金价...")
    current_price = fetcher.get_current_gold_price()
    if current_price:
        print(f"当前金价: ${current_price.price_usd:.2f} (¥{current_price.price_cny:.2f})")
        print(f"24小时变化: {current_price.change_percent_24h:.2f}%")
        print(f"数据源: {current_price.source}")
    
    print("\n获取历史金价...")
    historical_prices = fetcher.get_historical_prices(7)
    print(f"获取到 {len(historical_prices)} 天的历史数据")
    
    if historical_prices:
        stats = fetcher.get_price_statistics(historical_prices)
        print(f"\n价格统计:")
        print(f"当前价格: ${stats['current_price']:.2f}")
        print(f"最高价格: ${stats['highest_price']:.2f}")
        print(f"最低价格: ${stats['lowest_price']:.2f}")
        print(f"平均价格: ${stats['average_price']:.2f}")
        print(f"价格趋势: {stats['trend']}")