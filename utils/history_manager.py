# -*- coding: utf-8 -*-
"""
history_manager.py - 历史记录管理模块

功能:
    管理词云生成历史记录，使用本地 JSON 文件存储。
    所有读写 history.json 的操作集中在此文件中。

对外暴露的函数:
    save_history(record)     - 保存一条历史记录
    load_history()           - 加载所有历史记录
    delete_history(record_id)- 删除指定历史记录
    get_history_by_id(record_id) - 根据 id 获取一条记录
"""

import os
import json
import uuid
from datetime import datetime


# history.json 文件路径：项目根目录下的 data/history.json
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
HISTORY_FILE = os.path.join(DATA_DIR, 'history.json')


def _ensure_data_dir():
    """确保 data 目录存在。"""
    os.makedirs(DATA_DIR, exist_ok=True)


def _read_json():
    """
    安全读取 JSON 文件。

    如果文件不存在或内容为空，返回空列表。
    如果文件内容损坏，也返回空列表（避免崩溃）。

    返回:
        list: 历史记录列表
    """
    _ensure_data_dir()

    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        # 文件损坏时返回空列表，避免程序崩溃
        return []


def _write_json(data):
    """
    安全写入 JSON 文件。

    使用"先写临时文件再重命名"的策略，
    避免写入过程中断电或崩溃导致文件损坏。

    参数:
        data: 要写入的数据（列表）
    """
    _ensure_data_dir()

    # 先写入临时文件
    temp_file = HISTORY_FILE + '.tmp'
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 重命名临时文件为正式文件（原子操作）
    os.replace(temp_file, HISTORY_FILE)


def save_history(record):
    """
    保存一条历史记录。

    自动生成 id 和 time 字段，将记录追加到 history.json。

    参数:
        record: 字典，包含以下字段:
            - word_freq: 词频字典
            - params: 词云参数字典
            - filename: 原始文件名

    返回:
        str: 新生成的历史记录 id
    """
    # 读取现有记录
    history = _read_json()

    # 生成唯一 id 和时间戳
    record_id = uuid.uuid4().hex[:12]
    record_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 构建完整记录
    new_record = {
        'id': record_id,
        'time': record_time,
        'filename': record.get('filename', ''),
        'word_freq': record.get('word_freq', {}),
        'params': record.get('params', {})
    }

    # 追加到列表开头（最新的在前）
    history.insert(0, new_record)

    # 写入文件
    _write_json(history)

    return record_id


def load_history():
    """
    加载所有历史记录。

    返回:
        list: 历史记录列表，按时间倒序排列（最新在前）
    """
    return _read_json()


def delete_history(record_id):
    """
    删除指定 id 的历史记录。

    参数:
        record_id: 要删除的记录 id

    返回:
        bool: 是否成功删除（True=找到并删除，False=未找到）
    """
    history = _read_json()

    # 过滤掉指定 id 的记录
    new_history = [r for r in history if r.get('id') != record_id]

    if len(new_history) == len(history):
        # 没有找到要删除的记录
        return False

    _write_json(new_history)
    return True


def get_history_by_id(record_id):
    """
    根据 id 获取一条历史记录。

    参数:
        record_id: 记录 id

    返回:
        dict 或 None: 找到则返回记录字典，未找到返回 None
    """
    history = _read_json()

    for record in history:
        if record.get('id') == record_id:
            return record

    return None