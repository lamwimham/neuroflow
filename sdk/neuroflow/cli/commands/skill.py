"""
NeuroFlow CLI - Skill Commands

管理 NeuroFlow Skills - 支持灵活的模板和选项控制
"""

import click
from pathlib import Path
import yaml
from datetime import datetime
import shutil


@click.group("skill", help="Skill management commands")
def skill_cmd():
    pass


@skill_cmd.command("create", help="Create a new skill")
@click.argument("skill_name")
@click.option(
    "--description", "-d",
    required=True,
    help="Skill description (triggers and capabilities)",
)
@click.option(
    "--category", "-c",
    default="general",
    type=click.Choice([
        "data-analysis",
        "code-review", 
        "documentation",
        "testing",
        "security",
        "performance",
        "general"
    ]),
    help="Skill category",
)
@click.option(
    "--output-dir", "-o",
    default="skills",
    help="Output directory",
)
@click.option(
    "--template", "-t",
    default="standard",
    type=click.Choice(["minimal", "standard", "advanced"]),
    help="Skill template type (controls SKILL.md detail level)",
)
@click.option(
    "--with-framework",
    is_flag=True,
    help="Generate FRAMEWORK.md file",
)
@click.option(
    "--with-examples",
    is_flag=True,
    help="Generate EXAMPLES.md file",
)
@click.option(
    "--with-scripts",
    is_flag=True,
    help="Create scripts directory with template files",
)
@click.option(
    "--with-resources",
    is_flag=True,
    help="Create resources directory",
)
@click.option(
    "--assign-to", "-a",
    multiple=True,
    help="Assign skill to agent(s) (can be specified multiple times)",
)
@click.option(
    "--author",
    default="Your Name",
    help="Skill author",
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Overwrite existing skill",
)
def create(
    skill_name,
    description,
    category,
    output_dir,
    template,
    with_framework,
    with_examples,
    with_scripts,
    with_resources,
    assign_to,
    author,
    force
):
    """
    创建新的 Skill
    
    \b
    示例:
        # 创建基本 skill
        neuroflow skill create my-skill -d "技能描述"
        
        # 创建完整 skill (包含所有可选文件)
        neuroflow skill create my-skill -d "描述" --with-framework --with-examples --with-scripts
        
        # 创建并分配给 agent
        neuroflow skill create my-skill -d "描述" --assign-to assistant --assign-to analyst
        
        # 使用高级模板
        neuroflow skill create my-skill -d "描述" -t advanced
    """
    skills_dir = Path(output_dir)
    skill_dir = skills_dir / skill_name
    
    if skill_dir.exists():
        if force:
            click.echo(click.style(f"⚠ Overwriting existing skill '{skill_name}'", fg="yellow"))
            shutil.rmtree(skill_dir)
        else:
            click.echo(click.style(f"Error: Skill '{skill_name}' already exists", fg="red"))
            click.echo(click.style("  Use --force to overwrite", fg="yellow"))
            return
    
    # 创建目录结构
    skill_dir.mkdir(parents=True)
    
    # 始终创建 scripts 和 resources 目录（即使为空）
    (skill_dir / "scripts").mkdir(exist_ok=True)
    (skill_dir / "resources").mkdir(exist_ok=True)
    
    # 创建 SKILL.md (必需)
    _create_skill_md(
        skill_dir, 
        skill_name, 
        description, 
        category, 
        template,
        author,
        list(assign_to)
    )
    
    # 根据选项创建额外文件
    created_files = ["SKILL.md"]
    
    if with_framework or template == "advanced":
        _create_framework_md(skill_dir)
        created_files.append("FRAMEWORK.md")
    
    if with_examples or template == "advanced":
        _create_examples_md(skill_dir)
        created_files.append("EXAMPLES.md")
    
    if with_scripts:
        _create_scripts(skill_dir)
        created_files.append("scripts/")
    
    if with_resources:
        _create_resources(skill_dir)
        created_files.append("resources/")
    
    # 显示创建结果
    click.echo(click.style(f"\n✓ Skill '{skill_name}' created successfully!", fg="green"))
    click.echo(f"  Location: {skill_dir}")
    click.echo(f"  Template: {template}")
    click.echo(f"\n📁 Created files:")
    for f in created_files:
        click.echo(f"    ✓ {f}")
    
    if assign_to:
        click.echo(f"\n🤖 Assigned to agents:")
        for agent_name in assign_to:
            click.echo(f"    ✓ {agent_name}")
    
    click.echo(f"\n📝 Next steps:")
    click.echo(f"  1. Edit {skill_dir}/SKILL.md")
    if with_framework or template == "advanced":
        click.echo(f"  2. Edit {skill_dir}/FRAMEWORK.md (optional)")
    if with_examples or template == "advanced":
        click.echo(f"  3. Edit {skill_dir}/EXAMPLES.md (optional)")
    click.echo(f"  {'  ' if not (with_framework or with_examples or template == 'advanced') else ''}4. Add scripts to {skill_dir}/scripts/")
    click.echo(f"  {'  ' if not (with_framework or with_examples or template == 'advanced') else ''}5. Validate with: neuroflow skill validate {skill_name}")


