# -*- coding: utf-8 -*-
"""
中文词云工具 - Flask 主程序
运行方式: python app.py
浏览器访问: http://127.0.0.1:3326


=== API 接口规范 ===

1. 首页
   方法: GET
   路径: /
   参数: 无
   返回: HTML 页面（templates/index.html）

2. 上传 txt 文件
   方法: POST
   路径: /upload_txt
   参数: file（表单字段，.txt 文件）
   返回: JSON
     成功: {"status": "success", "filename": "xxx.txt", "original_name": "原始名.txt", "message": "上传成功！"}
     失败: {"status": "error", "message": "错误原因"}

3. 处理文本（分词 + 词频统计）
   方法: POST
   路径: /process_text
   参数: filename（JSON 字段，已上传的 txt 文件名）
   返回: JSON
     成功: {"status": "success", "word_freq": {"数据": 20, "分析": 15}}
     失败: {"status": "error", "message": "错误原因"}

4. 过滤词（用户自定义过滤）
   方法: POST
   路径: /filter_words
   参数: word_freq（词频字典）, remove_words（要移除的词列表）
   返回: JSON
     成功: {"status": "success", "filtered_word_freq": {"分析": 15}}
     失败: {"status": "error", "message": "错误原因"}
"""

import os
import uuid
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from utils.text_processor import process_file
from utils.filter_processor import filter_word_freq

# 创建 Flask 应用实例
app = Flask(__name__)

# 配置上传文件夹路径
# 使用 os.path.join 确保跨平台兼容
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 允许上传的文件扩展名（白名单，只允许 txt 文件）
ALLOWED_EXTENSIONS = {'txt'}

# 最大上传文件大小限制（16MB）
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


def allowed_file(filename):
    """
    检查上传的文件扩展名是否在白名单中。

    参数:
        filename: 上传文件的原始文件名

    返回:
        bool: 文件扩展名是否允许
    """
    # 使用 rsplit 从右侧分割一次，获取文件扩展名
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_safe_filename(original_filename):
    """
    生成安全的文件名：使用 UUID + 原始扩展名。

    为什么不用 secure_filename？
    secure_filename 会剥离所有非 ASCII 字符，
    导致中文文件名（如"测试文件.txt"）变成无意义的 "txt"。
    使用 UUID 替代文件名部分，既保证安全又保留扩展名。

    参数:
        original_filename: 用户上传的原始文件名

    返回:
        str: 安全的新文件名，例如 "a1b2c3d4.txt"
    """
    # 提取原始文件的扩展名（小写）
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    # 使用 UUID 生成唯一文件名，避免冲突和路径遍历
    safe_name = uuid.uuid4().hex[:8] + '.' + ext if ext else uuid.uuid4().hex[:8]
    return safe_name


def is_safe_filename(filename):
    """
    检查文件名是否安全（不含路径分隔符）。

    用于 /process_text 接口校验用户传入的 filename，
    防止路径遍历攻击（如 "../../../etc/passwd"）。

    参数:
        filename: 待检查的文件名

    返回:
        bool: 文件名是否安全
    """
    # 文件名不能为空
    if not filename:
        return False
    # 文件名不能包含路径分隔符
    if os.path.sep in filename or '/' in filename or '\\' in filename:
        return False
    # 文件名不能包含 ..
    if '..' in filename:
        return False
    return True


# 确保 uploads 文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def index():
    """首页路由：返回上传页面"""
    return render_template('index.html')


