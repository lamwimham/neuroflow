"""
NeuroFlow LLM Agent 使用示例

展示如何直接使用原生 LLM 能力构建 Agent
"""

import asyncio
import os
from neuroflow.llm_agent import agent, LLMAgent, LLMConfig, tool


# ============================================
# 示例 1: 简单的对话 Agent
# ============================================

@agent(name="simple_chat_agent", description="简单的对话 Agent")
class SimpleChatAgent(LLMAgent):
    """最简单的 LLM Agent"""
    
    async def handle(self, request: dict) -> dict:
        user_message = request.get("message", "Hello")
        
        # 直接调用 LLM
        response = await self.llm.complete(user_message)
        
        return {
            "response": response,
            "model": self.llm.config.model
        }


# ============================================
# 示例 2: 带系统提示词的 Agent
# ============================================

@agent(name="assistant_agent", description="AI 助手 Agent")
class AssistantAgent(LLMAgent):
    """带系统提示词的 AI 助手"""
    
    async def handle(self, request: dict) -> dict:
        user_message = request.get("message")
        
        # 使用带上下文的对话
        response = await self.chat_with_context(
            user_message=user_message,
            system_prompt="你是一个有帮助的 AI 助手，擅长解答各种问题。"
        )
        
        return {"response": response}


# ============================================
# 示例 3: 多轮对话 Agent（带记忆）
# ============================================

@agent(name="memory_chat_agent", description="带记忆的对话 Agent")
class MemoryChatAgent(LLMAgent):
    """支持多轮对话的 Agent"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_history = []
    
    async def handle(self, request: dict) -> dict:
        user_message = request.get("message")
        user_id = request.get("user_id", "default")
        
        # 加载历史（实际应用中应该从数据库加载）
        history = self._load_history(user_id)
        
        # 调用 LLM
        response = await self.chat_with_context(
            user_message=user_message,
            system_prompt="你是一个友好的聊天机器人。",
            history=history
        )
        
        # 保存历史
        self._save_history(user_id, user_message, response)
        
        return {
            "response": response,
            "user_id": user_id
        }
    
    def _load_history(self, user_id: str) -> list:
        """加载对话历史"""
        # 简化实现，实际应该从存储中加载
        return []
    
    def _save_history(self, user_id: str, user_msg: str, bot_resp: str):
        """保存对话历史"""
        self.conversation_history.append({
            "user": user_msg,
            "bot": bot_resp
        })
        # 只保留最近 10 轮
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]


# ============================================
# 示例 4: 带工具的 LLM Agent（Function Calling）
# ============================================

@agent(name="tool_using_agent", description="会使用工具的 Agent")
class ToolUsingAgent(LLMAgent):
    """可以调用工具的 LLM Agent"""
    
    @tool(name="calculate", description="计算器")
    async def calculate(self, expression: str) -> str:
        """计算工具"""
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    @tool(name="get_weather", description="获取天气")
    async def get_weather(self, city: str) -> str:
        """天气查询工具"""
        # 模拟天气数据
        weather_data = {
            "Beijing": "晴天，25°C",
            "Shanghai": "多云，22°C",
            "Guangzhou": "小雨，28°C"
        }
        return weather_data.get(city, f"未知城市：{city}")
    
    async def handle(self, request: dict) -> dict:
        user_message = request.get("message")
        
        # 方案 1: 使用 LLM 判断是否需要调用工具
        # 首先让 LLM 分析意图
        intent_prompt = f"""
分析用户消息的意图，判断是否需要使用工具。

可用工具:
1. calculate - 计算数学表达式
2. get_weather - 查询天气

用户消息：{user_message}

请判断:
1. 是否需要使用工具？(是/否)
2. 如果需要，使用哪个工具？
3. 工具参数是什么？

