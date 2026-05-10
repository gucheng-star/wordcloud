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

6. 保存历史记录
   方法: POST
   路径: /save_history
   参数: word_freq + params + filename（JSON）
   返回: JSON
     成功: {"status": "success", "id": "xxx"}
     失败: {"status": "error", "message": "错误原因"}

7. 获取历史记录列表
   方法: GET
   路径: /history_list
   参数: 无
   返回: JSON
     成功: {"status": "success", "history": [...]}

8. 加载历史记录
   方法: POST
   路径: /load_history
   参数: id（JSON）
   返回: JSON
     成功: {"status": "success", "word_freq": {...}, "params": {...}}
     失败: {"status": "error", "message": "错误原因"}

9. 删除历史记录
   方法: POST
   路径: /delete_history
   参数: id（JSON）
   返回: JSON
     成功: {"status": "success"}
     失败: {"status": "error", "message": "错误原因"}
"""

import os
import sys
import uuid
import webbrowser
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from utils.text_processor import process_file, process_text_string
from utils.filter_processor import filter_word_freq
from utils.cloud_generator import generate_wordcloud, overlay_wordcloud_with_image, VALID_LAYOUT_STYLES, VALID_FONT_FAMILIES
from utils.color_manager import VALID_COLOR_MODES, VALID_GRADIENT_THEMES, is_valid_hex, validate_color_params
from utils.mask_processor import generate_mask, is_allowed_image, get_mask_preview_info, generate_grayscale_image, invert_grayscale_image, validate_threshold
from utils.history_manager import save_history, load_history, delete_history, get_history_by_id, clear_all_history

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


BASE_PATH = get_base_path()

app = Flask(
    __name__,
    template_folder=get_resource_path('templates'),
    static_folder=get_resource_path('static')
)

UPLOAD_FOLDER = os.path.join(BASE_PATH, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

OUTPUT_FOLDER = os.path.join(BASE_PATH, 'outputs')
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

MASK_FOLDER = os.path.join(UPLOAD_FOLDER, 'masks')
app.config['MASK_FOLDER'] = MASK_FOLDER

# 允许上传的文件扩展名（白名单，只允许 txt 文件）
ALLOWED_EXTENSIONS = {'txt'}

MAX_TEXT_LENGTH = 5000000

# 最大上传文件大小限制（16MB）
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ========== 内存缓存：用 session_id 存储词频数据 ==========
# 结构: { "abc123": {"word_freq": {...}, "original_word_freq": {...}, "removed_words": [...]}, ... }
# original_word_freq: 未经用户过滤的原始词频（用于前端显示完整列表）
# removed_words: 用户已选择过滤的词列表（用于前端标记已过滤状态）
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
        word_freq_cache[session_id] = {
            'word_freq': word_freq,
            'original_word_freq': dict(word_freq),
            'removed_words': []
        }

        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'word_freq': word_freq,
            'removed_words': []
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

    # 执行过滤：基于原始词频，移除当前标记的词
    current_freq = word_freq_cache[session_id]['original_word_freq']

    # 直接使用前端传入的 remove_words 作为完整的过滤状态
    # 前端每次发送的是当前所有被标记为过滤的词（不是增量）
    # 这样用户取消过滤某个词后，该词会自动回到词频中
    all_removed = set(remove_words)

    # 基于原始词频过滤
    filtered = filter_word_freq(current_freq, list(all_removed))

    # 更新缓存
    word_freq_cache[session_id]['word_freq'] = filtered
    word_freq_cache[session_id]['removed_words'] = list(all_removed)

    return jsonify({
        'status': 'success',
        'word_freq': filtered,
        'original_word_freq': current_freq,
        'removed_words': list(all_removed)
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
            "color_mode": "preset_gradient",
            "gradient_theme": "blue_gradient",
            "base_color": "#3366ff",
            "width": 800,
            "height": 600,
            "layout_style": "classic"
        }

    返回 JSON:
        成功: {"status": "success", "image_url": "/outputs/wordcloud_abc123.png"}
        失败: {"status": "error", "message": "错误原因"}
    """
    data = request.get_json()

    if not data or 'session_id' not in data:
        return jsonify({'status': 'error', 'message': '缺少 session_id 参数'})

    session_id = data['session_id']

    if session_id not in word_freq_cache:
        return jsonify({'status': 'error', 'message': '会话已过期，请重新上传文件'})

    word_freq = word_freq_cache[session_id]['word_freq']

    if not word_freq:
        return jsonify({'status': 'error', 'message': '词频数据为空，无法生成词云'})

    max_font_size = data.get('max_font_size', 80)
    min_font_size = data.get('min_font_size', 20)
    color_mode = data.get('color_mode', 'preset_gradient')
    gradient_theme = data.get('gradient_theme', 'blue_gradient')
    base_color = data.get('base_color', '')
    width = data.get('width', 800)
    height = data.get('height', 600)
    layout_style = data.get('layout_style', 'classic')
    font_family = data.get('font_family', 'yahei')

    try:
        max_font_size = int(max_font_size)
        min_font_size = int(min_font_size)
        width = int(width)
        height = int(height)
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': '字号和尺寸参数必须为整数'})

    if max_font_size < min_font_size:
        return jsonify({'status': 'error', 'message': '最大字号不能小于最小字号'})

    color_error, color_params = validate_color_params(color_mode, gradient_theme, base_color)
    if color_error:
        return jsonify({'status': 'error', 'message': color_error})
    color_mode = color_params['color_mode']
    gradient_theme = color_params['gradient_theme']
    base_color = color_params['base_color']

    if font_family not in VALID_FONT_FAMILIES:
        font_family = 'yahei'

    if width < 200 or width > 4000:
        return jsonify({'status': 'error', 'message': '宽度范围：200 ~ 4000 像素'})

    if height < 200 or height > 4000:
        return jsonify({'status': 'error', 'message': '高度范围：200 ~ 4000 像素'})

    output_filename = f'wordcloud_{session_id}.png'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    try:
        generate_wordcloud(
            word_freq=word_freq,
            output_path=output_path,
            max_font_size=max_font_size,
            min_font_size=min_font_size,
            color_mode=color_mode,
            gradient_theme=gradient_theme,
            base_color=base_color,
            width=width,
            height=height,
            layout_style=layout_style,
            font_family=font_family
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


# ========== Mask 图片上传接口 ==========

@app.route('/upload_mask_image', methods=['POST'])
def upload_mask_image():
    """
    上传 mask 图片接口。

    接收图片文件，保存到 uploads/masks 目录。

    请求: multipart/form-data，字段名 file

    返回 JSON:
        成功: {"status": "success", "mask_filename": "xxx.png", "preview": {"width": 800, "height": 600, "white_ratio": 65.3}}
        失败: {"status": "error", "message": "错误原因"}
    """
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '未找到上传文件'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'status': 'error', 'message': '未选择文件'})

    if not is_allowed_image(file.filename):
        return jsonify({'status': 'error', 'message': '不支持的图片格式，请上传 png/jpg/jpeg/bmp/gif/webp'})

    ext = file.filename.rsplit('.', 1)[-1].lower()
    mask_filename = f'mask_{uuid.uuid4().hex[:8]}.{ext}'
    mask_path = os.path.join(app.config['MASK_FOLDER'], mask_filename)

    try:
        os.makedirs(app.config['MASK_FOLDER'], exist_ok=True)
        file.save(mask_path)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'图片保存失败：{str(e)}'})

    try:
        preview = get_mask_preview_info(mask_path, 128)
    except Exception:
        preview = None

    return jsonify({
        'status': 'success',
        'mask_filename': mask_filename,
        'preview': preview
    })