def _create_skill_md(
    skill_dir: Path, 
    name: str, 
    description: str, 
    category: str, 
    template: str,
    author: str,
    assign_to: list
):
    """创建 SKILL.md 文件"""
    
    # 根据模板类型生成不同详细程度的内容
    if template == "minimal":
        content = _generate_minimal_skill(name, description, category, author)
    elif template == "standard":
        content = _generate_standard_skill(name, description, category, author, assign_to)
    else:  # advanced
        content = _generate_advanced_skill(name, description, category, author, assign_to)
    
    (skill_dir / "SKILL.md").write_text(content)


def _generate_minimal_skill(name: str, description: str, category: str, author: str) -> str:
    """生成最小模板"""
    return f"""---
name: {name}
description: {description}
version: 1.0.0
author: {author}
category: {category}
created: {datetime.now().strftime('%Y-%m-%d')}
tags:
  - {category}
---

# {name.upper().replace('-', ' ')} SKILL

## Goal
- TODO: Define the skill's goal

## Workflow
1. TODO: Define workflow steps

## Output Format
- TODO: Define output format
"""


def _generate_standard_skill(name: str, description: str, category: str, author: str, assign_to: list) -> str:
    """生成标准模板"""
    assign_str = "\n".join([f"  - {agent}" for agent in assign_to]) if assign_to else "  - None"
    
    return f"""---
name: {name}
description: {description}
version: 1.0.0
author: {author}
category: {category}
created: {datetime.now().strftime('%Y-%m-%d')}
tags:
  - {category}
  - agent
  - workflow
trigger_words:
  - TODO: Add trigger words
assigned_agents:
{assign_str}
---

# {name.upper().replace('-', ' ')} SKILL

## Goal
TODO: Clearly define what this skill accomplishes
- Primary objective
- Secondary objectives

## Prerequisites
- TODO: List any prerequisites
- Required tools or access

## Workflow (Execute in Order)
1. **Step 1**: TODO - First step description
   - Input: What information is needed
   - Action: What to do
   - Output: Expected output

2. **Step 2**: TODO - Second step description
   - Input: What information is needed
   - Action: What to do
   - Output: Expected output

3. **Step 3**: TODO - Continue with more steps

## Quality Checklist
- [ ] TODO: Define quality criteria 1
- [ ] TODO: Define quality criteria 2
- [ ] TODO: Define quality criteria 3

## Output Format
```markdown
# [Title]

## Summary
TODO: Brief summary

## Details
TODO: Detailed output

## Recommendations
TODO: Actionable recommendations
```

## Examples
### Example 1
**Input**: TODO
**Output**: TODO

## Related Skills
- TODO: List related skills
"""


