#!/bin/bash

# ==========================================
# AWS 環境配置管理器
# ==========================================
# 用法:
#   ./config_manager.sh list                     列出所有環境配置
#   ./config_manager.sh show [STAGE]             顯示特定環境配置
#   ./config_manager.sh set [STAGE] [KEY] [VALUE] 設置參數
#   ./config_manager.sh init [STAGE]             初始化環境
#   ./config_manager.sh create [STAGE]           創建新環境配置
#   ./config_manager.sh delete [STAGE]           刪除環境配置
#
# ==========================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_section() {
    echo ""
    echo "=========================================="
    echo "  $1"
    echo "=========================================="
}

# 默認配置
DEFAULT_PARAMS=(
    "google-genai-api-key"
    "gemini-api-key"
    "tavily-api-key"
)

DEFAULT_REGIONS=(
    "ap-northeast-1"
    "us-east-1"
    "eu-west-1"
)

# 列出所有環境配置
list_configs() {
    print_section "AWS 環境配置列表"
    
    # 獲取所有參數路徑
    local all_params=$(aws ssm describe-parameters --query 'Parameters[].Name' --output text 2>/dev/null || echo "")
    
    if [ -z "$all_params" ]; then
        print_warning "未找到任何參數"
        return
    fi
    
    # 解析並列出環境
    declare -A stages
    
    for param in $all_params; do
        if [[ $param =~ ^/organ-brief-([^/]+)/ ]]; then
            stage="${BASH_REMATCH[1]}"
            stages["$stage"]=1
        fi
    done
    
    if [ ${#stages[@]} -eq 0 ]; then
        print_warning "未找到任何 organ-brief 環境配置"
        echo ""
        print_info "建議的環境: dev, staging, prod"
        return
    fi
    
    print_success "找到以下環境："
    for stage in "${!stages[@]}"; do
        echo "  - $stage"
    done
}

# 顯示特定環境配置
show_config() {
    local stage=$1
    
    if [ -z "$stage" ]; then
        print_error "請指定 STAGE"
        return 1
    fi
    
    print_section "環境配置: $stage"
    
    local param_prefix="/organ-brief-${stage}"
    
    echo "參數路徑前綴: $param_prefix"
    echo ""
    
    local found=false
    
    for param in "${DEFAULT_PARAMS[@]}"; do
        local param_path="${param_prefix}/${param}"
        
        if aws ssm get-parameter --name "$param_path" > /dev/null 2>&1; then
            print_success "✓ $param"
            found=true
        else
            print_warning "✗ $param（不存在）"
        fi
    done
    
    if [ "$found" = false ]; then
        print_warning "該環境沒有配置任何參數"
    fi
}

# 初始化環境
init_environment() {
    local stage=$1
    
    if [ -z "$stage" ]; then
        print_error "請指定 STAGE"
        return 1
    fi
    
    print_section "初始化環境: $stage"
    
    print_info "選擇 AWS 區域:"
    for i in "${!DEFAULT_REGIONS[@]}"; do
        echo "  $((i+1)). ${DEFAULT_REGIONS[$i]}"
    done
    echo "  5. 自定義"
    
    read -p "請選擇 (1-5): " region_choice
    
    local region=""
    case $region_choice in
        1) region="${DEFAULT_REGIONS[0]}" ;;
        2) region="${DEFAULT_REGIONS[1]}" ;;
        3) region="${DEFAULT_REGIONS[2]}" ;;
        5) read -p "請輸入區域代碼: " region ;;
        *) print_error "無效選擇"; return 1 ;;
    esac
    
    print_success "選擇區域: $region"
    
    # 收集 API Keys
    local param_prefix="/organ-brief-${stage}"
    
    print_info "請輸入必要的 API Keys (可留空稍後設置):"
    echo ""
    
    for param in "${DEFAULT_PARAMS[@]}"; do
        local param_path="${param_prefix}/${param}"
        read -p "  $param: " value
        
        if [ -n "$value" ]; then
            print_info "設置 $param..."
            aws ssm put-parameter \
                --name "$param_path" \
                --value "$value" \
                --type SecureString \
                --region "$region" \
                --overwrite \
                > /dev/null 2>&1
            
            print_success "✓ $param 已設置"
        else
            print_warning "⊘ $param 已跳過"
        fi
    done
    
    echo ""
    print_success "環境 $stage 初始化完成"
}

# 設置參數
set_parameter() {
    local stage=$1
    local key=$2
    local value=$3
    
    if [ -z "$stage" ] || [ -z "$key" ]; then
        print_error "用法: config_manager.sh set [STAGE] [KEY] [VALUE]"
        return 1
    fi
    
    if [ -z "$value" ]; then
        read -sp "請輸入 $key 的值: " value
        echo ""
    fi
    
    local param_path="/organ-brief-${stage}/${key}"
    
    print_info "設置參數: $param_path"
    
    aws ssm put-parameter \
        --name "$param_path" \
        --value "$value" \
        --type SecureString \
        --overwrite \
        > /dev/null 2>&1
    
    print_success "參數已設置"
}

# 刪除環境配置
delete_config() {
    local stage=$1
    
    if [ -z "$stage" ]; then
        print_error "請指定 STAGE"
        return 1
    fi
    
    print_section "刪除環境配置: $stage"
    
    read -p "確定要刪除 $stage 環境的所有參數嗎？(yes/no) " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_warning "操作已取消"
        return 0
    fi
    
    local param_prefix="/organ-brief-${stage}"
    
    for param in "${DEFAULT_PARAMS[@]}"; do
        local param_path="${param_prefix}/${param}"
        
        if aws ssm get-parameter --name "$param_path" > /dev/null 2>&1; then
            print_info "刪除 $param..."
            aws ssm delete-parameter --name "$param_path"
            print_success "✓ $param 已刪除"
        fi
    done
    
    print_success "環境 $stage 已刪除"
}

# 主流程
main() {
    local action=$1
    
    case $action in
        list)
            list_configs
            ;;
        show)
            show_config "$2"
            ;;
        set)
            set_parameter "$2" "$3" "$4"
            ;;
        init)
            init_environment "$2"
            ;;
        delete)
            delete_config "$2"
            ;;
        *)
            print_section "AWS 環境配置管理器"
            echo ""
            echo "用法:"
            echo "  ./config_manager.sh list                     列出所有環境配置"
            echo "  ./config_manager.sh show [STAGE]             顯示特定環境配置"
            echo "  ./config_manager.sh set [STAGE] [KEY] [VALUE] 設置參數"
            echo "  ./config_manager.sh init [STAGE]             初始化環境"
            echo "  ./config_manager.sh delete [STAGE]           刪除環境配置"
            echo ""
            echo "範例:"
            echo "  ./config_manager.sh list"
            echo "  ./config_manager.sh show dev"
            echo "  ./config_manager.sh init prod"
            echo "  ./config_manager.sh set dev google-genai-api-key sk-xxx"
            echo ""
            ;;
    esac
}

main "$@"
