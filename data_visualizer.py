import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import Counter
import streamlit as st
from typing import List, Dict, Any, Optional

class DataVisualizer:
    """数据可视化类，负责生成各种图表和可视化组件"""
    
    def __init__(self):
        """初始化可视化配置"""
        self.color_map = {
            'positive': '#51cf66',
            'negative': '#ff6b6b', 
            'neutral': '#74c0fc'
        }
        
        self.sentiment_labels = {
            'positive': '积极',
            'negative': '消极',
            'neutral': '中性'
        }
    
    def plot_sentiment_distribution(self, data: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """创建情感分布饼图
        
        Args:
            data: 包含情感分析结果的数据列表
            
        Returns:
            plotly图表对象或None
        """
        if not data:
            return None
        
        # 统计情感分布
        sentiment_counts = {}
        for item in data:
            sentiment = item.get('sentiment_analysis', {}).get('sentiment', 'neutral')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # 转换为中文标签
        labels = [self.sentiment_labels.get(k, k) for k in sentiment_counts.keys()]
        values = list(sentiment_counts.values())
        colors = [self.color_map.get(k, '#74c0fc') for k in sentiment_counts.keys()]
        
        # 创建饼图
        fig = px.pie(
            values=values,
            names=labels,
            title="新闻情感分布",
            color_discrete_sequence=colors
        )
        
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>数量: %{value}<br>占比: %{percent}<extra></extra>'
        )
        fig.update_layout(
            height=400,
            font=dict(size=12),
            showlegend=True
        )
        
        return fig
    
    def plot_sentiment_timeline(self, data: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """创建情感时间线散点图
        
        Args:
            data: 包含情感分析结果的数据列表
            
        Returns:
            plotly图表对象或None
        """
        if not data:
            return None
        
        # 准备时间线数据
        timeline_data = []
        for item in data:
            sentiment_analysis = item.get('sentiment_analysis', {})
            timeline_data.append({
                'time': item.get('time', ''),
                'title': item.get('title', '')[:50] + '...',
                'sentiment': sentiment_analysis.get('sentiment', 'neutral'),
                'score': sentiment_analysis.get('score', 0),
                'confidence': sentiment_analysis.get('confidence', 0)
            })
        
        # 按时间排序
        timeline_data.sort(key=lambda x: x['time'])
        
        df = pd.DataFrame(timeline_data)
        
        # 创建散点图
        fig = px.scatter(
            df, 
            x='time', 
            y='score',
            color='sentiment',
            size='confidence',
            hover_data=['title'],
            title="情感分值时间线",
            color_discrete_map=self.color_map,
            labels={
                'time': '时间',
                'score': '情感分值',
                'sentiment': '情感类型'
            }
        )
        
        # 添加零线
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            height=400,
            xaxis_title="时间",
            yaxis_title="情感分值",
            hovermode='closest'
        )
        
        return fig
    
    def plot_news_volume(self, data: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """创建新闻数量统计图
        
        Args:
            data: 包含新闻数据的列表
            
        Returns:
            plotly图表对象或None
        """
        if not data:
            return None
        
        # 按日期统计新闻数量
        date_counts = {}
        for item in data:
            # 提取日期部分
            time_str = item.get('time', '')
            if time_str:
                try:
                    # 假设时间格式为 YYYY-MM-DD HH:MM:SS
                    date_part = time_str.split(' ')[0]
                    date_counts[date_part] = date_counts.get(date_part, 0) + 1
                except:
                    continue
        
        if not date_counts:
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame([
            {'date': date, 'count': count} 
            for date, count in sorted(date_counts.items())
        ])
        
        # 创建柱状图
        fig = px.bar(
            df,
            x='date',
            y='count',
            title="每日新闻数量",
            labels={'date': '日期', 'count': '新闻数量'},
            color='count',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            height=400,
            xaxis_title="日期",
            yaxis_title="新闻数量",
            showlegend=False
        )
        
        return fig
    
    def plot_sentiment_heatmap(self, data: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """创建情感热力图（按时间和情感分值）
        
        Args:
            data: 包含情感分析结果的数据列表
            
        Returns:
            plotly图表对象或None
        """
        if not data:
            return None
        
        # 准备热力图数据
        heatmap_data = []
        for item in data:
            sentiment_analysis = item.get('sentiment_analysis', {})
            time_str = item.get('time', '')
            
            if time_str:
                try:
                    # 尝试不同的时间格式
                    if ' ' in time_str:
                        # 格式: "YYYY-MM-DD HH:MM:SS"
                        date_part, time_part = time_str.split(' ', 1)
                        hour = int(time_part.split(':')[0])
                    else:
                        # 如果没有时间部分，使用默认值
                        date_part = time_str
                        hour = 12  # 默认中午12点
                    
                    score = sentiment_analysis.get('score', 0)
                    
                    heatmap_data.append({
                        'date': date_part,
                        'hour': hour,
                        'score': score
                    })
                except Exception as e:
                    # 如果解析失败，跳过这条数据
                    continue
        
        if not heatmap_data:
            return None
        
        try:
            df = pd.DataFrame(heatmap_data)
            
            # 按日期和小时聚合平均分值
            pivot_df = df.groupby(['date', 'hour'])['score'].mean().reset_index()
            
            # 检查是否有足够的数据
            if len(pivot_df) == 0:
                return None
            
            pivot_table = pivot_df.pivot(index='date', columns='hour', values='score')
            
            # 填充缺失值
            pivot_table = pivot_table.fillna(0)
            
            # 如果数据太少，创建简化版本
            if pivot_table.shape[0] < 2 or pivot_table.shape[1] < 2:
                # 创建简单的条形图代替热力图
                avg_scores_by_date = df.groupby('date')['score'].mean().reset_index()
                
                fig = px.bar(
                    avg_scores_by_date,
                    x='date',
                    y='score',
                    title="按日期分组的平均情感分值",
                    labels={'date': '日期', 'score': '平均情感分值'},
                    color='score',
                    color_continuous_scale='RdYlGn'
                )
                
                fig.update_layout(height=400)
                return fig
            
            # 创建热力图
            fig = px.imshow(
                pivot_table.values,
                x=[f"{h:02d}:00" for h in pivot_table.columns],
                y=pivot_table.index,
                color_continuous_scale='RdYlGn',
                title="情感分值时间热力图",
                labels={'x': '小时', 'y': '日期', 'color': '平均情感分值'}
            )
            
            fig.update_layout(height=400)
            
            return fig
            
        except Exception as e:
            # 如果热力图创建失败，返回None
            return None
    
    def generate_wordcloud(self, data: List[Dict[str, Any]], sentiment_filter: Optional[str] = None) -> Optional[plt.Figure]:
        """生成关键词云图
        
        Args:
            data: 包含情感分析结果的数据列表
            sentiment_filter: 可选的情感过滤器 ('positive', 'negative', 'neutral')
            
        Returns:
            matplotlib图表对象或None
        """
        if not data:
            return None
        
        # 收集关键词
        all_keywords = []
        for item in data:
            sentiment_analysis = item.get('sentiment_analysis', {})
            
            # 如果指定了情感过滤器，只处理匹配的数据
            if sentiment_filter and sentiment_analysis.get('sentiment') != sentiment_filter:
                continue
                
            keywords = sentiment_analysis.get('keywords', [])
            if keywords:
                all_keywords.extend(keywords)
        
        if not all_keywords:
            return None
        
        # 统计词频
        word_freq = Counter(all_keywords)
        
        # 生成词云
        try:
            # 尝试使用系统中文字体
            import platform
            if platform.system() == 'Windows':
                font_path = 'C:/Windows/Fonts/simhei.ttf'  # 黑体
            else:
                font_path = None
        except:
            font_path = None
            
        wordcloud = WordCloud(
            width=800, 
            height=400, 
            background_color='white',
            font_path=font_path,
            max_words=100,
            colormap='viridis',
            prefer_horizontal=0.9,
            min_font_size=10
        ).generate_from_frequencies(word_freq)
        
        # 创建matplotlib图表
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        
        title = "关键词云图"
        if sentiment_filter:
            title += f" ({self.sentiment_labels.get(sentiment_filter, sentiment_filter)})"
        
        # 设置中文字体用于标题
        try:
            import matplotlib.font_manager as fm
            if platform.system() == 'Windows':
                # 使用系统中文字体
                ax.set_title(title, fontsize=16, pad=20, fontproperties='SimHei')
            else:
                ax.set_title(title, fontsize=16, pad=20)
        except:
            # 如果字体设置失败，使用默认设置
            ax.set_title(title, fontsize=16, pad=20)
        
        return fig
    
    def plot_confidence_distribution(self, data: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """创建置信度分布直方图
        
        Args:
            data: 包含情感分析结果的数据列表
            
        Returns:
            plotly图表对象或None
        """
        if not data:
            return None
        
        # 提取置信度数据
        confidences = []
        sentiments = []
        
        for item in data:
            sentiment_analysis = item.get('sentiment_analysis', {})
            confidence = sentiment_analysis.get('confidence', 0)
            sentiment = sentiment_analysis.get('sentiment', 'neutral')
            
            confidences.append(confidence)
            sentiments.append(sentiment)
        
        df = pd.DataFrame({
            'confidence': confidences,
            'sentiment': sentiments
        })
        
        # 创建分组直方图
        fig = px.histogram(
            df,
            x='confidence',
            color='sentiment',
            title="置信度分布（按情感分类）",
            labels={'confidence': '置信度分值', 'count': '数量'},
            color_discrete_map=self.color_map,
            nbins=20
        )
        
        fig.update_layout(
            height=400,
            xaxis_title="置信度分值",
            yaxis_title="数量",
            bargap=0.1
        )
        
        return fig
    
    def plot_score_vs_confidence(self, data: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """创建情感分值与置信度的散点图
        
        Args:
            data: 包含情感分析结果的数据列表
            
        Returns:
            plotly图表对象或None
        """
        if not data:
            return None
        
        # 准备数据
        plot_data = []
        for item in data:
            sentiment_analysis = item.get('sentiment_analysis', {})
            plot_data.append({
                'score': sentiment_analysis.get('score', 0),
                'confidence': sentiment_analysis.get('confidence', 0),
                'sentiment': sentiment_analysis.get('sentiment', 'neutral'),
                'title': item.get('title', '')[:50] + '...'
            })
        
        df = pd.DataFrame(plot_data)
        
        # 创建散点图
        fig = px.scatter(
            df,
            x='score',
            y='confidence',
            color='sentiment',
            hover_data=['title'],
            title="情感分值与置信度关系",
            labels={
                'score': '情感分值',
                'confidence': '置信度',
                'sentiment': '情感类型'
            },
            color_discrete_map=self.color_map
        )
        
        fig.update_layout(
            height=400,
            xaxis_title="情感分值",
            yaxis_title="置信度"
        )
        
        return fig
    
    def create_summary_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算汇总指标
        
        Args:
            data: 包含情感分析结果的数据列表
            
        Returns:
            包含各种统计指标的字典
        """
        if not data:
            return {}
        
        # 计算基础统计
        total_news = len(data)
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        total_score = 0
        total_confidence = 0
        scores = []
        confidences = []
        
        for item in data:
            sentiment_analysis = item.get('sentiment_analysis', {})
            sentiment = sentiment_analysis.get('sentiment', 'neutral')
            score = sentiment_analysis.get('score', 0)
            confidence = sentiment_analysis.get('confidence', 0)
            
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            total_score += score
            total_confidence += confidence
            scores.append(score)
            confidences.append(confidence)
        
        avg_score = total_score / total_news if total_news > 0 else 0
        avg_confidence = total_confidence / total_news if total_news > 0 else 0
        
        # 市场情绪判断
        if avg_score > 0.2:
            market_mood = "😊 乐观"
            market_mood_en = "Optimistic"
        elif avg_score < -0.2:
            market_mood = "😟 悲观"
            market_mood_en = "Pessimistic"
        else:
            market_mood = "😐 中性"
            market_mood_en = "Neutral"
        
        return {
            'total_news': total_news,
            'sentiment_counts': sentiment_counts,
            'avg_score': avg_score,
            'avg_confidence': avg_confidence,
            'market_mood': market_mood,
            'market_mood_en': market_mood_en,
            'score_std': np.std(scores) if scores else 0,
            'confidence_std': np.std(confidences) if confidences else 0,
            'positive_ratio': sentiment_counts['positive'] / total_news if total_news > 0 else 0,
            'negative_ratio': sentiment_counts['negative'] / total_news if total_news > 0 else 0,
            'neutral_ratio': sentiment_counts['neutral'] / total_news if total_news > 0 else 0
        }