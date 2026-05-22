"""
一键运行所有分析
Usage: python run_analysis.py
"""
import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.dirname(__file__))

from src.crawler import KaoyanScoreCrawler
from src.data_cleaner import DataCleaner
from src.analysis import ScoreAnalyzer
from src.visualization import ScoreVisualizer


def main():
    print("="*60)
    print("考研复试分数线影响因素分析系统")
    print("="*60)
    
    # Step 1: 数据采集
    print("\n[Step 1/4] 数据采集...")
    crawler = KaoyanScoreCrawler()
    
    # 检查是否已有数据
    if os.path.exists('data/raw/scores_raw.csv'):
        print("发现已有原始数据，跳过爬取...")
    else:
        all_data = crawler.crawl_all_years(list(range(2018, 2026)))
        crawler.save_to_csv(all_data)
    
    # Step 2: 数据清洗
    print("\n[Step 2/4] 数据清洗...")
    cleaner = DataCleaner()
    cleaner.load_data()
    cleaner.clean()
    cleaner.save_cleaned_data()
    cleaner.get_summary_statistics()
    
    # Step 3: 数据分析
    print("\n[Step 3/4] 数据分析...")
    analyzer = ScoreAnalyzer()
    results = analyzer.run_all_analyses()
    
    # Step 4: 可视化
    print("\n[Step 4/4] 数据可视化...")
    visualizer = ScoreVisualizer()
    visualizer.generate_all_figures()
    
    print("\n" + "="*60)
    print("分析完成！")
    print(f"数据文件: data/processed/scores_cleaned.csv")
    print(f"图表文件: output/figures/")
    print("="*60)


if __name__ == '__main__':
    main()