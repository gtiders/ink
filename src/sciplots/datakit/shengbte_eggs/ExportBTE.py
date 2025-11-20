import pandas as pd
import numpy as np


class BaseBTE:
    """
    处理三声子计算的基类
    提供处理ShengBTE三声子计算结果的基础功能
    """

    def __init__(self, sheng_folder_path, omega_file="BTE.omega", dim=3):
        """
        初始化 BaseBTE 类的实例。

        参数:
        sheng_folder_path (str): ShengBTE 计算完成的文件夹路径。
        omega_file (str): 声子频率文件的名称，默认为 "BTE.omega"。
        dim (int): 体系维度，默认为 3。
        """
        self.sheng_folder_path = sheng_folder_path
        # 构建 BTE.omega 文件的完整路径
        omega_file_path = sheng_folder_path + "/" + omega_file

        # 读取文件内容
        try:
            df = pd.read_csv(omega_file_path, sep=r"\s+", header=None)
            # 计算原子数
            self.natom = int(df.shape[1] / 3)
        except FileNotFoundError:
            raise FileNotFoundError(f"未找到文件: {omega_file_path}")
        except Exception as e:
            raise RuntimeError(f"读取文件 {omega_file_path} 时出错: {e}")

        if dim == 3:
            self.branch = ["TA1", "TA2", "LA"] + [
                f"OP{i + 1}" for i in range(3 * self.natom - 3)
            ]

        self.omega = df / (2 * np.pi)
        self.omega.columns = self.branch
        self.directs = ["xx", "xy", "xz", "yx", "yy", "yz", "zx", "zy", "zz"]

    def get_omega(self):
        """
        获取声子频率数据。

        返回:
        df_omega (pd.DataFrame): 包含频率数据的 DataFrame，列名对应不同的声子分支。
        频率单位: THz
        """
        return self.omega

    def get_dos(self, dos_file="BTE.dos", pdos_file="BTE.pdos"):
        """
        获取 DOS 数据 DataFrame。

        参数:
        dos_file (str): DOS 数据文件的名称，默认为 "BTE.dos"。
        pdos_file (str): PDOS 数据文件的名称，默认为 "BTE.pdos"。

        返回:
        df_dos (pd.DataFrame): 包含 DOS 数据的 DataFrame。(第一列为频率，第二列为DOS)
        df_pdos (pd.DataFrame): 包含 PDOS 数据的 DataFrame。(第一列为频率，第二列为每个原子的PDOS)
        频率单位: THz
        DOS单位: 1/(m K)
        PDOS单位: 1/(m K)
        """
        dos_file = self.sheng_folder_path + "/" + dos_file
        pdos_file = self.sheng_folder_path + "/" + pdos_file
        df_dos = pd.read_csv(dos_file, sep=r"\s+", header=None, names=["omega", "DOS"])
        df_dos["omega"] = df_dos["omega"] / (2 * np.pi)
        df_pdos = pd.read_csv(
            pdos_file,
            sep=r"\s+",
            header=None,
            names=["omega"] + [f"atom{i + 1}" for i in range(self.natom)],
        )
        df_pdos["omega"] = df_pdos["omega"] / (2 * np.pi)

        return df_dos, df_pdos

    def get_cv(self, cv_file="BTE.cvVsT"):
        """
        获取热容(CV)数据 DataFrame。

        参数:
        cv_file (str): CV 数据文件的名称，默认为 "BTE.cvVsT"。

        返回:
        df_cv (pd.DataFrame): 包含 CV 数据的 DataFrame。第一列为温度，第二列为CV。
        温度单位: K
        CV单位: J/(m^3 K)
        """
        cv_file = self.sheng_folder_path + "/" + cv_file
        df_cv = pd.read_csv(cv_file, sep=r"\s+", header=None, names=["T", "cv"])
        return df_cv

    def get_kappa_BTE(self, kappa_file="BTE.KappaTensorVsT_CONV"):
        """
        获取BTE计算晶格热导率

        返回:
        df_kappa (pd.DataFrame): 包含晶格热导率数据的 DataFrame。第一列为温度，剩余9列是晶格热导率的9个分量，最后一列是迭代次数。
        温度单位: K
        晶格热导率单位: W/(m K)
        """
        kappa_file = self.sheng_folder_path + "/" + kappa_file
        df_kappa = pd.read_csv(
            kappa_file, sep=r"\s+", header=None, names=["T"] + self.directs + ["iter"]
        )
        return df_kappa

    def get_kappa_RTA(self, kappa_file="BTE.KappaTensorVsT_RTA"):
        """
        获取RTA计算晶格热导率
        返回:
        df_kappa (pd.DataFrame): 包含晶格热导率数据的 DataFrame。第一列为温度，剩余9列是晶格热导率的9个分量，最后一列是迭代次数。
        温度单位: K
        晶格热导率单位: W/(m K)

        """
        kappa_file = self.sheng_folder_path + "/" + kappa_file
        df_kappa = pd.read_csv(
            kappa_file, sep=r"\s+", header=None, names=["T"] + self.directs + ["iter"]
        )
        return df_kappa

    def get_kappa_sg(self, kappa_file="BTE.KappaTensorVsT_SG"):
        """
        thermal conductivity tensor per unit of mean free path in the small-grain limit,
        返回:
        df_kappa (pd.DataFrame): 包含晶格热导率数据的 DataFrame。第一列为温度，剩余9列是晶格热导率的9个分量
        温度单位: K
        晶格热导率单位: W/(m K nm)
        """
        kappa_file = self.sheng_folder_path + "/" + kappa_file
        df_kappa = pd.read_csv(
            kappa_file, sep=r"\s+", header=None, names=["T"] + self.directs
        )
        return df_kappa

    def get_gruneisen(
        self,
        gruneisen_file="BTE.gruneisen",
        total_gruneisen_file="BTE.gruneisenVsT_total",
        if_branch=False,
    ):
        """
        获取gruneisen系数数据 DataFrame。

        参数:
        gruneisen_file (str): gruneisen系数数据文件的名称，默认为 "BTE.gruneisen"。
        total_gruneisen_file (str): 总gruneisen系数数据文件的名称，默认为 "BTE.gruneisenVsT_total"。
        if_branch (bool): 是否返回每个分支的gruneisen系数，默认为 False。

        返回:
        if if_branch:
            df_omega (pd.DataFrame): 包含频率数据的 DataFrame，列名对应不同的声子分支。
            df_gruneisen (pd.DataFrame): 包含gruneisen系数数据的 DataFrame。列名对应不同的声子分支。
            df_total_gruneisen (pd.DataFrame): 包含总gruneisen系数数据的 DataFrame。第一列为温度，第二列为总gruneisen系数。
        else:
            df_combined (pd.DataFrame): 包含omega和gruneisen数据的DataFrame，第一列为omega，第二列为gruneisen。
            df_total_gruneisen (pd.DataFrame): 包含总gruneisen系数数据的 DataFrame。第一列为温度，第二列为总gruneisen系数。
        温度单位: K
        频率单位: THz
        gruneisen系数单位: gamma
        """
        gruneisen_file = self.sheng_folder_path + "/" + gruneisen_file
        total_gruneisen_file = self.sheng_folder_path + "/" + total_gruneisen_file
        df_total_gruneisen = pd.read_csv(
            total_gruneisen_file,
            sep=r"\s+",
            header=None,
            names=["T", "total_gruneisen"],
        )
        df_gruneisen = pd.read_csv(
            gruneisen_file, sep=r"\s+", header=None, names=self.branch
        )
        if if_branch:
            return self.omega, df_gruneisen, df_total_gruneisen
        else:
            df_combined = self._flatten_and_combine(
                self.omega, df_gruneisen, "omega", "gruneisen"
            )
            return df_combined, df_total_gruneisen

    def get_P3(
        self,
        P3_file="BTE.P3",
        P3_plus_file="BTE.P3_plus",
        P3_minus_file="BTE.P3_minus",
        if_branch=False,
    ):
        """
        获取P3数据 DataFrame。

        参数:
        P3_file (str): P3数据文件的名称，默认为 "BTE.P3"。
        P3_plus_file (str): P3_plus数据文件的名称，默认为 "BTE.P3_plus"。
        P3_minus_file (str): P3_minus数据文件的名称，默认为 "BTE.P3_minus"。
        if_branch (bool): 是否返回声子分支数据，默认为 False。

        返回:
        if if_branch:
            df_omega (pd.DataFrame): 包含频率数据的 DataFrame，列名对应不同的声子分支。
            df_P3 (pd.DataFrame): 包含P3数据的 DataFrame。列名对应不同的声子分支。
            df_P3_plus (pd.DataFrame): 包含P3_plus数据的 DataFrame。列名对应不同的声子分支。
            df_P3_minus (pd.DataFrame): 包含P3_minus数据的 DataFrame。列名对应不同的声子分支。

        else:
            df_P3 (pd.DataFrame): 包含P3数据的 DataFrame。第一列为频率，第二列为P3。
            df_P3_plus (pd.DataFrame): 包含P3_plus数据的 DataFrame。第一列为频率，第二列为P3_plus。
            df_P3_minus (pd.DataFrame): 包含P3_minus数据的 DataFrame。第一列为频率，第二列为P3_minus。
        频率单位: THz
        P3单位:
        """
        P3_file = self.sheng_folder_path + "/" + P3_file
        P3_plus_file = self.sheng_folder_path + "/" + P3_plus_file
        P3_minus_file = self.sheng_folder_path + "/" + P3_minus_file
        df_P3 = pd.read_csv(P3_file, sep=r"\s+", header=None, names=self.branch)
        df_P3_plus = pd.read_csv(
            P3_plus_file, sep=r"\s+", header=None, names=self.branch
        )
        df_P3_minus = pd.read_csv(
            P3_minus_file, sep=r"\s+", header=None, names=self.branch
        )
        if if_branch:
            return self.omega, df_P3, df_P3_plus, df_P3_minus
        else:
            df_P3 = self._flatten_and_combine(self.omega, df_P3, "omega", "P3")
            df_P3_plus = self._flatten_and_combine(
                self.omega, df_P3_plus, "omega", "P3_plus"
            )
            df_P3_minus = self._flatten_and_combine(
                self.omega, df_P3_minus, "omega", "P3_minus"
            )
            return df_P3, df_P3_plus, df_P3_minus

    def get_v(self, v_file="BTE.v", if_branch=False):
        """
        获取声子群速度数据 DataFrame。

        参数:
        v_file (str): 声子群速度数据文件的名称，默认为 "BTE.v"。
        if_branch (bool): 是否返回声子分支数据，默认为 False。

        返回:
        if if_branch:
            df_omega (pd.DataFrame): 包含频率数据的 DataFrame，列名对应不同的声子分支。
            df_vx (pd.DataFrame),df_vy (pd.DataFrame),df_vz (pd.DataFrame): 包含声子群速度数据的 DataFrame。列名对应不同的声子分支。
        else:
            df_v (pd.DataFrame): 包含声子群速度数据的 DataFrame。第一列为频率，第二列为声子群速度。
        频率单位: THz
        声子群速度单位: km/s
        """
        v_file = self.sheng_folder_path + "/" + v_file
        df_v = pd.read_csv(v_file, sep=r"\s+", header=None, names=["vx", "vy", "vz"])
        df_vx, df_vy, df_vz = df_v["vx"], df_v["vy"], df_v["vz"]
        if if_branch:
            df_vx = self._split_colums_to_df(df_vx)
            df_vy = self._split_colums_to_df(df_vy)
            df_vz = self._split_colums_to_df(df_vz)
            return self.omega, df_vx, df_vy, df_vz
        else:
            df_v.insert(0, "omega", self.omega.values.flatten(order="F"))
            return df_v

    def _flatten_and_combine(self, data1, data2, name1, name2):
        """内部函数：将两个数据展平并按列优先顺序合并为DataFrame"""
        flat1 = data1.values.flatten("F")
        flat2 = data2.values.flatten("F")
        return pd.DataFrame({name1: flat1, name2: flat2})

    def _split_colums_to_df(self, df_col):
        """内部函数：将DataFrame的列拆分为按照声子分支为列名的新的DataFrame"""
        # 将单列数据按branch数量等分
        total_length = len(df_col)
        branch_count = len(self.branch)
        split_size = total_length // branch_count

        # 创建新的DataFrame，每列为一个branch的数据
        new_df = pd.DataFrame()
        for i, branch_name in enumerate(self.branch):
            start_idx = i * split_size
            end_idx = (i + 1) * split_size if i < branch_count - 1 else total_length
            new_df[branch_name] = df_col.iloc[start_idx:end_idx].values

        return new_df

    def get_w_anharmonic(
        self,
        w_file="BTE.w_anharmonic",
        w_plus_file="BTE.w_anharmonic_plus",
        w_minus_file="BTE.w_anharmonic_minus",
        T=300,
        if_branch=False,
    ):
        """
        获取三声子散射的散射率

        参数:
        w_file (str): 三声子散射的散射率数据文件的名称，默认为 "BTE.w_anharmonic"。
        w_plus_file (str): 三声子散射的散射率数据文件的名称，默认为 "BTE.w_anharmonic_plus"。
        w_minus_file (str): 三声子散射的散射率数据文件的名称，默认为 "BTE.w_anharmonic_minus"。
        T (float): 温度，默认为 300 K。
        if_branch (bool): 是否返回声子分支数据，默认为 False。

        返回:
        if if_branch:
            df_omega (pd.DataFrame): 包含频率数据的 DataFrame，列名对应不同的声子分支。
            df_w (pd.DataFrame): 包含三声子散射的散射率数据的 DataFrame。列名对应不同的声子分支。
            df_w_plus (pd.DataFrame): 包含三声子散射的散射率数据的 DataFrame。列名对应不同的声子分支。
            df_w_minus (pd.DataFrame): 包含三声子散射的散射率数据的 DataFrame。列名对应不同的声子分支。
        else:
            df_w (pd.DataFrame): 包含三声子散射的散射率数据的 DataFrame。第一列为频率，第二列为三声子散射的散射率。
            df_w_plus (pd.DataFrame): 包含三声子散射的散射率数据的 DataFrame。第一列为频率，第二列为三声子散射的散射率。
            df_w_minus (pd.DataFrame): 包含三声子散射的散射率数据的 DataFrame。第一列为频率，第二列为三声子散射的散射率。
        频率单位: THz
        三声子散射的散射率单位: ps^-1
        """
        w_file = self.sheng_folder_path + "/" + f"T{T}K/" + w_file
        w_plus_file = self.sheng_folder_path + "/" + f"T{T}K/" + w_plus_file
        w_minus_file = self.sheng_folder_path + "/" + f"T{T}K/" + w_minus_file
        df_w = pd.read_csv(w_file, sep=r"\s+", header=None, names=["omega", "w"])
        df_w_plus = pd.read_csv(
            w_plus_file, sep=r"\s+", header=None, names=["omega", "w_plus"]
        )
        df_w_minus = pd.read_csv(
            w_minus_file, sep=r"\s+", header=None, names=["omega", "w_minus"]
        )
        df_w["omega"] = df_w["omega"] / (2 * np.pi)
        df_w_plus["omega"] = df_w_plus["omega"] / (2 * np.pi)
        df_w_minus["omega"] = df_w_minus["omega"] / (2 * np.pi)
        if if_branch:
            df_omega = self._split_colums_to_df(df_w["omega"])
            df_w = self._split_colums_to_df(df_w["w"])
            df_w_plus = self._split_colums_to_df(df_w_plus["w_plus"])
            df_w_minus = self._split_colums_to_df(df_w_minus["w_minus"])
            return df_omega, df_w, df_w_plus, df_w_minus
        else:
            return df_w, df_w_plus, df_w_minus

    def get_w(self, w_file="BTE.w", T=300, if_branch=False):
        """
        total zeroth-order scattering rate for each q point and each band

        参数:
        w_file (str): 总散射率数据文件的名称，默认为 "BTE.w"。
        T (float): 温度，默认为 300 K。
        if_branch (bool): 是否返回声子分支数据，默认为 False。

        返回:
        if if_branch:
            df_omega (pd.DataFrame): 包含频率数据的 DataFrame，列名对应不同的声子分支。
            df_w (pd.DataFrame): 包含总零阶散射率数据的 DataFrame。列名对应不同的声子分支。
        else:
            df_w (pd.DataFrame): 包含总零阶散射率数据的 DataFrame。第一列为频率，第二列为总零阶散射率。
        频率单位: THz
        总零阶散射率单位: ps^-1
        """
        w_file = self.sheng_folder_path + "/" + f"T{T}K/" + w_file
        df_w = pd.read_csv(w_file, sep=r"\s+", header=None, names=["omega", "w"])
        df_w["omega"] = df_w["omega"] / (2 * np.pi)
        if if_branch:
            df_omega = self._split_colums_to_df(df_w["omega"])
            df_w = self._split_colums_to_df(df_w["w"])
            return df_omega, df_w
        else:
            return df_w

    def get_w_final(self, w_file="BTE.w_final", T=300, if_branch=False):
        """
        total converged scattering rate for each irreducible q point and each band, in ps<sup>-1</sup>
        总收敛散射率，每个不可约q点和每个带的总收敛散射率，单位为 ps<sup>-1</sup>
        总收敛散射率是指在给定温度下，每个不可约q点和每个带的总散射率的收敛值，单位为 ps<sup>-1</sup>

        参数:
        w_file (str): 总收敛散射率数据文件的名称，默认为 "BTE.w_final"。
        T (float): 温度，默认为 300 K。
        if_branch (bool): 是否返回声子分支数据，默认为 False。
        返回:
        if if_branch:
            df_omega (pd.DataFrame): 包含频率数据的 DataFrame，列名对应不同的声子分支。
            df_w (pd.DataFrame): 包含总收敛散射率数据的 DataFrame。列名对应不同的声子分支。
        else:
            df_w (pd.DataFrame): 包含总收敛散射率数据的 DataFrame。第一列为频率，第二列为总收敛散射率。
        频率单位: THz
        总收敛散射率单位: ps^-1
        """
        w_file = self.sheng_folder_path + "/" + f"T{T}K/" + w_file
        df_w = pd.read_csv(w_file, sep=r"\s+", header=None, names=["omega", "w"])
        df_w["omega"] = df_w["omega"] / (2 * np.pi)
        if if_branch:
            df_omega = self._split_colums_to_df(df_w["omega"])
            df_w = self._split_colums_to_df(df_w["w"])
            return df_omega, df_w
        else:
            return df_w

    def get_WP3(
        self,
        WP3_file="BTE.WP3",
        WP3_plus_file="BTE.WP3_plus",
        WP3_minus_file="BTE.WP3_minus",
        T=300,
        if_branch=False,
    ):
        """
        weighted phase space available for three-phonon processes  (in ps<sup>4</sup>rad<sup>-4</sup> , 2nd column) vs angular frequency (in rad/ps, 1st column) for those modes (q index changes first, and then band index) in the irreducible wedge. See

        参数:
        WP3_file (str): 三声子加权相位空间数据文件的名称，默认为 "BTE.WP3"。
        WP3_plus_file (str): 三声子加权相位空间数据文件的名称，默认为 "BTE.WP3_plus"。
        WP3_minus_file (str): 三声子加权相位空间数据文件的名称，默认为 "BTE.WP3_minus"。
        T (float): 温度，默认为 300 K。
        if_branch (bool): 是否返回声子分支数据，默认为 False。

        返回:
        if if_branch:
            df_omega (pd.DataFrame): 包含频率数据的 DataFrame，列名对应不同的声子分支。
            df_WP3 (pd.DataFrame): 包含三相子加权相位空间数据的 DataFrame。列名对应不同的声子分支。
            df_WP3_plus (pd.DataFrame): 包含三相子加权相位空间数据的 DataFrame。列名对应不同的声子分支。
            df_WP3_minus (pd.DataFrame): 包含三相子加权相位空间数据的 DataFrame。列名对应不同的声子分支。
        else:
            df_WP3 (pd.DataFrame): 包含三相子加权相位空间数据的 DataFrame。第一列为频率，第二列为三相子加权相位空间数据。
            df_WP3_plus (pd.DataFrame): 包含三相子加权相位空间数据的 DataFrame。第一列为频率，第二列为三相子加权相位空间数据。
            df_WP3_minus (pd.DataFrame): 包含三相子加权相位空间数据的 DataFrame。第一列为频率，第二列为三相子加权相位空间数据。
        频率单位: THz
        三相子加权相位空间数据单位: ps^4rad^-4
        """
        WP3_file = self.sheng_folder_path + "/" + f"T{T}K/" + WP3_file
        WP3_plus_file = self.sheng_folder_path + "/" + f"T{T}K/" + WP3_plus_file
        WP3_minus_file = self.sheng_folder_path + "/" + f"T{T}K/" + WP3_minus_file
        df_WP3 = pd.read_csv(WP3_file, sep=r"\s+", header=None, names=["omega", "WP3"])
        df_WP3_plus = pd.read_csv(
            WP3_plus_file, sep=r"\s+", header=None, names=["omega", "WP3_plus"]
        )
        df_WP3_minus = pd.read_csv(
            WP3_minus_file, sep=r"\s+", header=None, names=["omega", "WP3_minus"]
        )
        df_WP3["omega"] = df_WP3["omega"] / (2 * np.pi)
        df_WP3_plus["omega"] = df_WP3_plus["omega"] / (2 * np.pi)
        df_WP3_minus["omega"] = df_WP3_minus["omega"] / (2 * np.pi)
        if if_branch:
            df_omega = self._split_colums_to_df(df_WP3["omega"])
            df_WP3 = self._split_colums_to_df(df_WP3["WP3"])
            df_WP3_plus = self._split_colums_to_df(df_WP3_plus["WP3_plus"])
            df_WP3_minus = self._split_colums_to_df(df_WP3_minus["WP3_minus"])
            return df_omega, df_WP3, df_WP3_plus, df_WP3_minus
        else:
            return df_WP3, df_WP3_plus, df_WP3_minus

    def get_cumulative_kappa_scalar(
        self, kappa_file="BTE.cumulative_kappa_scalar", T=300
    ):
        """
        平均晶格热导率随平均自由程的累积

        参数:
        kappa_file (str): 晶格热导率数据文件的名称，默认为 "BTE.cumulative_kappa_scalar"。
        T (float): 温度，默认为 300 K。
        返回:
        df_kappa (pd.DataFrame): 包含平均晶格热导率数据的 DataFrame。第一列为平均自由程，第二列为平均晶格热导率。
        平均自由程单位: nm
        平均晶格热导率单位: W/mK
        """
        kappa_file = self.sheng_folder_path + "/" + f"T{T}K/" + kappa_file
        df_kappa = pd.read_csv(
            kappa_file, sep=r"\s+", header=None, names=["r", "kappa"]
        )
        return df_kappa

    def get_cumulative_kappa_tensor(
        self, kappa_file="BTE.cumulative_kappa_tensor", T=300
    ):
        """
        晶格热导率张量随平均自由程的累积

        参数:
        kappa_file (str): 晶格热导率数据文件的名称，默认为 "BTE.cumulative_kappa_tensor"。
        T (float): 温度，默认为 300 K。
        返回:
        df_kappa (pd.DataFrame): 包含平均晶格热导率数据的 DataFrame。第一列为平均自由程，其余九列为晶格热导率张量的九个分量。
        平均自由程单位: nm
        平均晶格热导率单位: W/mK
        """
        kappa_file = self.sheng_folder_path + "/" + f"T{T}K/" + kappa_file
        df_kappa = pd.read_csv(
            kappa_file, sep=r"\s+", header=None, names=["r"] + self.directs
        )
        return df_kappa

    def get_cumulative_kappa_tensor_vs_omega(
        self, kappa_file="BTE.cumulative_kappaVsOmega_tensor", T=300
    ):
        """
        晶格热导率张量随频率的累积

        参数:
        kappa_file (str): 晶格热导率数据文件的名称，默认为 "BTE.cumulative_kappa_tensor_vs_omega"。
        T (float): 温度，默认为 300 K。
        返回:
        df_kappa (pd.DataFrame): 包含平均晶格热导率数据的 DataFrame。第一列为频率，其余3列为晶格热导率张量的对角元(xx,yy,zz)。
        df_kappa_derivative (pd.DataFrame): 包含晶格热导率对频率导数数据的 DataFrame。第一列为频率，其余3列为热导率对角元的导数。
        频率单位: THz
        晶格热导率单位: W/mK
        导数单位: W/(mK·THz)
        """
        kappa_file = self.sheng_folder_path + "/" + f"T{T}K/" + kappa_file
        df_kappa = pd.read_csv(
            kappa_file, sep=r"\s+", header=None, names=["omega"] + self.directs
        )
        df_kappa["omega"] = df_kappa["omega"] / (2 * np.pi)
        # 删除非对角元
        df_kappa = df_kappa[["omega", "xx", "yy", "zz"]]

        # 求解晶格热导率随频率的导数与频率的关系
        # 计算每个方向的热导率对频率的导数
        df_kappa_derivative = df_kappa.copy()
        df_kappa_derivative["xx"] = np.gradient(df_kappa["xx"], df_kappa["omega"])
        df_kappa_derivative["yy"] = np.gradient(df_kappa["yy"], df_kappa["omega"])
        df_kappa_derivative["zz"] = np.gradient(df_kappa["zz"], df_kappa["omega"])
        return df_kappa, df_kappa_derivative

    def get_kappa_vs_branch(self, kappa_file="BTE.kappa", T=300):
        """
        获取每个声子分支对晶格热导率的贡献
        参数:
        kappa_file (str): 晶格热导率数据文件的名称，默认为 "BTE.kappa"。
        T (float): 温度，默认为 300 K。
        返回:
        df_kappa (pd.DataFrame): 第一列为声子分支，第二列为xx方向的贡献值，第三列为yy方向的贡献值，第四列为zz方向的贡献值，
        第五列为xx方向的贡献值占比，第六列为yy方向的贡献值占比，第七列为zz方向的贡献值占比。

        晶格热导率单位: W/mK
        贡献值占比单位: %
        """
        kappa_file = self.sheng_folder_path + "/" + f"T{T}K/" + kappa_file
        df_kappa = (
            pd.read_csv(kappa_file, sep=r"\s+", header=None)
            .values[-1, 1:]
            .reshape(-1, 9)
        )
        df_kappa = pd.DataFrame(df_kappa, columns=self.directs)[["xx", "yy", "zz"]]
        df_kappa.insert(0, "branch", self.branch)
        df_kappa["xx_percentage"] = df_kappa["xx"] / df_kappa["xx"].sum() * 100
        df_kappa["yy_percentage"] = df_kappa["yy"] / df_kappa["yy"].sum() * 100
        df_kappa["zz_percentage"] = df_kappa["zz"] / df_kappa["zz"].sum() * 100

        return df_kappa


