import typer


from .collect_dfts import collect_dfts as _collect_dfts


app = typer.Typer(help="ink.tools command-line interface")

# 注册 collect_dfts 命令：ink tools collect_dfts <paths...>
collect_dfts = app.command(name="collect_dfts")(_collect_dfts)


if __name__ == "__main__":
    app()