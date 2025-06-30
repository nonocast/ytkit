"""
YouTube工具集 - x命令（两步处理：预处理+LLM分析）
"""
import click
import os
import json
from .md import MdCommand
from ..llm_analyzer import LLMAnalyzer, PreprocessedFileParser


class XCommand:
    @staticmethod
    @click.command()
    @click.pass_context
    def x(ctx):
        """两步处理：预处理字幕 + LLM分析"""
        original_dir = ctx.obj.get('original_dir') or os.getcwd()
        result = MdCommand.check_vtt_file(original_dir)
        if not result:
            ctx.exit(1)
        video_id, vtt_file, url = result
        try:
            XCommand.step1_preprocess(video_id, vtt_file, original_dir)
            XCommand.step2_analyze(video_id, original_dir)
        except Exception as e:
            click.echo(f"❌ 命令执行失败: {e}")
            ctx.exit(1)

    @staticmethod
    def step1_preprocess(video_id, vtt_file, original_dir):
        """第一步：生成preprocessed.md"""
        click.echo("🔄 第一步：生成预处理文件...")
        MdCommand.process_md(video_id, vtt_file, original_dir)

    @staticmethod
    def step2_analyze(video_id, original_dir):
        """第二步：调用LLM生成分析字典"""
        click.echo("🤖 第二步：调用LLM分析...")
        
        # 检查文件是否存在
        preprocessed_file = os.path.join(original_dir, f'{video_id}.preprocessed.md')
        if not os.path.exists(preprocessed_file):
            click.echo(f"❌ 预处理文件不存在: {preprocessed_file}")
            click.echo("💡 请先运行第一步生成预处理文件")
            return
        
        # 解析预处理文件
        sentences = PreprocessedFileParser.parse_preprocessed_file(preprocessed_file)
        click.echo(f"📝 解析到 {len(sentences)} 个句子")
        
        # 创建LLM分析器并分析
        analyzer = LLMAnalyzer()
        results = analyzer.analyze_sentences(sentences)
        
        if not results:
            return
        
        # 保存结果
        output_file = os.path.join(original_dir, f'{video_id}.analyzed.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        click.echo(f"✅ 调试分析完成，结果保存至: {output_file}") 