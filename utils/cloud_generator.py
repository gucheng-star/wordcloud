# -*- coding: utf-8 -*-
"""
cloud_generator.py - 词云图生成模块

功能:
    1. 根据词频字典生成词云 PNG 图片
    2. 自动检测系统中文字体（不依赖前端传 font_path）
    3. 支持多种颜色模式：HEX 自定义色、预设主题、随机彩色
    4. 支持自定义最大/最小字号
    5. 支持自定义词云宽高（分辨率）
"""

import os
import random
import re
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
    windows_fonts = [
        'C:/Windows/Fonts/msyh.ttc',
        'C:/Windows/Fonts/msyhbd.ttc',
        'C:/Windows/Fonts/simhei.ttf',
        'C:/Windows/Fonts/simsun.ttc',
    ]

    linux_fonts = [
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
    ]

    for font_path in windows_fonts + linux_fonts:
        if os.path.exists(font_path):
            return font_path

    return None


# ========== 颜色主题 ==========

COLOR_THEMES = {
    'blue': 'Blues',
    'green': 'Greens',
    'red': 'Reds',
    'purple': 'Purples',
}

VALID_THEMES = list(COLOR_THEMES.keys()) + ['random']


def is_valid_hex(hex_str):
    """
    校验 HEX 颜色字符串是否合法。

    支持格式: #RGB 或 #RRGGBB（不区分大小写）

    返回:
        bool
    """
    if not hex_str:
        return False
    return bool(re.match(r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$', hex_str))


def hex_to_rgb(hex_str):
    """
    将 HEX 颜色字符串转换为 (R, G, B) 元组。

    参数:
        hex_str: 如 '#ff0000' 或 '#f00'

    返回:
        tuple: (R, G, B)，每个值 0-255
    """
    hex_str = hex_str.lstrip('#')
    if not is_valid_hex('#' + hex_str):
        raise ValueError(f'无效的 HEX 颜色格式: #{hex_str}，正确格式如 #ff0000 或 #f00')
    if len(hex_str) == 3:
        hex_str = ''.join([c * 2 for c in hex_str])
    return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))


def hex_color_func(hex_str):
    """
    基于 HEX 颜色生成 color_func 闭包。

    效果: 以 HEX 颜色为主色调，添加轻微透明度/亮度变化，
    让词云看起来有层次感而不是完全同色。

    参数:
        hex_str: HEX 颜色字符串，如 '#3366ff'

    返回:
        callable: 可传给 WordCloud(color_func=...) 的函数
    """
    r, g, b = hex_to_rgb(hex_str)

    def _color_func(word, font_size, position, orientation,
                    random_state=None, **kwargs):
        factor = random.uniform(0.7, 1.0)
        nr = min(255, int(r * factor))
        ng = min(255, int(g * factor))
        nb = min(255, int(b * factor))
        return f'rgb({nr}, {ng}, {nb})'

    return _color_func


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


def resolve_color_config(color_theme, color_hex):
    """
    根据颜色主题和 HEX 输入，解析出最终的词云颜色配置。

    优先级:
        1. 如果 color_hex 非空且合法 → 使用 HEX 自定义色
        2. 如果 color_theme 为 'random' → 随机颜色
        3. 如果 color_theme 为预设主题 → 使用 colormap

    参数:
        color_theme: 预设主题名称
        color_hex: HEX 颜色字符串（可为空）

    返回:
        dict: 包含 colormap 或 color_func 的配置字典
    """
    if color_hex and is_valid_hex(color_hex):
        return {'color_func': hex_color_func(color_hex)}

    if color_theme == 'random':
        return {'color_func': random_color_func}

    if color_theme in COLOR_THEMES:
        return {'colormap': COLOR_THEMES[color_theme]}

    return {'colormap': 'Blues'}


# ========== 词云生成主函数 ==========

def generate_wordcloud(word_freq, output_path,
                       max_font_size=80, min_font_size=20,
                       color_theme='blue', color_hex='',
                       width=800, height=600):
    """
    根据词频字典生成词云图片并保存。

    参数:
        word_freq: 词频字典，例如 {"数据": 20, "分析": 15}
        output_path: 输出图片的绝对路径
        max_font_size: 最大字号，默认 80
        min_font_size: 最小字号，默认 20
        color_theme: 颜色主题，默认 'blue'
        color_hex: HEX 自定义颜色，如 '#3366ff'，优先于 color_theme
        width: 词云图片宽度（像素），默认 800
        height: 词云图片高度（像素），默认 600

    返回:
        str: 生成的图片文件名

    异常:
        ValueError: 词频字典为空 或 HEX 颜色格式不合法
        RuntimeError: 找不到中文字体
    """
    if not word_freq:
        raise ValueError('词频数据为空，无法生成词云')

    if color_hex and not is_valid_hex(color_hex):
        raise ValueError(f'HEX 颜色格式不合法: {color_hex}，正确格式如 #ff0000 或 #f00')

    font_path = get_chinese_font_path()
    if not font_path:
        raise RuntimeError('未找到中文字体，请安装中文字体（如微软雅黑）')

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    wc_params = {
        'font_path': font_path,
        'width': width,
        'height': height,
        'background_color': 'white',
        'max_font_size': max_font_size,
        'min_font_size': min_font_size,
        'max_words': 200,
        'collocations': False,
    }

    color_config = resolve_color_config(color_theme, color_hex)
    wc_params.update(color_config)

    wc = WordCloud(**wc_params)
    wc.generate_from_frequencies(word_freq)
    wc.to_file(output_path)

    return os.path.basename(output_path)
