"""
YouTube工具集 - md命令（生成预处理字幕文件）
"""
import click
import os
import re

class MdCommand:
    @staticmethod
    @click.command()
    @click.pass_context
    def md(ctx):
        """生成预处理字幕文件"""
        # 获取工作目录
        original_dir = ctx.obj.get('original_dir') or os.getcwd()
        # 检查VTT文件
        result = MdCommand.check_vtt_file(original_dir)
        if not result:
            ctx.exit(1)
        video_id, vtt_file, _ = result
        try:
            MdCommand.process_md(video_id, vtt_file, original_dir)
        except Exception as e:
            click.echo(f"❌ 命令执行失败: {e}")
            ctx.exit(1)

    @staticmethod
    def check_vtt_file(original_dir):
        """检查并定位英文VTT文件"""
        youtube_file = os.path.join(original_dir, '.youtube')
        if not os.path.exists(youtube_file):
            click.echo("❌ 错误：当前目录下没有找到 .youtube 文件")
            click.echo("💡 提示：请先运行 ytkit init 命令初始化项目")
            return None
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

    @staticmethod
    def parse_vtt_file(vtt_file):
        """解析VTT文件，提取字幕数据"""
        click.echo(f"📝 解析VTT文件: {vtt_file}")
        try:
            with open(vtt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
            lines = content.strip().split('\n')
            transcript_data = []
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if not line or line == 'WEBVTT' or line.startswith('NOTE'):
                    i += 1
                    continue
                if line.isdigit():
                    i += 1
                    continue
                if '-->' in line:
                    time_parts = line.split(' --> ')
                    if len(time_parts) == 2:
                        start_time = MdCommand.parse_vtt_time(time_parts[0])
                        text_lines = []
                        i += 1
                        while i < len(lines) and lines[i].strip():
                            clean_line = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', lines[i].strip())
                            if clean_line:
                                text_lines.append(clean_line)
                            i += 1
                        if text_lines:
                            transcript_data.append({'start': start_time, 'text': ' '.join(text_lines)})
                    else:
                        i += 1
                else:
                    i += 1
            if transcript_data:
                first_time = MdCommand.format_time(transcript_data[0]['start'])
                last_time = MdCommand.format_time(transcript_data[-1]['start'])
                click.echo(f"📊 解析完成，共 {len(transcript_data)} 条字幕")
                click.echo(f"📊 时间范围: {first_time} - {last_time}")
            else:
                click.echo("⚠️ 警告：没有解析到任何字幕数据")
            return transcript_data
        except Exception as e:
            click.echo(f"❌ 解析VTT文件时出错: {e}")
            raise

    @staticmethod
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

    @staticmethod
    def clean_text(text):
        """清理字幕文本，去除无效内容"""
        text = re.sub(r'\[[^\]]*\]', '', text)  # 去除[Music]等
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def merge_segments(transcript_data, min_len=8, min_words=2):
        """合并字幕片段，尽量保证每句以标点结尾"""
        if not transcript_data:
            return []
        result = []
        buffer = ''
        start_time = None
        for item in transcript_data:
            text = MdCommand.clean_text(item['text'])
            if not text:
                continue
            sentences = re.split(r'(?<=[.!?])\s+', text)
            for sentence in sentences:
                s = sentence.strip()
                if not s:
                    continue
                if buffer == '':
                    buffer = s
                    start_time = item['start']
                else:
                    buffer += ' ' + s
                if buffer.endswith(('.', '?', '!')):
                    result.append({'start': start_time, 'text': buffer})
                    buffer = ''
                    start_time = None
        if buffer:
            result.append({'start': start_time, 'text': buffer})
        # 合并超短句
        final = []
        for seg in result:
            if final and (len(seg['text']) < min_len or len(seg['text'].split()) < min_words):
                final[-1]['text'] += ' ' + seg['text']
            else:
                final.append(seg)
        return final

    @staticmethod
    def format_time(seconds):
        """格式化时间为 MM:SS 格式"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def generate_preprocessed_md(transcript_data, output_file, max_segments=200):
        """生成预处理后的Markdown文件，控制总句数不超过max_segments"""
        click.echo("🔄 生成预处理字幕文件...")
        
        # 合并字幕片段
        merged_data = MdCommand.merge_segments(transcript_data)
        click.echo(f"📝 初步合并后共 {len(merged_data)} 个片段")

        # 如果片段数超过max_segments，按比例合并相邻句子
        if len(merged_data) > max_segments:
            import math
            ratio = math.ceil(len(merged_data) / max_segments)
            click.echo(f"⚠️ 片段数超过{max_segments}，将每{ratio}句合并为一句")
            new_merged = []
            buffer = ''
            start_time = None
            for idx, item in enumerate(merged_data):
                if buffer == '':
                    buffer = item['text']
                    start_time = item['start']
                else:
                    buffer += ' ' + item['text']
                # 每ratio句合并一次，或到最后一条
                if (idx + 1) % ratio == 0 or idx == len(merged_data) - 1:
                    new_merged.append({
                        'start': start_time, 
                        'text': buffer.strip()
                    })
                    buffer = ''
                    start_time = None
            merged_data = new_merged
            click.echo(f"✅ 合并后片段数: {len(merged_data)}")
        else:
            # 只保留开始时间和文本
            merged_data = [
                {'start': item['start'], 'text': item['text']} for item in merged_data
            ]

        # 生成预处理文件
        lines = []
        for i, item in enumerate(merged_data):
            timestamp = MdCommand.format_time(item['start'])
            text = item['text']
            lines.append(f"{timestamp} [{i+1:03d}] {text}")
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        click.echo(f"✅ 预处理文件已生成: {output_file}")
        return len(merged_data)

    @staticmethod
    def process_md(video_id, vtt_file, original_dir):
        """处理字幕文件，生成预处理Markdown"""
        click.echo(f"📝 处理字幕文件: {vtt_file}")
        try:
            transcript_data = MdCommand.parse_vtt_file(vtt_file)
            output_file = os.path.join(original_dir, f'{video_id}.preprocessed.md')
            segment_count = MdCommand.generate_preprocessed_md(transcript_data, output_file)
            click.echo("✅ 字幕文件处理完成")
            click.echo(f"📄 生成的预处理文件: {output_file}")
            click.echo(f"📊 共处理 {segment_count} 个字幕片段")
        except Exception as e:
            click.echo(f"❌ 处理字幕文件时出错: {e}")
            raise 