# ChatArch (Chat Asset Archiver)

> 面向个人与团队的 AI 聊天资产归档、检索、分析、复用与安全管理系统。

ChatArch（命令行工具名为 `chatasset`）不仅仅是一个存聊天记录的工具，它旨在将散落在 ChatGPT、Claude、Gemini、Cursor 以及各类终端 Agent 中的“对话废气”，经过自动化清洗、组织、脱敏和索引后，转化为可随时检索、提取知识、复用提示词的“数字矿场”。

## 🌟 核心价值

*   **统一资产池**：支持导入主流 AI 对话平台的导出记录，或手工录入分散对话。
*   **极致检索**：基于本地全文索引与标签分类，支持多条件高级筛选过滤。
*   **知识沉淀**：自动或手动标记“最佳回答”、提取 TODO 和高频 Prompt。
*   **版本控制与对比**：追踪会话演变、对比多模型对同一 Prompt 的表现差异。
*   **安全与脱敏**：全本地存储，支持数据加密与 PII (个人隐私信息) 自动脱敏。

## 🚀 快速开始 (Draft)

*注：当前处于早期开发阶段，以下安装和使用说明为目标设计方案。*

### 安装

```bash
# 推荐使用 pipx 或 pip 安装
pipx install chatarch-cli
```

### 基础使用场景

**1. 导入你的第一条会话记录：**

```bash
chatasset import --source ./chatgpt-export.zip --format openai
```

**2. 从剪贴板或标准输入流管道录入：**

```bash
cat awesome-discussion.md | chatasset import --format markdown --title "CLI 架构设计" --tags "design,cli"
```

**3. 搜索与知识提取：**

```bash
# 检索包含“向量数据库”的内容，并以 JSON 格式输出
chatasset search "向量数据库" --output json

# 列出最近包含 “rust” 标签的高价值精选会话
chatasset list --tag rust --starred
```

**4. 编辑与沉淀：**

```bash
# 调用本地默认编辑器深度清洗当前对话
chatasset edit <session-id>
```

**5. 导出为报告或离线知识库：**

```bash
# 按阅读版模板导出为 Markdown 文件
chatasset export <session-id> --template reading --output ./note.md
```

## 📂 核心文档规划

更详细的需求规划与架构设计请参考：
*   [产品需求文档 (PRD)](./docs/PRD.md)
*   开发指引与规范 (请参考本仓库中的 `AGENTS.md` 与 `GEMINI.md`)

## 🛠️ 技术栈选择建议

*   **CLI 框架**: Typer + Rich (打造极佳的终端输出体验)
*   **核心存储**: SQLite3 + SQLAlchemy + FTS5 全文检索扩展
*   **数据模型**: Pydantic
*   **架构模式**: 插件化解析器 (Parser Adapters) 与 模板化渲染引擎 (Jinja2)

---

**License:** MIT