def _generate_advanced_skill(name: str, description: str, category: str, author: str, assign_to: list) -> str:
    """生成高级模板"""
    assign_str = "\n".join([f"  - {agent}" for agent in assign_to]) if assign_to else "  - None"
    
    return f"""---
name: {name}
description: {description}
version: 1.0.0
author: {author}
category: {category}
created: {datetime.now().strftime('%Y-%m-%d')}
tags:
  - {category}
  - agent
  - workflow
  - advanced
trigger_words:
  - TODO: Add trigger word 1
  - TODO: Add trigger word 2
dependencies:
  - skill: TODO (optional)
  - mcp: TODO (optional)
tools_required:
  - TODO: List required tools
context: fork  # Use fork for isolation
allowed_tools:
  - read
  - write
  - bash
assigned_agents:
{assign_str}
---

# {name.upper().replace('-', ' ')} SKILL

## Overview
TODO: High-level description of this skill's purpose and value

## Goals
### Primary Goal
TODO: Main objective

### Secondary Goals
- TODO: Secondary objective 1
- TODO: Secondary objective 2

## Prerequisites
### Knowledge Requirements
- TODO: What the agent needs to know

### Tool Requirements
- TODO: Required tools and access

### Skill Dependencies
- TODO: Other skills this depends on

## Workflow

### Phase 1: Discovery
1. **Understand the Request**
   - Parse user requirements
   - Identify key constraints
   - Clarify ambiguities (ask if needed)

2. **Gather Context**
   - Review relevant files
   - Check existing documentation
   - Identify stakeholders

### Phase 2: Analysis
3. **Analyze Requirements**
   - Break down into components
   - Identify dependencies
   - Assess complexity

4. **Develop Approach**
   - Consider multiple solutions
   - Evaluate trade-offs
   - Select optimal approach

### Phase 3: Execution
5. **Implement Solution**
   - Follow best practices
   - Document decisions
   - Test incrementally

6. **Validate Results**
   - Verify against requirements
   - Check quality criteria
   - Ensure completeness

### Phase 4: Delivery
7. **Prepare Output**
   - Format according to template
   - Include evidence and rationale
   - Add recommendations

8. **Review and Refine**
   - Self-review against checklist
   - Ensure clarity
   - Polish presentation

## Quality Standards

### Code Quality (if applicable)
- [ ] Follows style guide
- [ ] Includes tests
- [ ] Documented
- [ ] No security issues

### Documentation Quality
- [ ] Clear and concise
- [ ] Includes examples
- [ ] Up-to-date
- [ ] Properly structured

### Analysis Quality
- [ ] Evidence-based conclusions
- [ ] Multiple perspectives considered
- [ ] Risks identified
- [ ] Recommendations actionable

## Output Template

```markdown
# [Title]

## Executive Summary
<2-3 sentence overview>

## Context
<Relevant background information>

## Analysis
<Detailed analysis with evidence>

## Findings
### Key Finding 1
- Description
- Evidence
- Impact

### Key Finding 2
- Description
- Evidence
- Impact

## Recommendations
### Immediate Actions
1. [Action 1] - [Timeline]
2. [Action 2] - [Timeline]

### Long-term Improvements
1. [Improvement 1]
2. [Improvement 2]

## Next Steps
- [ ] TODO: Immediate next action
- [ ] TODO: Follow-up items

## Appendix
### Evidence
- [Source 1](link)
- [Source 2](link)

### Methodology
<Brief description of approach>
```

## Error Handling
### Common Issues
1. **Issue**: TODO
   **Solution**: TODO

2. **Issue**: TODO
   **Solution**: TODO

### Escalation
When to escalate:
- TODO: Condition 1
- TODO: Condition 2

## Examples

### Example 1: Basic Usage
**User Request**: TODO
**Execution**: TODO
**Output**: TODO

### Example 2: Advanced Usage
**User Request**: TODO
**Execution**: TODO
**Output**: TODO

## Related Skills
- [[Related Skill 1]] - Brief description
- [[Related Skill 2]] - Brief description

## Changelog
- 1.0.0 (TODO) - Initial version
"""


def _create_framework_md(skill_dir: Path):
    """创建 FRAMEWORK.md 文件"""
    content = f"""# {skill_dir.name.upper()} Framework

Detailed framework and methodology for this skill.

## Background
TODO: Provide background information

## Methodology
TODO: Describe the methodology

### Step 1: Overview
TODO: Describe step 1

### Step 2: Details
TODO: Describe step 2

## Best Practices
TODO: List best practices

1. **Practice 1**: Description
2. **Practice 2**: Description
3. **Practice 3**: Description

## References
- TODO: Add references
- [Link 1](url)
- [Link 2](url)

## Tools and Resources
- TODO: List tools and resources
"""
    (skill_dir / "FRAMEWORK.md").write_text(content)


