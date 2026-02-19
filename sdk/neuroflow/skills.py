"""
NeuroFlow Skills系统
实现与Rust内核Skills系统的集成
"""
import os
import json
import yaml
from typing import Dict, List, Any, Optional, Callable, Awaitable
from pathlib import Path
import asyncio
import importlib.util
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SkillParameter:
    """技能参数定义"""
    name: str
    parameter_type: str  # "string", "number", "boolean", "array", "object"
    required: bool
    description: str
    default_value: Optional[Any] = None


@dataclass
class SkillDefinition:
    """技能定义"""
    name: str
    description: str
    version: str
    author: str
    parameters: List[SkillParameter]
    tags: List[str] = field(default_factory=list)
    license: Optional[str] = None
    skill_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class SkillsManager:
    """Skills管理器"""
    
    def __init__(self):
        self._skills_registry = {}
        self._skill_definitions = {}
        self._loaded_skills = set()
    
    async def register_skill_from_function(
        self, 
        func: Callable[..., Awaitable[Any]], 
        name: Optional[str] = None,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        从函数注册技能
        """
        skill_name = name or func.__name__
        
        # 如果没有提供参数，则尝试从类型注解推断
        if parameters is None:
            import inspect
            sig = inspect.signature(func)
            params = []
            for param_name, param in sig.parameters.items():
                # 默认为字符串类型
                param_schema = {
                    "name": param_name,
                    "parameter_type": "string",
                    "required": param.default == inspect.Parameter.empty,
                    "description": f"Parameter {param_name}"
                }
                if not param_schema["required"]:
                    param_schema["default_value"] = param.default
                params.append(SkillParameter(**param_schema))
        else:
            params = [SkillParameter(**p) for p in parameters]
        
        # 创建技能定义
        skill_def = SkillDefinition(
            name=skill_name,
            description=description,
            version="1.0.0",
            author="Developer",
            parameters=params
        )
        
        # 注册技能
        self._skills_registry[skill_name] = func
        self._skill_definitions[skill_name] = skill_def
        
        return skill_name
    
    async def register_skill_from_directory(self, skill_path: str) -> str:
        """
        从目录注册技能
        """
        skill_path = Path(skill_path)
        skill_md_path = skill_path / "SKILL.md"
        
        if not skill_md_path.exists():
            raise FileNotFoundError(f"SKILL.md not found in {skill_path}")
        
        # 读取SKILL.md文件
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析YAML前言和内容
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                yaml_frontmatter = parts[1]
                skill_body = parts[2]
                
                try:
                    metadata = yaml.safe_load(yaml_frontmatter)
                except yaml.YAMLError as e:
                    raise ValueError(f"Invalid YAML in SKILL.md: {e}")
            else:
                raise ValueError("Invalid SKILL.md format")
        else:
            raise ValueError("SKILL.md must start with YAML frontmatter")
        
        # 验证必需字段
        required_fields = ['name', 'description', 'version']
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Missing required field '{field}' in SKILL.md")
        
        # 创建技能定义
        skill_def = SkillDefinition(
            name=metadata['name'],
            description=metadata['description'],
            version=metadata.get('version', '1.0.0'),
            author=metadata.get('author', 'Unknown'),
            parameters=[SkillParameter(**p) for p in metadata.get('parameters', [])],
            tags=metadata.get('tags', []),
            license=metadata.get('license'),
            skill_path=str(skill_path)
        )
        
        # 检查是否有Python脚本
        scripts_dir = skill_path / "scripts"
        if scripts_dir.exists():
            main_script = scripts_dir / "main.py"
            if main_script.exists():
                # 动态加载Python脚本
                spec = importlib.util.spec_from_file_location(
                    f"skill_{metadata['name']}", 
                    main_script
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 假设脚本中有一个execute函数
                if hasattr(module, 'execute'):
                    skill_func = getattr(module, 'execute')
                    self._skills_registry[metadata['name']] = skill_func
                    self._skill_definitions[metadata['name']] = skill_def
                    self._loaded_skills.add(metadata['name'])
                    
                    return metadata['name']
        
        # 如果没有Python脚本，创建一个占位符
        async def placeholder_skill(**kwargs):
            """占位符技能函数"""
            return {
                "skill_name": metadata['name'],
                "status": "placeholder",
                "message": "Skill loaded from directory but no executable found",
                "metadata": metadata
            }
        
        self._skills_registry[metadata['name']] = placeholder_skill
        self._skill_definitions[metadata['name']] = skill_def
        self._loaded_skills.add(metadata['name'])
        
        return metadata['name']
    
    async def execute_skill(self, skill_name: str, **kwargs) -> Any:
        """
        执行技能
        """
        if skill_name not in self._skills_registry:
            raise ValueError(f"Skill '{skill_name}' not found")
        
        # 验证参数
        await self._validate_parameters(skill_name, kwargs)
        
        # 执行技能
        skill_func = self._skills_registry[skill_name]
        return await skill_func(**kwargs)
    
    async def _validate_parameters(self, skill_name: str, params: Dict[str, Any]) -> bool:
        """
        验证技能参数
        """
        skill_def = self._skill_definitions.get(skill_name)
        if not skill_def:
            raise ValueError(f"Skill definition for '{skill_name}' not found")
        
        # 检查必需参数
        for param_def in skill_def.parameters:
            if param_def.required and param_def.name not in params:
                if param_def.default_value is None:
                    raise ValueError(f"Missing required parameter '{param_def.name}' for skill '{skill_name}'")
                else:
                    params[param_def.name] = param_def.default_value
        
        # 验证参数类型
        for param_name, param_value in params.items():
            param_def = next((p for p in skill_def.parameters if p.name == param_name), None)
            if param_def:
                if not self._validate_parameter_type(param_def.parameter_type, param_value):
                    raise ValueError(f"Invalid type for parameter '{param_name}' in skill '{skill_name}'")
        
        return True
    
    def _validate_parameter_type(self, expected_type: str, value: Any) -> bool:
        """
        验证参数类型
        """
        type_mapping = {
            'string': str,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type is None:
            # 未知类型，接受任何值
            return True
        
        return isinstance(value, expected_python_type)
    
    def list_available_skills(self) -> List[str]:
        """
        列出可用技能
        """
        return list(self._skills_registry.keys())
    
    def get_skill_metadata(self, skill_name: str) -> Dict[str, Any]:
        """
        获取技能元数据
        """
        if skill_name not in self._skill_definitions:
            raise ValueError(f"Skill '{skill_name}' not found")
        
        skill_def = self._skill_definitions[skill_name]
        return {
            'name': skill_def.name,
            'description': skill_def.description,
            'version': skill_def.version,
            'author': skill_def.author,
            'tags': skill_def.tags,
            'license': skill_def.license,
            'parameters': [
                {
                    'name': p.name,
                    'type': p.parameter_type,
                    'required': p.required,
                    'description': p.description,
                    'default_value': p.default_value
                }
                for p in skill_def.parameters
            ],
            'skill_path': skill_def.skill_path,
            'created_at': skill_def.created_at.isoformat()
        }
    
    async def load_skills_from_directory(self, base_path: str) -> List[str]:
        """
        从目录加载所有技能
        """
        base_path = Path(base_path)
        loaded_skills = []
        
        if not base_path.exists():
            raise FileNotFoundError(f"Skills directory not found: {base_path}")
        
        # 遍历子目录
        for skill_dir in base_path.iterdir():
            if skill_dir.is_dir():
                try:
                    skill_name = await self.register_skill_from_directory(str(skill_dir))
                    loaded_skills.append(skill_name)
                    print(f"Loaded skill: {skill_name}")
                except Exception as e:
                    print(f"Failed to load skill from {skill_dir}: {e}")
        
        return loaded_skills


# 全局Skills管理器实例
skills_manager = SkillsManager()


def skill(
    name: Optional[str] = None,
    description: str = "",
    parameters: Optional[Dict[str, Any]] = None
):
    """
    技能装饰器
    """
    def decorator(func):
        # 将技能注册信息存储到全局列表中，稍后处理
        if not hasattr(skill, '_pending_registrations'):
            skill._pending_registrations = []
        
        skill._pending_registrations.append({
            'func': func,
            'name': name or func.__name__,
            'description': description,
            'parameters': parameters
        })
        
        return func
    
    return decorator


# 异步初始化函数
async def initialize_pending_skills():
    """
    初始化待处理的技能注册
    """
    if hasattr(skill, '_pending_registrations'):
        for registration in skill._pending_registrations:
            await skills_manager.register_skill_from_function(
                registration['func'],
                registration['name'],
                registration['description'],
                registration['parameters']
            )
        # 清空待处理列表
        skill._pending_registrations.clear()


# 在模块加载时安排初始化
async def schedule_initialization():
    """
    安排技能初始化
    """
    try:
        await initialize_pending_skills()
    except RuntimeError:
        # 如果没有事件循环，创建一个
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(initialize_pending_skills())


# 示例技能实现（不使用装饰器，直接注册）
async def hello_world_skill_impl(name: str) -> Dict[str, Any]:
    """
    示例问候技能实现
    """
    return {
        "greeting": f"Hello, {name}! Welcome to NeuroFlow.",
        "timestamp": datetime.now().isoformat(),
        "skill": "hello_world"
    }


async def echo_skill_impl(message: str, repeat: int = 1) -> Dict[str, Any]:
    """
    回声技能实现
    """
    repeated_message = " ".join([message] * repeat)
    return {
        "original": message,
        "repeated": repeated_message,
        "repeat_count": repeat,
        "skill": "echo"
    }


# 在模块加载时注册示例技能
async def register_example_skills():
    """
    注册示例技能
    """
    try:
        await skills_manager.register_skill_from_function(
            hello_world_skill_impl,
            name="hello_world",
            description="简单的问候技能",
            parameters=[
                {
                    "name": "name",
                    "parameter_type": "string",
                    "required": True,
                    "description": "被问候的人的名字"
                }
            ]
        )
        
        await skills_manager.register_skill_from_function(
            echo_skill_impl,
            name="echo",
            description="回声技能，返回输入参数",
            parameters=[
                {
                    "name": "message",
                    "parameter_type": "string",
                    "required": True,
                    "description": "要回显的消息"
                },
                {
                    "name": "repeat",
                    "parameter_type": "number",
                    "required": False,
                    "description": "重复次数",
                    "default_value": 1
                }
            ]
        )
    except Exception as e:
        print(f"Error registering example skills: {e}")


# 在模块加载时安排示例技能注册
async def schedule_example_skills():
    """
    安排示例技能注册
    """
    try:
        await register_example_skills()
    except RuntimeError:
        # 如果没有事件循环，创建一个
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(register_example_skills())


# 异步初始化
async def async_init():
    """
    异步初始化函数
    """
    await schedule_example_skills()
    await schedule_initialization()


# 技能执行辅助函数
async def execute_skill_safe(skill_name: str, **kwargs) -> Dict[str, Any]:
    """
    安全执行技能，包含错误处理
    """
    try:
        result = await skills_manager.execute_skill(skill_name, **kwargs)
        return {
            "success": True,
            "result": result,
            "skill": skill_name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "skill": skill_name
        }


# 尝试初始化（在有事件循环时）
try:
    # 如果已经有事件循环，就使用它
    loop = asyncio.get_running_loop()
    loop.create_task(async_init())
except RuntimeError:
    # 否则，创建一个新的事件循环
    import threading
    def run_async_init():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_init())
    
    # 在后台线程中运行初始化
    init_thread = threading.Thread(target=run_async_init, daemon=True)
    init_thread.start()