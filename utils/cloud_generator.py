# -*- coding: utf-8 -*-
"""
cloud_generator.py - 词云图生成模块

功能:
    1. 根据词频字典生成词云 PNG 图片
    2. 自动检测系统中文字体（不依赖前端传 font_path）
    3. 支持多种颜色主题
    4. 支持自定义最大/最小字号
"""

import os
import random
from wordcloud import WordCloud
import matplotlib.cm as cm


# ========== 字体路径自动检测 ==========

def get_chinese_font_path():
    """
    自动检测系统中文字体路径。

    检测顺序:
        1. Windows: C:/Windows/Fonts/msyh.ttc（微软雅黑）
        2. Linux: 常见中文字体路径

    返回:
        str: 字体文件路径，如果找不到则返回 None
    """
    # Windows 常见中文字体
    windows_fonts = [
        'C:/Windows/Fonts/msyh.ttc',      # 微软雅黑
        'C:/Windows/Fonts/msyhbd.ttc',     # 微软雅黑粗体
        'C:/Windows/Fonts/simhei.ttf',     # 黑体
        'C:/Windows/Fonts/simsun.ttc',     # 宋体
    ]

    # Linux 常见中文字体
    linux_fonts = [
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',       # 文泉驿正黑
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',     # 文泉驿微米黑
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',  # Noto Sans CJK
        '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',  # Droid
    ]

    # 按顺序检测，找到第一个存在的字体
    for font_path in windows_fonts + linux_fonts:
        if os.path.exists(font_path):
            return font_path

    return None


# ========== 颜色主题 ==========

# 预定义的颜色主题映射
COLOR_THEMES = {
    'blue': 'Blues',
    'green': 'Greens',
    'red': 'Reds',
    'purple': 'Purples',
}


def get_color_func(theme):
    """
    根据主题名称返回颜色配置。

    参数:
        theme: 颜色主题名称，支持 'blue'/'green'/'red'/'purple'/'random'

    返回:
        str 或 callable:
            - 如果是预定义主题，返回 matplotlib colormap 名称
            - 如果是 'random'，返回随机颜色函数
    """
    if theme in COLOR_THEMES:
        # 返回 matplotlib 的 colormap 名称
        return COLOR_THEMES[theme]

    # random 主题：使用随机颜色
    return 'random'


def random_color_func(word, font_size, position, orientation,
                      random_state=None, **kwargs):
    """
    随机颜色函数，用于 WordCloud 的 color_func 参数。

    生成随机的 RGB 颜色，确保颜色鲜艳（避免太暗或太亮）。
    """
    r = random.randint(50, 230)
    g = random.randint(50, 230)
    b = random.randint(50, 230)
    return f'rgb({r}, {g}, {b})'


# ========== 词云生成主函数 ==========

def generate_wordcloud(word_freq, output_path,
                       max_font_size=80, min_font_size=20,
                       color_theme='blue'):
    """
    根据词频字典生成词云图片并保存。

    参数:
        word_freq: 词频字典，例如 {"数据": 20, "分析": 15}
        output_path: 输出图片的绝对路径（例如 .../outputs/wordcloud.png）
        max_font_size: 最大字号，默认 80
        min_font_size: 最小字号，默认 20
        color_theme: 颜色主题，默认 'blue'

    返回:
        str: 生成的图片文件名

    异常:
        ValueError: 词频字典为空
        RuntimeError: 找不到中文字体
    """
    # 检查词频是否为空
    if not word_freq:
        raise ValueError('词频数据为空，无法生成词云')

    # 获取中文字体路径
    font_path = get_chinese_font_path()
    if not font_path:
        raise RuntimeError('未找到中文字体，请安装中文字体（如微软雅黑）')

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 构建词云参数
    wc_params = {
        'font_path': font_path,
        'width': 800,
        'height': 600,
        'background_color': 'white',
        'max_font_size': max_font_size,
        'min_font_size': min_font_size,
        'max_words': 200,
        'collocations': False,
    }

    # 根据颜色主题设置颜色
    theme = get_color_func(color_theme)
    if theme == 'random':
        wc_params['color_func'] = random_color_func
    else:
        wc_params['colormap'] = theme

    # 创建 WordCloud 实例
    wc = WordCloud(**wc_params)

    # 从词频字典生成词云
    wc.generate_from_frequencies(word_freq)

    # 保存为 PNG 图片
    wc.to_file(output_path)

    # 返回文件名
    return os.path.basename(output_path)