@app.route('/generate_grayscale', methods=['POST'])
def generate_grayscale_route():
    data = request.get_json()

    if not data or 'mask_filename' not in data:
        return jsonify({'status': 'error', 'message': '缺少 mask_filename 参数'})

    mask_filename = data['mask_filename']

    if not is_safe_filename(mask_filename):
        return jsonify({'status': 'error', 'message': '文件名无效'})

    mask_path = os.path.join(app.config['MASK_FOLDER'], mask_filename)
    if not os.path.exists(mask_path):
        return jsonify({'status': 'error', 'message': 'Mask 图片不存在，请重新上传'})

    threshold = data.get('threshold', 128)
    invert = data.get('invert', False)

    threshold = validate_threshold(threshold)

    grayscale_filename = f'grayscale_{uuid.uuid4().hex[:8]}.png'
    grayscale_path = os.path.join(app.config['OUTPUT_FOLDER'], grayscale_filename)

    try:
        result = generate_grayscale_image(mask_path, grayscale_path, threshold, invert)
        return jsonify({
            'status': 'success',
            'grayscale_url': f'/outputs/{grayscale_filename}',
            'grayscale_filename': grayscale_filename,
            'width': result['width'],
            'height': result['height']
        })
    except (FileNotFoundError, ValueError) as e:
        return jsonify({'status': 'error', 'message': str(e)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'灰度图生成失败：{str(e)}'})


