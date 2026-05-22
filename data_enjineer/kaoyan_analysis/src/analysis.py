"""
数据分析模块 - 围绕5个核心研究问题
"""
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import statsmodels.api as sm


class ScoreAnalyzer:
    """考研分数分析器"""
    
    def __init__(self, data_path='data/processed/scores_cleaned.csv'):
        self.df = pd.read_csv(data_path, encoding='utf-8-sig')
        print(f"数据加载完成: {len(self.df)} 条记录")
        
    def question1_time_trend(self):
        """
        RQ1: 时间维度分析
        2018-2025年间分数线整体变化趋势，是否存在"大小年"波动
        """
        print("\n" + "="*60)
        print("RQ1: 复试分数线时间变化趋势分析")
        print("="*60)
        
        # 按年份统计
        yearly_stats = self.df.groupby('年份').agg(
            平均分=('总分要求', 'mean'),
            中位数=('总分要求', 'median'),
            标准差=('总分要求', 'std'),
            最低分=('总分要求', 'min'),
            最高分=('总分要求', 'max')
        ).round(2)
        
        print("\n各年份分数线统计:")
        print(yearly_stats)
        
        # 检测"大小年"模式
        scores = yearly_stats['平均分'].values
        peaks = []
        valleys = []
        
        for i in range(1, len(scores) - 1):
            if scores[i] > scores[i-1] and scores[i] > scores[i+1]:
                peaks.append(i)
            elif scores[i] < scores[i-1] and scores[i] < scores[i+1]:
                valleys.append(i)
        
        # 统计趋势
        x = np.arange(len(scores)).reshape(-1, 1)
        y = scores
        slope = np.polyfit(x.flatten(), y, 1)[0]
        
        print(f"\n趋势斜率: {slope:.2f} 分/年")
        print(f"高点数: {len(peaks)}, 低点数: {len(valleys)}")
        print(f"是否存在'大小年'波动: {'是' if len(peaks) >= 2 and len(valleys) >= 2 else '否'}")
        
        return yearly_stats
    
    def question2_subject_difference(self):
        """
        RQ2: 学科差异分析
        不同学科门类分数差异，哪些学科上涨最快
        """
        print("\n" + "="*60)
        print("RQ2: 学科门类差异分析")
        print("="*60)
        
        # 按学科统计
        subject_stats = self.df.groupby('学科门类').agg(
            平均分=('总分要求', 'mean'),
            标准差=('总分要求', 'std'),
            最低分=('总分要求', 'min'),
            最高分=('总分要求', 'max')
        ).round(2).sort_values('平均分', ascending=False)
        
        print("\n各学科门类分数线统计:")
        print(subject_stats)
        
        # 计算各学科涨幅
        subject_growth = {}
        for subject in self.df['学科门类'].unique():
            sub_df = self.df[self.df['学科门类'] == subject].groupby('年份')['总分要求'].mean()
            if len(sub_df) >= 2:
                growth = (sub_df.iloc[-1] - sub_df.iloc[0])
                subject_growth[subject] = growth
        
        growth_df = pd.DataFrame(
            list(subject_growth.items()),
            columns=['学科门类', '涨幅(分)']
        ).sort_values('涨幅(分)', ascending=False)
        
        print("\n各学科门类涨幅排名:")
        print(growth_df)
        
        # ANOVA检验学科间差异显著性
        groups = [group['总分要求'].values for name, group in self.df.groupby('学科门类')]
        f_stat, p_value = stats.f_oneway(*groups)
        print(f"\nANOVA检验: F={f_stat:.2f}, p={p_value:.6f}")
        print(f"学科间差异显著: {'是' if p_value < 0.05 else '否'}")
        
        return subject_stats, growth_df
    
    def question3_regional_effect(self):
        """
        RQ3: 地域效应分析
        一线城市高校分数线是否显著高于其他地区
        """
        print("\n" + "="*60)
        print("RQ3: 地域效应分析")
        print("="*60)
        
        # 一线城市 vs 非一线城市
        regional_stats = self.df.groupby('是否一线城市').agg(
            平均分=('总分要求', 'mean'),
            中位数=('总分要求', 'median'),
            标准差=('总分要求', 'std'),
            学校数量=('学校名称', 'nunique')
        ).round(2)
        
        print("\n一线城市 vs 非一线城市:")
        print(regional_stats)
        
        # t检验
        tier1_scores = self.df[self.df['是否一线城市'] == '一线城市']['总分要求']
        non_tier1_scores = self.df[self.df['是否一线城市'] == '非一线城市']['总分要求']
        
        t_stat, p_value = stats.ttest_ind(tier1_scores, non_tier1_scores)
        mean_diff = tier1_scores.mean() - non_tier1_scores.mean()
        
        print(f"\n独立样本t检验:")
        print(f"t统计量: {t_stat:.2f}")
        print(f"p值: {p_value:.6f}")
        print(f"均值差: {mean_diff:.2f} 分")
        print(f"一线城市显著高于非一线: {'是' if p_value < 0.05 and mean_diff > 0 else '否'}")
        
        # 按城市统计
        city_stats = self.df.groupby('城市').agg(
            平均分=('总分要求', 'mean'),
            标准差=('总分要求', 'std')
        ).round(2).sort_values('平均分', ascending=False)
        
        print("\n各城市分数线排名 TOP10:")
        print(city_stats.head(10))
        
        return regional_stats, city_stats
    
    def question4_macro_correlation(self):
        """
        RQ4: 外部关联分析
        复试分数线与宏观经济指标的相关性
        """
        print("\n" + "="*60)
        print("RQ4: 宏观经济关联分析")
        print("="*60)
        
        # 宏观经济数据（来自国家统计局）
        macro_data = {
            2018: {'GDP增速': 6.7, '失业率': 4.9, '考研报名人数': 238},
            2019: {'GDP增速': 6.0, '失业率': 5.1, '考研报名人数': 290},
            2020: {'GDP增速': 2.3, '失业率': 5.2, '考研报名人数': 341},
            2021: {'GDP增速': 8.4, '失业率': 5.1, '考研报名人数': 377},
            2022: {'GDP增速': 3.0, '失业率': 5.5, '考研报名人数': 457},
            2023: {'GDP增速': 5.2, '失业率': 5.2, '考研报名人数': 474},
            2024: {'GDP增速': 5.0, '失业率': 5.1, '考研报名人数': 438},
            2025: {'GDP增速': 4.8, '失业率': 5.0, '考研报名人数': 420},
        }
        
        macro_df = pd.DataFrame(macro_data).T
        macro_df.index.name = '年份'
        
        # 合并数据
        yearly_avg = self.df.groupby('年份')['总分要求'].mean()
        merged = yearly_avg.to_frame().join(macro_df, how='inner')
        merged.columns = ['平均分数线'] + list(macro_df.columns)
        
        print("\n年度数据汇总:")
        print(merged)
        
        # 相关性分析
        print("\n相关性分析:")
        correlations = {}
        for col in macro_df.columns:
            if len(merged.dropna()) >= 3:
                r, p = pearsonr(merged['平均分数线'], merged[col])
                correlations[col] = {'相关系数': round(r, 3), 'p值': round(p, 4)}
                significance = "***" if p < 0.01 else ("**" if p < 0.05 else ("*" if p < 0.1 else ""))
                print(f"  分数线 vs {col}: r={r:.3f}, p={p:.4f} {significance}")
        
        # 回归分析
        print("\n多元回归分析:")
        X = merged[['GDP增速', '失业率']]
        X = sm.add_constant(X)
        y = merged['平均分数线']
        
        model = sm.OLS(y, X).fit()
        print(model.summary().tables[1])
        print(f"R² = {model.rsquared:.3f}")
        
        return merged, correlations
    
    def question5_enrollment_effect(self):
        """
        RQ5: 招生计划影响
        拟招生人数与分数线高低是否呈负相关
        """
        print("\n" + "="*60)
        print("RQ5: 招生计划影响分析")
        print("="*60)
        
        # 相关性分析
        r, p = pearsonr(self.df['拟招生人数'], self.df['总分要求'])
        print(f"\n招生人数与分数线相关系数: r={r:.3f}, p={p:.4f}")
        
        # 分组统计
        self.df['招生规模'] = pd.cut(
            self.df['拟招生人数'],
            bins=[0, 20, 50, 100, 500],
            labels=['小规模(<20)', '中等(20-50)', '较大(50-100)', '大规模(>100)']
        )
        
        size_stats = self.df.groupby('招生规模', observed=True).agg(
            平均分数线=('总分要求', 'mean'),
            标准差=('总分要求', 'std'),
            记录数=('总分要求', 'count')
        ).round(2)
        
        print("\n不同招生规模的平均分数线:")
        print(size_stats)
        
        # 控制学科门类的偏相关分析
        print("\n控制学科门类后的偏相关:")
        for subject in ['工学', '经济学', '法学', '文学']:
            sub_df = self.df[self.df['学科门类'] == subject]
            if len(sub_df) >= 10:
                r_sub, p_sub = pearsonr(sub_df['拟招生人数'], sub_df['总分要求'])
                print(f"  {subject}: r={r_sub:.3f}, p={p_sub:.4f}")
        
        return r, p, size_stats
    
    def run_all_analyses(self):
        """运行所有分析"""
        results = {}
        results['RQ1_trend'] = self.question1_time_trend()
        results['RQ2_subject'] = self.question2_subject_difference()
        results['RQ3_region'] = self.question3_regional_effect()
        results['RQ4_macro'] = self.question4_macro_correlation()
        results['RQ5_enrollment'] = self.question5_enrollment_effect()
        return results