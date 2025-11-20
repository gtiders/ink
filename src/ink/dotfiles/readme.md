# 安装dotfiles

## windows

```powershell
Start-Process -FilePath "uv" -ArgumentList "tool run dotbot -d . -c dotbot_config\windows.yaml" -Verb RunAs
```

## unix

```bash
uv tool run dotbot -d . -c dotbot_config/unix.yaml
```
