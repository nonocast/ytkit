# YouTube工具集 (yt)

一个功能强大的YouTube工具集，支持视频下载、音频转录等功能。

## 功能特性

- 🎥 **视频下载**: 支持多种格式的YouTube视频下载
- 🎤 **音频转录**: 使用OpenAI Whisper模型进行高质量转录
- ⚙️ **配置管理**: 灵活的配置系统
- 🛠️ **面向对象设计**: 清晰的代码结构和易于扩展

## 安装

```bash
# 克隆项目
git clone <repository-url>
cd yt

# 安装依赖
pip install -e .
```

## 使用方法

### 初始化

首次使用需要初始化工具：

```bash
yt init
```

这会创建必要的目录和配置文件。

### 下载视频

```bash
# 下载最佳质量视频
yt download https://www.youtube.com/watch?v=VIDEO_ID

# 指定格式
yt download https://www.youtube.com/watch?v=VIDEO_ID --format 720p

# 指定输出文件
yt download https://www.youtube.com/watch?v=VIDEO_ID --output video.mp4
```

### 转录音频

```bash
# 转录音频文件
yt transcript audio.mp3

# 指定输出文件
yt transcript audio.mp3 --output transcript.txt

# 使用特定模型
yt transcript audio.mp3 --model large
```

### 配置管理

```bash
# 查看当前配置
yt config

# 设置配置项
yt set-config download_dir /path/to/downloads
```

## 项目结构

```
yt/
├── yt/
│   ├── __init__.py
│   ├── main.py              # 主入口
│   ├── commands/            # 命令模块
│   │   ├── __init__.py
│   │   ├── base.py          # 命令基类
│   │   ├── init.py          # 初始化命令
│   │   ├── download.py      # 下载命令
│   │   └── transcript.py    # 转录命令
│   ├── config/              # 配置管理
│   │   ├── __init__.py
│   │   └── manager.py       # 配置管理器
│   └── utils/               # 工具模块
│       ├── __init__.py
│       └── helpers.py       # 辅助函数
├── pyproject.toml
└── README.md
```

## 依赖

- `click`: CLI框架
- `yt-dlp`: YouTube下载器
- `openai-whisper`: 音频转录
- `requests`: HTTP请求

## 开发

### 添加新命令

1. 在 `yt/commands/` 目录下创建新的命令文件
2. 继承 `BaseCommand` 类
3. 实现 `execute()` 和 `get_help()` 方法
4. 在 `yt/main.py` 中添加对应的CLI命令

### 示例

```python
from .base import BaseCommand

class MyCommand(BaseCommand):
    def execute(self, **kwargs) -> bool:
        # 实现命令逻辑
        return True
    
    def get_help(self) -> str:
        return "我的命令描述"
```

## 许可证

MIT License
