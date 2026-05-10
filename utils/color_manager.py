# -*- coding: utf-8 -*-
"""
color_manager.py - 词云颜色系统集中管理模块

功能:
    1. 预设同色系渐变主题（blue/green/red/purple/orange/cyberpunk/forest）
    2. 用户自定义 HEX 颜色自动渐变生成
    3. 三种颜色模式：solid / preset_gradient / auto_gradient
    4. 统一的 color_func 生成接口
"""

import random
import re


# ========== HEX 颜色工具 ==========

def is_valid_hex(hex_str):
    if not hex_str:
        return False
    return bool(re.match(r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$', hex_str))


def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    if not is_valid_hex('#' + hex_str):
        raise ValueError(f'无效的 HEX 颜色格式: #{hex_str}，正确格式如 #ff0000 或 #f00')
    if len(hex_str) == 3:
        hex_str = ''.join([c * 2 for c in hex_str])
    return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
    return '#{:02X}{:02X}{:02X}'.format(
        max(0, min(255, int(r))),
        max(0, min(255, int(g))),
        max(0, min(255, int(b)))
    )


def adjust_brightness(r, g, b, factor):
    """
    调整 RGB 颜色亮度。

    factor > 1.0 变亮，factor < 1.0 变暗。
    """
    return (
        max(0, min(255, int(r * factor))),
        max(0, min(255, int(g * factor))),
        max(0, min(255, int(b * factor)))
    )


# ========== 预设渐变主题 ==========

PRESET_GRADIENTS = {
    'blue_gradient': {
        'label': '蓝色渐变',
        'colors': ['#0D47A1', '#1565C0', '#1E88E5', '#42A5F5', '#90CAF9'],
    },
    'green_gradient': {
        'label': '绿色渐变',
        'colors': ['#1B5E20', '#2E7D32', '#43A047', '#66BB6A', '#A5D6A7'],
    },
    'red_gradient': {
        'label': '红色渐变',
        'colors': ['#B71C1C', '#C62828', '#E53935', '#EF5350', '#EF9A9A'],
    },
    'purple_gradient': {
        'label': '紫色渐变',
        'colors': ['#4A148C', '#6A1B9A', '#8E24AA', '#BA68C8', '#E1BEE7'],
    },
    'orange_gradient': {
        'label': '橙色渐变',
        'colors': ['#E65100', '#EF6C00', '#F57C00', '#FF9800', '#FFCC80'],
    },
    'cyberpunk_gradient': {
        'label': '赛博朋克',
        'colors': ['#00FFFF', '#00BFFF', '#7B68EE', '#FF00FF', '#FF1493'],
    },
    'forest_gradient': {
        'label': '森林',
        'colors': ['#1B5E20', '#33691E', '#558B2F', '#7CB342', '#AED581'],
    },
}

VALID_GRADIENT_THEMES = list(PRESET_GRADIENTS.keys())

VALID_COLOR_MODES = ['solid', 'preset_gradient', 'auto_gradient']


# ========== 自动渐变生成 ==========

def generate_auto_gradient(base_hex):
    """
    根据基色 HEX 自动生成同色系渐变颜色池。

    生成 5 级亮度：darker / dark / base / light / lighter

    参数:
        base_hex: 基色 HEX 字符串，如 '#3366ff'

    返回:
        list[str]: 5 个 HEX 颜色字符串的列表
    """
    if not is_valid_hex(base_hex):
        raise ValueError(f'无效的基色: {base_hex}')

    r, g, b = hex_to_rgb(base_hex)

    gradient = [
        rgb_to_hex(*adjust_brightness(r, g, b, 0.4)),
        rgb_to_hex(*adjust_brightness(r, g, b, 0.65)),
        rgb_to_hex(r, g, b),
        rgb_to_hex(*adjust_brightness(r, g, b, 1.4)),
        rgb_to_hex(*adjust_brightness(r, g, b, 1.8)),
    ]

    return gradient


# ========== color_func 生成器 ==========

def make_pool_color_func(color_pool):
    """
    根据颜色池生成 color_func 闭包。

    每个词从颜色池中随机选择一个颜色，实现同色系随机渐变效果。

    参数:
        color_pool: list[str]，HEX 颜色字符串列表

    返回:
        callable: 可传给 WordCloud(color_func=...) 的函数
    """
    rgb_pool = []
    for hex_color in color_pool:
        if is_valid_hex(hex_color):
            rgb_pool.append(hex_to_rgb(hex_color))

    if not rgb_pool:
        rgb_pool = [(0, 0, 0)]

    def _color_func(word, font_size, position, orientation,
                    random_state=None, **kwargs):
        r, g, b = random.choice(rgb_pool)
        return f'rgb({r}, {g}, {b})'

    return _color_func


def make_solid_color_func(base_hex):
    """
    生成单色 color_func，带轻微亮度变化增加层次感。

    参数:
        base_hex: HEX 颜色字符串

    返回:
        callable
    """
    if not is_valid_hex(base_hex):
        base_hex = '#3366ff'

    r, g, b = hex_to_rgb(base_hex)

    def _color_func(word, font_size, position, orientation,
                    random_state=None, **kwargs):
        factor = random.uniform(0.75, 1.0)
        nr, ng, nb = adjust_brightness(r, g, b, factor)
        return f'rgb({nr}, {ng}, {nb})'

    return _color_func


def random_color_func(word, font_size, position, orientation,
                      random_state=None, **kwargs):
    r = random.randint(50, 230)
    g = random.randint(50, 230)
    b = random.randint(50, 230)
    return f'rgb({r}, {g}, {b})'


# ========== 颜色配置解析 ==========

def resolve_color_config(color_mode, gradient_theme='', base_color=''):
    """
    根据颜色模式解析出最终的词云颜色配置。

    三种模式:
        1. solid: 单色模式，使用 base_color，带轻微亮度变化
        2. preset_gradient: 预设渐变，使用 gradient_theme 指定颜色池
        3. auto_gradient: 自动渐变，根据 base_color 生成同色系渐变池

    参数:
        color_mode: 'solid' / 'preset_gradient' / 'auto_gradient'
        gradient_theme: 预设渐变主题名，如 'blue_gradient'
        base_color: HEX 颜色字符串，如 '#3366ff'

    返回:
        dict: 包含 color_func 的配置字典，可直接传给 WordCloud
    """
    if color_mode not in VALID_COLOR_MODES:
        color_mode = 'preset_gradient'

    if color_mode == 'preset_gradient':
        theme = PRESET_GRADIENTS.get(gradient_theme)
        if theme:
            return {'color_func': make_pool_color_func(theme['colors'])}
        return {'color_func': make_pool_color_func(
            PRESET_GRADIENTS['blue_gradient']['colors']
        )}

    if color_mode == 'auto_gradient':
        if base_color and is_valid_hex(base_color):
            pool = generate_auto_gradient(base_color)
            return {'color_func': make_pool_color_func(pool)}
        return {'color_func': make_pool_color_func(
            PRESET_GRADIENTS['blue_gradient']['colors']
        )}

    if color_mode == 'solid':
        if base_color and is_valid_hex(base_color):
            return {'color_func': make_solid_color_func(base_color)}
        return {'color_func': make_solid_color_func('#3366ff')}

    if base_color and is_valid_hex(base_color):
        return {'color_func': make_solid_color_func(base_color)}

    return {'color_func': make_pool_color_func(
        PRESET_GRADIENTS['blue_gradient']['colors']
    )}


def validate_color_params(color_mode, gradient_theme='', base_color=''):
    """
    验证并修正颜色参数，返回验证后的参数字典。

    参数:
        color_mode: 颜色模式
        gradient_theme: 预设渐变主题
        base_color: HEX 基色

    返回:
        tuple: (error_message, validated_params)
            error_message 为 None 表示验证通过
            validated_params 为修正后的参数字典
    """
    if color_mode not in VALID_COLOR_MODES:
        return (f'不支持的颜色模式，可选：{" / ".join(VALID_COLOR_MODES)}', None)

    if color_mode == 'preset_gradient' and gradient_theme not in VALID_GRADIENT_THEMES:
        return (f'不支持的渐变主题，可选：{" / ".join(VALID_GRADIENT_THEMES)}', None)

    if base_color and not is_valid_hex(base_color):
        return ('HEX 颜色格式不正确，如 #ff0000 或 #f00', None)

    if color_mode in ('solid', 'auto_gradient') and not base_color:
        base_color = '#3366ff'

    return (None, {
        'color_mode': color_mode,
        'gradient_theme': gradient_theme,
        'base_color': base_color,
    })


def get_random_pool_color(gradient_theme='', base_color='', color_mode='preset_gradient'):
    """
    根据颜色配置从颜色池中随机获取一个 RGBA 颜色元组。
    用于旋转词语叠加时的颜色获取。

    返回:
        tuple: (R, G, B, A) 颜色元组
    """
    if color_mode == 'preset_gradient':
        theme = PRESET_GRADIENTS.get(gradient_theme)
        if theme:
            hex_color = random.choice(theme['colors'])
            r, g, b = hex_to_rgb(hex_color)
            return (r, g, b, 220)
    elif color_mode == 'auto_gradient':
        if base_color and is_valid_hex(base_color):
            pool = generate_auto_gradient(base_color)
            hex_color = random.choice(pool)
            r, g, b = hex_to_rgb(hex_color)
            return (r, g, b, 220)
    elif color_mode == 'solid':
        if base_color and is_valid_hex(base_color):
            r, g, b = hex_to_rgb(base_color)
            factor = random.uniform(0.7, 1.0)
            return (*adjust_brightness(r, g, b, factor), 220)

    return (random.randint(50, 230), random.randint(50, 230),
            random.randint(50, 230), 220)
