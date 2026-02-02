# FrameLeap

AI驱动的动态漫自动生成系统。

## 开发工作流

### 代码提交规范

**重要**：每次对项目进行修改或新增文件后，必须使用自动化提交脚本进行 git 提交。

```bash
# 提交所有更改
python git_auto_new.py "feat: 添加xxx功能"

# 只提交指定文件
python git_auto_new.py "docs: 更新README" -f README.md

# 不推送到远程（仅本地提交）
python git_auto_new.py "wip: 本地保存" --no-push

# 查看脚本帮助
python git_auto_new.py -h
```

**Commit Message 格式**：
- `feat:` - 新功能
- `fix:` - 修复bug
- `docs:` - 文档更新
- `refactor:` - 重构
- `opt:` - 优化
- `test:` - 测试相关
