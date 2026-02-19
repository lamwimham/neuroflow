"""
NeuroFlow Skills路由系统
实现基于语义和关键词的技能路由功能
"""
import asyncio
import re
from typing import List, Dict, Any, Optional
from .skills import skills_manager
from .context import get_context


class SkillRouter:
    """
    Skills路由系统
    支持语义匹配、关键词触发和LLM决策
    """
    
    def __init__(self):
        self.context_keywords = {
            "pdf": ["pdf", "form", "fill", "document", "acrobat"],
            "math": ["calculate", "compute", "math", "formula", "equation"],
            "text": ["analyze", "process", "text", "content", "document"],
            "web": ["search", "browse", "web", "url", "internet"],
            "data": ["data", "csv", "excel", "database", "analyze"]
        }
    
    async def route_to_skills(self, user_intent: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        根据用户意图路由到最相关的技能
        """
        # 1. 关键词初筛
        keyword_candidates = await self._keyword_filter(user_intent)
        
        # 2. 语义精排
        semantic_matches = await self._semantic_rank(user_intent, keyword_candidates)
        
        # 3. 上下文增强
        contextual_skills = await self._apply_context_filter(semantic_matches, context)
        
        return contextual_skills
    
    async def _keyword_filter(self, user_intent: str) -> List[str]:
        """
        基于关键词的初步筛选
        """
        intent_lower = user_intent.lower()
        matched_categories = []
        
        # 检查每个类别对应的关键词
        for category, keywords in self.context_keywords.items():
            for keyword in keywords:
                if keyword in intent_lower:
                    matched_categories.append(category)
                    break
        
        # 获取匹配类别的技能
        all_skills = skills_manager.list_available_skills()
        candidates = []
        
        for skill_name in all_skills:
            try:
                metadata = skills_manager.get_skill_metadata(skill_name)
                
                # 检查技能的triggers字段（如果存在）
                if 'triggers' in metadata:
                    for trigger in metadata['triggers']:
                        if trigger.lower() in intent_lower:
                            candidates.append(skill_name)
                            break
                
                # 检查技能标签
                for tag in metadata.get('tags', []):
                    if tag.lower() in matched_categories or tag.lower() in intent_lower:
                        candidates.append(skill_name)
                        break
                
                # 检查技能描述
                if any(keyword in metadata.get('description', '').lower() for keyword in intent_lower.split()):
                    if skill_name not in candidates:
                        candidates.append(skill_name)
                        
            except Exception as e:
                print(f"Error checking skill {skill_name}: {e}")
                continue
        
        return list(set(candidates))  # 去重
    
    async def _semantic_rank(self, user_intent: str, candidates: List[str]) -> List[Dict[str, Any]]:
        """
        基于语义相似度的精排
        """
        ranked_skills = []
        
        for skill_name in candidates:
            try:
                metadata = skills_manager.get_skill_metadata(skill_name)
                
                # 计算语义相关性得分
                relevance_score = self._calculate_relevance_score(user_intent, metadata)
                
                ranked_skills.append({
                    'skill_name': skill_name,
                    'metadata': metadata,
                    'relevance_score': relevance_score
                })
                
            except Exception as e:
                print(f"Error ranking skill {skill_name}: {e}")
                continue
        
        # 按相关性得分排序
        ranked_skills.sort(key=lambda x: x['relevance_score'], reverse=True)
        return ranked_skills
    
    def _calculate_relevance_score(self, user_intent: str, skill_metadata: Dict[str, Any]) -> float:
        """
        计算用户意图与技能的相关性得分
        """
        score = 0.0
        intent_lower = user_intent.lower()
        
        # 匹配技能名称 (权重: 0.3)
        skill_name_lower = skill_metadata['name'].lower()
        if skill_name_lower in intent_lower:
            score += 0.3
        elif any(word in intent_lower for word in skill_name_lower.split('_')):
            score += 0.15
        
        # 匹配技能描述 (权重: 0.4)
        description_lower = skill_metadata['description'].lower()
        if any(word in description_lower for word in intent_lower.split()):
            score += 0.4
        elif any(word in intent_lower for word in description_lower.split()):
            score += 0.2
        
        # 匹配触发词 (权重: 0.2)
        if 'triggers' in skill_metadata:
            for trigger in skill_metadata['triggers']:
                if trigger.lower() in intent_lower:
                    score += 0.2
                    break
        
        # 匹配标签 (权重: 0.1)
        for tag in skill_metadata.get('tags', []):
            if tag.lower() in intent_lower:
                score += 0.1
                break
        
        return min(score, 1.0)  # 限制在0-1范围内
    
    async def _apply_context_filter(self, ranked_skills: List[Dict[str, Any]], 
                                   context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        应用上下文过滤
        """
        if not context:
            return ranked_skills[:5]  # 返回前5个
        
        # 根据上下文调整排名
        adjusted_skills = []
        for skill_info in ranked_skills:
            # 检查上下文中的限制条件
            if await self._check_contextual_constraints(skill_info['skill_name'], context):
                adjusted_skills.append(skill_info)
        
        return adjusted_skills[:5]  # 返回前5个符合条件的
    
    async def _check_contextual_constraints(self, skill_name: str, context: Dict[str, Any]) -> bool:
        """
        检查技能是否符合上下文约束
        """
        # 检查权限
        if 'permissions' in context:
            required_permission = f"skill:{skill_name}"
            if required_permission not in context['permissions']:
                return False
        
        # 检查资源可用性
        if 'resources' in context:
            # 检查技能所需的资源是否可用
            metadata = skills_manager.get_skill_metadata(skill_name)
            # 这里可以根据具体需求实现资源检查逻辑
            
        return True
    
    async def get_top_skills(self, user_intent: str, limit: int = 3) -> List[str]:
        """
        获取最相关的技能列表
        """
        routed_skills = await self.route_to_skills(user_intent)
        return [skill['skill_name'] for skill in routed_skills[:limit]]
    
    async def select_best_skill(self, user_intent: str, context: Dict[str, Any] = None) -> Optional[str]:
        """
        选择最适合的技能
        """
        routed_skills = await self.route_to_skills(user_intent, context)
        if routed_skills:
            # 选择相关性得分最高的技能
            best_skill = max(routed_skills, key=lambda x: x['relevance_score'])
            return best_skill['skill_name']
        return None


# 全局技能路由器实例
skill_router = SkillRouter()


# 使用示例
async def example_usage():
    """
    技能路由使用示例
    """
    # 示例1: PDF表单填写
    user_intent1 = "I need to fill out this PDF form with my personal information"
    top_skills1 = await skill_router.get_top_skills(user_intent1)
    print(f"Top skills for '{user_intent1}': {top_skills1}")
    
    # 示例2: 数学计算
    user_intent2 = "Calculate the monthly payment for a loan"
    top_skills2 = await skill_router.get_top_skills(user_intent2)
    print(f"Top skills for '{user_intent2}': {top_skills2}")
    
    # 示例3: 文本分析
    user_intent3 = "Analyze the sentiment of this customer review"
    top_skills3 = await skill_router.get_top_skills(user_intent3)
    print(f"Top skills for '{user_intent3}': {top_skills3}")


if __name__ == "__main__":
    asyncio.run(example_usage())