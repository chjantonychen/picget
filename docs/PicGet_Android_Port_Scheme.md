# PicGet Android 移植方案

## 一、需求分析

### 1.1 原项目功能

| 功能模块 | 描述 |
|---------|------|
| 单页下载 | 输入URL，解析网页图片并下载 |
| 批量分析 | 分析多页URL规律，批量下载 |
| 视频下载 | M3U8视频流解析与合并 |
| GUI界面 | Tkinter桌面界面 |

### 1.2 Android移植挑战

| 挑战项 | 桌面方案 | Android方案 |
|--------|----------|-------------|
| UI框架 | Tkinter | Jetpack Compose |
| 网络请求 | requests | OkHttp / Retrofit |
| JS渲染 | Selenium + ChromeDriver | WebView + JSInterface |
| 视频处理 | ffmpeg命令行 | FFmpegKit (Android) |
| 存储 | 本地文件系统 | SAF (Storage Access Framework) |
| 并发 | ThreadPoolExecutor | Kotlin Coroutines |

---

## 二、技术选型

### 2.1 推荐技术栈

```
┌─────────────────────────────────────────────────────────┐
│                      UI 层                               │
│  Jetpack Compose (Material Design 3)                   │
├─────────────────────────────────────────────────────────┤
│                    业务逻辑层                            │
│  ViewModel + Kotlin Coroutines + Flow                   │
├─────────────────────────────────────────────────────────┤
│                    数据层                                │
│  OkHttp + Retrofit + Jsoup (HTML解析)                   │
├─────────────────────────────────────────────────────────┤
│                    原生能力层                            │
│  WebView + FFmpegKit + DownloadManager                  │
└─────────────────────────────────────────────────────────┘
```

### 2.2 关键依赖

```kotlin
// build.gradle (app)
dependencies {
    // UI
    implementation("androidx.compose.ui:ui:1.5.0")
    implementation("androidx.compose.material3:material3:1.1.0")
    
    // 网络
    implementation("com.squareup.okhttp3:okhttp:4.11.0")
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    
    // HTML解析
    implementation("org.jsoup:jsoup:1.16.1")
    
    // 视频处理
    implementation("com.arthenica:ffmpeg-kit-full:6.0-2")
    
    // 图片加载
    implementation("io.coil-kt:coil-compose:2.4.0")
    
    // JSON
    implementation("com.google.code.gson:gson:2.10.1")
}
```

---

## 三、架构设计

### 3.1 模块划分

```
com.picget.app/
├── ui/                      # UI层
│   ├── theme/              # 主题配置
│   ├── screens/            # 页面
│   │   ├── SingleDownloadScreen.kt
│   │   ├── BatchDownloadScreen.kt
│   │   └── VideoDownloadScreen.kt
│   └── components/         # 通用组件
│
├── viewmodel/              # ViewModel层
│   ├── SingleDownloadViewModel.kt
│   ├── BatchDownloadViewModel.kt
│   └── VideoDownloadViewModel.kt
│
├── data/                   # 数据层
│   ├── repository/         # 仓库
│   ├── network/            # 网络相关
│   │   ├── HttpClient.kt
│   │   └── ApiService.kt
│   └── parser/             # 解析器
│       ├── HtmlParser.kt
│       └── M3U8Parser.kt
│
├── domain/                 # 领域层
│   ├── model/             # 数据模型
│   └── usecase/           # 用例
│
└── util/                   # 工具类
    ├── FileUtils.kt
    ├── M3U8Downloader.kt
    └── ImageUtils.kt
```

### 3.2 核心流程

#### 单页图片下载流程

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  输入URL     │────▶│ WebView加载  │────▶│ 注入JS获取   │
└──────────────┘     │ (可选渲染)   │     │ 图片URL列表  │
                     └──────────────┘     └──────┬───────┘
                                                │
                     ┌──────────────┐     ┌──────▼───────┐
                     │  去重过滤    │◀────│  解析DOM     │
                     │  (MD5)       │     │  (Jsoup)     │
                     └──────┬───────┘     └──────────────┘
                            │
                     ┌──────▼───────┐
                     │  多线程下载  │
                     │  (Coroutines)│
                     └──────┬───────┘
                            │
                     ┌──────▼───────┐
                     │  保存到存储  │
                     │  (SAF)       │
                     └──────────────┘
