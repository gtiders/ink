#!/usr/bin/env python3
"""
ALAMODE声子谱数据可视化工具

该脚本用于读取ALAMODE计算得到的声子谱数据文件，并生成温度相关的声子色散曲线图。
支持自定义输入文件、输出格式、颜色映射等参数。

示例用法:
    python ExportALM.py  # 使用默认参数
    python ExportALM.py --input-file my_data.dat --output-file plot.png --temp-range 100 500
    python ExportALM.py --cmap plasma --dpi 300 --save-only
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import click
from typing import List, Tuple, Optional


def read_alamode_data(
    input_file: str,
) -> Tuple[List[str], List[float], pd.DataFrame, List[str]]:
    """
    读取ALAMODE声子谱数据文件

    参数:
        input_file (str): 输入文件路径

    返回:
        Tuple包含:
            - labels (List[str]): 高对称点标签列表
            - labels_distance (List[float]): 高对称点对应的距离值
            - data (pd.DataFrame): 声子谱数据
            - branchs (List[str]): 分支名称列表
    """
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            # 读取第一行：高对称点标签
            labels = f.readline().strip()[1:].split()
            # 读取第二行：高对称点对应的距离值
            labels_distance = f.readline().strip()[1:].split()
            labels_distance = [float(i) for i in labels_distance]
    except FileNotFoundError:
        raise click.ClickException(f"错误：文件 '{input_file}' 不存在")
    except Exception as e:
        raise click.ClickException(f"错误读取文件头信息: {str(e)}")

    try:
        # 读取声子谱数据
        # 跳过以#开头的注释行，使用空白字符分隔
        data = pd.read_csv(input_file, sep=r"\s+", comment="#", header=None)

        # 生成分支名称列表（从第3列开始，每列对应一个声子分支）
        branchs = [f"branch{i}" for i in range(1, data.shape[1] - 1)]

        # 设置列名：第一列为温度，第二列为距离，其余为各分支
        data.columns = ["T", "distance"] + branchs

        return labels, labels_distance, data, branchs

    except Exception as e:
        raise click.ClickException(f"错误读取声子谱数据: {str(e)}")


def filter_temperature_range(
    data: pd.DataFrame, temp_range: Tuple[float, float]
) -> pd.DataFrame:
    """
    根据温度范围过滤数据

    参数:
        data (pd.DataFrame): 输入数据
        temp_range (Tuple[float, float]): 温度范围 (min_temp, max_temp)

    返回:
        pd.DataFrame: 过滤后的数据
    """
    min_temp, max_temp = temp_range
    filtered_data = data[(data["T"] >= min_temp) & (data["T"] <= max_temp)]

    if filtered_data.empty:
        raise click.ClickException(
            f"错误：在温度范围 {min_temp}-{max_temp} K 内没有数据"
        )

    return filtered_data


def create_phonon_plot(
    data: pd.DataFrame,
    labels: List[str],
    labels_distance: List[float],
    branchs: List[str],
    cmap_name: str,
    title: str = "ALAMODE 声子色散曲线",
) -> plt.Figure:
    """
    创建声子色散曲线图

    参数:
        data (pd.DataFrame): 声子谱数据
        labels (List[str]): 高对称点标签
        labels_distance (List[float]): 高对称点距离值
        branchs (List[str]): 分支名称列表
        cmap_name (str): 颜色映射名称
        title (str): 图形标题

    返回:
        plt.Figure: matplotlib图形对象
    """
    # 按温度分组
    grouped_T = data.groupby("T")
    groups_key = sorted(grouped_T.groups.keys())

    # 创建颜色映射
    try:
        cmap = plt.get_cmap(cmap_name)
    except ValueError:
        available_cmaps = [
            "viridis",
            "plasma",
            "inferno",
            "magma",
            "cividis",
            "YlOrRd",
            "YlOrBr",
            "YlGnBu",
            "RdYlBu",
            "coolwarm",
        ]
        raise click.ClickException(
            f"错误：颜色映射 '{cmap_name}' 不存在。可用的颜色映射: {', '.join(available_cmaps)}"
        )

    # 根据温度数量生成颜色
    colors = cmap(np.linspace(0, 1, len(groups_key)))

    # 创建图形
    fig, ax = plt.subplots(figsize=(10, 6))

    # 绘制每个温度下的声子谱
    for index, T in enumerate(groups_key):
        df = grouped_T.get_group(T)
        # 将频率从THz转换为cm^-1（乘以33.35641）
        # 或者使用用户提供的转换因子
        conversion_factor = 0.0299792458  # THz到cm^-1的转换因子

        for branch in branchs:
            ax.plot(
                df["distance"],
                df[branch] * conversion_factor,
                color=colors[index],
                linewidth=1.5,
                alpha=0.8,
                label=f"{T}K" if branch == branchs[0] else "",  # 只在第一个分支添加标签
            )

    # 设置x轴标签（高对称点）
    ax.set_xticks(labels_distance)
    ax.set_xticklabels(labels)

    # 设置轴标签和标题
    ax.set_xlabel("波矢", fontsize=12)
    ax.set_ylabel("频率 (cm$^{-1}$)", fontsize=12)
    ax.set_title(title, fontsize=14, pad=20)

    # 添加网格
    ax.grid(True, alpha=0.3)

    # 添加图例（仅在图中有空间时）
    if len(groups_key) <= 10:  # 如果温度点不多，显示图例
        ax.legend(title="温度", bbox_to_anchor=(1.05, 1), loc="upper left")

    # 调整布局
    plt.tight_layout()

    return fig


@click.command()
@click.option(
    "--input-file",
    "-i",
    default="./scph_K.scph_bands",
    help="输入的ALAMODE声子谱数据文件路径 (默认: ./scph_K.scph_bands)",
)
@click.option("--output-file", "-o", help="输出图形文件路径 (如果不提供，则显示图形)")
@click.option(
    "--temp-range", "-t", nargs=2, type=float, help="温度范围 (最小值 最大值)，单位为K"
)
@click.option("--cmap", default="YlOrRd", help="颜色映射名称 (默认: YlOrRd)")
@click.option(
    "--title",
    default="ALAMODE 声子色散曲线",
    help='图形标题 (默认: "ALAMODE 声子色散曲线")',
)
@click.option("--dpi", default=150, type=int, help="输出图形DPI (默认: 150)")
@click.option("--save-only", is_flag=True, help="只保存图形，不显示")
@click.option("--width", default=10, type=float, help="图形宽度 (英寸) (默认: 10)")
@click.option("--height", default=6, type=float, help="图形高度 (英寸) (默认: 6)")
def main(
    input_file: str,
    output_file: Optional[str],
    temp_range: Optional[Tuple[float, float]],
    cmap: str,
    title: str,
    dpi: int,
    save_only: bool,
    width: float,
    height: float,
):
    """
    ALAMODE声子谱数据可视化主程序

    读取ALAMODE计算得到的声子谱数据，并生成温度相关的声子色散曲线图。
    """
    # 读取数据
    labels, labels_distance, data, branchs = read_alamode_data(input_file)

    # 如果指定了温度范围，过滤数据
    if temp_range:
        data = filter_temperature_range(data, temp_range)

    # 创建图形
    fig = create_phonon_plot(data, labels, labels_distance, branchs, cmap, title)

    # 设置图形大小
    fig.set_size_inches(width, height)

    # 保存或显示图形
    if output_file:
        try:
            fig.savefig(output_file, dpi=dpi, bbox_inches="tight")
            click.echo(f"图形已保存到: {output_file}")
        except Exception as e:
            raise click.ClickException(f"保存图形失败: {str(e)}")

    if not save_only and not output_file:
        plt.show()
    elif not save_only and output_file:
        plt.show()
    else:
        plt.close(fig)


if __name__ == "__main__":
    main()
