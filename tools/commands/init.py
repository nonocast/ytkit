"""
YouTube工具集 - init命令
"""
import click
from ..utils import YouTubeURLParser, ProjectManager


class InitCommand:
    """初始化命令处理器"""
    
    @staticmethod
    @click.command()
    @click.argument('url', required=True)
    @click.option('--prefix', default=None, show_default=True, help='指定创建目录的父路径')
    @click.pass_context
    def init(ctx, url: str, prefix: str):
        """初始化YouTube项目目录"""
        # 如果没有指定prefix，使用原始工作目录
        if prefix is None:
            prefix = ctx.obj.get('original_dir', '.')
        
        # 确保prefix不为None
        if prefix is None:
            prefix = '.'
        
        # 检查是否是有效的YouTube URL
        if not YouTubeURLParser.is_valid_youtube_url(url):
            click.echo(f"❌ 错误：'{url}' 不是有效的YouTube URL")
            return
        
        # 提取视频ID
        video_id = YouTubeURLParser.extract_video_id(url)
        click.echo(f"📹 检测到YouTube视频ID: {video_id}")
        
        # 创建项目
        project_manager = ProjectManager(prefix)
        success, result = project_manager.create_project(video_id, url)
        
        if not success:
            click.echo(f"⚠️  {result}")
            return
        
        click.echo(f"📁 创建目录: {result}")
        click.echo(f"📝 创建配置文件: {result}/.youtube")
        click.echo(f"✅ 初始化完成！") 