以 JSON 格式回答:
{{
    "need_tool": true/false,
    "tool_name": "工具名称",
    "parameters": {{"参数名": "参数值"}}
}}
"""
        
        intent_response = await self.llm.complete(intent_prompt)
        
        # 这里应该解析 JSON 并调用工具
        # 简化处理：直接返回 LLM 回复
        if "calculate" in user_message.lower() or "计算" in user_message:
            # 提取表达式并计算
            response = await self.execute_tool("calculate", expression="2+2")
            return {"response": f"计算结果：{response}"}
        
        elif "weather" in user_message.lower() or "天气" in user_message:
            # 查询天气
            city = "Beijing"  # 实际应该从消息中提取
            response = await self.execute_tool("get_weather", city=city)
            return {"response": f"天气：{response}"}
        
        else:
            # 普通对话
            response = await self.llm.complete(user_message)
            return {"response": response}


# ============================================
# 示例 5: 文本生成 Agent
# ============================================

@agent(name="text_generator", description="文本生成 Agent")
class TextGeneratorAgent(LLMAgent):
    """专业文本生成 Agent"""
    
    async def handle(self, request: dict) -> dict:
        task_type = request.get("type", "general")
        topic = request.get("topic")
        length = request.get("length", "medium")
        
        # 根据类型构建提示词
        prompts = {
            "article": f"请写一篇关于'{topic}'的文章，长度{length}。",
            "poem": f"请创作一首关于'{topic}'的诗歌。",
            "story": f"请写一个关于'{topic}'的短篇故事。",
            "email": f"请帮我写一封关于'{topic}'的邮件。",
            "general": f"请生成关于'{topic}'的内容。"
        }
        
        prompt = prompts.get(task_type, prompts["general"])
        
        # 调用 LLM
        response = await self.llm.complete(
            prompt,
            temperature=0.8,  # 创造性任务用较高温度
            max_tokens=1000 if length == "long" else 500
        )
        
        return {
            "type": task_type,
            "content": response,
            "topic": topic
        }


# ============================================
# 示例 6: 代码助手 Agent
# ============================================

@agent(name="coding_assistant", description="编程助手 Agent")
class CodingAssistantAgent(LLMAgent):
    """编程助手 Agent"""
    
    async def handle(self, request: dict) -> dict:
        task = request.get("task")
        code = request.get("code", "")
        language = request.get("language", "python")
        
        # 构建提示词
        if task == "explain":
            prompt = f"请解释以下{language}代码:\n\n```{language}\n{code}\n```"
        elif task == "debug":
            prompt = f"请找出以下{language}代码的问题并修复:\n\n```{language}\n{code}\n```"
        elif task == "optimize":
            prompt = f"请优化以下{language}代码的性能:\n\n```{language}\n{code}\n```"
        elif task == "generate":
            prompt = f"请生成{language}代码实现以下功能：{code}"
        else:
            prompt = f"请帮助解决这个编程问题：{task}"
        
        # 调用 LLM
        response = await self.llm.complete(
            prompt,
            temperature=0.2  # 代码任务用较低温度
        )
        
        return {
            "task": task,
            "response": response,
            "language": language
        }


# ============================================
# 使用示例
# ============================================

async def main():
    """演示如何使用这些 Agent"""
    
    # 配置 LLM（从环境变量读取 API Key）
    llm_config = LLMConfig(
        provider="openai",  # 或 "anthropic", "ollama"
        model="gpt-3.5-turbo",
        temperature=0.7
    )
    
    # 创建 Agent
    chat_agent = SimpleChatAgent(llm_config=llm_config)
    
    # 使用 Agent
    result = await chat_agent.handle({
        "message": "你好，请介绍一下自己"
    })
    
    print(f"Agent 回复：{result['response']}")
    
    # 使用带工具的 Agent
    tool_agent = ToolUsingAgent(llm_config=llm_config)
    
    result = await tool_agent.handle({
        "message": "计算 2+2"
    })
    
    print(f"工具 Agent 回复：{result['response']}")


if __name__ == "__main__":
    # 确保设置了 API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("请设置环境变量：export OPENAI_API_KEY=your-api-key")
    else:
        asyncio.run(main())