@app.route('/upload_txt', methods=['POST'])
def upload_file():
    """
    上传 txt 文件接口。

    请求:
        POST /upload_txt
        表单字段: file（.txt 文件）

    返回 JSON:
        成功: {"status": "success", "filename": "a1b2c3d4.txt", "original_name": "原始名.txt", "message": "上传成功！"}
        失败: {"status": "error", "message": "错误原因"}
    """
    # 检查请求中是否有文件
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '没有找到文件，请选择文件后上传'})

    file = request.files['file']

    # 检查是否选择了文件
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '未选择任何文件'})

    # 验证文件扩展名（使用原始文件名校验）
    if not allowed_file(file.filename):
        return jsonify({'status': 'error', 'message': '只允许上传 .txt 文件'})

    # 生成安全的文件名（UUID + 扩展名），解决中文文件名问题
    filename = generate_safe_filename(file.filename)

    # 保存文件到 uploads 文件夹
    try:
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'文件保存失败：{str(e)}'})

    # 返回成功响应，同时返回原始文件名供前端展示
    return jsonify({
        'status': 'success',
        'filename': filename,
        'original_name': file.filename,
        'message': '上传成功！'
    })


@app.route('/process_text', methods=['POST'])
def process_text():
    """
    处理文本接口：对已上传的 txt 文件进行分词和词频统计。

    请求:
        POST /process_text
        JSON 参数: {"filename": "xxx.txt"}

    返回 JSON:
        成功: {"status": "success", "word_freq": {"数据": 20, "分析": 15}}
        失败: {"status": "error", "message": "错误原因"}
    """
    # 获取请求中的 JSON 数据
    data = request.get_json()

    # 检查是否提供了 filename 参数
    if not data or 'filename' not in data:
        return jsonify({'status': 'error', 'message': '缺少 filename 参数'})

    filename = data['filename']

    # 安全检查：防止路径遍历攻击
    if not is_safe_filename(filename):
        return jsonify({'status': 'error', 'message': '文件名无效'})

    # 构建文件的完整路径
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # 检查文件是否存在
    if not os.path.exists(filepath):
        return jsonify({'status': 'error', 'message': '文件不存在，请先上传'})

    # 检查文件扩展名
    if not allowed_file(filename):
        return jsonify({'status': 'error', 'message': '只支持 .txt 文件'})

    try:
        # 调用文本处理模块
        word_freq = process_file(filepath)
        return jsonify({
            'status': 'success',
            'word_freq': word_freq
        })
    except UnicodeDecodeError:
        return jsonify({'status': 'error', 'message': '文件编码错误，请使用 UTF-8 编码的文本文件'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'处理失败：{str(e)}'})


@app.route('/filter_words', methods=['POST'])
def filter_words():
    """
    过滤词接口：根据用户选择的词，从词频结果中移除这些词。

    请求:
        POST /filter_words
        JSON 参数:
            word_freq: 词频字典，例如 {"数据": 20, "分析": 15}
            remove_words: 要移除的词列表，例如 ["数据"]

    返回 JSON:
        成功: {"status": "success", "filtered_word_freq": {"分析": 15}}
        失败: {"status": "error", "message": "错误原因"}
    """
    # 获取请求中的 JSON 数据
    data = request.get_json()

    # 检查是否提供了必要参数
    if not data:
        return jsonify({'status': 'error', 'message': '请求体不能为空'})

    if 'word_freq' not in data:
        return jsonify({'status': 'error', 'message': '缺少 word_freq 参数'})

    if 'remove_words' not in data:
        return jsonify({'status': 'error', 'message': '缺少 remove_words 参数'})

    word_freq = data['word_freq']
    remove_words = data['remove_words']

    # 类型校验：word_freq 必须是字典
    if not isinstance(word_freq, dict):
        return jsonify({'status': 'error', 'message': 'word_freq 必须是字典格式'})

    # 类型校验：remove_words 必须是列表
    if not isinstance(remove_words, list):
        return jsonify({'status': 'error', 'message': 'remove_words 必须是列表格式'})

    # 调用过滤模块
    filtered = filter_word_freq(word_freq, remove_words)

    return jsonify({
        'status': 'success',
        'filtered_word_freq': filtered
    })


if __name__ == '__main__':
    # 通过环境变量控制调试模式，默认关闭
    # 开发时设置: set FLASK_DEBUG=True
    # 生产环境: 不设置或设为 False
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='127.0.0.1', port=3326, debug=debug)