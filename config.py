# -*- coding: utf-8 -*-
"""
配置文件
管理应用的各种配置参数
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    
    # API配置
    API_BASE_URL = os.getenv('API_BASE_URL', 'https://api.zhizengzeng.com/v1/')
    API_KEY = os.getenv('API_KEY', 'sk-zk22fff00d0d5fe4cd7a64f0f5aaac6a014687a42c264dfb')
    MODEL_NAME = os.getenv('MODEL_NAME', 'hunyuan-lite')
    
    # 情感分析配置
    SENTIMENT_CACHE_SIZE = int(os.getenv('SENTIMENT_CACHE_SIZE', '1000'))
    SENTIMENT_BATCH_SIZE = int(os.getenv('SENTIMENT_BATCH_SIZE', '10'))
    SENTIMENT_TIMEOUT = int(os.getenv('SENTIMENT_TIMEOUT', '30'))
    SENTIMENT_MAX_RETRIES = int(os.getenv('SENTIMENT_MAX_RETRIES', '3'))
    
    # 数据文件配置
    DATA_DIR = os.getenv('DATA_DIR', './data')
    CACHE_DIR = os.getenv('CACHE_DIR', './cache')
    
    # Streamlit配置
    STREAMLIT_PORT = int(os.getenv('STREAMLIT_PORT', '8501'))
    STREAMLIT_HOST = os.getenv('STREAMLIT_HOST', 'localhost')
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'investment_app.log')
    
    # 可视化配置
    CHART_THEME = os.getenv('CHART_THEME', 'plotly')
    CHART_HEIGHT = int(os.getenv('CHART_HEIGHT', '400'))
    CHART_WIDTH = int(os.getenv('CHART_WIDTH', '800'))
    
    @classmethod
    def validate_config(cls):
        """验证配置的有效性"""
        errors = []
        
        if not cls.API_KEY:
            errors.append("API_KEY 未设置")
            
        if cls.SENTIMENT_CACHE_SIZE <= 0:
            errors.append("SENTIMENT_CACHE_SIZE 必须大于0")
            
        if cls.SENTIMENT_BATCH_SIZE <= 0:
            errors.append("SENTIMENT_BATCH_SIZE 必须大于0")
            
        if cls.SENTIMENT_TIMEOUT <= 0:
            errors.append("SENTIMENT_TIMEOUT 必须大于0")
            
        return errors
    
    @classmethod
    def get_api_config(cls):
        """获取API配置"""
        return {
            'base_url': cls.API_BASE_URL,
            'api_key': cls.API_KEY,
            'model': cls.MODEL_NAME,
            'timeout': cls.SENTIMENT_TIMEOUT,
            'max_retries': cls.SENTIMENT_MAX_RETRIES
        }
    
    @classmethod
    def get_sentiment_config(cls):
        """获取情感分析配置"""
        return {
            'cache_size': cls.SENTIMENT_CACHE_SIZE,
            'batch_size': cls.SENTIMENT_BATCH_SIZE,
            'timeout': cls.SENTIMENT_TIMEOUT,
            'max_retries': cls.SENTIMENT_MAX_RETRIES
        }
    
    @classmethod
    def get_visualization_config(cls):
        """获取可视化配置"""
        return {
            'theme': cls.CHART_THEME,
            'height': cls.CHART_HEIGHT,
            'width': cls.CHART_WIDTH
        }

# 创建全局配置实例
config = Config()

# 验证配置
config_errors = config.validate_config()
if config_errors:
    print("配置错误:")
    for error in config_errors:
        print(f"  - {error}")
    print("请检查环境变量设置")