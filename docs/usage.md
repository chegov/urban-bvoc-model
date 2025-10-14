```markdown
# Usage — urban-bvoc-model

1. 安装依赖：
   pip install -r requirements.txt

2. 运行示例：
   python examples/run_example.py

3. 自定义输入：
   - 气象 CSV: data/sample_inputs/met_hourly.csv（timestamp, T_C, PAR, precip_mm, irrigation_mm, RH, wind_m_s）
   - LAI: 可使用 GeoTIFF 或示例脚本生成的 LAI 矩阵（examples/run_example.py）
   - PFT/EF: pft_lookup.csv 和 pft_map.csv 用于将像元的植被类型映射到 EF

4. 结果：
   - 输出 NetCDF 文件：包含坐标 (time, y, x) 和变量 `bvoc_emission`，单位 µg C m^-2 h^-1

5. 接入生产流程：
   - 将输出映射到化学模式的 VOC speciation（例如 isoprene -> 模式中的 isoprene 类）
   - 时间同步至小时分辨率或向下聚合
