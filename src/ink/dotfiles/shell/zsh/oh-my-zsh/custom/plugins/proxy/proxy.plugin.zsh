
# 启用WSL代理win端口;需要windows的代理软件开启允许局域网;自行查看虚拟网络接口在局域网设置中
proxy_with_win() {
    # 检查参数数量
    if [ $# -ne 2 ]; then
        echo "用法: proxy_with_win <Windows主机IP地址> <代理端口>"
        echo "示例: proxy_with_win 172.25.144.1 7897"
        return 1
    fi

    local WIN_HOST="$1"  # 第一个参数直接是IP地址
    local PROXY_PORT="$2"  # 第二个参数是端口号

    # 显示配置信息
    echo "使用Windows主机IP: $WIN_HOST"
    echo "使用代理端口: $PROXY_PORT"
    
    # 拼接并设置代理
    export http_proxy="http://$WIN_HOST:$PROXY_PORT"
    export https_proxy="http://$WIN_HOST:$PROXY_PORT"
    export all_proxy="socks5://$WIN_HOST:$PROXY_PORT"

    echo "代理已设置: $WIN_HOST:$PROXY_PORT"
}
    

# 添加关闭代理的函数
proxy_off() {
    unset http_proxy
    unset https_proxy
    unset all_proxy
}