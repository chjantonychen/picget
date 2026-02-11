# PicGet - 网站图片下载工具

## 功能特点
- GUI界面，使用Python内置Tkinter
- 支持动态网站（Selenium处理JS渲染）
- 按a标签文本分类图片
- 图片去重（MD5哈希）
- 仅下载JPG格式图片
- 反爬虫措施：
  - 随机User-Agent
  - 请求延时
- ZIP打包下载

## 安装依赖
```bash
pip install -r requirements.txt
```

## 使用方法
1. 运行程序：`python picget.py`
2. 输入目标网址
3. 选择保存路径
4. 设置请求延时
5. 点击"开始下载"
6. 下载完成后自动生成ZIP压缩包

## 注意事项
- 需要安装Chrome浏览器和ChromeDriver
- 请勿设置过短的请求延时，以免被封
- 仅支持JPG格式图片
