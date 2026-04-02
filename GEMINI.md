# Gemini CLI Workspace Instructions (GEMINI.md)

本文件是针对本工作区 (ChatArch / `chatarch-cli`) 的强制性开发规范与指导原则。在使用 Gemini CLI 协助开发时，**必须**严格遵守以下规定。

## 1. 技术栈约束 (Tech Stack Mandates)

*   **语言**: Python 3.10+。必须使用 Type Hints (类型注解)。
*   **CLI 框架**: `typer` (基于 Click)。所有命令必须使用 Typer App 路由。
*   **UI/输出**: `rich`。严禁使用原生 `print()` 打印复杂表格或彩色文本。
*   **数据库/ORM**: `SQLAlchemy` 2.0+ 配合 `SQLite3`。对于全文检索必须使用 SQLite `FTS5` 模块。
*   **模型与校验**: `pydantic` v2。处理外部导入数据（如 JSON/Dict）时必须通过 Pydantic Model 进行校验。

## 2. 架构模式 (Architectural Patterns)

*   **解耦原则**: CLI 层 (如 `app.command()`) 与业务逻辑层 (Core Logic) 必须分离。CLI 层只负责参数解析、异常捕获以及调用 Core 函数，然后通过 Rich 输出结果。
*   **存储路径**: 
    *   默认数据库路径: `~/.chatarch/data.db` (或基于配置)
    *   默认配置路径: `~/.chatarch/config.yaml`
*   **防御性编程**: 对所有文件 I/O、数据库操作和 JSON 解析都要进行 `try...except` 处理，并通过 CLI 层输出友好的错误信息。

## 3. 代码风格与质量 (Code Style & Quality)

*   **Linter / Formatter**: 默认使用 `ruff` 和 `black` 风格。
*   **Docstrings**: 所有的公开类与函数必须包含符合 Google Style 的 Docstring。
*   **测试**: 新增解析器 (Parser) 或核心处理逻辑时，必须同步在 `tests/` 目录下添加 `pytest` 测试用例。

## 4. Git 提交流程 (Git Workflow)

*   除非用户明确要求（例如："Commit the change"），否则**不要**自动执行 git commit。
*   在被要求提交时，必须遵循 **Conventional Commits** 规范（如 `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`）。
*   在提交前，优先执行 `git status` 和 `git diff` 确认变更范围。

## 5. 项目级特殊提示 (Project Specifics)

*   当前项目名为 **ChatArch**，CLI 命令主体设计为 `chatasset`。
*   请随时参考 `docs/PRD.md` 中关于数据模型 (Conversation & Message) 的字段定义，严禁擅自修改核心表结构的设计理念，确需修改请先与用户探讨。
*   在进行大型重构或多文件关联更改前，请先输出 **Plan (计划)** 供用户确认。