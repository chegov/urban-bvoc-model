# urban-bvoc-model

最小可运行原型：基于城市水热变化诱导的城市森林 BVOC 排放模型。

功能概览
- 小型 Python 原型，实现按像元、按小时计算 BVOC 排放通量。
- 模型考虑温度、光照、土壤含水、季节性（LAI）与简单城市修正因子。
- 输出为 NetCDF（时空栅格）或 CSV（示例）。
- 含示例数据与演示脚本：examples/run_example.py

快速开始（本地）
1. 克隆并新建分支
   git clone git@github.com:chegov/urban-bvoc-model.git
   cd urban-bvoc-model
   git checkout -b bvoc-prototype

2. 创建虚拟环境并安装依赖
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt

3. 运行示例（会在 examples/output/ 输出结果）
   python examples/run_example.py

文件结构（已包含在仓库）
- README.md
- LICENSE (MIT)
- requirements.txt
- src/
  - bvoc_model.py     # 核心模型
  - io_utils.py       # 读写与数据处理辅助
- examples/
  - run_example.py    # 使用合成数据运行原型并保存结果
- data/sample_inputs/
  - met_hourly.csv
  - pft_lookup.csv
  - pft_map.csv
- docs/usage.md
- tests/test_core.py

默认设置
- 时间分辨率：小时
- 输出单位：µg C m^-2 h^-1
- 许可证：MIT
  
