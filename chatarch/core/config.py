import os
import yaml
from pathlib import Path
from typing import Dict, Any

HOME_DIR = Path.home()
CHATARCH_DIR = HOME_DIR / ".chatarch"
CONFIG_PATH = CHATARCH_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "llm": {
        "default_provider": "kimi",
        "providers": {
            "kimi": {
                "base_url": "https://api.moonshot.cn/v1",
                "api_key": "YOUR_KIMI_API_KEY",
                "model": "moonshot-v1-8k",
                "custom_headers": {
                    "User-Agent": "claude-code/0.1.0"
                }
            },
            "claude-code": {
                "base_url": "https://api.anthropic.com/v1", # 或者如果通过代理中转的地址
                "api_key": "YOUR_CLAUDE_API_KEY",
                "model": "claude-3-5-sonnet-20241022",
                "custom_headers": {
                    "User-Agent": "claude-code/0.1.0"
                }
            },
            "ollama": {
                "base_url": "http://127.0.0.1:11434/v1",
                "api_key": "ollama",
                "model": "llama3.1",
                "custom_headers": {}
            }
        }
    }
}

def load_config() -> Dict[str, Any]:
    """加载配置文件，如果不存在则使用默认配置初始化"""
    if not CONFIG_PATH.exists():
        CHATARCH_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(DEFAULT_CONFIG, f, allow_unicode=True, sort_keys=False)
        return DEFAULT_CONFIG
        
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or DEFAULT_CONFIG
        except yaml.YAMLError:
            return DEFAULT_CONFIG

def save_config(config_data: Dict[str, Any]) -> None:
    """保存配置到文件"""
    CHATARCH_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, allow_unicode=True, sort_keys=False)
