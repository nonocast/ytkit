"""
YouTube工具集 - LLM 处理模块
"""
import json
import click
from typing import List, Dict, Any
from config import Config

try:
    import openai
except ImportError:
    openai = None

try:
    from deepseek import DeepSeek
except ImportError:
    DeepSeek = None


class LLMProcessor:
    """LLM 处理器"""
    
    def __init__(self):
        self.config = Config.get_llm_config()
        self._validate_config()
        self._init_client()
    
    def _validate_config(self):
        """验证配置"""
        if not Config.validate_config():
            raise ValueError(
                f"LLM 配置不完整。请设置环境变量：\n"
                f"对于 OpenAI: OPENAI_API_KEY\n"
                f"对于 DeepSeek: DEEPSEEK_API_KEY\n"
                f"当前提供商: {self.config['provider']}"
            )
    
    def _init_client(self):
        """初始化客户端"""
        if self.config['provider'] == 'openai':
            if not openai:
                raise ImportError("请安装 openai 包: pip install openai")
            openai.api_key = self.config['api_key']
            self.client = openai
        elif self.config['provider'] == 'deepseek':
            if not DeepSeek:
                raise ImportError("请安装 deepseek-ai 包: pip install deepseek-ai")
            self.client = DeepSeek(api_key=self.config['api_key'])
    
    def process_transcript(self, transcript_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理字幕数据，生成结构化内容"""
        
        # 构建字幕文本
        transcript_text = self._build_transcript_text(transcript_data)
        
        # 构建提示词
        prompt = self._build_prompt(transcript_text)
        
        # 调用 LLM
        response = self._call_llm(prompt)
        
        # 解析响应
        return self._parse_response(response)
    
    def _build_transcript_text(self, transcript_data: List[Dict[str, Any]]) -> str:
        """构建字幕文本"""
        lines = []
        for item in transcript_data:
            start_time = self._format_time(item['start'])
            text = item['text']
            lines.append(f"{start_time} {text}")
        return "\n".join(lines)
    
    def _format_time(self, seconds: float) -> str:
        """格式化时间为 MM:SS 格式"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def _build_prompt(self, transcript_text: str) -> str:
        """构建中文提示词，要求返回英文标题+中文翻译"""
        return f"""请分析以下 YouTube 视频字幕，将其按语义和时间轴划分为章节，并生成结构化的文档。

要求：
1. 按时间轴和语义内容划分段落
2. 每个段落应该有明确的主题
3. 生成目录和正文两个部分
4. 目录格式：时间 (MM:SS) 英文标题 - 中文翻译
5. 正文格式：每个章节用 ### 标题，内容用 ```text 代码块包围
6. 所有章节标题必须包含英文和中文翻译，格式为：英文标题 - 中文翻译
7. 返回严格的 JSON 格式，包含以下字段：
{{
    "toc": [
        {{"time": "00:00", "title": "English Title - 中文翻译"}},
        ...
    ],
    "chapters": [
        {{
            "time": "00:00",
            "title": "English Title - 中文翻译",
            "content": "章节内容文本"
        }},
        ...
    ]
}}

字幕内容：
{transcript_text}

注意：所有标题必须包含英文和中文翻译，格式为"英文标题 - 中文翻译"。JSON 必须严格有效。
"""
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM API"""
        try:
            if self.config['provider'] == 'openai':
                response = self.client.chat.completions.create(
                    model=self.config['model'],
                    messages=[
                        {"role": "system", "content": "你是一个专业的视频字幕分析助手，擅长将字幕内容按语义和时间轴进行结构化分析。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=4000
                )
                return response.choices[0].message.content
            
            elif self.config['provider'] == 'deepseek':
                response = self.client.chat.completions.create(
                    model=self.config['model'],
                    messages=[
                        {"role": "system", "content": "你是一个专业的视频字幕分析助手，擅长将字幕内容按语义和时间轴进行结构化分析。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=4000
                )
                return response.choices[0].message.content
                
        except Exception as e:
            click.echo(f"❌ 调用 LLM API 时出错: {e}")
            raise
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析 LLM 响应"""
        try:
            # 尝试提取 JSON 部分
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("响应中未找到有效的 JSON")
            
            json_str = response[start_idx:end_idx]
            
            # 清理无效的控制字符
            import re
            # 移除或替换无效的控制字符
            json_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', json_str)
            
            # 调试：显示 JSON 字符串的前500个字符
            click.echo(f"🔍 JSON 字符串预览: {json_str[:500]}...")
            
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            click.echo(f"❌ JSON 解析错误: {e}")
            click.echo(f"错误位置: 第 {e.lineno} 行，第 {e.colno} 列")
            
            # 显示错误位置附近的内容
            lines = json_str.split('\n')
            if e.lineno <= len(lines):
                error_line = lines[e.lineno - 1]
                click.echo(f"错误行内容: {error_line}")
                if e.colno <= len(error_line):
                    click.echo(f"错误位置字符: '{error_line[e.colno-1]}' (ASCII: {ord(error_line[e.colno-1])})")
            
            # 尝试更激进的清理
            try:
                import re
                # 移除所有可能的控制字符和特殊字符
                cleaned_json = re.sub(r'[^\x20-\x7E\n\r\t]', '', json_str)
                click.echo("🔄 尝试清理后的 JSON...")
                return json.loads(cleaned_json)
            except Exception as clean_error:
                click.echo(f"❌ 清理后仍然无法解析 JSON: {clean_error}")
                click.echo(f"原始响应: {response[:1000]}...")
                raise
                
        except Exception as e:
            click.echo(f"❌ 解析 LLM 响应时出错: {e}")
            click.echo(f"原始响应: {response[:1000]}...")
            raise 