# -*- coding: utf-8 -*-
"""
text_processor.py - 中文文本处理模块

功能:
    1. 读取 txt 文件（UTF-8 编码）
    2. 使用 jieba 进行中文分词
    3. 加载停用词表并过滤停用词
    4. 过滤空格、换行、长度为1的无意义词
    5. 使用 Counter 统计词频
    6. 返回词频结果（按频次降序排列）
"""

import os
import jieba
from collections import Counter


# 停用词文件路径：与 app.py 同级的 stopwords.txt
STOPWORDS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'stopwords.txt')


def load_stopwords(filepath=STOPWORDS_PATH):
    """
    加载停用词表。

    参数:
        filepath: 停用词文件路径，默认为项目根目录下的 stopwords.txt

    返回:
        set: 停用词集合（使用 set 查找效率为 O(1)）
    """
    stopwords = set()

    # 如果停用词文件存在，逐行读取
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                # 去除首尾空白字符后加入集合
                word = line.strip()
                if word:
                    stopwords.add(word)

    return stopwords


def read_text_file(filepath):
    """
    读取文本文件内容。

    参数:
        filepath: 文件的绝对路径

    返回:
        str: 文件文本内容

    异常:
        FileNotFoundError: 文件不存在时抛出
        UnicodeDecodeError: 编码错误时抛出
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def segment_text(text, stopwords=None):
    """
    对文本进行中文分词，并过滤无意义词。

    处理流程:
        1. 使用 jieba 精确模式分词
        2. 过滤停用词
        3. 过滤空格、换行等空白字符
        4. 过滤长度为1的无意义词

    参数:
        text: 待分词的文本字符串
        stopwords: 停用词集合，默认为 None（不过滤停用词）

    返回:
        list: 过滤后的词语列表
    """
    # 使用 jieba 精确模式分词（cut_all=False）
    words = jieba.lcut(text, cut_all=False)

    # 如果没有传入停用词集合，使用空集合（不过滤）
    if stopwords is None:
        stopwords = set()

    # 过滤规则
    filtered_words = []
    for word in words:
        # 规则1: 去除首尾空白
        word = word.strip()

        # 规则2: 跳过空字符串
        if not word:
            continue

        # 规则3: 跳过纯空白字符（空格、换行、制表符等）
        if word.isspace():
            continue

        # 规则4: 跳过长度为1的词（通常是单字，意义不大）
        if len(word) <= 1:
            continue

        # 规则5: 跳过停用词
        if word in stopwords:
            continue

        filtered_words.append(word)

    return filtered_words


def count_word_freq(words, top_n=None):
    """
    统计词频并返回结果。

    参数:
        words: 词语列表（由 segment_text 返回）
        top_n: 返回前 N 个高频词，默认为 None（返回全部）

    返回:
        dict: 词频字典，按频次降序排列，例如 {"数据": 20, "分析": 15}
    """
    # 使用 Counter 统计词频
    counter = Counter(words)

    # 取前 top_n 个高频词（如果指定了 top_n）
    if top_n is not None:
        most_common = counter.most_common(top_n)
    else:
        most_common = counter.most_common()

    # 将列表转换为字典
    return dict(most_common)


def process_file(filepath, top_n=None):
    """
    完整的文本处理流程：读取 → 分词 → 过滤 → 统计词频。

    这是对外暴露的主函数，供 app.py 调用。

    参数:
        filepath: 待处理的 txt 文件绝对路径
        top_n: 返回前 N 个高频词，默认为 None（返回全部）

    返回:
        dict: 词频字典，例如 {"数据": 20, "分析": 15}

    异常:
        FileNotFoundError: 文件不存在
        UnicodeDecodeError: 文件编码非 UTF-8
    """
    # 第一步: 加载停用词
    stopwords = load_stopwords()

    # 第二步: 读取文件内容
    text = read_text_file(filepath)

    # 第三步: 分词 + 过滤
    words = segment_text(text, stopwords)

    # 第四步: 统计词频
    word_freq = count_word_freq(words, top_n)

    return word_freq