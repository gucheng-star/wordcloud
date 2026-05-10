# -*- coding: utf-8 -*-
"""
cloud_generator.py - 词云图生成模块

功能:
    1. 根据词频字典生成词云 PNG 图片
    2. 自动检测系统中文字体（不依赖前端传 font_path）
    3. 支持三种颜色模式：solid / preset_gradient / auto_gradient
    4. 支持自定义最大/最小字号
    5. 支持自定义词云宽高（分辨率）
    6. 支持布局风格：classic / dynamic / poster / vertical_mix
"""

import os
import random
from wordcloud import WordCloud
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from utils.color_manager import (
    is_valid_hex,
    resolve_color_config,
    get_random_pool_color,
)


FONT_FAMILIES = {
    'yahei': {
        'label': '微软雅黑',
        'css_name': 'Microsoft YaHei',
        'windows_path': 'C:/Windows/Fonts/msyh.ttc',
        'linux_paths': [
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        ],
        'description': '现代清晰，通用首选',
    },
    'simhei': {
        'label': '黑体',
        'css_name': 'SimHei',
        'windows_path': 'C:/Windows/Fonts/simhei.ttf',
        'linux_paths': [],
        'description': '粗犷有力，标题海报',
    },
    'simsun': {
        'label': '宋体',
        'css_name': 'SimSun',
        'windows_path': 'C:/Windows/Fonts/simsun.ttc',
        'linux_paths': [],
        'description': '经典正式，传统排版',
    },
    'simkai': {
        'label': '楷体',
        'css_name': 'KaiTi',
        'windows_path': 'C:/Windows/Fonts/simkai.ttf',
        'linux_paths': [],
        'description': '书法艺术，文化风格',
    },
    'simfang': {
        'label': '仿宋',
        'css_name': 'FangSong',
        'windows_path': 'C:/Windows/Fonts/simfang.ttf',
        'linux_paths': [],
        'description': '优雅传统，古典韵味',
    },
}

VALID_FONT_FAMILIES = list(FONT_FAMILIES.keys())

LINUX_FALLBACK_PATHS = [
    '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
    '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
]


def resolve_font_path(font_family='yahei'):
    """
    根据字体族名称解析字体文件路径。

    优先使用指定字体，找不到时按优先级回退。

    参数:
        font_family: 字体族键名，如 'yahei'、'simhei'

    返回:
        str: 字体文件路径，如果找不到则返回 None
    """
    font_config = FONT_FAMILIES.get(font_family)
    if font_config:
        if os.path.exists(font_config['windows_path']):
            return font_config['windows_path']
        for linux_path in font_config.get('linux_paths', []):
            if os.path.exists(linux_path):
                return linux_path

    for fallback in LINUX_FALLBACK_PATHS:
        if os.path.exists(fallback):
            return fallback

    for key in FONT_FAMILIES:
        wp = FONT_FAMILIES[key]['windows_path']
        if os.path.exists(wp):
            return wp

    return None


def get_chinese_font_path():
    """
    自动检测系统中文字体路径（默认微软雅黑）。

    返回:
        str: 字体文件路径，如果找不到则返回 None
    """
    return resolve_font_path('yahei')


LAYOUT_STYLES = {
    'classic': {
        'prefer_horizontal': 0.95,
        'rotate_steps': 2,
        'description': '传统布局，大部分水平',
    },
    'dynamic': {
        'prefer_horizontal': 0.7,
        'rotate_steps': 4,
        'description': '部分词随机旋转，增强视觉动感',
    },
    'poster': {
        'prefer_horizontal': 0.5,
        'rotate_steps': 6,
        'description': '宣传海报风格，增加垂直词和方向混排',
    },
    'vertical_mix': {
        'prefer_horizontal': 0.3,
        'rotate_steps': 2,
        'description': '水平与垂直混合布局',
    },
}

VALID_LAYOUT_STYLES = list(LAYOUT_STYLES.keys())


def resolve_layout_config(layout_style):
    if layout_style not in LAYOUT_STYLES:
        layout_style = 'classic'
    config = LAYOUT_STYLES[layout_style]
    return {
        'prefer_horizontal': config['prefer_horizontal'],
        'rotate_steps': config.get('rotate_steps', 2),
    }


