"""
YouTube工具集 - transcripts命令
"""
import click
import os
import re
import json
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import WebVTTFormatter
from tools.llm_processor import LLMProcessor


def check_vtt_file(original_dir):
    """检查是否存在英文VTT文件"""
    youtube_file = os.path.join(original_dir, '.youtube')
    
    if not os.path.exists(youtube_file):
        click.echo("❌ 错误：当前目录下没有找到 .youtube 文件")
        click.echo("💡 提示：请先运行 ytkit init 命令初始化项目")
        return None
    
    # 读取URL获取视频ID
    try:
        with open(youtube_file, 'r', encoding='utf-8') as f:
            url = f.read().strip()
        
        m = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url)
        video_id = m.group(1) if m else None
        
        if not video_id:
            click.echo("❌ 错误：无法从URL中提取视频ID")
            return None
        
        vtt_file = os.path.join(original_dir, f'{video_id}.en.vtt')
        
        if not os.path.exists(vtt_file):
            click.echo(f"❌ 错误：没有找到英文VTT文件 {vtt_file}")
            click.echo("💡 提示：请先运行 ytkit download 命令下载字幕")
            return None
        
        click.echo(f"✅ 找到VTT文件: {vtt_file}")
        return video_id, vtt_file, url
        
    except Exception as e:
        click.echo(f"❌ 读取 .youtube 文件时出错: {e}")
        return None