@app.route('/invert_grayscale', methods=['POST'])
def invert_grayscale_route():
    data = request.get_json()

    if not data or 'grayscale_filename' not in data:
        return jsonify({'status': 'error', 'message': '缺少 grayscale_filename 参数'})

    grayscale_filename = data['grayscale_filename']

    if not is_safe_filename(grayscale_filename):
        return jsonify({'status': 'error', 'message': '文件名无效'})

    grayscale_path = os.path.join(app.config['OUTPUT_FOLDER'], grayscale_filename)
    if not os.path.exists(grayscale_path):
        return jsonify({'status': 'error', 'message': '灰度图片不存在，请先生成灰度图'})

    threshold = data.get('threshold', 128)

    threshold = validate_threshold(threshold)

    inverted_filename = f'grayscale_inv_{uuid.uuid4().hex[:8]}.png'
    inverted_path = os.path.join(app.config['OUTPUT_FOLDER'], inverted_filename)

    try:
        result = invert_grayscale_image(grayscale_path, inverted_path, threshold)
        return jsonify({
            'status': 'success',
            'grayscale_url': f'/outputs/{inverted_filename}',
            'grayscale_filename': inverted_filename,
            'width': result['width'],
            'height': result['height']
        })
    except (FileNotFoundError, ValueError) as e:
        return jsonify({'status': 'error', 'message': str(e)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'灰度反转失败：{str(e)}'})


