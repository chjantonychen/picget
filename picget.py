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
    def __init__(self, root):
        self.root = root
        self.root.title("PicGet - 网站图片下载工具")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        self.driver = None
        self.downloaded_images = set()
        self.stop_analysis = False
        
        self.setup_ui()
    
    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.tab_single = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.tab_single, text="单页下载")
        
        self.tab_batch = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.tab_batch, text="批量分析")
        
        self.tab_video = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.tab_video, text="视频下载")
        
        self.setup_single_download_ui()
        self.setup_batch_download_ui()
        self.setup_video_download_ui()
    
    def setup_single_download_ui(self):
        url_frame = ttk.LabelFrame(self.tab_single, text="网站配置", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(url_frame, text="网址URL:").pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(url_frame, width=70)
        self.url_entry.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        
        settings_frame = ttk.LabelFrame(self.tab_single, text="下载设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(settings_frame, text="保存路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.save_path_entry = ttk.Entry(settings_frame, width=60)
        self.save_path_entry.grid(row=0, column=1, padx=(5, 5), pady=5, sticky=tk.W)
        self.save_path_entry.insert(0, "C:\\picget\\downloads")
        ttk.Button(settings_frame, text="浏览", command=self.browse_folder).grid(row=0, column=2, padx=(5, 0))
        
        ttk.Label(settings_frame, text="请求延时(秒):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.delay_entry = ttk.Entry(settings_frame, width=10)
        self.delay_entry.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        self.delay_entry.insert(0, "2")
        
        ttk.Label(settings_frame, text="线程数量:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.thread_entry = ttk.Entry(settings_frame, width=10)
        self.thread_entry.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        self.thread_entry.insert(0, "10")
        
        progress_frame = ttk.LabelFrame(self.tab_single, text="进度信息", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.progress_text = tk.Text(progress_frame, height=15, width=90)
        self.progress_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(progress_frame, orient=tk.VERTICAL, command=self.progress_text.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.progress_text.config(yscrollcommand=scrollbar.set)
        
        self.progress_bar = ttk.Progressbar(self.tab_single, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        button_frame = ttk.Frame(self.tab_single)
        button_frame.pack(fill=tk.X)
        
        self.start_button = ttk.Button(button_frame, text="开始下载", command=self.start_download)
        self.start_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.clear_button = ttk.Button(button_frame, text="清空日志", command=self.clear_log)
        self.clear_button.pack(side=tk.RIGHT)
    
    def setup_batch_download_ui(self):
        url_frame = ttk.LabelFrame(self.tab_batch, text="网址分析", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(url_frame, text="起始网址:").pack(side=tk.LEFT)
        self.batch_url_entry = ttk.Entry(url_frame, width=70)
        self.batch_url_entry.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        
        ttk.Button(url_frame, text="分析页数", command=self.analyze_pages).pack(side=tk.LEFT, padx=(0, 10))
        
        prefix_frame = ttk.Frame(url_frame)
        prefix_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(prefix_frame, text="网址前缀:").pack(side=tk.LEFT)
        self.prefix_entry = ttk.Entry(prefix_frame, width=50)
        self.prefix_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        settings_frame = ttk.LabelFrame(self.tab_batch, text="下载设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(settings_frame, text="保存路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.batch_save_path_entry = ttk.Entry(settings_frame, width=60)
        self.batch_save_path_entry.grid(row=0, column=1, padx=(5, 5), pady=5, sticky=tk.W)
        self.batch_save_path_entry.insert(0, "C:\\picget\\downloads")
        ttk.Button(settings_frame, text="浏览", command=self.browse_batch_folder).grid(row=0, column=2, padx=(5, 0))
        
        ttk.Label(settings_frame, text="请求延时(秒):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.batch_delay_entry = ttk.Entry(settings_frame, width=10)
        self.batch_delay_entry.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        self.batch_delay_entry.insert(0, "2")
        
        ttk.Label(settings_frame, text="线程数量:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.batch_thread_entry = ttk.Entry(settings_frame, width=10)
        self.batch_thread_entry.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        self.batch_thread_entry.insert(0, "50")
        
        list_frame = ttk.LabelFrame(self.tab_batch, text="页面列表 (支持Ctrl/Shift多选)", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.url_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=8)
        self.url_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.url_listbox.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.url_listbox.config(yscrollcommand=scrollbar.set)
        
        button_frame = ttk.Frame(self.tab_batch)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="全选", command=self.select_all_pages).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="取消全选", command=self.deselect_all_pages).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="分析图片地址", command=self.analyze_images).pack(side=tk.LEFT, padx=(20, 5))
        ttk.Button(button_frame, text="停止分析", command=self.stop_analyze).pack(side=tk.LEFT, padx=(5, 5))
        ttk.Button(button_frame, text="清空页面列表", command=self.clear_url_list).pack(side=tk.LEFT, padx=(5, 5))
        ttk.Button(button_frame, text="下载选中网址图片", command=self.download_selected_images).pack(side=tk.RIGHT, padx=(5, 0))
        
        img_list_frame = ttk.LabelFrame(self.tab_batch, text="图片链接", padding="10")
        img_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.img_listbox = tk.Listbox(img_list_frame, selectmode=tk.EXTENDED, height=8)
        self.img_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        img_scrollbar = ttk.Scrollbar(img_list_frame, orient=tk.VERTICAL, command=self.img_listbox.yview)
        img_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.img_listbox.config(yscrollcommand=img_scrollbar.set)
        
        img_button_frame = ttk.Frame(self.tab_batch)
        img_button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(img_button_frame, text="全选图片", command=self.select_all_images).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(img_button_frame, text="取消全选", command=self.deselect_all_images).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(img_button_frame, text="清空列表", command=self.clear_img_list).pack(side=tk.LEFT, padx=(20, 5))
        ttk.Button(img_button_frame, text="下载选中网址图片", command=self.download_selected_images).pack(side=tk.RIGHT, padx=(5, 0))
        
        batch_progress_frame = ttk.LabelFrame(self.tab_batch, text="下载进度", padding="10")
        batch_progress_frame.pack(fill=tk.X)
        
        self.batch_progress_text = tk.Text(batch_progress_frame, height=8, width=90)
        self.batch_progress_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        batch_scrollbar = ttk.Scrollbar(batch_progress_frame, orient=tk.VERTICAL, command=self.batch_progress_text.yview)
        batch_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.batch_progress_text.config(yscrollcommand=batch_scrollbar.set)
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="选择保存路径")
        if folder:
            self.save_path_entry.delete(0, tk.END)
            self.save_path_entry.insert(0, folder)
    
    def browse_batch_folder(self):
        folder = filedialog.askdirectory(title="选择保存路径")
        if folder:
            self.batch_save_path_entry.delete(0, tk.END)
            self.batch_save_path_entry.insert(0, folder)
    
    def setup_video_download_ui(self):
        url_frame = ttk.LabelFrame(self.tab_video, text="网站配置", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(url_frame, text="网址URL:").pack(side=tk.LEFT)
        self.video_url_entry = ttk.Entry(url_frame, width=70)
        self.video_url_entry.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        
        url_button_frame = ttk.Frame(url_frame)
        url_button_frame.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(url_button_frame, text="M3U8分析", command=self.analyze_m3u8).pack(side=tk.LEFT, padx=(0, 5))
        
        m3u8_frame = ttk.LabelFrame(self.tab_video, text="M3U8链接列表", padding="10")
        m3u8_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.m3u8_listbox = tk.Listbox(m3u8_frame, selectmode=tk.EXTENDED, height=6)
        self.m3u8_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        m3u8_scrollbar = ttk.Scrollbar(m3u8_frame, orient=tk.VERTICAL, command=self.m3u8_listbox.yview)
        m3u8_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.m3u8_listbox.config(yscrollcommand=m3u8_scrollbar.set)
        
        m3u8_content_frame = ttk.LabelFrame(self.tab_video, text="M3U8内容列表", padding="10")
        m3u8_content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.m3u8_content_listbox = tk.Listbox(m3u8_content_frame, selectmode=tk.EXTENDED, height=6)
        self.m3u8_content_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        m3u8_content_scrollbar = ttk.Scrollbar(m3u8_content_frame, orient=tk.VERTICAL, command=self.m3u8_content_listbox.yview)
        m3u8_content_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.m3u8_content_listbox.config(yscrollcommand=m3u8_content_scrollbar.set)
        
        m3u8_button_frame = ttk.Frame(self.tab_video)
        m3u8_button_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(m3u8_button_frame, text="分析M3U8内容", command=self.analyze_m3u8_content).pack(side=tk.LEFT)
        ttk.Button(m3u8_button_frame, text="清空M3U8列表", command=self.clear_m3u8_list).pack(side=tk.LEFT, padx=(10, 0))
        
        settings_frame = ttk.LabelFrame(self.tab_video, text="下载设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(settings_frame, text="保存路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.video_save_path_entry = ttk.Entry(settings_frame, width=60)
        self.video_save_path_entry.grid(row=0, column=1, padx=(5, 5), pady=5, sticky=tk.W)
        self.video_save_path_entry.insert(0, "C:\\picget\\downloads")
        ttk.Button(settings_frame, text="浏览", command=self.browse_video_folder).grid(row=0, column=2, padx=(5, 0))
        
        ttk.Label(settings_frame, text="MP4文件名:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.video_filename_entry = ttk.Entry(settings_frame, width=40)
        self.video_filename_entry.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        self.video_filename_entry.insert(0, "")
        
        ttk.Label(settings_frame, text="请求延时(秒):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.video_delay_entry = ttk.Entry(settings_frame, width=10)
        self.video_delay_entry.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        self.video_delay_entry.insert(0, "2")
        
        ttk.Label(settings_frame, text="线程数量:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.video_thread_entry = ttk.Entry(settings_frame, width=10)
        self.video_thread_entry.grid(row=3, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        self.video_thread_entry.insert(0, "10")
        
        progress_frame = ttk.LabelFrame(self.tab_video, text="下载进度", padding="10")
        progress_frame.pack(fill=tk.X)
        
        self.video_progress_text = tk.Text(progress_frame, height=8, width=90)
        self.video_progress_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(progress_frame, orient=tk.VERTICAL, command=self.video_progress_text.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.video_progress_text.config(yscrollcommand=scrollbar.set)
        
        button_frame = ttk.Frame(self.tab_video)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.video_start_button = ttk.Button(button_frame, text="开始下载", command=self.start_video_download)
        self.video_start_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.video_clear_button = ttk.Button(button_frame, text="清空日志", command=self.clear_video_log)
        self.video_clear_button.pack(side=tk.RIGHT)
    
    def browse_video_folder(self):
        folder = filedialog.askdirectory(title="选择保存路径")
        if folder:
            self.video_save_path_entry.delete(0, tk.END)
            self.video_save_path_entry.insert(0, folder)
    
    def clear_video_log(self):
        self.video_progress_text.delete(1.0, tk.END)
    
    def clear_m3u8_list(self):
        self.m3u8_listbox.delete(0, tk.END)
        self.m3u8_content_listbox.delete(0, tk.END)
    
    def analyze_m3u8(self):
        url = self.video_url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入网址URL")
            return
        
        self.m3u8_listbox.delete(0, tk.END)
        self.m3u8_listbox.insert(tk.END, "正在分析...")
        
        thread = threading.Thread(target=self.analyze_m3u8_thread, args=(url,))
        thread.daemon = True
        thread.start()
    
    def analyze_m3u8_thread(self, url):
        try:
            headers = self.get_headers()
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            match = re.search(r'var _h="([^"]+)"', response.text)
            if match:
                encoded = match.group(1)
                decoded = unquote(unquote(encoded))
            else:
                decoded = response.text
            
            title_match = re.search(r'<title>([^<]+)</title>', decoded)
            if not title_match:
                title_match = re.search(r'<title>([^<]+)</title>', response.text)
            
            if title_match:
                raw_title = title_match.group(1).strip()
                for encoding in ['gbk', 'gb2312', 'gb18030', 'utf-8']:
                    try:
                        title = raw_title.encode('latin1').decode(encoding)
                        self.root.after(0, lambda t=title: self.video_filename_entry.delete(0, tk.END))
                        self.root.after(0, lambda t=title: self.video_filename_entry.insert(0, t))
                        break
                    except:
                        continue
            
            m3u8_urls = []
            video_urls = []
            
            player_div = re.search(r'<div[^>]+id="player"[^>]*class="dplayer"[^>]*>(.*?)</div>', decoded, re.DOTALL)
            if player_div:
                player_content = player_div.group(1)
                
                json_match = re.search(r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', player_content)
                if json_match:
                    m3u8_url = json_match.group(1).replace('\\/', '/')
                    m3u8_urls.append(m3u8_url)
                
                m3u8_urls.extend(re.findall(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', player_content))
                video_urls = re.findall(r'src="([^"]+\.mp4[^"]*)"', player_content)
            
            if not m3u8_urls:
                json_match = re.search(r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', decoded)
                if json_match:
                    m3u8_url = json_match.group(1).replace('\\/', '/')
                    m3u8_urls.append(m3u8_url)
            
            if not m3u8_urls and not video_urls:
                m3u8_urls = re.findall(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', decoded.replace('\\/', '/'))
                video_urls = re.findall(r'src="([^"]+\.mp4[^"]*)"', decoded)
            
            m3u8_urls = list(set(m3u8_urls))
            video_urls = list(set(video_urls))
            
            self.root.after(0, lambda: self.m3u8_listbox.delete(0, tk.END))
            
            for m3u8_url in m3u8_urls:
                if m3u8_url.startswith('http'):
                    self.root.after(0, lambda u=m3u8_url: self.m3u8_listbox.insert(tk.END, u))
                else:
                    full_url = urljoin(url, m3u8_url)
                    self.root.after(0, lambda u=full_url: self.m3u8_listbox.insert(tk.END, u))
            
            for video_url in video_urls:
                if video_url.startswith('http'):
                    self.root.after(0, lambda u=video_url: self.m3u8_listbox.insert(tk.END, u))
                else:
                    full_url = urljoin(url, video_url)
                    self.root.after(0, lambda u=full_url: self.m3u8_listbox.insert(tk.END, u))
            
            total = len(m3u8_urls) + len(video_urls)
            self.root.after(0, lambda c=total: self.m3u8_listbox.insert(tk.END, f"--- 共找到 {c} 个链接 ---"))
            
            if total == 0:
                self.root.after(0, lambda: self.m3u8_listbox.insert(tk.END, "未找到M3U8或视频链接"))
                
        except Exception as e:
            self.root.after(0, lambda: self.m3u8_listbox.delete(0, tk.END))
            self.root.after(0, lambda msg=str(e): self.m3u8_listbox.insert(tk.END, f"分析失败: {msg}"))
    
    def analyze_m3u8_content(self):
        selected_indices = self.m3u8_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("错误", "请选择M3U8链接")
            return
        
        self.m3u8_content_listbox.delete(0, tk.END)
        self.m3u8_content_listbox.insert(tk.END, "正在分析...")
        
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
        
        thread = threading.Thread(target=self.analyze_m3u8_content_thread, args=(m3u8_urls,))
        thread.daemon = True
        thread.start()
    
    def analyze_m3u8_content_thread(self, m3u8_urls):
        all_segments = []
        
        def parse_m3u8(url, level=0):
            try:
                headers = self.get_headers()
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                lines = response.text.split('\n')
                base_url = url.rsplit('/', 1)[0] + '/'
                
                segments = []
                sub_m3u8s = []
                
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    if line.startswith('#EXT-X-STREAM-INF'):
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and not next_line.startswith('#'):
                                if next_line.startswith('http'):
                                    sub_m3u8s.append(next_line)
                                else:
                                    sub_m3u8s.append(base_url + next_line)
                    elif line and not line.startswith('#') and line.endswith('.ts'):
                        if line.startswith('http'):
                            segments.append(line)
                        else:
                            segments.append(base_url + line)
                    i += 1
                
                if segments:
                    return segments
                
                for sub_url in sub_m3u8s:
                    sub_segments = parse_m3u8(sub_url, level + 1)
                    if sub_segments:
                        return sub_segments
                
                return []
                
            except Exception as e:
                return []
        
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
        
        self.root.after(0, lambda: self.m3u8_content_listbox.delete(0, tk.END))
        
        for segment in all_segments:
            self.root.after(0, lambda s=segment: self.m3u8_content_listbox.insert(tk.END, s))
        
        self.root.after(0, lambda c=len(all_segments): self.m3u8_content_listbox.insert(tk.END, f"--- 共找到 {c} 个TS切片 ---"))
    
    def start_video_download(self):
        selected_indices = self.m3u8_content_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("错误", "请选择要下载的TS片段")
            return
        
        save_path = self.video_save_path_entry.get().strip()
        if not save_path:
            messagebox.showerror("错误", "请选择保存路径")
            return
        
        try:
            delay = float(self.video_delay_entry.get())
            thread_count = int(self.video_thread_entry.get())
        except ValueError:
            messagebox.showerror("错误", "请求延时必须是数字，线程数量必须是整数")
            return
        
        if thread_count < 1 or thread_count > 100:
            messagebox.showerror("错误", "线程数量必须在1-100之间")
            return
        
        self.video_start_button.config(state=tk.DISABLED)
        self.downloaded_images.clear()
        
        ts_urls = []
        for idx in selected_indices:
            item = self.m3u8_content_listbox.get(idx)
            if item.startswith("---") or item.startswith("正在分析"):
                continue
            ts_urls.append(item)
        
        if not ts_urls:
            messagebox.showerror("错误", "没有有效的TS片段")
            return
        
        thread = threading.Thread(target=self.download_ts_thread, args=(ts_urls, save_path, delay, thread_count))
        thread.daemon = True
        thread.start()
    
    def download_ts_thread(self, ts_urls, save_path, delay, thread_count):
        try:
            self.root.after(0, lambda: self.video_progress_text.insert(tk.END, f"开始下载 {len(ts_urls)} 个TS片段...\n"))
            
            video_url = self.video_url_entry.get().strip()
            custom_filename = self.video_filename_entry.get().strip()
            
            if custom_filename:
                title = self.sanitize_folder_name(custom_filename)
            else:
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
            
            title = self.sanitize_folder_name(title)
            page_save_path = os.path.join(save_path, title)
            os.makedirs(page_save_path, exist_ok=True)
            
            self.root.after(0, lambda t=title: self.video_progress_text.insert(tk.END, f"保存文件夹: {t}\n"))
            
            downloaded_count = [0]
            total_count = len(ts_urls)
            ts_files = []
            
            def download_one(ts_url):
                try:
                    headers = self.get_headers()
                    resp = requests.get(ts_url, headers=headers, timeout=60, stream=True)
                    resp.raise_for_status()
                    
                    filename = os.path.basename(ts_url.split('?')[0]) or f"ts_{downloaded_count[0]}.ts"
                    file_path = os.path.join(page_save_path, filename)
                    
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
            
            with ThreadPoolExecutor(max_workers=min(thread_count, total_count)) as executor:
                list(executor.map(download_one, ts_urls))
            
            if ts_files:
                mp4_path = os.path.join(page_save_path, f"{title}.mp4")
                self.root.after(0, lambda: self.video_progress_text.insert(tk.END, f"正在合并TS文件...\n"))
                
                with open(mp4_path, 'wb') as outfile:
                    for ts_file in sorted(ts_files):
                        try:
                            with open(ts_file, 'rb') as infile:
                                outfile.write(infile.read())
                        except Exception as e:
                            self.root.after(0, lambda msg=str(e): self.video_progress_text.insert(tk.END, f"读取文件失败: {msg}\n"))
                
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
            self.root.after(0, lambda: self.video_start_button.config(state=tk.NORMAL))
    
    def select_all_pages(self):
        self.url_listbox.select_set(0, tk.END)
    
    def deselect_all_pages(self):
        self.url_listbox.selection_clear(0, tk.END)
    
    def select_all_images(self):
        self.img_listbox.select_set(0, tk.END)
    
    def deselect_all_images(self):
        self.img_listbox.selection_clear(0, tk.END)
    
    def clear_img_list(self):
        self.img_listbox.delete(0, tk.END)
    
    def clear_url_list(self):
        self.url_listbox.delete(0, tk.END)
    
    def stop_analyze(self):
        self.stop_analysis = True
    
    def log_message(self, message):
        self.root.after(0, lambda: self.progress_text.insert(tk.END, message + "\n"))
        self.root.after(0, lambda: self.progress_text.see(tk.END))
    
    def batch_log_message(self, message):
        self.root.after(0, lambda: self.batch_progress_text.insert(tk.END, message + "\n"))
        self.root.after(0, lambda: self.batch_progress_text.see(tk.END))
    
    def clear_log(self):
        self.progress_text.delete(1.0, tk.END)
    
    def get_random_user_agent(self):
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
        import random
        delay = base_delay + random.uniform(0, 1)
        time.sleep(delay)
    
    def sanitize_folder_name(self, name):
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        name = name.strip()[:100]
        return name if name else "images"
    
    def extract_images_from_encoded_html(self, html_content):
        img_urls = []
        title = ""
        
        match = re.search(r'var _h="([^"]+)"', html_content)
        if match:
            encoded = match.group(1)
            decoded = unquote(unquote(encoded))
            
            title_match = re.search(r'<title>([^<]+)</title>', decoded)
            if title_match:
                title = title_match.group(1).strip()
            
            img_urls = re.findall(r'<img[^>]+src=[\'"]([^\'"]+)[\'"]', decoded)
        
        if not img_urls:
            soup = BeautifulSoup(html_content, 'lxml')
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            for img in soup.find_all('img'):
                src = img.get('src')
                if src:
                    img_urls.append(str(src))
        
        return list(set(img_urls)), title
    
    def download_image(self, url, folder_name, save_path, headers=None):
        try:
            if headers is None:
                headers = {
                    "User-Agent": self.get_random_user_agent(),
                    "Referer": url
                }
            else:
                headers["Referer"] = url
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            if not response.content:
                return False
            
            if not url.lower().endswith('.jpg') and not url.lower().endswith('.jpeg'):
                if 'image/jpeg' not in response.headers.get('content-type', ''):
                    return False
            
            image_hash = self.get_image_hash(response.content)
            if image_hash in self.downloaded_images:
                return False
            
            self.downloaded_images.add(image_hash)
            
            filename = os.path.basename(url.split('?')[0]) or f"image_{len(self.downloaded_images)}.jpg"
            if not filename.lower().endswith(('.jpg', '.jpeg')):
                filename += ".jpg"
            
            file_path = os.path.join(save_path, filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return True
            
        except Exception as e:
            return False
    
    def get_image_hash(self, image_data):
        return hashlib.md5(image_data).hexdigest()
    
    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入网址URL")
            return
        
        save_path = self.save_path_entry.get().strip()
        if not save_path:
            messagebox.showerror("错误", "请选择保存路径")
            return
        
        try:
            delay = float(self.delay_entry.get())
            thread_count = int(self.thread_entry.get())
        except ValueError:
            messagebox.showerror("错误", "请求延时必须是数字，线程数量必须是整数")
            return
        
        if thread_count < 1 or thread_count > 100:
            messagebox.showerror("错误", "线程数量必须在1-100之间")
            return
        
        self.start_button.config(state=tk.DISABLED)
        self.downloaded_images.clear()
        
        thread = threading.Thread(target=self.download_thread, args=(url, save_path, delay, thread_count))
        thread.daemon = True
        thread.start()
    
    def download_thread(self, url, save_path, delay, thread_count):
        try:
            self.log_message(f"开始处理网站: {url}")
            self.log_message("正在获取页面内容...")
            
            headers = {"User-Agent": self.get_random_user_agent()}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            self.log_message("正在解析页面内容...")
            
            img_urls, title = self.extract_images_from_encoded_html(response.text)
            
            folder_name = self.sanitize_folder_name(title)
            page_save_path = os.path.join(save_path, folder_name)
            os.makedirs(page_save_path, exist_ok=True)
            
            self.log_message(f"保存文件夹: {folder_name}")
            
            image_urls = [img for img in img_urls if str(img).lower().endswith(('.jpg', '.jpeg')) or 'image' in str(img).lower()]
            
            self.log_message(f"发现 {len(image_urls)} 张图片")
            
            total_count = len(image_urls)
            self.progress_bar['maximum'] = total_count
            downloaded_count = 0
            
            def download_one(img_url):
                nonlocal downloaded_count
                full_url = img_url if str(img_url).startswith('http') else urljoin(url, str(img_url))
                if self.download_image(full_url, folder_name, page_save_path):
                    downloaded_count += 1
                    self.root.after(0, lambda: self.progress_bar.configure(value=downloaded_count))
                    self.root.after(0, lambda: self.log_message(f"已下载 {downloaded_count}/{total_count}"))
                time.sleep(delay)
            
            with ThreadPoolExecutor(max_workers=min(thread_count, total_count)) as executor:
                list(executor.map(download_one, image_urls))
            
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
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
    
    def analyze_pages(self):
        url = self.batch_url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入起始网址")
            return
        
        self.url_listbox.delete(0, tk.END)
        self.url_listbox.insert(tk.END, "正在分析...")
        
        thread = threading.Thread(target=self.analyze_pages_thread, args=(url,))
        thread.daemon = True
        thread.start()
    
    def analyze_pages_thread(self, base_url):
        headers = {"User-Agent": self.get_random_user_agent()}
        
        results = None
        error_msg = ""
        
        try:
            response = requests.get(base_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            img_urls, title = self.extract_images_from_encoded_html(response.text)
            
            if not img_urls:
                error_msg = "未找到图片"
                raise Exception(error_msg)
            
            page_name = title if title else "images"
            
            parsed = urlparse(base_url)
            path = parsed.path
            
            page_urls = []
            total_pages = 1
            base_path = ""
            
            match = re.search(r'var _h="([^"]+)"', response.text)
            if match:
                encoded = match.group(1)
                decoded = unquote(unquote(encoded))
                
                last_page_match = re.search(r'<a[^>]+href="([^"]*index_(\d+)\.html)"[^>]*>尾页</a>', decoded)
                if last_page_match:
                    last_page_url = last_page_match.group(1)
                    total_pages = int(last_page_match.group(2))
                    
                    base_path = last_page_url.rsplit('/index_', 1)[0]
                    
                    for i in range(1, total_pages + 1):
                        if i == 1:
                            page_url = base_url
                        else:
                            page_url = f"{parsed.scheme}://{parsed.netloc}{base_path}/index_{i}.html"
                        
                        if i == 1:
                            page_name_i = title if title else "images"
                        else:
                            page_name_i = f"{title}_{i}" if title else f"page_{i}"
                        
                        page_urls.append((page_url, page_name_i))
                else:
                    page_urls.append((base_url, page_name))
                    total_pages = 1
            
            results = page_urls
            result_count = len(results)
            
        except Exception as e:
            error_msg = str(e)
        
        def update_ui():
            self.url_listbox.delete(0, tk.END)
            if results:
                for url, name in results:
                    self.url_listbox.insert(tk.END, f"{name} | {url}")
                self.url_listbox.insert(tk.END, f"--- 共找到 {len(results)} 页 ---")
            else:
                self.url_listbox.insert(tk.END, f"分析失败: {error_msg}")
        
        self.root.after(0, update_ui)
    
    def analyze_images(self):
        selected_indices = self.url_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("错误", "请选择要分析的页面")
            return
        
        self.stop_analysis = False
        thread = threading.Thread(target=self.analyze_images_thread, args=(selected_indices,))
        thread.daemon = True
        thread.start()
    
    def analyze_images_thread(self, selected_indices):
        prefix = self.prefix_entry.get().strip()
        try:
            base_delay = float(self.batch_delay_entry.get())
        except:
            base_delay = 2
        
        found_count = 0
        
        for idx in selected_indices:
            if self.stop_analysis:
                self.root.after(0, lambda: self.batch_log_message("\n=== 已停止分析 ==="))
                return
            
            item = self.url_listbox.get(idx)
            if item.startswith("---") or item.startswith("正在分析"):
                continue
            if " | " in item:
                url = item.split(" | ", 1)[1]
            else:
                url = item
            
            try:
                headers = self.get_headers()
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                
                match = re.search(r'var _h="([^"]+)"', response.text)
                if match:
                    encoded = match.group(1)
                    decoded = unquote(unquote(encoded))
                    
                    div_match = re.search(r'<div[^>]+id="tpl-img-content"[^>]*>(.*?)</div>', decoded, re.DOTALL)
                    if div_match:
                        links = re.findall(r'<a[^>]+href="([^"]+)"', div_match.group(1))
                    else:
                        links = re.findall(r'<a[^>]+href="([^"]+)"', decoded)
                    
                    for link in links:
                        if link and link.startswith('/'):
                            if prefix:
                                full_url = prefix + link
                            else:
                                full_url = link
                            self.root.after(0, lambda u=full_url: self.img_listbox.insert(tk.END, u))
                    
                    found_count += len([l for l in links if l and l.startswith('/')])
                    self.root.after(0, lambda c=len([l for l in links if l and l.startswith('/')]), u=url: self.batch_log_message(f"提取 {c} 个页面: {u}"))
                
                self.random_delay(base_delay)
                        
            except Exception as e:
                self.root.after(0, lambda msg=f"分析失败 {url}: {str(e)}": self.batch_log_message(msg))
        
        self.root.after(0, lambda c=found_count: self.batch_log_message(f"\n=== 共提取 {c} 个页面 ==="))
    
    def download_selected_images(self):
        selected_indices = self.img_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("错误", "请选择要下载的网址")
            return
        
        save_path = self.batch_save_path_entry.get().strip()
        if not save_path:
            messagebox.showerror("错误", "请选择保存路径")
            return
        
        try:
            delay = float(self.batch_delay_entry.get())
            thread_count = int(self.batch_thread_entry.get())
        except ValueError:
            messagebox.showerror("错误", "请求延时必须是数字，线程数量必须是整数")
            return
        
        img_urls = []
        for idx in selected_indices:
            item = self.img_listbox.get(idx)
            if item.startswith("---") or item.startswith("正在分析"):
                continue
            img_urls.append(item)
        
        if not img_urls:
            messagebox.showerror("错误", "没有有效的网址")
            return
        
        thread = threading.Thread(target=self.download_images_thread, args=(img_urls, save_path, delay, thread_count))
        thread.daemon = True
        thread.start()
    
    def download_images_thread(self, img_urls, save_path, delay, thread_count):
        total = len(img_urls)
        downloaded_count = 0
        
        self.root.after(0, lambda: self.batch_log_message(f"开始下载 {total} 个网址的图片..."))
        
        download_image = self.download_image
        get_headers = self.get_headers
        
        for page_url in img_urls:
            try:
                if not page_url.startswith('http'):
                    continue
                
                headers = get_headers()
                response = requests.get(page_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                img_urls_on_page, title = self.extract_images_from_encoded_html(response.text)
                
                folder_name = self.sanitize_folder_name(title)
                page_save_path = os.path.join(save_path, folder_name)
                os.makedirs(page_save_path, exist_ok=True)
                
                self.root.after(0, lambda n=folder_name: self.batch_log_message(f"正在下载: {n}"))
                
                image_urls = [img for img in img_urls_on_page if str(img).lower().endswith(('.jpg', '.jpeg')) or 'image' in str(img).lower()]
                
                page_downloaded = [0]
                
                def download_one(img_url):
                    full_url = img_url if str(img_url).startswith('http') else urljoin(page_url, str(img_url))
                    img_headers = get_headers(page_url)
                    if download_image(full_url, folder_name, page_save_path, img_headers):
                        page_downloaded[0] += 1
                        nonlocal downloaded_count
                        downloaded_count += 1
                
                if image_urls:
                    with ThreadPoolExecutor(max_workers=min(thread_count, len(image_urls))) as executor:
                        list(executor.map(download_one, image_urls))
                
                if page_downloaded[0] > 0:
                    self.root.after(0, lambda n=folder_name, c=page_downloaded[0]: self.batch_log_message(f"✓ {n}: {c} 张图片"))
                else:
                    self.root.after(0, lambda n=folder_name: self.batch_log_message(f"✗ {n}: 未找到图片"))
                
                self.random_delay(delay)
                
            except Exception as e:
                self.root.after(0, lambda msg=f"✗ 下载失败: {str(e)}": self.batch_log_message(msg))
        
        self.root.after(0, lambda c=downloaded_count: self.batch_log_message(f"\n=== 下载完成: 共 {c} 张图片 ==="))


def main():
    root = tk.Tk()
    app = PicGetApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()