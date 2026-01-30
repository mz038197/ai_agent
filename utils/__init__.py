"""
Utilities Package

提供各种工具函数和辅助类。
"""

from .skill_loader import (
    SkillLoader,
    load_skill,
    discover_skills,
    load_multiple_skills
)

__all__ = [
    "SkillLoader",
    "load_skill",
    "discover_skills",
    "load_multiple_skills"
]

# 便捷函数：加载工具
def load_skill_tools(skill_name: str, verbose: bool = True):
    """
    快捷函数：从 skill 加载工具
    
    参数:
        skill_name: skill 名称
        verbose: 是否打印信息
    
    返回:
        LangChain Tool 对象列表
    """
    loader = SkillLoader()
    return loader.load_tools(skill_name, verbose=verbose)


__all__.append("load_skill_tools")