@app.route('/generate_mask_wordcloud', methods=['POST'])
def generate_mask_wordcloud_route():
    """
    生成形状词云接口：使用 mask 图片生成词云。

    请求 JSON:
        {
            "session_id": "abc123",
            "mask_filename": "mask_xxx.png",
            "threshold": 128,
            "max_font_size": 80,
            "min_font_size": 20,
            "color_theme": "blue",
            "color_hex": "#3366ff"
        }

    返回 JSON:
        成功: {"status": "success", "image_url": "/outputs/wordcloud_abc123.png"}
        失败: {"status": "error", "message": "错误原因"}
    """
    data = request.get_json()

    if not data or 'session_id' not in data:
        return jsonify({'status': 'error', 'message': '缺少 session_id 参数'})

    if 'mask_filename' not in data:
        return jsonify({'status': 'error', 'message': '缺少 mask_filename 参数'})

    session_id = data['session_id']
    mask_filename = data['mask_filename']
    original_mask_filename = data.get('original_mask_filename', '')

    if session_id not in word_freq_cache:
        return jsonify({'status': 'error', 'message': '会话已过期，请重新上传文件'})

    word_freq = word_freq_cache[session_id]['word_freq']
    if not word_freq:
        return jsonify({'status': 'error', 'message': '词频数据为空，无法生成词云'})

    if not is_safe_filename(mask_filename):
        return jsonify({'status': 'error', 'message': '文件名无效'})

    mask_path = os.path.join(app.config['MASK_FOLDER'], mask_filename)
    grayscale_path = os.path.join(app.config['OUTPUT_FOLDER'], mask_filename)

    if os.path.exists(grayscale_path):
        mask_path = grayscale_path
    elif not os.path.exists(mask_path):
        return jsonify({'status': 'error', 'message': 'Mask 图片不存在，请重新上传'})

    original_mask_path = None
    if original_mask_filename and is_safe_filename(original_mask_filename):
        candidate = os.path.join(app.config['MASK_FOLDER'], original_mask_filename)
        if os.path.exists(candidate):
            original_mask_path = candidate

    threshold = data.get('threshold', 128)
    max_font_size = data.get('max_font_size', 80)
    min_font_size = data.get('min_font_size', 20)
    color_mode = data.get('color_mode', 'preset_gradient')
    gradient_theme = data.get('gradient_theme', 'blue_gradient')
    base_color = data.get('base_color', '')
    overlay_opacity = data.get('overlay_opacity', 0)
    layout_style = data.get('layout_style', 'classic')
    font_family = data.get('font_family', 'yahei')

    threshold = validate_threshold(threshold)

    try:
        max_font_size = int(max_font_size)
        min_font_size = int(min_font_size)
        overlay_opacity = float(overlay_opacity)
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': '参数格式不正确'})

    if overlay_opacity < 0 or overlay_opacity > 1:
        return jsonify({'status': 'error', 'message': '叠化透明度范围：0 ~ 1'})

    if max_font_size < min_font_size:
        return jsonify({'status': 'error', 'message': '最大字号不能小于最小字号'})

    color_error, color_params = validate_color_params(color_mode, gradient_theme, base_color)
    if color_error:
        return jsonify({'status': 'error', 'message': color_error})
    color_mode = color_params['color_mode']
    gradient_theme = color_params['gradient_theme']
    base_color = color_params['base_color']

    if font_family not in VALID_FONT_FAMILIES:
        font_family = 'yahei'

    try:
        mask = generate_mask(mask_path, threshold)
    except (FileNotFoundError, ValueError) as e:
        return jsonify({'status': 'error', 'message': str(e)})

    output_filename = f'wordcloud_{session_id}.png'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    try:
        generate_wordcloud(
            word_freq=word_freq,
            output_path=output_path,
            max_font_size=max_font_size,
            min_font_size=min_font_size,
            color_mode=color_mode,
            gradient_theme=gradient_theme,
            base_color=base_color,
            mask=mask,
            layout_style=layout_style,
            font_family=font_family
        )

        if overlay_opacity > 0:
            overlay_filename = f'wordcloud_overlay_{session_id}.png'
            overlay_path = os.path.join(app.config['OUTPUT_FOLDER'], overlay_filename)
            overlay_source = original_mask_path if original_mask_path else mask_path
            try:
                overlay_wordcloud_with_image(output_path, overlay_source, overlay_path, overlay_opacity)
                output_filename = overlay_filename
            except Exception:
                pass

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


# ========== 静态文件路由 ==========

