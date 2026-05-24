from typing import Dict, List, Tuple  # 添加必要的类型导入

VERSION = 7

prices: Dict[str, float] = {}
"""
dict
key: 服务器标识符
value: 服务器使用价格 (RMB/h)
"""

speeds: Dict[str, float] = {}
"""
dict
key: 服务器标识符
value: 服务器传输速率 (Mbps)
"""

price_end: float = 0
"""
float, 发送/接收端服务器价格之和 (RMB/h)
"""

speed_limit: float = -1
"""
float, 总速率限制, 小于0为无限制 (Mbps)
"""


def add_node(key: str, price: float, speed: float) -> None:
    """
    添加节点信息
    """
    prices[key] = price
    speeds[key] = speed


def dprice(key: str) -> float:
    """
    服务器传输价格（按数据量计算）
    """
    return prices[key] / speeds[key]


def dprice_limited(key: str, key_list: List[str]) -> float:
    """
    服务器传输价格（按数据量计算），在有速率限制的情况下
    """
    if speed_limit < 0:
        return dprice(key)
    elif speed_limit <= speed(key_list):
        return float("inf")
    else:
        return prices[key] / min(speeds[key], speed_limit - speed(key_list))


def sum_price(key_list: List[str]) -> float:
    """
    服务器价格总和，包括发送/接收端服务器
    """
    s = price_end
    for k in key_list:
        s += prices[k]
    return s


def sum_speed(key_list: List[str]) -> float:
    """
    中间服务器总传输速率
    """
    s = 0
    for k in key_list:
        s += speeds[k]
    return s


def average_dprice(key_list: List[str]) -> float:
    """
    平均服务器传输价格（按数据量计算）
    """
    sp = speed(key_list)
    if sp <= 0:
        return float("Inf")
    return sum_price(key_list) / sp


def speed(key_list: List[str]) -> float:
    """
    预期传输速率
    """
    if speed_limit < 0:
        return sum_speed(key_list)
    else:
        return min(speed_limit, sum_speed(key_list))


def time(key_list: List[str], data_size: float) -> float:
    """
    预期传输时间
    """
    return data_size / sum_speed(key_list)


def cost(key_list: List[str], data_size: float) -> float:
    """
    预期总费用
    """
    return data_size * sum_price(key_list) / speed(key_list)


def __best_cost() -> Tuple[List[str], List[str]]:
    key_list: List[str] = []
    unused: List[str] = list(prices.keys())
    dp = float("Inf")
    while len(unused) > 0:
        dp = average_dprice(key_list)
        unused.sort(key=lambda k: dprice_limited(k, key_list))
        k = unused.pop(0)
        if dprice_limited(k, key_list) < dp:
            key_list.append(k)
        else:
            break
    return key_list, unused


def best_cost() -> List[str]:
    """
    生成最少花费方案
    """
    return __best_cost()[0]


def __speed_required(min_speed: float) -> Tuple[List[str], List[str]]:
    key_list, unused = __best_cost()
    __ms = min_speed
    if speed_limit > 0 and speed_limit < __ms:
        __ms = speed_limit
    while len(unused) > 0:
        if speed(key_list) >= __ms:
            break
        unused.sort(key=lambda k: dprice_limited(k, key_list))
        k = unused.pop(0)
        key_list.append(k)
    return key_list, unused


def speed_required(min_speed: float) -> List[str]:
    """
    生成最少花费方案，在有最低速率限制的情况下
    """
    return __speed_required(min_speed)[0]


def speed_order() -> List[str]:
    """
    按速率从高到低排序
    """
    li: List[str] = list(prices.keys())
    li.sort(key=lambda k: speeds[k], reverse=True)
    while speed_limit > 0 and sum_speed(li[:-1]) > speed_limit:
        li.pop()
    return li