io_utils.py

轻量级输入/输出：CSV 气象、简单栅格（使用 numpy/rasterio 生成/读取）和 NetCDF 输出。
"""

import os
import numpy as np
import pandas as pd
import xarray as xr
import rasterio
from rasterio.transform import from_origin


def read_met_csv(path):
    """
    读取示例格式的气象 CSV：
    timestamp,T_C,PAR,precip_mm,irrigation_mm,RH,wind_m_s
    返回 pandas.DataFrame（索引为 datetime）
    """
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.set_index("timestamp").sort_index()
    return df


def save_emissions_netcdf(da, path):
    """
    保存 xarray.DataArray 到 NetCDF
    """
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    ds = da.to_dataset(name="bvoc_emission")
    ds.to_netcdf(path)
    return path


def create_lai_geotiff(path, LAI_grid, xres=10.0, yres=10.0, x0=0.0, y0=0.0, crs="EPSG:4326"):
    """
    创建一个简单的 GeoTIFF（小型示例），用于示例脚本。
    LAI_grid: 2D numpy array
    """
    ny, nx = LAI_grid.shape
    transform = from_origin(x0, y0, xres, yres)
    dtype = rasterio.float32
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=ny,
        width=nx,
        count=1,
        dtype=dtype,
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(LAI_grid.astype(dtype), 1)
    return path


def read_lai_geotiff(path):
    with rasterio.open(path) as src:
        arr = src.read(1)
    return arr
