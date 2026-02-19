"""
NeuroFlow Python SDK - Skill Learning System

LLM 驱动的技能学习系统:
1. 从示例中学习技能
2. 生成技能实现代码
3. 技能验证和优化
4. 技能注册和执行
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json
import uuid
import logging

from ..orchestrator import LLMClient, Message
from ..tools import (
    ToolDefinition,
    ToolParameter,
    ToolSource,
    ToolExecutionMode,
)

logger = logging.getLogger(__name__)


@dataclass
class SkillExample:
    """技能示例"""
    input: Dict[str, Any]
    expected_output: Any
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "input": self.input,
            "expected_output": self.expected_output,
            "context": self.context,
        }


@dataclass
class LearnedSkill:
    """学习到的技能"""
    id: str
    name: str
    description: str
    implementation_code: str
    parameters: List[ToolParameter]
    return_type: str
    examples: List[SkillExample] = field(default_factory=list)
    confidence: float = 0.0
    language: str = "python"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "implementation_code": self.implementation_code,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.parameter_type,
                    "description": p.description,
                    "required": p.required,
                }
                for p in self.parameters
            ],
            "return_type": self.return_type,
            "examples": [e.to_dict() for e in self.examples],
            "confidence": self.confidence,
            "language": self.language,
            "metadata": self.metadata,
        }


class SkillLearner:
    """
    技能学习器 - 让 LLM 从示例中学习并生成新技能
    
    核心能力:
    1. 分析示例推断技能功能
    2. 生成技能实现代码
    3. 验证技能正确性
    4. 优化技能性能
    
    用法:
        learner = SkillLearner(llm_client)
        
        skill = await learner.learn_skill(
            skill_description="将文本转换为摩尔斯电码",
            examples=[
                SkillExample(
                    input={"text": "HELLO"},
                    expected_output=".... . .-.. .-.. ---",
                ),
            ],
        )
        
        tool_def = await learner.generate_tool_definition(skill)
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        
        # 技能学习提示词
        self.learning_prompt = """你是一个善于学习的 AI 助手。请从示例中学习一个新技能。

技能描述：{skill_description}

示例:
{examples}

请完成以下任务:
1. 分析示例，推断技能的输入参数和输出格式
2. 编写 Python 函数实现这个技能
3. 确保函数能处理示例中的所有情况
4. 添加适当的错误处理

请用以下 JSON 格式输出:
{{
    "name": "技能名称",
    "description": "技能描述",
    "parameters": [
        {{"name": "param1", "type": "string", "description": "...", "required": true}}
    ],
    "return_type": "object",
    "implementation": "def skill_function(...):\\n    ...",
    "confidence": 0.9,
    "test_cases": [
        {{"input": {{...}}, "expected_output": "..."}}
    ]
}}
"""
        
        # 技能优化提示词
        self.optimization_prompt = """你是一个善于优化的 AI 助手。请优化以下技能实现。

当前技能:
- 名称：{skill_name}
- 描述：{skill_description}
- 当前实现:
{current_implementation}

性能数据:
- 平均执行时间：{avg_time_ms}ms
- 成功率：{success_rate}%
- 使用次数：{usage_count}

用户反馈:
{feedback}

请优化技能实现，使其:
1. 执行更快
2. 更可靠
3. 代码更清晰
4. 错误处理更完善

请输出优化后的 Python 代码实现。
"""
    
    async def learn_skill(
        self,
        skill_description: str,
        examples: List[SkillExample],
    ) -> LearnedSkill:
        """
        从示例学习新技能
        
        Args:
            skill_description: 技能描述
            examples: 示例列表
            
        Returns:
            学习到的技能
        """
        # 构建示例文本
        examples_text = "\n\n".join([
            f"示例 {i+1}:\n输入：{json.dumps(e.input)}\n期望输出：{json.dumps(e.expected_output)}"
            for i, e in enumerate(examples)
        ])
        
        messages = [
            Message.system(
                self.learning_prompt.format(
                    skill_description=skill_description,
                    examples=examples_text,
                )
            ),
            Message.user("请学习这个技能并输出 JSON 格式的实现。"),
        ]
        
        # 调用 LLM
        response = await self.llm.chat(
            messages=messages,
            response_format={"type": "json_object"},
        )
        
        try:
            skill_data = json.loads(response.content)
            
            # 解析参数
            parameters = [
                ToolParameter(
                    name=p["name"],
                    parameter_type=p.get("type", "string"),
                    description=p.get("description", ""),
                    required=p.get("required", True),
                )
                for p in skill_data.get("parameters", [])
            ]
            
            # 创建技能
            skill = LearnedSkill(
                id=f"learned:{uuid.uuid4().hex[:8]}",
                name=skill_data.get("name", f"skill_{uuid.uuid4().hex[:8]}"),
                description=skill_data.get("description", skill_description),
                implementation_code=skill_data.get("implementation", ""),
                parameters=parameters,
                return_type=skill_data.get("return_type", "object"),
                examples=examples,
                confidence=skill_data.get("confidence", 0.0),
                metadata={
                    "test_cases": skill_data.get("test_cases", []),
                },
            )
            
            logger.info(f"Learned new skill: {skill.name}")
            return skill
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse learned skill: {e}")
            raise ValueError(f"Failed to parse learned skill: {e}")
    
    async def optimize_skill(
        self,
        existing_skill: LearnedSkill,
        performance_data: Dict[str, Any],
        feedback: Optional[List[Dict[str, Any]]] = None,
    ) -> LearnedSkill:
        """
        优化现有技能
        
        Args:
            existing_skill: 现有技能
            performance_data: 性能数据
            feedback: 用户反馈
            
        Returns:
            优化后的技能
        """
        feedback_text = "\n".join([
            f"- {f.get('comment', '无具体评论')}"
            for f in (feedback or [])
        ]) or "暂无反馈"
        
        messages = [
            Message.system(
                self.optimization_prompt.format(
                    skill_name=existing_skill.name,
                    skill_description=existing_skill.description,
                    current_implementation=existing_skill.implementation_code,
                    avg_time_ms=performance_data.get("avg_time_ms", 0),
                    success_rate=performance_data.get("success_rate", 100),
                    usage_count=performance_data.get("usage_count", 0),
                    feedback=feedback_text,
                )
            ),
            Message.user("请输出优化后的代码实现。"),
        ]
        
        response = await self.llm.chat(messages=messages)
        
        # 创建优化后的技能
        optimized_skill = LearnedSkill(
            id=existing_skill.id,
            name=existing_skill.name,
            description=existing_skill.description,
            implementation_code=response.content,
            parameters=existing_skill.parameters,
            return_type=existing_skill.return_type,
            examples=existing_skill.examples,
            confidence=min(1.0, existing_skill.confidence + 0.1),
            metadata={
                **existing_skill.metadata,
                "optimized": True,
            },
        )
        
        logger.info(f"Optimized skill: {optimized_skill.name}")
        return optimized_skill
    
    async def generate_tool_definition(
        self, 
        skill: LearnedSkill
    ) -> ToolDefinition:
        """将学习到的技能转换为工具定义"""
        return ToolDefinition(
            id=skill.id,
            name=skill.name,
            description=skill.description,
            source=ToolSource.LLM_GENERATED,
            parameters=skill.parameters,
            return_type=skill.return_type,
            execution_mode=ToolExecutionMode.SANDBOXED,
            metadata={
                "implementation": skill.implementation_code,
                "examples_count": len(skill.examples),
                "confidence": skill.confidence,
                "language": skill.language,
            },
            generated_by=self.llm.config.model,
        )
    
    async def validate_skill(
        self,
        skill: LearnedSkill,
        test_cases: Optional[List[SkillExample]] = None,
    ) -> Dict[str, Any]:
        """
        验证技能正确性
        
        Args:
            skill: 技能
            test_cases: 测试用例
            
        Returns:
            验证结果
        """
        if test_cases is None:
            test_cases = skill.examples
        
        results = {
            "total": len(test_cases),
            "passed": 0,
            "failed": 0,
            "details": [],
        }
        
        for i, test in enumerate(test_cases):
            try:
                # 执行技能代码
                result = await self._execute_skill_code(
                    skill.implementation_code,
                    test.input,
                )
                
                # 比较结果
                if result == test.expected_output:
                    results["passed"] += 1
                    results["details"].append({
                        "test": i + 1,
                        "passed": True,
                    })
                else:
                    results["failed"] += 1
                    results["details"].append({
                        "test": i + 1,
                        "passed": False,
                        "expected": test.expected_output,
                        "got": result,
                    })
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "test": i + 1,
                    "passed": False,
                    "error": str(e),
                })
        
        results["success_rate"] = results["passed"] / results["total"] if results["total"] > 0 else 0
        return results
    
    async def _execute_skill_code(
        self,
        code: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """执行技能代码（沙箱环境）"""
        # 创建安全的执行环境
        safe_globals = self._create_safe_globals()
        safe_locals = {}
        
        try:
            # 执行代码定义函数
            exec(code, safe_globals, safe_locals)
            
            # 获取函数
            func_name = None
            for name, obj in safe_locals.items():
                if callable(obj) and not name.startswith('_'):
                    func_name = name
                    break
            
            if not func_name:
                raise ValueError("No function found in code")
            
            func = safe_locals[func_name]
            
            # 调用函数
            import asyncio
            if asyncio.iscoroutinefunction(func):
                result = await func(**arguments)
            else:
                result = func(**arguments)
            
            return result
        except Exception as e:
            raise RuntimeError(f"Skill execution error: {e}")
    
    def _create_safe_globals(self) -> Dict[str, Any]:
        """创建安全的全局命名空间"""
        # 只允许安全的内置函数
        safe_builtins = {
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'range': range,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'sorted': sorted,
            'reversed': reversed,
            'any': any,
            'all': all,
            'isinstance': isinstance,
            'issubclass': issubclass,
            'hasattr': hasattr,
            'getattr': getattr,
            'setattr': setattr,
            'print': print,
            'json': json,
        }
        
        return {'__builtins__': safe_builtins}


__all__ = [
    "SkillExample",
    "LearnedSkill",
    "SkillLearner",
]
