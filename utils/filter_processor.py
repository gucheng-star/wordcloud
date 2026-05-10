# -*- coding: utf-8 -*-
"""
filter_processor.py - 用户自定义过滤词处理模块

功能:
    接收用户选择要过滤的词列表，从词频字典中删除这些词，
    返回过滤后的新词频结果。

使用场景:
    用户在前端词频列表中勾选不需要的词，点击"确认过滤"后，
    后端调用此模块进行过滤处理。
"""


def filter_word_freq(word_freq, remove_words):
    """
    从词频字典中移除指定的词。

    参数:
        word_freq: 原始词频字典，例如 {"数据": 20, "分析": 15, "模型": 10}
        remove_words: 用户选择要移除的词列表，例如 ["数据", "模型"]

    返回:
        dict: 过滤后的新词频字典，例如 {"分析": 15}
              注意：返回的是新字典，不会修改原始字典
    """
    # 将 remove_words 转为集合，查找效率 O(1)
    remove_set = set(remove_words)

    # 使用字典推导式，保留不在移除列表中的词
    filtered = {
        word: freq
        for word, freq in word_freq.items()
        if word not in remove_set
    }

    return filtered