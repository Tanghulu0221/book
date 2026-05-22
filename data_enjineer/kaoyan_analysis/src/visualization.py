"""
可视化模块 - 生成论文所需图表（强制中文显示）
"""
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm   # 关键：导入 font_manager 并命名为 fm
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')

# ---------- 强制加载中文字体（直接指定字体文件）----------
font_path = '/home/wangkun/.local/share/fonts/SimHei.ttf'

# 备选字体路径（如果上面不存在，尝试系统其他常见路径）
fallback_paths = [
    '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
    '/System/Library/Fonts/PingFang.ttc',          # macOS
    'C:/Windows/Fonts/simhei.ttf'                 # Windows
]

if not os.path.exists(font_path):
    for path in fallback_paths:
        if os.path.exists(path):
            font_path = path
            break

if os.path.exists(font_path):
    chinese_font = fm.FontProperties(fname=font_path)
    print(f"✅ 成功加载中文字体: {font_path}")
else:
    # 如果都不存在，尝试使用系统名称（可能失败）
    chinese_font = fm.FontProperties()
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'SimHei']
    print("⚠️ 未找到字体文件，将尝试使用系统字体名称")

plt.rcParams['axes.unicode_minus'] = False
# --------------------------------------------------------

# 设置绘图风格
sns.set_style("whitegrid")
sns.set_palette("husl")