@app.route('/outputs/<path:filename>')
def serve_output(filename):
    """提供词云图片的访问路由。"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


@app.route('/masks/<path:filename>')
def serve_mask(filename):
    """提供 mask 图片的访问路由。"""
    if not is_safe_filename(filename):
        return jsonify({'status': 'error', 'message': '文件名无效'}), 400
    return send_from_directory(app.config['MASK_FOLDER'], filename)


@app.route('/download_image/<path:filename>')
def download_image(filename):
    """
    下载词云图片接口。

    触发浏览器下载而非直接显示图片。

    路径参数:
        filename: 图片文件名，如 wordcloud_abc123.png

    返回:
        文件下载响应
    """
    if not is_safe_filename(filename):
        return jsonify({'status': 'error', 'message': '文件名无效'}), 400

    filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'status': 'error', 'message': '文件不存在'}), 404

    return send_from_directory(
        app.config['OUTPUT_FOLDER'],
        filename,
        as_attachment=True,
        download_name=filename
    )


# ========== 历史记录接口 ==========

@app.route('/cache_word_freq', methods=['POST'])
def cache_word_freq():
    """
    缓存词频数据接口（用于历史记录重新生成）。

    将词频数据写入内存缓存，返回 session_id，
    供后续 /generate_wordcloud 使用。

    请求 JSON:
        {"word_freq": {...}}

    返回 JSON:
        成功: {"status": "success", "session_id": "xxx"}
        失败: {"status": "error", "message": "错误原因"}
    """
    data = request.get_json()

    if not data or 'word_freq' not in data:
        return jsonify({'status': 'error', 'message': '缺少 word_freq 参数'})

    if not isinstance(data['word_freq'], dict):
        return jsonify({'status': 'error', 'message': 'word_freq 必须是字典格式'})

    if not data['word_freq']:
        return jsonify({'status': 'error', 'message': '词频数据不能为空'})

    session_id = uuid.uuid4().hex[:8]
    word_freq_cache[session_id] = {
        'word_freq': data['word_freq'],
        'original_word_freq': dict(data['word_freq']),
        'removed_words': []
    }

    return jsonify({'status': 'success', 'session_id': session_id})


@app.route('/save_history', methods=['POST'])
def save_history_route():
    """
    保存历史记录接口。

    请求 JSON:
        {"word_freq": {...}, "params": {...}, "filename": "xxx.txt"}

    返回 JSON:
        成功: {"status": "success", "id": "xxx"}
        失败: {"status": "error", "message": "错误原因"}
    """
    data = request.get_json()

    if not data:
        return jsonify({'status': 'error', 'message': '请求体不能为空'})

    if 'word_freq' not in data:
        return jsonify({'status': 'error', 'message': '缺少 word_freq 参数'})

    if 'params' not in data:
        return jsonify({'status': 'error', 'message': '缺少 params 参数'})

    try:
        record_id = save_history({
            'word_freq': data['word_freq'],
            'params': data['params'],
            'filename': data.get('filename', '')
        })
        return jsonify({'status': 'success', 'id': record_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'保存失败：{str(e)}'})


@app.route('/history_list', methods=['GET'])
def history_list_route():
    """
    获取历史记录列表接口。

    返回 JSON:
        成功: {"status": "success", "history": [...]}
    """
    try:
        history = load_history()
        return jsonify({'status': 'success', 'history': history})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'加载失败：{str(e)}'})


@app.route('/load_history', methods=['POST'])
def load_history_route():
    """
    加载指定历史记录接口。

    请求 JSON:
        {"id": "xxx"}

    返回 JSON:
        成功: {"status": "success", "word_freq": {...}, "params": {...}}
        失败: {"status": "error", "message": "错误原因"}
    """
    data = request.get_json()

    if not data or 'id' not in data:
        return jsonify({'status': 'error', 'message': '缺少 id 参数'})

    record = get_history_by_id(data['id'])

    if record is None:
        return jsonify({'status': 'error', 'message': '记录不存在'})

    return jsonify({
        'status': 'success',
        'word_freq': record.get('word_freq', {}),
        'params': record.get('params', {})
    })


@app.route('/delete_history', methods=['POST'])
def delete_history_route():
    """
    删除历史记录接口。

    请求 JSON:
        {"id": "xxx"}

    返回 JSON:
        成功: {"status": "success"}
        失败: {"status": "error", "message": "错误原因"}
    """
    data = request.get_json()

    if not data or 'id' not in data:
        return jsonify({'status': 'error', 'message': '缺少 id 参数'})

    success = delete_history(data['id'])

    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': '记录不存在'})


@app.route('/clear_all_history', methods=['POST'])
def clear_all_history_route():
    """
    清空所有历史记录接口。

    返回 JSON:
        成功: {"status": "success", "deleted": 5}
        失败: {"status": "error", "message": "错误原因"}
    """
    count = clear_all_history()
    return jsonify({'status': 'success', 'deleted': count})


# ========== 文本输入接口 ==========

@app.route('/process_text_input', methods=['POST'])
def process_text_input():
    """
    直接处理文本字符串接口：分词 + 词频统计 + 存入缓存。

    用于"直接输入文本"功能，不需要上传文件。

    请求 JSON:
        {"text": "用户输入的文本内容"}

    返回 JSON:
        成功: {"status": "success", "session_id": "abc123", "word_freq": {...}, "removed_words": []}
        失败: {"status": "error", "message": "错误原因"}
    """
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({'status': 'error', 'message': '缺少 text 参数'})

    text = data['text']

    # 输入验证：检查是否为空
    if not isinstance(text, str):
        return jsonify({'status': 'error', 'message': 'text 必须是字符串'})

    if not text.strip():
        return jsonify({'status': 'error', 'message': '文本内容不能为空'})

    # 输入验证：长度限制
    if len(text) > MAX_TEXT_LENGTH:
        return jsonify({'status': 'error', 'message': '文本内容过长，请控制在 500 万字符以内'})

    try:
        word_freq = process_text_string(text)

        session_id = uuid.uuid4().hex[:8]
        word_freq_cache[session_id] = {
            'word_freq': word_freq,
            'original_word_freq': dict(word_freq),
            'removed_words': []
        }

        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'word_freq': word_freq,
            'removed_words': []
        })
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'处理失败：{str(e)}'})


# ========== 数据管理接口 ==========

@app.route('/storage_info', methods=['GET'])
def storage_info():
    """
    获取存储空间使用情况接口。

    返回 JSON:
        {"status": "success", "uploads": {"files": N, "size_kb": N}, "outputs": {"files": N, "size_kb": N}}
    """
    def get_dir_info(dir_path):
        """获取目录的文件数量和总大小（排除 .gitkeep 等隐藏文件）。"""
        total_size = 0
        file_count = 0
        if os.path.exists(dir_path):
            for f in os.listdir(dir_path):
                fp = os.path.join(dir_path, f)
                if os.path.isfile(fp) and not f.startswith('.'):
                    total_size += os.path.getsize(fp)
                    file_count += 1
        return {'files': file_count, 'size_kb': round(total_size / 1024, 1)}

    return jsonify({
        'status': 'success',
        'uploads': get_dir_info(UPLOAD_FOLDER),
        'outputs': get_dir_info(OUTPUT_FOLDER),
        'masks': get_dir_info(MASK_FOLDER)
    })


@app.route('/clean_uploads', methods=['POST'])
def clean_uploads():
    """
    清理 uploads 目录中的文本文件接口。

    返回 JSON:
        成功: {"status": "success", "deleted": N, "freed_kb": N}
    """
    deleted = 0
    freed = 0

    for f in os.listdir(UPLOAD_FOLDER):
        fp = os.path.join(UPLOAD_FOLDER, f)
        if os.path.isfile(fp) and not f.startswith('.'):
            freed += os.path.getsize(fp)
            os.remove(fp)
            deleted += 1

    return jsonify({
        'status': 'success',
        'deleted': deleted,
        'freed_kb': round(freed / 1024, 1)
    })


@app.route('/clean_outputs', methods=['POST'])
def clean_outputs():
    """
    清理 outputs 目录中的图片文件接口。

    返回 JSON:
        成功: {"status": "success", "deleted": N, "freed_kb": N}
    """
    deleted = 0
    freed = 0

    for f in os.listdir(OUTPUT_FOLDER):
        fp = os.path.join(OUTPUT_FOLDER, f)
        if os.path.isfile(fp) and not f.startswith('.'):
            freed += os.path.getsize(fp)
            os.remove(fp)
            deleted += 1

    return jsonify({
        'status': 'success',
        'deleted': deleted,
        'freed_kb': round(freed / 1024, 1)
    })


@app.route('/clean_masks', methods=['POST'])
def clean_masks():
    """
    清理 masks 目录中的图片文件接口。

    返回 JSON:
        成功: {"status": "success", "deleted": N, "freed_kb": N}
    """
    deleted = 0
    freed = 0

    if os.path.exists(MASK_FOLDER):
        for f in os.listdir(MASK_FOLDER):
            fp = os.path.join(MASK_FOLDER, f)
            if os.path.isfile(fp) and not f.startswith('.'):
                freed += os.path.getsize(fp)
                os.remove(fp)
                deleted += 1

    return jsonify({
        'status': 'success',
        'deleted': deleted,
        'freed_kb': round(freed / 1024, 1)
    })


def open_browser():
    webbrowser.open('http://127.0.0.1:3326')


if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    if not debug:
        threading.Timer(1.5, open_browser).start()
    app.run(host='127.0.0.1', port=3326, debug=debug)