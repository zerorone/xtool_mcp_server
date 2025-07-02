# MCP服务跨项目测试

这是一个用于测试XTool MCP服务跨项目使用的测试项目。

## 配置说明

本项目已包含 `.mcp.json` 配置文件，配置为连接到本地运行的 `xtool-mcp` Docker容器。

## 测试步骤

1. **确保MCP服务正在运行**
   ```bash
   docker ps | grep xtool-mcp
   ```

2. **在此目录启动Claude Code**
   ```bash
   cd test-project
   claude .
   ```

3. **测试MCP工具**
   
   在Claude Code中，可以尝试以下命令来测试MCP工具：

   - 列出可用模型：
     ```
     使用xtool列出所有可用的AI模型
     ```

   - 分析代码：
     ```
     使用xtool的analyze工具分析test_mcp.py文件
     ```

   - 代码审查：
     ```
     使用xtool的codereview工具审查test_mcp.py，重点关注代码质量和潜在问题
     ```

   - 生成测试：
     ```
     使用xtool的testgen工具为Calculator类生成单元测试
     ```

   - 生成文档：
     ```
     使用xtool的docgen工具为test_mcp.py生成详细文档
     ```

## 验证成功标准

1. Claude Code能够成功连接到MCP服务
2. 能够列出可用的AI模型
3. 能够使用各种工具分析和处理代码
4. 工具返回有意义的结果

## 故障排除

如果遇到问题：

1. 检查Docker容器状态：
   ```bash
   docker logs xtool-mcp
   ```

2. 验证MCP配置：
   ```bash
   cat .mcp.json
   ```

3. 确保API密钥已配置（检查父目录的.env文件）

## 下一步

成功验证后，可以将相同的 `.mcp.json` 配置复制到任何其他项目中使用MCP服务。