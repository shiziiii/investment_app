#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资建议引擎模块
功能：基于情感分析结果生成投资建议和风险评估
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MarketSentiment(Enum):
    """市场情绪枚举"""
    VERY_BULLISH = "强烈看涨"
    BULLISH = "温和看涨"
    NEUTRAL = "中性观望"
    BEARISH = "温和看跌"
    VERY_BEARISH = "强烈看跌"

class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "低风险"
    MEDIUM = "中等风险"
    HIGH = "高风险"
    VERY_HIGH = "极高风险"

class TrendDirection(Enum):
    """趋势方向枚举"""
    STRONG_UPWARD = "强烈上升"
    UPWARD = "温和上升"
    SIDEWAYS = "横盘整理"
    DOWNWARD = "温和下降"
    STRONG_DOWNWARD = "强烈下降"

@dataclass
class TrendAnalysis:
    """趋势分析数据类"""
    direction: TrendDirection
    strength: float  # 趋势强度 0-1
    duration: int    # 趋势持续天数
    momentum: float  # 动量指标 -1到1
    volatility: float # 波动率
    consistency: float # 趋势一致性 0-1
    recent_change: float # 近期变化率

@dataclass
class InvestmentAdvice:
    """投资建议数据类"""
    market_sentiment: MarketSentiment
    risk_level: RiskLevel
    confidence_score: float
    recommendation: str
    reasoning: str
    action_suggestions: List[str]
    risk_warnings: List[str]
    time_horizon: str
    position_sizing: str
    trend_analysis: TrendAnalysis
    trend_impact: str  # 趋势对投资决策的影响描述

