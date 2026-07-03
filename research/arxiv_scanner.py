
import arxiv
import os
import pandas as pd
from datetime import datetime

def scan_quant_papers(query='"Alpha Factor" OR "Stock Returns" OR "Quantitative Strategy"', max_results=10):
    print(f"🔎 [PaperScanner] 正在 arXiv 搜索最新量化论文: {query}...")
    
    # 1. 执行搜索
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    results = []
    for result in client.results(search):
        results.append({
            "title": result.title,
            "date": result.published,
            "url": result.pdf_url,
            "summary": result.summary[:200] + "..."
        })
    
    # 2. 保存结果
    df = pd.DataFrame(results)
    os.makedirs("research/reports", exist_ok=True)
    file_path = f"research/reports/new_papers_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(file_path, index=False)
    
    print(f"✅ 扫描完成！共找到 {len(results)} 篇论文。报告已保存至: {file_path}")
    print("\n🌟 最新论文预览:")
    for i, r in enumerate(results[:3]):
        print(f"   [{i+1}] {r['title']}")
        print(f"       PDF: {r['url']}")

if __name__ == "__main__":
    # 安装依赖: uv pip install arxiv
    try:
        scan_quant_papers()
    except ImportError:
        print("💡 请先安装依赖: uv pip install arxiv")
