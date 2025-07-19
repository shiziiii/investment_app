import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime, timedelta
import sys
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']	# 显示中文
plt.rcParams['axes.unicode_minus'] = False		# 显示负号

from data_visualizer import DataVisualizer

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sentiment_analyzer import SentimentAnalyzer
from investment_advisor import InvestmentAdvisor
from utils import load_json_data, get_file_list
from config import Config
from gold_price_fetcher import GoldPriceFetcher, GoldPriceData

# 页面配置
st.set_page_config(
    page_title="黄金投资情感分析系统",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #ff6b6b;
}
.positive { border-left-color: #51cf66 !important; }
.negative { border-left-color: #ff6b6b !important; }
.neutral { border-left-color: #74c0fc !important; }
</style>
""", unsafe_allow_html=True)

def load_latest_analysis_results():
    """加载最新的分析结果"""
    try:
        # 查找最新的分析结果文件
        result_files = get_file_list('.', '.json')
        analysis_files = [f for f in result_files if 'sentiment_analysis_results_' in os.path.basename(f)]
        
        if not analysis_files:
            return None
        
        # 按文件名排序，获取最新的
        analysis_files.sort(reverse=True)
        latest_file = analysis_files[0]
        
        return load_json_data(latest_file)
    except Exception as e:
        st.error(f"加载分析结果失败: {e}")
        return None

def load_news_data():
    """加载新闻数据"""
    try:
        # 查找gold_news_data目录
        data_dir = os.path.join(os.getcwd(), 'gold_news_data')
        if os.path.exists(data_dir):
            news_files = [f for f in os.listdir(data_dir) if f.startswith('gold_news_') and f.endswith('.json')]
            if news_files:
                news_files.sort(reverse=True)
                file_path = os.path.join(data_dir, news_files[0])
                return load_json_data(file_path)
        
        # 检查当前目录
        news_files = get_file_list('.', '.json')
        gold_news_files = [f for f in news_files if 'gold_news_' in os.path.basename(f)]
        
        if gold_news_files:
            return load_json_data(gold_news_files[0])
        
        return None
    except Exception as e:
        st.error(f"加载新闻数据失败: {e}")
        return None

# 移除原有的create_sentiment_distribution_chart函数，使用DataVisualizer类

# 移除原有的create_sentiment_timeline函数，使用DataVisualizer类

def display_news_analysis(data, limit=5):
    """显示新闻分析详情"""
    if not data:
        st.warning("没有找到分析数据")
        return
    
    st.subheader(f"📰 最新 {limit} 条新闻分析")
    
    for i, item in enumerate(data[:limit]):
        sentiment_analysis = item.get('sentiment_analysis', {})
        sentiment = sentiment_analysis.get('sentiment', 'neutral')
        score = sentiment_analysis.get('score', 0)
        confidence = sentiment_analysis.get('confidence', 0)
        keywords = sentiment_analysis.get('keywords', [])
        reasoning = sentiment_analysis.get('reasoning', '')
        
        # 情感颜色映射
        sentiment_colors = {
            'positive': '🟢',
            'negative': '🔴', 
            'neutral': '🟡'
        }
        
        sentiment_labels = {
            'positive': '积极',
            'negative': '消极',
            'neutral': '中性'
        }
        
        with st.expander(f"{sentiment_colors.get(sentiment, '🟡')} {item.get('title', '无标题')}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("情感倾向", sentiment_labels.get(sentiment, '中性'))
            
            with col2:
                st.metric("情感分值", f"{score:.3f}")
            
            with col3:
                st.metric("置信度", f"{confidence:.3f}")
            
            if keywords:
                st.write("**关键词:**", ", ".join(keywords))
            
            if reasoning:
                st.write("**分析理由:**")
                st.write(reasoning)
            
            st.write("**发布时间:**", item.get('publish_time', '未知'))
            st.write("**来源:**", item.get('author', '未知'))

def display_gold_price_section():
    """显示金价模块"""
    st.subheader("💰 实时金价")
    
    # 创建金价获取器
    fetcher = GoldPriceFetcher()
    
    # 获取当前金价
    with st.spinner("正在获取实时金价..."):
        current_price = fetcher.get_current_gold_price()
    
    if current_price:
        # 显示当前金价
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            price_color = "🟢" if current_price.change_24h >= 0 else "🔴"
            st.metric(
                "美元金价",
                f"${current_price.price_usd:.2f}",
                f"{current_price.change_24h:+.2f}",
                help="每盎司黄金的美元价格"
            )
        
        with col2:
            st.metric(
                "人民币金价", 
                f"¥{current_price.price_cny:.2f}",
                f"{current_price.change_24h * 7.2:+.2f}",
                help="每盎司黄金的人民币价格"
            )
        
        with col3:
            change_color = "🟢" if current_price.change_percent_24h >= 0 else "🔴"
            st.metric(
                "24小时涨跌幅",
                f"{change_color} {current_price.change_percent_24h:+.2f}%",
                help="24小时内的价格变化百分比"
            )
        
        with col4:
            st.metric(
                "数据源",
                current_price.source,
                help="金价数据来源"
            )
        
        # 显示更新时间
        st.caption(f"📅 最后更新: {current_price.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
    else:
        st.error("⚠️ 无法获取实时金价数据，请稍后重试")
        return
    
    st.markdown("---")
    
    # 历史金价部分
    st.subheader("📈 历史金价走势")
    
    # 时间范围选择
    col1, col2 = st.columns([3, 1])
    
    with col1:
        time_range = st.selectbox(
            "选择时间范围",
            options=[7, 15, 30, 60, 90],
            format_func=lambda x: f"最近 {x} 天",
            index=2,  # 默认选择30天
            help="选择要显示的历史数据时间范围"
        )
    
    with col2:
        if st.button("🔄 刷新数据", help="重新获取最新的金价数据"):
            st.rerun()
    
    # 获取历史数据
    with st.spinner(f"正在获取最近 {time_range} 天的历史数据..."):
        historical_data = fetcher.get_historical_prices(time_range)
    
    if historical_data:
        # 创建历史价格图表
        create_gold_price_charts(historical_data, current_price)
        
        # 显示价格统计
        display_price_statistics(fetcher, historical_data)
        
    else:
        st.warning("⚠️ 无法获取历史金价数据")

def create_gold_price_charts(historical_data, current_price):
    """创建金价图表"""
    # 准备数据
    df = pd.DataFrame([
        {
            'date': data.timestamp,
            'price_usd': data.price_usd,
            'price_cny': data.price_cny,
            'change_percent': data.change_percent_24h
        }
        for data in historical_data
    ])
    
    # 创建双轴图表
    col1, col2 = st.columns(2)
    
    with col1:
        # 美元价格走势
        fig_usd = go.Figure()
        
        fig_usd.add_trace(go.Scatter(
            x=df['date'],
            y=df['price_usd'],
            mode='lines+markers',
            name='美元金价',
            line=dict(color='#FFD700', width=2),
            marker=dict(size=4),
            hovertemplate='<b>日期:</b> %{x}<br><b>价格:</b> $%{y:.2f}<extra></extra>'
        ))
        
        # 添加当前价格线
        if current_price:
            fig_usd.add_hline(
                y=current_price.price_usd,
                line_dash="dash",
                line_color="red",
                annotation_text=f"当前价格: ${current_price.price_usd:.2f}"
            )
        
        fig_usd.update_layout(
            title="💵 美元金价走势",
            xaxis_title="日期",
            yaxis_title="价格 (USD/盎司)",
            height=400,
            showlegend=True,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_usd, use_container_width=True)
    
    with col2:
        # 人民币价格走势
        fig_cny = go.Figure()
        
        fig_cny.add_trace(go.Scatter(
            x=df['date'],
            y=df['price_cny'],
            mode='lines+markers',
            name='人民币金价',
            line=dict(color='#FF6B6B', width=2),
            marker=dict(size=4),
            hovertemplate='<b>日期:</b> %{x}<br><b>价格:</b> ¥%{y:.2f}<extra></extra>'
        ))
        
        # 添加当前价格线
        if current_price:
            fig_cny.add_hline(
                y=current_price.price_cny,
                line_dash="dash",
                line_color="red",
                annotation_text=f"当前价格: ¥{current_price.price_cny:.2f}"
            )
        
        fig_cny.update_layout(
            title="💴 人民币金价走势",
            xaxis_title="日期",
            yaxis_title="价格 (CNY/盎司)",
            height=400,
            showlegend=True,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_cny, use_container_width=True)
    
    # 价格变化百分比图表
    st.subheader("📊 每日涨跌幅")
    
    fig_change = go.Figure()
    
    # 根据涨跌设置颜色
    colors = ['green' if x >= 0 else 'red' for x in df['change_percent']]
    
    fig_change.add_trace(go.Bar(
        x=df['date'],
        y=df['change_percent'],
        name='每日涨跌幅',
        marker_color=colors,
        hovertemplate='<b>日期:</b> %{x}<br><b>涨跌幅:</b> %{y:.2f}%<extra></extra>'
    ))
    
    fig_change.update_layout(
        title="📈 每日涨跌幅分布",
        xaxis_title="日期",
        yaxis_title="涨跌幅 (%)",
        height=300,
        showlegend=False,
        hovermode='x unified'
    )
    
    # 添加零线
    fig_change.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    st.plotly_chart(fig_change, use_container_width=True)

def display_price_statistics(fetcher, historical_data):
    """显示价格统计信息"""
    st.subheader("📊 价格统计分析")
    
    # 计算统计信息
    stats = fetcher.get_price_statistics(historical_data)
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "最高价",
                f"${stats['highest_price']:.2f}",
                help="统计期间内的最高价格"
            )
        
        with col2:
            st.metric(
                "最低价",
                f"${stats['lowest_price']:.2f}",
                help="统计期间内的最低价格"
            )
        
        with col3:
            st.metric(
                "平均价",
                f"${stats['average_price']:.2f}",
                help="统计期间内的平均价格"
            )
        
        with col4:
            st.metric(
                "价格区间",
                f"${stats['price_range']:.2f}",
                help="最高价与最低价的差值"
            )
        
        # 第二行统计
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            volatility_color = "🟢" if stats['volatility'] < 50 else "🟡" if stats['volatility'] < 100 else "🔴"
            st.metric(
                "波动率",
                f"{volatility_color} {stats['volatility']:.2f}",
                help="价格波动的标准差，数值越大表示波动越大"
            )
        
        with col6:
            trend_emoji = {
                "上升趋势": "📈",
                "下降趋势": "📉",
                "横盘整理": "➡️",
                "无趋势": "❓"
            }
            emoji = trend_emoji.get(stats['trend'], "❓")
            st.metric(
                "价格趋势",
                f"{emoji} {stats['trend']}",
                help="基于历史数据分析的价格趋势"
            )
        
        with col7:
            # 计算涨跌天数
            up_days = sum(1 for data in historical_data if data.change_percent_24h > 0)
            down_days = sum(1 for data in historical_data if data.change_percent_24h < 0)
            st.metric(
                "上涨天数",
                f"📈 {up_days}天",
                help="统计期间内价格上涨的天数"
            )
        
        with col8:
            st.metric(
                "下跌天数",
                f"📉 {down_days}天",
                help="统计期间内价格下跌的天数"
            )

def main():
    """主函数"""
    st.title("🏆 黄金投资情感分析系统")
    st.markdown("---")
    
    # 侧边栏配置
    with st.sidebar:
        st.header("📊 控制面板")
        
        # 功能选择
        st.subheader("🎯 功能选择")
        page_option = st.selectbox(
            "选择功能",
            options=["📰 新闻分析", "💰 金价监控"],
            help="选择要使用的功能模块"
        )
        
        # 刷新数据按钮
        if st.button("🔄 刷新数据", help="重新获取最新数据"):
            st.rerun()
        
        st.markdown("---")
        
        if page_option == "💰 金价监控":
            # 金价监控设置
            st.subheader("⚙️ 金价设置")
            st.info("💡 实时金价数据来源于多个API")
            st.info("📊 历史数据基于模拟生成")
            
            # 金价提醒设置
            st.write("价格提醒")
            enable_alerts = st.checkbox("启用价格提醒", help="当金价达到设定值时提醒")
            
            if enable_alerts:
                alert_price = st.number_input(
                    "提醒价格 (USD)",
                    min_value=1000.0,
                    max_value=5000.0,
                    value=2000.0,
                    step=10.0,
                    help="当金价达到此价格时显示提醒"
                )
                
                # 存储提醒设置到session state
                st.session_state['price_alert'] = {
                    'enabled': enable_alerts,
                    'price': alert_price
                }
    
    # 根据选择的功能显示不同内容
    if page_option == "💰 金价监控":
        # 显示金价模块
        display_gold_price_section()
        return
    
    # 新闻分析模块
    # 加载数据
    analysis_data = load_latest_analysis_results()
    
    # 获取新闻总数用于动态设置滑块最大值
    total_news_count = len(analysis_data) if analysis_data else 20
    max_display_limit = min(max(total_news_count, 5), 100)  # 最小5，最大100
    
    # 继续侧边栏配置（新闻分析部分）
    with st.sidebar:
        if page_option == "📰 新闻分析":
            # 分析设置
            st.subheader("🔧 分析设置")
        
        # 显示新闻总数信息
        if analysis_data:
            st.info(f"📊 当前共有 {total_news_count} 条新闻数据")
        
        # 筛选模式选择
        filter_mode = st.radio(
            "筛选模式",
            ["按数量筛选", "按日期筛选"],
            help="选择新闻筛选方式"
        )
        
        # 根据筛选模式显示不同的控件
        if filter_mode == "按数量筛选":
            # 动态设置滑块最大值
            default_limit = min(5, total_news_count)
            show_limit = st.slider(
                "显示新闻数量", 
                1, 
                max_display_limit, 
                default_limit,
                help=f"可显示范围：1-{max_display_limit} 条新闻"
            )
            # 按数量筛选数据
            filtered_data = analysis_data[:show_limit] if analysis_data else []
            st.info(f"📊 显示前 {len(filtered_data)} 条新闻")
        else:
            # 按日期筛选
            if analysis_data:
                # 获取新闻日期范围
                dates = []
                for item in analysis_data:
                    time_str = item.get('time') or item.get('publish_time', '')
                    if time_str:
                        try:
                            # 处理不同的时间格式
                            if len(time_str) >= 10:
                                date_str = time_str[:10]  # 取前10个字符作为日期
                                dates.append(datetime.strptime(date_str, '%Y-%m-%d').date())
                        except:
                            continue
                
                if dates:
                    min_date = min(dates)
                    max_date = max(dates)
                    
                    # 日期范围选择
                    date_range = st.slider(
                        "选择日期范围（天数）",
                        min_value=1,
                        max_value=(max_date - min_date).days + 1,
                        value=min(7, (max_date - min_date).days + 1),
                        help=f"从最新日期({max_date})往前推的天数"
                    )
                    
                    # 计算筛选的起始日期
                    start_date = max_date - timedelta(days=date_range - 1)
                    
                    st.info(f"📅 筛选日期范围：{start_date} 至 {max_date}")
                    
                    # 按日期筛选数据
                    filtered_data = []
                    for item in analysis_data:
                        time_str = item.get('time') or item.get('publish_time', '')
                        if time_str:
                            try:
                                if len(time_str) >= 10:
                                    date_str = time_str[:10]
                                    item_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                                    if start_date <= item_date <= max_date:
                                        filtered_data.append(item)
                            except:
                                continue
                    
                    show_limit = len(filtered_data)
                    st.info(f"📊 筛选后共有 {show_limit} 条新闻")
                else:
                    st.warning("无法解析新闻日期信息")
                    filtered_data = analysis_data
                    show_limit = min(5, total_news_count)
            else:
                filtered_data = []
                show_limit = 0
        
        st.markdown("---")
        

    
    if not analysis_data:
        st.warning("⚠️ 没有找到分析结果，请先运行情感分析。")
        
        # 提供运行分析的选项
        if st.button("🚀 立即运行情感分析"):
            with st.spinner("正在分析新闻情感..."):
                try:
                    # 运行分析
                    os.system("python demo_sentiment_analysis.py")
                    st.success("✅ 分析完成！请刷新页面查看结果。")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 分析失败: {e}")
        return
    
    # 显示概览统计
    st.subheader("📈 情感分析概览")
    
    # 图表区域
    visualizer = DataVisualizer()
    
    # 获取汇总指标
    metrics = visualizer.create_summary_metrics(filtered_data)
    
    # 显示关键指标
    if metrics:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📰 总新闻数", metrics['total_news'])
        with col2:
            st.metric("📊 平均情感分值", f"{metrics['avg_score']:.3f}")
        with col3:
            st.metric("🎯 平均置信度", f"{metrics['avg_confidence']:.3f}")
        with col4:
            st.metric("🌡️ 市场情绪", metrics['market_mood'])
    
    # 主要图表区域
    st.subheader("📊 核心分析图表")
    col1, col2 = st.columns(2)
    
    with col1:
        # 情感分布图
        sentiment_chart = visualizer.plot_sentiment_distribution(filtered_data)
        if sentiment_chart:
            st.plotly_chart(sentiment_chart, use_container_width=True)
    
    with col2:
        # 情感时间线
        timeline_chart = visualizer.plot_sentiment_timeline(filtered_data)
        if timeline_chart:
            st.plotly_chart(timeline_chart, use_container_width=True)
    
    st.markdown("---")
    
    # 投资建议模块
    st.subheader("💡 智能投资建议")
    
    try:
        # 初始化投资建议引擎
        advisor = InvestmentAdvisor()
        
        # 生成投资建议
        investment_advice = advisor.generate_investment_advice(filtered_data)
        
        # 显示市场汇总
        market_summary = advisor.get_market_summary(filtered_data)
        
        # 建议概览
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sentiment_emoji = {
                "强烈看涨": "🚀",
                "温和看涨": "📈", 
                "中性观望": "⚖️",
                "温和看跌": "📉",
                "强烈看跌": "⬇️"
            }
            emoji = sentiment_emoji.get(investment_advice.market_sentiment.value, "⚖️")
            st.metric(
                "市场情绪", 
                f"{emoji} {investment_advice.market_sentiment.value}",
                help="基于新闻情感分析得出的市场整体情绪"
            )
        
        with col2:
            risk_emoji = {
                "低风险": "🟢",
                "中等风险": "🟡",
                "高风险": "🟠", 
                "极高风险": "🔴"
            }
            emoji = risk_emoji.get(investment_advice.risk_level.value, "🟡")
            st.metric(
                "风险等级",
                f"{emoji} {investment_advice.risk_level.value}",
                help="综合评估的当前投资风险等级"
            )
        
        with col3:
            confidence_color = "🟢" if investment_advice.confidence_score > 0.7 else "🟡" if investment_advice.confidence_score > 0.4 else "🔴"
            st.metric(
                "建议置信度",
                f"{confidence_color} {investment_advice.confidence_score:.1%}",
                help="对当前投资建议的置信程度"
            )
        
        st.markdown("---")
        
        # 趋势分析概览
        st.markdown("### 📈 趋势分析")
        
        trend_col1, trend_col2, trend_col3, trend_col4 = st.columns(4)
        
        with trend_col1:
            direction_emoji = {
                "强烈上升": "🚀",
                "温和上升": "📈",
                "横盘整理": "➡️",
                "温和下降": "📉",
                "强烈下降": "⬇️"
            }
            emoji = direction_emoji.get(investment_advice.trend_analysis.direction.value, "➡️")
            st.metric(
                "趋势方向",
                f"{emoji} {investment_advice.trend_analysis.direction.value}",
                help="基于时间序列分析的市场情感趋势方向"
            )
        
        with trend_col2:
            strength_color = "🟢" if investment_advice.trend_analysis.strength > 0.7 else "🟡" if investment_advice.trend_analysis.strength > 0.4 else "🔴"
            st.metric(
                "趋势强度",
                f"{strength_color} {investment_advice.trend_analysis.strength:.2f}",
                help="趋势的强度和可靠性（0-1）"
            )
        
        with trend_col3:
            st.metric(
                "持续天数",
                f"📅 {investment_advice.trend_analysis.duration}天",
                help="当前趋势已持续的天数"
            )
        
        with trend_col4:
            momentum_emoji = "⬆️" if investment_advice.trend_analysis.momentum > 0.1 else "⬇️" if investment_advice.trend_analysis.momentum < -0.1 else "➡️"
            st.metric(
                "市场动量",
                f"{momentum_emoji} {investment_advice.trend_analysis.momentum:.2f}",
                help="市场动量指标（-1到1）"
            )
        
        # 趋势详细信息
        with st.expander("📊 趋势分析详情"):
            trend_detail_col1, trend_detail_col2 = st.columns(2)
            
            with trend_detail_col1:
                st.metric("波动率", f"{investment_advice.trend_analysis.volatility:.2f}", help="市场情感波动程度")
                st.metric("一致性", f"{investment_advice.trend_analysis.consistency:.2f}", help="趋势方向的一致性")
            
            with trend_detail_col2:
                st.metric("近期变化", f"{investment_advice.trend_analysis.recent_change:.2f}", help="最近几天的变化率")
                st.write(f"**趋势影响:** {investment_advice.trend_impact}")
        
        st.markdown("---")
        
        # 主要建议
        st.markdown("### 📋 投资建议详情")
        
        # 建议内容
        st.info(f"**💼 投资建议:** {investment_advice.recommendation}")
        
        # 分析理由
        with st.expander("📊 分析理由", expanded=True):
            st.write(investment_advice.reasoning)
        
        # 行动建议和风险警告
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ✅ 行动建议")
            for i, suggestion in enumerate(investment_advice.action_suggestions, 1):
                st.write(f"{i}. {suggestion}")
        
        with col2:
            st.markdown("#### ⚠️ 风险警告")
            for i, warning in enumerate(investment_advice.risk_warnings, 1):
                st.write(f"{i}. {warning}")
        
        # 投资参数建议
        st.markdown("### ⚙️ 投资参数建议")
        
        param_col1, param_col2 = st.columns(2)
        
        with param_col1:
            st.metric(
                "建议时间范围",
                investment_advice.time_horizon,
                help="基于当前市场情况建议的投资持有时间"
            )
        
        with param_col2:
            st.metric(
                "建议仓位规模", 
                investment_advice.position_sizing,
                help="建议的黄金投资在总投资组合中的占比"
            )
        
        # 市场数据概览
        with st.expander("📈 市场数据概览"):
            st.json({
                "分析新闻总数": market_summary['total_news'],
                "平均情感分值": market_summary['average_sentiment_score'],
                "最后更新时间": market_summary['last_update']
            })
        
    except Exception as e:
        st.error(f"生成投资建议时出错: {str(e)}")
        st.info("请确保有足够的情感分析数据来生成投资建议。")
    
    st.markdown("---")
    
    # 详细分析
    display_news_analysis(filtered_data, show_limit)
    
    # 页脚
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"  
        "🏆 黄金投资情感分析系统 | 基于大语言模型的智能分析"  
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()