"""
get data from sina
"""
from datetime import datetime
from typing import Any

import requests
from app.log_util import get_logger

logger = get_logger('sina')

# sgt_sz
# hgt_sh
# hs_bjs
NODES = [
    "sgt_sz",
    "hgt_sh",
    "hs_bjs",
    "kcb",
    "cyb"
]
# https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=40&sort=changepercent&asc=1&node=hs_a&symbol&_s_r_a=init


def get(url, payload=None) -> Any | None:
    """
    base method: get data
    """
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "User-Agent": "insomnia/9.3.0-beta.6",
        "Connection": "keep-alive"
    }
    resp = requests.get(url, params=payload, headers=headers, timeout=30)
    if resp.status_code == 200:
        return resp.json()
    else:
        return None


def get_hq_count(node: str):
    """
    > hgt_sh
    
    """    
    url = f'https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeStockCount?node={node}'
    data = get(url)
    if isinstance(data, str) and data.isdigit():
        return int(data)
    return 0


def get_hq_data(params):
    """
    get hang qing data
    """
    json_api = 'https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData'
    # page=1&num=40&sort=changepercent&asc=1&node=hs_a&symbol&_s_r_a=init

    payload = params.get('payload') 
    res = get(json_api, payload)
    if res is None:
        return
    date = datetime.now().strftime('%Y%m%d')
    rtn = []
    for item in res:
        item['idx'] = f'{date}@{item["symbol"]}'
        item['node'] = payload['node']
        item['date'] = date
        rtn.append(item)
    return rtn


def get_hq_node_data(node):
    """
    按node查询行情
    """
    result = []
    _now = datetime.now()
    count = get_hq_count(node)
    logger.info(f'Find {node} has {count} items.')
    p, m = divmod(count, 40)
    if m > 0:
        pages = p + 2
    else:
        pages = p + 1
    for i in range(1, pages):

        payload = {"page": i,
               "num": 40,
               "sort": "changepercent",
               "asc": 1,
               "symbol": "",
               "node": node,
               "_s_r_a": "init"}
        rtn = get_hq_data({"payload": payload, "node": node})
        if rtn is not None and isinstance(rtn, list):
            result.extend(rtn)
    _spend = datetime.now() - _now
    logger.info(f'Got {len(result)} items in {_spend.seconds}s.')
    return {"data": result, "count": len(result), "total": count, "node": node}



def get_sina_data():
    """
    get sina data
    """
    result = []
    for node in NODES:
        data = get_hq_node_data(node)
        if data is not None:
            logger.info(f'Got {data["count"]} items for node {node}.')
            result.extend(data['data'])
    return result
