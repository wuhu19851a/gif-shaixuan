# 导入所需的库
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QFileDialog, QScrollArea,
                             QLabel, QGridLayout, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QRect, QSize
from PyQt6.QtGui import QPixmap, QMovie
import sys
import os
import shutil

class GifViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化主窗口
        self.setWindowTitle('GIF图片批量筛选工具')
        self.setGeometry(100, 100, 800, 600)
        
        # 创建主窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建顶部按钮布局
        self.top_layout = QHBoxLayout()
        
        # 创建选择文件夹按钮
        self.select_folder_btn = QPushButton('选择文件夹')
        self.select_folder_btn.clicked.connect(self.select_folder)
        self.top_layout.addWidget(self.select_folder_btn)
        
        # 创建批量复制按钮
        self.batch_copy_btn = QPushButton('复制文件名')
        self.batch_copy_btn.clicked.connect(self.batch_copy)
        self.top_layout.addWidget(self.batch_copy_btn)
        
        # 创建批量复制视频地址按钮
        self.batch_copy_mp4_btn = QPushButton('复制视频地址')
        self.batch_copy_mp4_btn.clicked.connect(self.batch_copy_mp4)
        self.top_layout.addWidget(self.batch_copy_mp4_btn)
        
        # 将顶部布局添加到主布局
        self.main_layout.addLayout(self.top_layout)
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area)
        
        # 存储当前显示的GIF
        self.current_folder = ''
        self.current_gifs = []
        self.playing_movies = {}
        self.selected_gifs = set()
        
        # 设置定时器用于检查GIF可见性
        self.visibility_timer = QTimer(self)
        self.visibility_timer.timeout.connect(self.check_gif_visibility)
        self.visibility_timer.start(500)  # 每500ms检查一次
        
        # 连接滚动区域的滚动信号
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)

    def select_folder(self):
        """选择文件夹并加载GIF图片"""
        folder = QFileDialog.getExistingDirectory(self, '选择文件夹')
        if folder:
            self.current_folder = folder
            self.load_gifs()
    
    def load_gifs(self):
        """加载文件夹中的GIF图片"""
        # 清除现有内容
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        # 清除选中状态
        self.selected_gifs.clear()
        
        # 获取所有GIF文件
        self.current_gifs = [f for f in os.listdir(self.current_folder) 
                           if f.lower().endswith('.gif')]
        
        # 在网格中显示GIF
        row = 0
        col = 0
        for gif in self.current_gifs:
            container = QWidget()
            container.setProperty('gif_name', gif)
            layout = QVBoxLayout(container)
            
            # 创建GIF显示标签
            label = QLabel()
            label.setFixedSize(300, 450)  # 设置固定大小
            movie = QMovie(os.path.join(self.current_folder, gif))
            movie.setScaledSize(QSize(300, 450))
            label.setMovie(movie)
            layout.addWidget(label)
            
            # 创建文件名标签
            name_label = QLabel(gif)
            layout.addWidget(name_label)
            
            # 创建按钮布局
            btn_layout = QHBoxLayout()
            
            # 创建选择复选框
            select_btn = QPushButton('选择')
            select_btn.setCheckable(True)
            select_btn.clicked.connect(lambda checked, g=gif: self.toggle_selection(g))
            btn_layout.addWidget(select_btn)
            
            layout.addLayout(btn_layout)
            
            # 将容器添加到网格布局
            self.grid_layout.addWidget(container, row, col)
            
            # 更新行列位置
            col += 1
            if col > 4:  # 每行显示5个GIF
                col = 0
                row += 1
            
            # 存储movie对象
            self.playing_movies[gif] = movie
    
    def check_gif_visibility(self):
        """检查GIF是否在可视区域内并控制播放状态"""
        viewport_rect = self.scroll_area.viewport().rect()
        viewport_global = self.scroll_area.viewport().mapToGlobal(viewport_rect.topLeft())
        viewport_rect.moveTo(viewport_global)

        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                # 获取widget在全局坐标系中的位置和大小
                widget_global = widget.mapToGlobal(widget.rect().topLeft())
                widget_rect = QRect(widget_global, widget.size())
                
                # 检查是否与viewport相交
                is_visible = viewport_rect.intersects(widget_rect)
                
                # 获取对应的GIF名称和Movie对象
                gif_name = widget.property('gif_name')
                if gif_name in self.playing_movies:
                    movie = self.playing_movies[gif_name]
                    
                    # 根据可见性控制播放状态
                    if is_visible:
                        if movie.state() == QMovie.MovieState.NotRunning:
                            movie.start()
                    else:
                        if movie.state() == QMovie.MovieState.Running:
                            movie.stop()
                            movie.jumpToFrame(0)  # 重置到第一帧
    
    def on_scroll(self):
        """滚动时触发GIF可见性检查"""
        self.check_gif_visibility()
    
    def toggle_selection(self, gif_name):
        """切换GIF的选中状态"""
        if gif_name in self.selected_gifs:
            self.selected_gifs.remove(gif_name)
        else:
            self.selected_gifs.add(gif_name)
    
    def batch_copy(self):
        """将选中的GIF文件名复制到剪贴板（包含后缀）"""
        if not self.selected_gifs:
            QMessageBox.warning(self, '警告', '请先选择要复制的文件！')
            return
        
        # 收集所有选中文件的文件名（包含后缀）
        filenames = list(self.selected_gifs)
        # 将文件名以换行符连接
        clipboard_text = '\n'.join(filenames)
        
        # 将文本复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(clipboard_text)
        
        QMessageBox.information(self, '完成', f'已成功复制{len(filenames)}个文件名到剪贴板。')
    
    def batch_copy_mp4(self):
        """将选中的GIF文件名复制到剪贴板（将后缀改为.mp4）"""
        if not self.selected_gifs:
            QMessageBox.warning(self, '警告', '请先选择要复制的文件！')
            return
        
        # 收集所有选中文件的文件名（将后缀改为.mp4）
        filenames = [os.path.splitext(gif_name)[0] + '.mp4' for gif_name in self.selected_gifs]
        # 将文件名以换行符连接
        clipboard_text = '\n'.join(filenames)
        
        # 将文本复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(clipboard_text)
        
        QMessageBox.information(self, '完成', f'已成功复制{len(filenames)}个视频地址到剪贴板。')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = GifViewer()
    viewer.show()
    sys.exit(app.exec())