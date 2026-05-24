import node_select as ns
from typing import List, Dict  # 添加类型导入

VERSION = 3


def fill_data(keys: List[str], prices: List[float], max_speed: List[float],
             speed_table: List[List[float]], node_f: str, node_t: str) -> None:
    """
    向计算模块填充数据
    可以填充 prices, price_end, speeds
    keys:           标识符列表
    prices:         价格列表
    max_speed:      节点的最大带宽
    speed_table:    二维列表 [发送][接收]
    node_f:         发送节点标识符
    node_t:         接收节点标识符
    """
    __f = -1
    __t = -1
    for __i in range(len(keys)):
        if keys[__i] == node_f:
            __f = __i
            ns.price_end += prices[__i]
            if ns.speed_limit < 0:
                ns.speed_limit = max_speed[__i]
            else:
                ns.speed_limit = min(ns.speed_limit, max_speed[__i])
        elif keys[__i] == node_t:
            __t = __i
            ns.price_end += prices[__i]
            if ns.speed_limit < 0:
                ns.speed_limit = max_speed[__i]
            else:
                ns.speed_limit = min(ns.speed_limit, max_speed[__i])
        else:
            ns.prices[keys[__i]] = prices[__i]

    for __i in range(len(keys)):
        if __i != __f and __i != __t:
            ns.speeds[keys[__i]] = min(speed_table[__f][__i], speed_table[__i][__t])


def clear() -> None:
    """清除所有数据"""
    ns.prices = {}  # type: Dict[str, float]
    ns.speeds = {}  # type: Dict[str, float]
    ns.price_end = 0.0
    ns.speed_limit = -1.0