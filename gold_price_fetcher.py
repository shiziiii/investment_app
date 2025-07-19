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
            price_data = self._fetch_from_coinapi() or self._fetch_from_metals_api() or self._fetch_from_backup_source()
            
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
        """从CoinAPI获取金价数据"""
        try:
            # 使用免费的金价API
            url = "https://api.metals.live/v1/spot/gold"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # 解析数据
                price_usd = float(data.get('price', 0))
                change_24h = float(data.get('change', 0))
                change_percent = float(data.get('change_percent', 0))
                
                # 估算人民币价格 (使用固定汇率7.2作为示例)
                price_cny = price_usd * 7.2
                
                return GoldPriceData(
                    timestamp=datetime.now(),
                    price_usd=price_usd,
                    price_cny=price_cny,
                    change_24h=change_24h,
                    change_percent_24h=change_percent,
                    source="metals.live"
                )
        except Exception as e:
            logger.warning(f"从metals.live获取数据失败: {e}")
            return None
    
    def _fetch_from_metals_api(self) -> Optional[GoldPriceData]:
        """从metals-api获取金价数据"""
        try:
            # 备用API
            url = "https://api.metalpriceapi.com/v1/latest?api_key=demo&base=USD&currencies=XAU"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', {})
                
                if 'XAU' in rates:
                    # XAU是每盎司黄金的价格，需要转换
                    price_per_oz = 1 / float(rates['XAU'])  # 转换为美元/盎司
                    price_cny = price_per_oz * 7.2
                    
                    return GoldPriceData(
                        timestamp=datetime.now(),
                        price_usd=price_per_oz,
                        price_cny=price_cny,
                        change_24h=0,  # 该API不提供变化数据
                        change_percent_24h=0,
                        source="metalpriceapi.com"
                    )
        except Exception as e:
            logger.warning(f"从metalpriceapi.com获取数据失败: {e}")
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
            
            # 如果缓存没有，生成模拟历史数据
            return self._generate_mock_historical_data(days)
            
        except Exception as e:
            logger.error(f"获取历史金价失败: {e}")
            return self._generate_mock_historical_data(days)
    
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