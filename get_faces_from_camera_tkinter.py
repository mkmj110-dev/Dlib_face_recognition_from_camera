# Copyright (C) 2018-2021 coneypo
# SPDX-License-Identifier: MIT

# 人脸录入 Tkinter GUI - V6 简化稳定版

import dlib
import numpy as np
import cv2
import os
import shutil
import time
import logging
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk

detector = dlib.get_frontal_face_detector()

# 颜色
BG = "#f5f5f7"
CARD = "#ffffff"
BORDER = "#c0c0c0"
TEXT = "#333333"
GRAY = "#888888"
GREEN = "#34c759"
BLUE = "#007aff"
RED = "#ff3b30"
ORANGE = "#ff9500"


class Face_Register:
    def __init__(self):
        self.current_frame_faces_cnt = 0
        self.existing_faces = 0
        self.ss_cnt = 0
        self.registered_names = []
        
        self.path_photos_from_camera = "data/data_faces_from_camera/"
        self.current_face_dir = ""

        if os.path.isdir(self.path_photos_from_camera) and os.listdir(self.path_photos_from_camera):
            self.existing_faces = len(os.listdir(self.path_photos_from_camera))

        self.win = ttk.Window(themename="litera")
        self.win.title("人脸录入系统")
        self.win.geometry("1000x650")
        self.win.minsize(800, 550)
        
        self.setup_ui()
        
        self.current_frame = None
        self.face_ROI_width_start = 0
        self.face_ROI_height_start = 0
        self.face_ROI_width = 0
        self.face_ROI_height = 0
        self.ww = 0
        self.hh = 0
        self.out_of_range_flag = False
        self.face_folder_created_flag = False
        self.frame_start_time = time.time()
        self.fps = 0

        self.cap = cv2.VideoCapture(0)

    def setup_ui(self):
        # 主背景
        self.win.configure(bg=BG)
        
        # 顶部标题
        header = tk.Frame(self.win, bg=BG)
        header.pack(fill=X, padx=25, pady=(20, 15))
        tk.Label(header, text="🎭 人脸录入系统", font=("Microsoft YaHei UI", 20, "bold"),
                bg=BG, fg=TEXT).pack(side=LEFT)
        
        # 主内容区 - 使用 Grid 实现 7:3 比例
        main = tk.Frame(self.win, bg=BG)
        main.pack(fill=BOTH, expand=True, padx=25, pady=(0, 15))
        
        # 配置 Grid 列权重 6:4
        main.columnconfigure(0, weight=6)
        main.columnconfigure(1, weight=4)
        main.rowconfigure(0, weight=1)
        
        # ===== 左侧视频 =====
        left = tk.Frame(main, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        
        # 视频头部
        left_header = tk.Frame(left, bg=CARD)
        left_header.pack(fill=X, padx=15, pady=12)
        tk.Label(left_header, text="📹 实时摄像头", font=("Microsoft YaHei UI", 12, "bold"),
                bg=CARD, fg=TEXT).pack(side=LEFT)
        self.fps_label = tk.Label(left_header, text="FPS: 0", font=("Consolas", 10),
                                 bg=CARD, fg=GRAY)
        self.fps_label.pack(side=RIGHT)
        
        # 视频画面
        self.video_label = tk.Label(left, bg="#f0f0f0")
        self.video_label.pack(fill=BOTH, expand=True, padx=15, pady=(0, 10))
        
        # 警告
        self.warning_label = tk.Label(left, text="", font=("Microsoft YaHei UI", 10),
                                     bg=CARD, fg=RED)
        self.warning_label.pack(pady=(0, 10))

        # ===== 右侧控制面板 =====
        right = tk.Frame(main, bg=BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        
        # 卡片1: 状态
        card1 = tk.Frame(right, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        card1.pack(fill=X, pady=(0, 10))
        
        tk.Label(card1, text="📊 状态信息", font=("Microsoft YaHei UI", 11, "bold"),
                bg=CARD, fg=TEXT).pack(anchor=W, padx=12, pady=(12, 8))
        
        stat_row = tk.Frame(card1, bg=CARD)
        stat_row.pack(fill=X, padx=12, pady=(0, 12))
        
        # 左统计
        s1 = tk.Frame(stat_row, bg=CARD)
        s1.pack(side=LEFT, expand=True)
        tk.Label(s1, text="已录入", font=("Microsoft YaHei UI", 9), bg=CARD, fg=GRAY).pack()
        self.db_count = tk.Label(s1, text=str(self.existing_faces), font=("Microsoft YaHei UI", 18, "bold"),
                                bg=CARD, fg=GREEN)
        self.db_count.pack()
        
        # 右统计
        s2 = tk.Frame(stat_row, bg=CARD)
        s2.pack(side=RIGHT, expand=True)
        tk.Label(s2, text="当前检测", font=("Microsoft YaHei UI", 9), bg=CARD, fg=GRAY).pack()
        self.face_count = tk.Label(s2, text="0", font=("Microsoft YaHei UI", 18, "bold"),
                                  bg=CARD, fg=BLUE)
        self.face_count.pack()
        
        # 卡片2: 输入
        card2 = tk.Frame(right, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        card2.pack(fill=X, pady=(0, 10))
        
        tk.Label(card2, text="📝 步骤1: 输入姓名", font=("Microsoft YaHei UI", 11, "bold"),
                bg=CARD, fg=TEXT).pack(anchor=W, padx=12, pady=(12, 8))
        
        self.name_entry = ttk.Entry(card2, font=("Microsoft YaHei UI", 10))
        self.name_entry.pack(fill=X, padx=12, pady=(0, 8), ipady=4)
        
        btn_row = tk.Frame(card2, bg=CARD)
        btn_row.pack(fill=X, padx=12, pady=(0, 12))
        
        ttk.Button(btn_row, text="录入", command=self.do_register, bootstyle="success", width=7).pack(side=LEFT, padx=(0, 5))
        ttk.Button(btn_row, text="更改", command=self.do_change, bootstyle="warning", width=7).pack(side=LEFT, padx=5)
        ttk.Button(btn_row, text="删除", command=self.do_delete, bootstyle="danger", width=7).pack(side=LEFT, padx=(5, 0))
        
        # 卡片3: 保存
        card3 = tk.Frame(right, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        card3.pack(fill=X, pady=(0, 10))
        
        tk.Label(card3, text="📸 步骤2: 保存人脸", font=("Microsoft YaHei UI", 11, "bold"),
                bg=CARD, fg=TEXT).pack(anchor=W, padx=12, pady=(12, 8))
        
        ttk.Button(card3, text="📷 保存当前人脸", command=self.do_save,
                  bootstyle="primary").pack(fill=X, padx=12, pady=(0, 12), ipady=4)
        
        # 卡片4: 管理
        card4 = tk.Frame(right, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        card4.pack(fill=X)
        
        tk.Label(card4, text="⚙️ 数据管理", font=("Microsoft YaHei UI", 11, "bold"),
                bg=CARD, fg=TEXT).pack(anchor=W, padx=12, pady=(12, 8))
        
        ttk.Button(card4, text="清空所有数据", command=self.do_clear,
                  bootstyle="danger-outline").pack(fill=X, padx=12, pady=(0, 12))
        
        # 底部日志
        self.log_label = tk.Label(self.win, text="系统就绪，请输入姓名后点击「录入」",
                                 font=("Microsoft YaHei UI", 9), bg=BG, fg=GRAY, anchor=W)
        self.log_label.pack(fill=X, padx=25, pady=(0, 15))

    def log(self, msg, color=GRAY):
        self.log_label.configure(text=msg, fg=color)

    def pre_work_mkdir(self):
        if not os.path.isdir(self.path_photos_from_camera):
            os.makedirs(self.path_photos_from_camera)

    def check_existing_faces(self):
        if os.listdir(self.path_photos_from_camera):
            for p in os.listdir(self.path_photos_from_camera):
                self.registered_names.append(p.split('_')[1])
            self.existing_faces = len(self.registered_names)
            self.db_count.configure(text=str(self.existing_faces))

    def do_register(self):
        name = self.name_entry.get().strip()
        if not name:
            self.log("❌ 请输入姓名", RED)
            return
        if name in self.registered_names:
            self.log("⚠️ 该姓名已存在", ORANGE)
            return
        self.current_face_dir = self.path_photos_from_camera + "person_" + name
        os.makedirs(self.current_face_dir)
        self.registered_names.append(name)
        self.existing_faces += 1
        self.db_count.configure(text=str(self.existing_faces))
        self.ss_cnt = 0
        self.face_folder_created_flag = True
        self.log(f"✅ 已创建: {name}，现在可以保存人脸", GREEN)

    def do_delete(self):
        name = self.name_entry.get().strip()
        if name and name in self.registered_names:
            shutil.rmtree(self.path_photos_from_camera + "person_" + name)
            self.registered_names.remove(name)
            self.existing_faces -= 1
            self.db_count.configure(text=str(self.existing_faces))
            self.log(f"✅ 已删除: {name}", GREEN)
        else:
            self.log("⚠️ 未找到该姓名", ORANGE)

    def do_change(self):
        name = self.name_entry.get().strip()
        if name and name in self.registered_names:
            self.current_face_dir = self.path_photos_from_camera + "person_" + name
            self.ss_cnt = len(os.listdir(self.current_face_dir))
            self.face_folder_created_flag = True
            self.log(f"✅ 已选择: {name}", GREEN)
        else:
            self.log("⚠️ 未找到该姓名", ORANGE)

    def do_save(self):
        if not self.face_folder_created_flag:
            self.log("❌ 请先完成步骤1", RED)
            return
        if self.current_frame_faces_cnt != 1:
            self.log("❌ 请确保画面中只有一张人脸", RED)
            return
        if self.out_of_range_flag:
            self.log("❌ 人脸超出范围", RED)
            return
        
        self.ss_cnt += 1
        h2, w2 = self.face_ROI_height * 2, self.face_ROI_width * 2
        roi = np.zeros((h2, w2, 3), np.uint8)
        for i in range(h2):
            for j in range(w2):
                try:
                    roi[i][j] = self.current_frame[self.face_ROI_height_start - self.hh + i][self.face_ROI_width_start - self.ww + j]
                except:
                    pass
        Image.fromarray(roi).save(f"{self.current_face_dir}/img_face_{self.ss_cnt}.jpg")
        self.log(f"✅ 已保存第 {self.ss_cnt} 张照片", GREEN)

    def do_clear(self):
        for f in os.listdir(self.path_photos_from_camera):
            shutil.rmtree(self.path_photos_from_camera + f)
        if os.path.isfile("./data/features_all.csv"):
            os.remove("./data/features_all.csv")
        self.registered_names.clear()
        self.existing_faces = 0
        self.db_count.configure(text="0")
        self.face_folder_created_flag = False
        self.log("✅ 已清空所有数据", GREEN)

    def get_frame(self):
        try:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    return ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        except:
            pass
        return False, None

    def process(self):
        ret, frame = self.get_frame()
        if not ret:
            self.win.after(100, self.process)
            return

        self.current_frame = frame
        
        # FPS
        now = time.time()
        self.fps = 1.0 / (now - self.frame_start_time) if (now - self.frame_start_time) > 0 else 0
        self.frame_start_time = now
        self.fps_label.configure(text=f"FPS: {self.fps:.1f}")
        
        # 检测人脸
        faces = detector(self.current_frame, 0)
        self.face_count.configure(text=str(len(faces)))
        self.current_frame_faces_cnt = len(faces)
        
        for d in faces:
            self.face_ROI_width_start = d.left()
            self.face_ROI_height_start = d.top()
            self.face_ROI_height = d.bottom() - d.top()
            self.face_ROI_width = d.right() - d.left()
            self.hh = self.face_ROI_height // 2
            self.ww = self.face_ROI_width // 2

            h, w = self.current_frame.shape[:2]
            out = (d.right() + self.ww > w) or (d.bottom() + self.hh > h) or (d.left() - self.ww < 0) or (d.top() - self.hh < 0)
            
            if out:
                self.warning_label.configure(text="⚠️ 人脸超出范围")
                self.out_of_range_flag = True
                color = (231, 76, 60)
            else:
                self.warning_label.configure(text="")
                self.out_of_range_flag = False
                color = (52, 199, 89)
            
            cv2.rectangle(self.current_frame, (d.left()-self.ww, d.top()-self.hh),
                         (d.right()+self.ww, d.bottom()+self.hh), color, 2)

        # 显示视频
        self.video_label.update_idletasks()
        lw, lh = self.video_label.winfo_width(), self.video_label.winfo_height()
        
        if lw > 50 and lh > 50:
            img = Image.fromarray(self.current_frame)
            ratio = min(lw / img.width, lh / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.video_label.img_tk = photo
            self.video_label.configure(image=photo)

        self.win.after(25, self.process)

    def run(self):
        self.pre_work_mkdir()
        self.check_existing_faces()
        self.process()
        self.win.mainloop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    Face_Register().run()
