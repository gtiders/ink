import numpy as np
import matplotlib.pyplot as plt
# import pylustrator
# pylustrator.start()
# import lazykit.eggs.matplotlib_eggs
# plt.style.use('science')

# #导入数据
w_anharmonic = np.loadtxt(
    "/cache/ybgao2024/K3-Rb3-Au3Sb2/result/K3Au3Sb2/sheng80/4th_test_sample/300K_scph/T300K/BTE.w_4ph"
)

omega = w_anharmonic[:, 0]  # cm^-1
lifetime = 1 / w_anharmonic[:, 1]  # ps
omega_max = np.max(w_anharmonic[:, 0])
omega_min = np.min(w_anharmonic[:, 0])
delta_omega = 24 / omega_max


def omega_to_lifetime(omega_min, omega_max):
    return np.linspace(omega_min, omega_max, 1000), 1 / np.linspace(
        omega_min, omega_max, 1000
    )


fig, ax1 = plt.subplots(1, 1)
# 填充颜色
# 在delta_omega横线上方填充颜色
ax1.axhspan(delta_omega, 1e3, facecolor="#D8B365", alpha=0.3)
# 在声子频率倒数的下方填充颜色
x_fill, y_fill = omega_to_lifetime(omega_min, 40)
ax1.fill_between(x_fill, y_fill, 1e-2, facecolor="#5BB5AC", alpha=0.3)
# 在delta_omega横线下方和声子频率倒数的之间填充颜色#DE526C
ax1.fill_between(
    x_fill,
    y_fill,
    delta_omega,
    where=(y_fill < delta_omega),
    facecolor="#DE526C",
    alpha=0.3,
)

# 先绘制线条
ax1.axhline(delta_omega, color="black", linestyle="--")
ax1.plot(
    omega_to_lifetime(omega_min, 40)[0],
    omega_to_lifetime(omega_min, 40)[1],
    color="black",
    linestyle="--",
)

# 最后绘制散点图(会覆盖在之前的图形上方)
ax1.scatter(omega, lifetime, label="300K", s=4, zorder=3)  # 添加zorder确保在最上层
# ax1.scatter(omega,1/w_anharmonic_900[:,1],label='900K',s=4, zorder=3)
ax1.set_yscale("log")
ax1.set_xlabel("Frequency (cm$^{-1}$)")
ax1.set_ylabel("Phonon Lifetime (ps)")
ax1.set_xlim(0, 40)
ax1.set_ylim(1e-2, 1e3)

# plt.show()
plt.savefig("figure1.png")
