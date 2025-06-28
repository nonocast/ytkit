"""
YouTube工具集 - 配置文件
"""
import os
from typing import Optional


class Config:
    """配置管理类"""
    
    # LLM 提供商配置
    LLM_PROVIDER = os.getenv('YTKIT_LLM_PROVIDER', 'openai')  # 'openai' 或 'deepseek'
    
    # OpenAI 配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('YTKIT_OPENAI_MODEL', 'gpt-4o-mini')
    
    # DeepSeek 配置
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    DEEPSEEK_MODEL = os.getenv('YTKIT_DEEPSEEK_MODEL', 'deepseek-chat')
    
    @classmethod
    def get_llm_config(cls) -> dict:
        """获取当前 LLM 配置"""
        if cls.LLM_PROVIDER == 'openai':
            return {
                'provider': 'openai',
                'api_key': cls.OPENAI_API_KEY,
                'model': cls.OPENAI_MODEL
            }
        elif cls.LLM_PROVIDER == 'deepseek':
            return {
                'provider': 'deepseek',
                'api_key': cls.DEEPSEEK_API_KEY,
                'model': cls.DEEPSEEK_MODEL
            }
        else:
            raise ValueError(f"不支持的 LLM 提供商: {cls.LLM_PROVIDER}")
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置是否完整"""
        config = cls.get_llm_config()
        if not config['api_key']:
            return False
        return True 