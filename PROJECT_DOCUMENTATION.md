# PicGet 项目文档

## 1. 项目概述



### 1.1 项目简介
PicGet 是一个基于 Python 的 GUI 应用程序，用于从网站批量下载图片和视频。支持单页下载、批量分析下载以及 M3U8 视频下载功能。

### 1.2 技术栈
- **GUI框架**: Tkinter (Python内置)
- **网络请求**: requests
- **HTML解析**: BeautifulSoup4 + lxml
- **并发处理**: ThreadPoolExecutor
- **界面组件**: ttk (Tkinter Themed Widgets)

### 1.3 项目结构
```
C:\picget\
├── picget.py           # 主程序文件 (1110行)
├── requirements.txt    # 依赖清单
├── README.md          # 简要说明
└── downloads/         # 下载目录 (运行时生成)
```

---

## 2. 功能模块

### 2.1 单页下载 (Single Page Download)
**功能**: 从单个URL下载图片

**界面组件**:
- 网址输入框
- 保存路径选择 (默认: C:\picget\downloads)
- 请求延时设置 (默认: 2秒)
- 线程数量设置 (默认: 10)
- 进度文本框
- 进度条
- 开始下载/清空日志按钮

**核心逻辑**:
```
1. 获取用户输入URL和配置
2. 发送HTTP请求获取页面
3. 解析页面提取图片URL (支持编码HTML解码)
4. 创建保存目录
5. 多线程下载图片
6. MD5去重处理
7. 保存图片文件
```

### 2.2 批量分析 (Batch Analysis)
**功能**: 分析分页网站，批量下载多页图片

**界面组件**:
- 起始网址输入框
- 分析页数按钮
- 网址前缀设置
- 页面列表 (支持Ctrl/Shift多选)
- 图片链接列表
- 全选/取消全选按钮
- 分析/停止分析按钮
- 下载选中按钮

**核心逻辑**:
```
1. 分析起始页获取总页数
2. 生成所有页面URL列表
3. 批量分析页面提取图片链接
4. 用户选择要下载的页面
5. 批量下载选中页面的图片
```

### 2.3 视频下载 (Video Download)
**功能**: 分析并下载M3U8视频流，合并为MP4

**界面组件**:
- M3U8链接输入框
- M3U8分析按钮
- M3U8链接列表
- M3U8内容列表 (TS切片)
- 分析M3U8内容按钮
- 保存路径选择
- MP4文件名设置
- 请求延时/线程数量设置

**核心逻辑**:
```
1. 分析页面提取M3U8/MP4链接
2. 解析M3U8文件获取TS切片URL列表
3. 多线程下载TS切片
4. 按顺序合并TS文件为MP4
5. 删除临时TS文件
```

---

## 3. 核心类与方法

### 3.1 PicGetApp 类

#### 3.1.1 初始化
```python
class PicGetApp:
    def __init__(self, root):
        self.root = root                    # Tkinter根窗口
        self.driver = None                  # Selenium WebDriver (未使用)
        self.downloaded_images = set()      # 已下载图片MD5集合
        self.stop_analysis = False          # 停止分析标志
```

#### 3.1.2 UI设置方法
| 方法名 | 功能 | 行号 |
|--------|------|------|
| `setup_ui()` | 初始化主界面和Tab | 29-44 |
| `setup_single_download_ui()` | 单页下载界面 | 46-93 |
| `setup_batch_download_ui()` | 批量分析界面 | 95-176 |
| `setup_video_download_ui()` | 视频下载界面 | 190-268 |

#### 3.1.3 图片下载核心方法
| 方法名 | 功能 | 行号 |
|--------|------|------|
| `start_download()` | 启动图片下载 | 784-811 |
| `download_thread()` | 图片下载线程 | 813-864 |
| `download_image()` | 单张图片下载 | 741-779 |
| `extract_images_from_encoded_html()` | 提取图片URL | 714-739 |

#### 3.1.4 批量分析核心方法
| 方法名 | 功能 | 行号 |
|--------|------|------|
| `analyze_pages()` | 分析分页 | 866-877 |
| `analyze_pages_thread()` | 分页分析线程 | 879-947 |
| `analyze_images()` | 分析图片链接 | 949-958 |
| `analyze_images_thread()` | 图片分析线程 | 960-1014 |
| `download_selected_images()` | 下载选中图片 | 1016-1047 |
| `download_images_thread()` | 批量下载线程 | 1049-1101 |

#### 3.1.5 视频下载核心方法
| 方法名 | 功能 | 行号 |
|--------|------|------|
| `analyze_m3u8()` | 分析M3U8链接 | 283-294 |
| `analyze_m3u8_thread()` | M3U8分析线程 | 296-376 |
| `analyze_m3u8_content()` | 分析M3U8内容 | 378-401 |
| `analyze_m3u8_content_thread()` | TS切片分析线程 | 403-467 |
| `start_video_download()` | 启动视频下载 | 469-507 |
| `download_ts_thread()` | TS下载线程 | 509-634 |

