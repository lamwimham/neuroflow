"""
trader Agent

一个专注于加密货币市场的交易员

此 Agent 使用 Skills 系统提供技术分析能力。
"""
import asyncio
import yaml
import sys
from pathlib import Path
from neuroflow import AINativeAgent, AINativeAgentConfig, LLMConfig
from neuroflow.skills import SkillsManager


class TraderAgent(AINativeAgent):
    """
    一个专注于加密货币市场的交易员
    
    使用 Skills:
    - technical-indicators: 技术指标计算
    - trading-signals: 交易信号生成
    """

    def __init__(self, config_path: str = "config.yaml"):
        # 加载配置
        self.config_data = self._load_config(config_path)
        
        # 初始化 Skills 管理器
        self.skills_manager = SkillsManager()

        super().__init__(
            AINativeAgentConfig(
                name="trader",
                description="一个专注于加密货币市场的交易员，提供技术分析和交易信号",
                llm_config=LLMConfig(
                    provider="deepseek",
                    model="deepseek-chat",
                ),
            )
        )

        # 加载 Skills
        self._load_skills()

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_skills(self):
        """加载交易相关的 Skills"""
        # 获取当前文件所在目录
        current_dir = Path(__file__).parent
        skills_dir = current_dir / "skills"
        
        if not skills_dir.exists():
            print(f"⚠️  Skills directory not found: {skills_dir}")
            return
        
        # 加载 technical-indicators skill
        tech_indicators_path = skills_dir / "technical-indicators"
        if tech_indicators_path.exists():
            try:
                asyncio.get_event_loop().run_until_complete(
                    self.skills_manager.register_skill_from_directory(str(tech_indicators_path))
                )
                print(f"✅ Loaded skill: technical-indicators")
            except Exception as e:
                print(f"❌ Failed to load technical-indicators: {e}")
        
        # 加载 trading-signals skill
        trading_signals_path = skills_dir / "trading-signals"
        if trading_signals_path.exists():
            try:
                asyncio.get_event_loop().run_until_complete(
                    self.skills_manager.register_skill_from_directory(str(trading_signals_path))
                )
                print(f"✅ Loaded skill: trading-signals")
            except Exception as e:
                print(f"❌ Failed to load trading-signals: {e}")

    def _register_tools(self):
        """注册 Agent 专用工具"""

        @self.tool(name="greet", description="问候用户")
        async def greet(name: str) -> str:
            """问候用户"""
            return f"你好，{name}! 我是 trader，加密货币交易分析专家。我可以使用 technical-indicators 和 trading-signals skills 为你提供技术分析。"

        # 使用 Skills 管理器注册工具
        @self.tool(
            name="calculate_rsi",
            description="计算相对强弱指数 (RSI) - 判断超买超卖"
        )
        async def calculate_rsi(prices: list, period: int = 14) -> dict:
            """计算 RSI - 调用 technical-indicators skill"""
            try:
                result = await self.skills_manager.execute(
                    skill_name="technical-indicators",
                    function="calculate_rsi",
                    params={"prices": prices, "period": period}
                )
                return result
            except Exception as e:
                return {"error": str(e)}

        @self.tool(
            name="calculate_macd",
            description="计算 MACD 指标 - 判断趋势和动量"
        )
        async def calculate_macd(prices: list) -> dict:
            """计算 MACD - 调用 technical-indicators skill"""
            try:
                result = await self.skills_manager.execute(
                    skill_name="technical-indicators",
                    function="calculate_macd",
                    params={"prices": prices}
                )
                return result
            except Exception as e:
                return {"error": str(e)}

        @self.tool(
            name="generate_trading_signal",
            description="生成综合交易信号 - 结合多个指标"
        )
        async def generate_trading_signal(prices: list) -> dict:
            """生成交易信号 - 调用 trading-signals skill"""
            try:
                result = await self.skills_manager.execute(
                    skill_name="trading-signals",
                    function="generate_signal",
                    params={"prices": prices}
                )
                return result
            except Exception as e:
                return {"error": str(e)}

    async def handle_request(self, user_message: str) -> dict:
        """
        处理用户请求

        Args:
            user_message: 用户消息

        Returns:
            响应字典
        """
        # LLM 会自动决定使用哪个工具
        # 工具已注册到 Agent，可以通过 function calling 调用
        return await self.handle(user_message)

    async def shutdown(self):
        """关闭 Agent"""
        print("👋 Agent shutdown complete")


async def main():
    """测试 Agent"""
    agent = TraderAgent()

    # 测试
    print("=" * 50)
    print(f"Agent: {agent.config.name}")
    print(f"描述：{agent.config.description}")
    print(f"LLM: {agent.config.llm_config.provider} / {agent.config.llm_config.model}")
    print(f"Loaded Skills: {list(agent.skills_manager._skills_registry.keys())}")
    print("=" * 50)

    # 测试对话
    result = await agent.handle_request("你好，帮我分析 BTC 的技术指标")
    print(f"\n响应：{result.get('response', 'No response')}")

    # 关闭
    await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
