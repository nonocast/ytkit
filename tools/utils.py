"""
YouTube工具集 - 工具函数
"""
import re
import os
from pathlib import Path


class YouTubeURLParser:
    """YouTube URL解析器"""
    
    @staticmethod
    def extract_video_id(url: str) -> str:
        """从YouTube URL中提取视频ID，支持多参数和多格式"""
        # 1. 先尝试短链接和embed
        patterns = [
            r'(?:youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        # 2. 处理watch?v=xxx&... 这种情况，提取v参数
        match = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def is_valid_youtube_url(url: str) -> bool:
        """检查是否是有效的YouTube URL"""
        return YouTubeURLParser.extract_video_id(url) is not None


class ProjectManager:
    """项目目录管理器"""
    
    def __init__(self, prefix: str = '.'):
        self.prefix = prefix
    
    def create_project(self, video_id: str, url: str) -> bool:
        """创建项目目录和配置文件"""
        target_dir = os.path.join(os.path.expanduser(self.prefix), video_id)
        youtube_file_path = os.path.join(target_dir, '.youtube')
        
        # 检查.youtube文件是否已存在
        if os.path.exists(youtube_file_path):
            return False, f"配置文件 '{youtube_file_path}' 已存在，跳过创建"
        
        try:
            # 创建目录（如果不存在）
            os.makedirs(target_dir, exist_ok=True)
            
            # 创建.youtube文件并写入URL
            with open(youtube_file_path, 'w', encoding='utf-8') as f:
                f.write(url)
            
            return True, target_dir
            
        except Exception as e:
            return False, f"创建目录时出错: {e}" 