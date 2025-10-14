"""
bvoc_model.py

最小可运行 BVOC 排放原型实现（按像元、按小时）。
实现公式：
 E = EF * LAI * gamma_T(T) * gamma_L(PAR) * gamma_SM(theta) * f_phen(DOY) * f_urban

输出单位： µg C m^-2 h^-1
"""

import numpy as np
import pandas as pd
import xarray as xr
from datetime import datetime


# ---------- 生理/环境响应函数 ----------
def temp_response(T_C, T_ref=30.0, Ea=70000.0):
    """
    温度响应，Arrhenius 形式（基于示例）
    T_C: 摄氏度或数组
    Ea: 活化能 J mol^-1（典型 50-100 kJ mol^-1）
    返回无量纲响应 gamma_T
    """
    R = 8.314  # J mol-1 K-1
    T = T_C + 273.15
    T0 = T_ref + 273.15
    # 避免 overflow
    exponent = (Ea / R) * (1.0 / T0 - 1.0 / T)
    exponent = np.clip(exponent, -700, 700)
    return np.exp(exponent)


def light_response(PAR, K_L=200.0):
    """
    光响应：Michaelis-Menten 型
    PAR: µmol m^-2 s^-1
    K_L: 半饱和常数
    """
    PAR = np.maximum(PAR, 0.0)
    return PAR / (PAR + K_L)


def soil_moisture_response(theta, theta_min=0.05, theta_opt=0.25, kind="piecewise"):
    """
    土壤含水响应，θ 为体积含水量（0-1）
    返回 0-1 的抑制/激活因子
    """
    if kind == "sigmoid":
        a = 30.0
        theta0 = theta_opt * 0.6
        return 1.0 / (1.0 + np.exp(-a * (theta - theta0)))
    else:
        # piecewise linear
        gamma = np.zeros_like(theta, dtype=float)
        gamma = np.where(theta <= theta_min, 0.0, gamma)
        mask = (theta > theta_min) & (theta < theta_opt)
        gamma = np.where(mask, (theta - theta_min) / (theta_opt - theta_min), gamma)
        gamma = np.where(theta >= theta_opt, 1.0, gamma)
        return gamma


def phenology_factor(doy, LAI, LAI_max=6.0):
    """
    季节因子：基于实际 LAI / LAI_max
    doy: day of year (unused explicitly here, kept for extensibility)
    LAI: 当前像元 LAI
    """
    LAI_max_arr = np.maximum(LAI_max, 0.1)
    return np.clip(LAI / LAI_max_arr, 0.0, 1.0)


def urban_factor(irrigation_flag=0, impervious_frac=0.0, deltaT_uhi=0.0,
                 alpha_irr=0.15, beta_imp=0.1, gamma_uhi=0.05):
    """
    城市修正因子示例（线性组合）
    返回 f_urban >= 0
    """
    return 1.0 + alpha_irr * irrigation_flag - beta_imp * impervious_frac + gamma_uhi * deltaT_uhi


# ---------- 简化土壤水量桶模型 ----------
def bucket_soil_model(theta0, precip_mm, evap_mm, field_capacity=0.35, porosity=0.45, area_m2=1.0):
    """
    非厌氧的简单单层桶模型（逐小时/日更新）
    theta0: 初始体积含水量（0-porosity）
    precip_mm: 当期降水（mm）
    evap_mm: 蒸散损失（mm）
    返回 theta_new, fluxes (in mm)
    """
    # 把体积含水量转换到 mm（假设根域深度为 100 mm * porosity? 这里使用根系深度 100 mm 作为示例）
    root_depth_mm = 100.0  # example root zone depth
    water_mm = theta0 * root_depth_mm
    water_mm += np.maximum(precip_mm, 0.0)
    water_mm -= np.maximum(evap_mm, 0.0)
    # 底部回渗裁剪（不考虑地下水补给）
    max_water_mm = porosity * root_depth_mm
    water_mm = np.clip(water_mm, 0.0, max_water_mm)
    theta_new = water_mm / root_depth_mm
    return theta_new


# ---------- 主计算函数 ----------
def compute_emission(EF, LAI, T_C, PAR, theta, doy,
                     irrigation_flag=0, impervious_frac=0.0, deltaT_uhi=0.0,
                     species="isoprene"):
    """
    计算单像元单时刻的排放（µg C m^-2 h^-1）
    EF: 基线排放因子（µg C m^-2 h^-1 / LAI?  —— 以 EF 为像元在参考条件下每单位 LAI 的释放速率）
    LAI: 叶面积指数（m2 leaf m-2 ground）
    T_C, PAR, theta: 环境变量
    doy: day of year
    返回 E
    """
    gamma_T = temp_response(T_C)
    if species.lower() in ["isoprene"]:
        gamma_L = light_response(PAR)
    else:
        gamma_L = 1.0  # 非光依赖化合物简化
    gamma_SM = soil_moisture_response(theta)
    f_phen = phenology_factor(doy, LAI)
    f_urban = urban_factor(irrigation_flag=irrigation_flag,
                           impervious_frac=impervious_frac,
                           deltaT_uhi=deltaT_uhi)
    E = EF * LAI * gamma_T * gamma_L * gamma_SM * f_phen * f_urban
    # 保证非负
    E = np.maximum(E, 0.0)
    return E


# ---------- 批量栅格计算（简化） ----------
def grid_emissions(EF_grid, LAI_grid, T_C_series, PAR_series, theta_grid,
                   times, pft_grid=None, irrigation_grid=None, imperv_grid=None,
                   deltaT_uhi_grid=None, species="isoprene"):
    """
    计算整张栅格（nrows, ncols）在 times（长度 nt）上的排放。
    EF_grid, LAI_grid, theta_grid, pft_grid, irrigation_grid, imperv_grid, deltaT_uhi_grid: 2D arrays
    T_C_series, PAR_series: 1D arrays 长度 nt
    times: pandas.DatetimeIndex 长度 nt
    返回 xarray.DataArray: dims (time, y, x)
    """
    ny, nx = LAI_grid.shape
    nt = len(times)
    data = np.zeros((nt, ny, nx), dtype=float)
    # time loop（可改为向量化/并行）
    for i, t in enumerate(times):
        T = T_C_series[i]
        PAR = PAR_series[i]
        doy = t.timetuple().tm_yday
        # 对整个栅格批量计算
        gamma_T = temp_response(T)
        if species.lower() in ["isoprene"]:
            gamma_L = light_response(PAR)
        else:
            gamma_L = 1.0
        gamma_SM = soil_moisture_response(theta_grid)
        f_phen = phenology_factor(doy, LAI_grid)
        irrigation_flag = irrigation_grid if irrigation_grid is not None else np.zeros_like(LAI_grid)
        imperv = imperv_grid if imperv_grid is not None else np.zeros_like(LAI_grid)
        deltaT = deltaT_uhi_grid if deltaT_uhi_grid is not None else np.zeros_like(LAI_grid)
        f_urban = urban_factor(irrigation_flag=irrigation_flag,
                               impervious_frac=imperv,
                               deltaT_uhi=deltaT)
        E = EF_grid * LAI_grid * gamma_T * gamma_L * gamma_SM * f_phen * f_urban
        data[i, :, :] = np.maximum(E, 0.0)
    da = xr.DataArray(data,
                      coords={"time": times, "y": np.arange(ny), "x": np.arange(nx)},
                      dims=("time", "y", "x"))
    da.attrs["units"] = "ug C m^-2 h^-1"
    return da
