# 中文词云工具

本地运行的中文词云生成工具，基于 Flask + 原生 JS（ES Modules），无前端框架、无数据库。

## 功能特性

- **文本输入**：支持上传 `.txt` 文件或直接输入中文文本
- **智能分词**：基于 jieba 分词 + 停用词过滤 + 词频统计
- **词语过滤**：点击词语标签切换过滤状态，灰色划线 = 已过滤
- **颜色系统**：
  - 预设渐变主题（蓝色/绿色/红色/紫色/橙色/赛博朋克/森林）
  - 自定义 HEX 颜色自动生成同色系渐变
  - 单色模式（带亮度变化）
- **布局风格**：经典 / 动感 / 海报 / 竖排混排
- **字体选择**：微软雅黑 / 黑体 / 宋体 / 楷体 / 仿宋
- **灰度图片处理**：上传图片 → 生成灰度预览 → 灰度反转 → 形状词云
- **叠化效果**：词云与原图叠加融合，透明度可调
- **历史记录**：自动保存，支持恢复/删除/清空
- **数据管理**：一键清理上传文件、词云图片、灰度图片
- **响应式布局**：CSS Grid 三断点（单列/双列/三列）

## 快速开始

```bash
# 克隆项目
git clone <repo-url>
cd wordcloud

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动应用
python app.py

# 浏览器访问
# http://127.0.0.1:3326
```

## 项目结构

```
wordcloud/
├── app.py                      # Flask 主应用，路由层
├── requirements.txt            # Python 依赖
├── stopwords.txt               # 中文停用词列表
├── .gitignore
├── data/
│   └── .gitkeep                # 历史记录存储（JSON，运行时生成）
├── uploads/
│   ├── .gitkeep
│   └── masks/                  # 上传图片存放目录（运行时生成）
├── outputs/                    # 词云图片输出目录（运行时生成）
│   └── .gitkeep
├── utils/
│   ├── __init__.py
│   ├── text_processor.py       # jieba 分词 + 停用词过滤 + 词频统计
│   ├── filter_processor.py     # 词频过滤：从词频字典中删除指定词
│   ├── cloud_generator.py      # 词云生成 + 布局风格 + 字体选择 + 叠化效果
│   ├── color_manager.py        # 颜色系统：预设渐变 / 自动渐变 / 单色
│   ├── mask_processor.py       # 灰度图生成 + 反转 + 阈值验证
│   └── history_manager.py      # 历史记录：JSON 文件读写，增删查清空
├── templates/
│   └── index.html              # 主页面
├── static/
│   ├── css/                    # 按功能区域拆分的 CSS（15 个文件）
│   │   ├── base.css            # 全局重置、body、容器
│   │   ├── layout.css          # CSS Grid 响应式布局（3 断点）
│   │   ├── tabs.css            # 输入方式切换标签
│   │   ├── upload.css          # 文件上传区域
│   │   ├── text-input.css      # 直接输入文本区域
│   │   ├── buttons.css         # 通用按钮样式
│   │   ├── message.css         # 提示消息
│   │   ├── process.css         # 分词处理区域
│   │   ├── result.css          # 词频结果 + 词语标签
│   │   ├── cloud.css           # 词云参数 + 颜色 + 字体 + 下载
│   │   ├── mask.css            # 灰度图片处理 + 预览 + 反转
│   │   ├── history.css         # 历史记录
│   │   ├── manage.css          # 数据管理
│   │   ├── info.css            # 使用说明
│   │   └── modal.css           # 自定义确认弹窗
│   └── js/                     # ES Modules
│       ├── app.js              # 入口：try-catch 初始化所有模块
│       ├── state.js            # 共享状态 + DOM 引用
│       ├── utils.js            # postJSON、showMessage、showConfirm
│       ├── tabs.js             # 输入方式切换
│       ├── upload.js           # 文件上传
│       ├── text-input.js       # 文本输入
│       ├── process.js          # 分词分析
│       ├── filter.js           # 词频过滤 + renderWordFreq
│       ├── cloud.js            # 词云生成 + 颜色/字体/布局参数
│       ├── mask.js             # 灰度图生成 + 反转 + 预览
│       ├── history.js          # 历史记录管理
│       └── manage.js           # 数据管理 + 存储信息
└── venv/                       # Python 虚拟环境
```

## 颜色系统

### 三种颜色模式

