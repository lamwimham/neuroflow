"""
NeuroFlow Template Renderer

模板渲染引擎，用于生成 Agent 项目文件
"""

import os
import shutil
from pathlib import Path
from string import Template
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """
    模板渲染器
    
    用法:
        renderer = TemplateRenderer("standard")
        renderer.render(
            output_dir=Path("my_agent"),
            variables={
                "agent_name": "assistant",
                "description": "智能助手",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
            }
        )
    """
    
    def __init__(self, template_name: str = "standard"):
        """
        初始化模板渲染器
        
        Args:
            template_name: 模板名称 (basic/standard/advanced)
        """
        self.template_name = template_name
        self.template_dir = self._get_template_dir()
        
        if not self.template_dir.exists():
            raise ValueError(f"Template '{template_name}' not found at {self.template_dir}")
        
        logger.info(f"Initialized template renderer: {template_name}")
        logger.info(f"Template directory: {self.template_dir}")
    
    def _get_template_dir(self) -> Path:
        """获取模板目录"""
        base_dir = Path(__file__).parent.parent / "templates" / "agent"
        return base_dir / self.template_name
    
    def render(
        self,
        output_dir: Path,
        variables: Dict[str, Any],
        overwrite: bool = False,
    ) -> bool:
        """
        渲染模板到指定目录
        
        Args:
            output_dir: 输出目录
            variables: 模板变量字典
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            是否成功
        """
        logger.info(f"Rendering template '{self.template_name}' to {output_dir}")
        logger.info(f"Variables: {variables}")
        
        try:
            # 创建输出目录
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制并渲染所有文件
            files_rendered = 0
            for item in self.template_dir.rglob("*"):
                if item.is_file():
                    # 计算相对路径
                    rel_path = item.relative_to(self.template_dir)
                    target_path = output_dir / rel_path
                    
                    # 创建目标目录
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 检查是否已存在
                    if target_path.exists() and not overwrite:
                        logger.warning(f"File exists, skipping: {target_path}")
                        continue
                    
                    # 渲染文件内容
                    if self._is_template_file(item):
                        self._render_file(item, target_path, variables)
                    else:
                        # 二进制文件直接复制
                        shutil.copy2(item, target_path)
                    
                    files_rendered += 1
                    logger.debug(f"Rendered: {target_path}")
            
            logger.info(f"Template rendered successfully. Files: {files_rendered}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to render template: {e}")
            raise
    
    def _is_template_file(self, file_path: Path) -> bool:
        """检查是否是模板文件（文本文件）"""
        text_extensions = {'.py', '.yaml', '.yml', '.md', '.txt', '.sh', '.toml', '.json'}
        return file_path.suffix in text_extensions
    
    def _render_file(
        self,
        source_path: Path,
        target_path: Path,
        variables: Dict[str, Any],
    ):
        """
        渲染单个文件
        
        Args:
            source_path: 源文件路径
            target_path: 目标文件路径
            variables: 模板变量
        """
        # 读取源文件
        content = source_path.read_text(encoding='utf-8')
        
        # 渲染文件名（处理 {{agent_name}}.py.template 格式）
        target_name = self._render_filename(source_path.name, variables)
        target_path = target_path.parent / target_name
        
        # 渲染文件内容
        rendered_content = self._render_content(content, variables)
        
        # 写入目标文件
        target_path.write_text(rendered_content, encoding='utf-8')
    
    def _render_filename(self, filename: str, variables: Dict[str, Any]) -> str:
        """渲染文件名"""
        # 移除 .template 后缀（如果有）
        if filename.endswith('.template'):
            filename = filename[:-9]
        
        # 替换变量
        for key, value in variables.items():
            filename = filename.replace(f'{{{{{key}}}}}', str(value))
        
        return filename
    
    def _render_content(
        self,
        content: str,
        variables: Dict[str, Any],
    ) -> str:
        """渲染文件内容"""
        # 使用 Python Template 进行变量替换
        template = Template(content)
        
        # 添加默认变量
        all_variables = {
            'version': '0.4.1',
            'python_version': '3.10',
        }
        all_variables.update(variables)
        
        try:
            rendered = template.safe_substitute(all_variables)
            return rendered
        except Exception as e:
            logger.warning(f"Template substitution error: {e}")
            return content
    
    def get_template_info(self) -> Dict[str, Any]:
        """获取模板信息"""
        info_file = self.template_dir / "TEMPLATE_INFO.yaml"
        
        if info_file.exists():
            import yaml
            try:
                return yaml.safe_load(info_file.read_text())
            except Exception as e:
                logger.warning(f"Failed to load template info: {e}")
        
        # 返回默认信息
        return {
            "name": self.template_name,
            "description": f"{self.template_name} agent template",
            "version": "0.4.1",
        }


def create_agent_from_template(
    agent_name: str,
    output_dir: Path,
    template: str = "standard",
    description: str = "智能助手",
    llm_provider: str = "openai",
    llm_model: str = "gpt-4",
    overwrite: bool = False,
) -> bool:
    """
    从模板创建 Agent
    
    Args:
        agent_name: Agent 名称
        output_dir: 输出目录
        template: 模板名称
        description: Agent 描述
        llm_provider: LLM 提供商
        llm_model: LLM 模型
        overwrite: 是否覆盖
        
    Returns:
        是否成功
    """
    logger.info(f"Creating agent '{agent_name}' from template '{template}'")
    
    # 准备变量
    variables = {
        "agent_name": agent_name,
        "description": description,
        "llm_provider": llm_provider,
        "llm_model": llm_model,
        "workspace_name": f"{agent_name}_workspace",
    }
    
    # 渲染模板
    renderer = TemplateRenderer(template)
    success = renderer.render(output_dir, variables, overwrite)
    
    if success:
        logger.info(f"Agent '{agent_name}' created successfully at {output_dir}")
    
    return success


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python template_renderer.py <output_dir> [template_name]")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    template = sys.argv[2] if len(sys.argv) > 2 else "standard"
    
    success = create_agent_from_template(
        agent_name="test_agent",
        output_dir=output_dir,
        template=template,
    )
    
    if success:
        print(f"✅ Agent created successfully at {output_dir}")
    else:
        print("❌ Failed to create agent")
        sys.exit(1)
