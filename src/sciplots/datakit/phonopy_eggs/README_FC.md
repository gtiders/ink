# 高阶力常数计算器

使用 `hiphive` 和 `ase` 计算高阶力常数的命令行工具，支持多种势函数和灵活的配置方式。

## 功能特性

- 🧮 使用hiphive计算高阶力常数（2阶、3阶等）
- 🎯 支持多种势函数：EMT、Lennard-Jones、Morse、EAM
- 📊 自动生成训练结构并进行力常数拟合
- ⚙️ 支持命令行参数和JSON配置文件
- 📁 输出标准格式的力常数文件
- 🔧 所有参数都有合理的默认值

## 安装依赖

```bash
pip install -r requirements_fc.txt
```

## 使用方法

### 1. 基本使用

```bash
# 使用默认EMT势函数
python force_constants_calc.py --poscar POSCAR

# 使用EAM势函数
python force_constants_calc.py --poscar POSCAR --potential-file potential.eam.alloy --potential-type eam

# 使用配置文件
python force_constants_calc.py --poscar POSCAR --config config_example.json

# 创建默认配置文件
python force_constants_calc.py --create-config

# 使用超胞文件（SPOSCAR或xyz格式）和微扰构型
python force_constants_calc.py --poscar SPOSCAR --supercell-file supercell.xyz --perturb-file perturbed_structures.xyz
```

### 2. 命令行参数

```bash
python force_constants_calc.py --help
```

**必需参数：**
- `--poscar, -p`: POSCAR结构文件路径

**可选参数：**
- `--potential-file, -pf`: 势函数文件路径（推荐提供）
- `--potential-type, -pt`: 势函数类型 [nep, dp, emt] (默认: emt)
- `--config, -c`: JSON配置文件路径
- `--output-dir, -o`: 输出目录 (默认: output)
- `--supercell`: 超胞矩阵 [A11 A12 A13 A21 A22 A23 A31 A32 A33] (9元素，默认: 2 0 0 0 2 0 0 0 2)
- `--perturb-file`: 微扰构型xyz文件路径
- `--n-structures, -n`: 训练结构数量 (默认: 50)
- `--rattle-std, -r`: 扰动标准差(Å) (默认: 0.01)
- `--cutoffs`: 截断距离(Å) [2阶 3阶 4阶] (默认: 5.0 4.0 3.5)
- `--fit-method, -fm`: 拟合方法 [ridge, least_squares, lasso, ard] (默认: ridge)
- `--save-higher-order/--no-save-higher-order`: 是否保存高阶力常数 (默认: 保存)
- `--create-config`: 创建默认配置文件

### 3. JSON配置文件

创建 `config.json` 文件来设置参数：

```json
{
    "supercell": [3, 3, 3],
    "n_structures": 100,
    "rattle_std": 0.015,
    "cutoffs": [6.0, 5.0, 4.0],
    "fit_method": "ridge",
    "min_distance": 1.8,
    "save_higher_order": true,
    "output_dir": "my_output",
    "supercell_file": "supercell.xyz",
    "perturb_file": "perturbed_structures.xyz"
}
```

配置文件中的参数会覆盖命令行参数的默认值。

## 势函数支持

| 势函数类型 | 文件格式 | 描述 |
|---|---|---|
| `emt` | - | 有效介质理论（默认） |
| `nep` | `.nep.txt` | NEP机器学习势函数 |
| `dp` | `.pb` | DeepMD势函数 |

> **注意**：NEP和DP势函数需要用户实现具体的计算器加载逻辑。参考代码中的`_load_nep_calculator`和`_load_dp_calculator`方法。

## 输出文件

计算完成后，输出目录包含：

- `FORCE_CONSTANTS`: 二阶力常数（Phonopy格式）
- `fc3.npy`: 三阶力常数（NumPy格式，可选）
- 其他相关数据文件

## 示例工作流程

### 示例工作流程

### 示例1：铜的力常数计算

```bash
# 1. 准备POSCAR文件（铜的晶胞）
# 2. 运行计算（使用9元素超胞矩阵）
python force_constants_calc.py --poscar POSCAR_Cu --supercell 3 0 0 0 3 0 0 0 3 --n-structures 80

# 3. 查看结果
cd output
ls -la
```

