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
   返回: HTML 页面

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
     成功: {"status": "success", "session_id": "abc123", "word_freq": {...}}
     失败: {"status": "error", "message": "错误原因"}

4. 过滤词（用户自定义过滤）
   方法: POST
   路径: /filter_words
   参数: session_id + remove_words（JSON）
   返回: JSON
     成功: {"status": "success", "word_freq": {...}}
     失败: {"status": "error", "message": "错误原因"}

5. 生成词云
   方法: POST
   路径: /generate_wordcloud
   参数: session_id + max_font_size + min_font_size + color_theme（JSON）
   返回: JSON
     成功: {"status": "success", "image_url": "/outputs/wordcloud_xxx.png"}
     失败: {"status": "error", "message": "错误原因"}
"""

import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from utils.text_processor import process_file
from utils.filter_processor import filter_word_freq
from utils.cloud_generator import generate_wordcloud

# 创建 Flask 应用实例
app = Flask(__name__)

# 配置上传文件夹路径
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 配置词云输出文件夹路径
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# 允许上传的文件扩展名（白名单，只允许 txt 文件）
ALLOWED_EXTENSIONS = {'txt'}

# 最大上传文件大小限制（16MB）
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ========== 内存缓存：用 session_id 存储词频数据 ==========
# 结构: { "abc123": {"word_freq": {...}}, ... }
word_freq_cache = {}


def allowed_file(filename):
    """检查上传的文件扩展名是否在白名单中。"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_safe_filename(original_filename):
    """生成安全的文件名：使用 UUID + 原始扩展名。"""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    safe_name = uuid.uuid4().hex[:8] + '.' + ext if ext else uuid.uuid4().hex[:8]
    return safe_name


def is_safe_filename(filename):
    """检查文件名是否安全（不含路径分隔符）。"""
    if not filename:
        return False
    if os.path.sep in filename or '/' in filename or '\\' in filename:
        return False
    if '..' in filename:
        return False
    return True


# 确保必要文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route('/')
def index():
    """首页路由：返回上传页面"""
    return render_template('index.html')


@app.route('/upload_txt', methods=['POST'])
def upload_file():
    """
    上传 txt 文件接口。

    返回 JSON:
        成功: {"status": "success", "filename": "xxx.txt", "original_name": "原始名.txt", "message": "上传成功！"}
        失败: {"status": "error", "message": "错误原因"}
    """
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '没有找到文件，请选择文件后上传'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'status': 'error', 'message': '未选择任何文件'})

    if not allowed_file(file.filename):
        return jsonify({'status': 'error', 'message': '只允许上传 .txt 文件'})

    filename = generate_safe_filename(file.filename)

    try:
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'文件保存失败：{str(e)}'})

    return jsonify({
        'status': 'success',
        'filename': filename,
        'original_name': file.filename,
        'message': '上传成功！'
    })


@app.route('/process_text', methods=['POST'])
def process_text():
    """
    处理文本接口：分词 + 词频统计 + 存入缓存。

    返回 JSON:
        成功: {"status": "success", "session_id": "abc123", "word_freq": {...}}
        失败: {"status": "error", "message": "错误原因"}
    """
    data = request.get_json()

    if not data or 'filename' not in data:
        return jsonify({'status': 'error', 'message': '缺少 filename 参数'})

    filename = data['filename']

    if not is_safe_filename(filename):
        return jsonify({'status': 'error', 'message': '文件名无效'})

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return jsonify({'status': 'error', 'message': '文件不存在，请先上传'})

    if not allowed_file(filename):
        return jsonify({'status': 'error', 'message': '只支持 .txt 文件'})

    try:
        word_freq = process_file(filepath)

        # 生成 session_id，存入内存缓存
        session_id = uuid.uuid4().hex[:8]
        word_freq_cache[session_id] = {'word_freq': word_freq}

        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'word_freq': word_freq
        })
    except UnicodeDecodeError:
        return jsonify({'status': 'error', 'message': '文件编码错误，请使用 UTF-8 编码的文本文件'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'处理失败：{str(e)}'})


