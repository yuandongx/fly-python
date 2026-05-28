from datetime import datetime
from typing import Any
import random
from decimal import getcontext
import requests
from app.log_util import get_logger

logger = get_logger('qq')

NAMES = ['index',
         'name',
         'code',
         'price',
         'close',
         'open',
         'volume', # 成交量
         'wai_pan',
         'nei_pan',
         'buy_price_1',
         'buy_1', 'buy_price_2', 'buy_2',
         'buy_price_3', 'buy_3', 'buy_price_4', 'buy_4',
         'buy_price_5', 'buy_5', 'sale_price_1', 'sale_1',
         'sale_price_2', 'sale_2', 'sale_price_3', 'sale_3',
         'sale_price_4', 'sale_4', 'sale_price_5', 'sale_5',
         'unknow1',  # 未知字段1
         'close_time',  # 收盘时间
         'change',  # 涨跌额
         'changepercent',  # 涨跌幅
         'high',  # 最高价
         'low',  # 最低价
         '___',  # '10.13/134948/136338519',  # 当前价/成交量（手）/成交额（元）
         'total_trade',  # 成交量
         'trade_value',  # 成交额
         'turnover',  # 换手率
         'ttm_pe',  # 滚动市盈率
         'unknown9',  # 未知字段1
         'high1',  # 最高价
         'low1',  # 最低价
         'zheng_fu',  # 振幅
         'market_cap',  # 流通市值
         'amount_value',  # 总市值
         'pb',  # 市净率
         'max_price',  # 涨停价
         'min_price',  # 跌停价
         'unknown2',  # 未知字段2
         'unknown3',  # 未知字段3
         'avg_price',  # 均价
         'ttl_pe',  # 动态市盈率
         'pe',  # 市盈率 静态市盈率
         'unknown4',  # 未知字段4
         'unknown5',  # 未知字段5
         'dividend',  # 每股收益（元）
         'amount',  # 成交额
         'unknown5',  # 未知字段5
         'unknown7',  # 未知字段7
         'unknown8',  # 未知字段8
         'type',  # 类型-- 股票/基金/债券等
         'unknown10',
         'unknown11',
         'dividend_yiel', # 股息率
         'unknown12',
         'unknown13',
         'last52high',
         'last52low',
         'unknown14',
         'unknown15',
         'unknown16',
         'unknown17',
         'total_volume',  # 总股本
         'ratio', # 委比
         'unknown18',
         'unknown19',
         'unknown20',
         'unknown21',
         'unknown22',
         'unknown23',
         'unknown24',
         'currency',  # 币种
         'unknown25',
         'status',  # 状态
         'unknown26',  # 未知字段26
         'unknown27',  # 未知字段27
         ]

getcontext().prec = 16  # Set decimal precision for calculations


def map_qq_data(data: list) -> dict:
    """
    Maps the QQ Finance data to a dictionary with predefined keys.

    Args:
        data (list): The list of stock information from QQ Finance.

    Returns:
        dict: A dictionary mapping the stock information to predefined keys.
    """
    if len(data) != len(NAMES):
        logger.error(f"Data length mismatch: expected {len(NAMES)}, got {len(data)}")
        return {}

    return {name: value for name, value in zip(NAMES, data)}

def fetch_qq_info(code: str) -> Any:
    """
    Fetches the stock information from QQ Finance.

    Args:
        code (str): The stock code.

    Returns:
        Any: The parsed stock information.
    """
    random.seed(datetime.now().timestamp())
    r = random.random()  # Random number to prevent caching
    url = f"https://web.sqt.gtimg.cn/q={code}?r={r}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.text.strip().replace('"', '')
        if '=' in data and len(data) < 20:
            logger.error(f"Unexpected data format for code {code}: {data}")
            return None
        data = data.split('=')[1].split('~')
        data = map_qq_data(data)
       
        return data
    except requests.RequestException as e:
        logger.error(f"Error fetching data for code {code}: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    code = "sh603300"
    stock_info = fetch_qq_info(code)
    if stock_info:
        logger.info(f"Fetched stock info for {code}: {stock_info}")
    else:
        logger.error(f"Failed to fetch stock info for {code}")
