import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.widgets import CheckButtons, Slider, Button
from matplotlib import cm
import matplotlib.gridspec as gridspec
import os
import sys
from pathlib import Path
import time
import matplotlib as mpl

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'KaiTi', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False 

class ThreeBodyAnimator:
    def __init__(self, csv_file, output_dir=None):
        """初始化动画器"""
        self.csv_file = csv_file
        self.output_dir = output_dir or Path(csv_file).parent / 'Animation results'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 加载数据
        self.load_data()
        
        # 动画控制参数
        self.show_trajectories = True      # 显示轨迹
        self.show_velocity_vectors = True  # 显示速度向量
        self.show_coordinate_grid = True   # 显示坐标网格
        self.show_energy_plot = True       # 显示能量图
        self.show_speed_text = True        # 显示速度文本
        self.animation_speed = 1.0         # 动画速度 (1.0 = 实时)
        self.current_frame = 0             # 当前帧
        self.is_playing = True             # 是否播放
        self.max_points_in_trajectory = 1000  # 轨迹最大点数
        
        # 设置视觉效果
        self.setup_visuals()
        
        # 创建图形和动画
        self.create_figure()
        self.setup_animation()
    
    def load_data(self):
        """加载CSV数据并验证格式"""
        print(f"加载数据文件: {self.csv_file}")
        
        try:
            self.df = pd.read_csv(self.csv_file)
            
            # 检测天体
            self.body_names = []
            for col in self.df.columns:
                if '_X(m)' in col:
                    body_name = col.replace('_X(m)', '')
                    self.body_names.append(body_name)
            
            if not self.body_names:
                raise ValueError("未检测到天体数据，请检查CSV格式")
            
            print(f"检测到天体: {', '.join(self.body_names)}")
            print(f"数据点数量: {len(self.df)}")
            print(f"时间范围: 0 到 {self.df['Time(s)'].max():.2f} 秒")
            
            # 验证必要的列
            required_columns = ['Time(s)', 'Total_Energy(J)']
            for body in self.body_names:
                required_columns.extend([
                    f'{body}_X(m)', f'{body}_Y(m)', f'{body}_Z(m)',
                    f'{body}_VX(m/s)', f'{body}_VY(m/s)', f'{body}_VZ(m/s)'
                ])
            
            missing_cols = [col for col in required_columns if col not in self.df.columns]
            if missing_cols:
                raise ValueError(f"缺少必要的列: {', '.join(missing_cols)}")
            
            # 计算初始能量偏差
            self.initial_energy = self.df['Total_Energy(J)'].iloc[0]
            self.energy_deviation = (self.df['Total_Energy(J)'] - self.initial_energy) / abs(self.initial_energy) * 100
            
        except Exception as e:
            print(f"加载数据时出错: {e}")
            sys.exit(1)
    
    def setup_visuals(self):
        """设置视觉效果参数"""
        # 颜色方案
        self.body_colors = {
            'Sun': '#FFD700',      # 金色
            'Earth': '#1E90FF',    # 道奇蓝
            'Moon': '#A9A9A9',     # 暗灰色
            'Star1': '#FF4500',    # 橙红色
            'Star2': '#32CD32',    # 石灰绿
            'Star3': '#9370DB',    # 中紫色
            'Body1': '#FF6347',    # 番茄红
            'Body2': '#3CB371',    # 海绿色
            'Body3': '#4169E1'     # 皇家蓝
        }
        
        # 为未定义的天体分配颜色
        default_colors = ['#FF6347', '#3CB371', '#4169E1', '#9370DB', '#FFD700', '#1E90FF']
        for i, body in enumerate(self.body_names):
            if body not in self.body_colors:
                self.body_colors[body] = default_colors[i % len(default_colors)]
        
        # 大小设置
        self.body_sizes = {
            'Sun': 1000,
            'Earth': 300,
            'Moon': 100,
            'Star1': 500, 'Star2': 500, 'Star3': 500,
            'Body1': 400, 'Body2': 400, 'Body3': 400
        }
        
        # 速度向量缩放因子
        self.velocity_scale = 1e-4
        self.velocity_arrow_scale = 0.1
        
        # 轨迹透明度
        self.trajectory_alpha = 0.3
        
        # 网格设置
        self.grid_alpha = 0.2
        self.grid_color = '#333333'
    
    def create_figure(self):
        """创建图形布局 - 优化后的布局"""
        # 创建主图形
        self.fig = plt.figure(figsize=(18, 14), dpi=100)  # 增大整体尺寸
        self.fig.canvas.manager.set_window_title('三体模拟 - 交互式动画')
        
        # ====== 优化后的网格布局 ======
        # 1. 3D图表区域 (占整个布局的50%)
        # 2. 2D图表区域 (占30%)
        # 3. 控制面板 (占20%)
        
        # 定义主布局 - 3行4列
        gs = gridspec.GridSpec(3, 4, figure=self.fig, 
                              height_ratios=[3, 2, 1],  # 调整行高比例
                              width_ratios=[2, 2, 2, 1])  # 调整列宽比例
        
        # 3D轨迹图 (占据左上角较大区域)
        self.ax3d = self.fig.add_subplot(gs[0, 0:2], projection='3d')
        
        # 2D XY平面图 (左下)
        self.ax2d_xy = self.fig.add_subplot(gs[1, 0])
        
        # 2D XZ平面图 (左下)
        self.ax2d_xz = self.fig.add_subplot(gs[1, 1])
        
        # 能量分析图 (右上)
        self.ax_energy = self.fig.add_subplot(gs[0, 2])
        
        # 速度分析图 (中右)
        self.ax_speed = self.fig.add_subplot(gs[1, 2])
        
        # 信息文本框 (左下角)
        self.ax_info = self.fig.add_subplot(gs[2, 0:2])
        self.ax_info.axis('off')
        
        # 控制面板 (右侧)
        self.ax_control = self.fig.add_subplot(gs[0:3, 3])
        self.ax_control.set_title('控制面板', fontsize=12, pad=10)
        self.ax_control.axis('off')
        
        # ====== 优化后的子图标题 ======
        self.ax3d.set_title('3D 轨迹', fontsize=16, pad=15)
        self.ax2d_xy.set_title('XY 平面', fontsize=14, pad=10)
        self.ax2d_xz.set_title('XZ 平面', fontsize=14, pad=10)
        self.ax_energy.set_title('能量守恒分析', fontsize=16, pad=15)
        self.ax_speed.set_title('天体速度分析', fontsize=16, pad=15)
        
        # ====== 优化后的控制面板布局 ======
        self.add_control_panel()
        
        # ====== 优化后的布局调整 ======
        self.fig.tight_layout()
        plt.subplots_adjust(
            left=0.05,     # 左边距
            right=0.85,    # 右边距
            bottom=0.08,   # 下边距
            top=0.95,      # 上边距
            wspace=0.3,    # 列间距
            hspace=0.4     # 行间距
        )
    
    def add_control_panel(self):
        """添加交互式控制面板 - 优化布局"""
        # ====== 优化后的控制面板布局 ======
        # 1. 复选框区域 (顶部)
        # 2. 滑块区域 (中间)
        # 3. 按钮区域 (底部)
        
        # 复选框区域
        ax_check = plt.axes([0.92, 0.65, 0.07, 0.25], facecolor='#f0f0f0')
        self.check = CheckButtons(ax_check, 
                                 ['显示轨迹', '显示速度向量', '显示坐标网格', '显示能量图', '显示速度文本'],
                                 [self.show_trajectories, self.show_velocity_vectors, 
                                  self.show_coordinate_grid, self.show_energy_plot, self.show_speed_text])
        
        # 速度滑块区域
        ax_slider = plt.axes([0.92, 0.4, 0.07, 0.2], facecolor='#f0f0f0')
        self.speed_slider = Slider(ax_slider, '速度倍率', 0.1, 10.0, valinit=self.animation_speed, valstep=0.1)
        
        # 按钮区域
        button_height = 0.06
        button_width = 0.07
        button_spacing = 0.03
        
        # 播放/暂停按钮
        ax_play = plt.axes([0.92, 0.25, button_width, button_height])
        self.play_button = Button(ax_play, '暂停', color='#ff9999', hovercolor='#ff6666')
        
        # 重置按钮
        ax_reset = plt.axes([0.92, 0.15, button_width, button_height])
        self.reset_button = Button(ax_reset, '重置', color='#99ccff', hovercolor='#6699ff')
        
        # 保存按钮
        ax_save = plt.axes([0.92, 0.05, button_width, button_height])
        self.save_button = Button(ax_save, '保存动画', color='#99ff99', hovercolor='#66cc66')
        
        # 连接事件
        self.check.on_clicked(self.toggle_features)
        self.speed_slider.on_changed(self.update_speed)
        self.play_button.on_clicked(self.toggle_play)
        self.reset_button.on_clicked(self.reset_animation)
        self.save_button.on_clicked(self.save_animation)
    
    def toggle_features(self, label):
        """切换显示功能"""
        if label == '显示轨迹':
            self.show_trajectories = not self.show_trajectories
        elif label == '显示速度向量':
            self.show_velocity_vectors = not self.show_velocity_vectors
        elif label == '显示坐标网格':
            self.show_coordinate_grid = not self.show_coordinate_grid
        elif label == '显示能量图':
            self.show_energy_plot = not self.show_energy_plot
        elif label == '显示速度文本':
            self.show_speed_text = not self.show_speed_text
    
    def update_speed(self, val):
        """更新动画速度"""
        self.animation_speed = val
    
    def toggle_play(self, event):
        """切换播放/暂停"""
        self.is_playing = not self.is_playing
        self.play_button.label.set_text('播放' if not self.is_playing else '暂停')
        self.play_button.color = '#99ff99' if not self.is_playing else '#ff9999'
        self.play_button.hovercolor = '#66cc66' if not self.is_playing else '#ff6666'
    
    def reset_animation(self, event):
        """重置动画"""
        self.current_frame = 0
        self.is_playing = True
        self.play_button.label.set_text('暂停')
        self.play_button.color = '#ff9999'
        self.play_button.hovercolor = '#ff6666'
    
    def save_animation(self, event):
        """保存动画"""
        print("开始保存动画... 这可能需要几分钟时间")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f'三体动画_{timestamp}.mp4'
        
        # 临时设置为保存模式
        original_show = {
            'trajectories': self.show_trajectories,
            'velocity_vectors': self.show_velocity_vectors,
            'coordinate_grid': self.show_coordinate_grid,
            'energy_plot': self.show_energy_plot,
            'speed_text': self.show_speed_text,
            'playing': self.is_playing
        }
        
        # 设置保存参数
        self.show_trajectories = True
        self.show_velocity_vectors = True
        self.show_coordinate_grid = True
        self.show_energy_plot = True
        self.show_speed_text = True
        self.is_playing = True
        
        try:
            # 创建视频写入器
            writer = FFMpegWriter(fps=30, bitrate=5000, codec='h264')
            
            with writer.saving(self.fig, str(output_file), 100):
                total_frames = min(300, len(self.df))  # 限制为300帧以节省时间
                for frame in range(total_frames):
                    self.current_frame = frame
                    self.update(frame)
                    writer.grab_frame()
                    if frame % 10 == 0:
                        print(f"保存进度: {frame}/{total_frames} 帧")
            
            print(f"动画已保存至: {output_file}")
            
            # 恢复原始设置
            self.show_trajectories = original_show['trajectories']
            self.show_velocity_vectors = original_show['velocity_vectors']
            self.show_coordinate_grid = original_show['coordinate_grid']
            self.show_energy_plot = original_show['energy_plot']
            self.show_speed_text = original_show['speed_text']
            self.is_playing = original_show['playing']
            
        except Exception as e:
            print(f"保存动画时出错: {e}")
            print("请确保已安装ffmpeg: conda install -c conda-forge ffmpeg")
    
    def setup_animation(self):
        """初始化动画元素"""
        self.trajectory_lines_3d = {}
        self.body_points_3d = {}
        self.velocity_arrows_3d = {}
        
        self.trajectory_lines_xy = {}
        self.body_points_xy = {}
        self.velocity_arrows_xy = {}
        
        self.trajectory_lines_xz = {}
        self.body_points_xz = {}
        self.velocity_arrows_xz = {}
        
        # 3D轨迹
        for body in self.body_names:
            color = self.body_colors[body]
            size = self.body_sizes.get(body, 200)
            
            # 轨迹线
            line3d, = self.ax3d.plot([], [], [], color=color, alpha=self.trajectory_alpha, linewidth=1.5)
            self.trajectory_lines_3d[body] = line3d
            
            # 天体点
            point3d = self.ax3d.scatter([], [], [], color=color, s=size, edgecolors='black', zorder=10)
            self.body_points_3d[body] = point3d
            
            # 速度向量
            arrow3d = self.ax3d.quiver([], [], [], [], [], [], color='red', alpha=0.7)
            self.velocity_arrows_3d[body] = arrow3d
        
        # XY平面
        for body in self.body_names:
            color = self.body_colors[body]
            size = self.body_sizes.get(body, 100)
            
            # 轨迹线
            line_xy, = self.ax2d_xy.plot([], [], color=color, alpha=self.trajectory_alpha, linewidth=1.5)
            self.trajectory_lines_xy[body] = line_xy
            
            # 天体点
            point_xy, = self.ax2d_xy.plot([], [], 'o', color=color, markersize=size**0.5/2, 
                                         markeredgecolor='black', zorder=10)
            self.body_points_xy[body] = point_xy
            
            # 速度向量
            arrow_xy = self.ax2d_xy.quiver([], [], [], [], color='red', alpha=0.7, scale=50)
            self.velocity_arrows_xy[body] = arrow_xy
        
        # XZ平面
        for body in self.body_names:
            color = self.body_colors[body]
            size = self.body_sizes.get(body, 100)
            
            # 轨迹线
            line_xz, = self.ax2d_xz.plot([], [], color=color, alpha=self.trajectory_alpha, linewidth=1.5)
            self.trajectory_lines_xz[body] = line_xz
            
            # 天体点
            point_xz, = self.ax2d_xz.plot([], [], 'o', color=color, markersize=size**0.5/2, 
                                         markeredgecolor='black', zorder=10)
            self.body_points_xz[body] = point_xz
            
            # 速度向量
            arrow_xz = self.ax2d_xz.quiver([], [], [], [], color='red', alpha=0.7, scale=50)
            self.velocity_arrows_xz[body] = arrow_xz
        
        # 能量图
        if self.show_energy_plot:
            self.energy_line, = self.ax_energy.plot([], [], 'r-', linewidth=2, label='能量偏差')
            self.ax_energy.set_yscale('log')
            self.ax_energy.set_xlabel('时间 (秒)')
            self.ax_energy.set_ylabel('相对偏差 (%)')
            self.ax_energy.grid(True, alpha=0.3)
            self.ax_energy.legend()
            
            # 初始设置能量图范围
            max_dev = max(1e-10, np.max(np.abs(self.energy_deviation)))
            self.ax_energy.set_ylim(1e-20, max_dev * 10)
        
        # 速度图
        self.speed_lines = {}
        for body in self.body_names:
            color = self.body_colors[body]
            line, = self.ax_speed.plot([], [], color=color, linewidth=2, label=body)
            self.speed_lines[body] = line
        
        self.ax_speed.set_xlabel('时间 (秒)')
        self.ax_speed.set_ylabel('速度 (m/s)')
        self.ax_speed.set_yscale('log')
        self.ax_speed.grid(True, alpha=0.3)
        self.ax_speed.legend()
        
        # 设置坐标轴范围
        self.set_axis_limits()
        
        # 创建动画
        self.ani = FuncAnimation(self.fig, self.update, frames=len(self.df),
                               interval=50, blit=False)
    
    def set_axis_limits(self):
        """设置所有子图的坐标轴范围"""
        # 获取所有位置数据
        all_x = []
        all_y = []
        all_z = []
        
        for body in self.body_names:
            all_x.extend(self.df[f'{body}_X(m)'].values)
            all_y.extend(self.df[f'{body}_Y(m)'].values)
            all_z.extend(self.df[f'{body}_Z(m)'].values)
        
        # 计算范围
        margin = 0.1
        x_range = max(all_x) - min(all_x)
        y_range = max(all_y) - min(all_y)
        z_range = max(all_z) - min(all_z)
        
        x_center = (max(all_x) + min(all_x)) / 2
        y_center = (max(all_y) + min(all_y)) / 2
        z_center = (max(all_z) + min(all_z)) / 2
        
        x_lim = [x_center - x_range*(0.5 + margin), x_center + x_range*(0.5 + margin)]
        y_lim = [y_center - y_range*(0.5 + margin), y_center + y_range*(0.5 + margin)]
        z_lim = [z_center - z_range*(0.5 + margin), z_center + z_range*(0.5 + margin)]
        
        # 设置3D轴
        self.ax3d.set_xlim(x_lim)
        self.ax3d.set_ylim(y_lim)
        self.ax3d.set_zlim(z_lim)
        self.ax3d.set_xlabel('X 位置 (m)', labelpad=10)
        self.ax3d.set_ylabel('Y 位置 (m)', labelpad=10)
        self.ax3d.set_zlabel('Z 位置 (m)', labelpad=10)
        self.ax3d.tick_params(axis='both', which='major', labelsize=9)
        
        # 设置XY平面
        self.ax2d_xy.set_xlim(x_lim)
        self.ax2d_xy.set_ylim(y_lim)
        self.ax2d_xy.set_xlabel('X 位置 (m)', labelpad=5)
        self.ax2d_xy.set_ylabel('Y 位置 (m)', labelpad=5)
        self.ax2d_xy.grid(True, alpha=0.3)
        self.ax2d_xy.set_aspect('equal')
        self.ax2d_xy.tick_params(axis='both', which='major', labelsize=9)
        
        # 设置XZ平面
        self.ax2d_xz.set_xlim(x_lim)
        self.ax2d_xz.set_ylim(z_lim)
        self.ax2d_xz.set_xlabel('X 位置 (m)', labelpad=5)
        self.ax2d_xz.set_ylabel('Z 位置 (m)', labelpad=5)
        self.ax2d_xz.grid(True, alpha=0.3)
        self.ax2d_xz.set_aspect('equal')
        self.ax2d_xz.tick_params(axis='both', which='major', labelsize=9)
        
        # 设置能量图
        self.ax_energy.set_xlim(0, self.df['Time(s)'].max())
        self.ax_energy.tick_params(axis='both', which='major', labelsize=9)
        
        # 设置速度图
        self.ax_speed.set_xlim(0, self.df['Time(s)'].max())
        self.ax_speed.tick_params(axis='both', which='major', labelsize=9)
        
        # 添加网格
        if self.show_coordinate_grid:
            self.add_coordinate_grid()
    
    def add_coordinate_grid(self):
        """添加坐标网格"""
        # 3D网格
        self.ax3d.grid(True, alpha=self.grid_alpha, color=self.grid_color, linestyle='--')
    
    def update(self, frame):
        """更新动画帧"""
        if not self.is_playing:
            return
        
        # 根据速度调整帧
        frame_step = max(1, int(self.animation_speed))
        self.current_frame = (self.current_frame + frame_step) % len(self.df)
        frame = self.current_frame
        
        current_time = self.df['Time(s)'].iloc[frame]
        current_energy = self.df['Total_Energy(J)'].iloc[frame]
        energy_dev = abs((current_energy - self.initial_energy) / self.initial_energy) * 100
        
        # 更新3D视图
        for body in self.body_names:
            color = self.body_colors[body]
            size = self.body_sizes.get(body, 200)
            
            # 获取位置和速度
            x = self.df[f'{body}_X(m)'].iloc[frame]
            y = self.df[f'{body}_Y(m)'].iloc[frame]
            z = self.df[f'{body}_Z(m)'].iloc[frame]
            vx = self.df[f'{body}_VX(m/s)'].iloc[frame]
            vy = self.df[f'{body}_VY(m/s)'].iloc[frame]
            vz = self.df[f'{body}_VZ(m/s)'].iloc[frame]
            
            speed = np.sqrt(vx**2 + vy**2 + vz**2)
            
            # 更新3D天体位置
            self.body_points_3d[body]._offsets3d = ([x], [y], [z])
            
            # 更新3D轨迹
            if self.show_trajectories:
                start_idx = max(0, frame - self.max_points_in_trajectory)
                traj_x = self.df[f'{body}_X(m)'].iloc[start_idx:frame+1].values
                traj_y = self.df[f'{body}_Y(m)'].iloc[start_idx:frame+1].values
                traj_z = self.df[f'{body}_Z(m)'].iloc[start_idx:frame+1].values
                self.trajectory_lines_3d[body].set_data_3d(traj_x, traj_y, traj_z)
            
            # 更新3D速度向量
            if self.show_velocity_vectors:
                scale = self.velocity_arrow_scale
                self.velocity_arrows_3d[body].remove()
                self.velocity_arrows_3d[body] = self.ax3d.quiver(
                    x, y, z, vx*scale, vy*scale, vz*scale,
                    color='red', alpha=0.7, length=1e10
                )
            
            # 更新XY平面
            self.body_points_xy[body].set_data([x], [y])
            if self.show_trajectories:
                self.trajectory_lines_xy[body].set_data(
                    self.df[f'{body}_X(m)'].iloc[start_idx:frame+1],
                    self.df[f'{body}_Y(m)'].iloc[start_idx:frame+1]
                )
            if self.show_velocity_vectors:
                self.velocity_arrows_xy[body].remove()
                self.velocity_arrows_xy[body] = self.ax2d_xy.quiver(
                    x, y, vx*scale, vy*scale, color='red', alpha=0.7, scale=50
                )
            
            # 更新XZ平面
            self.body_points_xz[body].set_data([x], [z])
            if self.show_trajectories:
                self.trajectory_lines_xz[body].set_data(
                    self.df[f'{body}_X(m)'].iloc[start_idx:frame+1],
                    self.df[f'{body}_Z(m)'].iloc[start_idx:frame+1]
                )
            if self.show_velocity_vectors:
                self.velocity_arrows_xz[body].remove()
                self.velocity_arrows_xz[body] = self.ax2d_xz.quiver(
                    x, z, vx*scale, vz*scale, color='red', alpha=0.7, scale=50
                )
            
            # 更新速度图
            if frame > 0:
                self.speed_lines[body].set_data(
                    self.df['Time(s)'].iloc[:frame+1],
                    np.sqrt(self.df[f'{body}_VX(m/s)'].iloc[:frame+1]**2 + 
                           self.df[f'{body}_VY(m/s)'].iloc[:frame+1]**2 + 
                           self.df[f'{body}_VZ(m/s)'].iloc[:frame+1]**2)
                )
        
        # 更新能量图
        if self.show_energy_plot and frame > 0:
            self.energy_line.set_data(
                self.df['Time(s)'].iloc[:frame+1],
                np.abs(self.energy_deviation.iloc[:frame+1])
            )
        
        # 更新信息面板
        info_text = f"当前时间: {current_time:.2f} 秒\n"
        info_text += f"能量偏差: {energy_dev:.6e}%\n"
        info_text += f"动画速度: {self.animation_speed:.1f}x\n"
        info_text += f"当前帧: {frame}/{len(self.df)}"
        
        self.ax_info.clear()
        self.ax_info.axis('off')
        self.ax_info.text(0.02, 0.95, info_text, 
                         transform=self.ax_info.transAxes,
                         fontsize=10, family='monospace',
                         bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray', linewidth=0.5))
        
        # 重绘
        self.fig.canvas.draw_idle()
        
        return []
    
    def run(self):
        """运行动画"""
        print("启动动画... 使用控制面板调整设置")
        print("按 Ctrl+C 退出程序")
        plt.show()

def main():
    """主函数"""
    # 自动检测CSV文件
    current_dir = Path(__file__).parent
    possible_csv_files = [
        current_dir / 'three_body_results.csv',
        current_dir.parent / 'three_body_results.csv',
        current_dir / 'results.csv'
    ]
    
    csv_file = None
    for file in possible_csv_files:
        if file.exists():
            csv_file = str(file)
            break
    
    if csv_file is None:
        print("未找到CSV文件。请指定文件路径：")
        print("  python dynamic_visualizer.py <csv_file_path>")
        if len(sys.argv) > 1:
            csv_file = sys.argv[1]
        else:
            sys.exit(1)
    
    print(f"找到CSV文件: {csv_file}")
    
    # 创建动画器
    animator = ThreeBodyAnimator(csv_file)
    
    # 运行动画
    animator.run()

if __name__ == "__main__":
    main()