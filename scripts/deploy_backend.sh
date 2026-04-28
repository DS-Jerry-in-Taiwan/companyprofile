#!/bin/bash

# ==========================================
# 後端部署腳本（增強版）
# ==========================================
# 用法:
#   ./deploy_backend.sh [OPTIONS]
#
# 選項:
#   -s, --stage STAGE           部署階段 (dev/staging/prod) [默認: dev]
#   -r, --region REGION         AWS 區域 (ap-northeast-1/us-east-1/etc) [默認: ap-northeast-1]
#   -p, --profile PROFILE       AWS Profile 名稱
#   -e, --env-file FILE         環境變數檔案路徑 [默認: .env.deploy]
#   --skip-validate             跳過驗證檢查
#   --skip-login                跳過 ECR 登入
#   --dry-run                   乾跑模式（只顯示執行命令但不執行）
#   --force                     強制部署（即使有未提交的改動）
#   -h, --help                  顯示幫助信息
#
# 版本規則:
#   使用 Git Tag + Commit Hash 組合 version
#   格式: v0.0.2-abc1234
#   如果沒有 tag，則使用 commit hash
#
# 範例:
#   ./deploy_backend.sh -s dev -r ap-northeast-1
#   ./deploy_backend.sh --stage prod --region us-east-1 --profile prod-account
#   ./deploy_backend.sh -s staging --profile staging --dry-run
#
# ==========================================

set -e

# ==========================================
# 默認值
# ==========================================
STAGE="dev"
AWS_REGION="ap-northeast-1"
AWS_PROFILE=""
ENV_FILE=".env.deploy"
SKIP_VALIDATE=false
SKIP_LOGIN=false
DRY_RUN=false
FORCE_DEPLOY=false

# ==========================================
# 顏色輸出
# ==========================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ==========================================
# 取得版本資訊 (Git Tag + Commit Hash)
# ==========================================
get_version_info() {
    # 取得当前 commit hash (7位)
    GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    
    # 取得最新的 tag名稱
    GIT_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    
    if [ -n "$GIT_TAG" ]; then
        # 如果有 tag，組合 version: v0.0.2-abc1234
        DEPLOY_VERSION="${GIT_TAG}-${GIT_COMMIT}"
    else
        # 如果沒有 tag，使用 commit hash 作為 version
        DEPLOY_VERSION="$GIT_COMMIT"
    fi
    
    export DEPLOY_VERSION
    export GIT_COMMIT
    export GIT_TAG
}

# ==========================================
# 檢查 Git 狀態
# ==========================================
check_git_status() {
    # 檢查是否有未提交的改動
    if [ -n "$(git status --porcelain)" ]; then
        print_warning "Git working tree 有未提交的改動："
        git status --short
        echo ""
        if [ "$FORCE_DEPLOY" != "true" ]; then
            print_error "請先提交或stash這些改動，或使用 --force 強制部署"
            return 1
        else
            print_warning "使用 --force 參數，強制部署"
        fi
    fi
    
    # 檢查當前 branch
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || git symbolic-ref --short HEAD 2>/dev/null || echo "unknown")
    print_info "當前分支: $CURRENT_BRANCH"
    
    return 0
}

# ==========================================
# 函數定義
# ==========================================

print_help() {
    grep "^#" "$0" | head -40
}

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

# 解析命令行參數
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -s|--stage)
                STAGE="$2"
                shift 2
                ;;
            -r|--region)
                AWS_REGION="$2"
                shift 2
                ;;
            -p|--profile)
                AWS_PROFILE="$2"
                shift 2
                ;;
            -e|--env-file)
                ENV_FILE="$2"
                shift 2
                ;;
            --skip-validate)
                SKIP_VALIDATE=true
                shift
                ;;
            --skip-login)
                SKIP_LOGIN=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force)
                FORCE_DEPLOY=true
                shift
                ;;
            -h|--help)
                print_help
                exit 0
                ;;
            *)
                print_error "未知參數: $1"
                echo ""
                print_help
                exit 1
                ;;
        esac
    done
}

