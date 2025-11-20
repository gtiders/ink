"""
SciPlots - Matplotlib样式管理器
提供基础和高阶的matplotlib样式设置功能
"""

import matplotlib.pyplot as plt
from cycler import cycler


class SciPlotsStyle:
    """
    基础Matplotlib样式配置器
    提供基础的plt.rc参数设置
    """
    
    def __init__(self):
        """初始化基础样式配置器"""
        self._original_rc = {}
        self._current_style = {}
        self._backup_rc_params()
        self.set_basic_params()

        
    def _backup_rc_params(self):
        """备份当前的rc参数"""
        self._original_rc = plt.rcParams.copy()
        
    def reset_to_default(self):
        """重置到默认的matplotlib样式"""
        plt.rcParams.update(self._original_rc)
        self._current_style = {}
        
    def set_basic_params(self):
        """设置基础参数 - 最常用的rc设置"""
        # 字体设置 - 使用STIX Two Math
        plt.rc('font', family='STIX Two Math', size=10.5, weight='normal')
        plt.rc('axes', unicode_minus=False)
        
        # 数学字体设置
        plt.rc('mathtext', 
               fontset='custom',
               rm='STIX Two Math',
               default='rm',
               fallback='cm')
        
        # 颜色循环设置
        colors = [
            "#55B7E6",
            "#56BA77",
            "#ED6E69",
            "#9FAA3F",
            "#BD79B6"
        ]

        plt.rc('axes', prop_cycle=cycler('color', colors))
        
        # 线条设置
        plt.rc('lines', linewidth=1.0, markersize=6)
        plt.rc('axes', linewidth=0.5)
        plt.rc('grid', linewidth=0.5, linestyle='--')
        
        # X轴刻度设置
        plt.rc('xtick', direction='in', top=True)
        plt.rc('xtick.major', size=3, width=0.5)
        plt.rc('xtick.minor', size=1.5, width=0.5, visible=True)
        
        # Y轴刻度设置
        plt.rc('ytick', direction='in', right=True)
        plt.rc('ytick.major', size=3, width=0.5)
        plt.rc('ytick.minor', size=1.5, width=0.5, visible=True)
        
        # 轴设置
        plt.rc('axes.spines', top=True, right=True)
        
        # 图例设置
        plt.rc('legend', 
               loc='upper left',
               frameon=False,
               markerscale=1.0,
               handlelength=1.0,
               handletextpad=0.5,
               fontsize=11)
        
        # 图形设置
        plt.rc('figure', figsize=(6.4, 4.8))
        
        # 子图布局设置
        plt.rc('figure.subplot', left=0.25, right=0.75, bottom=0.25, top=0.75)
        
        # 保存设置
        plt.rc('savefig', bbox='tight', pad_inches=0.05, dpi=300)