class InvestmentAdvisor:
    """投资建议引擎"""
    
    def __init__(self):
        """初始化投资建议引擎"""
        # 情感分值阈值配置
        self.sentiment_thresholds = {
            'very_bullish': 0.6,
            'bullish': 0.2,
            'neutral_upper': 0.2,
            'neutral_lower': -0.2,
            'bearish': -0.6
        }
        
        # 置信度阈值
        self.confidence_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
        
        # 风险评估权重
        self.risk_weights = {
            'sentiment_volatility': 0.3,
            'confidence_level': 0.25,
            'news_volume': 0.2,
            'sentiment_consistency': 0.25
        }
        
        # 趋势分析配置
        self.trend_config = {
            'min_data_points': 3,  # 最少数据点数
            'short_term_days': 3,  # 短期趋势天数
            'medium_term_days': 7, # 中期趋势天数
            'trend_threshold': 0.1, # 趋势判断阈值
            'momentum_weight': 0.4, # 动量权重
            'consistency_weight': 0.3, # 一致性权重
            'volatility_weight': 0.3   # 波动性权重
        }
    
    def analyze_market_sentiment(self, sentiment_data: List[Dict]) -> MarketSentiment:
        """
        分析市场情绪
        
        Args:
            sentiment_data: 情感分析数据列表
            
        Returns:
            市场情绪枚举值
        """
        if not sentiment_data:
            return MarketSentiment.NEUTRAL
        
        # 计算平均情感分值
        scores = []
        for item in sentiment_data:
            sentiment_analysis = item.get('sentiment_analysis', {})
            if sentiment_analysis:
                scores.append(sentiment_analysis.get('score', 0.0))
        
        if not scores:
            return MarketSentiment.NEUTRAL
        
        avg_score = sum(scores) / len(scores)
        
        # 根据平均分值判断市场情绪
        if avg_score > self.sentiment_thresholds['very_bullish']:
            return MarketSentiment.VERY_BULLISH
        elif avg_score > self.sentiment_thresholds['bullish']:
            return MarketSentiment.BULLISH
        elif avg_score >= self.sentiment_thresholds['neutral_lower']:
            return MarketSentiment.NEUTRAL
        elif avg_score >= self.sentiment_thresholds['bearish']:
            return MarketSentiment.BEARISH
        else:
            return MarketSentiment.VERY_BEARISH
    
    def calculate_risk_level(self, sentiment_data: List[Dict]) -> Tuple[RiskLevel, Dict]:
        """
        计算风险等级
        
        Args:
            sentiment_data: 情感分析数据列表
            
        Returns:
            风险等级和详细风险指标
        """
        if not sentiment_data:
            return RiskLevel.HIGH, {}
        
        # 提取分析数据
        scores = []
        confidences = []
        sentiments = []
        
        for item in sentiment_data:
            sentiment_analysis = item.get('sentiment_analysis', {})
            if sentiment_analysis:
                scores.append(sentiment_analysis.get('score', 0.0))
                confidences.append(sentiment_analysis.get('confidence', 0.0))
                sentiments.append(sentiment_analysis.get('sentiment', 'neutral'))
        
        if not scores:
            return RiskLevel.HIGH, {}
        
        # 计算风险指标
        risk_metrics = self._calculate_risk_metrics(scores, confidences, sentiments)
        
        # 计算综合风险分数
        risk_score = (
            risk_metrics['sentiment_volatility'] * self.risk_weights['sentiment_volatility'] +
            risk_metrics['confidence_risk'] * self.risk_weights['confidence_level'] +
            risk_metrics['volume_risk'] * self.risk_weights['news_volume'] +
            risk_metrics['consistency_risk'] * self.risk_weights['sentiment_consistency']
        )
        
        # 确定风险等级
        if risk_score < 0.3:
            risk_level = RiskLevel.LOW
        elif risk_score < 0.5:
            risk_level = RiskLevel.MEDIUM
        elif risk_score < 0.7:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.VERY_HIGH
        
        return risk_level, risk_metrics
    
    def analyze_sentiment_trend(self, sentiment_data: List[Dict]) -> TrendAnalysis:
        """
        分析情感趋势
        
        Args:
            sentiment_data: 情感分析数据列表
            
        Returns:
            趋势分析结果
        """
        if not sentiment_data or len(sentiment_data) < self.trend_config['min_data_points']:
            return self._create_default_trend()
        
        # 按时间排序数据
        sorted_data = self._sort_data_by_time(sentiment_data)
        
        # 提取时间序列数据
        time_series = self._extract_time_series(sorted_data)
        
        if len(time_series) < self.trend_config['min_data_points']:
            return self._create_default_trend()
        
        # 计算趋势指标
        direction = self._calculate_trend_direction(time_series)
        strength = self._calculate_trend_strength(time_series)
        duration = self._calculate_trend_duration(time_series)
        momentum = self._calculate_momentum(time_series)
        volatility = self._calculate_volatility(time_series)
        consistency = self._calculate_trend_consistency(time_series)
        recent_change = self._calculate_recent_change(time_series)
        
        return TrendAnalysis(
            direction=direction,
            strength=strength,
            duration=duration,
            momentum=momentum,
            volatility=volatility,
            consistency=consistency,
            recent_change=recent_change
        )
    
    def _sort_data_by_time(self, sentiment_data: List[Dict]) -> List[Dict]:
        """
        按时间排序数据
        
        Args:
            sentiment_data: 情感分析数据列表
            
        Returns:
            按时间排序的数据列表
        """
        def parse_time(item):
            time_str = item.get('time', '')
            try:
                # 尝试解析不同的时间格式
                if 'T' in time_str:
                    return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                else:
                    return datetime.strptime(time_str, '%Y-%m-%d')
            except:
                return datetime.min
        
        return sorted(sentiment_data, key=parse_time)
    
    def _extract_time_series(self, sorted_data: List[Dict]) -> List[Dict]:
        """
        提取时间序列数据
        
        Args:
            sorted_data: 按时间排序的数据
            
        Returns:
            时间序列数据点列表
        """
        time_series = []
        
        for item in sorted_data:
            sentiment_analysis = item.get('sentiment_analysis', {})
            if sentiment_analysis:
                time_point = {
                    'time': item.get('time', ''),
                    'score': sentiment_analysis.get('score', 0.0),
                    'confidence': sentiment_analysis.get('confidence', 0.0),
                    'sentiment': sentiment_analysis.get('sentiment', 'neutral')
                }
                time_series.append(time_point)
        
        return time_series
    
    def _calculate_trend_direction(self, time_series: List[Dict]) -> TrendDirection:
        """
        计算趋势方向
        
        Args:
            time_series: 时间序列数据
            
        Returns:
            趋势方向
        """
        if len(time_series) < 2:
            return TrendDirection.SIDEWAYS
        
        scores = [point['score'] for point in time_series]
        
        # 计算线性回归斜率
        import numpy as np
        x = np.arange(len(scores))
        y = np.array(scores)
        
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]
        else:
            slope = 0
        
        # 根据斜率判断趋势方向
        threshold = self.trend_config['trend_threshold']
        
        if slope > threshold * 2:
            return TrendDirection.STRONG_UPWARD
        elif slope > threshold:
            return TrendDirection.UPWARD
        elif slope < -threshold * 2:
            return TrendDirection.STRONG_DOWNWARD
        elif slope < -threshold:
            return TrendDirection.DOWNWARD
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_trend_strength(self, time_series: List[Dict]) -> float:
        """
        计算趋势强度
        
        Args:
            time_series: 时间序列数据
            
        Returns:
            趋势强度 (0-1)
        """
        if len(time_series) < 2:
            return 0.0
        
        scores = [point['score'] for point in time_series]
        
        import numpy as np
        x = np.arange(len(scores))
        y = np.array(scores)
        
        # 计算R²值作为趋势强度指标
        if len(x) > 1:
            correlation = np.corrcoef(x, y)[0, 1]
            r_squared = correlation ** 2 if not np.isnan(correlation) else 0.0
        else:
            r_squared = 0.0
        
        return min(max(r_squared, 0.0), 1.0)
    
    def _calculate_trend_duration(self, time_series: List[Dict]) -> int:
        """
        计算趋势持续天数
        
        Args:
            time_series: 时间序列数据
            
        Returns:
            趋势持续天数
        """
        if len(time_series) < 2:
            return 0
        
        # 简化计算：返回数据跨度天数
        try:
            first_time = datetime.strptime(time_series[0]['time'], '%Y-%m-%d')
            last_time = datetime.strptime(time_series[-1]['time'], '%Y-%m-%d')
            duration = (last_time - first_time).days + 1
            return max(duration, 1)
        except:
            return len(time_series)
    
    def _calculate_momentum(self, time_series: List[Dict]) -> float:
        """
        计算动量指标
        
        Args:
            time_series: 时间序列数据
            
        Returns:
            动量指标 (-1到1)
        """
        if len(time_series) < 3:
            return 0.0
        
        scores = [point['score'] for point in time_series]
        
        # 计算短期和长期平均值
        short_term = min(self.trend_config['short_term_days'], len(scores))
        
        recent_avg = sum(scores[-short_term:]) / short_term
        overall_avg = sum(scores) / len(scores)
        
        # 动量 = (近期平均 - 整体平均) / 最大可能差值
        momentum = (recent_avg - overall_avg) / 2.0  # 假设最大差值为2
        
        return min(max(momentum, -1.0), 1.0)
    
    def _calculate_volatility(self, time_series: List[Dict]) -> float:
        """
        计算波动率
        
        Args:
            time_series: 时间序列数据
            
        Returns:
            波动率 (0-1)
        """
        if len(time_series) < 2:
            return 0.0
        
        scores = [point['score'] for point in time_series]
        
        import numpy as np
        volatility = np.std(scores)
        
        # 标准化到0-1范围（假设最大标准差为1）
        return min(volatility, 1.0)
    
    def _calculate_trend_consistency(self, time_series: List[Dict]) -> float:
        """
        计算趋势一致性
        
        Args:
            time_series: 时间序列数据
            
        Returns:
            趋势一致性 (0-1)
        """
        if len(time_series) < 3:
            return 0.0
        
        scores = [point['score'] for point in time_series]
        
        # 计算相邻点的变化方向一致性
        changes = []
        for i in range(1, len(scores)):
            change = scores[i] - scores[i-1]
            if abs(change) > 0.01:  # 忽略微小变化
                changes.append(1 if change > 0 else -1)
            else:
                changes.append(0)
        
        if not changes:
            return 0.0
        
        # 计算同方向变化的比例
        positive_changes = sum(1 for c in changes if c > 0)
        negative_changes = sum(1 for c in changes if c < 0)
        total_directional_changes = positive_changes + negative_changes
        
        if total_directional_changes == 0:
            return 0.0
        
        # 一致性 = 主导方向的比例
        consistency = max(positive_changes, negative_changes) / total_directional_changes
        
        return consistency
    
    def _calculate_recent_change(self, time_series: List[Dict]) -> float:
        """
        计算近期变化率
        
        Args:
            time_series: 时间序列数据
            
        Returns:
            近期变化率
        """
        if len(time_series) < 2:
            return 0.0
        
        # 计算最近几个数据点的变化
        recent_points = min(3, len(time_series))
        recent_scores = [point['score'] for point in time_series[-recent_points:]]
        
        if len(recent_scores) < 2:
            return 0.0
        
        # 变化率 = (最新值 - 起始值) / 时间跨度
        change_rate = (recent_scores[-1] - recent_scores[0]) / (len(recent_scores) - 1)
        
        return change_rate
    
    def _create_default_trend(self) -> TrendAnalysis:
        """
        创建默认趋势分析（数据不足时）
        
        Returns:
            默认趋势分析
        """
        return TrendAnalysis(
            direction=TrendDirection.SIDEWAYS,
            strength=0.0,
            duration=0,
            momentum=0.0,
            volatility=0.0,
            consistency=0.0,
            recent_change=0.0
        )
    
    def _calculate_risk_metrics(self, scores: List[float], confidences: List[float], 
                               sentiments: List[str]) -> Dict[str, float]:
        """
        计算详细风险指标
        
        Args:
            scores: 情感分值列表
            confidences: 置信度列表
            sentiments: 情感类别列表
            
        Returns:
            风险指标字典
        """
        import numpy as np
        
        # 情感分值波动性
        sentiment_volatility = np.std(scores) if len(scores) > 1 else 0.0
        
        # 置信度风险（低置信度 = 高风险）
        avg_confidence = np.mean(confidences) if confidences else 0.0
        confidence_risk = 1.0 - avg_confidence
        
        # 新闻数量风险（数量过少或过多都有风险）
        news_count = len(scores)
        if news_count < 5:
            volume_risk = 0.8  # 数据不足
        elif news_count > 50:
            volume_risk = 0.6  # 信息过载
        else:
            volume_risk = 0.2  # 适中
        
        # 情感一致性风险
        sentiment_counts = {}
        for sentiment in sentiments:
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # 计算情感分布的熵（不一致性）
        total = len(sentiments)
        entropy = 0.0
        for count in sentiment_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * np.log2(p)
        
        # 标准化熵值（最大熵为log2(3) ≈ 1.585）
        max_entropy = np.log2(min(3, len(sentiment_counts))) if sentiment_counts else 1.0
        consistency_risk = entropy / max_entropy if max_entropy > 0 else 0.0
        
        return {
            'sentiment_volatility': min(sentiment_volatility * 2, 1.0),  # 标准化到0-1
            'confidence_risk': confidence_risk,
            'volume_risk': volume_risk,
            'consistency_risk': consistency_risk,
            'avg_confidence': avg_confidence,
            'news_count': news_count,
            'sentiment_distribution': sentiment_counts
        }
    
    def generate_investment_advice(self, sentiment_data: List[Dict]) -> InvestmentAdvice:
        """
        生成投资建议
        
        Args:
            sentiment_data: 情感分析数据列表
            
        Returns:
            投资建议对象
        """
        if not sentiment_data:
            return self._create_default_advice()
        
        # 分析市场情绪
        market_sentiment = self.analyze_market_sentiment(sentiment_data)
        
        # 计算风险等级
        risk_level, risk_metrics = self.calculate_risk_level(sentiment_data)
        
        # 分析情感趋势
        trend_analysis = self.analyze_sentiment_trend(sentiment_data)
        
        # 计算置信度分数（包含趋势因素）
        confidence_score = self._calculate_confidence_score_with_trend(sentiment_data, risk_metrics, trend_analysis)
        
        # 生成具体建议（包含趋势考量）
        recommendation = self._generate_recommendation_with_trend(market_sentiment, risk_level, trend_analysis)
        reasoning = self._generate_reasoning_with_trend(market_sentiment, risk_level, risk_metrics, trend_analysis)
        action_suggestions = self._generate_action_suggestions_with_trend(market_sentiment, risk_level, trend_analysis)
        risk_warnings = self._generate_risk_warnings_with_trend(risk_level, risk_metrics, trend_analysis)
        time_horizon = self._determine_time_horizon_with_trend(market_sentiment, risk_level, trend_analysis)
        position_sizing = self._suggest_position_sizing_with_trend(market_sentiment, risk_level, trend_analysis)
        
        # 生成趋势对投资决策的影响描述
        trend_impact = self._generate_trend_impact_description(trend_analysis, market_sentiment)
        
        return InvestmentAdvice(
            market_sentiment=market_sentiment,
            risk_level=risk_level,
            confidence_score=confidence_score,
            recommendation=recommendation,
            reasoning=reasoning,
            action_suggestions=action_suggestions,
            risk_warnings=risk_warnings,
            time_horizon=time_horizon,
            position_sizing=position_sizing,
            trend_analysis=trend_analysis,
            trend_impact=trend_impact
        )
    
    def _generate_trend_impact_description(self, trend_analysis: TrendAnalysis, 
                                         market_sentiment: MarketSentiment) -> str:
        """
        生成趋势对投资决策的影响描述
        
        Args:
            trend_analysis: 趋势分析结果
            market_sentiment: 市场情感
            
        Returns:
            趋势影响描述
        """
        impact_parts = []
        
        # 趋势方向影响
        if trend_analysis.direction == TrendDirection.STRONG_UPWARD:
            impact_parts.append("强烈上升趋势支持积极投资策略")
        elif trend_analysis.direction == TrendDirection.UPWARD:
            impact_parts.append("上升趋势有利于投资机会")
        elif trend_analysis.direction == TrendDirection.STRONG_DOWNWARD:
            impact_parts.append("强烈下降趋势建议谨慎或避险")
        elif trend_analysis.direction == TrendDirection.DOWNWARD:
            impact_parts.append("下降趋势增加投资风险")
        else:
            impact_parts.append("横盘趋势适合观望或区间操作")
        
        # 趋势强度影响
        if trend_analysis.strength > 0.7:
            impact_parts.append("高趋势强度增加决策信心")
        elif trend_analysis.strength < 0.3:
            impact_parts.append("低趋势强度降低决策确定性")
        
        # 波动率影响
        if trend_analysis.volatility > 0.6:
            impact_parts.append("高波动率要求更严格的风险管理")
        
        # 动量影响
        if abs(trend_analysis.momentum) > 0.3:
            momentum_impact = "支持趋势延续" if trend_analysis.momentum > 0 else "暗示可能反转"
            impact_parts.append(f"当前动量{momentum_impact}")
        
        if not impact_parts:
            return "趋势分析对当前投资决策影响有限"
        
        return "；".join(impact_parts) + "。"
    
    def _calculate_confidence_score_with_trend(self, sentiment_data: List[Dict], 
                                             risk_metrics: Dict, trend_analysis: TrendAnalysis) -> float:
        """
        计算包含趋势因素的置信度分数
        
        Args:
            sentiment_data: 情感分析数据
            risk_metrics: 风险指标
            trend_analysis: 趋势分析结果
            
        Returns:
            置信度分数（0-1）
        """
        # 获取基础置信度
        base_confidence = self._calculate_confidence_score(sentiment_data, risk_metrics)
        
        # 趋势因素调整
        trend_adjustment = 0.0
        
        # 趋势强度越高，置信度越高
        trend_adjustment += trend_analysis.strength * 0.1
        
        # 趋势一致性越高，置信度越高
        trend_adjustment += trend_analysis.consistency * 0.1
        
        # 波动率越低，置信度越高
        trend_adjustment += (1 - trend_analysis.volatility) * 0.05
        
        # 趋势持续时间适中时置信度较高
        if 3 <= trend_analysis.duration <= 30:
            trend_adjustment += 0.05
        
        adjusted_confidence = base_confidence + trend_adjustment
        return min(max(adjusted_confidence, 0.0), 1.0)
    
    def _calculate_confidence_score(self, sentiment_data: List[Dict], 
                                   risk_metrics: Dict) -> float:
        """
        计算建议的置信度分数
        
        Args:
            sentiment_data: 情感分析数据
            risk_metrics: 风险指标
            
        Returns:
            置信度分数（0-1）
        """
        if not sentiment_data:
            return 0.0
        
        # 基础置信度（基于情感分析的平均置信度）
        confidences = []
        for item in sentiment_data:
            sentiment_analysis = item.get('sentiment_analysis', {})
            if sentiment_analysis:
                confidences.append(sentiment_analysis.get('confidence', 0.0))
        
        base_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # 如果基础置信度为0，设置最小值
        if base_confidence == 0.0:
            base_confidence = 0.3  # 设置最小基础置信度
        
        # 调整因子（使用加权平均而非相乘，避免结果过小）
        data_quality_factor = min(len(sentiment_data) / 10, 1.0)  # 数据量调整
        consistency_factor = 1.0 - risk_metrics.get('consistency_risk', 0.3)  # 一致性调整
        volatility_factor = 1.0 - risk_metrics.get('sentiment_volatility', 0.3)  # 波动性调整
        
        # 使用加权平均计算最终置信度，而不是相乘
        weights = [0.5, 0.2, 0.15, 0.15]  # 基础置信度权重最高
        factors = [base_confidence, data_quality_factor, consistency_factor, volatility_factor]
        
        final_confidence = sum(w * f for w, f in zip(weights, factors))
        
        # 确保置信度在合理范围内
        final_confidence = max(final_confidence, 0.1)  # 最小置信度10%
        
        return round(min(max(final_confidence, 0.0), 1.0), 3)
    
    def _generate_recommendation_with_trend(self, market_sentiment: MarketSentiment, 
                                          risk_level: RiskLevel, trend_analysis: TrendAnalysis) -> str:
        """
        生成包含趋势考量的投资建议文本
        
        Args:
            market_sentiment: 市场情绪
            risk_level: 风险等级
            trend_analysis: 趋势分析结果
            
        Returns:
            投资建议文本
        """
        base_recommendation = self._generate_recommendation(market_sentiment, risk_level)
        
        # 根据趋势调整建议
        if trend_analysis.direction in [TrendDirection.STRONG_UPWARD, TrendDirection.UPWARD]:
            if trend_analysis.strength > 0.7 and trend_analysis.consistency > 0.6:
                if "增加" in base_recommendation:
                    return base_recommendation.replace("建议", "强烈建议")
                elif "保持" in base_recommendation:
                    return base_recommendation.replace("保持", "适度增加")
        
        elif trend_analysis.direction in [TrendDirection.STRONG_DOWNWARD, TrendDirection.DOWNWARD]:
            if trend_analysis.strength > 0.7 and trend_analysis.consistency > 0.6:
                if "减少" in base_recommendation:
                    return base_recommendation.replace("建议", "强烈建议")
                elif "保持" in base_recommendation:
                    return base_recommendation.replace("保持", "适度减少")
        
        # 趋势不明确或波动过大时保守处理
        elif trend_analysis.volatility > 0.8:
            if "增加" in base_recommendation or "减少" in base_recommendation:
                return "建议保持谨慎，密切观察市场变化"
        
        return base_recommendation
    
    def _generate_recommendation(self, market_sentiment: MarketSentiment, 
                               risk_level: RiskLevel) -> str:
        """
        生成投资建议文本
        
        Args:
            market_sentiment: 市场情绪
            risk_level: 风险等级
            
        Returns:
            投资建议文本
        """
        recommendations = {
            MarketSentiment.VERY_BULLISH: {
                RiskLevel.LOW: "强烈建议增加黄金配置，市场情绪极度乐观且风险可控",
                RiskLevel.MEDIUM: "建议适度增加黄金配置，但需注意风险管理",
                RiskLevel.HIGH: "谨慎看涨，建议小幅增加配置并设置止损",
                RiskLevel.VERY_HIGH: "虽然情绪乐观，但风险极高，建议观望"
            },
            MarketSentiment.BULLISH: {
                RiskLevel.LOW: "建议增加黄金配置，市场情绪积极",
                RiskLevel.MEDIUM: "建议适度增加黄金配置",
                RiskLevel.HIGH: "谨慎乐观，可考虑小幅增加配置",
                RiskLevel.VERY_HIGH: "情绪积极但风险过高，建议观望"
            },
            MarketSentiment.NEUTRAL: {
                RiskLevel.LOW: "建议保持现有配置，市场情绪中性",
                RiskLevel.MEDIUM: "建议保持现有配置并观察市场变化",
                RiskLevel.HIGH: "建议保持谨慎，避免大幅调整配置",
                RiskLevel.VERY_HIGH: "市场不确定性高，建议观望"
            },
            MarketSentiment.BEARISH: {
                RiskLevel.LOW: "建议减少黄金配置，市场情绪偏悲观",
                RiskLevel.MEDIUM: "建议适度减少黄金配置",
                RiskLevel.HIGH: "建议减少配置并加强风险管理",
                RiskLevel.VERY_HIGH: "强烈建议减少配置，风险极高"
            },
            MarketSentiment.VERY_BEARISH: {
                RiskLevel.LOW: "强烈建议减少黄金配置，市场情绪极度悲观",
                RiskLevel.MEDIUM: "建议大幅减少黄金配置",
                RiskLevel.HIGH: "建议大幅减少配置并考虑对冲",
                RiskLevel.VERY_HIGH: "建议避免黄金投资，风险极高"
            }
        }
        
        return recommendations.get(market_sentiment, {}).get(risk_level, "建议保持谨慎")
    
    def _generate_reasoning_with_trend(self, market_sentiment: MarketSentiment, 
                                     risk_level: RiskLevel, risk_metrics: Dict, 
                                     trend_analysis: TrendAnalysis) -> str:
        """
        生成包含趋势分析的分析理由
        
        Args:
            market_sentiment: 市场情绪
            risk_level: 风险等级
            risk_metrics: 风险指标
            trend_analysis: 趋势分析结果
            
        Returns:
            分析理由文本
        """
        base_reasoning = self._generate_reasoning(market_sentiment, risk_level, risk_metrics)
        
        # 添加趋势分析部分
        trend_reasoning = self._generate_trend_reasoning(trend_analysis)
        
        return f"{base_reasoning} {trend_reasoning}"
    
    def _generate_trend_reasoning(self, trend_analysis: TrendAnalysis) -> str:
        """
        生成趋势分析推理
        
        Args:
            trend_analysis: 趋势分析结果
            
        Returns:
            趋势推理描述
        """
        direction_desc = {
            TrendDirection.STRONG_UPWARD: "强烈上升",
            TrendDirection.UPWARD: "上升",
            TrendDirection.SIDEWAYS: "横盘整理",
            TrendDirection.DOWNWARD: "下降",
            TrendDirection.STRONG_DOWNWARD: "强烈下降"
        }
        
        reasoning_parts = []
        
        # 趋势方向
        direction = direction_desc.get(trend_analysis.direction, "不明确")
        reasoning_parts.append(f"趋势分析显示市场情感呈现{direction}态势")
        
        # 趋势强度
        if trend_analysis.strength > 0.7:
            reasoning_parts.append(f"趋势强度较高({trend_analysis.strength:.2f})")
        elif trend_analysis.strength > 0.4:
            reasoning_parts.append(f"趋势强度中等({trend_analysis.strength:.2f})")
        else:
            reasoning_parts.append(f"趋势强度较低({trend_analysis.strength:.2f})")
        
        # 波动率分析
        if trend_analysis.volatility > 0.6:
            reasoning_parts.append(f"市场波动率较高({trend_analysis.volatility:.2f})")
        elif trend_analysis.volatility < 0.3:
            reasoning_parts.append(f"市场相对稳定({trend_analysis.volatility:.2f})")
        
        return "，".join(reasoning_parts) + "。"
    
    def _generate_reasoning(self, market_sentiment: MarketSentiment, 
                          risk_level: RiskLevel, risk_metrics: Dict) -> str:
        """
        生成分析理由
        
        Args:
            market_sentiment: 市场情绪
            risk_level: 风险等级
            risk_metrics: 风险指标
            
        Returns:
            分析理由文本
        """
        sentiment_desc = market_sentiment.value
        risk_desc = risk_level.value
        
        reasoning_parts = [
            f"当前市场情绪为{sentiment_desc}，风险等级为{risk_desc}。"
        ]
        
        # 添加具体的风险分析
        if 'avg_confidence' in risk_metrics:
            conf_pct = risk_metrics['avg_confidence'] * 100
            reasoning_parts.append(f"分析置信度为{conf_pct:.1f}%。")
        
        if 'news_count' in risk_metrics:
            count = risk_metrics['news_count']
            reasoning_parts.append(f"基于{count}条新闻数据的分析。")
        
        if 'sentiment_distribution' in risk_metrics:
            dist = risk_metrics['sentiment_distribution']
            if dist:
                main_sentiment = max(dist.items(), key=lambda x: x[1])
                reasoning_parts.append(f"主要情感倾向为{main_sentiment[0]}（{main_sentiment[1]}条）。")
        
        return " ".join(reasoning_parts)
    
    def _generate_action_suggestions_with_trend(self, market_sentiment: MarketSentiment, 
                                              risk_level: RiskLevel, trend_analysis: TrendAnalysis) -> List[str]:
        """
        生成包含趋势考量的行动建议
        
        Args:
            market_sentiment: 市场情绪
            risk_level: 风险等级
            trend_analysis: 趋势分析结果
            
        Returns:
            行动建议列表
        """
        base_suggestions = self._generate_action_suggestions(market_sentiment, risk_level)
        trend_suggestions = []
        
        # 根据趋势特征添加建议
        if trend_analysis.direction in [TrendDirection.STRONG_UPWARD, TrendDirection.UPWARD]:
            if trend_analysis.strength > 0.6:
                trend_suggestions.append("趋势向上且强度较高，可考虑逐步建仓")
            if trend_analysis.momentum > 0.2:
                trend_suggestions.append("上升动量强劲，可适当关注买入机会")
        
        elif trend_analysis.direction in [TrendDirection.STRONG_DOWNWARD, TrendDirection.DOWNWARD]:
            if trend_analysis.strength > 0.6:
                trend_suggestions.append("下降趋势明确，建议谨慎或减仓")
            if trend_analysis.momentum < -0.2:
                trend_suggestions.append("下跌动量加速，需要控制风险")
        
        # 波动率相关建议
        if trend_analysis.volatility > 0.7:
            trend_suggestions.append("市场波动较大，建议分批操作")
        
        # 趋势持续性建议
        if trend_analysis.duration > 14 and trend_analysis.consistency > 0.6:
            trend_suggestions.append("趋势持续时间较长且一致性好，可考虑趋势跟随")
        elif trend_analysis.duration < 3:
            trend_suggestions.append("趋势刚刚形成，建议等待确认")
        
        return base_suggestions + trend_suggestions
    
    def _generate_action_suggestions(self, market_sentiment: MarketSentiment, 
                                   risk_level: RiskLevel) -> List[str]:
        """
        生成行动建议
        
        Args:
            market_sentiment: 市场情绪
            risk_level: 风险等级
            
        Returns:
            行动建议列表
        """
        suggestions = []
        
        # 基于市场情绪的建议
        if market_sentiment in [MarketSentiment.VERY_BULLISH, MarketSentiment.BULLISH]:
            suggestions.extend([
                "关注黄金ETF或实物黄金投资机会",
                "考虑分批建仓以降低时机风险",
                "关注美联储政策和通胀数据"
            ])
        elif market_sentiment in [MarketSentiment.BEARISH, MarketSentiment.VERY_BEARISH]:
            suggestions.extend([
                "考虑减少黄金配置或获利了结",
                "关注美元走势和实际利率变化",
                "可考虑黄金相关的看跌期权"
            ])
        else:
            suggestions.extend([
                "保持现有配置，等待明确信号",
                "密切关注市场动态和经济数据",
                "准备根据情况调整投资策略"
            ])
        
        # 基于风险等级的建议
        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            suggestions.extend([
                "设置严格的止损点",
                "控制仓位规模，避免过度集中",
                "考虑分散投资降低风险"
            ])
        
        return suggestions
    
    def _generate_risk_warnings_with_trend(self, risk_level: RiskLevel, 
                                         risk_metrics: Dict, trend_analysis: TrendAnalysis) -> List[str]:
        """
        生成包含趋势考量的风险警告
        
        Args:
            risk_level: 风险等级
            risk_metrics: 风险指标
            trend_analysis: 趋势分析结果
            
        Returns:
            风险警告列表
        """
        base_warnings = self._generate_risk_warnings(risk_level, risk_metrics)
        trend_warnings = []
        
        # 基于趋势的风险警告
        if trend_analysis.volatility > 0.8:
            trend_warnings.append("市场情感波动极大，存在急剧变化风险")
        
        if trend_analysis.consistency < 0.3:
            trend_warnings.append("趋势一致性较低，方向可能发生反转")
        
        if abs(trend_analysis.momentum) > 0.5:
            trend_warnings.append("市场动量过强，可能存在过度反应风险")
        
        if trend_analysis.duration > 30:
            trend_warnings.append("趋势持续时间较长，需警惕反转风险")
        
        if trend_analysis.strength < 0.2 and trend_analysis.volatility > 0.6:
            trend_warnings.append("趋势不明确且波动较大，投资风险较高")
        
        return base_warnings + trend_warnings
    
    def _generate_risk_warnings(self, risk_level: RiskLevel, 
                              risk_metrics: Dict) -> List[str]:
        """
        生成风险警告
        
        Args:
            risk_level: 风险等级
            risk_metrics: 风险指标
            
        Returns:
            风险警告列表
        """
        warnings = []
        
        # 通用风险警告
        warnings.append("黄金价格受多种因素影响，投资需谨慎")
        
        # 基于风险等级的警告
        if risk_level == RiskLevel.VERY_HIGH:
            warnings.extend([
                "当前市场风险极高，建议避免大额投资",
                "市场波动性较大，可能出现急剧变化"
            ])
        elif risk_level == RiskLevel.HIGH:
            warnings.extend([
                "当前市场风险较高，建议控制仓位",
                "注意市场情绪变化，及时调整策略"
            ])
        
        # 基于具体风险指标的警告
        if risk_metrics.get('confidence_risk', 0) > 0.5:
            warnings.append("分析置信度较低，建议谨慎参考")
        
        if risk_metrics.get('consistency_risk', 0) > 0.6:
            warnings.append("市场情绪分歧较大，存在不确定性")
        
        if risk_metrics.get('news_count', 0) < 5:
            warnings.append("数据样本较少，分析结果可能不够全面")
        
        return warnings
    
    def _determine_time_horizon_with_trend(self, market_sentiment: MarketSentiment, 
                                         risk_level: RiskLevel, trend_analysis: TrendAnalysis) -> str:
        """
        确定包含趋势考量的投资时间范围
        
        Args:
            market_sentiment: 市场情绪
            risk_level: 风险等级
            trend_analysis: 趋势分析结果
            
        Returns:
            时间范围建议
        """
        base_horizon = self._determine_time_horizon(market_sentiment, risk_level)
        
        # 根据趋势调整时间范围
        if trend_analysis.strength > 0.7 and trend_analysis.consistency > 0.6:
            # 强趋势可以考虑稍长时间
            if "短期" in base_horizon:
                return base_horizon.replace("短期", "中短期")
            elif "中期" in base_horizon:
                return base_horizon.replace("中期", "中长期")
        
        elif trend_analysis.volatility > 0.8:
            # 高波动建议缩短时间
            if "中期" in base_horizon:
                return base_horizon.replace("中期", "短期")
            elif "中长期" in base_horizon:
                return base_horizon.replace("中长期", "中期")
        
        return base_horizon
    
    def _determine_time_horizon(self, market_sentiment: MarketSentiment, 
                              risk_level: RiskLevel) -> str:
        """
        确定投资时间范围
        
        Args:
            market_sentiment: 市场情绪
            risk_level: 风险等级
            
        Returns:
            时间范围建议
        """
        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            return "短期（1-4周）"
        elif market_sentiment in [MarketSentiment.VERY_BULLISH, MarketSentiment.VERY_BEARISH]:
            return "中短期（1-3个月）"
        else:
            return "中期（3-6个月）"
    
    def _suggest_position_sizing_with_trend(self, market_sentiment: MarketSentiment, 
                                          risk_level: RiskLevel, trend_analysis: TrendAnalysis) -> str:
        """
        建议包含趋势考量的仓位规模
        
        Args:
            market_sentiment: 市场情绪
            risk_level: 风险等级
            trend_analysis: 趋势分析结果
            
        Returns:
            仓位建议
        """
        base_sizing = self._suggest_position_sizing(market_sentiment, risk_level)
        
        # 根据趋势调整仓位
        if trend_analysis.strength > 0.7 and trend_analysis.consistency > 0.6 and trend_analysis.volatility < 0.5:
            # 强趋势、高一致性、低波动 - 可以适当增加仓位
            if "极小" in base_sizing:
                return base_sizing.replace("极小", "小")
            elif "小" in base_sizing:
                return base_sizing.replace("小", "中等")
        
        elif trend_analysis.volatility > 0.8 or trend_analysis.consistency < 0.3:
            # 高波动或低一致性 - 减少仓位
            if "中等" in base_sizing:
                return base_sizing.replace("中等", "小")
            elif "适中" in base_sizing:
                return base_sizing.replace("适中", "小")
        
        return base_sizing
    
    def _suggest_position_sizing(self, market_sentiment: MarketSentiment, 
                               risk_level: RiskLevel) -> str:
        """
        建议仓位规模
        
        Args:
            market_sentiment: 市场情绪
            risk_level: 风险等级
            
        Returns:
            仓位建议
        """
        if risk_level == RiskLevel.VERY_HIGH:
            return "极小仓位（<5%）"
        elif risk_level == RiskLevel.HIGH:
            return "小仓位（5-10%）"
        elif market_sentiment in [MarketSentiment.VERY_BULLISH, MarketSentiment.VERY_BEARISH]:
            return "中等仓位（10-20%）"
        else:
            return "适中仓位（15-25%）"
    
    def _create_default_advice(self) -> InvestmentAdvice:
        """
        创建默认投资建议（当没有数据时）
        
        Returns:
            默认投资建议
        """
        default_trend = self._create_default_trend()
        
        return InvestmentAdvice(
            market_sentiment=MarketSentiment.NEUTRAL,
            risk_level=RiskLevel.HIGH,
            confidence_score=0.0,
            recommendation="数据不足，建议观望",
            reasoning="缺乏足够的市场数据进行分析",
            action_suggestions=["等待更多市场数据", "关注市场动态", "保持谨慎态度"],
            risk_warnings=["数据不足可能导致分析偏差", "建议等待更多信息后再做决策"],
            time_horizon="待定",
            position_sizing="暂不建议投资",
            trend_analysis=default_trend,
            trend_impact="数据不足，无法进行趋势分析"
        )
    
    def get_market_summary(self, sentiment_data: List[Dict]) -> Dict:
        """
        获取市场情况汇总
        
        Args:
            sentiment_data: 情感分析数据列表
            
        Returns:
            市场汇总信息
        """
        if not sentiment_data:
            return {
                'total_news': 0,
                'market_sentiment': MarketSentiment.NEUTRAL.value,
                'risk_level': RiskLevel.HIGH.value,
                'confidence': 0.0,
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        # 生成投资建议
        advice = self.generate_investment_advice(sentiment_data)
        
        # 计算统计信息
        scores = []
        for item in sentiment_data:
            sentiment_analysis = item.get('sentiment_analysis', {})
            if sentiment_analysis:
                scores.append(sentiment_analysis.get('score', 0.0))
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            'total_news': len(sentiment_data),
            'market_sentiment': advice.market_sentiment.value,
            'risk_level': advice.risk_level.value,
            'confidence': advice.confidence_score,
            'average_sentiment_score': round(avg_score, 3),
            'recommendation': advice.recommendation,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

# 测试函数
def test_investment_advisor():
    """
    测试投资建议引擎
    """
    advisor = InvestmentAdvisor()
    
    # 测试数据
    test_data = [
        {
            'sentiment_analysis': {
                'sentiment': 'positive',
                'score': 0.7,
                'confidence': 0.8,
                'keywords': ['上涨', '利好']
            }
        },
        {
            'sentiment_analysis': {
                'sentiment': 'positive',
                'score': 0.5,
                'confidence': 0.7,
                'keywords': ['增长', '乐观']
            }
        },
        {
            'sentiment_analysis': {
                'sentiment': 'neutral',
                'score': 0.1,
                'confidence': 0.6,
                'keywords': ['稳定', '观望']
            }
        }
    ]
    
    print("=== 投资建议引擎测试 ===")
    
    # 生成投资建议
    advice = advisor.generate_investment_advice(test_data)
    
    print(f"市场情绪: {advice.market_sentiment.value}")
    print(f"风险等级: {advice.risk_level.value}")
    print(f"置信度: {advice.confidence_score:.3f}")
    print(f"投资建议: {advice.recommendation}")
    print(f"分析理由: {advice.reasoning}")
    print(f"时间范围: {advice.time_horizon}")
    print(f"仓位建议: {advice.position_sizing}")
    
    print("\n行动建议:")
    for suggestion in advice.action_suggestions:
        print(f"  - {suggestion}")
    
    print("\n风险警告:")
    for warning in advice.risk_warnings:
        print(f"  - {warning}")
    
    # 市场汇总
    print("\n=== 市场汇总 ===")
    summary = advisor.get_market_summary(test_data)
    for key, value in summary.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    test_investment_advisor()