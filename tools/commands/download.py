"""
YouTube工具集 - download命令
"""
import click
import os
import yt_dlp
import requests
import re
import glob


def download_mp4(url, original_dir):
    click.echo(f"🎬 下载音视频 mp4: {url}")
    # 获取视频ID
    import re as _re
    m = _re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url)
    video_id = m.group(1) if m else 'video'
    mp4_file = os.path.join(original_dir, f'{video_id}.mp4')
    if os.path.exists(mp4_file):
        click.echo(f"⚠️ 视频文件已存在，跳过下载: {mp4_file}")
        return
    try:
        ydl_opts = {
            'quiet': False,
            'outtmpl': mp4_file,
            'merge_output_format': 'mp4',
            'format': (
                'bestvideo[height<=1080][height>=720][ext=mp4][vcodec^=avc1]'
                '+bestaudio[ext=m4a][language^=en]'
                '/best[ext=mp4][vcodec^=avc1]'
            ),
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        click.echo(f"✅ 视频已保存为 {mp4_file}")
    except Exception as e:
        click.echo(f"❌ 下载视频时出错: {e}")

def download_subtitle(url, lang, original_dir):
    click.echo(f"📝 检查字幕 ({lang}): {url}")
    
    # 获取视频ID
    import re as _re
    m = _re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url)
    video_id = m.group(1) if m else 'video'
    subtitle_file = os.path.join(original_dir, f'{video_id}.{lang}.srt')
    if os.path.exists(subtitle_file):
        click.echo(f"⚠️ 字幕文件已存在，跳过下载: {subtitle_file}")
        return
    
    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,  # 支持自动字幕
            'subtitleslangs': [lang],
            'subtitlesformat': 'srt',
            'outtmpl': os.path.join(original_dir, '%(title)s.%(ext)s'),  # 使用默认命名
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # 调试输出可用字幕信息
            click.echo(f"  - info['subtitles'] keys: {list(info.get('subtitles', {}).keys())}")
            click.echo(f"  - info['automatic_captions'] keys: {list(info.get('automatic_captions', {}).keys())}")
            has_sub = lang in info.get('subtitles', {})
            has_auto = lang in info.get('automatic_captions', {})
            if not (has_sub or has_auto):
                if lang == 'en':
                    click.echo(f"❌ 没有找到英文字幕 (en)，无法下载！")
                else:
                    click.echo(f"⚠️ 没有找到 {lang} 字幕，跳过。")
                return
            
            # 下载字幕
            ydl.download([url])
            
            # 搜索所有相关的字幕文件
            patterns = [
                os.path.join(original_dir, f'*.{lang}.srt'),
                os.path.join(original_dir, f'*auto*{lang}*.srt'),
                os.path.join(original_dir, f'*orig*{lang}*.srt'),
            ]
            found = False
            for pattern in patterns:
                for f in glob.glob(pattern):
                    os.rename(f, subtitle_file)
                    click.echo(f"✅ 字幕 ({lang}) 已保存为 {subtitle_file}")
                    found = True
                    break
                if found:
                    break
            if not found:
                click.echo(f"❌ 字幕文件下载失败，未找到匹配的srt文件")
                
    except Exception as e:
        click.echo(f"❌ 下载字幕 ({lang}) 时出错: {e}")

def download_cover(url, original_dir):
    click.echo(f"🖼️ 获取封面信息: {url}")
    
    # 检查文件是否已存在
    cover_file = os.path.join(original_dir, 'cover.jpg')
    if os.path.exists(cover_file):
        click.echo(f"⚠️ 封面文件已存在，跳过下载: {cover_file}")
        return
    
    try:
        ydl_opts = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            thumbnail_url = info.get('thumbnail')
            if not thumbnail_url:
                click.echo("❌ 未找到封面图片URL")
                return
            click.echo(f"🌐 封面图片URL: {thumbnail_url}")
            # 下载图片
            resp = requests.get(thumbnail_url, timeout=10)
            if resp.status_code == 200:
                with open(cover_file, 'wb') as f:
                    f.write(resp.content)
                click.echo(f"✅ 封面已保存为 {cover_file}")
            else:
                click.echo(f"❌ 下载封面失败，HTTP状态码: {resp.status_code}")
    except Exception as e:
        click.echo(f"❌ 获取或下载封面时出错: {e}")

def merge_subtitles(original_dir, video_id):
    """合并中英文字幕，英文在上，中文在下"""
    en_file = os.path.join(original_dir, f'{video_id}.en.srt')
    zh_file = os.path.join(original_dir, f'{video_id}.zh-Hans.srt')
    merged_file = os.path.join(original_dir, f'{video_id}.bilingual.srt')
    
    # 检查文件是否存在
    if not os.path.exists(en_file):
        click.echo(f"❌ 英文字幕文件不存在: {en_file}")
        return
    if not os.path.exists(zh_file):
        click.echo(f"❌ 中文字幕文件不存在: {zh_file}")
        return
    if os.path.exists(merged_file):
        click.echo(f"⚠️ 双语字幕文件已存在，跳过: {merged_file}")
        return
    
    try:
        # 读取字幕文件
        def parse_srt(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            subtitles = []
            blocks = content.split('\n\n')
            for block in blocks:
                if not block.strip():
                    continue
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    index = lines[0]
                    timestamp = lines[1]
                    text = '\n'.join(lines[2:])
                    subtitles.append((index, timestamp, text))
            return subtitles
        
        en_subs = parse_srt(en_file)
        zh_subs = parse_srt(zh_file)
        
        # 合并字幕
        with open(merged_file, 'w', encoding='utf-8') as f:
            for i, (en_index, en_timestamp, en_text) in enumerate(en_subs):
                # 写入序号
                f.write(f"{i+1}\n")
                # 写入时间戳
                f.write(f"{en_timestamp}\n")
                # 写入英文（在上）
                f.write(f"{en_text}\n")
                # 写入中文（在下）
                if i < len(zh_subs):
                    zh_text = zh_subs[i][2]
                    f.write(f"{zh_text}\n")
                f.write("\n")
        
        click.echo(f"✅ 双语字幕生成完成: {merged_file}")
        
    except Exception as e:
        click.echo(f"❌ 合并字幕时出错: {e}")

class DownloadCommand:
    """下载命令处理器"""
    
    @staticmethod
    @click.command()
    @click.pass_context
    def download(ctx):
        """下载YouTube视频"""
        # 使用原始工作目录
        original_dir = ctx.obj.get('original_dir', '.')
        if original_dir is None:
            original_dir = '.'
        
        youtube_file = os.path.join(original_dir, '.youtube')
        
        # 检查当前目录是否有.youtube文件
        if not os.path.exists(youtube_file):
            click.echo("❌ 错误：当前目录下没有找到 .youtube 文件")
            click.echo("💡 提示：请先运行 yt init 命令初始化项目")
            return
        
        # 读取URL
        try:
            with open(youtube_file, 'r', encoding='utf-8') as f:
                url = f.read().strip()
            click.echo(f"📥 准备下载: {url}")
            # 下载mp4
            download_mp4(url, original_dir)
            # 下载字幕（en，zh-Hans）
            download_subtitle(url, 'en', original_dir)
            download_subtitle(url, 'zh-Hans', original_dir)
            
            # 合并字幕
            import re as _re
            m = _re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url)
            video_id = m.group(1) if m else 'video'
            merge_subtitles(original_dir, video_id)
            
            # 下载封面
            download_cover(url, original_dir)
            click.echo("✅ 下载流程框架已建立，具体功能待实现...")
        except Exception as e:
            click.echo(f"❌ 读取 .youtube 文件时出错: {e}") 