def _create_examples_md(skill_dir: Path):
    """创建 EXAMPLES.md 文件"""
    content = f"""# {skill_dir.name.upper()} Examples

Real-world examples of this skill in action.

## Example 1
### Context
TODO: Describe the situation

### Input
```
TODO: Show input
```

### Execution
TODO: Describe what was done

### Output
```
TODO: Show output
```

### Lessons Learned
TODO: What worked well, what didn't

## Example 2
### Context
TODO: Describe the situation

### Input
```
TODO: Show input
```

### Execution
TODO: Describe what was done

### Output
```
TODO: Show output
```

### Lessons Learned
TODO: What worked well, what didn't

## Example 3: Edge Case
### Context
TODO: Describe the edge case

### Handling
TODO: Describe how it was handled
"""
    (skill_dir / "EXAMPLES.md").write_text(content)


def _create_scripts(skill_dir: Path):
    """创建 scripts 目录和模板文件"""
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    
    # 创建 Python 脚本模板
    script_template = """#!/usr/bin/env python3
\"\"\"
TODO: Script description
\"\"\"

import sys
import json


def main():
    \"\"\"Main function\"\"\"
    # TODO: Implement script logic
    pass


if __name__ == "__main__":
    main()
"""
    (scripts_dir / "process.py").write_text(script_template)
    (scripts_dir / "process.py").chmod(0o755)
    
    # 创建 Bash 脚本模板
    bash_template = """#!/bin/bash
# TODO: Script description

set -e

# TODO: Implement script logic
echo "TODO: Add your commands here"
"""
    (scripts_dir / "process.sh").write_text(bash_template)
    (scripts_dir / "process.sh").chmod(0o755)


def _create_resources(skill_dir: Path):
    """创建 resources 目录"""
    resources_dir = skill_dir / "resources"
    resources_dir.mkdir(exist_ok=True)
    
    # 创建 .gitkeep 文件
    (resources_dir / ".gitkeep").touch()


@skill_cmd.command("list", help="List all skills")
@click.option(
    "--category", "-c",
    default=None,
    help="Filter by category",
)
@click.option(
    "--output-dir", "-o",
    default="skills",
    help="Skills directory",
)
@click.option(
    "--format", "-f",
    default="table",
    type=click.Choice(["table", "json", "simple"]),
    help="Output format",
)
def list_skills(category, output_dir, format):
    """列出所有 Skills"""
    skills_dir = Path(output_dir)
    
    if not skills_dir.exists():
        click.echo("No skills directory found")
        return
    
    # 查找所有 SKILL.md 文件
    skill_files = list(skills_dir.glob("*/SKILL.md"))
    
    if not skill_files:
        click.echo("No skills found")
        return
    
    skills = []
    for skill_file in skill_files:
        try:
            content = skill_file.read_text()
            # 解析 YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 2:
                    metadata = yaml.safe_load(parts[1])
                    if category is None or metadata.get('category') == category:
                        skills.append({
                            'name': metadata.get('name', skill_file.parent.name),
                            'description': metadata.get('description', 'No description'),
                            'category': metadata.get('category', 'general'),
                            'version': metadata.get('version', '1.0.0'),
                            'author': metadata.get('author', 'Unknown'),
                            'assigned_agents': metadata.get('assigned_agents', []),
                        })
        except Exception as e:
            click.echo(click.style(f"Error reading {skill_file}: {e}", fg="yellow"))
    
    if not skills:
        click.echo("No skills found" + (f" in category '{category}'" if category else ""))
        return
    
    # 显示列表
    if format == "json":
        click.echo(json.dumps(skills, indent=2))
    elif format == "simple":
        click.echo(f"\nFound {len(skills)} skill(s)" + (f" in category '{category}'" if category else "") + ":\n")
        for skill in sorted(skills, key=lambda x: x['name']):
            click.echo(f"  • {skill['name']} ({skill['category']}) - {skill['description'][:50]}...")
    else:  # table
        click.echo(f"\nFound {len(skills)} skill(s)" + (f" in category '{category}'" if category else "") + ":\n")
        click.echo(f"{'Name':<25} {'Category':<18} {'Version':<10} {'Author':<15} Description")
        click.echo("─" * 90)
        
        for skill in sorted(skills, key=lambda x: x['category']):
            desc = skill['description'][:35] + "..." if len(skill['description']) > 35 else skill['description']
            author = skill['author'][:13] + "..." if len(skill['author']) > 15 else skill['author']
            click.echo(f"{skill['name']:<25} {skill['category']:<18} {skill['version']:<10} {author:<15} {desc}")
        
        click.echo()


