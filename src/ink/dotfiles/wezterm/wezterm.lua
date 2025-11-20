local wezterm = require 'wezterm'
local config = wezterm.config_builder()

-- 获取配置文件所在目录（WezTerm 提供的正确方法）
local config_dir = wezterm.config_dir

-- 字体设置
-- 字体设置 - 添加回退机制
config.font = wezterm.font_with_fallback({
    'LXGW Bright Code GB', 'Consolas', -- Windows默认等宽字体
    'Courier New', -- 通用等宽字体
    'monospace' -- 最终回退
})
config.font_size = 12

-- 基础设置
config.color_scheme = 'Ayu Mirage'
config.max_fps = 120
config.front_end = 'WebGpu'
config.webgpu_power_preference = 'HighPerformance'

-- 根据操作系统选择Shell
if wezterm.target_triple:find("windows") ~= nil then
    -- Windows系统：nu → pwsh → powershell → cmd
    local function command_exists(cmd)
        local success, stdout, stderr =
            wezterm.run_child_process({"where", cmd})
        return success and stdout and stdout ~= ""
    end

    if command_exists("nu.exe") then
        config.default_prog = {'nu.exe', '-l'}
    elseif command_exists("powershell.exe") then
        config.default_prog = {'powershell.exe', '-NoLogo'}
    else
        config.default_prog = {'cmd.exe'}
    end
else
    -- Unix系统：nu → zsh → bash
    local function command_exists(cmd)
        local success, stdout, stderr = wezterm.run_child_process({
            "sh", "-c", "command -v " .. cmd
        })
        return success and stdout and stdout ~= ""
    end

    if command_exists("nu") then
        config.default_prog = {'nu', '-i'}
    elseif command_exists("bash") then
        config.default_prog = {'bash', '-i'}
    else
        config.default_prog = {'sh', '-i'}
    end
end

-- 窗口样式
config.window_decorations = "INTEGRATED_BUTTONS|RESIZE"
config.window_frame = {active_titlebar_bg = '#090909'}
config.integrated_title_button_alignment = "Right"
config.integrated_title_button_style = "Windows"
config.integrated_title_buttons = {"Hide", "Maximize", "Close"}

-- config.window_padding = {left = 0, right = 0, top = 10, bottom = 7.5}
config.adjust_window_size_when_changing_font_size = false
config.window_close_confirmation = 'NeverPrompt'

-- 标签栏配置
config.enable_tab_bar = false
config.show_new_tab_button_in_tab_bar = true
config.show_tab_index_in_tab_bar = true
-- config.show_tabs_in_tab_bar = true
config.switch_to_last_active_tab_when_closing_tab = true
config.tab_max_width = 25
config.use_fancy_tab_bar = true
config.window_frame = {
    active_titlebar_bg = "#090909",
    inactive_titlebar_bg = "#090909"
}

-- 背景图片配置
-- config.background = {
--     {
--         source = { File = config_dir .. "/cherry-lava.jpg" },
--         hsb = {
--             brightness = 0.5,        -- 调整亮度 (0.0-1.0)
--             saturation = 1,        -- 调整饱和度 (0.0-1.0)
--             hue = 1,               -- 调整色调 (0.0-1.0)
--         },
--         opacity = 0.9,               -- 透明度 (0.0-1.0)
--         vertical_align = "Middle",   -- 垂直对齐方式
--         horizontal_align = "Center", -- 水平对齐方式
--         repeat_x = "NoRepeat",       -- 水平重复
--         repeat_y = "NoRepeat",       -- 垂直重复
--         attachment = "Fixed",        -- 背景附着方式
--     }
-- }

