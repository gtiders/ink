import typer

from .ShengBTE import main as _shengbte_main
from .collect_dfts import collect_dfts as _collect_dfts


app = typer.Typer(help="ink.tools command-line interface")

# 使用 command() 的方式注册 shengbte 命令
shengbte = app.command(name="shengbte")(_shengbte_main)

# 注册 collect_dfts 命令：ink tools collect_dfts <paths...>
collect_dfts = app.command(name="collect_dfts")(_collect_dfts)


if __name__ == "__main__":
    app()