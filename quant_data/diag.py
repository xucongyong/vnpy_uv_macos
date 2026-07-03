
import requests
import sys

def check():
    # 东方财富的 A 股代码列表接口
    url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=20&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print("📡 [Diag] 正在诊断行情源连通性...")
    
    # 测试 1: 国内行情源
    try:
        r = requests.get(url, headers=headers, timeout=5)
        print(f"✅ [Test 1] 东方财富响应状态码: {r.status_code}")
    except Exception as e:
        print(f"❌ [Test 1] 东方财富连接失败: {e}")

    # 测试 2: 百度 (检查基础互联网连接)
    try:
        r = requests.get("https://www.baidu.com", timeout=5)
        print(f"✅ [Test 2] 百度响应状态码: {r.status_code}")
    except Exception as e:
        print(f"❌ [Test 2] 基础网络不可用: {e}")

if __name__ == "__main__":
    check()
