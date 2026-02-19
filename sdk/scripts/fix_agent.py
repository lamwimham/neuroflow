#!/usr/bin/env python3
"""
NeuroFlow Agent 修复工具

用于修复常见的 Agent 代码问题
"""

import sys
import os
from pathlib import Path


def fix_agent_file(agent_file: Path) -> bool:
    """修复 Agent 文件"""
    
    if not agent_file.exists():
        print(f"❌ 文件不存在：{agent_file}")
        return False
    
    content = agent_file.read_text()
    
    # 检查是否已经正确
    if 'AINativeAgentConfig(' in content and 'name=' in content:
        print(f"✅ 文件已经是正确的：{agent_file}")
        return True
    
    # 检查是否是 Agent 文件
    if 'AINativeAgent' not in content:
        print(f"⚠️  文件不包含 AINativeAgent: {agent_file}")
        return False
    
    print(f"🔧 正在修复：{agent_file}")
    
    # 修复 AINativeAgentConfig 初始化
    old_pattern = "AINativeAgentConfig()"
    new_pattern = """AINativeAgentConfig(
                name="agent",
                description="Agent",
            )"""
    
    content = content.replace(old_pattern, new_pattern)
    
    # 写回文件
    agent_file.write_text(content)
    
    print(f"✅ 修复完成：{agent_file}")
    print(f"\n📝 请手动检查并修改:")
    print(f"   1. 修改 name=\"agent\" 为实际的 Agent 名称")
    print(f"   2. 修改 description=\"Agent\" 为实际的描述")
    print(f"   3. 添加 llm_config 配置 (可选)")
    
    return True


def main():
    """主函数"""
    
    if len(sys.argv) < 2:
        print("NeuroFlow Agent 修复工具")
        print("=" * 50)
        print("\n用法:")
        print(f"  {sys.argv[0]} <agent_file.py>")
        print(f"  {sys.argv[0]} <agent_name>")
        print("\n示例:")
        print(f"  {sys.argv[0]} agents/first_agent.py")
        print(f"  {sys.argv[0]} first_agent")
        print("\n该工具会修复以下常见问题:")
        print("  - AINativeAgentConfig 缺少 name 参数")
        print("  - AINativeAgentConfig 缺少 description 参数")
        print()
        return
    
    arg = sys.argv[1]
    
    # 尝试不同的路径
    possible_paths = [
        Path(arg),
        Path(f"agents/{arg}"),
        Path(f"agents/{arg}.py"),
        Path(f"skills/{arg}"),
        Path(f"skills/{arg}.py"),
    ]
    
    agent_file = None
    for path in possible_paths:
        if path.exists():
            agent_file = path
            break
    
    if not agent_file:
        print(f"❌ 找不到文件：{arg}")
        print("\n请检查文件路径是否正确")
        return
    
    # 修复文件
    success = fix_agent_file(agent_file)
    
    if success:
        print("\n✅ 修复完成！")
        print("\n下一步:")
        print("  1. 编辑文件，修改 name 和 description")
        print("  2. 运行测试：neuroflow agent run <agent_name> \"你好\"")
    else:
        print("\n❌ 修复失败")
        print("请手动检查文件内容")


if __name__ == "__main__":
    main()
