import re
import pandas as pd
import itertools


class ExportLobster:
    def __init__(self):
        """
        初始化 Lobster_analysis
        获取并分析Lobster产生的数据
        """
        pass

    def get_cohp(self, cohp_file="COHPCAR.lobster"):
        """
        获取Lobster计算的COHP数据
        """
        with open(cohp_file, "r") as f:
            next(f)  # 跳过第一行
            data = f.readlines()
            pairs_num = int(data[0].split()[0])
            pairs = self.extract_connection_info(data[1 : pairs_num + 1])
        with open(cohp_file, "r") as f:
            nested_names = [[f"{pair}_cohp", f"{pair}_icohp"] for pair in pairs]
            names = list(itertools.chain(*nested_names))
            cohp_df = pd.read_csv(
                f,
                skiprows=pairs_num + 2,
                sep=r"\s+",
                header=None,
                names=["energy"] + names,
            )
        return pairs, cohp_df

    def extract_connection_info(self, data):
        """
        从包含编号、箭头连接元素等信息的字符串列表中提取关键信息。

        Args:
            data (list): 包含原始字符串的列表。

        Returns:
            list: 提取出的关键信息列表。
        """
        result = []
        for item in data:
            # 去除换行符
            item = item.strip()
            if item == "Average":
                result.append(item)
            else:
                # 使用正则表达式提取箭头连接的元素
                match = re.search(r":([^(\n]+)", item)
                if match:
                    result.append(match.group(1))
        return result
