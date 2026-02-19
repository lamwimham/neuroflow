# 使用 MCP 服务

MCP (Model Context Protocol) 提供与 AI 模型服务的标准化集成，包括文本生成、嵌入向量等功能。

## 什么是 MCP?

MCP 是一个标准化的协议，用于:

- 🤖 **文本生成**: 调用 LLM 生成文本
- 🔢 **嵌入向量**: 获取文本的向量表示
- 🎨 **多模态处理**: 图像、音频等
- 🔄 **流式响应**: 实时生成内容

## MCP 客户端

### 基础使用

```python
from neuroflow import agent, BaseAgent

@agent(name="mcp_agent")
class MCPAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        prompt = request.get("prompt")
        
        # 使用 MCP 生成文本
        response = await self.generate_text(
            prompt=prompt,
            model="gpt-3.5-turbo",
            params={
                "temperature": 0.7,
                "max_tokens": 100
            }
        )
        
        return {"response": response}
```

### 获取嵌入向量

```python
@agent(name="embedding_agent")
class EmbeddingAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        texts = request.get("texts", [])
        
        # 获取嵌入向量
        embeddings = await self.get_embeddings(
            texts=texts,
            model="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        return {
            "embeddings": embeddings,
            "dimensions": len(embeddings[0]) if embeddings else 0
        }
```

## 实用示例

### 1. 文本摘要 Agent

```python
from neuroflow import agent, BaseAgent

@agent(name="summarizer", description="文本摘要 Agent")
class SummarizerAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        text = request.get("text")
        max_length = request.get("max_length", 100)
        
        prompt = f"""
Summarize the following text in Chinese, keeping it under {max_length} characters:

{text}

Summary:
"""
        
        summary = await self.generate_text(
            prompt=prompt,
            model="gpt-3.5-turbo",
            params={
                "temperature": 0.3,
                "max_tokens": 200
            }
        )
        
        return {"summary": summary}
```

### 2. 文本分类 Agent

```python
from neuroflow import agent, BaseAgent

@agent(name="classifier", description="文本分类 Agent")
class ClassifierAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        text = request.get("text")
        categories = request.get("categories", ["positive", "negative", "neutral"])
        
        prompt = f"""
Classify the following text into one of these categories: {', '.join(categories)}

Text: {text}

Category:
"""
        
        category = await self.generate_text(
            prompt=prompt,
            model="gpt-3.5-turbo",
            params={
                "temperature": 0.1,  # 低温度确保稳定性
                "max_tokens": 20
            }
        )
        
        return {"category": category.strip()}
```

### 3. 语义搜索 Agent

```python
import numpy as np

@agent(name="semantic_search", description="语义搜索 Agent")
class SemanticSearchAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        query = request.get("query")
        documents = request.get("documents", [])
        top_k = request.get("top_k", 3)
        
        # 获取查询和文档的嵌入
        all_texts = [query] + documents
        embeddings = await self.get_embeddings(
            texts=all_texts,
            model="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # 计算相似度
        query_embedding = np.array(embeddings[0])
        doc_embeddings = np.array(embeddings[1:])
        
        # 余弦相似度
        similarities = []
        for i, doc_emb in enumerate(doc_embeddings):
            sim = np.dot(query_embedding, doc_emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_emb)
            )
            similarities.append((i, float(sim)))
        
        # 排序并返回 top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = [
            {"index": idx, "score": score, "document": documents[idx]}
            for idx, score in similarities[:top_k]
        ]
        
        return {"results": results}
```

### 4. 对话机器人 Agent

