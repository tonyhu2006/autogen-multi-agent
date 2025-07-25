# 测试和开发流程

## 测试策略

### 测试类型
1. **系统测试**: 使用 `python run_v4.py --test` 验证整体系统配置
2. **组件测试**: 使用 `python quick_test.py` 快速测试核心组件
3. **SMTP测试**: 使用 `python test_direct_smtp.py` 测试邮件发送功能
4. **API测试**: 验证Gemini Balance API连接和认证

### 测试工具
- **pytest**: 主要测试框架
- **pytest-asyncio**: 异步测试支持
- **自定义测试脚本**: quick_test.py, debug_401_precise.py

## 开发工作流

### 任务完成后的标准流程
1. **代码质量检查**:
   ```bash
   # 代码格式化
   black .
   
   # 代码风格检查
   flake8 .
   
   # 类型检查
   mypy .
   ```

2. **功能测试**:
   ```bash
   # 系统完整性测试
   python run_v4.py --test
   
   # 快速功能测试
   python quick_test.py
   
   # SMTP功能测试
   python test_direct_smtp.py
   ```

3. **单元测试**:
   ```bash
   # 运行所有测试
   pytest
   
   # 异步测试
   pytest -v --asyncio-mode=auto
   
   # 生成覆盖率报告
   pytest --cov=.
   ```

## 调试和故障排除

### 常见问题调试
1. **API认证问题**: 使用 `debug_401_precise.py` 调试401错误
2. **环境配置问题**: 检查 `.env.local` 文件配置
3. **SMTP连接问题**: 运行 `test_direct_smtp.py` 验证邮件配置
4. **依赖问题**: 重新安装 `pip install -r requirements.txt`

### 日志调试
- **系统日志**: `autogen_system_v4.log`
- **邮件服务日志**: `scheduled_email_simple.log`
- **研究服务日志**: `scheduled_research.log`

### 调试模式
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 在代码中添加调试信息
logger = logging.getLogger(__name__)
logger.debug("调试信息")
```

## 性能测试

### 内存使用监控
- 监控代理内存使用情况
- 定期清理对话历史
- 调整批处理大小

### API调用优化
- 实现请求缓存机制
- 设置合理的超时时间
- 使用连接池

## 部署前检查清单

### 配置验证
- [ ] 环境变量配置完整
- [ ] API密钥有效
- [ ] SMTP配置正确
- [ ] 邮件调度配置合理

### 功能验证
- [ ] 系统测试通过
- [ ] 邮件发送测试成功
- [ ] 研究功能正常
- [ ] 定时任务运行正常

### 代码质量
- [ ] 代码格式化完成
- [ ] 静态检查通过
- [ ] 类型检查无错误
- [ ] 单元测试覆盖率达标

## 持续集成建议

### 自动化测试
```bash
# 创建测试脚本 test_all.bat
@echo off
echo 开始代码质量检查...
black --check .
flake8 .
mypy .

echo 开始功能测试...
python run_v4.py --test
python quick_test.py

echo 开始单元测试...
pytest -v --asyncio-mode=auto

echo 所有测试完成！
```

### 代码审查要点
- 代码风格一致性
- 类型注解完整性
- 错误处理充分性
- 文档字符串完整性
- 测试覆盖率