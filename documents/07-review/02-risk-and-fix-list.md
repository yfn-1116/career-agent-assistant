# 风险点与修复清单

## 一、已识别风险

### 1. 检索精度

- **风险**：MemoryVectorStore 使用关键词 Token 重叠打分，召回精度低于 Embedding 语义检索
- **影响**：如果用户资料和 JD 用词不一致（如 JD 写"容器化部署"，资料写"Docker"），可能检索不到
- **修复方向**：接入 Embedding 模型 + Chroma/FAISS（已预留 VectorStore 接口）
- **当前对策**：在 JD Parser 的关键词池中覆盖常见同义词

### 2. 分析和生成质量

- **风险**：MatchAnalysisAgent 和 BuildAgent 为规则型，输出模板化
- **影响**：匹配分析的广度和深度有限，沟通话术不够自然
- **修复方向**：接入 LLM API（已预留 provider 接口）
- **当前对策**：规则覆盖了主要的技能匹配和模板生成场景

### 3. 样例数据覆盖

- **风险**：5 份 profile 文件覆盖场景有限
- **影响**：特定岗位（如非 AI 方向）匹配效果可能不佳
- **修复方向**：补充更多样化的样例数据
- **当前对策**：4 份 JD 覆盖了 4 个不同方向

### 4. 环境依赖

- **风险**：缺少 `pyproject.toml`，需要手动设置 `PYTHONPATH=src`
- **影响**：新用户可能遇到 `ModuleNotFoundError`
- **修复方向**：添加 `pyproject.toml`，或创建简单安装脚本
- **当前对策**：运行手册中明确说明了 `PYTHONPATH` 设置

### 5. CI 缺失

- **风险**：无 GitHub Actions 自动测试
- **影响**：push 后无法自动验证代码质量
- **修复方向**：添加 `.github/workflows/test.yml`
- **当前对策**：本地运行测试后再 push（运行手册中有说明）

## 二、修复优先级

| 优先级 | 项目 | 工作量 | 收益 |
|---|---|---|---|
| 🔴 高 | pyproject.toml | 小 | 消除 PYTHONPATH 问题 |
| 🟡 中 | GitHub Actions CI | 小 | 自动验证 |
| 🟡 中 | Embedding 检索 | 中 | 大幅提升召回精度 |
| 🟡 中 | LLM API 接入 | 中 | 大幅提升分析/生成质量 |
| 🟢 低 | 更多样例数据 | 小 | 覆盖更多场景 |
| 🟢 低 | README 截图 | 小 | 更好的展示效果 |

## 三、展示前必须确认

- [x] 165 tests 全部通过
- [x] `outputs/demo/*.md` 不被提交
- [x] README 状态与实际代码一致
- [x] 运行手册中的命令可执行
- [ ] Streamlit 页面在目标环境可启动（需现场验证）
- [ ] 学校服务器端口可访问（需现场验证）