```

---

## 四、详细设计

### 4.1 单页下载模块

```kotlin
// SingleDownloadViewModel.kt
class SingleDownloadViewModel : ViewModel() {
    
    private val _uiState = MutableStateFlow(DownloadUiState())
    val uiState: StateFlow<DownloadUiState> = _uiState.asStateFlow()
    
    fun startDownload(url: String, savePath: Uri) {
        viewModelScope.launch {
            _uiState.update { it.copy(status = Status.Loading) }
            
            try {
                // 1. 获取页面HTML
                val html = httpClient.get(url)
                
                // 2. 解析图片URL
                val imageUrls = htmlParser.extractImageUrls(html, url)
                
                // 3. 去重
                val uniqueUrls = deduplicate(imageUrls)
                
                // 4. 下载图片
                val results = downloader.downloadMultiple(
                    urls = uniqueUrls,
                    saveDir = savePath,
                    onProgress = { current, total ->
                        _uiState.update { it.copy(progress = current to total) }
                    }
                )
                
                _uiState.update { it.copy(status = Status.Success(results)) }
            } catch (e: Exception) {
                _uiState.update { it.copy(status = Status.Error(e.message)) }
            }
        }
    }
}
```

### 4.2 批量分析模块

```kotlin
// BatchDownloadViewModel.kt
class BatchDownloadViewModel : ViewModel() {
    
    fun analyzeUrlPattern(startUrl: String): UrlPatternResult {
        // 1. 访问起始页面
        // 2. 解析分页规律
        // 3. 生成完整URL列表
        // 4. 返回待下载URL列表
    }
    
    fun batchDownload(urls: List<String>, settings: DownloadSettings) {
        // 使用WorkManager进行后台下载
        // 支持断点续传
    }
}
```

### 4.3 视频下载模块

```kotlin
// M3U8Downloader.kt
class M3U8Downloader {
    
    suspend fun download(
        m3u8Url: String,
        outputPath: String,
        onProgress: (Float) -> Unit
    ) {
        // 1. 下载并解析m3u8文件
        val m3u8Content = okHttpClient.get(m3u8Url)
        val tsUrls = m3u8Parser.parse(m3u8Content, m3u8Url)
        
        // 2. 下载所有ts片段
        val tempDir = createTempDir()
        tsUrls.forEachIndexed { index, url ->
            downloadTs(url, "$tempDir/segment_$index.ts")
            onProgress(index.toFloat() / tsUrls.size)
        }
        
        // 3. 合并ts文件
        ffmpegKit.runCommand("-i concat:... -c copy $outputPath")
        
        // 4. 清理临时文件
        tempDir.deleteRecursively()
    }
}
```

### 4.4 WebView集成（JS渲染）

```kotlin
// WebViewHelper.kt
class WebViewHelper(private val context: Context) {
    
    private val webView = WebView(context).apply {
        settings.javaScriptEnabled = true
    }
    
    fun getImagesWithJavaScript(url: String): List<String> {
        // 注入JS获取动态加载的图片
        val js = """
            (function() {
                var images = [];
                document.querySelectorAll('img').forEach(img => {
                    if (img.src) images.push(img.src);
                });
                document.querySelectorAll('[style*="background-image"]').forEach(el => {
                    var match = el.style.backgroundImage.match(/url\(["']?(.+?)["']?\)/);
                    if (match) images.push(match[1]);
                });
                return images;
            })();
        """.trimIndent()
        
        return webView.evaluateJavascript(js, null)
    }
}
```

---

## 五、权限设计

### 5.1 AndroidManifest.xml

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    
    <!-- 网络权限 -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    
    <!-- 存储权限 (Android 10以下) -->
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" 
        android:maxSdkVersion="28" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" 
        android:maxSdkVersion="32" />
    
    <!-- Android 13+ 媒体权限 -->
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
    <uses-permission android:name="android.permission.READ_MEDIA_VIDEO" />
    
    <!-- 通知权限 (下载进度) -->
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    
    <!-- 前台服务 (后台下载) -->
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_DATA_SYNC" />
    
</manifest>
```