@skill_cmd.command("show", help="Show skill details")
@click.argument("skill_name")
@click.option(
    "--output-dir", "-o",
    default="skills",
    help="Skills directory",
)
def show_skill(skill_name, output_dir):
    """显示 Skill 详情"""
    skills_dir = Path(output_dir)
    skill_file = skills_dir / skill_name / "SKILL.md"
    
    if not skill_file.exists():
        click.echo(click.style(f"Error: Skill '{skill_name}' not found", fg="red"))
        return
    
    content = skill_file.read_text()
    
    # 解析 YAML frontmatter
    metadata = {}
    body = content
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 2:
            metadata = yaml.safe_load(parts[1])
            body = parts[2] if len(parts) > 2 else ""
    
    # 显示详情
    click.echo(f"\n{'='*70}")
    click.echo(f"Skill: {metadata.get('name', skill_name)}")
    click.echo(f"{'='*70}\n")
    
    click.echo(f"Category:    {metadata.get('category', 'N/A')}")
    click.echo(f"Version:     {metadata.get('version', 'N/A')}")
    click.echo(f"Author:      {metadata.get('author', 'N/A')}")
    click.echo(f"Created:     {metadata.get('created', 'N/A')}")
    
    if metadata.get('assigned_agents'):
        click.echo(f"\nAssigned Agents:")
        for agent in metadata.get('assigned_agents', []):
            click.echo(f"  • {agent}")
    
    click.echo(f"\nDescription:")
    desc = metadata.get('description', 'N/A')
    # 自动换行
    import textwrap
    for line in textwrap.wrap(desc, width=68):
        click.echo(f"  {line}")
    
    if metadata.get('trigger_words'):
        click.echo(f"\nTrigger Words:")
        for word in metadata.get('trigger_words', []):
            click.echo(f"  • {word}")
    
    if metadata.get('tags'):
        click.echo(f"\nTags:")
        for tag in metadata.get('tags', []):
            click.echo(f"  • {tag}")
    
    # 显示目录结构
    skill_dir = skill_file.parent
    click.echo(f"\n📁 Files:")
    try:
        for file in sorted(skill_dir.rglob("*")):
            if file.is_file() and file.name != ".gitkeep":
                try:
                    rel_path = file.relative_to(skill_dir)
                    size = file.stat().st_size
                    click.echo(f"  {rel_path:<35} ({size:,} bytes)")
                except Exception:
                    pass
    except Exception:
        pass

    click.echo()


