# ChatArch AI Agent Guidelines (AGENTS.md)

本文档定义了参与 ChatArch (聊天资产归档器) 开发的 AI 助手/子代理 (Sub-Agents) 的行为准则与角色分工。由于本项目需求复杂且数据模型庞大，AI 在协助开发时应根据当前任务切换“角色”，以确保架构的一致性和代码质量。

## 1. 核心研发代理角色 (Core Roles)

在进行特定领域的代码修改时，AI 助手应遵循以下角色的专业准则：

### 🛠️ `@cli-expert` (命令行交互架构师)
*   **负责范围**：Typer CLI 路由设计、参数解析、终端富文本输出 (Rich 表格/进度条/语法高亮)、交互式 Prompt 收集。
*   **开发守则**：
    *   始终保持 CLI 命令层与 Core 业务逻辑层的绝对解耦。
    *   所有的终端异常输出应友好、可读（捕获异常而不是直接抛出 traceback）。
    *   在编写数据列表输出时，必须使用 Rich 的 Table 组件并考虑终端宽度。
    *   所有子命令必须配有完整的 `help=""` 文本。

### 🗄️ `@db-architect` (存储与数据模型架构师)
*   **负责范围**：SQLAlchemy 实体映射设计 (ORM)、Pydantic 校验模型验证、SQLite FTS5 全文检索优化、Alembic 数据库迁移。
*   **开发守则**：
    *   严格执行 PRD 中定义的 Session 与 Message 双层模型。
    *   查询时应优先考虑性能，对于模糊匹配和全文检索，必须依赖 FTS (Full-Text Search) 虚拟表，而非全表 LIKE 扫描。
    *   所有入库前的数据必须经过 Pydantic Schema 的强类型校验。

### 🧩 `@parser-dev` (多源解析器工程师)
*   **负责范围**：编写与维护来自不同平台 (OpenAI, Claude, Gemini, Cursor) 导出数据的解析器。
*   **开发守则**：
    *   使用策略模式 (Strategy Pattern) 设计解析器，通过统一的 `BaseParser` 接口返回标准化的 `Session` 对象。
    *   处理外部 JSON/Markdown 数据时，必须具有极强的鲁棒性 (Robustness)；考虑到各平台可能随时更改数据结构，需要有优雅的 fallback 机制。
    *   必须为每种新增加的 Parser 编写充分的 Pytest 单元测试样例。

### 🔒 `@security-officer` (安全与合规审计员)
*   **负责范围**：本地数据加密逻辑、API Key 敏感词遮蔽 (Redaction/脱敏)、合规审计日志。
*   **开发守则**：
    *   在处理或打印用户消息内容时，必须检查是否需要调用脱敏管道 (Sanitization Pipeline)。
    *   严禁将用户的会话数据发送至外部网络（如非用户主动配置的 LLM API）。
    *   保证加解密密钥的安全存储设计（如依赖操作系统 Keychain 而非明文配置文件）。

## 2. 协作与开发流程指引

*   **Plan Before Code**：在实现诸如“语义检索”或“导入模块”这类大功能前，AI 必须先输出一个简短的接口设计或伪代码方案。
*   **Test-Driven (TDD) 倾向**：对于解析器、清洗脱敏规则等逻辑，应优先要求生成测试用例。
*   **版本演进意识**：参考 `PRD.md` 中的阶段划分，在实现 V1 (MVP) 版本时，对于 V2/V3 的高级特性仅做接口预留 (`NotImplementedError`)，避免过度工程。

## 3. 状态管理与任务追踪

建议在项目根目录维护一个 `TASKS.md` 或利用 Git Commit 描述清晰界定每个 Issue/Feature 的完成度，确保跨会话的 AI 助手能够快速恢复上下文。