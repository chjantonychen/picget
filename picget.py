import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
import os
import hashlib
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import unquote


class PicGetApp:
    """
    PicGet应用程序主类 - 网站图片下载工具
    
    功能：
    - 单页图片下载：从单个网页下载所有图片
    - 批量分析下载：分析多页并批量下载图片
    - 视频下载：支持M3U8格式的视频流下载和合并
    """
    
    def __init__(self, root):
        """
        初始化应用程序
        
        参数:
            root: tkinter根窗口对象
        """
        self.root = root
        self.root.title("PicGet - 网站图片下载工具")
        self.root.geometry("900x700")  # 设置窗口大小为900x700像素
        self.root.resizable(True, True)  # 允许窗口缩放
        self.root.state('zoomed')  # 窗口最大化显示
        
        # 初始化成员变量
        self.driver = None  # Selenium WebDriver（预留，当前未使用）
        self.downloaded_images = set()  # 存储已下载图片的MD5哈希值，用于去重
        self.stop_analysis = False  # 停止分析标志位
        
        self.setup_ui()  # 设置用户界面
    
    def setup_ui(self):
        """
        设置用户界面主框架
        创建标签页容器，包含三个主要功能标签页
        """
        # 创建Notebook（标签页容器）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建单页下载标签页
        self.tab_single = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.tab_single, text="单页下载")
        
        # 创建批量分析标签页
        self.tab_batch = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.tab_batch, text="批量分析")
        
        # 创建视频下载标签页
        self.tab_video = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.tab_video, text="视频下载")
        
        # 调用各标签页的UI设置方法
        self.setup_single_download_ui()
        self.setup_batch_download_ui()
        self.setup_video_download_ui()
    
    def setup_single_download_ui(self):
        """
        设置单页下载标签页的UI
        包含网址输入、保存路径、线程设置和进度显示等组件
        """
        # ========== 网站配置区域 ==========
        url_frame = ttk.LabelFrame(self.tab_single, text="网站配置", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        # URL输入框及标签
        ttk.Label(url_frame, text="网址URL:").pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(url_frame, width=70)  # 输入框宽度70字符
        self.url_entry.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        
        # ========== 下载设置区域 ==========
        settings_frame = ttk.LabelFrame(self.tab_single, text="下载设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 保存路径选择
        ttk.Label(settings_frame, text="保存路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.save_path_entry = ttk.Entry(settings_frame, width=60)
        self.save_path_entry.grid(row=0, column=1, padx=(5, 5), pady=5, sticky=tk.W)
        self.save_path_entry.insert(0, "C:\\picget\\downloads")  # 默认保存路径
        ttk.Button(settings_frame, text="浏览", command=self.browse_folder).grid(row=0, column=2, padx=(5, 0))
        
        # 请求延时设置
        ttk.Label(settings_frame, text="请求延时(秒):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.delay_entry = ttk.Entry(settings_frame, width=10)
        self.delay_entry.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        self.delay_entry.insert(0, "2")  # 默认延时2秒
        
        # 线程数量设置
        ttk.Label(settings_frame, text="线程数量:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.thread_entry = ttk.Entry(settings_frame, width=10)
        self.thread_entry.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        self.thread_entry.insert(0, "10")  # 默认10个线程
        
        # ========== 进度信息区域 ==========
        progress_frame = ttk.LabelFrame(self.tab_single, text="进度信息", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 进度文本显示区（带滚动条）
        self.progress_text = tk.Text(progress_frame, height=15, width=90)
        self.progress_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(progress_frame, orient=tk.VERTICAL, command=self.progress_text.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.progress_text.config(yscrollcommand=scrollbar.set)  # 绑定滚动条
        
        # 进度条控件
        self.progress_bar = ttk.Progressbar(self.tab_single, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # ========== 操作按钮区域 ==========
        button_frame = ttk.Frame(self.tab_single)
        button_frame.pack(fill=tk.X)
        
        # 开始下载按钮
        self.start_button = ttk.Button(button_frame, text="开始下载", command=self.start_download)
        self.start_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 清空日志按钮
        self.clear_button = ttk.Button(button_frame, text="清空日志", command=self.clear_log)
        self.clear_button.pack(side=tk.RIGHT)
    
    def setup_batch_download_ui(self):
        """
        设置批量分析标签页的UI
        支持分析多页面、批量下载、多线程处理等功能
        """
        # ========== 网址分析区域 ==========
        url_frame = ttk.LabelFrame(self.tab_batch, text="网址分析", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 起始网址输入
        ttk.Label(url_frame, text="起始网址:").pack(side=tk.LEFT)
        self.batch_url_entry = ttk.Entry(url_frame, width=70)
        self.batch_url_entry.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        
        # 分析页数按钮
        ttk.Button(url_frame, text="分析页数", command=self.analyze_pages).pack(side=tk.LEFT, padx=(0, 10))
        
        # 网址前缀设置（用于相对链接）
        prefix_frame = ttk.Frame(url_frame)
        prefix_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(prefix_frame, text="网址前缀:").pack(side=tk.LEFT)
        self.prefix_entry = ttk.Entry(prefix_frame, width=50)
        self.prefix_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # ========== 下载设置区域 ==========
        settings_frame = ttk.LabelFrame(self.tab_batch, text="下载设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 保存路径选择
        ttk.Label(settings_frame, text="保存路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.batch_save_path_entry = ttk.Entry(settings_frame, width=60)
        self.batch_save_path_entry.grid(row=0, column=1, padx=(5, 5), pady=5, sticky=tk.W)
        self.batch_save_path_entry.insert(0, "C:\\picget\\downloads")
        ttk.Button(settings_frame, text="浏览", command=self.browse_batch_folder).grid(row=0, column=2, padx=(5, 0))
        
        # 请求延时设置
        ttk.Label(settings_frame, text="请求延时(秒):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.batch_delay_entry = ttk.Entry(settings_frame, width=10)
        self.batch_delay_entry.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        self.batch_delay_entry.insert(0, "2")
        
        # 线程数量设置
        ttk.Label(settings_frame, text="线程数量:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.batch_thread_entry = ttk.Entry(settings_frame, width=10)
        self.batch_thread_entry.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        self.batch_thread_entry.insert(0, "50")  # 批量模式默认50个线程
        
        # ========== 页面列表区域 ==========
        list_frame = ttk.LabelFrame(self.tab_batch, text="页面列表 (支持Ctrl/Shift多选)", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 页面列表框（支持多选）
        self.url_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=8)
        self.url_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.url_listbox.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.url_listbox.config(yscrollcommand=scrollbar.set)
        
        # 页面列表操作按钮
        button_frame = ttk.Frame(self.tab_batch)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="全选", command=self.select_all_pages).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="取消全选", command=self.deselect_all_pages).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="分析图片地址", command=self.analyze_images).pack(side=tk.LEFT, padx=(20, 5))
        ttk.Button(button_frame, text="停止分析", command=self.stop_analyze).pack(side=tk.LEFT, padx=(5, 5))
        ttk.Button(button_frame, text="清空页面列表", command=self.clear_url_list).pack(side=tk.LEFT, padx=(5, 5))
        ttk.Button(button_frame, text="下载选中网址图片", command=self.download_selected_images).pack(side=tk.RIGHT, padx=(5, 0))
        
        # ========== 图片链接区域 ==========
        img_list_frame = ttk.LabelFrame(self.tab_batch, text="图片链接", padding="10")
        img_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 图片链接列表框
        self.img_listbox = tk.Listbox(img_list_frame, selectmode=tk.EXTENDED, height=8)
        self.img_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        img_scrollbar = ttk.Scrollbar(img_list_frame, orient=tk.VERTICAL, command=self.img_listbox.yview)
        img_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.img_listbox.config(yscrollcommand=img_scrollbar.set)
        
        # 图片列表操作按钮
        img_button_frame = ttk.Frame(self.tab_batch)
        img_button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(img_button_frame, text="全选图片", command=self.select_all_images).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(img_button_frame, text="取消全选", command=self.deselect_all_images).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(img_button_frame, text="清空列表", command=self.clear_img_list).pack(side=tk.LEFT, padx=(20, 5))
        ttk.Button(img_button_frame, text="下载选中网址图片", command=self.download_selected_images).pack(side=tk.RIGHT, padx=(5, 0))
        
        # ========== 下载进度区域 ==========
        batch_progress_frame = ttk.LabelFrame(self.tab_batch, text="下载进度", padding="10")
        batch_progress_frame.pack(fill=tk.X)
        
        self.batch_progress_text = tk.Text(batch_progress_frame, height=8, width=90)
        self.batch_progress_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        batch_scrollbar = ttk.Scrollbar(batch_progress_frame, orient=tk.VERTICAL, command=self.batch_progress_text.yview)
        batch_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.batch_progress_text.config(yscrollcommand=batch_scrollbar.set)
    
    def browse_folder(self):
        """
        单页下载：弹出文件夹选择对话框
        选择后将路径填入保存路径输入框
        """
        folder = filedialog.askdirectory(title="选择保存路径")
        if folder:
            self.save_path_entry.delete(0, tk.END)
            self.save_path_entry.insert(0, folder)
    
    def browse_batch_folder(self):
        """
        批量下载：弹出文件夹选择对话框
        """
        folder = filedialog.askdirectory(title="选择保存路径")
        if folder:
            self.batch_save_path_entry.delete(0, tk.END)
            self.batch_save_path_entry.insert(0, folder)
    
    def setup_video_download_ui(self):
        """
        设置视频下载标签页的UI
        支持M3U8视频流分析和TS片段下载合并
        """
        # ========== 网站配置区域 ==========
        url_frame = ttk.LabelFrame(self.tab_video, text="网站配置", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        # URL输入框
        ttk.Label(url_frame, text="网址URL:").pack(side=tk.LEFT)
        self.video_url_entry = ttk.Entry(url_frame, width=70)
        self.video_url_entry.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        
        # M3U8分析按钮
        url_button_frame = ttk.Frame(url_frame)
        url_button_frame.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(url_button_frame, text="M3U8分析", command=self.analyze_m3u8).pack(side=tk.LEFT, padx=(0, 5))
        
        # ========== M3U8链接列表区域 ==========
        m3u8_frame = ttk.LabelFrame(self.tab_video, text="M3U8链接列表", padding="10")
        m3u8_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.m3u8_listbox = tk.Listbox(m3u8_frame, selectmode=tk.EXTENDED, height=6)
        self.m3u8_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        m3u8_scrollbar = ttk.Scrollbar(m3u8_frame, orient=tk.VERTICAL, command=self.m3u8_listbox.yview)
        m3u8_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.m3u8_listbox.config(yscrollcommand=m3u8_scrollbar.set)
        
        # ========== M3U8内容列表区域（TS片段）==========
        m3u8_content_frame = ttk.LabelFrame(self.tab_video, text="M3U8内容列表", padding="10")
        m3u8_content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.m3u8_content_listbox = tk.Listbox(m3u8_content_frame, selectmode=tk.EXTENDED, height=6)
        self.m3u8_content_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        m3u8_content_scrollbar = ttk.Scrollbar(m3u8_content_frame, orient=tk.VERTICAL, command=self.m3u8_content_listbox.yview)
        m3u8_content_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.m3u8_content_listbox.config(yscrollcommand=m3u8_content_scrollbar.set)
        
        # M3U8内容操作按钮
        m3u8_button_frame = ttk.Frame(self.tab_video)
        m3u8_button_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(m3u8_button_frame, text="分析M3U8内容", command=self.analyze_m3u8_content).pack(side=tk.LEFT)
        ttk.Button(m3u8_button_frame, text="清空M3U8列表", command=self.clear_m3u8_list).pack(side=tk.LEFT, padx=(10, 0))
        
        # ========== 下载设置区域 ==========
        settings_frame = ttk.LabelFrame(self.tab_video, text="下载设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 保存路径
        ttk.Label(settings_frame, text="保存路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.video_save_path_entry = ttk.Entry(settings_frame, width=60)
        self.video_save_path_entry.grid(row=0, column=1, padx=(5, 5), pady=5, sticky=tk.W)
        self.video_save_path_entry.insert(0, "C:\\picget\\downloads")
        ttk.Button(settings_frame, text="浏览", command=self.browse_video_folder).grid(row=0, column=2, padx=(5, 0))
        
        # MP4文件名设置
        ttk.Label(settings_frame, text="MP4文件名:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.video_filename_entry = ttk.Entry(settings_frame, width=40)
        self.video_filename_entry.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        self.video_filename_entry.insert(0, "")
        
        # 请求延时
        ttk.Label(settings_frame, text="请求延时(秒):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.video_delay_entry = ttk.Entry(settings_frame, width=10)
        self.video_delay_entry.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        self.video_delay_entry.insert(0, "2")
        
        # 线程数量
        ttk.Label(settings_frame, text="线程数量:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.video_thread_entry = ttk.Entry(settings_frame, width=10)
        self.video_thread_entry.grid(row=3, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        self.video_thread_entry.insert(0, "50")
        
        # ========== 下载进度区域 ==========
        progress_frame = ttk.LabelFrame(self.tab_video, text="下载进度", padding="10")
        progress_frame.pack(fill=tk.X)
        
        self.video_progress_text = tk.Text(progress_frame, height=8, width=90)
        self.video_progress_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(progress_frame, orient=tk.VERTICAL, command=self.video_progress_text.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.video_progress_text.config(yscrollcommand=scrollbar.set)
        
        # ========== 操作按钮区域 ==========
        button_frame = ttk.Frame(self.tab_video)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 开始下载按钮
        self.video_start_button = ttk.Button(button_frame, text="开始下载", command=self.start_video_download)
        self.video_start_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 清空日志按钮
        self.video_clear_button = ttk.Button(button_frame, text="清空日志", command=self.clear_video_log)
        self.video_clear_button.pack(side=tk.RIGHT)
    
    def browse_video_folder(self):
        """
        视频下载：弹出文件夹选择对话框
        """
        folder = filedialog.askdirectory(title="选择保存路径")
        if folder:
            self.video_save_path_entry.delete(0, tk.END)
            self.video_save_path_entry.insert(0, folder)
    
    def clear_video_log(self):
        """
        清空视频下载标签页的日志文本
        """
        self.video_progress_text.delete(1.0, tk.END)
    
    def clear_m3u8_list(self):
        """
        清空M3U8链接列表和内容列表
        """
        self.m3u8_listbox.delete(0, tk.END)
        self.m3u8_content_listbox.delete(0, tk.END)
    
    def analyze_m3u8(self):
        """
        分析网页中的M3U8视频链接
        启动后台线程执行分析任务，避免阻塞UI
        """
        url = self.video_url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入网址URL")
            return
        
        # 清空列表并显示分析中提示
        self.m3u8_listbox.delete(0, tk.END)
        self.m3u8_listbox.insert(tk.END, "正在分析...")
        
        # 创建后台线程执行分析
        thread = threading.Thread(target=self.analyze_m3u8_thread, args=(url,))
        thread.daemon = True  # 守护线程，主程序退出时自动结束
        thread.start()
    
    def analyze_m3u8_thread(self, url):
        """
        在后台线程中分析M3U8链接
        
        参数:
            url: 要分析的网页URL
        """
        try:
            # 获取HTTP请求头
            headers = self.get_headers()
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()  # 检查请求是否成功
            
            # 尝试解码响应内容（某些网站使用双重URL编码）
            match = re.search(r'var _h="([^"]+)"', response.text)
            if match:
                encoded = match.group(1)
                decoded = unquote(unquote(encoded))  # 双重解码
            else:
                decoded = response.text
            
            # 提取网页标题
            title_match = re.search(r'<title>([^<]+)</title>', decoded)
            if not title_match:
                title_match = re.search(r'<title>([^<]+)</title>', response.text)
            
            # 处理标题编码（支持GBK/GB2312/UTF-8等）
            if title_match:
                raw_title = title_match.group(1).strip()
                for encoding in ['gbk', 'gb2312', 'gb18030', 'utf-8']:
                    try:
                        title = raw_title.encode('latin1').decode(encoding)
                        # 更新文件名输入框
                        self.root.after(0, lambda t=title: self.video_filename_entry.delete(0, tk.END))
                        self.root.after(0, lambda t=title: self.video_filename_entry.insert(0, t))
                        break
                    except:
                        continue
            
            # 提取M3U8和视频链接
            m3u8_urls = []
            video_urls = []
            
            # 在player div中搜索M3U8链接
            player_div = re.search(r'<div[^>]+id="player"[^>]*class="dplayer"[^>]*>(.*?)</div>', decoded, re.DOTALL)
            if player_div:
                player_content = player_div.group(1)
                
                # 从JSON格式中提取URL
                json_match = re.search(r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', player_content)
                if json_match:
                    m3u8_url = json_match.group(1).replace('\\/', '/')  # 处理转义斜杠
                    m3u8_urls.append(m3u8_url)
                
                # 正则匹配M3U8和MP4链接
                m3u8_urls.extend(re.findall(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', player_content))
                video_urls = re.findall(r'src="([^"]+\.mp4[^"]*)"', player_content)
            
            # 如果player div没找到，在整个页面中搜索
            if not m3u8_urls:
                json_match = re.search(r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', decoded)
                if json_match:
                    m3u8_url = json_match.group(1).replace('\\/', '/')
                    m3u8_urls.append(m3u8_url)
            
            # 最后的全局搜索
            if not m3u8_urls and not video_urls:
                m3u8_urls = re.findall(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', decoded.replace('\\/', '/'))
                video_urls = re.findall(r'src="([^"]+\.mp4[^"]*)"', decoded)
            
            # 去重
            m3u8_urls = list(set(m3u8_urls))
            video_urls = list(set(video_urls))
            
            # 更新UI显示结果
            self.root.after(0, lambda: self.m3u8_listbox.delete(0, tk.END))
            
            # 添加M3U8链接到列表
            for m3u8_url in m3u8_urls:
                if m3u8_url.startswith('http'):
                    self.root.after(0, lambda u=m3u8_url: self.m3u8_listbox.insert(tk.END, u))
                else:
                    # 相对链接转换为绝对链接
                    full_url = urljoin(url, m3u8_url)
                    self.root.after(0, lambda u=full_url: self.m3u8_listbox.insert(tk.END, u))
            
            # 添加视频链接到列表
            for video_url in video_urls:
                if video_url.startswith('http'):
                    self.root.after(0, lambda u=video_url: self.m3u8_listbox.insert(tk.END, u))
                else:
                    full_url = urljoin(url, video_url)
                    self.root.after(0, lambda u=full_url: self.m3u8_listbox.insert(tk.END, u))
            
            # 显示总数
            total = len(m3u8_urls) + len(video_urls)
            self.root.after(0, lambda c=total: self.m3u8_listbox.insert(tk.END, f"--- 共找到 {c} 个链接 ---"))
            
            # 未找到链接的提示
            if total == 0:
                self.root.after(0, lambda: self.m3u8_listbox.insert(tk.END, "未找到M3U8或视频链接"))
                
        except Exception as e:
            # 显示错误信息
            self.root.after(0, lambda: self.m3u8_listbox.delete(0, tk.END))
            self.root.after(0, lambda msg=str(e): self.m3u8_listbox.insert(tk.END, f"分析失败: {msg}"))
    
    def analyze_m3u8_content(self):
        """
        分析选中的M3U8链接内容
        提取其中的TS片段URL
        """
        selected_indices = self.m3u8_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("错误", "请选择M3U8链接")
            return
        
        # 清空内容列表
        self.m3u8_content_listbox.delete(0, tk.END)
        self.m3u8_content_listbox.insert(tk.END, "正在分析...")
        
        # 收集选中的M3U8链接
        m3u8_urls = []
        for idx in selected_indices:
            item = self.m3u8_listbox.get(idx)
            if item.startswith("---") or item.startswith("正在分析"):
                continue
            if item.startswith("http"):
                m3u8_urls.append(item)
        
        if not m3u8_urls:
            messagebox.showerror("错误", "没有有效的M3U8链接")
            return
        
        # 启动后台线程分析
        thread = threading.Thread(target=self.analyze_m3u8_content_thread, args=(m3u8_urls,))
        thread.daemon = True
        thread.start()
    
    def analyze_m3u8_content_thread(self, m3u8_urls):
        """
        在后台线程中解析M3U8文件内容，提取TS片段URL
        
        参数:
            m3u8_urls: M3U8链接列表
        """
        all_segments = []
        
        def parse_m3u8(url, level=0):
            """
            递归解析M3U8文件
            
            参数:
                url: M3U8文件URL
                level: 递归层级，防止无限递归
            返回:
                TS片段URL列表
            """
            try:
                headers = self.get_headers()
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                lines = response.text.split('\n')
                base_url = url.rsplit('/', 1)[0] + '/'  # 基础URL用于相对路径
                
                segments = []  # TS片段列表
                sub_m3u8s = []  # 子M3U8列表（主M3U8可能包含多个子M3U8）
                
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    # 检测流信息标签，下一行通常是M3U8或TS链接
                    if line.startswith('#EXT-X-STREAM-INF'):
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and not next_line.startswith('#'):
                                if next_line.startswith('http'):
                                    sub_m3u8s.append(next_line)
                                else:
                                    sub_m3u8s.append(base_url + next_line)
                    # 检测TS片段行
                    elif line and not line.startswith('#') and line.endswith('.ts'):
                        if line.startswith('http'):
                            segments.append(line)
                        else:
                            segments.append(base_url + line)
                    i += 1
                
                # 如果找到TS片段直接返回
                if segments:
                    return segments
                
                # 否则递归解析子M3U8
                for sub_url in sub_m3u8s:
                    sub_segments = parse_m3u8(sub_url, level + 1)
                    if sub_segments:
                        return sub_segments
                
                return []
                
            except Exception as e:
                return []
        
        # 解析每个M3U8文件
        for m3u8_url in m3u8_urls:
            try:
                segments = parse_m3u8(m3u8_url)
                
                if segments:
                    all_segments.extend(segments)
                    self.root.after(0, lambda u=m3u8_url, c=len(segments): self.video_progress_text.insert(tk.END, f"{u}: {c} 个TS切片\n"))
                else:
                    self.root.after(0, lambda u=m3u8_url: self.video_progress_text.insert(tk.END, f"{u}: 未找到切片\n"))
                
            except Exception as e:
                self.root.after(0, lambda msg=str(e): self.video_progress_text.insert(tk.END, f"分析失败: {msg}\n"))
        
        # 更新内容列表
        self.root.after(0, lambda: self.m3u8_content_listbox.delete(0, tk.END))
        
        for segment in all_segments:
            self.root.after(0, lambda s=segment: self.m3u8_content_listbox.insert(tk.END, s))
        
        self.root.after(0, lambda c=len(all_segments): self.m3u8_content_listbox.insert(tk.END, f"--- 共找到 {c} 个TS切片 ---"))
    
    def start_video_download(self):
        """
        开始视频下载
        验证输入后启动后台下载线程
        """
        selected_indices = self.m3u8_content_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("错误", "请选择要下载的TS片段")
            return
        
        save_path = self.video_save_path_entry.get().strip()
        if not save_path:
            messagebox.showerror("错误", "请选择保存路径")
            return
        
        # 验证输入参数
        try:
            delay = float(self.video_delay_entry.get())
            thread_count = int(self.video_thread_entry.get())
        except ValueError:
            messagebox.showerror("错误", "请求延时必须是数字，线程数量必须是整数")
            return
        
        if thread_count < 1 or thread_count > 100:
            messagebox.showerror("错误", "线程数量必须在1-100之间")
            return
        
        # 禁用开始按钮防止重复点击
        self.video_start_button.config(state=tk.DISABLED)
        self.downloaded_images.clear()
        
        # 收集选中的TS片段URL
        ts_urls = []
        for idx in selected_indices:
            item = self.m3u8_content_listbox.get(idx)
            if item.startswith("---") or item.startswith("正在分析"):
                continue
            ts_urls.append(item)
        
        if not ts_urls:
            messagebox.showerror("错误", "没有有效的TS片段")
            return
        
        # 启动下载线程
        thread = threading.Thread(target=self.download_ts_thread, args=(ts_urls, save_path, delay, thread_count))
        thread.daemon = True
        thread.start()
    
    def download_ts_thread(self, ts_urls, save_path, delay, thread_count):
        """
        在后台线程中下载TS片段并合并为MP4
        
        参数:
            ts_urls: TS片段URL列表
            save_path: 保存路径
            delay: 请求延时
            thread_count: 下载线程数
        """
        try:
            self.root.after(0, lambda: self.video_progress_text.insert(tk.END, f"开始下载 {len(ts_urls)} 个TS片段...\n"))
            
            video_url = self.video_url_entry.get().strip()
            custom_filename = self.video_filename_entry.get().strip()
            
            # 确定视频标题/文件名
            if custom_filename:
                title = self.sanitize_folder_name(custom_filename)
            else:
                # 如果没有自定义文件名，从网页提取标题
                headers = self.get_headers()
                response = requests.get(video_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                match = re.search(r'var _h="([^"]+)"', response.text)
                if match:
                    encoded = match.group(1)
                    try:
                        decoded = unquote(unquote(encoded))
                    except:
                        decoded = response.text
                    title_match = re.search(r'<title>([^<]+)</title>', decoded)
                    if title_match:
                        raw_title = title_match.group(1).strip()
                        for encoding in ['gbk', 'gb2312', 'gb18030', 'utf-8']:
                            try:
                                title = raw_title.encode('latin1').decode(encoding)
                                break
                            except:
                                continue
                        else:
                            title = self.sanitize_folder_name(response.text)
                            title_match2 = re.search(r'<title>([^<]+)</title>', response.text)
                            if title_match2:
                                raw_title2 = title_match2.group(1).strip()
                                for encoding in ['gbk', 'gb2312', 'gb18030', 'utf-8']:
                                    try:
                                        title = raw_title2.encode('latin1').decode(encoding)
                                        break
                                    except:
                                        continue
                    else:
                        title_match2 = re.search(r'<title>([^<]+)</title>', response.text)
                        if title_match2:
                            raw_title2 = title_match2.group(1).strip()
                            for encoding in ['gbk', 'gb2312', 'gb18030', 'utf-8']:
                                try:
                                    title = raw_title2.encode('latin1').decode(encoding)
                                    break
                                except:
                                    continue
                        if not title:
                            title = "video"
                else:
                    title = "video"
                if not title:
                    title = "video"
            
            # 创建保存文件夹
            title = self.sanitize_folder_name(title)
            page_save_path = os.path.join(save_path, title)
            os.makedirs(page_save_path, exist_ok=True)
            
            self.root.after(0, lambda t=title: self.video_progress_text.insert(tk.END, f"保存文件夹: {t}\n"))
            
            # 下载计数器和文件列表
            downloaded_count = [0]
            total_count = len(ts_urls)
            ts_files = []
            
            def download_one(ts_url):
                """
                下载单个TS片段
                
                参数:
                    ts_url: TS片段URL
                """
                try:
                    headers = self.get_headers()
                    resp = requests.get(ts_url, headers=headers, timeout=60, stream=True)
                    resp.raise_for_status()
                    
                    # 生成文件名（去除查询参数）
                    filename = os.path.basename(ts_url.split('?')[0]) or f"ts_{downloaded_count[0]}.ts"
                    file_path = os.path.join(page_save_path, filename)
                    
                    # 流式写入文件
                    with open(file_path, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    ts_files.append(file_path)
                    downloaded_count[0] += 1
                    self.root.after(0, lambda n=downloaded_count[0], t=total_count: self.video_progress_text.insert(tk.END, f"已下载 {n}/{t}\n"))
                
                except Exception as e:
                    self.root.after(0, lambda msg=str(e): self.video_progress_text.insert(tk.END, f"下载失败: {msg}\n"))
                
                time.sleep(delay)
            
            # 使用线程池并发下载
            with ThreadPoolExecutor(max_workers=min(thread_count, total_count)) as executor:
                list(executor.map(download_one, ts_urls))
            
            # 合并TS文件为MP4
            if ts_files:
                mp4_path = os.path.join(page_save_path, f"{title}.mp4")
                self.root.after(0, lambda: self.video_progress_text.insert(tk.END, f"正在合并TS文件...\n"))
                
                # 按文件名排序后合并
                with open(mp4_path, 'wb') as outfile:
                    for ts_file in sorted(ts_files):
                        try:
                            with open(ts_file, 'rb') as infile:
                                outfile.write(infile.read())
                        except Exception as e:
                            self.root.after(0, lambda msg=str(e): self.video_progress_text.insert(tk.END, f"读取文件失败: {msg}\n"))
                
                # 删除TS临时文件
                self.root.after(0, lambda: self.video_progress_text.insert(tk.END, f"正在删除TS文件...\n"))
                
                deleted_count = 0
                for ts_file in ts_files:
                    try:
                        if os.path.exists(ts_file):
                            os.remove(ts_file)
                            deleted_count += 1
                    except Exception as e:
                        self.root.after(0, lambda msg=str(e), ts=ts_file: self.video_progress_text.insert(tk.END, f"删除失败 {ts}: {msg}\n"))
                
                self.root.after(0, lambda t=title, c=deleted_count: self.video_progress_text.insert(tk.END, f"\n合并完成: {t}.mp4 (删除 {c} 个TS文件)\n"))
            else:
                self.root.after(0, lambda: self.video_progress_text.insert(tk.END, f"\n未下载任何文件\n"))
        
        except Exception as e:
            self.root.after(0, lambda msg=str(e): self.video_progress_text.insert(tk.END, f"错误: {msg}\n"))
        
        finally:
            # 重新启用开始按钮
            self.root.after(0, lambda: self.video_start_button.config(state=tk.NORMAL))
    
    def select_all_pages(self):
        """
        全选页面列表中的所有项目
        """
        self.url_listbox.select_set(0, tk.END)
    
    def deselect_all_pages(self):
        """
        取消全选页面列表
        """
        self.url_listbox.selection_clear(0, tk.END)
    
    def select_all_images(self):
        """
        全选图片列表中的所有项目
        """
        self.img_listbox.select_set(0, tk.END)
    
    def deselect_all_images(self):
        """
        取消全选图片列表
        """
        self.img_listbox.selection_clear(0, tk.END)
    
    def clear_img_list(self):
        """
        清空图片列表
        """
        self.img_listbox.delete(0, tk.END)
    
    def clear_url_list(self):
        """
        清空页面URL列表
        """
        self.url_listbox.delete(0, tk.END)
    
    def stop_analyze(self):
        """
        设置停止分析标志，用于中断批量分析过程
        """
        self.stop_analysis = True
    
    def log_message(self, message):
        """
        向单页下载标签页的进度文本框添加日志
        
        参数:
            message: 要显示的日志消息
        """
        self.root.after(0, lambda: self.progress_text.insert(tk.END, message + "\n"))
        self.root.after(0, lambda: self.progress_text.see(tk.END))  # 自动滚动到底部
    
    def batch_log_message(self, message):
        """
        向批量下载标签页的进度文本框添加日志
        
        参数:
            message: 要显示的日志消息
        """
        self.root.after(0, lambda: self.batch_progress_text.insert(tk.END, message + "\n"))
        self.root.after(0, lambda: self.batch_progress_text.see(tk.END))
    
    def clear_log(self):
        """
        清空单页下载标签页的日志文本
        """
        self.progress_text.delete(1.0, tk.END)
    
    def get_random_user_agent(self):
        """
        随机获取一个User-Agent字符串
        用于模拟不同浏览器，降低被反爬虫检测的概率
        
        返回:
            随机User-Agent字符串
        """
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
        ]
        return random.choice(user_agents)
    
    def get_headers(self, referer=None):
        """
        生成HTTP请求头
        包含随机的User-Agent和Accept-Language，模拟真实浏览器请求
        
        参数:
            referer: 来源页面URL（可选）
        返回:
            请求头字典
        """
        accept_languages = [
            "zh-CN,zh;q=0.9,en;q=0.8",
            "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "zh-CN,zh;q=0.9,en-US;q=0.8",
            "zh;q=0.9,en;q=0.8",
            "en-US,en;q=0.9,zh-CN;q=0.8"
        ]
        return {
            "User-Agent": self.get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": random.choice(accept_languages),
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "Referer": referer if referer else ""
        }
    
    def random_delay(self, base_delay):
        """
        执行随机延时
        在基础延时上增加0-1秒的随机值，模拟人类行为
        
        参数:
            base_delay: 基础延时秒数
        """
        import random
        delay = base_delay + random.uniform(0, 1)
        time.sleep(delay)
    
    def sanitize_folder_name(self, name):
        """
        清理文件夹名称，移除非法字符
        Windows文件名中不能包含: < > : " / \ | ? *
        
        参数:
            name: 原始名称
        返回:
            清理后的安全名称
        """
        name = re.sub(r'[<>:"/\\|?*]', '', name)  # 移除非法字符
        name = name.strip()[:100]  # 限制长度100字符
        return name if name else "images"  # 如果为空则返回默认值
    
    def extract_images_from_encoded_html(self, html_content):
        """
        从HTML内容中提取图片URL和页面标题
        支持双重URL编码的HTML内容
        
        参数:
            html_content: HTML页面内容
        返回:
            (图片URL列表, 页面标题) 元组
        """
        img_urls = []
        title = ""
        
        # 尝试查找双重编码的HTML（var _h变量）
        match = re.search(r'var _h="([^"]+)"', html_content)
        if match:
            encoded = match.group(1)
            decoded = unquote(unquote(encoded))
            
            # 提取标题 - decoded 已经是正确编码的字符串
            title_match = re.search(r'<title>([^<]+)</title>', decoded)
            if title_match:
                title = title_match.group(1).strip()
            
            # 提取图片URL
            img_urls = re.findall(r'<img[^>]+src=[\'"]([^\'"]+)[\'"]', decoded)
        
        # 如果没有找到编码内容或没有图片，使用BeautifulSoup解析原始HTML
        if not img_urls:
            soup = BeautifulSoup(html_content, 'lxml')
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            for img in soup.find_all('img'):
                src = img.get('src')
                if src:
                    img_urls.append(str(src))
        
        return list(set(img_urls)), title  # 去重后返回
    
    def download_image(self, url, folder_name, save_path, headers=None):
        """
        下载单张图片
        
        参数:
            url: 图片URL
            folder_name: 文件夹名称（用于日志）
            save_path: 保存路径
            headers: HTTP请求头（可选）
        返回:
            下载成功返回True，否则返回False
        """
        try:
            # 设置请求头
            if headers is None:
                headers = {
                    "User-Agent": self.get_random_user_agent(),
                    "Referer": url
                }
            else:
                headers["Referer"] = url
            
            # 发送请求
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 检查内容是否为空
            if not response.content:
                return False
            
            # 检查内容类型（仅下载JPG/JPEG图片）
            if not url.lower().endswith('.jpg') and not url.lower().endswith('.jpeg'):
                if 'image/jpeg' not in response.headers.get('content-type', ''):
                    return False
            
            # 计算MD5哈希用于去重
            image_hash = self.get_image_hash(response.content)
            if image_hash in self.downloaded_images:
                return False
            
            self.downloaded_images.add(image_hash)
            
            # 生成文件名
            filename = os.path.basename(url.split('?')[0]) or f"image_{len(self.downloaded_images)}.jpg"
            if not filename.lower().endswith(('.jpg', '.jpeg')):
                filename += ".jpg"
            
            file_path = os.path.join(save_path, filename)
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return True
            
        except Exception as e:
            return False
    
    def get_image_hash(self, image_data):
        """
        计算图片数据的MD5哈希值
        用于图片去重
        
        参数:
            image_data: 图片二进制数据
        返回:
            MD5哈希字符串
        """
        return hashlib.md5(image_data).hexdigest()
    
    def start_download(self):
        """
        单页下载：验证输入并启动下载线程
        """
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入网址URL")
            return
        
        save_path = self.save_path_entry.get().strip()
        if not save_path:
            messagebox.showerror("错误", "请选择保存路径")
            return
        
        # 验证输入
        try:
            delay = float(self.delay_entry.get())
            thread_count = int(self.thread_entry.get())
        except ValueError:
            messagebox.showerror("错误", "请求延时必须是数字，线程数量必须是整数")
            return
        
        if thread_count < 1 or thread_count > 100:
            messagebox.showerror("错误", "线程数量必须在1-100之间")
            return
        
        # 禁用开始按钮并清空已下载集合
        self.start_button.config(state=tk.DISABLED)
        self.downloaded_images.clear()
        
        # 启动下载线程
        thread = threading.Thread(target=self.download_thread, args=(url, save_path, delay, thread_count))
        thread.daemon = True
        thread.start()
    
    def download_thread(self, url, save_path, delay, thread_count):
        """
        单页下载的后台线程
        
        参数:
            url: 目标网页URL
            save_path: 保存路径
            delay: 请求延时
            thread_count: 下载线程数
        """
        try:
            self.log_message(f"开始处理网站: {url}")
            self.log_message("正在获取页面内容...")
            
            # 获取页面内容
            headers = {"User-Agent": self.get_random_user_agent()}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            self.log_message("正在解析页面内容...")
            
            # 提取图片URL和标题
            img_urls, title = self.extract_images_from_encoded_html(response.text)
            
            # 创建保存文件夹
            folder_name = self.sanitize_folder_name(title)
            page_save_path = os.path.join(save_path, folder_name)
            os.makedirs(page_save_path, exist_ok=True)
            
            self.log_message(f"保存文件夹: {folder_name}")
            
            # 筛选JPG图片
            image_urls = [img for img in img_urls if str(img).lower().endswith(('.jpg', '.jpeg')) or 'image' in str(img).lower()]
            
            self.log_message(f"发现 {len(image_urls)} 张图片")
            
            # 设置进度条
            total_count = len(image_urls)
            self.progress_bar['maximum'] = total_count
            downloaded_count = 0
            
            def download_one(img_url):
                """
                下载单张图片
                
                参数:
                    img_url: 图片URL
                """
                nonlocal downloaded_count
                # 将相对URL转换为绝对URL
                full_url = img_url if str(img_url).startswith('http') else urljoin(url, str(img_url))
                if self.download_image(full_url, folder_name, page_save_path):
                    downloaded_count += 1
                    self.root.after(0, lambda: self.progress_bar.configure(value=downloaded_count))
                    self.root.after(0, lambda: self.log_message(f"已下载 {downloaded_count}/{total_count}"))
                time.sleep(delay)
            
            # 使用线程池并发下载
            with ThreadPoolExecutor(max_workers=min(thread_count, total_count)) as executor:
                list(executor.map(download_one, image_urls))
            
            # 显示完成信息
            if downloaded_count > 0:
                self.log_message(f"\n下载完成!")
                self.log_message(f"总共下载: {downloaded_count} 张图片")
            else:
                self.log_message(f"\n下载完成!")
                self.log_message(f"未找到任何图片")
            
        except Exception as e:
            self.log_message(f"错误: {str(e)}")
            messagebox.showerror("错误", f"下载过程中出现错误:\n{str(e)}")
        
        finally:
            # 重新启用开始按钮
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
    
    def analyze_pages(self):
        """
        批量分析：分析网页中的所有分页
        查找"尾页"链接来确定总页数
        """
        url = self.batch_url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入起始网址")
            return
        
        # 清空列表并显示分析中
        self.url_listbox.delete(0, tk.END)
        self.url_listbox.insert(tk.END, "正在分析...")
        
        # 启动分析线程
        thread = threading.Thread(target=self.analyze_pages_thread, args=(url,))
        thread.daemon = True
        thread.start()
    
    def analyze_pages_thread(self, base_url):
        """
        批量分析的后台线程
        解析分页结构并生成所有页面的URL
        
        参数:
            base_url: 起始网页URL
        """
        headers = {"User-Agent": self.get_random_user_agent()}
        
        results = None
        error_msg = ""
        
        try:
            # 获取页面内容
            response = requests.get(base_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # 尝试提取图片和标题
            img_urls, title = self.extract_images_from_encoded_html(response.text)
            
            # 从URL路径中提取标题作为备用
            if not title:
                path_match = re.search(r'/art/([^/]+)/', base_url)
                if path_match:
                    title = path_match.group(1)
            
            page_name = title if title else "images"
            
            # 解析URL
            parsed = urlparse(base_url)
            path = parsed.path
            
            page_urls = []
            total_pages = 1
            base_path = ""
            
            # 查找尾页链接来确定总页数
            match = re.search(r'var _h="([^"]+)"', response.text)
            if match:
                encoded = match.group(1)
                decoded = unquote(unquote(encoded))
                
                last_page_match = re.search(r'<a[^>]+href="([^"]*index_(\d+)\.html)"[^>]*>尾页</a>', decoded)
                if last_page_match:
                    last_page_url = last_page_match.group(1)
                    total_pages = int(last_page_match.group(2))
                    
                    base_path = last_page_url.rsplit('/index_', 1)[0]
                    
                    # 生成所有页面的URL
                    for i in range(1, total_pages + 1):
                        if i == 1:
                            page_url = base_url
                        else:
                            page_url = f"{parsed.scheme}://{parsed.netloc}{base_path}/index_{i}.html"
                        
                        # 生成页面名称
                        if i == 1:
                            page_name_i = title if title else "images"
                        else:
                            page_name_i = f"{title}_{i}" if title else f"page_{i}"
                        
                        page_urls.append((page_url, page_name_i))
                else:
                    page_urls.append((base_url, page_name))
                    total_pages = 1
            
            # 备用逻辑：如果 var_h 不存在，从原始HTML中查找分页链接
            if not page_urls:
                # 查找所有 index_N.html 链接
                index_links = re.findall(r'href="([^"]*index_(\d+)\.html)"', response.text)
                if index_links:
                    # findall 返回元组列表 (完整匹配, 页码)，用索引访问
                    max_page = max(int(m[1]) for m in index_links)
                    total_pages = max_page
                    
                    # 提取基础路径
                    first_link = index_links[0][0]
                    base_path = first_link.rsplit('/index_', 1)[0].lstrip('/')
                    
                    for i in range(1, total_pages + 1):
                        if i == 1:
                            page_url = base_url
                        else:
                            page_url = f"{parsed.scheme}://{parsed.netloc}/{base_path}/index_{i}.html"
                        
                        if i == 1:
                            page_name_i = title if title else "images"
                        else:
                            page_name_i = f"{title}_{i}" if title else f"page_{i}"
                        
                        page_urls.append((page_url, page_name_i))
            
            # 如果仍然没有分页，至少添加当前页面
            if not page_urls:
                page_urls.append((base_url, page_name))
                total_pages = 1
            
            # 检查是否成功找到分页
            if not page_urls or (len(page_urls) == 1 and page_urls[0][0] == base_url and total_pages == 1):
                error_msg = "未找到分页信息"
                raise Exception(error_msg)
            
            results = page_urls
            result_count = len(results)
            
        except Exception as e:
            error_msg = str(e)
        
        def update_ui():
            """
            在UI线程中更新分析结果
            """
            self.url_listbox.delete(0, tk.END)
            if results:
                for url, name in results:
                    self.url_listbox.insert(tk.END, f"{name} | {url}")
                self.url_listbox.insert(tk.END, f"--- 共找到 {len(results)} 页 ---")
            else:
                self.url_listbox.insert(tk.END, f"分析失败: {error_msg}")
        
        self.root.after(0, update_ui)
    
    def analyze_images(self):
        """
        分析选中页面的图片链接
        提取页面中的<a>标签href属性值
        """
        selected_indices = self.url_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("错误", "请选择要分析的页面")
            return
        
        # 重置停止标志并启动分析线程
        self.stop_analysis = False
        thread = threading.Thread(target=self.analyze_images_thread, args=(selected_indices,))
        thread.daemon = True
        thread.start()
    
    def analyze_images_thread(self, selected_indices):
        """
        图片分析的后台线程
        从选中的页面提取图片链接
        
        参数:
            selected_indices: 选中的页面索引列表
        """
        prefix = self.prefix_entry.get().strip()  # 获取网址前缀
        try:
            base_delay = float(self.batch_delay_entry.get())
        except:
            base_delay = 2
        
        found_count = 0
        
        # 遍历选中的页面
        for idx in selected_indices:
            # 检查是否被要求停止
            if self.stop_analysis:
                self.root.after(0, lambda: self.batch_log_message("\n=== 已停止分析 ==="))
                return
            
            item = self.url_listbox.get(idx)
            if item.startswith("---") or item.startswith("正在分析"):
                continue
            # 从"名称 | URL"格式中提取URL
            if " | " in item:
                url = item.split(" | ", 1)[1]
            else:
                url = item
            
            try:
                # 获取页面内容
                headers = self.get_headers()
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                
                # 尝试解码内容
                match = re.search(r'var _h="([^"]+)"', response.text)
                page_urls = []  # 存储详情页URL
                
                if match:
                    encoded = match.group(1)
                    decoded = unquote(unquote(encoded))
                    
                    # 查找详情页链接（如 /art/toupaizipai/764307/）
                    # 模式：/art/分类名/数字/
                    category = re.search(r'/art/([^/]+)/', url)
                    if category:
                        category_name = category.group(1)
                        # 查找该分类下的详情页链接
                        links = re.findall(r'<a[^>]+href="(/art/' + category_name + r'/\d+/)"', decoded)
                        
                        for link in links:
                            full_url = 'https://www.v6491h.com' + link
                            page_urls.append(full_url)
                    
                    # 如果上面的模式没匹配，尝试通用模式
                    if not page_urls:
                        # 查找所有 /art/数字/ 模式的链接
                        links = re.findall(r'<a[^>]+href="(/art/\d{6,}/)"', decoded)
                        for link in links:
                            full_url = 'https://www.v6491h.com' + link
                            if full_url not in page_urls:
                                page_urls.append(full_url)
                
                # 没有 var_h，从原始HTML查找详情页链接
                if not page_urls:
                    # 查找 /art/分类名/数字/ 模式
                    category = re.search(r'/art/([^/]+)/', url)
                    if category:
                        category_name = category.group(1)
                        links = re.findall(r'href="(/art/' + category_name + r'/\d+/)"', response.text)
                        for link in links:
                            full_url = 'https://www.v6491h.com' + link
                            page_urls.append(full_url)
                
                # 去重
                page_urls = list(set(page_urls))
                
                # 添加到列表
                for page_url in page_urls[:100]:  # 限制数量
                    self.root.after(0, lambda u=page_url: self.img_listbox.insert(tk.END, u))
                
                found_count = len(page_urls)
                self.root.after(0, lambda c=found_count, u=url: self.batch_log_message(f"提取 {c} 个详情页: {u}"))
                
                # 随机延时
                self.random_delay(base_delay)
                        
            except Exception as e:
                self.root.after(0, lambda msg=f"分析失败 {url}: {str(e)}": self.batch_log_message(msg))
        
        # 显示完成信息
        self.root.after(0, lambda c=found_count: self.batch_log_message(f"\n=== 共提取 {c} 个页面 ==="))
    
    def download_selected_images(self):
        """
        下载选中的图片
        验证输入后启动下载线程
        """
        selected_indices = self.img_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("错误", "请选择要下载的网址")
            return
        
        save_path = self.batch_save_path_entry.get().strip()
        if not save_path:
            messagebox.showerror("错误", "请选择保存路径")
            return
        
        # 验证输入
        try:
            delay = float(self.batch_delay_entry.get())
            thread_count = int(self.batch_thread_entry.get())
        except ValueError:
            messagebox.showerror("错误", "请求延时必须是数字，线程数量必须是整数")
            return
        
        # 收集选中的图片URL
        img_urls = []
        
        for idx in selected_indices:
            item = self.img_listbox.get(idx)
            if item.startswith("---") or item.startswith("正在分析"):
                continue
            img_urls.append(item)
        
        if not img_urls:
            messagebox.showerror("错误", "没有有效的网址")
            return
        
        # 启动下载线程
        thread = threading.Thread(target=self.download_images_thread, args=(img_urls, save_path, delay, thread_count))
        thread.daemon = True
        thread.start()
    
    def download_images_thread(self, img_urls, save_path, delay, thread_count):
        """
        批量图片下载的后台线程
        
        参数:
            img_urls: 图片页面URL列表
            save_path: 保存路径
            delay: 请求延时
            thread_count: 下载线程数
        """
        total = len(img_urls)
        downloaded_count = 0
        
        self.root.after(0, lambda: self.batch_log_message(f"开始下载 {total} 个网址的图片..."))
        
        # 缓存方法引用以提高性能
        download_image = self.download_image
        get_headers = self.get_headers
        
        # 遍历每个图片页面
        for page_url in img_urls:
            try:
                # 跳过非HTTP链接
                if not page_url.startswith('http'):
                    continue
                
                # 获取页面内容
                headers = get_headers()
                response = requests.get(page_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # 提取图片URL和标题
                img_urls_on_page, page_title = self.extract_images_from_encoded_html(response.text)
                
                # 用当前详情页的标题作为文件夹名称
                if page_title:
                    folder_name = self.sanitize_folder_name(page_title)
                else:
                    # 如果没有标题，从URL提取
                    match = re.search(r'/art/([^/]+)/', page_url)
                    folder_name = match.group(1) if match else "images"
                
                # 为每个详情页创建独立的保存文件夹
                page_save_path = os.path.join(save_path, folder_name)
                os.makedirs(page_save_path, exist_ok=True)
                
                self.root.after(0, lambda n=folder_name: self.batch_log_message(f"正在下载: {n}"))
                
                # 筛选JPG图片
                image_urls = [img for img in img_urls_on_page if str(img).lower().endswith(('.jpg', '.jpeg')) or 'image' in str(img).lower()]
                
                page_downloaded = [0]
                
                def download_one(img_url):
                    """
                    下载单张图片
                    """
                    full_url = img_url if str(img_url).startswith('http') else urljoin(page_url, str(img_url))
                    img_headers = get_headers(page_url)
                    if download_image(full_url, folder_name, page_save_path, img_headers):
                        page_downloaded[0] += 1
                        nonlocal downloaded_count
                        downloaded_count += 1
                
                # 使用线程池并发下载
                if image_urls:
                    with ThreadPoolExecutor(max_workers=min(thread_count, len(image_urls))) as executor:
                        list(executor.map(download_one, image_urls))
                
                # 显示页面下载结果
                if page_downloaded[0] > 0:
                    self.root.after(0, lambda n=folder_name, c=page_downloaded[0]: self.batch_log_message(f"✓ {n}: {c} 张图片"))
                else:
                    self.root.after(0, lambda n=folder_name: self.batch_log_message(f"✗ {n}: 未找到图片"))
                
                # 随机延时
                self.random_delay(delay)
                
            except Exception as e:
                self.root.after(0, lambda msg=f"✗ 下载失败: {str(e)}": self.batch_log_message(msg))
        
        # 显示总下载完成信息
        self.root.after(0, lambda c=downloaded_count: self.batch_log_message(f"\n=== 下载完成: 共 {c} 张图片 ==="))


def main():
    """
    程序入口函数
    创建Tkinter根窗口并启动应用程序
    """
    root = tk.Tk()  # 创建主窗口
    app = PicGetApp(root)  # 初始化应用程序
    root.mainloop()  # 进入事件循环


if __name__ == "__main__":
    main()
