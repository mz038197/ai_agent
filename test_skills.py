"""
测试 Skills 加载功能

这个脚本用于测试 skill 加载和管理功能。
"""

import sys
import io

# UTF-8 编码设置
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from utils import SkillLoader, load_skill, discover_skills


def test_discover_skills():
    """测试 skill 发现功能"""
    print("=" * 70)
    print("测试 1: 发现所有 skills")
    print("=" * 70)
    
    skills = discover_skills()
    print(f"\n发现 {len(skills)} 个 skills:")
    for skill in skills:
        print(f"  ✅ {skill}")
    
    return len(skills) > 0


def test_load_skill():
    """测试加载单个 skill"""
    print("\n" + "=" * 70)
    print("测试 2: 加载 google-sheets skill")
    print("=" * 70 + "\n")
    
    content = load_skill("google-sheets")
    
    if content:
        print(f"✅ 成功加载，内容长度: {len(content)} 字符")
        print(f"\n前 200 个字符预览:")
        print("-" * 70)
        print(content[:200] + "...")
        return True
    else:
        print("❌ 加载失败")
        return False


def test_skill_loader_class():
    """测试 SkillLoader 类"""
    print("\n" + "=" * 70)
    print("测试 3: 使用 SkillLoader 类")
    print("=" * 70 + "\n")
    
    loader = SkillLoader()
    
    # 测试 discover
    print("📚 发现 skills:")
    skills = loader.discover()
    for skill in skills:
        print(f"  - {skill}")
    
    # 测试 get_info
    print("\n📖 获取 skill 信息:")
    for skill in skills:
        info = loader.get_info(skill)
        if info:
            print(f"\nSkill: {info['name']}")
            print(f"  标题: {info['title']}")
            print(f"  描述: {info['description'][:80]}..." if info['description'] else "  描述: (无)")
            print(f"  路径: {info['path']}")
            print(f"  大小: {info['size']} 字符")
    
    # 测试 list_all
    print("\n📋 列出所有 skills 信息:")
    all_skills = loader.list_all()
    for info in all_skills:
        print(f"  - {info['name']}: {info['title']}")
    
    return len(all_skills) > 0


def test_load_multiple_skills():
    """测试加载多个 skills"""
    print("\n" + "=" * 70)
    print("测试 4: 加载多个 skills")
    print("=" * 70 + "\n")
    
    loader = SkillLoader()
    skills = loader.discover()
    
    if len(skills) >= 1:
        # 加载所有发现的 skills
        content = loader.load_multiple(skills[:2] if len(skills) >= 2 else skills)
        print(f"✅ 成功组合 {min(2, len(skills))} 个 skills")
        print(f"总长度: {len(content)} 字符")
        
        # 显示前几行
        lines = content.split("\n")[:10]
        print(f"\n前 10 行预览:")
        print("-" * 70)
        for line in lines:
            print(line)
        
        return True
    else:
        print("⚠️  没有足够的 skills 进行测试")
        return False


def test_skill_in_prompt():
    """测试在 system prompt 中使用 skill"""
    print("\n" + "=" * 70)
    print("测试 5: 构建包含 skill 的 system prompt")
    print("=" * 70 + "\n")
    
    skill = load_skill("google-sheets", verbose=False)
    
    system_prompt = f"""你是一个专业的 Google Sheets 助手。

{skill}

请根据以上指导完成任务。
"""
    
    print("✅ System Prompt 构建成功")
    print(f"总长度: {len(system_prompt)} 字符")
    print(f"\n前 300 个字符:")
    print("-" * 70)
    print(system_prompt[:300] + "...")
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "🎯" * 35)
    print("Skills 系统测试")
    print("🎯" * 35 + "\n")
    
    results = []
    
    # 运行所有测试
    results.append(("发现 skills", test_discover_skills()))
    results.append(("加载单个 skill", test_load_skill()))
    results.append(("SkillLoader 类", test_skill_loader_class()))
    results.append(("加载多个 skills", test_load_multiple_skills()))
    results.append(("Skill 在 prompt 中", test_skill_in_prompt()))
    
    # 显示测试结果
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70 + "\n")
    
    passed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}  {name}")
        if result:
            passed += 1
    
    print("\n" + "-" * 70)
    print(f"总计: {passed}/{len(results)} 个测试通过")
    print("=" * 70 + "\n")
    
    if passed == len(results):
        print("🎉 所有测试通过！Skills 系统工作正常。")
    else:
        print("⚠️  部分测试失败，请检查 skills 目录和文件。")


if __name__ == "__main__":
    main()
