"""
YouTube工具集 - x命令（两步处理：预处理+LLM分析）
"""
import click
import os
import re
import json
import openai
from .md import MdCommand


class XCommand:
    @staticmethod
    @click.command()
    @click.option('--step', type=click.Choice(['preprocess', 'analyze', 'both']), 
                  default='both', help='执行步骤：preprocess(预处理), analyze(分析), both(全部)')
    @click.option('--batch-size', default=5, help='LLM批量处理大小')
    @click.option('--model', default='gpt-4o-mini', help='LLM模型名称')
    @click.option('--api-key', help='OpenAI API密钥')
    @click.pass_context
    def x(ctx, step, batch_size, model, api_key):
        """两步处理：预处理字幕 + LLM分析"""
        original_dir = ctx.obj.get('original_dir') or os.getcwd()
        result = MdCommand.check_vtt_file(original_dir)
        if not result:
            ctx.exit(1)
        video_id, vtt_file, url = result
        try:
            if step in ['preprocess', 'both']:
                XCommand.step1_preprocess(video_id, vtt_file, original_dir)
            if step in ['analyze', 'both']:
                XCommand.step2_analyze(video_id, original_dir, batch_size, model, api_key)
        except Exception as e:
            click.echo(f"❌ 命令执行失败: {e}")
            ctx.exit(1)

    @staticmethod
    def step1_preprocess(video_id, vtt_file, original_dir):
        """第一步：生成preprocessed.md"""
        click.echo("🔄 第一步：生成预处理文件...")
        MdCommand.process_md(video_id, vtt_file, original_dir)

    @staticmethod
    def step2_analyze(video_id, original_dir, batch_size, model, api_key):
        """第二步：调用LLM生成分析字典"""
        click.echo("🤖 第二步：调用LLM分析...")
        
        # 检查analyzed.json是否已存在
        output_file = os.path.join(original_dir, f'{video_id}.analyzed.json')
        if os.path.exists(output_file):
            click.echo(f"⚠️ 分析文件已存在，跳过LLM分析: {output_file}")
            click.echo("💡 如需重新分析，请删除该文件后重试")
            return
        
        preprocessed_file = os.path.join(original_dir, f'{video_id}.preprocessed.md')
        if not os.path.exists(preprocessed_file):
            click.echo(f"❌ 预处理文件不存在: {preprocessed_file}")
            click.echo("💡 请先运行第一步生成预处理文件")
            return
        sentences = XCommand.parse_preprocessed_file(preprocessed_file)
        click.echo(f"📝 解析到 {len(sentences)} 个句子")
        all_results = []
        for i in range(0, len(sentences), batch_size):
            batch = sentences[i:i+batch_size]
            click.echo(f"🔄 处理批次 {i//batch_size + 1}/{(len(sentences)-1)//batch_size + 1}")
            results = XCommand.call_llm_analyze(batch, model, api_key)
            if not results:
                click.echo("❌ LLM分析失败，停止处理")
                return
            all_results.extend(results)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        click.echo(f"✅ 分析完成，结果保存至: {output_file}")

    @staticmethod
    def parse_preprocessed_file(file_path):
        """解析preprocessed.md文件"""
        sentences = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                match = re.match(r'(\d{2}:\d{2})\s+\[(\d+)\]\s+(.+)', line)
                if match:
                    timestamp, sentence_id, text = match.groups()
                    sentences.append({
                        'id': sentence_id,
                        'timestamp': timestamp,
                        'sentence': text
                    })
        return sentences

    @staticmethod
    def call_llm_analyze(sentences, model, api_key):
        """调用LLM分析句子"""
        # 检查API密钥
        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            click.echo("❌ 未找到OpenAI API密钥")
            click.echo("💡 请设置环境变量 OPENAI_API_KEY 或使用 --api-key 参数")
            return None
        
        try:
            # 设置OpenAI客户端
            client = openai.OpenAI(api_key=api_key)
            prompt = XCommand.build_analysis_prompt(sentences)
            
            # 调用API
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个专业的英语语法和词汇分析助手。请严格按照JSON格式输出。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            # 解析响应
            content = response.choices[0].message.content.strip()
            try:
                results = json.loads(content)
                if isinstance(results, list):
                    return results
                else:
                    click.echo("⚠️ LLM返回格式异常，不是数组格式")
                    return None
            except json.JSONDecodeError as e:
                click.echo(f"⚠️ LLM返回非JSON格式: {e}")
                click.echo(f"返回内容: {content[:200]}...")
                return None
                
        except Exception as e:
            click.echo(f"❌ LLM调用失败: {e}")
            return None

    @staticmethod
    def build_analysis_prompt(sentences):
        """构建LLM分析prompt"""
        prompt = """你是一位英语教学专家，请对下列英文句子进行结构化分析。

**重要：你必须返回严格的JSON数组格式，不要包含任何其他文字。**

每条句子分析包含以下字段：
- id: 句子编号（字符串格式）
- explanation: 中文解释句子含义
- syntax: 中文说明语法结构
- vocabulary: 对象，key为单词，value为"音标,词性,CEFR等级,中文含义"
- phrases: 对象，key为短语，value为中文解释

**输出要求：**
1. 必须是有效的JSON数组
2. 不要包含任何解释性文字
3. 不要使用markdown格式
4. 直接输出JSON数组

示例格式：
[
  {
    "id": "001",
    "explanation": "她向观众问好",
    "syntax": "简单句结构",
    "vocabulary": {
      "morning": "/ˈmɔːrnɪŋ/, noun, A1, 早晨"
    },
    "phrases": {
      "Good morning": "早上好"
    }
  }
]

句子列表：
"""
        for sentence in sentences:
            prompt += f"{sentence['id']} {sentence['sentence']}\n"
        prompt += "\n请直接输出JSON数组，不要包含任何其他内容。"
        return prompt 