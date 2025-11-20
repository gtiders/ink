#!/usr/bin/env python3
"""
Phonopy声子谱和ADPs热位移计算器

这个脚本使用phonopy库从FORCECONSTANTS或FORCESETS文件计算声子谱和ADPs热位移。
使用seekpath自动寻找高对称点路径，无需配置文件。
支持读取VASP或其他DFT计算生成的力常数文件。

使用方法:
    python phonopy_calculator.py --help
    python phonopy_calculator.py --poscar POSCAR --force_constants FORCE_CONSTANTS
    python phonopy_calculator.py --poscar POSCAR --force_sets FORCE_SETS --dim 2 2 2
"""

import os
import numpy as np
from phonopy import Phonopy
from phonopy.interface.vasp import read_vasp
from phonopy.file_IO import parse_FORCE_CONSTANTS, parse_FORCE_SETS
from phonopy.units import VaspToTHz


class PhonopyCalculator:
    """声子计算主类"""

    def __init__(self, poscar_file, supercell_matrix=None):
        """
        初始化Phonopy计算器

        Parameters:
        -----------
        poscar_file : str
            POSCAR文件路径
        supercell_matrix : list, optional
            超胞矩阵，默认为[1, 1, 1]
        """
        self.poscar_file = poscar_file
        self.supercell_matrix = supercell_matrix or [1, 1, 1]

        # 读取晶体结构
        self.unitcell = read_vasp(poscar_file)

        # 初始化Phonopy对象
        self.phonon = Phonopy(
            self.unitcell,
            supercell_matrix=np.diag(self.supercell_matrix),
            factor=VaspToTHz,
        )

        print(f"已加载结构文件: {poscar_file}")
        print(f"原子数: {len(self.unitcell.get_scaled_positions())}")
        print(f"超胞矩阵: {self.supercell_matrix}")

    def load_force_constants(self, force_constants_file):
        """
        从FORCE_CONSTANTS文件加载力常数

        Parameters:
        -----------
        force_constants_file : str
            FORCE_CONSTANTS文件路径
        """
        if not os.path.exists(force_constants_file):
            raise FileNotFoundError(f"找不到力常数文件: {force_constants_file}")

        force_constants = parse_FORCE_CONSTANTS(force_constants_file)
        self.phonon.set_force_constants(force_constants)
        print(f"已加载力常数: {force_constants_file}")

    def load_force_sets(self, force_sets_file, dim=None):
        """
        从FORCE_SETS文件加载力集合

        Parameters:
        -----------
        force_sets_file : str
            FORCE_SETS文件路径
        dim : list, optional
            超胞维度，默认为[2, 2, 2]
        """
        if not os.path.exists(force_sets_file):
            raise FileNotFoundError(f"找不到力集合文件: {force_sets_file}")

        force_sets = parse_FORCE_SETS(force_sets_file)
        self.phonon.set_force_sets(force_sets)
        self.phonon.produce_force_constants()
        print(f"已加载力集合并生成力常数: {force_sets_file}")

    def set_mesh_sampling(self, mesh=[20, 20, 20]):
        """
        设置q点网格采样

        Parameters:
        -----------
        mesh : list
            q点网格大小
        """
        self.phonon.set_mesh(mesh, is_eigenvectors=True)
        print(f"已设置q点网格: {mesh}")

    def calculate_band_structure(self):
        """
        计算声子谱，使用seekpath自动寻找高对称点路径

        Returns:
        --------
        dict : 包含声子谱数据的字典
        """
        print("使用seekpath自动寻找高对称点路径...")

        # 使用seekpath获取高对称点路径
        bands = self._get_seekpath_band_path()

        self.phonon.set_band_structure(bands)

        # 获取计算结果
        q_points, distances, frequencies, eigenvectors = (
            self.phonon.get_band_structure()
        )

        # 保存结果
        self._save_band_data(q_points, distances, frequencies)

        return {
            "q_points": q_points,
            "distances": distances,
            "frequencies": frequencies,
            "eigenvectors": eigenvectors,
        }

    def calculate_dos(self, mesh=[40, 40, 40]):
        """
        计算声子态密度(DOS)

        Parameters:
        -----------
        mesh : list
            q点网格大小

        Returns:
        --------
        dict : 包含DOS数据的字典
        """
        self.phonon.set_mesh(mesh)
        self.phonon.set_total_DOS()

        # 获取DOS数据
        dos = self.phonon.get_total_DOS()
        frequencies = dos[0]
        total_dos = dos[1]

        # 保存DOS数据
        np.savetxt(
            "total_dos.dat",
            np.column_stack([frequencies, total_dos]),
            header="Frequency(THz)  DOS",
            fmt="%.8f",
        )

        return {"frequencies": frequencies, "total_dos": total_dos}

    def calculate_adps(self, temperatures=None):
        """
        计算ADPs热位移

        Parameters:
        -----------
        temperatures : list, optional
            温度列表(K)，默认为[100, 200, 300, 400, 500]

        Returns:
        --------
        dict : 包含ADPs数据的字典
        """
        if temperatures is None:
            temperatures = [100, 200, 300, 400, 500]

        # 设置q点网格
        self.phonon.set_mesh([40, 40, 40], is_eigenvectors=True)

        adps_data = []

        for temp in temperatures:
            # 计算热位移
            self.phonon.set_thermal_displacements(temperature=temp)

            # 获取热位移数据
            thermal_displacements = self.phonon.get_thermal_displacements()

            # 提取每个原子的热位移
            atom_displacements = []
            for atom_idx in range(len(self.unitcell.get_scaled_positions())):
                # 获取原子热位移张量
                displacement_tensor = thermal_displacements[atom_idx]
                # 计算各向同性位移 (Uiso)
                u_iso = np.trace(displacement_tensor) / 3.0
                atom_displacements.append(u_iso)

            adps_data.append([temp] + atom_displacements)

        # 保存ADPs数据
        atom_names = self._get_atom_names()
        header = "Temperature(K) " + " ".join(atom_names)
        np.savetxt("adps.dat", adps_data, header=header, fmt="%.6f")

        # 保存YAML格式的热位移数据
        self.phonon.set_thermal_displacements(temperature=300)
        self.phonon.write_yaml_thermal_displacements()

        return {
            "temperatures": temperatures,
            "adps_data": adps_data,
            "atom_names": atom_names,
        }


if __name__ == "__main__":
    # 示例用法
    poscar_file = r"C:\Users\gwins\Desktop\sciplots\datakit\phonopy_eggs\data\POSCAR"
    force_sets_file = (
        r"C:\Users\gwins\Desktop\sciplots\datakit\phonopy_eggs\data\FORCE_SETS"
    )
    force_constants_file = r"C:\Users\gwins\Desktop\sciplots\datakit\shengbte_eggs\data\3rd\FORCE_CONSTANTS_2ND"

    calculator = PhonopyCalculator(poscar_file, supercell_matrix=[3, 3, 3])
    calculator.load_force_sets(force_sets_file)
