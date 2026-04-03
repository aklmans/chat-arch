import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI

from chatarch.core.config import load_config
from chatarch.db.models import Session

def get_llm_client(provider_name: Optional[str] = None) -> tuple[OpenAI, str]:
    """
    根据配置获取初始化好的 OpenAI 兼容客户端和模型名称
    """
    config = load_config()
    llm_config = config.get("llm", {})
    
    provider = provider_name or llm_config.get("default_provider", "kimi")
    providers = llm_config.get("providers", {})
    
    if provider not in providers:
        raise ValueError(f"配置中未找到指定的 LLM 提供商: {provider}。请检查 ~/.chatarch/config.yaml")
        
    p_config = providers[provider]
    base_url = p_config.get("base_url")
    api_key = p_config.get("api_key", "sk-xxx")
    model = p_config.get("model")
    custom_headers = p_config.get("custom_headers", {})
    
    # 兼容像 claude-code 需要特定 User-Agent 头的需求
    # 在 openai-python SDK 中，直接传递 default_headers 才能有效覆盖默认的 User-Agent
    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
        default_headers=custom_headers if custom_headers else None
    )
    
    return client, model

def enrich_session(session: Session, provider_name: Optional[str] = None) -> Dict[str, Any]:
    """
    通过大语言模型提炼会话（生成摘要与标签）
    """
    if not session.messages:
        raise ValueError("会话为空，无法提炼。")
        
    client, model = get_llm_client(provider_name)
    
    # 构建上下文 (为节省 token，这里只提取角色和内容，并且如果有必要可以做截断)
    context_text = ""
    for msg in session.messages:
        # 只提取前 50 轮左右或截断，避免超出窗口
        context_text += f"[{msg.role}]: {msg.content}\n"
    
    # 限制上下文长度（约 10000 字符，避免超出某些模型的限制，可根据实际需求调整）
    if len(context_text) > 15000:
         context_text = context_text[:7500] + "\n...(中间内容已截断)...\n" + context_text[-7500:]

    system_prompt = """
你是一个专业的数据归档与知识整理助手。
请阅读以下聊天记录上下文，并为其生成：
1. 一段精确且简短的摘要（50字以内）。
2. 提取 3-5 个最相关的英文或中文标签（小写，不要带有空格）。

你必须只输出一个严格合法的 JSON 对象，不要输出任何 Markdown 标记 (如 ```json) 或多余的文字说明，格式如下：
{
  "summary": "这是一段关于 xxx 的讨论，主要解决了 yyy 问题。",
  "tags": ["python", "cli", "bug-fix"]
}
"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": context_text}
            ],
            temperature=0.3, # 较低的温度以保持 JSON 格式稳定
        )
        
        content = response.choices[0].message.content.strip()
        
        # 兼容某些大模型可能还是会带上 markdown code block 的情况
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        content = content.strip()
        
        result = json.loads(content)
        return {
            "summary": result.get("summary", ""),
            "tags": result.get("tags", [])
        }
        
    except json.JSONDecodeError as e:
        raise ValueError(f"大模型返回的格式非标准 JSON，解析失败。内容为: \n{content}") from e
    except Exception as e:
        raise RuntimeError(f"调用大语言模型 API 时失败: {e}")
