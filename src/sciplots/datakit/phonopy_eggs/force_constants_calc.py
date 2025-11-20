#!/usr/bin/env python3
"""
高阶力常数计算器

使用hiphive和ase计算高阶力常数，支持多种势函数和配置方式。
支持从命令行参数或JSON配置文件设置计算参数。

使用方法:
    python force_constants_calc.py --help
    python force_constants_calc.py --poscar POSCAR --potential-file potential.xml
    python force_constants_calc.py --config config.json
"""

import os
import json
import click
import numpy as np
from ase.io import read
from hiphive import ClusterSpace, StructureContainer, ForceConstantPotential
from trainstation import Optimizer
from hiphive.utilities import prepare_structures
from hiphive.structure_generation import generate_mc_rattled_structures
import warnings

warnings.filterwarnings("ignore")


class ForceConstantsCalculator:
    """高阶力常数计算器类"""

    def __init__(self, config):
        """
        初始化计算器

        Parameters:
        -----------
        config : dict
            计算配置参数字典
        """
        self.config = config
        self.atoms = None
        self.calculator = None
        self.cluster_space = None
        self.structure_container = None
        self.fcp = None

    def load_structure(self, structure_file):
        """加载结构文件，支持POSCAR和xyz格式"""
        try:
            self.atoms = read(structure_file)
            file_format = (
                "POSCAR"
                if structure_file.lower().endswith(("poscar", "vasp"))
                else "xyz"
                if structure_file.lower().endswith("xyz")
                else "unknown"
            )
            print(f"已加载结构: {structure_file} (格式: {file_format})")
            print(f"原子数: {len(self.atoms)}")
            print(f"化学式: {self.atoms.get_chemical_formula()}")
            return True
        except Exception as e:
            print(f"加载结构文件失败: {e}")
            return False

    def setup_calculator(self, potential_file=None, potential_type=None):
        """设置计算器，支持多种势函数"""
        if potential_file and os.path.exists(potential_file):
            # 根据势函数类型和文件名设置计算器
            if potential_type == "nep" or (
                potential_file and potential_file.endswith(".nep.txt")
            ):
                print(f"加载NEP势函数: {potential_file}")
                self.calculator = self._load_nep_calculator(potential_file)
            elif potential_type == "dp" or (
                potential_file and potential_file.endswith(".pb")
            ):
                print(f"加载DP势函数: {potential_file}")
                self.calculator = self._load_dp_calculator(potential_file)
            else:
                print("使用默认EMT势函数")
                self.calculator = self._load_default_calculator()
        else:
            print("使用默认EMT势函数")
            self.calculator = self._load_default_calculator()

    def _load_nep_calculator(self, potential_file):
        """加载NEP势函数计算器 - 请在此实现具体加载逻辑"""
        # TODO: 用户需要在此实现NEP势函数的加载逻辑
        # 示例:
        # from your_nep_module import NEP
        # return NEP(potential_file)
        raise NotImplementedError("NEP势函数加载逻辑需要用户实现")

    def _load_dp_calculator(self, potential_file):
        """加载DP势函数计算器 - 请在此实现具体加载逻辑"""
        # TODO: 用户需要在此实现DP势函数的加载逻辑
        # 示例:
        # from deepmd.calculator import DP
        # return DP(model=potential_file)
        raise NotImplementedError("DP势函数加载逻辑需要用户实现")

    def _load_default_calculator(self):
        """加载默认计算器"""
        # 默认使用ASE的EMT势函数
        from ase.calculators.emt import EMT

        return EMT()

    def generate_training_structures(self):
        """生成训练结构 - 统一使用9元素超胞矩阵"""
        print("正在准备训练结构...")

        # 统一获取超胞原子结构（9元素矩阵格式）
        supercell_atoms = self._get_supercell_atoms()

        # 检查是否提供了微扰构型文件
        perturb_file = self.config.get("perturb_file")
        if perturb_file and os.path.exists(perturb_file):
            print(f"从xyz文件读取微扰构型: {perturb_file}")

            # 使用ASE直接读取xyz文件中的所有构型
            try:
                structures = read(perturb_file, index=":")
                if structures:
                    prepared_structures = prepare_structures(
                        structures, supercell_atoms, self.calculator
                    )
                    print(f"从xyz文件加载了 {len(prepared_structures)} 个构型")
                    return prepared_structures
                else:
                    print("xyz文件为空，将生成随机扰动构型")
            except Exception as e:
                print(f"xyz文件读取失败: {e}，将生成随机扰动构型")

        # 生成随机扰动构型
        n_structures = self.config.get("n_structures", 100)
        rattle_std = self.config.get("rattle_std", 0.03)
        min_distance = self.config.get("min_distance", 1.5)

        structures = generate_mc_rattled_structures(
            supercell_atoms,
            n_structures=n_structures,
            rattle_std=rattle_std,
            d_min=min_distance,
        )
        prepared_structures = prepare_structures(
            structures, supercell_atoms, self.calculator
        )

        print(f"最终获得 {len(prepared_structures)} 个训练结构")
        return prepared_structures

    def setup_cluster_space(self):
        """设置簇空间，支持从超胞文件或原胞+倍数创建"""
        print("正在设置簇空间...")

        # 获取截断距离
        cutoffs = self.config.get("cutoffs", [5.0, 4.0, 3.5])

        # 统一获取超胞原子结构
        supercell_atoms = self._get_supercell_atoms()

        # 设置簇空间
        self.cluster_space = ClusterSpace(supercell_atoms, cutoffs=list(cutoffs))

        print("簇空间设置完成")
        self.cluster_space.print_tables()
        self.cluster_space.print_orbits()

        return self.cluster_space

    def _get_supercell_atoms(self):
        """统一获取超胞原子结构 - 仅支持9元素矩阵格式"""
        supercell = self.config.get("supercell", [3, 0, 0, 0, 3, 0, 0, 0, 3])

        # 验证必须是9元素格式
        if not isinstance(supercell, list) or len(supercell) != 9:
            print(
                "警告：配置中的supercell不是9元素，使用默认值 [3, 0, 0, 0, 3, 0, 0, 0, 3]"
            )
            supercell = [3, 0, 0, 0, 3, 0, 0, 0, 3]

        # 9元素矩阵格式
        supercell_matrix = np.array(supercell).reshape(3, 3)
        from ase.build import make_supercell

        supercell_atoms = make_supercell(self.atoms, supercell_matrix)
        print(f"使用9元素超胞矩阵: \n{supercell_matrix}")

        return supercell_atoms

    def fit_force_constants(self, structures):
        """拟合力常数"""
        print("正在拟合力常数...")

        # 创建结构容器
        self.structure_container = StructureContainer(self.cluster_space)
        for structure in structures:
            self.structure_container.add_structure(structure)

        # 训练模型
        opt = Optimizer(self.structure_container.get_fit_data())
        opt.train()
        print(opt)

        # 创建力常数势
        self.fcp = ForceConstantPotential(self.cluster_space, opt.parameters)

        # 保存力常数势
        output_dir = self.config.get("output_dir", "output")
        os.makedirs(output_dir, exist_ok=True)
        self.fcp.write("force_constants.fcp")
        supercell_atoms = self._get_supercell_atoms()
        self.fcp.get_force_constants(supercell_atoms).write_to_phonopy(
            "2nd", format="text"
        )
        self.fcp.get_force_constants(supercell_atoms).write_to_shengBTE(
            "3nd", self.atoms
        )
        return self.fcp

    def run_full_calculation(
        self, structure_file, potential_file=None, potential_type=None
    ):
        """运行完整计算流程，支持POSCAR和xyz格式"""
        print("开始高阶力常数计算...")

        # 1. 加载结构
        if not self.load_structure(structure_file):
            return False

        # 2. 设置计算器
        self.setup_calculator(potential_file, potential_type)

        # 3. 生成训练结构
        structures = self.generate_training_structures()

        # 4. 设置簇空间
        self.setup_cluster_space()

        # 5. 拟合力常数
        self.fit_force_constants(structures)

        print("计算完成！")
        return True

    @staticmethod
    def create_default_config(filename="default_config.json"):
        """创建默认配置文件 - 仅支持9元素超胞矩阵"""
        default_config = {
            "supercell": [3, 0, 0, 0, 3, 0, 0, 0, 3],
            "n_structures": 100,
            "rattle_std": 0.03,
            "cutoffs": [5.0, 4.0, 3.5],
            "fit_method": "ridge",
            "min_distance": 1.5,
            "save_higher_order": True,
            "output_dir": "output",
            "perturb_file": None,
        }

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            print(f"默认配置文件已创建: {filename}")
            return True
        except Exception as e:
            print(f"创建配置文件失败: {e}")
            return False


