
# 请求的url
# https://hq.sinajs.cn/rn=1782286579827&list=s_sh000001,s_sz399001,s_bj899050,s_sz399006,s_sh000680,s_sh000300
A_SHARE = "s_sh000001,s_sz399001,s_bj899050,s_sz399006,s_sh000680,s_sh000300"

# 返回的数据结构
# var hq_str_s_sh000001="上证指数,4110.8134,4.5617,0.11,6445275,151419329";
# var hq_str_s_sz399001="深证成指,16051.32,197.123,1.24,790129563,177012359";
# var hq_str_s_bj899050="北证50,1295.954,14.741,1.151,864727396,22852423559.000";
# var hq_str_s_sz399006="创业板指,4251.42,59.230,1.41,45331913,39263595";
# var hq_str_s_sh000680="科创综指,2342.6385,63.9098,2.80,651348,50790896";
# var hq_str_s_sh000300="沪深300,4943.0197,23.6337,0.48,3122490,96494585";

# 请求的url
# https://hq.sinajs.cn/rn=1782286844319&list=rt_hkHSI,b_NKY,znb_TWJQ,b_AS30
ASIA = "rt_hkHSI,b_NKY,znb_TWJQ,b_AS30"
# 返回的数据结构
# var hq_str_rt_hkHSI = "HSI,恒生指数,23420.700,23336.279,23565.650,23248.870,23436.061,99.780,0.430,0.000,0.000,294361564.550,12747146019,0.000,0.000,28056.100,23252.130,2026/06/24,15:40:46,,,,,,";
# var hq_str_b_NKY = "日经225指数,69174.7500,-613.63,-0.88,2:12 AM,14:12:00,2026-06-24,14:30:01,69615.0800,69788.3800,70218.7100,68461.1000,0";
# var hq_str_znb_TWJQ = "台湾加权指数,46043.6000,-1057.05,-2.24,,,2026-06-24,13:38:15,46909.9800,47100.6500,46909.9800,45819.7100,15872270336";
# var hq_str_b_AS30 = "澳交所普通股指数 ,7887.10,17.50,0.22,02:57:43,14:57:43";

# 请求的url
# https://hq.sinajs.cn/rn=1782286889873&list=EURUSD,b_UKX,b_DAX,b_SX5E,b_CAC
EUROPE = "EURUSD,b_UKX,b_DAX,b_SX5E,b_CAC"  
# 返回的数据结构
# var hq_str_EURUSD = "15:41:26,1.1357,1.1357,1.1381,33,1.1380,1.1384,1.1351,1.1357,欧元美元,2026-06-24";
# var hq_str_b_UKX = "富时100指数,10435.0600,6.21,0.06,9/26/2025,2025-09-26,2026-06-24,15:26:24,10429.0200,10428.8500,10441.4000,10412.7700,0";
# var hq_str_b_DAX = "德国DAX指数,24757.1400,-136.44,-0.55,9/26/2025,2025-09-26,2026-06-24,15:40:51,24790.7000,24893.5800,24800.6600,24745.4800,3301416";
# var hq_str_b_SX5E = "道琼斯欧元区斯托克50指数,6208.9500,-21.61,-0.35,9/26/2025,2025-09-26,2026-06-24,15:41:15,6234.7100,6230.5600,6243.5200,6205.9000,0";
# var hq_str_b_CAC = "法国CAC40指数,8352.9600,12.25,0.15,9/26/2025,2025-09-26,2026-06-24,15:40:46,8353.6800,8340.7100,8369.8900,8348.0500,0";

# 请求的url
# https://hq.sinajs.cn/rn=1782286933140&list=gb_dji,gb_ixic,gb_inx
AMERICA = "gb_dji,gb_ixic,gb_inx"
# 返回的数据结构
# var hq_str_gb_ixic = "纳斯达克,25587.0391,-2.21,2026-06-24 05:30:00,-579.5627,25549.7566,25882.5677,25513.2614,27190.2070,19795.2871,13852269966,9838058467,0,0.00,--,0.00,0.00,0.00,0.00,0,0,0.0000,0.00,0.00,,Jun 23 05:16PM EDT,26166.6018,0,1,2026,0.0000,0.0000,0.0000,0.0000,0.0000,0.0000";
# var hq_str_gb_inx = "标普500指数,7365.4600,-1.44,2026-06-24 04:20:23,-107.3300,7366.5098,7424.1699,7347.6001,7620.8999,6080.0898,3568083740,3651220570,0,0.00,--,0.00,0.00,0.00,0.00,0,0,0.0000,0.00,0.0000,,Jun 23 04:20PM EDT,7472.7900,0,1,2026";


"""
获取新浪指数数据 (A股/港股/美股/外汇/欧洲等)

URL: https://hq.sinajs.cn/rn={rn}&list={codes}
返回: var hq_str_{code}="name,value1,value2,..."; 格式的文本
"""
import re
from typing import Any, Optional
import time

import requests

from app.log_util import get_logger

logger = get_logger("sina_zs")

# ---------- 各类型指数的通用字段映射 ----------

# A股指数字段: s_sh000001 → 上证指数,4110.81,4.56,0.11,6445275,151419329
_A_SHARE_FIELDS = ["name", "price", "change", "change_pct", "volume", "amount"]

