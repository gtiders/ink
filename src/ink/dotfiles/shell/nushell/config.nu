$env.config.show_banner = false

$env.config.shell_integration.osc133 = false  # 解决weztermm和nushell的配合问题
#如果不能解决继续增加这一行
# $env.config.shell_integration.osc633 = false  # 解决weztermm和nushell的配合问题


if (which hx | is-not-empty) {
    $env.config.buffer_editor = "hx"
} else if (which helix | is-not-empty) {
    $env.config.buffer_editor = "helix"
} else if (which nvim | is-not-empty) {
    $env.config.buffer_editor = "nvim"
} else if (which vim | is-not-empty) {
    $env.config.buffer_editor = "vim"
} else {
    $env.config.buffer_editor = "vi"
}

# 设置uv的环境代理
$env.UV_DEFAULT_INDEX = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"

# 增加Home/.local/bin到环境变量
$env.PATH = (
  $env.PATH
  | split row (char esep)
  | append (
    if $nu.os-info.name == "windows" {
      $env.HOMEPATH | path join ".local/bin"
    } else {
      $env.HOME | path join ".local/bin"
    }
  )
  | uniq
)

# 将brew的软件路径加到nushell
if $nu.os-info.name == "linux" {
$env.PATH = ($env.PATH | split row (char esep) | prepend '/home/linuxbrew/.linuxbrew/bin')
}

# 增加pixi的环境变量
$env.PATH = (
  $env.PATH
  | split row (char esep)
  | append (
    if $nu.os-info.name == "windows" {
      $env.HOMEPATH | path join ".pixi/bin"
    } else {
      $env.HOME | path join ".pixi/bin"
    }
  )
  | uniq
)

# 增加cargo的环境变量
$env.PATH = (
  $env.PATH
  | split row (char esep)
  | append (
    if $nu.os-info.name == "windows" {
      $env.HOMEPATH | path join ".cargo/bin"
    } else {
      $env.HOME | path join ".cargo/bin"
    }
  )
  | uniq
)

# 加载一些自己的脚本
use ( $nu.config-path | path dirname | path join "scripts/conda.nu")


# 使用yazi打开当前目录
def --env yy [...args] {
	let tmp = (mktemp -t "yazi-cwd.XXXXXX")
	yazi ...$args --cwd-file $tmp
	let cwd = (open $tmp)
	if $cwd != "" and $cwd != $env.PWD {
		cd $cwd
	}
	rm -fp $tmp
}
# 给yazi配置file.exe的环境变量
if (which scoop | is-not-empty) {
    let scoop_grandparent = (which scoop | get path | first) | path dirname | path dirname
    $env.PATH = (
        $env.PATH
        | split row (char esep)
        | append ($scoop_grandparent | path join "apps/git/current/usr/bin")
        | uniq
    )
}

# 设置一个函数改变代理（只接受端口号）
def --env vpn-proxy [port: string = "7897"] {
    let host = "127.0.0.1"
    let proxy_url = $"http://($host):($port)"
    load-env { 
        http_proxy: $proxy_url, 
        https_proxy: $proxy_url,
        HTTP_PROXY: $proxy_url,
        HTTPS_PROXY: $proxy_url
    }
    print $"代理已设置为: ($proxy_url)"
}

# 清除代理的函数
def --env no-proxy [] {
    load-env { 
        http_proxy: null, 
        https_proxy: null,
        HTTP_PROXY: null,
        HTTPS_PROXY: null
    }
    print "代理已清除"
}


# 检测starship是否可用并设置自动加载
def setup-starship-autoload [] {
    if (which starship | is-empty) {
        print "starship not found, skipping starship setup"
    } else {
        mkdir ($nu.data-dir | path join "vendor/autoload")
        starship init nu | save -f ($nu.data-dir | path join "vendor/autoload/starship.nu")
    }
}

# 检测pixi是否可用并设置自动加载
def setup-pixi-autoload [] {
    if (which pixi | is-empty) {
        print "pixi not found, skipping pixi setup"
    } else {
        mkdir $"($nu.data-dir)/vendor/autoload"
        pixi completion --shell nushell | save --force $"($nu.data-dir)/vendor/autoload/pixi-completions.nu"
    }
}

setup-pixi-autoload
setup-starship-autoload