@click.command()
@click.option("--poscar", "-p", required=True, help="POSCAR结构文件路径")
@click.option("--potential-file", "-pf", help="势函数文件路径")
@click.option(
    "--potential-type",
    "-pt",
    type=click.Choice(["nep", "dp", "emt"], case_sensitive=False),
    default="emt",
    help="势函数类型 (默认: emt)",
)
@click.option("--config", "-c", help="JSON配置文件路径")
@click.option("--output-dir", "-o", default="output", help="输出目录")
@click.option(
    "--supercell", "-s", nargs=9, type=int, default=None, help="超胞矩阵(9元素)"
)
@click.option("--n-structures", "-n", type=int, default=50, help="训练结构数量")
@click.option("--rattle-std", "-r", type=float, default=0.01, help="扰动标准差(Å)")
@click.option(
    "--cutoffs",
    "-cut",
    nargs=3,
    type=float,
    default=[5.0, 4.0, 3.5],
    help="截断距离(Å)",
)
@click.option(
    "--fit-method",
    "-fm",
    default="ridge",
    type=click.Choice(["ridge", "least_squares", "lasso", "ard"], case_sensitive=False),
    help="拟合方法",
)
@click.option(
    "--save-higher-order/--no-save-higher-order",
    default=True,
    help="是否保存高阶力常数",
)
@click.option("--create-config", is_flag=True, help="创建默认配置文件")
@click.option("--perturb-file", "-pf", help="微扰构型xyz文件路径")
def main(
    poscar,
    potential_file,
    potential_type,
    config,
    output_dir,
    supercell,
    n_structures,
    rattle_std,
    cutoffs,
    fit_method,
    save_higher_order,
    create_config,
    perturb_file,
):
    """高阶力常数计算器主程序"""

    # 创建默认配置文件
    if create_config:
        ForceConstantsCalculator.create_default_config()
        return

    # 加载配置
    calculation_config = {
        "supercell": supercell,
        "n_structures": n_structures,
        "rattle_std": rattle_std,
        "cutoffs": cutoffs,
        "fit_method": fit_method,
        "output_dir": output_dir,
        "save_higher_order": save_higher_order,
        "perturb_file": perturb_file,
    }

    # 合并JSON配置
    if config and os.path.exists(config):
        try:
            with open(config, "r") as f:
                json_config = json.load(f)
            calculation_config.update(json_config)
            print(f"已加载配置文件: {config}")
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return

    # 打印配置
    print("计算配置:")
    for key, value in calculation_config.items():
        print(f"  {key}: {value}")

    # 创建计算器并运行
    calculator = ForceConstantsCalculator(calculation_config)

    success = calculator.run_full_calculation(
        poscar, potential_file=potential_file, potential_type=potential_type
    )

    if success:
        print("计算成功完成！")
    else:
        print("计算失败！")


if __name__ == "__main__":
    main()