# 驗證部署配置
validate_deployment() {
    print_section "驗證部署配置"
    
    print_info "檢查必要文件..."
    required_files=(
        "serverless.yml"
        "src/functions/Dockerfile"
        "src/functions/lambda_handler.py"
        "src/functions/requirements.txt"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "文件不存在: $file"
            return 1
        fi
        print_success "$file"
    done
    
    return 0
}

# 檢查 AWS 環境
check_aws_environment() {
    print_section "檢查 AWS 環境"
    
    local aws_cmd="aws"
    if [ -n "$AWS_PROFILE" ]; then
        aws_cmd="aws --profile $AWS_PROFILE"
    fi
    
    print_info "檢查 AWS CLI 配置..."
    if ! eval "$aws_cmd sts get-caller-identity > /dev/null 2>&1"; then
        print_error "AWS CLI 配置失敗或憑證無效"
        return 1
    fi
    
    # 獲取帳戶信息
    local account_info
    account_info=$(eval "$aws_cmd sts get-caller-identity")
    local account_id=$(echo "$account_info" | grep -o '"Account": "[^"]*' | cut -d'"' -f4)
    local user_arn=$(echo "$account_info" | grep -o '"Arn": "[^"]*' | cut -d'"' -f4)
    
    print_success "AWS 帳戶: $account_id"
    print_success "用戶: $user_arn"
    print_success "區域: $AWS_REGION"
    
    return 0
}

# 檢查 Parameter Store 參數
check_parameter_store() {
    print_section "檢查 AWS Parameter Store 參數"
    
    local aws_cmd="aws"
    if [ -n "$AWS_PROFILE" ]; then
        aws_cmd="aws --profile $AWS_PROFILE"
    fi
    
    # 統一路徑: /organ-brief/ (所有環境共用同一組 keys)
    local param_prefix="/organ-brief"
    
    print_info "參數路徑前綴: $param_prefix"
    
    # 檢查必要的參數
    local required_params=(
        "google-genai-api-key"
        "gemini-api-key"
        "tavily-api-key"
    )
    
    local missing_params=()
    
    for param in "${required_params[@]}"; do
        local param_path="${param_prefix}/${param}"
        
        if eval "$aws_cmd ssm get-parameter --name '$param_path' --region $AWS_REGION > /dev/null 2>&1"; then
            print_success "✓ $param_path"
        else
            print_warning "✗ $param_path（不存在）"
            missing_params+=("$param_path")
        fi
    done
    
    if [ ${#missing_params[@]} -gt 0 ]; then
        echo ""
        print_warning "缺少以下參數，部署將使用環境變數或默認值："
        for param in "${missing_params[@]}"; do
            echo "  - $param"
        done
        echo ""
        print_info "設置參數的命令示例："
        for param in "${required_params[@]}"; do
            echo "  aws ssm put-parameter --name '/organ-brief-${STAGE}/${param}' --value 'YOUR_VALUE' --type SecureString --region $AWS_REGION"
        done
        echo ""
    fi
    
    return 0
}

# 登入 ECR
login_ecr() {
    if [ "$SKIP_LOGIN" = true ]; then
        print_warning "跳過 ECR 登入"
        return 0
    fi
    
    print_section "登入 ECR"
    
    local aws_cmd="aws"
    if [ -n "$AWS_PROFILE" ]; then
        aws_cmd="aws --profile $AWS_PROFILE"
    fi
    
    print_info "獲取 AWS 帳戶 ID..."
    local account_id
    account_id=$(eval "$aws_cmd sts get-caller-identity --query Account --output text")
    print_success "帳戶 ID: $account_id"
    
    print_info "登入 ECR..."
    if [ "$DRY_RUN" = true ]; then
        echo "  [DRY-RUN] docker login --username AWS --password-stdin $account_id.dkr.ecr.$AWS_REGION.amazonaws.com"
    else
        eval "$aws_cmd ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin \"$account_id.dkr.ecr.$AWS_REGION.amazonaws.com\""
        print_success "ECR 登入成功"
    fi
    
    return 0
}

# 執行部署
deploy_serverless() {
    print_section "部署 Serverless"
    
    # 取得版本資訊 (Git Tag + Commit Hash)
    get_version_info
    
    if [ "$DRY_RUN" = false ]; then
        BUILD_DATE=$(date -u +"%Y%m%d-%H%M%S")
        export BUILD_DATE
    fi
    
    print_info "部署版本: $DEPLOY_VERSION"
    print_info "Git Tag: ${GIT_TAG:-無}"
    print_info "Commit: $GIT_COMMIT"
    echo ""
    
    local deploy_cmd="serverless deploy --stage $STAGE"
    
    if [ -n "$AWS_PROFILE" ]; then
        deploy_cmd="$deploy_cmd --aws-profile $AWS_PROFILE"
    fi
    
    print_info "執行部署命令..."
    echo "  $deploy_cmd"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        echo "  [DRY-RUN] 跳過實際部署"
        return 0
    else
        if eval "$deploy_cmd"; then
            return 0
        else
            print_error "Serverless 部署失敗"
            return 1
        fi
    fi
}

# 從 .env 同步 API Key 到 SSM Parameter Store
sync_parameters_from_env() {
    if [ "$SKIP_VALIDATE" = true ]; then
        return 0
    fi

    print_section "同步 .env → SSM Parameter Store"

    local aws_cmd="aws"
    if [ -n "$AWS_PROFILE" ]; then
        aws_cmd="aws --profile $AWS_PROFILE"
    fi

    local env_file="${ENV_FILE:-.env}"
    if [ ! -f "$env_file" ]; then
        # 若指定檔案不存在，改用專案根目錄的 .env
        env_file="$(dirname "$(readlink -f "$0")")/../.env"
    fi
    if [ ! -f "$env_file" ]; then
        print_warning ".env 檔案不存在，跳過參數同步"
        return 0
    fi

    # 載入 .env
    set -a
    source "$env_file"
    set +a

    # 要同步的參數對應 (依 stage 選擇對應的 env var)
    local params=()
    case $STAGE in
        dev)
            params=(
                "gemini-api-key:DEV_GEMINI_API_KEY"
                "tavily-api-key:TAVILY_API_KEY"
            )
            ;;
        prod)
            params=(
                "gemini-api-key:PRD_GEMINI_API_KEY"
                "tavily-api-key:TAVILY_API_KEY"
            )
            ;;
    esac

    local synced=0
    local skipped=0
    for entry in "${params[@]}"; do
        local ssm_name="${entry%%:*}"
        local env_name="${entry##*:}"
        local env_value="${!env_name}"

        if [ -z "$env_value" ]; then
            print_warning "環境變數 $env_name 為空，跳過"
            skipped=$((skipped + 1))
            continue
        fi

        local param_path="/organ-brief/${ssm_name}"

        # 檢查是否已存在
        if eval "$aws_cmd ssm get-parameter --name '$param_path' --region $AWS_REGION > /dev/null 2>&1"; then
            print_success "✓ $ssm_name (已存在)"
            skipped=$((skipped + 1))
            continue
        fi

        # 建立參數
        if [ "$DRY_RUN" = true ]; then
            echo "  [DRY-RUN] aws ssm put-parameter --name '$param_path' --value '***' --type SecureString --region $AWS_REGION"
        else
            if eval "$aws_cmd ssm put-parameter --name '$param_path' --value '$env_value' --type SecureString --region $AWS_REGION --overwrite > /dev/null 2>&1"; then
                print_success "✓ $ssm_name (已建立)"
                synced=$((synced + 1))
            else
                print_error "✗ $ssm_name (建立失敗)"
            fi
        fi
    done

    print_info "完成: $synced 同步, $skipped 跳過"
}

# 主流程
main() {
    print_section "後端部署腳本（增強版）"
    
    # 解析參數
    parse_arguments "$@"
    
    # 顯示配置信息
    print_info "部署配置："
    echo "  Stage: $STAGE"
    echo "  Region: $AWS_REGION"
    echo "  Profile: ${AWS_PROFILE:-默認憑證}"
    [ "$DRY_RUN" = true ] && echo "  模式: DRY-RUN（只顯示不執行）"
    [ "$FORCE_DEPLOY" = true ] && echo "  模式: FORCE（強制部署）"
    echo ""
    
    # 改變到專案根目錄
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR/.."
    
    # 執行部署步驟
    if [ "$SKIP_VALIDATE" != true ]; then
        validate_deployment || exit 1
    fi
    
    check_git_status || exit 1
    check_aws_environment || exit 1
    check_parameter_store || true
    sync_parameters_from_env || true
    login_ecr || exit 1
    deploy_serverless || exit 1
    
    print_section "部署完成！"
    echo ""
    print_success "後端服務已部署到 $STAGE 環境"
    print_info "版本: ${DEPLOY_VERSION:-unknown}"
}

# 執行主流程
main "$@"