def generate_wordcloud(word_freq, output_path,
                       max_font_size=80, min_font_size=20,
                       color_mode='preset_gradient',
                       gradient_theme='blue_gradient',
                       base_color='#3366ff',
                       width=800, height=600,
                       mask=None, layout_style='classic',
                       font_family='yahei'):
    """
    根据词频字典生成词云图片并保存。

    参数:
        word_freq: 词频字典，例如 {"数据": 20, "分析": 15}
        output_path: 输出图片的绝对路径
        max_font_size: 最大字号，默认 80
        min_font_size: 最小字号，默认 20
        color_mode: 颜色模式，'solid' / 'preset_gradient' / 'auto_gradient'
        gradient_theme: 预设渐变主题，如 'blue_gradient'
        base_color: HEX 基色，如 '#3366ff'
        width: 词云图片宽度（像素），默认 800
        height: 词云图片高度（像素），默认 600
        mask: numpy 数组形式的 mask，如果提供则忽略 width/height
        layout_style: 布局风格，可选 classic/dynamic/poster/vertical_mix
        font_family: 字体族，可选 yahei/simhei/simsun/simkai/simfang

    返回:
        str: 生成的图片文件名

    异常:
        ValueError: 词频字典为空 或 HEX 颜色格式不合法
        RuntimeError: 找不到中文字体
    """
    if not word_freq:
        raise ValueError('词频数据为空，无法生成词云')

    if base_color and not is_valid_hex(base_color):
        raise ValueError(f'HEX 颜色格式不合法: {base_color}，正确格式如 #ff0000 或 #f00')

    font_path = resolve_font_path(font_family)
    if not font_path:
        raise RuntimeError('未找到中文字体，请安装中文字体（如微软雅黑）')

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    layout_config = resolve_layout_config(layout_style)

    wc_params = {
        'font_path': font_path,
        'background_color': 'white',
        'max_font_size': max_font_size,
        'min_font_size': min_font_size,
        'max_words': 200,
        'collocations': False,
        'prefer_horizontal': layout_config['prefer_horizontal'],
    }

    if mask is not None:
        wc_params['mask'] = mask
        wc_params['contour_width'] = 0
    else:
        wc_params['width'] = width
        wc_params['height'] = height

    color_config = resolve_color_config(color_mode, gradient_theme, base_color)
    wc_params.update(color_config)

    wc = WordCloud(**wc_params)
    wc.generate_from_frequencies(word_freq)
    wc.to_file(output_path)

    if layout_style in ('dynamic', 'poster'):
        _add_rotated_words(output_path, word_freq, font_path,
                           max_font_size, min_font_size,
                           color_mode, gradient_theme, base_color,
                           layout_style)

    return os.path.basename(output_path)


def _add_rotated_words(image_path, word_freq, font_path,
                       max_font_size, min_font_size,
                       color_mode, gradient_theme, base_color,
                       layout_style):
    """
    在已生成的词云图片上叠加额外旋转词语，增强视觉动感。

    仅对 dynamic 和 poster 布局风格生效。
    - dynamic: 少量词语以 ±30° 旋转叠加
    - poster: 更多词语以 ±45° 旋转叠加，增加海报感
    """
    try:
        img = Image.open(image_path).convert('RGBA')
    except Exception:
        return

    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

    if layout_style == 'dynamic':
        word_count = min(5, len(sorted_words) // 4)
        angles = [-30, 30, -20, 20, -15]
    elif layout_style == 'poster':
        word_count = min(8, len(sorted_words) // 3)
        angles = [-45, 45, -30, 30, -60, 60, -15, 15]
    else:
        return

    if word_count == 0:
        return

    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    img_w, img_h = img.size

    start_idx = max(3, len(sorted_words) // 5)
    candidates = sorted_words[start_idx:start_idx + word_count * 3]

    if not candidates:
        return

    selected = candidates[:word_count]

    for i, (word, freq) in enumerate(selected):
        font_size = int(min_font_size + (max_font_size - min_font_size) * 0.3)
        font_size = max(min_font_size, min(font_size, max_font_size // 2))

        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            continue

        color = get_random_pool_color(gradient_theme, base_color, color_mode)

        angle = angles[i % len(angles)]

        bbox = draw.textbbox((0, 0), word, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        margin = max(tw, th) + 10
        x = random.randint(margin, max(margin, img_w - margin))
        y = random.randint(margin, max(margin, img_h - margin))

        word_img = Image.new('RGBA', (tw + 20, th + 20), (0, 0, 0, 0))
        word_draw = ImageDraw.Draw(word_img)
        word_draw.text((10 - bbox[0], 10 - bbox[1]), word, fill=color, font=font)

        rotated = word_img.rotate(angle, resample=Image.BICUBIC, expand=True)

        rx = x - rotated.width // 2
        ry = y - rotated.height // 2

        overlay.paste(rotated, (rx, ry), rotated)

    result = Image.alpha_composite(img, overlay)
    result.convert('RGB').save(image_path)


def overlay_wordcloud_with_image(wordcloud_path, mask_image_path, output_path, opacity=0.3):
    """
    将词云图片与原始 mask 图片进行叠化混合。

    效果: 在词云上叠加半透明的原始图片，帮助用户确认词云形状与输入图片的匹配程度。

    参数:
        wordcloud_path: 词云图片路径
        mask_image_path: 原始 mask 图片路径
        output_path: 叠化后输出路径
        opacity: 原图叠化透明度，0.0~1.0，默认 0.3
            0.0 = 完全透明（只显示词云）
            1.0 = 完全不透明（只显示原图）

    返回:
        str: 输出文件名
    """
    opacity = max(0.0, min(1.0, float(opacity)))

    wc_img = Image.open(wordcloud_path).convert('RGBA')
    mask_img = Image.open(mask_image_path).convert('RGBA')

    mask_img = mask_img.resize(wc_img.size, Image.LANCZOS)

    wc_arr = np.array(wc_img).astype(np.float32)
    mask_arr = np.array(mask_img).astype(np.float32)

    blended = wc_arr * (1 - opacity) + mask_arr * opacity
    blended = np.clip(blended, 0, 255).astype(np.uint8)

    result = Image.fromarray(blended, 'RGBA')
    result.save(output_path)

    return os.path.basename(output_path)
