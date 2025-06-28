"""
YouTube工具集 - 主入口
"""
import click
import logging
from tools.commands.init import InitCommand
from tools.commands.download import DownloadCommand

# 配置logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.group()
@click.version_option(version="0.1.0", prog_name="ytkit")
@click.option('--original-dir', hidden=True, help='原始工作目录')
@click.pass_context
def main(ctx, original_dir):
    """YouTube工具集"""
    ctx.ensure_object(dict)
    ctx.obj['original_dir'] = original_dir

# 注册命令
main.add_command(InitCommand.init)
main.add_command(DownloadCommand.download)

if __name__ == "__main__":
    main() 