class ExportBTE(BaseBTE):
    def __init__(self, sheng_folder_path, omega_file="BTE.omega", dim=3):
        super().__init__(sheng_folder_path, omega_file, dim)

    def get_P4(
        self,
        P4_file="BTE.P4",
        P4_plusplus_file="BTE.P4_plusplus",
        P4_plusminus_file="BTE.P4_plusmius",
        P4_minusminus_file="BTE.P4_minusminus",
        if_branch=False,
    ):
        """
        获取P4
        参数:
        P4_file (str): P4数据文件的名称，默认为 "BTE.P4"。
        P4_plusplus_file (str): P4++数据文件的名称，默认为 "BTE.P4_plusplus"。
        P4_plusminus_file (str): P4+-数据文件的名称，默认为 "BTE.P4_plusmius"。
        P4_minusminus_file (str): P4--数据文件的名称，默认为 "BTE.P4_minusminus"。
        if_branch (bool): 是否返回每个声子分支的贡献，默认为 False。
        返回:
        if if_branch:
            df_omega (pd.DataFrame): 包含频率数据的 DataFrame，列名对应不同的声子分支。
            df_P4 (pd.DataFrame): 包含P4数据的 DataFrame。列名对应不同的声子分支。
            df_P4_plusplus (pd.DataFrame): 包含P4++数据的 DataFrame。列名对应不同的声子分支。
            df_P4_plusminus (pd.DataFrame): 包含P4+-数据的 DataFrame。列名对应不同的声子分支。
            df_P4_minusminus (pd.DataFrame): 包含P4--数据的 DataFrame。列名对应不同的声子分支。
        else:
            df_P4 (pd.DataFrame): 包含P4数据的 DataFrame。第一列为频率，第二列为P4。
            df_P4_plusplus (pd.DataFrame): 包含P4++数据的 DataFrame。第一列为频率，第二列为P4++。
            df_P4_plusminus (pd.DataFrame): 包含P4+-数据的 DataFrame。第一列为频率，第二列为P4+-。
            df_P4_minusminus (pd.DataFrame): 包含P4--数据的 DataFrame。第一列为频率，第二列为P4--。
        频率单位: THz
        P4单位:
        """
        P4_file = self.sheng_folder_path + "/" + P4_file
        P4_plusplus_file = self.sheng_folder_path + "/" + P4_plusplus_file
        P4_plusminus_file = self.sheng_folder_path + "/" + P4_plusminus_file
        P4_minusminus_file = self.sheng_folder_path + "/" + P4_minusminus_file
        df_P4 = pd.read_csv(P4_file, sep=r"\s+", header=None, names=self.branch)
        df_P4_plusplus = pd.read_csv(
            P4_plusplus_file, sep=r"\s+", header=None, names=self.branch
        )
        df_P4_plusminus = pd.read_csv(
            P4_plusminus_file, sep=r"\s+", header=None, names=self.branch
        )
        df_P4_minusminus = pd.read_csv(
            P4_minusminus_file, sep=r"\s+", header=None, names=self.branch
        )
        if if_branch:
            return self.omega, df_P4, df_P4_plusplus, df_P4_plusminus, df_P4_minusminus
        else:
            df_P4 = self._flatten_and_combine(self.omega, df_P4, "omega", "P4")
            df_P4_plusplus = self._flatten_and_combine(
                self.omega, df_P4_plusplus, "omega", "P4_plusplus"
            )
            df_P4_plusminus = self._flatten_and_combine(
                self.omega, df_P4_plusminus, "omega", "P4_plusminus"
            )
            df_P4_minusminus = self._flatten_and_combine(
                self.omega, df_P4_minusminus, "omega", "P4_minusminus"
            )
            return df_P4, df_P4_plusplus, df_P4_plusminus, df_P4_minusminus

    def get_w_3ph(
        self,
        w_file="BTE.w_3ph",
        w_plus_file="BTE.w_3ph_plus",
        w_minus_file="BTE.w_3ph_minus",
        T=300,
        if_branch=False,
    ):
        """
        获取三声子散射的散射率

        参数:
        w_file (str): 三声子散射的散射率数据文件的名称，默认为 "BTE.w_3ph"。
        w_plus_file (str): 三声子散射的散射率数据文件的名称，默认为 "BTE.w_3ph_plus"。
        w_minus_file (str): 三声子散射的散射率数据文件的名称，默认为 "BTE.w_3ph_minus"。
        T (float): 温度，默认为 300 K。
        if_branch (bool): 是否返回声子分支数据，默认为 False。

        返回:
        if if_branch:
            df_omega (pd.DataFrame): 包含频率数据的 DataFrame，列名对应不同的声子分支。
            df_w (pd.DataFrame): 包含三声子散射的散射率数据的 DataFrame。列名对应不同的声子分支。
            df_w_plus (pd.DataFrame): 包含三声子散射的散射率数据的 DataFrame。列名对应不同的声子分支。
            df_w_minus (pd.DataFrame): 包含三声子散射的散射率数据的 DataFrame。列名对应不同的声子分支。
        else:
            df_w (pd.DataFrame): 包含三声子散射的散射率数据的 DataFrame。第一列为频率，第二列为三声子散射的散射率。
            df_w_plus (pd.DataFrame): 包含三声子散射的散射率数据的 DataFrame。第一列为频率，第二列为三声子散射的散射率。
            df_w_minus (pd.DataFrame): 包含三声子散射的散射率数据的 DataFrame。第一列为频率，第二列为三声子散射的散射率。
        频率单位: THz
        三声子散射的散射率单位: ps^-1
        """
        return self.get_w_anharmonic(
            w_file=w_file,
            w_plus_file=w_plus_file,
            w_minus_file=w_minus_file,
            T=T,
            if_branch=if_branch,
        )

    def get_w_4ph(
        self,
        w_4ph_file="BTE.w_4ph",
        w_4ph_normal_file="BTE.w_4ph_normal",
        w_4ph_Umklapp_file="BTE.w_4ph_Umklapp",
        w_4ph_plusplus_file="BTE.w_4ph_plusplus",
        w_4ph_plusminus_file="BTE.w_4ph_plusminus",
        w_4ph_minusminus_file="BTE.w_4ph_minusminus",
        T=300,
        if_branch=False,
    ):
        """
        获取四声子散射率及有关过程的四声子散射率
        参数:
        w_4ph_file (str): w_4ph数据文件的名称，默认为 "BTE.w_4ph"。
        w_4ph_normal_file (str): w_4ph_normal数据文件的名称，默认为 "BTE.w_4ph_normal"。
        w_4ph_Umklapp_file (str): w_4ph_Umklapp数据文件的名称，默认为 "BTE.w_4ph_Umklapp"。
        w_4ph_plusplus_file (str): w_4ph_plusplus数据文件的名称，默认为 "BTE.w_4ph_plusplus"。
        w_4ph_plusminus_file (str): w_4ph_plusminus数据文件的名称，默认为 "BTE.w_4ph_plusminus"。
        w_4ph_minusminus_file (str): w_4ph_minusminus数据文件的名称，默认为 "BTE.w_4ph_minusminus"。
        if_branch (bool): 是否返回每个声子分支的贡献，默认为 False。
        返回:
        if if_branch:
            df_omega (pd.DataFrame): 包含频率数据的 DataFrame，列名对应不同的声子分支。
            df_w_4ph (pd.DataFrame): 包含w_4ph数据的 DataFrame。列名对应不同的声子分支。
            df_w_4ph_normal (pd.DataFrame): 包含w_4ph_normal数据的 DataFrame。列名对应不同的声子分支。
            df_w_4ph_Umklapp (pd.DataFrame): 包含w_4ph_Umklapp数据的 DataFrame。列名对应不同的声子分支。
            df_w_4ph_plusplus (pd.DataFrame): 包含w_4ph_plusplus数据的 DataFrame。列名对应不同的声子分支。
            df_w_4ph_plusminus (pd.DataFrame): 包含w_4ph_plusminus数据的 DataFrame。列名对应不同的声子分支。
            df_w_4ph_minusminus (pd.DataFrame): 包含w_4ph_minusminus数据的 DataFrame。列名对应不同的声子分支。
        else:
            df_w_4ph (pd.DataFrame):第一列是频率，第二列是w_4ph
            df_w_4ph_normal (pd.DataFrame): 包含w_4ph_normal数据的 DataFrame。第一列为频率，第二列为w_4ph_normal。
            df_w_4ph_Umklapp (pd.DataFrame): 包含w_4ph_Umklapp数据的 DataFrame。第一列为频率，第二列为w_4ph_Umklapp。
            df_w_4ph_plusplus (pd.DataFrame): 包含w_4ph_plusplus数据的 DataFrame。第一列为频率，第二列为w_4ph_plusplus。
            df_w_4ph_plusminus (pd.DataFrame): 包含w_4ph_plusminus数据的 DataFrame。第一列为频率，第二列为w_4ph_plusminus。
            df_w_4ph_minusminus (pd.DataFrame): 包含w_4ph_minusminus数据的 DataFrame。第一列为频率，第二列为w_4ph_minusminus。
        频率单位: THz
        w_4ph单位: ps^-1
        """
        w_4ph_file = self.sheng_folder_path + "/" + f"T{T}K/" + w_4ph_file
        w_4ph_normal_file = self.sheng_folder_path + "/" + f"T{T}K/" + w_4ph_normal_file
        w_4ph_Umklapp_file = (
            self.sheng_folder_path + "/" + f"T{T}K/" + w_4ph_Umklapp_file
        )
        w_4ph_plusplus_file = (
            self.sheng_folder_path + "/" + f"T{T}K/" + w_4ph_plusplus_file
        )
        w_4ph_plusminus_file = (
            self.sheng_folder_path + "/" + f"T{T}K/" + w_4ph_plusminus_file
        )
        w_4ph_minusminus_file = (
            self.sheng_folder_path + "/" + f"T{T}K/" + w_4ph_minusminus_file
        )
        df_w_4ph = pd.read_csv(
            w_4ph_file, sep=r"\s+", header=None, names=["omega", "w_4ph"]
        )
        df_w_4ph_normal = pd.read_csv(
            w_4ph_normal_file,
            sep=r"\s+",
            header=None,
            names=[
                "omega",
                "recombination",
                "redistribution",
                "splitting",
                "w_4ph_normal",
            ],
        )
        df_w_4ph_Umklapp = pd.read_csv(
            w_4ph_Umklapp_file,
            sep=r"\s+",
            header=None,
            names=[
                "omega",
                "recombination",
                "redistribution",
                "splitting",
                "w_4ph_Umklapp",
            ],
        )
        df_w_4ph_plusplus = pd.read_csv(
            w_4ph_plusplus_file,
            sep=r"\s+",
            header=None,
            names=["omega", "w_4ph_plusplus"],
        )
        df_w_4ph_plusminus = pd.read_csv(
            w_4ph_plusminus_file,
            sep=r"\s+",
            header=None,
            names=["omega", "w_4ph_plusminus"],
        )
        df_w_4ph_minusminus = pd.read_csv(
            w_4ph_minusminus_file,
            sep=r"\s+",
            header=None,
            names=["omega", "w_4ph_minusminus"],
        )
        # 转换omega
        df_w_4ph["omega"] = df_w_4ph["omega"] / (2 * np.pi)
        df_w_4ph_normal["omega"] = df_w_4ph_normal["omega"] / (2 * np.pi)
        df_w_4ph_Umklapp["omega"] = df_w_4ph_Umklapp["omega"] / (2 * np.pi)
        df_w_4ph_plusplus["omega"] = df_w_4ph_plusplus["omega"] / (2 * np.pi)
        df_w_4ph_plusminus["omega"] = df_w_4ph_plusminus["omega"] / (2 * np.pi)
        df_w_4ph_minusminus["omega"] = df_w_4ph_minusminus["omega"] / (2 * np.pi)
        if if_branch:
            df_omega = self._split_colums_to_df(df_w_4ph["omega"])
            df_w_4ph = self._split_colums_to_df(df_w_4ph["w_4ph"])
            df_w_4ph_normal = self._split_colums_to_df(df_w_4ph_normal["w_4ph_normal"])
            df_w_4ph_Umklapp = self._split_colums_to_df(
                df_w_4ph_Umklapp["w_4ph_Umklapp"]
            )
            df_w_4ph_plusplus = self._split_colums_to_df(
                df_w_4ph_plusplus["w_4ph_plusplus"]
            )
            df_w_4ph_plusminus = self._split_colums_to_df(
                df_w_4ph_plusminus["w_4ph_plusminus"]
            )
            df_w_4ph_minusminus = self._split_colums_to_df(
                df_w_4ph_minusminus["w_4ph_minusminus"]
            )
            return (
                df_omega,
                df_w_4ph,
                df_w_4ph_normal,
                df_w_4ph_Umklapp,
                df_w_4ph_plusplus,
                df_w_4ph_plusminus,
                df_w_4ph_minusminus,
            )
        else:
            return (
                df_w_4ph,
                df_w_4ph_normal,
                df_w_4ph_Umklapp,
                df_w_4ph_plusplus,
                df_w_4ph_plusminus,
                df_w_4ph_minusminus,
            )

    def get_WP4(
        self,
        WP4_file="BTE.WP4",
        WP4_plusplus_file="BTE.WP4_plusplus",
        WP4_plusminus_file="BTE.WP4_plusminus",
        WP4_minusminus_file="BTE.WP4_minusminus",
        T=300,
        if_branch=False,
    ):
        """
        weighted phase space available for four-phonon processes  (in ps<sup>4</sup>rad<sup>-4</sup> , 2nd column) vs angular frequency (in rad/ps, 1st column) for those modes (q index changes first, and then band index) in the irreducible wedge. See

        参数:
        WP4_file (str): 三相子加权相位空间数据文件的名称，默认为 "BTE.WP4"。
        WP4_plusplus_file (str): 三相子加权相位空间数据文件的名称，默认为 "BTE.WP4_plusplus"。
        WP4_plusminus_file (str): 三相子加权相位空间数据文件的名称，默认为 "BTE.WP4_plusminus"。
        WP4_minusminus_file (str): 三相子加权相位空间数据文件的名称，默认为 "BTE.WP4_minuxminus"。
        T (float): 温度，默认为 300 K。
        if_branch (bool): 是否返回声子分支数据，默认为 False。

        返回:
        if if_branch:
            df_omega (pd.DataFrame): 包含频率数据的 DataFrame，列名对应不同的声子分支。
            df_WP4 (pd.DataFrame): 包含四相子加权相位空间数据的 DataFrame。列名对应不同的声子分支
            df_WP4_plusplus (pd.DataFrame): 包含四相子加权相位空间数据的 DataFrame。列名对应不同的声子分支
            df_WP4_plusminus (pd.DataFrame): 包含四相子加权相位空间数据的 DataFrame。列名对应不同的声子分支
            df_WP4_minusminus (pd.DataFrame): 包含四相子加权相位空间数据的 DataFrame。列名对应不同的声子分支
        else:
            df_WP4 (pd.DataFrame): 包含四相子加权相位空间数据的 DataFrame。第一列为频率，第二列为四相子加权相位空间数据。
            df_WP4_plusplus (pd.DataFrame): 包含四相子加权相位空间数据的 DataFrame。第一列为频率，第二列为四相子加权相位空间数据。
            df_WP4_plusminus (pd.DataFrame): 包含四相子加权相位空间数据的 DataFrame。第一列为频率，第二列为四相子加权相位空间数据。
            df_WP4_minusminus (pd.DataFrame): 包含四相子加权相位空间数据的 DataFrame。第一列为频率，第二列为四相子加权相位空间数据。
        频率单位: THz
        四相子加权相位空间数据单位: ps^4rad^-4
        """
        WP4_file = self.sheng_folder_path + "/" + f"T{T}K/" + WP4_file
        WP4_plusplus_file = self.sheng_folder_path + "/" + f"T{T}K/" + WP4_plusplus_file
        WP4_plusminus_file = (
            self.sheng_folder_path + "/" + f"T{T}K/" + WP4_plusminus_file
        )
        WP4_minusminus_file = (
            self.sheng_folder_path + "/" + f"T{T}K/" + WP4_minusminus_file
        )
        df_WP4 = pd.read_csv(WP4_file, sep=r"\s+", header=None, names=["omega", "WP4"])
        df_WP4_plusplus = pd.read_csv(
            WP4_plusplus_file, sep=r"\s+", header=None, names=["omega", "WP4_plusplus"]
        )
        df_WP4_plusminus = pd.read_csv(
            WP4_plusminus_file,
            sep=r"\s+",
            header=None,
            names=["omega", "WP4_plusminus"],
        )
        df_WP4_minusminus = pd.read_csv(
            WP4_minusminus_file,
            sep=r"\s+",
            header=None,
            names=["omega", "WP4_minusminus"],
        )
        df_WP4["omega"] = df_WP4["omega"] / (2 * np.pi)
        df_WP4_plusplus["omega"] = df_WP4_plusplus["omega"] / (2 * np.pi)
        df_WP4_plusminus["omega"] = df_WP4_plusminus["omega"] / (2 * np.pi)
        df_WP4_minusminus["omega"] = df_WP4_minusminus["omega"] / (2 * np.pi)
        if if_branch:
            df_omega = self._split_colums_to_df(df_WP4["omega"])
            df_WP4 = self._split_colums_to_df(df_WP4["WP4"])
            df_WP4_plusplus = self._split_colums_to_df(df_WP4_plusplus["WP4_plusplus"])
            df_WP4_plusminus = self._split_colums_to_df(
                df_WP4_plusminus["WP4_plusminus"]
            )
            df_WP4_minusminus = self._split_colums_to_df(
                df_WP4_minusminus["WP4_minusminus"]
            )
            return (
                df_omega,
                df_WP4,
                df_WP4_plusplus,
                df_WP4_plusminus,
                df_WP4_minusminus,
            )
        else:
            return df_WP4, df_WP4_plusplus, df_WP4_plusminus, df_WP4_minusminus
