# -*- coding: utf-8 -*-
"""
工具模块
提供通用的工具函数
"""

import os
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

def setup_logging(log_level: str = 'INFO', log_file: str = 'app.log'):
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def ensure_dir(directory: str) -> None:
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        
def load_json_data(file_path: str) -> List[Dict[str, Any]]:
    """加载JSON数据文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else [data]
    except FileNotFoundError:
        logging.error(f"文件未找到: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"JSON解析错误: {e}")
        return []
    except Exception as e:
        logging.error(f"加载数据时发生错误: {e}")
        return []

def save_json_data(data: List[Dict[str, Any]], file_path: str) -> bool:
    """保存数据到JSON文件"""
    try:
        ensure_dir(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"保存数据时发生错误: {e}")
        return False

def generate_cache_key(text: str) -> str:
    """生成缓存键"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def parse_datetime(date_str: str) -> Optional[datetime]:
    """解析日期时间字符串"""
    if not date_str:
        return None
        
    # 常见的日期时间格式
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M',
        '%Y/%m/%d',
        '%m-%d %H:%M',
        '%m/%d %H:%M'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logging.warning(f"无法解析日期时间: {date_str}")
    return None

def clean_text(text: str) -> str:
    """清理文本内容"""
    if not text:
        return ""
    
    # 移除多余的空白字符
    text = ' '.join(text.split())
    
    # 移除特殊字符（保留中文、英文、数字、基本标点）
    import re
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s.,!?;:()\[\]{}"\'-]', '', text)
    
    return text.strip()

def format_number(num: float, decimal_places: int = 2) -> str:
    """格式化数字显示"""
    if num is None:
        return "N/A"
    
    if abs(num) >= 1000000:
        return f"{num/1000000:.{decimal_places}f}M"
    elif abs(num) >= 1000:
        return f"{num/1000:.{decimal_places}f}K"
    else:
        return f"{num:.{decimal_places}f}"

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """计算百分比变化"""
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100

def get_file_list(directory: str, extension: str = '.json') -> List[str]:
    """获取目录下指定扩展名的文件列表"""
    if not os.path.exists(directory):
        return []
    
    files = []
    for file in os.listdir(directory):
        if file.endswith(extension):
            files.append(os.path.join(directory, file))
    
    return sorted(files, key=os.path.getmtime, reverse=True)

def convert_to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """将数据转换为DataFrame"""
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # 处理时间列
    time_columns = ['time', 'crawl_time', 'publish_time']
    for col in time_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return df

def validate_news_data(news_item: Dict[str, Any]) -> bool:
    """验证新闻数据的完整性"""
    required_fields = ['title', 'content']
    
    for field in required_fields:
        if field not in news_item or not news_item[field]:
            return False
    
    # 检查标题和内容长度
    if len(news_item['title']) < 5 or len(news_item['content']) < 20:
        return False
    
    return True

def batch_process(items: List[Any], batch_size: int = 10):
    """批量处理数据"""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """安全获取字典值"""
    return dictionary.get(key, default) if dictionary else default

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断文本"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def get_sentiment_color(sentiment: str) -> str:
    """根据情感获取颜色"""
    color_map = {
        'positive': '#2E8B57',  # 海绿色
        'negative': '#DC143C',  # 深红色
        'neutral': '#4682B4',   # 钢蓝色
        'unknown': '#808080'    # 灰色
    }
    return color_map.get(sentiment.lower(), color_map['unknown'])

def format_sentiment_score(score: float) -> str:
    """格式化情感分数显示"""
    if score is None:
        return "N/A"
    
    if score > 0.1:
        return f"积极 ({score:.2f})"
    elif score < -0.1:
        return f"消极 ({score:.2f})"
    else:
        return f"中性 ({score:.2f})"