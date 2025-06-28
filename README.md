# YouTube Toolkit (ytkit)

一个功能强大的 YouTube 工具集，支持项目化管理和批量下载。

## 功能特性

- 🚀 **项目化管理**: 为每个 YouTube 视频创建独立项目目录
- 📥 **智能下载**: 支持视频下载和字幕提取
- 🌐 **双语字幕**: 自动合并中英文字幕（英文在上，中文在下）
- 🎯 **URL 解析**: 支持多种 YouTube URL 格式
- 📁 **灵活路径**: 支持自定义下载目录
- 🔧 **模块化设计**: 面向对象，易于扩展

## 安装

### 前置要求

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (推荐) 或 pip

### 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/nonocast/ytkit.git
cd ytkit
```

2. 安装依赖：
```bash
uv sync
```

3. 创建软链接（可选，用于全局访问）：
```bash
# 方法1：使用系统目录（需要 sudo）
sudo ln -sf $(pwd)/ytkit /usr/local/bin/ytkit

# 方法2：使用用户目录（推荐）
mkdir -p ~/.local/bin
ln -sf $(pwd)/ytkit ~/.local/bin/ytkit
# 确保 ~/.local/bin 在你的 PATH 中
```

## 使用方法

### 1. 初始化项目 (`ytkit init`)

为 YouTube 视频创建项目目录：

```bash
# 基本用法
ytkit init "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# 指定目录
ytkit init --prefix ~/Desktop "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**功能说明：**
- 自动提取视频 ID
- 创建以视频 ID 命名的目录
- 在目录下生成 `.youtube` 配置文件
- 支持多种 YouTube URL 格式（包括带参数的链接）

**支持的 URL 格式：**
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/watch?v=VIDEO_ID&t=6s`
- `https://www.youtube.com/watch?v=VIDEO_ID&list=PLAYLIST_ID`

### 2. 下载内容 (`ytkit download`)

在项目目录中下载视频和相关资源：

```bash
# 进入项目目录
cd VIDEO_ID

# 下载所有内容
ytkit download
```

**下载内容：**
- 📹 **视频文件**: 自动选择最佳质量（1080p mp4_dash）
- 📝 **英文字幕**: `VIDEO_ID.en.srt`
- 📝 **中文字幕**: `VIDEO_ID.zh-Hans.srt`
- 🌐 **双语字幕**: `VIDEO_ID.bilingual.srt`（英文在上，中文在下）
- 🖼️ **封面图片**: `cover.jpg`

## 项目结构

```
项目目录/
├── .youtube              # 配置文件（存储原始URL）
├── VIDEO_ID.mp4          # 下载的视频文件
├── VIDEO_ID.en.srt       # 英文字幕
├── VIDEO_ID.zh-Hans.srt  # 中文字幕
├── VIDEO_ID.bilingual.srt # 双语字幕
└── cover.jpg             # 视频封面
```

## 命令参考

### `ytkit init`

```bash
ytkit init [OPTIONS] URL

Options:
  --prefix TEXT  指定创建目录的父路径 [默认: 当前目录]
  --help         显示帮助信息
```

### `ytkit download`

```bash
ytkit download [OPTIONS]

Options:
  --help         显示帮助信息
```

**注意**: `ytkit download` 需要在包含 `.youtube` 文件的项目目录中运行。

## 技术架构

```
ytkit/
├── main.py                 # 主入口文件
├── ytkit                   # 命令行脚本
├── tools/                  # 核心模块
│   ├── __init__.py
│   ├── utils.py           # 工具类（URL解析、项目管理）
│   └── commands/          # 命令模块
│       ├── __init__.py
│       ├── init.py        # init命令实现
│       └── download.py    # download命令实现
├── pyproject.toml         # 项目配置
└── .gitignore            # Git忽略文件
```

## 依赖

- **click**: 命令行界面框架
- **yt-dlp**: YouTube 下载器
- **requests**: HTTP 请求库

## 开发

### 添加新命令

1. 在 `tools/commands/` 下创建新命令文件
2. 在 `main.py` 中导入并注册命令
3. 遵循现有的模块化设计模式

### 本地开发

```bash
# 安装开发依赖
uv sync

# 运行测试
./ytkit init "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v0.1.0
- ✨ 初始版本发布
- 🎯 支持 `ytkit init` 命令
- 📥 支持 `ytkit download` 命令
- 🌐 支持双语字幕合并
- 📁 支持自定义下载目录
