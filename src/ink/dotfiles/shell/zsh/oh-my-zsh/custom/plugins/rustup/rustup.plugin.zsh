# 检查文件是否存在且可读
if [[ -f "$HOME/.rustup/env" && -r "$HOME/.rustup/env" ]]; then
. "$HOME/.rustup/env"
fi

if [[ -f "$HOME/.cargo/env" && -r "$HOME/.cargo/env" ]]; then
# 加载环境变量文件
. "$HOME/.cargo/env"
fi