"""
工具管理模块
提供工具注册、发现和权限控制功能
"""

import asyncio
import json
from typing import Dict, List, Optional, Callable, Any, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import re


class PermissionLevel(Enum):
    """权限等级"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


@dataclass
class ToolInfo:
    """工具信息"""
    name: str
    description: str
    category: str
    permissions: List[PermissionLevel]
    parameters: Dict[str, Any]
    version: str
    author: str
    created_at: datetime
    updated_at: datetime
    enabled: bool = True


class ToolPermissionError(Exception):
    """工具权限错误"""
    pass


class ToolNotFoundError(Exception):
    """工具未找到错误"""
    pass


class ToolManager:
    """工具管理器"""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_info: Dict[str, ToolInfo] = {}
        self._categories: Dict[str, List[str]] = {}
        self._permissions: Dict[str, List[PermissionLevel]] = {}
    
    def register_tool(
        self,
        name: str,
        description: str = "",
        category: str = "general",
        permissions: List[PermissionLevel] = None,
        parameters: Dict[str, Any] = None,
        version: str = "1.0.0",
        author: str = "system"
    ):
        """
        注册工具的装饰器
        """
        if permissions is None:
            permissions = [PermissionLevel.EXECUTE]
        if parameters is None:
            parameters = {}
        
        def decorator(func: Callable):
            # 存储工具函数
            self._tools[name] = func
            
            # 创建工具信息
            tool_info = ToolInfo(
                name=name,
                description=description,
                category=category,
                permissions=permissions,
                parameters=parameters,
                version=version,
                author=author,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self._tool_info[name] = tool_info
            
            # 按类别组织
            if category not in self._categories:
                self._categories[category] = []
            self._categories[category].append(name)
            
            # 存储权限信息
            self._permissions[name] = permissions
            
            return func
        return decorator
    
    def register_function(
        self,
        func: Callable,
        name: str = None,
        description: str = "",
        category: str = "general",
        permissions: List[PermissionLevel] = None,
        parameters: Dict[str, Any] = None,
        version: str = "1.0.0",
        author: str = "system"
    ):
        """
        直接注册函数作为工具
        """
        tool_name = name or func.__name__
        
        if permissions is None:
            permissions = [PermissionLevel.EXECUTE]
        if parameters is None:
            parameters = {}
        
        # 存储工具函数
        self._tools[tool_name] = func
        
        # 创建工具信息
        tool_info = ToolInfo(
            name=tool_name,
            description=description,
            category=category,
            permissions=permissions,
            parameters=parameters,
            version=version,
            author=author,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self._tool_info[tool_name] = tool_info
        
        # 按类别组织
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool_name)
        
        # 存储权限信息
        self._permissions[tool_name] = permissions
    
    def get_tool(self, name: str, user_permissions: List[PermissionLevel] = None) -> Callable:
        """
        获取工具函数（带权限检查）
        """
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' not found")
        
        # 权限检查
        if user_permissions:
            required_perms = self._permissions.get(name, [])
            if not self._has_permission(required_perms, user_permissions):
                raise ToolPermissionError(f"Insufficient permissions to access tool '{name}'")
        
        return self._tools[name]
    
    def execute_tool(
        self,
        name: str,
        *args,
        user_permissions: List[PermissionLevel] = None,
        **kwargs
    ) -> Any:
        """
        执行工具（带权限检查和错误处理）
        """
        tool_func = self.get_tool(name, user_permissions)
        
        try:
            if asyncio.iscoroutinefunction(tool_func):
                return asyncio.run(tool_func(*args, **kwargs))
            else:
                return tool_func(*args, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Error executing tool '{name}': {str(e)}")
    
    async def execute_tool_async(
        self,
        name: str,
        *args,
        user_permissions: List[PermissionLevel] = None,
        **kwargs
    ) -> Any:
        """
        异步执行工具（带权限检查和错误处理）
        """
        tool_func = self.get_tool(name, user_permissions)
        
        try:
            if asyncio.iscoroutinefunction(tool_func):
                return await tool_func(*args, **kwargs)
            else:
                return tool_func(*args, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Error executing tool '{name}': {str(e)}")
    
    def get_tool_info(self, name: str) -> Optional[ToolInfo]:
        """获取工具信息"""
        return self._tool_info.get(name)
    
    def list_tools(self, category: str = None, enabled_only: bool = True) -> List[str]:
        """列出工具"""
        if category:
            return [name for name in self._categories.get(category, []) 
                   if not enabled_only or self._tool_info[name].enabled]
        else:
            return [name for name in self._tools.keys() 
                   if not enabled_only or self._tool_info[name].enabled]
    
    def list_categories(self) -> List[str]:
        """列出所有类别"""
        return list(self._categories.keys())
    
    def list_tools_by_category(self, category: str) -> List[str]:
        """按类别列出工具"""
        return self._categories.get(category, [])
    
    def update_tool(self, name: str, **updates) -> bool:
        """更新工具信息"""
        if name not in self._tool_info:
            return False
        
        tool_info = self._tool_info[name]
        for attr, value in updates.items():
            if hasattr(tool_info, attr):
                setattr(tool_info, attr, value)
        
        tool_info.updated_at = datetime.now()
        return True
    
    def disable_tool(self, name: str) -> bool:
        """禁用工具"""
        if name in self._tool_info:
            self._tool_info[name].enabled = False
            return True
        return False
    
    def enable_tool(self, name: str) -> bool:
        """启用工具"""
        if name in self._tool_info:
            self._tool_info[name].enabled = True
            return True
        return False
    
    def has_permission(self, tool_name: str, user_permissions: List[PermissionLevel]) -> bool:
        """检查用户是否有权限访问工具"""
        required_perms = self._permissions.get(tool_name, [])
        return self._has_permission(required_perms, user_permissions)
    
    def _has_permission(
        self,
        required_perms: List[PermissionLevel],
        user_perms: List[PermissionLevel]
    ) -> bool:
        """检查权限"""
        # 如果没有指定权限要求，则允许访问
        if not required_perms:
            return True
        
        # 检查用户权限是否包含所需权限
        user_perm_values = [perm.value for perm in user_perms]
        required_perm_values = [perm.value for perm in required_perms]
        
        # 如果用户有ADMIN权限，则允许所有操作
        if "admin" in user_perm_values:
            return True
        
        # 检查是否具有所有必需的权限
        return all(req_perm in user_perm_values for req_perm in required_perm_values)
    
    def search_tools(self, query: str) -> List[str]:
        """搜索工具"""
        query_lower = query.lower()
        results = []
        
        for name, info in self._tool_info.items():
            if (query_lower in name.lower() or 
                query_lower in info.description.lower() or
                query_lower in info.category.lower()):
                results.append(name)
        
        return results
    
    def get_tools_by_pattern(self, pattern: str) -> List[str]:
        """通过正则表达式模式查找工具"""
        compiled_pattern = re.compile(pattern, re.IGNORECASE)
        return [name for name in self._tools.keys() 
                if compiled_pattern.search(name)]


# 全局工具管理器实例
tool_manager = ToolManager()


# 便捷装饰器
def tool(
    name: str,
    description: str = "",
    category: str = "general",
    permissions: List[PermissionLevel] = None,
    parameters: Dict[str, Any] = None,
    version: str = "1.0.0",
    author: str = "system"
):
    """
    工具装饰器 - 增强版
    """
    return tool_manager.register_tool(
        name=name,
        description=description,
        category=category,
        permissions=permissions,
        parameters=parameters,
        version=version,
        author=author
    )


# 内置工具示例
@tool(
    name="builtin_math_calculator",
    description="内置数学计算器",
    category="utility",
    permissions=[PermissionLevel.EXECUTE],
    parameters={
        "expression": {"type": "string", "description": "数学表达式"}
    }
)
def math_calculator(expression: str) -> float:
    """
    简单的安全数学计算器
    注意：在实际生产环境中，应使用更安全的表达式解析器
    """
    # 简单的安全检查 - 只允许数字、运算符和括号
    allowed_chars = set('0123456789+-*/(). ')
    if not all(c in allowed_chars for c in expression):
        raise ValueError("Invalid characters in expression")
    
    try:
        # 使用eval的安全版本（实际生产中应使用ast.literal_eval或专门的表达式解析器）
        result = eval(expression, {"__builtins__": {}}, {})
        return float(result)
    except Exception as e:
        raise RuntimeError(f"Calculation error: {str(e)}")


@tool(
    name="builtin_string_utils",
    description="字符串处理工具",
    category="utility",
    permissions=[PermissionLevel.READ],
    parameters={
        "text": {"type": "string", "description": "输入文本"},
        "operation": {"type": "string", "description": "操作类型"}
    }
)
async def string_utils(text: str, operation: str) -> str:
    """
    字符串处理工具
    """
    operations = {
        "upper": lambda s: s.upper(),
        "lower": lambda s: s.lower(),
        "reverse": lambda s: s[::-1],
        "length": lambda s: str(len(s)),
        "words": lambda s: str(len(s.split())),
    }
    
    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")
    
    return operations[operation](text)


__all__ = [
    "ToolManager",
    "tool_manager",
    "tool",
    "ToolInfo",
    "PermissionLevel",
    "ToolPermissionError",
    "ToolNotFoundError"
]