@app.route('/filter_words', methods=['POST'])
def filter_words():
    """
    过滤词接口：从缓存中读取词频，删除指定词，更新缓存。

    请求 JSON:
        {"session_id": "abc123", "remove_words": ["我们", "数据"]}

    返回 JSON:
        成功: {"status": "success", "word_freq": {...}}
        失败: {"status": "error", "message": "错误原因"}
    """
    data = request.get_json()

    if not data:
        return jsonify({'status': 'error', 'message': '请求体不能为空'})

    if 'session_id' not in data:
        return jsonify({'status': 'error', 'message': '缺少 session_id 参数'})

    if 'remove_words' not in data:
        return jsonify({'status': 'error', 'message': '缺少 remove_words 参数'})

    session_id = data['session_id']
    remove_words = data['remove_words']

    # 从缓存中读取词频
    if session_id not in word_freq_cache:
        return jsonify({'status': 'error', 'message': '会话已过期，请重新上传文件'})

    if not isinstance(remove_words, list):
        return jsonify({'status': 'error', 'message': 'remove_words 必须是列表格式'})

    # 执行过滤
    current_freq = word_freq_cache[session_id]['word_freq']
    filtered = filter_word_freq(current_freq, remove_words)

    # 更新缓存
    word_freq_cache[session_id]['word_freq'] = filtered

    return jsonify({
        'status': 'success',
        'word_freq': filtered
    })


@app.route('/generate_wordcloud', methods=['POST'])
def generate_wordcloud_route():
    """
    生成词云接口：从缓存读取词频，生成词云 PNG 图片。

    请求 JSON:
        {
            "session_id": "abc123",
            "max_font_size": 80,
            "min_font_size": 20,
            "color_theme": "blue"
        }

    返回 JSON:
        成功: {"status": "success", "image_url": "/outputs/wordcloud_abc123.png"}
        失败: {"status": "error", "message": "错误原因"}
    """
    data = request.get_json()

    if not data or 'session_id' not in data:
        return jsonify({'status': 'error', 'message': '缺少 session_id 参数'})

    session_id = data['session_id']

    # 从缓存中读取词频
    if session_id not in word_freq_cache:
        return jsonify({'status': 'error', 'message': '会话已过期，请重新上传文件'})

    word_freq = word_freq_cache[session_id]['word_freq']

    if not word_freq:
        return jsonify({'status': 'error', 'message': '词频数据为空，无法生成词云'})

    # 读取参数（带默认值）
    max_font_size = data.get('max_font_size', 80)
    min_font_size = data.get('min_font_size', 20)
    color_theme = data.get('color_theme', 'blue')

    # 参数校验
    try:
        max_font_size = int(max_font_size)
        min_font_size = int(min_font_size)
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': '字号参数必须为整数'})

    if max_font_size < min_font_size:
        return jsonify({'status': 'error', 'message': '最大字号不能小于最小字号'})

    if color_theme not in ['blue', 'green', 'red', 'purple', 'random']:
        return jsonify({'status': 'error', 'message': '不支持的颜色主题，可选：blue/green/red/purple/random'})

    # 生成输出文件名
    output_filename = f'wordcloud_{session_id}.png'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    try:
        generate_wordcloud(
            word_freq=word_freq,
            output_path=output_path,
            max_font_size=max_font_size,
            min_font_size=min_font_size,
            color_theme=color_theme
        )

        return jsonify({
            'status': 'success',
            'image_url': f'/outputs/{output_filename}'
        })
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)})
    except RuntimeError as e:
        return jsonify({'status': 'error', 'message': str(e)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'词云生成失败：{str(e)}'})


# 静态文件路由：提供 outputs 文件夹中的图片访问
@app.route('/outputs/<path:filename>')
def serve_output(filename):
    """提供词云图片的访问路由。"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='127.0.0.1', port=3326, debug=debug)