class ScoreVisualizer:
    """考研分数可视化器"""
    
    def __init__(self, data_path='data/processed/scores_cleaned.csv'):
        # 处理路径
        if not os.path.isabs(data_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, data_path)
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"数据文件不存在: {data_path}")
        self.df = pd.read_csv(data_path, encoding='utf-8-sig')
        
        # 检查必要列
        required = ['年份', '总分要求', '学科门类', '城市', '是否一线城市', '拟招生人数', '学校名称']
        missing = [c for c in required if c not in self.df.columns]
        if missing:
            raise ValueError(f"缺少列: {missing}")
        
        # 输出目录绝对路径
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir = os.path.join(base_dir, 'output', 'figures')
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"图片将保存到: {self.output_dir}")
        
        # 保存中文字体对象
        self.chinese_font = chinese_font
        
        # 强制 matplotlib 全局字体（确保所有绘图元素使用中文）
        plt.rcParams['font.sans-serif'] = [self.chinese_font.get_name()]
        plt.rcParams['axes.unicode_minus'] = False
        
        # 重新应用 seaborn 样式（保持美观，但字体已被强制）
        sns.set_style("whitegrid")
        sns.set_palette("husl")
        
    def _set_labels(self, ax, title=None, xlabel=None, ylabel=None):
        """内部辅助函数：设置中文标题和轴标签"""
        if title:
            ax.set_title(title, fontproperties=self.chinese_font, fontsize=13, fontweight='bold')
        if xlabel:
            ax.set_xlabel(xlabel, fontproperties=self.chinese_font, fontsize=12)
        if ylabel:
            ax.set_ylabel(ylabel, fontproperties=self.chinese_font, fontsize=12)
    
    def plot1_time_trend(self):
        """
        图1: 历年复试分数线趋势图
        对应RQ1: 时间维度分析
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # 子图1: 年度均值趋势线
        ax1 = axes[0]
        yearly_avg = self.df.groupby('年份')['总分要求'].mean()
        yearly_std = self.df.groupby('年份')['总分要求'].std()
        years = yearly_avg.index
        
        # 绘制均值线
        ax1.plot(years, yearly_avg, 'o-', color='#2196F3', linewidth=2.5, 
                markersize=8, label='平均分数线', zorder=5)
        # 添加标准差阴影
        ax1.fill_between(years, yearly_avg - yearly_std, yearly_avg + yearly_std, 
                         alpha=0.2, color='#2196F3', label='±1标准差')
        # 趋势线
        z = np.polyfit(years, yearly_avg, 1)
        trend = np.poly1d(z)
        ax1.plot(years, trend(years), '--', color='#FF5722', linewidth=1.5, 
                 alpha=0.7, label=f'趋势线 (斜率={z[0]:.1f})')
        
        self._set_labels(ax1, title='34所自划线高校复试分数线趋势\n(2018-2025)', 
                         xlabel='年份', ylabel='复试分数线 (分)')
        ax1.legend(prop=self.chinese_font, loc='upper left')
        ax1.set_xticks(years)
        ax1.grid(True, alpha=0.3)
        
        # 标注"峰值"
        for i in range(1, len(yearly_avg) - 1):
            if yearly_avg.iloc[i] > yearly_avg.iloc[i-1] and yearly_avg.iloc[i] > yearly_avg.iloc[i+1]:
                ax1.annotate('峰值', (years[i], yearly_avg.iloc[i]), 
                             xytext=(0, 10), textcoords='offset points',
                             fontsize=9, color='red', ha='center',
                             fontproperties=self.chinese_font)
        
        # 子图2: 箱线图
        ax2 = axes[1]
        yearly_data = [self.df[self.df['年份'] == y]['总分要求'].values for y in years]
        bp = ax2.boxplot(yearly_data, labels=years, patch_artist=True, showfliers=False)
        colors = plt.cm.Blues(np.linspace(0.3, 0.9, len(years)))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
        
        self._set_labels(ax2, title='各年度分数线分布', xlabel='年份', ylabel='复试分数线 (分)')
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, 'fig1_time_trend.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"图1已保存: {filepath}")
        
    def plot2_subject_comparison(self):
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
        # 子图1: 学科箱线图
        ax1 = axes[0]
        subject_order = self.df.groupby('学科门类')['总分要求'].median().sort_values(ascending=False).index
        sns.boxplot(data=self.df, x='学科门类', y='总分要求', order=subject_order, ax=ax1,
                    palette='RdYlBu_r', width=0.6, showfliers=False)
    
        # 设置中文标题和标签（使用辅助函数）
        self._set_labels(ax1, title='不同学科门类复试分数线分布', 
                        xlabel='学科门类', ylabel='复试分数线 (分)')
        # 关键：设置 x 轴刻度标签字体
        ax1.set_xticklabels(ax1.get_xticklabels(), fontproperties=self.chinese_font, rotation=45)
        ax1.grid(True, alpha=0.3, axis='y')
    
        # 添加均值标注（散点标记）
        for i, subject in enumerate(subject_order):
            mean_val = self.df[self.df['学科门类'] == subject]['总分要求'].mean()
            ax1.scatter(i, mean_val, color='red', s=50, zorder=10, marker='D')
            # 可选：添加数值文本
            ax1.text(i, mean_val + 1, f'{mean_val:.0f}', ha='center', va='bottom',
                    fontsize=8, fontproperties=self.chinese_font)
    
        # 子图2: 学科涨幅排名
        ax2 = axes[1]
        growth_data = []
        for subject in self.df['学科门类'].unique():
            sub_df = self.df[self.df['学科门类'] == subject]
            scores_by_year = sub_df.groupby('年份')['总分要求'].mean()
            if len(scores_by_year) >= 2:
                growth = scores_by_year.iloc[-1] - scores_by_year.iloc[0]
                growth_data.append({'学科门类': subject, '涨幅(分)': growth})
        growth_df = pd.DataFrame(growth_data).sort_values('涨幅(分)', ascending=True)
        colors_bar = ['#4CAF50' if x > 0 else '#F44336' for x in growth_df['涨幅(分)']]
        bars = ax2.barh(growth_df['学科门类'], growth_df['涨幅(分)'], color=colors_bar,
                        edgecolor='white', height=0.6)
        for bar, val in zip(bars, growth_df['涨幅(分)']):
            ax2.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    f'{val:.1f}', va='center', fontsize=10, fontproperties=self.chinese_font)
    
        self._set_labels(ax2, title='各学科门类分数线涨幅对比\n(2018 vs 2025)',
                        xlabel='分数变化 (分)', ylabel='学科门类')
        ax2.set_yticklabels(growth_df['学科门类'], fontproperties=self.chinese_font)
        ax2.axvline(x=0, color='black', linewidth=0.8, linestyle='-')
        ax2.grid(True, alpha=0.3, axis='x')
    
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, 'fig2_subject_comparison.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"图2已保存: {filepath}")

    def plot3_regional_comparison(self):
        """
        图3: 地域效应对比
        对应RQ3: 地域效应分析
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # 子图1: 一线城市 vs 非一线城市
        ax1 = axes[0]
        vp = ax1.violinplot(
            [self.df[self.df['是否一线城市'] == '一线城市']['总分要求'],
             self.df[self.df['是否一线城市'] == '非一线城市']['总分要求']],
            positions=[1, 2], showmeans=True, showmedians=True
        )
        vp['bodies'][0].set_facecolor('#FF6B6B')
        vp['bodies'][0].set_alpha(0.7)
        vp['bodies'][1].set_facecolor('#4ECDC4')
        vp['bodies'][1].set_alpha(0.7)
        
        ax1.set_xticks([1, 2])
        ax1.set_xticklabels(['一线城市', '非一线城市'], fontproperties=self.chinese_font, fontsize=12)
        self._set_labels(ax1, title='一线城市与非一线城市分数线对比', ylabel='复试分数线 (分)')
        ax1.grid(True, alpha=0.3, axis='y')
        
        tier1_mean = self.df[self.df['是否一线城市'] == '一线城市']['总分要求'].mean()
        non_tier1_mean = self.df[self.df['是否一线城市'] == '非一线城市']['总分要求'].mean()
        ax1.annotate(f'均值: {tier1_mean:.1f}', xy=(1, tier1_mean), xytext=(0, 5),
                     textcoords='offset points', fontsize=10, ha='center', fontweight='bold',
                     fontproperties=self.chinese_font)
        ax1.annotate(f'均值: {non_tier1_mean:.1f}', xy=(2, non_tier1_mean), xytext=(0, 5),
                     textcoords='offset points', fontsize=10, ha='center', fontweight='bold',
                     fontproperties=self.chinese_font)
        
        # 子图2: 各城市排名
        ax2 = axes[1]
        city_avg = self.df.groupby('城市')['总分要求'].mean().sort_values(ascending=True)
        colors = ['#FF6B6B' if c in ['北京', '上海', '广州', '深圳'] else '#4ECDC4' for c in city_avg.index]
        ax2.barh(range(len(city_avg)), city_avg.values, color=colors, edgecolor='white', height=0.7)
        ax2.set_yticks(range(len(city_avg)))
        ax2.set_yticklabels(city_avg.index, fontproperties=self.chinese_font, fontsize=10)
        self._set_labels(ax2, title='各城市高校平均分数线排名', xlabel='平均复试分数线 (分)')
        ax2.grid(True, alpha=0.3, axis='x')
        
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='#FF6B6B', label='一线城市'),
                           Patch(facecolor='#4ECDC4', label='其他城市')]
        ax2.legend(handles=legend_elements, prop=self.chinese_font, loc='lower right')
        
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, 'fig3_regional_comparison.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"图3已保存: {filepath}")
        
    
    def plot4_macro_correlation(self):
        """
        图4: 宏观经济关联分析
        对应RQ4: 外部关联分析
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        macro_data = {
            2018: [6.7, 4.9, 238], 2019: [6.0, 5.1, 290],
            2020: [2.3, 5.2, 341], 2021: [8.4, 5.1, 377],
            2022: [3.0, 5.5, 457], 2023: [5.2, 5.2, 474],
            2024: [5.0, 5.1, 438], 2025: [4.8, 5.0, 420]
        }
        yearly_avg = self.df.groupby('年份')['总分要求'].mean()
        
        # GDP增速
        ax1 = axes[0, 0]
        gdp_rates = [macro_data[y][0] for y in yearly_avg.index if y in macro_data]
        scores_for_gdp = [yearly_avg[y] for y in yearly_avg.index if y in macro_data]
        ax1.scatter(gdp_rates, scores_for_gdp, s=100, c='#2196F3', edgecolors='white', linewidth=1.5, zorder=5)
        for i, year in enumerate([y for y in yearly_avg.index if y in macro_data]):
            ax1.annotate(str(year), (gdp_rates[i], scores_for_gdp[i]), xytext=(5,5), textcoords='offset points', fontsize=9)
        z = np.polyfit(gdp_rates, scores_for_gdp, 1)
        x_fit = np.linspace(min(gdp_rates), max(gdp_rates), 100)
        ax1.plot(x_fit, np.poly1d(z)(x_fit), '--', color='red', alpha=0.5)
        self._set_labels(ax1, title='GDP增速与复试分数线关系', xlabel='GDP增速 (%)', ylabel='平均分数线 (分)')
        ax1.grid(True, alpha=0.3)
        
        # 失业率
        ax2 = axes[0, 1]
        unemp_rates = [macro_data[y][1] for y in yearly_avg.index if y in macro_data]
        ax2.scatter(unemp_rates, scores_for_gdp, s=100, c='#FF5722', edgecolors='white', linewidth=1.5, zorder=5)
        for i, year in enumerate([y for y in yearly_avg.index if y in macro_data]):
            ax2.annotate(str(year), (unemp_rates[i], scores_for_gdp[i]), xytext=(5,5), textcoords='offset points', fontsize=9)
        self._set_labels(ax2, title='失业率与复试分数线关系', xlabel='城镇调查失业率 (%)', ylabel='平均分数线 (分)')
        ax2.grid(True, alpha=0.3)
        
        # 考研报名人数
        ax3 = axes[1, 0]
        applicants = [macro_data[y][2] for y in yearly_avg.index if y in macro_data]
        ax3.scatter(applicants, scores_for_gdp, s=100, c='#4CAF50', edgecolors='white', linewidth=1.5, zorder=5)
        for i, year in enumerate([y for y in yearly_avg.index if y in macro_data]):
            ax3.annotate(str(year), (applicants[i], scores_for_gdp[i]), xytext=(5,5), textcoords='offset points', fontsize=9)
        self._set_labels(ax3, title='考研报名人数与复试分数线关系', xlabel='考研报名人数 (万人)', ylabel='平均分数线 (分)')
        ax3.grid(True, alpha=0.3)
        
        # 相关性热力图
        ax4 = axes[1, 1]
        corr_data = pd.DataFrame({
            '平均分数线': scores_for_gdp,
            'GDP增速': gdp_rates,
            '失业率': unemp_rates,
            '考研报名人数': applicants
        })
        corr_matrix = corr_data.corr()
        # 绘制热力图，并获取 colorbar 对象
        hm = sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
                        square=True, linewidths=0.5, ax=ax4, cbar_kws={'shrink': 0.8})
        cbar = hm.collections[0].colorbar
        # 设置 colorbar 标签字体
        cbar.set_label('相关系数', fontproperties=self.chinese_font, fontsize=10)
        # 设置刻度标签字体（关键修复）
        ax4.set_xticklabels(ax4.get_xticklabels(), fontproperties=self.chinese_font, rotation=45)
        ax4.set_yticklabels(ax4.get_yticklabels(), fontproperties=self.chinese_font)
        # 设置热力图标题（已有）
        ax4.set_title('各指标相关性矩阵', fontproperties=self.chinese_font, fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, 'fig4_macro_correlation.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"图4已保存: {filepath}")
        
        
    def plot5_enrollment_effect(self):
        """
        图5: 招生计划影响分析
        对应RQ5: 招生计划影响
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # 散点图
        ax1 = axes[0]
        sample_df = self.df.sample(min(1000, len(self.df)), random_state=42)
        scatter = ax1.scatter(sample_df['拟招生人数'], sample_df['总分要求'],
                              c=sample_df['总分要求'], cmap='viridis',
                              alpha=0.6, s=30, edgecolors='white', linewidth=0.5)
        z = np.polyfit(self.df['拟招生人数'], self.df['总分要求'], 1)
        x_fit = np.linspace(self.df['拟招生人数'].min(), self.df['拟招生人数'].max(), 100)
        ax1.plot(x_fit, np.poly1d(z)(x_fit), 'r--', linewidth=2, label=f'拟合线 (斜率={z[0]:.2f})')
        
        self._set_labels(ax1, title='拟招生人数与复试分数线关系', xlabel='拟招生人数', ylabel='复试分数线 (分)')
        ax1.legend(prop=self.chinese_font)
        ax1.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax1, label='分数线')
        
        # 分组柱状图
        ax2 = axes[1]
        self.df['招生规模'] = pd.cut(
            self.df['拟招生人数'],
            bins=[0, 20, 50, 100, 500],
            labels=['小规模\n(<20)', '中等\n(20-50)', '较大\n(50-100)', '大规模\n(>100)']
        )
        size_stats = self.df.groupby('招生规模', observed=True)['总分要求'].agg(['mean', 'std'])
        bars = ax2.bar(range(len(size_stats)), size_stats['mean'], yerr=size_stats['std'], capsize=5,
                       color=['#FF6B6B', '#FFD93D', '#6BCB77', '#4D96FF'],
                       edgecolor='white', linewidth=1.5, width=0.6)
        for bar, val in zip(bars, size_stats['mean']):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                     f'{val:.1f}', ha='center', fontsize=11, fontweight='bold',
                     fontproperties=self.chinese_font)
        ax2.set_xticks(range(len(size_stats)))
        ax2.set_xticklabels(size_stats.index, fontproperties=self.chinese_font, fontsize=10)
        self._set_labels(ax2, title='不同招生规模的平均分数线', xlabel='招生规模', ylabel='平均复试分数线 (分)')
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, 'fig5_enrollment_effect.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"图5已保存: {filepath}")
        
    def plot6_heatmap(self):
        fig, ax = plt.subplots(figsize=(16, 8))
        top_schools = ['清华大学', '北京大学', '复旦大学', '上海交通大学', '浙江大学',
                    '南京大学', '武汉大学', '中山大学', '四川大学', '西安交通大学']
        main_subjects = ['哲学', '经济学', '法学', '文学', '理学', '工学', '医学', '管理学']
    
        heatmap_data = self.df[
            (self.df['学校名称'].isin(top_schools)) & 
            (self.df['学科门类'].isin(main_subjects))
        ].pivot_table(values='总分要求', index='学校名称', columns='学科门类', aggfunc='mean')
    
        # 绘制热力图，并获取 colorbar 对象
        hm = sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='RdYlGn_r',
                        center=330, ax=ax, linewidths=0.5,
                        cbar_kws={'label': '复试分数线 (分)'})
        cbar = hm.collections[0].colorbar  # 获取 colorbar 对象
    
        # 设置 colorbar 标签字体
        cbar.set_label('复试分数线 (分)', fontproperties=self.chinese_font, fontsize=12)
        # 设置 colorbar 刻度标签字体
        cbar.ax.tick_params(labelsize=10)
        for label in cbar.ax.get_yticklabels():
            label.set_fontproperties(self.chinese_font)
    
        # 设置主图标题和轴标签
        ax.set_title('主要高校 × 学科门类复试分数线热力图', 
                    fontproperties=self.chinese_font, fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel('学科门类', fontproperties=self.chinese_font, fontsize=12)
        ax.set_ylabel('高校', fontproperties=self.chinese_font, fontsize=12)
    
        # 设置 x/y 轴刻度标签字体
        ax.set_xticklabels(ax.get_xticklabels(), fontproperties=self.chinese_font, rotation=45)
        ax.set_yticklabels(ax.get_yticklabels(), fontproperties=self.chinese_font)
    
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, 'fig6_school_subject_heatmap.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"图6已保存: {filepath}")
        
    def generate_all_figures(self):
        """生成所有图表"""
        print("\n" + "="*60)
        print("开始生成所有图表...")
        print("="*60)
        
        self.plot1_time_trend()
        self.plot2_subject_comparison()
        self.plot3_regional_comparison()
        self.plot4_macro_correlation()
        self.plot5_enrollment_effect()
        self.plot6_heatmap()
        
        print(f"\n所有图表已生成到: {self.output_dir}/")