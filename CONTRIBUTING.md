# 为 OpenClaw AkShare 技能贡献代码

感谢你参与 OpenClaw AkShare 技能的开发。

## 贡献方式

### 报告缺陷

提交缺陷前，请先搜索现有问题。缺陷报告应包含清晰的标题、问题说明、复现步骤、预期行为、实际行为，以及 Python、AkShare 和操作系统版本。

### 建议改进

请使用明确的标题，详细描述建议内容、实际价值和适用示例。

### 提交合并请求

1. 派生本仓库。
2. 创建功能分支：`git checkout -b feature/amazing-feature`。
3. 提交修改：`git commit -m 'feat: 增加某项功能'`。
4. 推送分支：`git push origin feature/amazing-feature`。
5. 创建合并请求。

## 代码规范

- Python 代码遵循 PEP 8。
- 使用含义明确的变量名和函数名。
- 为函数和类添加中文文档字符串。
- 保持函数职责单一、实现简洁。
- 为复杂逻辑添加中文注释。
- 代码标识符、第三方 API、协议字段等为保证兼容性可以保留英文。

## 语言规范

后续开发中的说明性内容统一使用简体中文，包括代码注释、文档字符串、用户可见文案、项目文档、测试说明、提交信息和评审说明。详细规则见 [Agent.md](Agent.md)。

## 文档与测试

- 新增功能时同步更新相关文档和测试。
- 保持示例与当前实现一致。
- 使用清晰、简洁的中文。
- 提交前确保现有测试全部通过。
- 条件允许时覆盖多个 Python 版本。

## 开发环境

```bash
git clone https://github.com/your-username/openclaw-akshare-skill.git
cd openclaw-akshare-skill
python -m venv venv
source venv/bin/activate  # Windows：venv\Scripts\activate
pip install akshare
python scripts/test_quick.py
```

## 项目结构

```text
openclaw-akshare-skill/
├── SKILL.md              # 技能主说明
├── README.md             # 项目说明
├── Agent.md              # 仓库语言规范
├── LICENSE               # MIT 许可证
├── CHANGELOG.md          # 版本记录
├── CONTRIBUTING.md       # 贡献指南
├── references/           # 参考资料
└── scripts/              # 工具、示例和测试
```

## 分支与版本

推荐使用 `feature/`、`fix/`、`docs/`、`test/` 和 `refactor/` 分支前缀。项目版本号遵循语义化版本规范。

## 行为准则

尊重所有参与者，欢迎并帮助新贡献者，提供具体、建设性的反馈，并保持包容、专业的协作环境。
