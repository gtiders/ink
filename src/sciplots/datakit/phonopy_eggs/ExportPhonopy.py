import yaml
import pandas as pd
import numpy as np


class ExportPhonopy:
    def __init__(self, yaml_file="phonopy_disp.yaml"):
        """
        初始化 Phonopy_analysis
        获取并分析Phonopy产生的数据

        Parameters
        ----------
        yaml_file : str, optional
            phonopy_disp.yaml文件路径, by default "phonopy_disp.yaml"
        """

        # 定义 _add_suffix_to_atom 函数
        def _add_suffix_to_atom(lst):
            def generate_suffix():
                counts = {}  # 内部计数器字典

                def get_suffix(element):
                    counts[element] = counts.get(element, 0) + 1  # 更新计数器
                    return f"{element}{counts[element]}"  # 返回带编号的元素

                return get_suffix

            suffix_generator = generate_suffix()
            result = [suffix_generator(e) for e in lst]
            return result

        # 读取phonopy生成结构文件时的通用信息
        with open(yaml_file, "r") as f:
            phonopy_disp_data = yaml.safe_load(f)
        self.primitive_cell_atoms = _add_suffix_to_atom(
            [
                point.get("symbol")
                for point in phonopy_disp_data["primitive_cell"]["points"]
            ]
        )

    def get_band(self, yaml_file="band.yaml"):
        """
        获取Phonopy计算的声子谱数据
        """
        with open(yaml_file, "r") as f:
            data = yaml.safe_load(f)
        natom = data.get("natom")
        phonon_branches = ["TA1", "TA2", "LA"] + [
            f"OP{i + 1}" for i in range(3 * natom - 3)
        ]
        labels = data.get("labels")
        if labels is None:
            raise KeyError("'labels' key not found in the YAML data")

        segment_nqpoint = data.get("segment_nqpoint")
        if segment_nqpoint is None:
            raise KeyError("'segment_nqpoint' key not found in the YAML data")

        # 计算每段的开始和结束索引
        end_indices = [
            sum(segment_nqpoint[: i + 1]) for i in range(len(segment_nqpoint))
        ]
        start_indices = [0] + end_indices[:-1]
        segment_indices = list(zip(start_indices, end_indices))
        split_segment_nqpoint = [i[1] for i in segment_indices]

        phonon = data.get("phonon")
        if phonon is None:
            raise KeyError("'phonon' key not found in the YAML data")
        band_dict = {branch: [] for branch in phonon_branches}
        for band_idx, branch in enumerate(phonon_branches):
            for phonon_index, phonon_info in enumerate(phonon):
                band_dict[branch].append(phonon_info["band"][band_idx]["frequency"])
                if phonon_index + 1 in split_segment_nqpoint:
                    band_dict[branch].append(np.nan)
        distance = [phonon_info["distance"] for phonon_info in phonon]

        # 获取每个区间对应 distance 的值
        distance_values = [
            (distance[start], distance[end - 1]) for start, end in segment_indices
        ]

        if len(labels) != len(segment_indices):
            raise ValueError(
                "The length of labels does not match the length of segment_indices"
            )
        label_pairs = [(label[0], label[1]) for label in labels]

        band_distance = []
        for i in range(len(distance)):
            band_distance.append(distance[i])
            if i + 1 in split_segment_nqpoint:
                band_distance.append(np.nan)
        band_df = pd.DataFrame(band_dict)
        band_df.insert(0, "distance", band_distance)
        band_df.to_csv("band.csv", index=False, float_format="%.10f", sep=",")
        return band_df, list(zip(label_pairs, distance_values))

    def get_dos(self, dos_file="projected_dos.dat"):
        """
        获取Phonopy计算的DOS数据
        """
        dos_df = pd.read_csv(
            dos_file,
            sep=r"\s+",
            comment="#",
            header=None,
            names=["Frequency"] + self.primitive_cell_atoms,
        )
        total_dos = dos_df.iloc[:, 1:].sum(axis=1)
        dos_df.insert(1, "tdos", total_dos)
        return dos_df

    def get_adps(self, yaml_file="thermal_displacements.yaml"):
        """
        获取Phonopy计算的ADPs数据
        """
        # 导出ADPs数据即热位移数据
        with open(yaml_file, "r") as f:
            thermal_displacements_data = yaml.safe_load(f)["thermal_displacements"]
        # 提取热位移数据
        thermal_displacements_dict = {atom: [] for atom in self.primitive_cell_atoms}
        thermal_displacements_temperature = []
        for entry in thermal_displacements_data:
            thermal_displacements_temperature.append(entry["temperature"])
            for atom_idx, displacements in enumerate(entry["displacements"]):
                atom = self.primitive_cell_atoms[atom_idx]
                thermal_displacements_dict[atom].append(displacements[0])
        thermal_displacements_df = pd.DataFrame(thermal_displacements_dict)
        thermal_displacements_df.insert(
            0, "temperature", thermal_displacements_temperature
        )
        return thermal_displacements_df
