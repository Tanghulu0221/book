"""
数据清洗和预处理模块
"""
import pandas as pd
import numpy as np
import os


class DataCleaner:
    """数据清洗器"""
    
    def __init__(self, raw_data_path='data/raw/scores_raw.csv'):
        self.raw_data_path = raw_data_path
        self.df = None
        self.cleaned_df = None
        
    def load_data(self):
        """加载原始数据"""
        if os.path.exists(self.raw_data_path):
            self.df = pd.read_csv(self.raw_data_path, encoding='utf-8-sig')
            print(f"原始数据加载成功: {len(self.df)} 条记录")
        else:
            print("原始数据不存在，先生成模拟数据...")
            from src.crawler import KaoyanScoreCrawler
            crawler = KaoyanScoreCrawler()
            all_data = crawler.crawl_all_years()
            self.df = crawler.save_to_csv(all_data)
        
        return self.df
    
    def clean(self):
        """执行数据清洗"""
        if self.df is None:
            self.load_data()
        
        df = self.df.copy()
        
        # 1. 检查缺失值
        print("\n=== 缺失值统计 ===")
        missing = df.isnull().sum()
        print(missing[missing > 0])
        
        # 2. 处理缺失值
        # 对数值型列用中位数填充
        numeric_cols = ['总分要求', '单科满分100', '单科满分150', '拟招生人数']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].median())
        
        # 3. 检测异常值
        print("\n=== 异常值检测 ===")
        if '总分要求' in df.columns:
            Q1 = df['总分要求'].quantile(0.25)
            Q3 = df['总分要求'].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = df[(df['总分要求'] < lower_bound) | (df['总分要求'] > upper_bound)]
            print(f"总分要求异常值数量: {len(outliers)}")
            
            # 将异常值限制在边界内
            df['总分要求'] = df['总分要求'].clip(lower_bound, upper_bound)
        
        # 4. 添加衍生变量
        df['年份'] = df['年份'].astype(int)
        df['总分要求'] = df['总分要求'].astype(int)
        df['单科满分100'] = df['单科满分100'].astype(int)
        df['单科满分150'] = df['单科满分150'].astype(int)
        
        # 添加学校层次分类
        top_schools = ['清华大学', '北京大学', '复旦大学', '上海交通大学', '浙江大学']
        df['学校层次'] = df['学校名称'].apply(
            lambda x: 'TOP5' if x in top_schools else '其他自划线高校'
        )
        
        # 添加地区分组
        df['是否一线城市'] = df['地区类别'].apply(
            lambda x: '一线城市' if x == '一线城市' else '非一线城市'
        )
        
        # 添加学科热度分类
        hot_subjects = ['经济学', '文学', '管理学', '艺术学']
        df['学科热度'] = df['学科门类'].apply(
            lambda x: '热门学科' if x in hot_subjects else '一般学科'
        )
        
        self.cleaned_df = df
        print(f"\n数据清洗完成，共 {len(df)} 条有效记录")
        
        return self.cleaned_df
    
    def save_cleaned_data(self, filename='data/processed/scores_cleaned.csv'):
        """保存清洗后的数据"""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        if self.cleaned_df is not None:
            self.cleaned_df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"清洗后数据已保存至: {filename}")
    
    def get_summary_statistics(self):
        """获取描述性统计"""
        if self.cleaned_df is None:
            self.clean()
        
        print("\n=== 描述性统计 ===")
        desc = self.cleaned_df.describe()
        print(desc)
        
        print("\n=== 学科门类分布 ===")
        print(self.cleaned_df['学科门类'].value_counts())
        
        print("\n=== 年份分布 ===")
        print(self.cleaned_df['年份'].value_counts().sort_index())
        
        return desc