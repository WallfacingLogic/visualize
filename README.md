# 三体模拟可视化器 (Three-Body Simulation Visualizer)

一个用于可视化三体问题模拟结果的Python应用程序。该工具可以读取模拟数据并生成动态动画，展示天体的运动轨迹、速度向量、能量变化等。

## 功能特性

- **动态动画**: 实时显示天体运动轨迹和速度向量
- **交互控制**: 提供播放/暂停、速度调节、显示选项切换等控件
- **多视角视图**: 支持3D轨迹和2D投影视图
- **能量监控**: 实时显示系统总能量和能量偏差
- **数据导出**: 支持将动画导出为视频文件
- **自定义可视化**: 可调节轨迹长度、颜色方案等参数

## 安装

### 环境要求

- Python >= 3.14
- 推荐使用 uv 包管理器

### 安装依赖

```bash
# 使用 uv 安装依赖
uv sync
```

主要依赖包：
- numpy: 数值计算
- pandas: 数据处理
- matplotlib: 绘图和动画
- scipy: 科学计算
- ffmpeg-python: 视频导出

## 使用方法

### 基本使用

1. 准备包含模拟数据的CSV文件（格式见下文）
2. 运行可视化器：

```bash
python dynamic_visualizer.py
```

程序会自动检测当前目录下的 `results.csv` 文件，或提示选择文件。

### 命令行参数

```bash
python dynamic_visualizer.py [CSV文件路径]
```

### 交互控制

运行后会出现动画窗口，包含以下控件：

- **播放/暂停按钮**: 控制动画播放
- **速度滑块**: 调节动画播放速度
- **显示选项**: 切换轨迹、速度向量、网格、能量图等的显示
- **帧滑块**: 跳转到特定时间点

### 数据格式

CSV文件应包含以下列：

#### 必需列：
- `Time(s)`: 时间（秒）
- `Total_Energy(J)`: 系统总能量（焦耳）

#### 天体数据列（每个天体需要以下6列）：
- `{BodyName}_X(m)`: X坐标（米）
- `{BodyName}_Y(m)`: Y坐标（米）
- `{BodyName}_Z(m)`: Z坐标（米）
- `{BodyName}_VX(m/s)`: X方向速度（米/秒）
- `{BodyName}_VY(m/s)`: Y方向速度（米/秒）
- `{BodyName}_VZ(m/s)`: Z方向速度（米/秒）

#### 示例格式：
```
Time(s),Total_Energy(J),Sun_X(m),Sun_Y(m),Sun_Z(m),Sun_VX(m/s),Sun_VY(m/s),Sun_VZ(m/s),Earth_X(m),...
0.0,1.23e10,0.0,0.0,0.0,0.0,0.0,0.0,1.5e11,...
0.1,1.23e10,0.0,0.0,0.0,0.0,0.0,0.0,1.5e11,...
...
```

## 构建可执行文件

使用 PyInstaller 构建独立的可执行文件：

```bash
# 安装 PyInstaller（已包含在依赖中）
# 构建
pyinstaller dynamic_visualizer.spec

# 或直接使用
pyinstaller --onefile --windowed dynamic_visualizer.py
```

构建后的可执行文件位于 `dist/` 目录下。

## 项目结构

```
visualize/
├── dynamic_visualizer.py    # 主程序文件
├── pyproject.toml          # 项目配置和依赖
└── README.md               # 本文档
```

## 故障排除

### 常见问题

1. **字体显示问题**: 如果中文标签显示异常，请确保系统安装了中文字体
2. **视频导出失败**: 确保安装了 FFmpeg 并添加到系统PATH
3. **性能问题**: 对于大量数据点，考虑减少轨迹显示长度

### 依赖检查

运行以下命令检查依赖是否正确安装：

```bash
python -c "import numpy, pandas, matplotlib, scipy; print('所有依赖已安装')"
```

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 版本历史

- v0.1.0: 初始版本，支持基本的三体可视化功能