#### 3.1.6 工具方法
| 方法名 | 功能 | 行号 |
|--------|------|------|
| `get_random_user_agent()` | 随机User-Agent | 668-679 |
| `get_headers()` | 构建请求头 | 681-702 |
| `random_delay()` | 随机延时 | 704-707 |
| `sanitize_folder_name()` | 清理文件夹名 | 709-712 |
| `get_image_hash()` | 计算图片MD5 | 781-782 |

---

## 4. 关键技术细节

### 4.1 图片去重机制
```python
def get_image_hash(self, image_data):
    return hashlib.md5(image_data).hexdigest()
```
- 使用MD5哈希检测重复图片
- 已下载图片存储在 `self.downloaded_images` 集合中

### 4.2 编码HTML解码
```python
def extract_images_from_encoded_html(self, html_content):
    match = re.search(r'var _h="([^"]+)"', html_content)
    if match:
        encoded = match.group(1)
        decoded = unquote(unquote(encoded))
```
- 支持双重URL编码的HTML内容
- 常见于某些图片网站的内容保护

### 4.3 TS文件合并流程
```
1. 下载所有TS切片到临时文件
2. 创建MP4文件
3. 按文件名排序读取所有TS文件
4. 依次写入MP4文件
5. 合并完成后删除TS文件
```

### 4.4 反爬虫措施
1. **随机User-Agent**: 每次请求使用不同的UA
2. **请求延时**: 防止请求过于频繁
3. **随机延时**: 在基础延时上增加随机波动
4. **Accept-Language轮换**: 模拟不同地区用户

---

## 5. 依赖说明

| 包名 | 版本要求 | 用途 |
|------|----------|------|
| selenium | >=4.15.0 | WebDriver (代码中未实际使用) |
| requests | >=2.31.0 | HTTP请求 |
| beautifulsoup4 | >=4.12.0 | HTML解析 |
| lxml | >=4.9.0 | XML/HTML解析器 |

---

## 6. 使用指南

### 6.1 环境安装
```bash
pip install -r requirements.txt
```

### 6.2 运行程序
```bash
python picget.py
```

### 6.3 单页下载流程
1. 在"单页下载"Tab中输入目标网址
2. 选择保存路径 (可选，默认C:\picget\downloads)
3. 设置请求延时 (建议2-5秒)
4. 点击"开始下载"
5. 等待下载完成

### 6.4 批量下载流程
1. 切换到"批量分析"Tab
2. 输入起始网址，点击"分析页数"
3. 在页面列表中选择要下载的页面 (支持Ctrl/Shift多选)
4. 点击"分析图片地址"
5. 在图片链接列表中查看结果
6. 选择要下载的链接，点击"下载选中网址图片"

### 6.5 视频下载流程
1. 切换到"视频下载"Tab
2. 输入视频页面URL
3. 点击"M3U8分析"
4. 在M3U8链接列表中选择链接
5. 点击"分析M3U8内容"
6. 在M3U8内容列表中查看TS切片
7. 选择要下载的切片 (通常全选)
8. 点击"开始下载"
9. 等待合并完成

---

## 7. 注意事项

1. **请求延时**: 建议不要设置过短(小于1秒)，可能被网站封禁
2. **图片格式**: 目前仅支持JPG/JPEG格式
3. **编码问题**: 部分网站可能使用特殊编码，已做GBK/UTF-8兼容处理
4. **M3U8解析**: 只解析一级M3U8，不支持多级嵌套
5. **TS合并**: 合并后会自动删除临时TS文件以节省空间

---

## 8. 错误处理

### 8.1 常见错误
- `ConnectionError`: 网络连接失败
- `TimeoutError`: 请求超时
- `ValueError`: 参数格式错误
- `FileNotFoundError`: 保存路径不存在

### 8.2 错误提示
所有错误都会通过 `messagebox.showerror()` 弹出提示，并在进度文本框中显示详细错误信息。

---

## 9. 性能优化

### 9.1 并发控制
- 图片下载线程数: 默认10，最大100
- 视频TS下载线程数: 默认10，最大100
- 使用 `ThreadPoolExecutor` 管理线程池

### 9.2 内存优化
- 图片MD5使用集合存储，避免重复下载
- 大文件使用流式写入 (`iter_content`)
- TS合并使用二进制模式，避免内存溢出

---

## 10. 未来改进建议

1. **Selenium集成**: 当前代码保留了Selenium接口但未使用，可用于处理JavaScript渲染的网站
2. **代理支持**: 添加HTTP/SOCKS代理支持
3. **断点续传**: 支持中断后继续下载
4. **更多视频格式**: 支持除M3U8外的其他视频流格式
5. **图片压缩**: 添加图片压缩/格式转换功能
6. **历史记录**: 保存下载历史和配置

---

## 11. 版本信息

- **当前版本**: v1.0
- **代码行数**: 1110行 (不含空行)
- **最后更新**: 2024年
- **开发语言**: Python 3.x

---

*文档生成时间: 2026-02-12*
