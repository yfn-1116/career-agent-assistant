# Browser Assistant Usage Guide

## 启动本地 API

```bash
uvicorn career_agent.api.app:app --host 127.0.0.1 --port 8765
```

## 加载 Chrome 插件

1. Chrome → `chrome://extensions`
2. 开启开发者模式
3. 加载已解压的扩展程序 → 选择 `browser_extension/` 目录

## 使用方式

### 分析岗位详情页

1. 打开 BOSS/实习僧岗位页面
2. 点击 Chrome 工具栏的 Smart Apply 图标
3. 点击 "Analyze Current Page"
4. 查看匹配分数、招聘意图、话术
5. 点击 "Copy Message" 复制话术发给 HR

### 批量筛选岗位列表

1. 打开搜索/推荐页
2. 点击 "Analyze Current Page"
3. 查看 Top 5 推荐岗位和排名

### HR 聊天回复

1. 打开聊天页面
2. 点击 "Analyze Current Page"
3. 查看建议回复
4. 点击 "Copy Reply" 复制发送

## 安全边界

- 插件只读取当前页面文本
- 不自动发送消息
- 不自动投递简历
- 不保存账号密码
- 不绕过验证码
- 所有外部动作需用户确认

## 当前限制

- 需要本地运行 API 服务
- 页面解析依赖文本内容，不解析 DOM 结构
- PDF 简历在服务器生成，需要本地文件系统访问
