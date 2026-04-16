#!/bin/bash

# ==========================================
# 環境初始化腳本
# ==========================================
# 用途：
#   - 創建 Python 虛擬環境
#   - 安裝專案依賴
#   - 初始化 .env 配置文件
#   - 驗證環境配置
#
# 使用方式：
#   ./scripts/setup_environment.sh [--skip-pip] [--skip-env-copy]
# ==========================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 預設值
SKIP_PIP=false
SKIP_ENV_COPY=false
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"

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
    echo -e "${CYAN}=========================================="
    echo "  $1"
    echo -e "==========================================${NC}"
}

check_python_version() {
    print_section "檢查 Python 版本"
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安裝"
        exit 1
    fi
    
    local python_version=$(python3 --version 2>&1 | awk '{print $2}')
    local major=$(echo "$python_version" | cut -d. -f1)
    local minor=$(echo "$python_version" | cut -d. -f2)
    
    print_success "Python 版本: $python_version"
    
    if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 8 ]); then
        print_error "需要 Python 3.8 或更高版本"
        exit 1
    fi
    
    print_success "Python 版本檢查通過"
}

create_virtualenv() {
    print_section "創建虛擬環境"
    
    if [ -d "$VENV_DIR" ]; then
        print_warning "虛擬環境已存在: $VENV_DIR"
        read -p "是否要刪除並重新創建？(yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            print_info "刪除現有虛擬環境..."
            rm -rf "$VENV_DIR"
        else
            print_info "跳過虛擬環境創建"
            return 0
        fi
    fi
    
    print_info "創建虛擬環境: $VENV_DIR"
    python3 -m venv "$VENV_DIR"
    
    if [ $? -eq 0 ]; then
        print_success "虛擬環境創建成功"
    else
        print_error "虛擬環境創建失敗"
        exit 1
    fi
}

activate_venv() {
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
        print_success "虛擬環境已啟用"
    else
        print_error "無法找到虛擬環境 activation 腳本"
        exit 1
    fi
}

install_dependencies() {
    print_section "安裝依賴"
    
    if [ "$SKIP_PIP" = true ]; then
        print_warning "跳過 pip 安裝"
        return 0
    fi
    
    local requirements_file="$PROJECT_ROOT/requirements.txt"
    
    if [ ! -f "$requirements_file" ]; then
        print_error "找不到 requirements.txt: $requirements_file"
        exit 1
    fi
    
    print_info "升級 pip..."
    python -m pip install --upgrade pip --quiet
    
    print_info "安裝依賴套件..."
    pip install -r "$requirements_file" --quiet
    
    if [ $? -eq 0 ]; then
        print_success "依賴安裝完成"
    else
        print_error "依賴安裝失敗"
        exit 1
    fi
}

init_env_file() {
    print_section "初始化 .env 文件"
    
    if [ "$SKIP_ENV_COPY" = true ]; then
        print_warning "跳過 .env 複製"
        return 0
    fi
    
    local env_example="$PROJECT_ROOT/.env.example"
    local env_file="$PROJECT_ROOT/.env"
    
    if [ ! -f "$env_example" ]; then
        print_error "找不到 .env.example: $env_example"
        exit 1
    fi
    
    if [ -f "$env_file" ]; then
        print_warning ".env 文件已存在"
        read -p "是否要覆蓋？(yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            print_info "跳過 .env 複製"
            return 0
        fi
    fi
    
    print_info "複製 .env.example 到 .env..."
    cp "$env_example" "$env_file"
    print_success ".env 文件已創建"
    print_info "請編輯 .env 文件填入必要的 API Keys"
}

validate_environment() {
    print_section "驗證環境配置"
    
    activate_venv
    
    local errors=0
    
    print_info "檢查 Python 版本..."
    python --version || ((errors++))
    
    print_info "檢查關鍵依賴..."
    
    if python -c "import flask" 2>/dev/null; then
        print_success "✓ Flask"
    else
        print_error "✗ Flask (未安裝)"
        ((errors++))
    fi
    
    if python -c "import google.genai" 2>/dev/null; then
        print_success "✓ Google Generative AI"
    else
        print_error "✗ Google Generative AI (未安裝)"
        ((errors++))
    fi
    
    if python -c "import langgraph" 2>/dev/null; then
        print_success "✓ LangGraph"
    else
        print_error "✗ LangGraph (未安裝)"
        ((errors++))
    fi
    
    if python -c "import pydantic" 2>/dev/null; then
        print_success "✓ Pydantic"
    else
        print_error "✗ Pydantic (未安裝)"
        ((errors++))
    fi
    
    print_info "檢查 .env 文件..."
    if [ -f "$PROJECT_ROOT/.env" ]; then
        print_success "✓ .env 文件存在"
    else
        print_warning "✗ .env 文件不存在"
    fi
    
    echo ""
    if [ $errors -eq 0 ]; then
        print_success "環境驗證通過"
    else
        print_error "環境驗證失敗 ($errors 個錯誤)"
        return 1
    fi
}

show_next_steps() {
    print_section "後續步驟"
    
    echo "1. 編輯 .env 文件填入 API Keys:"
    echo "   nano $PROJECT_ROOT/.env"
    echo ""
    echo "2. 啟動開發伺服器:"
    echo "   source $VENV_DIR/bin/activate"
    echo "   python run_api.py"
    echo ""
    echo "3. 運行測試:"
    echo "   pytest tests/"
    echo ""
    echo "4. 使用配置管理器設置 AWS 環境:"
    echo "   ./scripts/config_manager.sh init dev"
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-pip)
                SKIP_PIP=true
                shift
                ;;
            --skip-env-copy)
                SKIP_ENV_COPY=true
                shift
                ;;
            --help|-h)
                echo "用法: $0 [選項]"
                echo ""
                echo "選項:"
                echo "  --skip-pip       跳過 pip 安裝"
                echo "  --skip-env-copy   跳過 .env 複製"
                echo "  --help, -h        顯示此幫助"
                exit 0
                ;;
            *)
                print_error "未知選項: $1"
                exit 1
                ;;
        esac
    done
}

main() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════╗"
    echo "║     環境初始化腳本 - 公司簡介生成系統      ║"
    echo "╚══════════════════════════════════════════╝"
    echo -e "${NC}"
    
    parse_args "$@"
    
    check_python_version
    create_virtualenv
    activate_venv
    install_dependencies
    init_env_file
    validate_environment
    show_next_steps
    
    print_section "初始化完成"
    print_success "環境已成功配置!"
}

main "$@"