# 港股/日经/台湾/澳洲: rt_hkHSI → HSI,恒生指数,23420.70,...
_ASIA_FIELDS = ["eng_name", "name", "price", "prev_close", "high", "low", "open",
                "change", "change_pct", "bid", "ask", "volume", "amount",
                "year_high", "year_low", "date", "time"]

# 外汇: EURUSD → 15:41:26,1.1357,1.1357,1.1381,33,...
_FOREX_FIELDS = ["time", "price", "bid", "ask", "volume", "high", "low",
                 "prev_close", "open", "name", "date"]

# 欧洲指数: b_UKX → 富时100指数,10435.06,6.21,0.06,...
_EUROPE_FIELDS = ["name", "price", "change", "change_pct", "prev_date",
                  "date", "update_time", "prev_close", "open", "high", "low", "volume"]

# 美股指数: gb_ixic → 纳斯达克,25587.04,-2.21,2026-06-24 05:30:00,...
_US_FIELDS = ["name", "price", "change_pct", "update_time", "change",
              "open", "high", "low", "year_high", "year_low",
              "volume", "amount", "prev_close", "bid", "ask",
              "bid_size", "ask_size", "amplitude", "turnover_rate",
              "pe", "pb", "dividend_yield", "market_cap"]


def _detect_index_type(code: str) -> str:
    """根据 code 前缀判断指数类型"""
    if code.startswith(("s_sh", "s_sz", "s_bj")):
        return "a_share"
    if code.startswith(("rt_hk", "b_NKY", "znb_TW", "b_AS")):
        return "asia"
    if not "_" in code:
        return "forex"  # e.g. EURUSD
    if code.startswith("b_"):
        return "europe"
    if code.startswith("gb_"):
        return "us"
    return "unknown"


def _fields_for_code(code: str) -> list[str]:
    """根据指数类型返回字段名列表"""
    type_map = {
        "a_share": _A_SHARE_FIELDS,
        "asia": _ASIA_FIELDS,
        "forex": _FOREX_FIELDS,
        "europe": _EUROPE_FIELDS,
        "us": _US_FIELDS,
    }
    return type_map.get(_detect_index_type(code), [])


def _parse_values(code: str, values: list[str]) -> dict:
    """将原始值列表映射为命名字段, 并附加 code/name/type"""
    item: dict[str, Any] = {"code": code, "raw": values}
    fields = _fields_for_code(code)
    for i, val in enumerate(values):
        item[f"f{i}"] = val  # 全部保留为 f0, f1, ...
        if i < len(fields):
            item[fields[i]] = val
    # 名称统一处理
    name_field = item.get("name", "")
    if not name_field and values:
        # 对 A股指数, name 就是第一个字段
        if _detect_index_type(code) == "a_share":
            item["name"] = values[0].strip()
        elif _detect_index_type(code) in ("asia", "europe", "us"):
            item["name"] = values[1].strip() if len(values) > 1 else values[0].strip()
        elif _detect_index_type(code) == "forex":
            # 外汇名称在倒数第 2 个
            item["name"] = values[-2].strip() if len(values) >= 2 else ""
    item["type"] = _detect_index_type(code)
    return item


# ---------- 主函数 ----------

def get_sina_zs_data(params: dict) -> Optional[list[dict]]:
    """
    获取新浪指数数据

    params: dict
        {
            "list": "s_sh000001,s_sz399001,s_bj899050,...",
            "rn": "1782286579827"
        }

    Returns:
        list[dict] | None — 解析后的指数列表, 失败或空数据返回 None
    """
    list_str = params.get("list", "")
    rn = params.get("rn", "")
    _date = time.strftime("%Y-%m-%d", time.localtime())
    if not list_str:
        logger.warning("get_sina_zs_data: list 参数为空")
        return None

    url = f"https://hq.sinajs.cn/rn={rn}&list={list_str}"

    headers = {
        "Referer": "https://finance.sina.com.cn",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = "gb2312"

        if resp.status_code != 200:
            logger.error("请求 hq.sinajs.cn 失败: status=%d", resp.status_code)
            return None

        text = resp.text
    except requests.RequestException as exc:
        logger.error("请求 hq.sinajs.cn 异常: %s", exc)
        return None

    # 解析 var hq_str_{code}="..." 格式
    pattern = r'var hq_str_(\w+)\s*=\s*"([^"]*)"'
    matches = re.findall(pattern, text)

    if not matches:
        logger.warning("未匹配到指数数据, 原始响应: %.200s", text)
        return None

    result = []
    for code, data_str in matches:
        values = data_str.split(",")
        item = _parse_values(code, values)
        item['date'] = _date
        result.append(item)

    logger.info("成功解析 %d 条指数数据", len(result))
    return result


def get_sina_zs_data_with_timestamp() -> Optional[list[dict]]:
    """
    获取新浪指数数据, 自动生成 rn 时间戳

    list_str: str — 指数代码列表, 逗号分隔
    Returns:
        list[dict] | None — 解析后的指数列表, 失败或空数据返回 None
    """
    result = []
    for list_str in [A_SHARE, ASIA, EUROPE, AMERICA]:

        rn = str(int(time.time() * 1000))  # 毫秒级时间戳
        params = {"list": list_str, "rn": rn}
        rtn = get_sina_zs_data(params)
        if rtn:
            result.extend(rtn)
        time.sleep(3) # 避免请求过快
    return result if result else []