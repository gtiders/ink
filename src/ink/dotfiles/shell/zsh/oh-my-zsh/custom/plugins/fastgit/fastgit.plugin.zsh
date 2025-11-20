#!/usr/bin/env zsh

# 一个用于增强 git clone 命令的函数，专门处理 http 开头的网址
# 在网址前面添加指定的字符串（如 fastgit 镜像前缀）
function fastclone() {
    # 检查参数数量
    if [[ $# -lt 1 ]]; then
        echo "用法: fastclone <url> [其他 git clone 参数]"
        echo "注意: URL 必须以 http 开头"
        return 1
    fi
    # 定义默认的前缀字符串
    FASTGIT_PREFIX="https://ghfast.top/"

    # 用法: fastclone <url> [其他 git clone 参数]
    # 示例: fastclone https://github.com/user/repo.git
    #       fastclone https://github.com/user/repo.git -b dev
    
    # 获取第一个参数作为 URL
    local url=$1
    # 移除第一个参数，剩下的作为 git clone 的其他参数
    shift
    
    # 检查 URL 是否以 http 开头
    if [[ ! $url =~ ^http ]]; then
        echo "错误: URL 必须以 http 或 https 开头"
        return 1
    fi
    
    # 在 URL 前面添加前缀字符串
    local modified_url="${FASTGIT_PREFIX}${url}"
    
    # 输出将要执行的命令信息
    echo "正在使用修改后的 URL 克隆仓库: $modified_url"
    
    # 执行 git clone 命令
    git clone "$modified_url" "$@"
}