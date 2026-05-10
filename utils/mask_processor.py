# -*- coding: utf-8 -*-
"""
mask_processor.py - 图片 mask 处理模块

功能:
    1. 读取上传的图片文件
    2. 转换为灰度图
    3. 根据阈值进行二值化处理
    4. 生成 numpy mask 数组供 WordCloud 使用

处理流程:
    上传图片 → Pillow 读取 → convert('L') 灰度化
    → numpy.array() → 阈值二值化 → mask

阈值逻辑:
    pixel > threshold  → 255（白色区域，允许生成词）
    pixel <= threshold → 0（黑色区域，禁止生成词）
"""

import os
import numpy as np
from PIL import Image


ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp'}


def validate_threshold(threshold, default=128):
    try:
        threshold = int(threshold)
    except (ValueError, TypeError):
        threshold = default
    if threshold < 0:
        threshold = 0
    elif threshold > 255:
        threshold = 255
    return threshold


def is_allowed_image(filename):
    """
    检查图片文件扩展名是否合法。

    参数:
        filename: 文件名

    返回:
        bool
    """
    if not filename:
        return False
    ext = filename.rsplit('.', 1)[-1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


def generate_mask(image_path, threshold=128):
    """
    根据图片和阈值生成词云 mask。

    处理流程:
        1. 使用 Pillow 读取图片
        2. 转换为灰度图（'L' 模式）
        3. 转为 numpy 数组
        4. 根据阈值二值化：
           - pixel > threshold → 255（白色，允许生成词）
           - pixel <= threshold → 0（黑色，禁止生成词）

    参数:
        image_path: 图片文件的绝对路径
        threshold: 灰度阈值，0~255，默认 128

    返回:
        numpy.ndarray: 二值化后的 mask 数组

    异常:
        FileNotFoundError: 图片文件不存在
        ValueError: 阈值超出范围 或 图片无法读取
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f'图片文件不存在: {image_path}')

    threshold = validate_threshold(threshold)

    try:
        img = Image.open(image_path)
    except Exception as e:
        raise ValueError(f'无法读取图片文件: {str(e)}')

    gray_img = img.convert('L')

    mask_array = np.array(gray_img)

    mask_array = np.where(mask_array > threshold, 255, 0)

    mask_array = mask_array.astype(np.uint8)

    return mask_array


def generate_grayscale_image(image_path, output_path, threshold=128, invert=False):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f'图片文件不存在: {image_path}')

    threshold = validate_threshold(threshold)

    try:
        img = Image.open(image_path)
    except Exception as e:
        raise ValueError(f'无法读取图片文件: {str(e)}')

    gray_img = img.convert('L')

    mask_array = np.array(gray_img)

    if invert:
        mask_array = 255 - mask_array

    mask_array = np.where(mask_array > threshold, 255, 0)

    mask_array = mask_array.astype(np.uint8)

    result_img = Image.fromarray(mask_array, mode='L')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result_img.save(output_path)

    return {
        'width': mask_array.shape[1],
        'height': mask_array.shape[0],
        'output_path': output_path
    }


def invert_grayscale_image(grayscale_path, output_path, threshold=128):
    if not os.path.exists(grayscale_path):
        raise FileNotFoundError(f'灰度图片不存在: {grayscale_path}')

    try:
        img = Image.open(grayscale_path)
    except Exception as e:
        raise ValueError(f'无法读取灰度图片: {str(e)}')

    gray_array = np.array(img.convert('L'))

    inverted = 255 - gray_array

    inverted = np.where(inverted > threshold, 255, 0)

    inverted = inverted.astype(np.uint8)

    result_img = Image.fromarray(inverted, mode='L')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result_img.save(output_path)

    return {
        'width': inverted.shape[1],
        'height': inverted.shape[0],
        'output_path': output_path
    }


def get_mask_preview_info(image_path, threshold=128):
    """
    获取 mask 预览信息（用于前端展示）。

    返回 mask 的基本属性，便于前端调试和展示。

    参数:
        image_path: 图片文件的绝对路径
        threshold: 灰度阈值

    返回:
        dict: 包含 width, height, white_ratio 等信息
    """
    mask = generate_mask(image_path, threshold)
    total_pixels = mask.size
    white_pixels = np.count_nonzero(mask)
    white_ratio = round(white_pixels / total_pixels * 100, 1) if total_pixels > 0 else 0

    return {
        'width': mask.shape[1],
        'height': mask.shape[0],
        'white_ratio': white_ratio
    }
