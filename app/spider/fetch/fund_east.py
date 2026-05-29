import requests
import re
import json
import time

# 1. 接口地址 + 参数
url = "https://fund.eastmoney.com/data/rankhandler.aspx"


# 2. 关键请求头（绕过反爬）
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://fund.eastmoney.com/data/fundranking.html"
}

def get_params(**kwargs):
    params = {
    "op": "ph",
    "dt": "kf",
    "ft": "all",
    "rs": "",
    "gs": "0",
    "sc": "1nzf",
    "st": "desc",
    "sd": "2025-05-29",
    "ed": "2026-05-29",
    "qdii": "",
    "tabSubtype": ",,,,,,",
    "pi": "1",
    "pn": "50",
    "dx": "1",
    "v": "0.9357918680370687"
}
    params.update(kwargs)
    return params
def js_to_json(js_str):
    # 给没有引号的 key 加上双引号（正则自动处理）
    json_str = re.sub(r'([a-zA-Z0-9_]+):', r'"\1":', js_str)
    return json_str
def get_fund_rank(**kwargs):
    try:
        params = get_params(**kwargs)

        # 发送请求
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        text = resp.text

        # 校验返回码
        if "ErrCode:-999" in text:
            print("❌ 访问被拦截，Cookie/请求头不足，请手动补充网页Cookie")
            return

        # 正则提取括号内的核心数据
        # 格式大概：rankData([...])
        # print(text)
        print("🔍 正在解析数据...")
        pattern = r"rankData\s*=\s*?(.*)"
        match = re.search(pattern, text)
        if not match:
            print("❌ 未匹配到数据")
            return

        raw_data = match.group(1).strip().rstrip(";").strip(",")
        # 处理JSON字符串
        raw_data = js_to_json(raw_data)
        data = json.loads(raw_data)

        # 解析列表：data[0] 统计信息，data[1] 基金列表
        # 25个字段名称（严格对应顺序）
        fields = [
            "基金代码",
            "基金简称",
            "基金拼音缩写",
            "数据日期",
            "单位净值",
            "累计净值",
            "日增长率(%)",
            "近1月收益(%)",
            "近3月收益(%)",
            "近6月收益(%)",
            "近1年收益(%)",
            "近3年收益(%)",
            "近5年收益(%)",
            "今年以来收益(%)",
            "成立以来年化收益(%)",
            "基金规模(万元)",
            "成立日期",
            "状态标识",
            "综合评分",
            "原始申购费率",
            "标准优惠费率",
            "费率标识",
            "实际执行费率",
            "优惠类型标识",
            "同类排名"
        ]
        all_records = data['datas']
        new_datas = []
        print(f"✅ 数据获取成功，基金总数：{data['allNum']}, 分页总数：{data['allPages']}")
        print("-" * 80)
        n_fields = len(fields)
        for record in all_records:
            tmp = record.split(",")
            if len(tmp) != n_fields:
                print(f"⚠️ 记录字段数不匹配，跳过：{record}")
                continue
            fund_info = dict(zip(fields, tmp))
            new_datas.append(fund_info)
        data['datas'] = new_datas
        return data
    except Exception as e:
        print(f"请求异常：{str(e)}")
        return None

def get_tiantain_fund_rank_data(): 
    max_get_num = 10000
    result = []
    for n in range(1, max_get_num):
        time.sleep(2) # 避免过快请求被封
        data = get_fund_rank(pi=str(n), pn="50")
        if not data or not data.get('datas'):
            print(f"❌ 第{n}页数据获取失败，停止爬取")
            break
        all_pages =  data['allPages']
        pages_index = data['pageIndex']
        print(f"✅ 第{n}/{all_pages}页数据获取成功，记录数：{len(data['datas'])}")
        result.extend(data['datas'])
        if pages_index == all_pages or n > int(all_pages):
            print(f"✅ 已获取所有{all_pages}页数据，停止爬取")
            break
    return result

if __name__ == "__main__":
    get_tiantain_fund_rank_data()