```python
@agent(name="chatbot", description="对话机器人 Agent")
class ChatbotAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        user_id = request.get("user_id")
        message = request.get("message")
        
        # 获取对话历史
        history = self._get_history(user_id)
        
        # 构建提示
        prompt = self._build_prompt(history, message)
        
        # 生成回复
        response = await self.generate_text(
            prompt=prompt,
            model="gpt-3.5-turbo",
            params={
                "temperature": 0.7,
                "max_tokens": 150
            }
        )
        
        # 更新历史
        self._update_history(user_id, message, response)
        
        return {
            "response": response,
            "conversation_id": user_id
        }
    
    def _get_history(self, user_id: str) -> list:
        """获取对话历史"""
        key = f"chat_history_{user_id}"
        return self.retrieve_memory(key) or []
    
    def _update_history(self, user_id: str, user_msg: str, bot_resp: str):
        """更新对话历史"""
        key = f"chat_history_{user_id}"
        history = self._get_history(user_id)
        history.append({"user": user_msg, "bot": bot_resp})
        
        # 只保留最近 10 轮
        if len(history) > 10:
            history = history[-10:]
        
        self.store_memory(key, history, "long_term")
    
    def _build_prompt(self, history: list, new_message: str) -> str:
        """构建提示"""
        prompt = "You are a helpful assistant.\n\n"
        
        for turn in history[-5:]:  # 最近 5 轮
            prompt += f"User: {turn['user']}\n"
            prompt += f"Assistant: {turn['bot']}\n"
        
        prompt += f"User: {new_message}\n"
        prompt += "Assistant: "
        
        return prompt
```

### 5. 代码生成 Agent

```python
@agent(name="code_generator", description="代码生成 Agent")
class CodeGeneratorAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        description = request.get("description")
        language = request.get("language", "python")
        
        prompt = f"""
Generate {language} code based on the following description:

{description}

Requirements:
- Write clean, readable code
- Include comments
- Follow best practices

Code:
"""
        
        code = await self.generate_text(
            prompt=prompt,
            model="gpt-3.5-turbo",
            params={
                "temperature": 0.2,  # 低温度确保代码准确性
                "max_tokens": 500
            }
        )
        
        return {
            "code": code,
            "language": language
        }
```

### 6. 翻译 Agent

```python
@agent(name="translator", description="翻译 Agent")
class TranslatorAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        text = request.get("text")
        source_lang = request.get("source_lang", "auto")
        target_lang = request.get("target_lang", "en")
        
        if source_lang == "auto":
            prompt = f"""
Translate the following text to {target_lang}:

{text}

Translation:
"""
        else:
            prompt = f"""
Translate the following text from {source_lang} to {target_lang}:

{text}

Translation:
"""
        
        translation = await self.generate_text(
            prompt=prompt,
            model="gpt-3.5-turbo",
            params={
                "temperature": 0.3,
                "max_tokens": 300
            }
        )
        
        return {
            "translation": translation,
            "source_lang": source_lang,
            "target_lang": target_lang
        }
```

## 高级用法

### 流式生成

```python
@agent(name="streaming_agent")
class StreamingAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        prompt = request.get("prompt")
        
        # 流式生成 (伪代码，实际实现取决于 MCP 服务端)
        async for chunk in self.generate_text_stream(
            prompt=prompt,
            model="gpt-3.5-turbo"
        ):
            yield {"chunk": chunk}
```

### 多模型协作

```python
@agent(name="multi_model_agent")
class MultiModelAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        prompt = request.get("prompt")
        
        # 使用不同模型处理不同任务
        # 1. 使用快速模型生成草稿
        draft = await self.generate_text(
            prompt=prompt,
            model="gpt-3.5-turbo",
            params={"temperature": 0.7}
        )
        
        # 2. 使用高质量模型优化
        refined = await self.generate_text(
            prompt=f"Improve the following text:\n\n{draft}",
            model="gpt-4",
            params={"temperature": 0.3}
        )
        
        return {
            "draft": draft,
            "refined": refined
        }
```

### 提示工程

```python
@agent(name="prompt_engineer")
class PromptEngineerAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        task = request.get("task")
        context = request.get("context", "")
        examples = request.get("examples", [])
        
        # 构建结构化提示
        prompt = self._build_structured_prompt(task, context, examples)
        
        response = await self.generate_text(
            prompt=prompt,
            model="gpt-3.5-turbo"
        )
        
        return {"response": response}
    
    def _build_structured_prompt(
        self,
        task: str,
        context: str,
        examples: list
    ) -> str:
        """构建结构化提示"""
        prompt = "You are an expert assistant.\n\n"
        
        # 添加上下文
        if context:
            prompt += f"Context:\n{context}\n\n"
        
        # 添加示例 (Few-shot)
        if examples:
            prompt += "Examples:\n"
            for example in examples:
                prompt += f"Input: {example['input']}\n"
                prompt += f"Output: {example['output']}\n\n"
        
        # 添加任务
        prompt += f"Task:\n{task}\n\n"
        prompt += "Response:\n"
        
        return prompt
```