def parse_vtt_file(vtt_file):
    """解析VTT文件，提取字幕数据"""
    click.echo(f"📝 解析VTT文件: {vtt_file}")
    
    try:
        with open(vtt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 清理内容中的控制字符
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
        
        # 简单的VTT解析
        lines = content.strip().split('\n')
        transcript_data = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过空行和WEBVTT头部
            if not line or line == 'WEBVTT' or line.startswith('NOTE'):
                i += 1
                continue
            
            # 跳过序号行
            if line.isdigit():
                i += 1
                continue
            
            # 解析时间戳行
            if '-->' in line:
                time_parts = line.split(' --> ')
                if len(time_parts) == 2:
                    start_time = parse_vtt_time(time_parts[0])
                    
                    # 收集文本内容
                    text_lines = []
                    i += 1
                    while i < len(lines) and lines[i].strip():
                        # 清理每行文本中的控制字符
                        clean_line = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', lines[i].strip())
                        if clean_line:
                            text_lines.append(clean_line)
                        i += 1
                    
                    if text_lines:
                        transcript_data.append({
                            'start': start_time,
                            'text': ' '.join(text_lines)
                        })
                else:
                    i += 1
            else:
                i += 1
        
        click.echo(f"📊 解析完成，共 {len(transcript_data)} 条字幕")
        return transcript_data
        
    except Exception as e:
        click.echo(f"❌ 解析VTT文件时出错: {e}")
        raise


def parse_vtt_time(time_str):
    """解析VTT时间格式为秒数"""
    # VTT格式: HH:MM:SS.mmm
    parts = time_str.split(':')
    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    return 0.0


def generate_markdown(transcript_data, video_id, original_dir):
    """使用LLM生成Markdown文档"""
    click.echo("🤖 使用LLM处理字幕数据...")
    
    try:
        # 检查是否有 API 密钥
        from config import Config
        if not Config.validate_config():
            click.echo("⚠️ 未配置 LLM API 密钥，使用模拟数据生成示例文档")
            result = generate_mock_result(transcript_data)
        else:
            # 初始化LLM处理器
            llm_processor = LLMProcessor()
            
            # 处理字幕数据
            result = llm_processor.process_transcript(transcript_data)
        
        # 生成Markdown内容
        markdown_content = generate_markdown_content(result)
        
        # 保存Markdown文件
        markdown_file = os.path.join(original_dir, f'{video_id}.transcripts.md')
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        click.echo(f"✅ Markdown文件已生成: {markdown_file}")
        return markdown_file
        
    except Exception as e:
        click.echo(f"❌ 生成Markdown时出错: {e}")
        raise


def generate_mock_result(transcript_data):
    """生成模拟的 LLM 结果用于测试"""
    # 基于字幕数据生成简单的章节划分
    toc = []
    chapters = []
    
    if not transcript_data:
        return {"toc": [], "chapters": []}
    
    # 简单的章节划分逻辑
    current_chapter = {
        "time": format_time(transcript_data[0]['start']),
        "title": "开场介绍",
        "content": ""
    }
    
    chapter_count = 0
    for i, item in enumerate(transcript_data):
        # 每30条字幕作为一个章节
        if i > 0 and i % 30 == 0:
            if current_chapter["content"]:
                chapters.append(current_chapter)
                toc.append({
                    "time": current_chapter["time"],
                    "title": current_chapter["title"]
                })
            
            chapter_count += 1
            current_chapter = {
                "time": format_time(item['start']),
                "title": f"章节 {chapter_count + 1}",
                "content": ""
            }
        
        current_chapter["content"] += item['text'] + " "
    
    # 添加最后一个章节
    if current_chapter["content"]:
        chapters.append(current_chapter)
        toc.append({
            "time": current_chapter["time"],
            "title": current_chapter["title"]
        })
    
    return {
        "toc": toc,
        "chapters": chapters
    }


def format_time(seconds):
    """格式化时间为 MM:SS 格式"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def generate_markdown_content(result):
    """构建Markdown内容，全部英文"""
    lines = []
    
    # 只保留目录，不加标题
    lines.append("## Table of Contents")
    for item in result.get('toc', []):
        # 只用英文标题，没有则用英文占位
        title = item.get('en_title') or item.get('title') or 'Untitled'
        if not title:
            title = 'Untitled'
        lines.append(f"- {item['time']} {title}")
    # lines.append("")
    
    # 添加正文
    lines.append("## Content")
    # lines.append("")
    
    for chapter in result.get('chapters', []):
        title = chapter.get('en_title') or chapter.get('title') or 'Untitled'
        if not title:
            title = 'Untitled'
        lines.append(f"### {chapter['time']} {title}")
        lines.append("```text")
        # 清理和连接文本内容，去除空白行
        content = clean_and_connect_text(chapter['content'])
        lines.append(content)
        lines.append("```")
        lines.append("")
    
    return "\n".join(lines)


def clean_and_connect_text(text):
    """每句一段，按句号、问号、感叹号分割，每句单独成行，无空白行。"""
    import re
    # 移除重复的 ```text 标签
    text = re.sub(r'```text\s*```text', '```text', text)
    text = re.sub(r'```text\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    # 清理多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    # 修复双句号问题
    text = re.sub(r'\.\.+', '.', text)
    # 按句号、问号、感叹号分割
    sentences = re.split(r'([.?!])', text)
    lines = []
    current = ''
    for seg in sentences:
        if seg in '.?!':
            current += seg
            lines.append(current.strip())
            current = ''
        else:
            current += seg
    # 处理最后一段
    if current.strip():
        lines.append(current.strip())
    # 去除空白行
    result = '\n'.join([line for line in lines if line])
    return result


def process_transcripts(video_id, vtt_file, original_dir):
    """处理字幕文件"""
    click.echo(f"📝 处理字幕文件: {vtt_file}")
    
    try:
        # 解析VTT文件
        transcript_data = parse_vtt_file(vtt_file)
        
        # 生成Markdown文档
        markdown_file = generate_markdown(transcript_data, video_id, original_dir)
        
        click.echo("✅ 字幕文件处理完成")
        click.echo(f"📄 生成的文档: {markdown_file}")
        
    except Exception as e:
        click.echo(f"❌ 处理字幕文件时出错: {e}")


class TranscriptsCommand:
    """字幕处理命令处理器"""
    
    @staticmethod
    @click.command()
    @click.pass_context
    def transcripts(ctx):
        """处理YouTube视频字幕"""
        # 使用原始工作目录
        original_dir = ctx.obj.get('original_dir', '.')
        if original_dir is None:
            original_dir = '.'
        
        # 检查VTT文件
        result = check_vtt_file(original_dir)
        if result is None:
            return
        
        video_id, vtt_file, url = result
        
        # 处理字幕
        process_transcripts(video_id, vtt_file, original_dir) 