config.colors = {
    scrollbar_thumb = '#242936',
    tab_bar = {
        active_tab = {bg_color = '#090909', fg_color = '#ff6565'},
        inactive_tab = {bg_color = '#090909', fg_color = '#95e6cb'},
        inactive_tab_hover = {bg_color = '#0f1419', fg_color = '#95e6cb'},
        new_tab = {bg_color = '#090909', fg_color = '#95e6cb'},
        new_tab_hover = {bg_color = '#42a5f5', fg_color = '#ffffff'}
    }
}

-- 光标与交互
config.cursor_blink_ease_in = 'EaseOut'
config.cursor_blink_ease_out = 'EaseOut'
config.default_cursor_style = 'BlinkingBar'
config.cursor_blink_rate = 650
config.underline_thickness = '1pt'
config.inactive_pane_hsb = {saturation = 1, brightness = 1}

-- 自定义启动菜单项
config.launch_menu = {
    {label = "Bash", args = {"bash", "-l"}},
    {label = "Zsh", args = {"zsh", "-l"}}, {
        label = "Pwsh",
        args = {"pwsh.exe", "-NoLogo"} -- Windows only
    }, {
        label = "PowerShell",
        args = {"powershell.exe", "-NoLogo"} -- Windows only
    }, -- SSH 连接
    {
        label = "SSH: ybgao2024",
        args = {"ssh", "-p 22", "ybgao2024@122.207.79.205"} -- Wq(wbBNB(:8?Q&nHMo5G
    }, {
        label = "SSH: software",
        args = {"ssh", "-p", "22", "software@122.207.79.205"} -- DjB*q(utH#i4XimnuU2R
    }, -- WSL 发行版
    {
        label = "WSL: fedora",
        args = {"wsl.exe", "-d", "fedora"} -- Windows only
    }
}

-- 添加切换标签栏显示状态的事件处理器
wezterm.on('toggle-tab-bar', function(window, pane)
    local overrides = window:get_config_overrides() or {}
    if overrides.enable_tab_bar == nil then
        overrides.enable_tab_bar = false
    else
        overrides.enable_tab_bar = not overrides.enable_tab_bar
    end
    window:set_config_overrides(overrides)
end)

-- 统一的键位配置方案
config.disable_default_key_bindings = true

-- 全局leader键 
config.leader = {key = "a", mods = "CTRL", timeout_milliseconds = 1500}

-- 重新组织的快捷键配置
config.keys = {
    -- F11: 切换全屏模式
    {key = 'F11', mods = 'NONE', action = wezterm.action.ToggleFullScreen},
    -- Leader+m: 隐藏窗口
    {key = 'm', mods = 'LEADER', action = wezterm.action.Hide},
    -- Leader+t: 新建标签页
    {key = 'n', mods = 'LEADER', action = wezterm.action.SpawnTab('CurrentPaneDomain')},
    -- Leader+w: 关闭当前标签页
    {key = 'w', mods = 'LEADER', action = wezterm.action.CloseCurrentTab({confirm = false})},
    -- Leader+Tab: 切换到下一个标签页
    {key = 'Tab', mods = 'LEADER', action = wezterm.action.ActivateTabRelative(1)},
    -- Leader+\: 水平分割
    {key = '\\', mods = 'LEADER', action = wezterm.action.SplitHorizontal({domain = 'CurrentPaneDomain'})},
    -- Leader+-: 垂直分割
    {key = '-', mods = 'LEADER', action = wezterm.action.SplitVertical({domain = 'CurrentPaneDomain'})},    
    -- Leader+方向键: 切换窗格
    {key = "LeftArrow", mods = 'LEADER', action = wezterm.action.ActivatePaneDirection('Left')},
    {key = "DownArrow", mods = 'LEADER', action = wezterm.action.ActivatePaneDirection('Down')},
    {key = "UpArrow", mods = 'LEADER', action = wezterm.action.ActivatePaneDirection('Up')},
    {key = "RightArrow", mods = 'ALT', action = wezterm.action.ActivatePaneDirection('Right')},
    -- Ctrl+Shift+方向键: 调整窗格大小
    {key = "LeftArrow", mods = 'CTRL|SHIFT', action = wezterm.action.AdjustPaneSize({'Left', 5})},
    {key = "DownArrow", mods = 'CTRL|SHIFT', action = wezterm.action.AdjustPaneSize({'Down', 5})},
    {key = "UpArrow", mods = 'CTRL|SHIFT', action = wezterm.action.AdjustPaneSize({'Up', 5})},
    {key = "RightArrow", mods = 'CTRL|SHIFT', action = wezterm.action.AdjustPaneSize({'Right', 5})},
    -- Ctrl+Shift+W: 关闭当前窗格
    {key = 'w', mods = 'CTRL|SHIFT', action = wezterm.action.CloseCurrentPane({confirm = true})},
    -- Leader+T: 切换标签栏显示
    {key = "t", mods = 'LEADER', action = wezterm.action.EmitEvent('toggle-tab-bar')},
    -- Leader+F: 搜索
    {key = 'f', mods = 'LEADER', action = wezterm.action.Search('CurrentSelectionOrEmptyString')},
    -- Leader+P: 快速打开 (类似 VS Code)
    {key = 'p', mods = 'LEADER', action = wezterm.action.ShowLauncher},
    -- Leader+K: 清除屏幕
    {key = 'k', mods = 'LEADER', action = wezterm.action.ClearScrollback('ScrollbackAndViewport')},
    -- F1: 帮助和命令面板
    {key = "F1", action = wezterm.action.ShowLauncherArgs {
        flags = "FUZZY|LAUNCH_MENU_ITEMS|DOMAINS|KEY_ASSIGNMENTS"
    }},
    
    -- Leader+Home/End: 跳到顶部/底部
    {key = 'Home', mods = 'LEADER', action = wezterm.action.ScrollToTop},
    {key = 'End', mods = 'LEADER', action = wezterm.action.ScrollToBottom},
}

-- 鼠标行为
-- 鼠标行为
config.disable_default_mouse_bindings = false
config.mouse_bindings = {
    {  -- 点击左键选择文本
        event = {Up = {streak = 1, button = 'Left'}},
        mods = 'NONE',
        action = wezterm.action.CompleteSelection('Clipboard')
    }, {  -- 点击右键粘贴
        event = {Down = {streak = 1, button = 'Right'}},
        mods = 'NONE',
        action = wezterm.action.PasteFrom('Clipboard')
    }, {
        -- 按住 Ctrl+Alt 键并拖动鼠标来移动窗口
        event = {Drag = {streak = 1, button = 'Left'}},
        mods = 'CTRL|ALT',
        action = wezterm.action.StartWindowDrag
    }, {
        -- 按住 Ctrl 键并点击左键打开超链接
        event = {Up = {streak = 1, button = 'Left'}},
        mods = 'CTRL',
        action = wezterm.action.OpenLinkAtMouseCursor
    },
}

-- 高级功能
config.enable_scroll_bar = true
config.scrollback_lines = 10000 -- 修改滚动条长度为10000行
config.automatically_reload_config = true
config.exit_behavior = 'CloseOnCleanExit'
config.exit_behavior_messaging = 'Verbose'
config.status_update_interval = 50000
config.scrollback_lines = 20000

-- 超链接处理
config.hyperlink_rules = {
    {regex = '\\((\\w+://\\S+)\\)', format = '$1', highlight = 1},
    {regex = '\\[(\\w+://\\S+)\\]', format = '$1', highlight = 1},
    {regex = '\\{(\\w+://\\S+)\\}', format = '$1', highlight = 1},
    {regex = '<(\\w+://\\S+)>', format = '$1', highlight = 1},
    {regex = '\\b\\w+://\\S+[)/a-zA-Z0-9-]+', format = '$0'},
    {regex = '\\b\\w+@[\\w-]+(\\.[\\w-]+)+\\b', format = 'mailto:$0'}
}


return config