@skill_cmd.command("validate", help="Validate a skill")
@click.argument("skill_name")
@click.option(
    "--output-dir", "-o",
    default="skills",
    help="Skills directory",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Enable strict validation (warnings become errors)",
)
def validate_skill(skill_name, output_dir, strict):
    """验证 Skill"""
    skills_dir = Path(output_dir)
    skill_file = skills_dir / skill_name / "SKILL.md"
    
    if not skill_file.exists():
        click.echo(click.style(f"✗ Skill '{skill_name}' not found", fg="red"))
        return False
    
    click.echo(f"Validating skill: {skill_name}\n")
    
    errors = []
    warnings = []
    
    # 读取内容
    content = skill_file.read_text()
    
    # 检查 YAML frontmatter
    if not content.startswith('---'):
        errors.append("Missing YAML frontmatter (must start with '---')")
    else:
        parts = content.split('---', 2)
        if len(parts) < 2:
            errors.append("Invalid YAML frontmatter")
        else:
            try:
                metadata = yaml.safe_load(parts[1])
                
                # 检查必需字段
                required_fields = ['name', 'description']
                for field in required_fields:
                    if field not in metadata:
                        errors.append(f"Missing required field: {field}")
                
                # 检查可选字段
                optional_fields = ['version', 'author', 'category', 'tags', 'trigger_words']
                for field in optional_fields:
                    if field not in metadata:
                        warnings.append(f"Missing recommended field: {field}")
                
                # 验证 name 匹配
                if metadata.get('name') != skill_name:
                    warnings.append(f"Skill name '{metadata.get('name')}' doesn't match directory '{skill_name}'")
                
                # 检查 description 是否包含触发词
                desc = metadata.get('description', '')
                if '触发词' not in desc and 'trigger' not in desc.lower():
                    warnings.append("Description should include trigger words")
                
            except yaml.YAMLError as e:
                errors.append(f"Invalid YAML: {e}")
    
    # 检查文件结构
    skill_dir = skill_file.parent
    
    # 检查可选文件
    optional_files = {
        'FRAMEWORK.md': 'Framework documentation',
        'EXAMPLES.md': 'Usage examples',
    }
    
    for file, desc in optional_files.items():
        if not (skill_dir / file).exists():
            warnings.append(f"Missing optional file: {file} ({desc})")
    
    # 检查 scripts 目录
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists():
        scripts = list(scripts_dir.glob("*.py")) + list(scripts_dir.glob("*.sh"))
        if not scripts:
            warnings.append("scripts directory is empty")
    
    # 检查内容长度
    line_count = len(content.split('\n'))
    if line_count > 500:
        warnings.append(f"SKILL.md is {line_count} lines (recommended ≤500) - consider splitting into sub-files")
    elif line_count < 20:
        warnings.append(f"SKILL.md is only {line_count} lines - may need more detail")
    
    # 显示结果
    def show_issues(title, issues, icon, color):
        if issues:
            click.echo(click.style(f"{title}:", fg=color))
            for issue in issues:
                click.echo(click.style(f"  {icon} {issue}", fg=color))
            click.echo()
    
    show_issues("Errors", errors, "✗", "red")
    show_issues("Warnings", warnings, "⚠", "yellow")
    
    if strict:
        all_issues = errors + warnings
    else:
        all_issues = errors
    
    if not all_issues:
        click.echo(click.style("✓ Skill is valid!", fg="green"))
        return True
    elif not errors:
        click.echo(click.style(f"✓ Skill is valid (with {len(warnings)} warning(s))", fg="green"))
        return True
    else:
        click.echo(click.style(f"✗ Skill has {len(errors)} error(s)", fg="red"))
        return False


@skill_cmd.command("assign", help="Assign skill to agent")
@click.argument("skill_name")
@click.argument("agent_name")
@click.option(
    "--output-dir", "-o",
    default="skills",
    help="Skills directory",
)
@click.option(
    "--remove", "-r",
    is_flag=True,
    help="Remove assignment instead of adding",
)
def assign_skill(skill_name, agent_name, output_dir, remove):
    """分配 Skill 到 Agent"""
    skills_dir = Path(output_dir)
    skill_file = skills_dir / skill_name / "SKILL.md"
    
    if not skill_file.exists():
        click.echo(click.style(f"Error: Skill '{skill_name}' not found", fg="red"))
        return
    
    content = skill_file.read_text()
    
    # 解析 YAML frontmatter
    if not content.startswith('---'):
        click.echo(click.style("Error: Invalid SKILL.md format", fg="red"))
        return
    
    parts = content.split('---', 2)
    if len(parts) < 2:
        click.echo(click.style("Error: Invalid SKILL.md format", fg="red"))
        return
    
    try:
        metadata = yaml.safe_load(parts[1])
        body = parts[2] if len(parts) > 2 else ""
        
        # 获取当前分配
        assigned = metadata.get('assigned_agents', [])
        if not assigned:
            assigned = []
        
        if remove:
            if agent_name in assigned:
                assigned.remove(agent_name)
                click.echo(f"✓ Removed assignment to agent '{agent_name}'")
            else:
                click.echo(f"Skill was not assigned to agent '{agent_name}'")
                return
        else:
            if agent_name in assigned:
                click.echo(f"Skill already assigned to agent '{agent_name}'")
                return
            assigned.append(agent_name)
            click.echo(f"✓ Assigned skill to agent '{agent_name}'")
        
        # 重建 YAML frontmatter
        metadata['assigned_agents'] = assigned
        
        # 写回文件
        new_content = "---\n" + yaml.dump(metadata, allow_unicode=True, default_flow_style=False) + "---\n" + body
        skill_file.write_text(new_content)
        
        if assigned:
            click.echo(f"\nCurrent assignments: {', '.join(assigned)}")
        
    except yaml.YAMLError as e:
        click.echo(click.style(f"Error parsing YAML: {e}", fg="red"))


__all__ = ["skill_cmd"]
