"""
LLM分析器 - 负责调用大模型进行句子分析
"""
import os
import re
import json
import openai
import click


class LLMAnalyzer:
    """LLM分析器，负责调用大模型进行句子分析"""
    
    def __init__(self, model='gpt-4o-mini', api_key=None):
        self.model = model
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = None
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
    
    def analyze_sentences(self, sentences, batch_size=5):
        """分析句子列表，返回结构化结果"""
        if not self.client:
            click.echo("❌ 未找到OpenAI API密钥")
            click.echo("💡 请设置环境变量 OPENAI_API_KEY 或使用 --api-key 参数")
            return None
        
        # 调试时只处理第一批
        batch = sentences[0:batch_size] 
        click.echo(f"🔄 处理第一批 {batch_size} 个句子进行调试")
        
        results = self._call_llm_analyze(batch)
        if not results:
            click.echo("❌ LLM分析失败，停止处理")
            return None
            
        return results
    
    def _call_llm_analyze(self, sentences):
        """调用LLM分析句子"""
        try:
            prompt = self._build_analysis_prompt(sentences)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的英语语法和词汇分析助手。请严格按照JSON格式输出。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            return self._parse_response(content)
                
        except Exception as e:
            click.echo(f"❌ LLM调用失败: {e}")
            return None
    
    def _parse_response(self, content):
        """解析LLM响应"""
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
    
    def _build_analysis_prompt(self, sentences):
        """构建LLM分析prompt"""
        prompt = """
你是一位英语教学专家，请根据我当前的英语学习情况，逐句分析下面这段英文句子列表。返回 JSON 数组，每句一个对象，格式如下字段：

- id: 句子编号（如 "001"）
- sentence: 原句
- explanation: 用中文解释该句子的含义和语境，尽量还原说话者的情绪和目的
- syntax: 用通俗中文指出该句的具体语法结构，尤其标出以下结构：宾语从句、非谓语结构、情态结构、比较状语、强调句等；请避免笼统描述如"复合句"
- vocabulary: 一个 object，列出该句中我可能不熟悉的中高级词汇（CEFR B2及以上，或语义/用法易混的词），key 是单词，value 为 "音标, 词性, CEFR等级, 中文含义"
- phrases: 一个 object，列出该句中值得学习的**固定搭配、动词短语、口语表达、常见句型结构**，key 是短语，value 为中文解释或常用语境说明

我的英语背景：
- 词汇量约 5000，A1–B1 词汇基本掌握；
- 动词短语、句子结构和口语表达是我主要的弱项；
- 希望提升句法理解和真实语境表达能力。

请不要输出我已经掌握的基础词（如: fun, love, kind, idea 等）。请只返回 JSON 数组，不要额外文字说明。

**重要：你必须返回严格的JSON数组格式，不要包含任何其他文字。**

**输出要求：**
1. 必须是有效的JSON数组
2. 不要包含任何解释性文字
3. 不要使用markdown格式
4. 直接输出JSON数组

示例格式：
[
  {
    "id": "005",
    "sentence": "Like I know in advance kind of what I want to do. But to be honest, I have no idea what I'm going to do today.",
    "explanation": "她说平常她都会提前有些想法，但今天她完全没有计划，这是表达轻微焦虑或放松随性的情绪。",
    "syntax": "第一句是宾语从句（what I want to do），由 like 引导的语气句；第二句是主句 + what 引导的宾语从句。",
    "vocabulary": {
      "no idea": "/nəʊ aɪˈdɪə/, phrase, B2, 完全不知道，表达完全没有头绪"
    },
    "phrases": {
      "like I know": "像是我知道…，常用于引入一种不确定/随意语气",
      "in advance": "提前，常用于计划或准备场景", 
      "kind of": "有点，模糊语气，降低语气强度",
      "to be honest": "说实话，常用于表达个人真实情绪或转折",
      "I have no idea": "我一点头绪都没有，非常常用的表达完全不知道"
    }
  }
]

句子列表：
"""
        for sentence in sentences:
            prompt += f"{sentence['id']} {sentence['sentence']}\n"
        prompt += "\n请直接输出JSON数组，不要包含任何其他内容。"
        return prompt


class PreprocessedFileParser:
    """预处理文件解析器"""
    
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