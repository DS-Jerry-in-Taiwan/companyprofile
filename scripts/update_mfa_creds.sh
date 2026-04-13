#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_section() { echo ""; echo "=========================================="; echo "  $1"; echo "=========================================="; }

# 檢查 profile 是否存在
profile_exists() {
    local name="$1"
    python3 -c "
import configparser
c = configparser.ConfigParser()
c.read('/home/ubuntu/.aws/config')
print('EXISTS' if c.has_section('$name') or c.has_section('profile $name') else 'NOT_FOUND')
" 2>/dev/null | grep -q "EXISTS"
}

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         AWS MFA 臨時憑證更新工具                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: 選擇要更新的 Profile
print_section "步驟 1/3：選擇要更新的 Profile"
echo ""

echo "可用的 Profiles："
grep -E "^\[|^profile" ~/.aws/config 2>/dev/null | sed 's/\[//g;s/\]//g;s/profile //g' | sort -u | while read line; do
    echo "  - $line"
done
echo ""

read -p "請輸入要更新的 Profile 名稱: " profile_name

if [ -z "$profile_name" ]; then
    print_error "Profile 名稱不能為空"; exit 1
fi

if ! profile_exists "$profile_name"; then
    print_error "Profile '$profile_name' 不存在"; exit 1
fi

print_success "選擇 Profile: $profile_name"

# Step 2: 選擇用於獲取 MFA ARN 的 Profile
print_section "步驟 2/3：選擇驗證用 Profile"
echo ""

print_info "因為 '$profile_name' 的憑證可能已過期"
print_info "需要用另一個有效的 profile 來獲取 MFA Device ARN"
echo ""

echo "可用的驗證用 Profiles："
for p in default office; do
    if profile_exists "$p"; then
        echo "  - $p"
    fi
done
echo ""

read -p "請輸入一個有效的 Profile（用於獲取 MFA ARN）: " auth_profile

if [ -z "$auth_profile" ]; then
    print_error "Profile 名稱不能為空"; exit 1
fi

if ! profile_exists "$auth_profile"; then
    print_error "Profile '$auth_profile' 不存在"; exit 1
fi

# 嘗試獲取 MFA serial
mfa_serial=$(aws configure get mfa_serial --profile "$auth_profile" 2>/dev/null || true)

if [ -z "$mfa_serial" ]; then
    # 從用戶 ARN 推斷
    user_arn=$(aws sts get-caller-identity --profile "$auth_profile" --query 'Arn' --output text 2>/dev/null || true)
    if [ -n "$user_arn" ]; then
        account_id=$(echo "$user_arn" | grep -o '[0-9]\{12\}' | head -1)
        username=$(echo "$user_arn" | grep -o 'user/[^:]*$' | sed 's/user\///')
        mfa_serial="arn:aws:iam::${account_id}:mfa/${username}"
    fi
fi

if [ -z "$mfa_serial" ]; then
    print_error "無法獲取 MFA Device ARN"
    read -p "請輸入 MFA Device ARN: " mfa_serial
else
    print_success "找到 MFA Device: $mfa_serial"
    read -p "是否使用這個設備？ (Y/n): " confirm
    if [[ "$confirm" =~ ^[Nn]$ ]]; then
        read -p "請輸入 MFA Device ARN: " mfa_serial
    fi
fi

# Step 3: MFA Code
print_section "步驟 3/3：輸入 MFA 驗證碼"
echo ""

print_info "請打開您的 MFA 應用，輸入 6 位數驗證碼"
read -p "請輸入 MFA 驗證碼: " mfa_code

if ! [[ "$mfa_code" =~ ^[0-9]{6}$ ]]; then
    print_error "MFA 驗證碼應該是 6 位數字"; exit 1
fi

# Get STS using auth_profile (not the expired profile)
print_section "正在獲取 STS 臨時憑證"
echo ""

print_info "使用 Profile: $auth_profile 進行驗證"
print_info "將更新 Profile: $profile_name"

# 使用有效的 profile 獲取 STS，然後更新目標 profile
sts_output=$(aws sts get-session-token \
    --serial-number "$mfa_serial" \
    --token-code "$mfa_code" \
    --profile "$auth_profile" 2>&1)

if [ $? -ne 0 ]; then
    print_error "STS 調用失敗"; echo "$sts_output"; exit 1
fi

AWS_ACCESS_KEY_ID=$(echo "$sts_output" | grep -o '"AccessKeyId": "[^"]*' | cut -d'"' -f4)
AWS_SECRET_ACCESS_KEY=$(echo "$sts_output" | grep -o '"SecretAccessKey": "[^"]*' | cut -d'"' -f4)
AWS_SESSION_TOKEN=$(echo "$sts_output" | grep -o '"SessionToken": "[^"]*' | cut -d'"' -f4)

if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    print_error "解析 STS 輸出失敗"; exit 1
fi

print_success "成功獲取臨時憑證！"

# Update Profile
print_section "更新 Profile: $profile_name"
echo ""

backup_file=~/.aws/credentials.backup.$(date +%Y%m%d_%H%M%S)
cp ~/.aws/credentials "$backup_file"
print_info "已備份到: $backup_file"

python3 << PYTHON_SCRIPT
import configparser
config = configparser.ConfigParser()
config.read('/home/ubuntu/.aws/credentials')
if not config.has_section('$profile_name'):
    config.add_section('$profile_name')
config.set('$profile_name', 'aws_access_key_id', '$AWS_ACCESS_KEY_ID')
config.set('$profile_name', 'aws_secret_access_key', '$AWS_SECRET_ACCESS_KEY')
config.set('$profile_name', 'aws_session_token', '$AWS_SESSION_TOKEN')
with open('/home/ubuntu/.aws/credentials', 'w') as f:
    config.write(f)
print("OK")
PYTHON_SCRIPT

print_success "Profile '$profile_name' 憑證已更新！"

# Verify
echo ""
test_result=$(aws sts get-caller-identity --profile "$profile_name" 2>&1 || true)
if echo "$test_result" | grep -q "UserId"; then
    print_success "✅ 憑證更新成功！"
    echo "$test_result" | python3 -m json.tool 2>/dev/null || echo "$test_result"
else
    print_error "驗證失敗"
fi

echo ""
print_success "完成！"
echo "新 Access Key: ${AWS_ACCESS_KEY_ID:0:15}..."
echo ""
