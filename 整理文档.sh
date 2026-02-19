#!/bin/bash

# NeuroFlow 根目录 MD 文件整理脚本
# 将根目录下的文档文件移动到 docs 目录

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "📂 NeuroFlow 文档整理脚本"
echo "================================"
echo ""

# 进入项目根目录
cd /Users/lianwenhua/indie/NeuroFlow

# 定义需要移动的文件（保留 README.md）
files_to_move=(
    "ARCHITECTURE_REVIEW.md"
    "DEVELOPER_FEEDBACK_SURVEY.md"
    "ENHANCED_FEATURES.md"
    "ITERATION_PLAN.md"
    "ITERATION_SUMMARY.md"
    "MCP_CORE_INTEGRATION_PLAN.md"
    "MCP_INTEGRATION_SUMMARY.md"
    "MILESTONE1_COMPLETION_REPORT.md"
    "NEXT_STEPS.md"
    "PHASE1_PROGRESS_REPORT.md"
    "PHASE2_DEVELOPMENT_PLAN.md"
    "PHASE2_KICKOFF.md"
    "QUICKSTART.md"
    "SKILLS_INTEGRATION_PLAN.md"
    "SKILLS_USER_MANUAL.md"
    "SKILL_LEARNING_FEATURES.md"
    "SUMMARY.md"
    "DOCUMENTATION_COMPLETION_REPORT.md"
)

# 统计
moved_count=0
skipped_count=0

echo "开始移动文件..."
echo ""

for file in "${files_to_move[@]}"; do
    if [ -f "$file" ]; then
        # 确定目标目录
        case "$file" in
            *ARCHITECTURE*)
                target_dir="docs/architecture"
                ;;
            *PLAN*|*NEXT_STEPS*)
                target_dir="docs/plans"
                ;;
            *SUMMARY*|*REPORT*|*KICKOFF*|*PROGRESS*)
                target_dir="docs/reports"
                ;;
            *QUICKSTART*|*MANUAL*)
                target_dir="docs/guides"
                ;;
            *)
                target_dir="docs/project-info"
                ;;
        esac
        
        # 移动文件
        mv "$file" "$target_dir/"
        echo -e "${GREEN}✓${NC} 移动 $file → $target_dir/"
        ((moved_count++))
    else
        echo -e "${YELLOW}⚠${NC} 跳过（文件不存在）: $file"
        ((skipped_count++))
    fi
done

echo ""
echo "================================"
echo -e "${GREEN}✓ 整理完成！${NC}"
echo "  移动文件数：$moved_count"
echo "  跳过文件数：$skipped_count"
echo ""
echo "📂 文档目录结构:"
echo "  docs/"
echo "  ├── project-info/     # 项目信息"
echo "  ├── architecture/     # 架构设计"
echo "  ├── plans/           # 计划文档"
echo "  ├── reports/         # 报告文档"
echo "  └── guides/          # 指南文档"
echo ""
echo "📖 查看文档索引：docs/README.md"
echo ""
