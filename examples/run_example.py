"""
run_example.py

使用合成数据运行原型模型并保存结果为 NetCDF。
会在 examples/output/ 目录下创建输出文件。
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.bvoc_model import grid_emissions, bucket_soil_model
from src.io_utils import create_lai_geotiff, read_met_csv, save_emissions_netcdf

DATA_DIR = "data/sample_inputs"
OUT_DIR = "examples/output"
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

def make_synthetic_met(start_time, hours=24):
    times = pd.date_range(start_time, periods=hours, freq="H")
    # diurnal T and PAR patterns
    hour = times.hour.values
    T = 20 + 8 * np.sin((hour - 6) / 24 * 2 * np.pi)  # simple diurnal
    PAR = np.maximum(0, 1200 * np.sin((hour - 6) / 24 * 2 * np.pi))
    precip = np.zeros_like(hour, dtype=float)
    # small rain at hour 6
    precip[6] = 5.0
    irrigation = np.zeros_like(hour)
    df = pd.DataFrame({
        "timestamp": times,
        "T_C": T,
        "PAR": PAR,
        "precip_mm": precip,
        "irrigation_mm": irrigation,
        "RH": 60.0,
        "wind_m_s": 2.0
    })
    met_csv = os.path.join(DATA_DIR, "met_hourly.csv")
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(met_csv, index=False)
    return met_csv, times

def main():
    # --- prepare synthetic inputs ---
    met_csv, times = make_synthetic_met(datetime(2025, 6, 1, 0, 0), hours=24)
    met = read_met_csv(met_csv)
    # small grid 4x4
    ny, nx = 4, 4
    LAI_grid = np.array([
        [1.0, 2.0, 2.5, 1.0],
        [1.0, 3.0, 3.5, 1.5],
        [0.5, 2.0, 2.0, 1.0],
        [0.2, 0.5, 1.0, 0.8]
    ], dtype=float)
    # create LAI geotiff for demo (optional)
    lai_tif = os.path.join(DATA_DIR, "lai_demo.tif")
    create_lai_geotiff(lai_tif, LAI_grid, xres=10.0, yres=10.0, x0=0.0, y0=0.0)

    # Emission factor grid (EF) — example: uniform EF per LAI unit (µg C m^-2 h^-1 per LAI)
    EF_grid = np.full((ny, nx), 10.0)  # baseline EF

    # initial soil theta grid (example)
    theta_grid = np.full((ny, nx), 0.22)

    # optional city modifiers
    irrigation_grid = np.zeros((ny, nx))
    irrigation_grid[0, :] = 1  # simulate irrigated row
    imperv_grid = np.zeros((ny, nx))
    imperv_grid[:, 0] = 0.4     # some impervious fraction in first column
    deltaT_grid = np.full((ny, nx), 1.5)  # simple UHI +1.5C

    # run grid emissions
    T_series = met["T_C"].values
    PAR_series = met["PAR"].values

    da = grid_emissions(EF_grid, LAI_grid, T_series, PAR_series, theta_grid,
                        times=times,
                        irrigation_grid=irrigation_grid,
                        imperv_grid=imperv_grid,
                        deltaT_uhi_grid=deltaT_grid,
                        species="isoprene")

    out_nc = os.path.join(OUT_DIR, "bvoc_emissions_demo.nc")
    save_emissions_netcdf(da, out_nc)
    print("Saved emissions to:", out_nc)
    print("Example run complete. Inspect the NetCDF with xarray or ncdump.")


if __name__ == "__main__":
    main()