## 配置 MCP 客户端

### 自定义端点

```python
from neuroflow.agent import MCPClient

# 使用自定义 MCP 端点
mcp_client = MCPClient(endpoint="http://your-mcp-server.com/mcp")

async with mcp_client as client:
    embeddings = await client.get_embeddings(["text1", "text2"])
    text = await client.generate_text(prompt="Hello")
```

### 模型选择

```python
# 不同任务使用不同模型

# 嵌入向量
embeddings = await self.get_embeddings(
    texts=["text1", "text2"],
    model="sentence-transformers/all-MiniLM-L6-v2"  # 轻量级
)

# 快速响应
fast_response = await self.generate_text(
    prompt="Quick answer",
    model="gpt-3.5-turbo"  # 快速
)

# 高质量响应
quality_response = await self.generate_text(
    prompt="Detailed analysis",
    model="gpt-4"  # 高质量
)
```

## 最佳实践

### 1. 提示优化

```python
# ❌ 模糊的提示
prompt = "Tell me about AI"

# ✅ 具体的提示
prompt = """
Provide a concise introduction to artificial intelligence (AI) covering:
1. Definition
2. Key applications
3. Current trends

Keep it under 200 words.
"""
```

### 2. 参数调优

```python
# 创造性任务 (高 temperature)
creative = await self.generate_text(
    prompt="Write a poem",
    model="gpt-3.5-turbo",
    params={"temperature": 0.8, "top_p": 0.9}
)

# 事实性任务 (低 temperature)
factual = await self.generate_text(
    prompt="Explain quantum computing",
    model="gpt-3.5-turbo",
    params={"temperature": 0.2, "top_p": 0.5}
)
```

### 3. 错误处理

```python
@agent(name="robust_mcp_agent")
class RobustMCPAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        prompt = request.get("prompt")
        
        try:
            response = await self.generate_text(
                prompt=prompt,
                model="gpt-3.5-turbo",
                params={"timeout": 30}
            )
            return {"response": response}
        
        except TimeoutError:
            self.context.logger.error("MCP request timed out")
            return {"error": "Request timeout"}
        
        except Exception as e:
            self.context.logger.exception(f"MCP error: {e}")
            return {"error": str(e)}
```

### 4. 成本控制

```python
@agent(name="cost_aware_agent")
class CostAwareAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        prompt = request.get("prompt")
        budget = request.get("budget", "low")
        
        # 根据预算选择模型
        if budget == "low":
            model = "gpt-3.5-turbo"
            max_tokens = 100
        elif budget == "medium":
            model = "gpt-3.5-turbo"
            max_tokens = 500
        else:
            model = "gpt-4"
            max_tokens = 1000
        
        response = await self.generate_text(
            prompt=prompt,
            model=model,
            params={"max_tokens": max_tokens}
        )
        
        return {
            "response": response,
            "model": model,
            "tokens_used": max_tokens
        }
```

## 调试和监控

### 日志记录

```python
@agent(name="logged_mcp_agent")
class LoggedMCPAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        prompt = request.get("prompt")
        
        self.context.logger.info(f"MCP request: {prompt[:100]}...")
        
        response = await self.generate_text(prompt=prompt)
        
        self.context.logger.info(f"MCP response: {response[:100]}...")
        
        return {"response": response}
```

### 性能监控

```python
import time

@agent(name="monitored_agent")
class MonitoredAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        start = time.time()
        
        response = await self.generate_text(
            prompt=request.get("prompt")
        )
        
        elapsed = time.time() - start
        
        return {
            "response": response,
            "latency_ms": elapsed * 1000
        }
```

## 下一步

- 🤖 **[构建 Agent](building-agents.md)** - 使用 MCP 创建 Agent
- 🛠️ **[开发工具](developing-tools.md)** - 集成 MCP 工具
- 📊 **[性能优化](../best-practices/performance.md)** - 优化 MCP 调用
- 🔒 **[安全实践](../best-practices/security.md)** - MCP 安全考虑

---

**参考资源**:
- [MCP 规范](https://modelcontextprotocol.io/)
- [示例代码](../examples/advanced.md)
- [故障排除](../troubleshooting/faq.md)
