"""
Skill Loader Utility

提供加载和管理 skill 文件的工具函数。
Skills 是存储在 ./skills/ 目录下的 SKILL.md 文件，用于指导 AI Agent 的行为。
同时支持加载 skill 中定义的工具函数。
"""

import sys
import importlib.util
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
from langchain_core.tools import Tool, StructuredTool
from pydantic import BaseModel, Field
import inspect


class SkillLoader:
    """Skill 加载器"""
    
    def __init__(self, skills_dir: str = "./skills"):
        """
        初始化 Skill Loader
        
        参数:
            skills_dir: skills 目录路径
        """
        self.skills_dir = Path(skills_dir)
        
    def discover(self) -> List[str]:
        """
        发现所有可用的 skills
        
        返回:
            skill 名称列表
        """
        if not self.skills_dir.exists():
            return []
        
        skills = [
            d.name for d in self.skills_dir.iterdir() 
            if d.is_dir() and (d / "SKILL.md").exists()
        ]
        return sorted(skills)
    
    def load(self, skill_name: str, verbose: bool = True) -> str:
        """
        加载指定的 skill
        
        参数:
            skill_name: skill 名称
            verbose: 是否打印加载信息
        
        返回:
            skill 内容，如果不存在则返回空字符串
        """
        skill_path = self.skills_dir / skill_name / "SKILL.md"
        
        if skill_path.exists():
            if verbose:
                print(f"✅ 成功加载 skill: {skill_name}")
            return skill_path.read_text(encoding="utf-8")
        else:
            if verbose:
                print(f"⚠️  Skill 文件不存在: {skill_path}")
            return ""
    
    def load_multiple(self, skill_names: List[str], separator: str = "\n\n") -> str:
        """
        加载多个 skills 并组合
        
        参数:
            skill_names: skill 名称列表
            separator: skills 之间的分隔符
        
        返回:
            组合后的 skills 内容
        """
        skills_content = []
        
        for skill_name in skill_names:
            content = self.load(skill_name, verbose=False)
            if content:
                skills_content.append(f"# Skill: {skill_name}\n\n{content}")
        
        return separator.join(skills_content) if skills_content else ""
    
    def get_info(self, skill_name: str) -> Optional[Dict[str, str]]:
        """
        获取 skill 的基本信息
        
        参数:
            skill_name: skill 名称
        
        返回:
            包含 skill 信息的字典，如果不存在则返回 None
        """
        skill_path = self.skills_dir / skill_name / "SKILL.md"
        
        if not skill_path.exists():
            return None
        
        content = skill_path.read_text(encoding="utf-8")
        
        # 提取第一行作为标题
        lines = content.split("\n")
        title = lines[0].strip("# ").strip() if lines else skill_name
        
        # 尝试提取描述（通常在 ## 描述 后面）
        description = ""
        for i, line in enumerate(lines):
            if "## 描述" in line or "## Description" in line:
                # 获取下一个非空行作为描述
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() and not lines[j].startswith("#"):
                        description = lines[j].strip()
                        break
                break
        
        return {
            "name": skill_name,
            "title": title,
            "description": description,
            "path": str(skill_path),
            "size": len(content)
        }
    
    def list_all(self) -> List[Dict[str, str]]:
        """
        列出所有 skills 的信息
        
        返回:
            包含所有 skills 信息的列表
        """
        skills = self.discover()
        return [info for skill in skills if (info := self.get_info(skill))]
    
    def get_metadata(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """
        获取 skill 的 metadata（从 YAML front matter）
        
        参数:
            skill_name: skill 名称
        
        返回:
            metadata 字典，如果没有则返回 None
        """
        skill_path = self.skills_dir / skill_name / "SKILL.md"
        
        if not skill_path.exists():
            return None
        
        content = skill_path.read_text(encoding="utf-8")
        
        # 检查是否有 YAML front matter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    import yaml
                    metadata = yaml.safe_load(parts[1])
                    return metadata
                except:
                    pass
        
        # 如果没有 YAML，返回基本信息
        return self.get_info(skill_name)
    
    def load_tools(self, skill_name: str, verbose: bool = True) -> List[Tool]:
        """
        从 skill 中加载工具函数并转换为 LangChain Tools
        
        参数:
            skill_name: skill 名称
            verbose: 是否打印加载信息
        
        返回:
            LangChain Tool 对象列表
        """
        metadata = self.get_metadata(skill_name)
        
        if not metadata or 'tools_file' not in metadata:
            if verbose:
                print(f"⚠️  Skill '{skill_name}' 没有定义 tools_file")
            return []
        
        tools_file = metadata['tools_file']
        tools_path = self.skills_dir / skill_name / tools_file
        
        if not tools_path.exists():
            if verbose:
                print(f"⚠️  工具文件不存在: {tools_path}")
            return []
        
        # 动态导入模块
        try:
            spec = importlib.util.spec_from_file_location(
                f"skills.{skill_name}.tools", 
                tools_path
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # 获取要导出的工具列表
            tool_names = metadata.get('tools', [])
            if not tool_names:
                # 如果 metadata 中没有指定，尝试从模块的 __all__ 获取
                tool_names = getattr(module, '__all__', [])
            
            # 转换为 LangChain Tools
            tools = []
            for tool_name in tool_names:
                if hasattr(module, tool_name):
                    func = getattr(module, tool_name)
                    if callable(func):
                        # 检查函数参数数量
                        sig = inspect.signature(func)
                        params = [p for p in sig.parameters.values() 
                                 if p.kind not in (inspect.Parameter.VAR_POSITIONAL, 
                                                  inspect.Parameter.VAR_KEYWORD)]
                        
                        # 如果只有一个参数，使用 Tool；否则使用 StructuredTool
                        if len(params) <= 1:
                            tool = Tool(
                                name=tool_name,
                                func=func,
                                description=func.__doc__ or f"{tool_name} from {skill_name}"
                            )
                        else:
                            # 使用 StructuredTool 支持多参数
                            tool = StructuredTool.from_function(
                                func=func,
                                name=tool_name,
                                description=func.__doc__ or f"{tool_name} from {skill_name}"
                            )
                        tools.append(tool)
            
            if verbose:
                print(f"✅ 从 '{skill_name}' 加载了 {len(tools)} 个工具")
            
            return tools
            
        except Exception as e:
            if verbose:
                print(f"❌ 加载工具失败: {e}")
            return []
    
    def load_all_tools(self, skill_names: Optional[List[str]] = None, verbose: bool = True) -> List[Tool]:
        """
        从多个 skills 加载所有工具
        
        参数:
            skill_names: skill 名称列表，如果为 None 则加载所有 skills
            verbose: 是否打印加载信息
        
        返回:
            所有 LangChain Tool 对象列表
        """
        if skill_names is None:
            skill_names = self.discover()
        
        all_tools = []
        for skill_name in skill_names:
            tools = self.load_tools(skill_name, verbose=verbose)
            all_tools.extend(tools)
        
        return all_tools


# 便捷函数
def load_skill(skill_name: str, skills_dir: str = "./skills", verbose: bool = True) -> str:
    """
    快捷函数：加载单个 skill
    
    参数:
        skill_name: skill 名称
        skills_dir: skills 目录路径
        verbose: 是否打印信息
    
    返回:
        skill 内容
    """
    loader = SkillLoader(skills_dir)
    return loader.load(skill_name, verbose=verbose)


def discover_skills(skills_dir: str = "./skills") -> List[str]:
    """
    快捷函数：发现所有可用的 skills
    
    参数:
        skills_dir: skills 目录路径
    
    返回:
        skill 名称列表
    """
    loader = SkillLoader(skills_dir)
    return loader.discover()


def load_multiple_skills(skill_names: List[str], skills_dir: str = "./skills") -> str:
    """
    快捷函数：加载多个 skills
    
    参数:
        skill_names: skill 名称列表
        skills_dir: skills 目录路径
    
    返回:
        组合后的 skills 内容
    """
    loader = SkillLoader(skills_dir)
    return loader.load_multiple(skill_names)