### 5.2 运行时权限处理

```kotlin
// PermissionHelper.kt
class PermissionHelper(private val activity: Activity) {
    
    fun requestStoragePermissions() {
        when {
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU -> {
                // Android 13+
                activity.requestPermissions(
                    arrayOf(
                        android.Manifest.permission.READ_MEDIA_IMAGES,
                        android.Manifest.permission.READ_MEDIA_VIDEO
                    ),
                    REQUEST_CODE_MEDIA
                )
            }
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q -> {
                // Android 10-12: 使用SAF，无需权限
            }
            else -> {
                // Android 9以下
                activity.requestPermissions(
                    arrayOf(android.Manifest.permission.WRITE_EXTERNAL_STORAGE),
                    REQUEST_CODE_STORAGE
                )
            }
        }
    }
}
```

---

## 六、UI设计

### 6.1 页面结构

```
┌─────────────────────────────┐
│        PicGet              │  ← 顶部标题栏
├─────────────────────────────┤
│  [单页] [批量] [视频]       │  ← Tab导航
├─────────────────────────────┤
│                             │
│     各Tab内容区域           │
│                             │
│                             │
│                             │
├─────────────────────────────┤
│  ━━━━━━━━━━━━░░░░░░  60%   │  ← 底部进度条
└─────────────────────────────┘
```

### 6.2 单页下载界面

```
┌────────────────────────────────────┐
│ 单页下载                           │
├────────────────────────────────────┤
│                                    │
│  网址: [https://example.com    ]  │
│                                    │
│  保存到: [选择文件夹          ] 📁 │
│                                    │
│  ☑ 启用JS渲染 (WebView)           │
│                                    │
│  [      开始下载      ]            │
│                                    │
├────────────────────────────────────┤
│ 已找到 25 张图片                   │
│                                    │
│ □ image1.jpg          120KB   ✓   │
│ □ image2.jpg          98KB    ✓   │
│ □ image3.jpg          150KB   ✓   │
│   ...                              │
│                                    │
│ 已下载: 15/25                      │
│ ████████████░░░░░░░░░  60%         │
└────────────────────────────────────┘
```

---

## 七、性能优化

### 7.1 下载优化

| 优化项 | 实现方式 |
|--------|----------|
| 并发下载 | Kotlin Coroutines (max 5并发) |
| 断点续传 | OkHttp Range请求支持 |
| 内存优化 | Flow控制 + 磁盘缓存 |
| 电量优化 | WorkManager + 低电量跳过 |

### 7.2 WebView优化

| 优化项 | 实现方式 |
|--------|----------|
| 缓存 | WebView独立进程 |
| 内存 | 及时destroy() |
| 渲染 | 启用硬件加速 |

---

## 八、开发计划

### 8.1 MVP阶段 (4周)

| 周次 | 任务 |
|------|------|
| 第1周 | 项目搭建 + UI框架 |
| 第2周 | 单页下载核心逻辑 |
| 第3周 | 网络层 + HTML解析 |
| 第4周 | 集成测试 + Bug修复 |

### 8.2 完整版阶段 (4周)

| 周次 | 任务 |
|------|------|
| 第5周 | 批量分析功能 |
| 第6周 | 视频下载(M3U8) |
| 第7周 | 权限适配 + 后台下载 |
| 第8周 | 优化 + 发布 |

---

## 九、总结

此方案将原Python桌面应用完全重写为Android原生应用：
- 使用现代Android开发技术 (Kotlin + Compose + Coroutines)
- 保留核心功能（图片下载、批量分析、视频下载）
- 针对Android特性做了专门适配（权限、存储、后台服务）

如需开始实现，我可以帮你生成项目初始代码结构。