#### 2. NEP势函数
```bash
# 使用NEP势函数（需要实现_nep_calculator方法）
python force_constants_calc.py POSCAR --potential-file nep.txt --potential-type nep
```

#### 3. DP势函数
```bash
# 使用DeepMD势函数（需要实现_dp_calculator方法）
python force_constants_calc.py POSCAR --potential-file model.pb --potential-type dp
```

### 示例3：文件格式支持

```bash
# 使用xyz格式的结构文件
python force_constants_calc.py --poscar structure.xyz --potential-file Cu.eam.alloy --potential-type eam

# 使用超胞文件（无需扩包倍数）
python force_constants_calc.py --supercell-file supercell.xyz --perturb-file perturbed.xyz

# 使用SPOSCAR文件
python force_constants_calc.py --poscar SPOSCAR --supercell-file SPOSCAR
```

## 超胞设置

### 超胞格式
仅支持9元素矩阵格式：

```json
"supercell": [3, 0, 0, 0, 3, 0, 0, 0, 3]
```
对应3x3矩阵：
```
[[3, 0, 0],
 [0, 3, 0],
 [0, 0, 3]]
```

### 不同体系的推荐参数

**简单金属：**
- `supercell`: [3, 0, 0, 0, 3, 0, 0, 0, 3]
- `n_structures`: 50-100
- `rattle_std`: 0.01-0.02 Å
- `cutoffs`: [5.0, 4.0, 3.5] Å

**半导体：**
- `supercell`: [2, 0, 0, 0, 2, 0, 0, 0, 2]
- `n_structures`: 80-150
- `rattle_std`: 0.008-0.015 Å
- `cutoffs`: [4.5, 3.5, 3.0] Å

**复杂氧化物：**
- `supercell`: [2, 0, 0, 0, 2, 0, 0, 0, 2]
- `n_structures`: 100-200
- `rattle_std`: 0.005-0.01 Å
- `cutoffs`: [5.5, 4.5, 4.0] Å

## 常见问题

### 1. 内存不足

减少超胞尺寸或训练结构数量：
```bash
python force_constants_calc.py --poscar POSCAR --supercell 2 2 2 --n-structures 30
```

### 2. 计算太慢

减少训练结构数量或使用更小的截断距离：
```bash
python force_constants_calc.py --poscar POSCAR --n-structures 30 --cutoffs 4.5 3.5 3.0
```

### 3. 拟合质量差

增加训练结构或调整扰动大小：
```bash
python force_constants_calc.py --poscar POSCAR --n-structures 150 --rattle-std 0.02
```

### 4. 势函数文件问题

确保势函数文件格式正确，对于EAM势：
- 文件扩展名应为 `.eam` 或 `.eam.alloy`
- 文件路径正确且可读

## 技术细节

### 算法流程

1. **结构准备**: 加载POSCAR并创建超胞
2. **训练集生成**: 通过随机扰动生成训练结构
3. **力计算**: 使用指定势函数计算力和能量
4. **簇空间构建**: 定义力常数的数学表示
5. **参数拟合**: 使用优化算法拟合力常数参数
6. **力常数提取**: 计算并保存最终力常数矩阵

### 数学基础

- 力常数展开基于晶格动力学理论
- 使用最小二乘法进行参数优化
- 支持正则化方法防止过拟合

## 势函数扩展开发

### NEP势函数集成
在`force_constants_calc.py`中实现`_load_nep_calculator`方法：

```python
def _load_nep_calculator(self, potential_file):
    from your_nep_module import NEP  # 替换为实际的NEP模块
    return NEP(potential_file)
```

### DP势函数集成
在`force_constants_calc.py`中实现`_load_dp_calculator`方法：

```python
def _load_dp_calculator(self, potential_file):
    from deepmd.calculator import DP  # 替换为实际的DP模块
    return DP(model=potential_file)
```

## 相关工具

- [hiphive文档](https://hiphive.materialsmodeling.org/)
- [ase文档](https://wiki.fysik.dtu.dk/ase/)
- [Phonopy](https://phonopy.github.io/phonopy/) - 用于后续声子计算