| 模式 | 说明 | 前端显示 |
|------|------|---------|
| `preset_gradient` | 预设渐变颜色池 | 渐变主题下拉 |
| `auto_gradient` | 用户输入 HEX 自动生成同色系渐变 | HEX 输入框 |
| `solid` | 单色 + 轻微亮度变化 | HEX 输入框 |

### 预设渐变主题

| 主题 | 颜色池 |
|------|--------|
| 蓝色渐变 | #0D47A1 → #90CAF9 |
| 绿色渐变 | #1B5E20 → #A5D6A7 |
| 红色渐变 | #B71C1C → #EF9A9A |
| 紫色渐变 | #4A148C → #E1BEE7 |
| 橙色渐变 | #E65100 → #FFCC80 |
| 赛博朋克 | #00FFFF → #FF1493 |
| 森林 | #1B5E20 → #AED581 |

### 自动渐变

输入基色 `#3366ff`，系统自动生成 5 级亮度渐变：

```
#142866 → #2142A5 → #3366FF → #478EFF → #5BB7FF
darker      dark       base      lighter     lighter
```

## 布局风格

| 风格 | 水平词比例 | 旋转增强 | 适用场景 |
|------|-----------|---------|---------|
| 经典 | 95% | 无 | 正式文档、报告 |
| 动感 | 70% | ±30° 旋转词叠加 | 活动宣传 |
| 海报 | 50% | ±45° 旋转词叠加 | 设计海报 |
| 竖排混排 | 30% | 无 | 中式风格 |

## 字体选择

| 字体 | 特性 | 适用场景 |
|------|------|---------|
| 微软雅黑 | 现代清晰，笔画匀称 | 通用首选 |
| 黑体 | 粗犷有力，视觉冲击 | 标题、海报 |
| 宋体 | 经典正式，横细竖粗 | 传统排版 |
| 楷体 | 书法韵味，笔画流畅 | 文化风格 |
| 仿宋 | 优雅传统，笔画秀丽 | 古典韵味 |

## 灰度图片处理

1. 上传图片 → 自动预览
2. 调整灰度阈值（0~255）→ 点击"生成灰度图片"
3. 灰度预览区显示结果，提示"词云将在黑色部分生成"
4. 可选"灰度反转"翻转黑白区域
5. 点击"生成形状词云"→ 词云按灰度图形状生成
6. 可调叠化透明度，将词云与原图融合

## API 接口

| 路由 | 方法 | 功能 |
|------|------|------|
| `GET /` | GET | 返回首页 |
| `POST /upload_txt` | POST | 上传 txt 文件 |
| `POST /process_text` | POST | 文件分词，返回词频 |
| `POST /process_text_input` | POST | 直接输入文本分词 |
| `POST /cache_word_freq` | POST | 缓存词频到内存 |
| `POST /filter_words` | POST | 过滤指定词 |
| `POST /generate_wordcloud` | POST | 生成词云 |
| `POST /upload_mask_image` | POST | 上传图片 |
| `POST /generate_grayscale` | POST | 生成灰度图片 |
| `POST /invert_grayscale` | POST | 灰度反转 |
| `POST /generate_mask_wordcloud` | POST | 生成形状词云 |
| `GET /outputs/<filename>` | GET | 访问词云图片 |
| `GET /masks/<filename>` | GET | 访问上传图片 |
| `GET /download_image/<filename>` | GET | 下载词云图片 |
| `POST /save_history` | POST | 保存历史记录 |
| `GET /history_list` | GET | 获取历史记录列表 |
| `POST /load_history` | POST | 加载历史记录 |
| `POST /delete_history` | POST | 删除历史记录 |
| `POST /clear_all_history` | POST | 清空历史记录 |
| `GET /storage_info` | GET | 获取存储信息 |
| `POST /clean_uploads` | POST | 清理上传文件 |
| `POST /clean_outputs` | POST | 清理词云图片 |
| `POST /clean_masks` | POST | 清理灰度图片 |

## 技术栈

- **后端**：Python 3.10+ / Flask 3.0 / jieba / wordcloud / Pillow / numpy
- **前端**：原生 HTML + CSS + JavaScript（ES Modules），零框架依赖
- **布局**：CSS Grid 响应式三断点

## 依赖

```
flask>=3.0
werkzeug>=3.0
jieba>=0.42
wordcloud>=1.9
matplotlib>=3.7
Pillow>=10.0
numpy>=1.24
```

## 许可

MIT
