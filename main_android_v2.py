#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电子罗盘 · 玄空飞星排盘 - Android 版本 (Kivy) - 修复版 v2
==========================================================
修复：
    • 中文字体支持（自动加载 Windows 字体）
    • 界面布局优化（BoxLayout 行布局）
    • 控件颜色对比度（白底黑字）
    • 触摸操作优化
"""

import math
import os
import platform
from kivy.config import Config

# 仅在 Windows/macOS 上设置窗口大小（Android 上不需要）
if platform.system() in ('Windows', 'Darwin'):
    # 设置窗口大小（模拟手机竖屏）- 必须在导入 App 之前
    Config.set('graphics', 'width', '360')
    Config.set('graphics', 'height', '640')
    Config.set('graphics', 'resizable', '0')
    Config.set('graphics', 'fullscreen', '0')
    Config.set('kivy', 'window_icon', '')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Line, Color, Rectangle, Ellipse
from kivy.core.text import Label as CoreLabel, LabelBase
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.core.window import Window


# ============================================================
# 字体配置 - 加载中文字体
# ============================================================
CHINESE_FONT = 'chinese'
FONT_PATH = None

# Windows 字体路径
font_candidates = [
    'C:/Windows/Fonts/simsun.ttc',
    'C:/Windows/Fonts/simhei.ttf',
    'C:/Windows/Fonts/msyh.ttc',
]

for font_path in font_candidates:
    if os.path.exists(font_path):
        FONT_PATH = font_path
        break

# Android 字体路径
if not FONT_PATH:
    android_fonts = [
        '/system/fonts/NotoSansCJK-Regular.ttc',
        '/system/fonts/DroidSansFallback.ttf',
        '/system/fonts/NotoSansSC-Regular.otf',
    ]
    for font_path in android_fonts:
        if os.path.exists(font_path):
            FONT_PATH = font_path
            break

if FONT_PATH:
    LabelBase.register(name='chinese', fn_regular=FONT_PATH)
else:
    # 如果找不到中文字体，使用默认字体（可能显示方块）
    CHINESE_FONT = 'Roboto'
    print("警告：未找到中文字体，将使用默认字体")

from kivy.lang import Builder
_spinner_font = CHINESE_FONT
Builder.load_string(f'''
<SpinnerOption>:
    font_name: '{_spinner_font}'
    background_normal: ''
    background_color: 0.95, 0.95, 0.95, 1
    color: 0, 0, 0, 1
    height: dp(35)
''')


# ============================================================
# 常量与数据
# ============================================================
SHAN_24 = ["子", "癸", "丑", "艮", "寅", "甲", "卯", "乙",
           "辰", "巽", "巳", "丙", "午", "丁", "未", "坤",
           "申", "庚", "酉", "辛", "戌", "乾", "亥", "壬"]

SHAN_TO_GONG = [7, 7, 6, 6, 6, 3, 3, 3, 0, 0, 0, 1, 1, 1, 2, 2, 2, 5, 5, 5, 8, 8, 8, 7]

TI_GUA = {
    "子": 1, "癸": 1, "甲": 1, "申": 1,
    "坤": 2, "壬": 2, "乙": 2, "卯": 2, "未": 2,
    "艮": 7, "丙": 7, "辛": 7, "酉": 7, "丑": 7,
    "乾": 6, "巽": 6, "亥": 6, "巳": 6, "戌": 6, "辰": 6,
    "寅": 9, "午": 9, "庚": 9, "丁": 9,
}

DAXIE = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
         6: "六", 7: "七", 8: "八", 9: "九"}

ZUO_ORDER = [23, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
             11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]

LUOSHU_ORDER = [4, 8, 5, 6, 1, 7, 2, 3, 0]

YUN_RANGE = {1: (1864, 1883), 2: (1884, 1903), 3: (1904, 1923),
             4: (1924, 1943), 5: (1944, 1963), 6: (1964, 1983),
             7: (1984, 2003), 8: (2004, 2023), 9: (2024, 2043)}

YUAN_LONG = {
    "乾": "天", "坤": "天", "艮": "天", "巽": "天", "子": "天", "午": "天", "卯": "天", "酉": "天",
    "甲": "地", "庚": "地", "壬": "地", "丙": "地", "辰": "地", "戌": "地", "丑": "地", "未": "地",
    "寅": "人", "申": "人", "巳": "人", "亥": "人", "癸": "人", "丁": "人", "乙": "人", "辛": "人"
}

YIN_YANG = {
    "乾": True, "坤": True, "艮": True, "巽": True,
    "子": False, "午": False, "卯": False, "酉": False,
    "甲": True, "庚": True, "壬": True, "丙": True,
    "辰": False, "戌": False, "丑": False, "未": False,
    "寅": True, "申": True, "巳": True, "亥": True,
    "癸": False, "丁": False, "乙": False, "辛": False
}

GONG_CHARS = {
    1: {"天": "子", "地": "壬", "人": "癸"},
    2: {"天": "坤", "地": "未", "人": "申"},
    3: {"天": "卯", "地": "甲", "人": "乙"},
    4: {"天": "巽", "地": "辰", "人": "巳"},
    6: {"天": "乾", "地": "戌", "人": "亥"},
    7: {"天": "酉", "地": "庚", "人": "辛"},
    8: {"天": "艮", "地": "丑", "人": "寅"},
    9: {"天": "午", "地": "丙", "人": "丁"}
}


# ============================================================
# 玄空飞星计算核心
# ============================================================
def fei_xing(center, yang):
    pan = [0] * 9
    for k in range(9):
        if yang:
            s = (center - 1 + k) % 9 + 1
        else:
            s = (center - 1 - k) % 9 + 1
        pan[LUOSHU_ORDER[k]] = s
    return pan


def yun_pan(yun):
    return fei_xing(yun, True)


def get_star_info(yuan_star, shan_char, is_jian):
    yuan = YUAN_LONG[shan_char]
    if yuan_star == 5:
        char_in_gong = None
    else:
        char_in_gong = GONG_CHARS[yuan_star][yuan]

    if is_jian and yuan_star != 5:
        fly_star = TI_GUA[char_in_gong]
    else:
        fly_star = yuan_star

    if yuan_star == 5:
        is_yang = YIN_YANG[shan_char]
    else:
        is_yang = YIN_YANG[char_in_gong]

    return fly_star, is_yang


def compute_feixing(yun, zuo_deg):
    zuo_idx = int(((zuo_deg + 7.5) % 360) / 15) % 24
    center = zuo_idx * 15
    offset = ((zuo_deg - center + 180) % 360) - 180
    is_jian = abs(offset) > 4.5

    xiang_idx = (zuo_idx + 12) % 24
    shan_gong = SHAN_TO_GONG[zuo_idx]
    xiang_gong = SHAN_TO_GONG[xiang_idx]

    yp = yun_pan(yun)
    yuan_shan_star = yp[shan_gong]
    yuan_xiang_star = yp[xiang_gong]

    shan_char = SHAN_24[zuo_idx]
    xiang_char = SHAN_24[xiang_idx]

    shan_c, shan_yang = get_star_info(yuan_shan_star, shan_char, is_jian)
    xiang_c, xiang_yang = get_star_info(yuan_xiang_star, xiang_char, is_jian)

    sp = fei_xing(shan_c, shan_yang)
    xp = fei_xing(xiang_c, xiang_yang)

    return {
        "yun": yun,
        "zuo_idx": zuo_idx,
        "zuo_deg": zuo_deg,
        "xiang_deg": (zuo_deg + 180) % 360,
        "is_jian": is_jian,
        "yun_pan": yp,
        "shan_pan": sp,
        "xiang_pan": xp,
    }


def year_star(year):
    s = (11 - year % 9) % 9
    return s if s != 0 else 9


def _dizhi_index(year):
    return (year - 4) % 12


def month_star(year, month):
    if month >= 2:
        zhi_year = year
        month_idx = month - 1
    else:
        zhi_year = year - 1
        month_idx = 12

    z = _dizhi_index(zhi_year)
    if z in (0, 6, 3, 9):
        first = 8
    elif z in (4, 10, 1, 7):
        first = 5
    else:
        first = 2

    return (first - (month_idx - 1) - 1) % 9 + 1


def add_year_month(result, year, month, lichun=False):
    if lichun and month <= 1:
        star_year = year - 1
    else:
        star_year = year

    ys = year_star(star_year)
    ms = month_star(year, month)

    result["year"] = year
    result["month"] = month
    result["star_year"] = star_year
    result["lichun"] = lichun
    result["year_star"] = ys
    result["month_star"] = ms
    result["year_pan"] = fei_xing(ys, True)
    result["month_pan"] = fei_xing(ms, True)
    return result


# ============================================================
# 九宫飞星盘绘制组件
# ============================================================
class FeiXingCanvas(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.result = None
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def set_result(self, result):
        self.result = result
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.clear()

        with self.canvas:
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)

            width = min(self.width, self.height) * 0.85
            height = width
            cell_w = width / 3
            cell_h = height / 3
            x_start = self.x + (self.width - width) / 2
            y_start = self.y + (self.height - height) / 2

            Color(0, 0, 0, 1)
            Line(width=dp(2))
            for i in range(4):
                x = x_start + i * cell_w
                Line(points=[x, y_start, x, y_start + height])
            for i in range(4):
                y = y_start + i * cell_h
                Line(points=[x_start, y, x_start + width, y])

            if not self.result:
                return

            yp = self.result.get("yun_pan", [0] * 9)
            shan_pan = self.result.get("shan_pan", [0] * 9)
            xp = self.result.get("xiang_pan", [0] * 9)
            year_pan = self.result.get("year_pan")
            month_pan = self.result.get("month_pan")
            show_year = self.result.get("show_year", False)
            show_month = self.result.get("show_month", False)

            for idx in range(9):
                row = idx // 3
                col = idx % 3
                cx = x_start + col * cell_w + cell_w / 2
                cy = y_start + (2 - row) * cell_h + cell_h / 2

                yun_text = DAXIE.get(yp[idx], str(yp[idx]))
                yun_label = CoreLabel(text=yun_text, font_size=sp(18), font_name=CHINESE_FONT)
                yun_label.refresh()
                Color(0, 0, 0, 1)
                Rectangle(texture=yun_label.texture,
                         pos=(cx - yun_label.texture.size[0]/2, cy - yun_label.texture.size[1]/2),
                         size=yun_label.texture.size)

                shan_label = CoreLabel(text=str(shan_pan[idx]), font_size=sp(16), font_name=CHINESE_FONT)
                shan_label.refresh()
                Color(0, 0, 0, 1)
                Rectangle(texture=shan_label.texture,
                         pos=(cx - cell_w/2 + dp(4), cy + cell_h/2 - shan_label.texture.size[1] - dp(4)),
                         size=shan_label.texture.size)

                xiang_label = CoreLabel(text=str(xp[idx]), font_size=sp(16), font_name=CHINESE_FONT)
                xiang_label.refresh()
                Color(0, 0, 0, 1)
                Rectangle(texture=xiang_label.texture,
                         pos=(cx + cell_w/2 - xiang_label.texture.size[0] - dp(4), cy + cell_h/2 - xiang_label.texture.size[1] - dp(4)),
                         size=xiang_label.texture.size)

                if show_year and year_pan:
                    year_label = CoreLabel(text=str(year_pan[idx]), font_size=sp(16), font_name=CHINESE_FONT)
                    year_label.refresh()
                    Color(1, 0, 0, 1)
                    Rectangle(texture=year_label.texture,
                             pos=(cx - cell_w/2 + dp(4), cy - cell_h/2 + dp(4)),
                             size=year_label.texture.size)

                if show_month and month_pan:
                    month_label = CoreLabel(text=str(month_pan[idx]), font_size=sp(16), font_name=CHINESE_FONT)
                    month_label.refresh()
                    Color(0, 0.6, 0, 1)
                    Rectangle(texture=month_label.texture,
                             pos=(cx + cell_w/2 - month_label.texture.size[0] - dp(4), cy - cell_h/2 + dp(4)),
                             size=month_label.texture.size)


# ============================================================
# 主界面
# ============================================================
class LuopanApp(App):
    def build(self):
        # 强制设置窗口尺寸
        Window.size = (360, 640)
        
        self.title = '玄空飞星排盘'
        self.result = None

        main_layout = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(5))

        # 标题
        title_label = Label(
            text='电子罗盘 · 玄空飞星排盘',
            size_hint_y=None,
            height=dp(35),
            font_size=sp(16),
            bold=True,
            font_name=CHINESE_FONT,
            color=(0, 0, 0, 1)
        )
        with title_label.canvas.before:
            Color(1, 1, 1, 1)
            Rectangle(pos=title_label.pos, size=title_label.size)
        title_label.bind(pos=lambda inst, val: setattr(inst.canvas.before.children[-1], 'pos', val),
                        size=lambda inst, val: setattr(inst.canvas.before.children[-1], 'size', val))
        main_layout.add_widget(title_label)

        # 滚动区域
        scroll = ScrollView(size_hint_y=0.42, scroll_type=['bars', 'content'])
        params_container = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(5), spacing=dp(8))
        params_container.bind(minimum_height=params_container.setter('height'))

        with params_container.canvas.before:
            Color(1, 1, 1, 1)
            self.params_bg = Rectangle(pos=params_container.pos, size=params_container.size)
        params_container.bind(pos=lambda inst, val: setattr(self.params_bg, 'pos', val),
                             size=lambda inst, val: setattr(self.params_bg, 'size', val))

        def make_label(text):
            lbl = Label(text=text, size_hint_x=0.3, size_hint_y=None, height=dp(28), font_size=sp(13),
                        font_name=CHINESE_FONT, color=(0, 0, 0, 1), halign='left', valign='middle')
            lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
            return lbl

        # 元运
        row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(5))
        row.add_widget(make_label('元  运：'))
        self.yun_spinner = Spinner(
            text=f'{DAXIE[8]}运（{YUN_RANGE[8][0]}-{YUN_RANGE[8][1]}）',
            values=[f'{DAXIE[i]}运（{YUN_RANGE[i][0]}-{YUN_RANGE[i][1]}）' for i in range(1, 10)],
            size_hint_x=0.7,
            font_size=sp(13),
            font_name=CHINESE_FONT,
            background_color=(0.95, 0.95, 0.95, 1),
            background_normal='',
            color=(0, 0, 0, 1),
            option_cls='SpinnerOption'
        )
        with self.yun_spinner.canvas.after:
            Color(0.7, 0.7, 0.7, 1)
            self.yun_border = Line(rectangle=(self.yun_spinner.x, self.yun_spinner.y,
                                               self.yun_spinner.width, self.yun_spinner.height), width=dp(1))
        self.yun_spinner.bind(pos=lambda inst, val: setattr(self.yun_border, 'rectangle',
                              (val[0], val[1], inst.width, inst.height)),
                              size=lambda inst, val: setattr(self.yun_border, 'rectangle',
                              (inst.x, inst.y, val[0], val[1])))
        row.add_widget(self.yun_spinner)
        params_container.add_widget(row)

        # 坐向
        row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(5))
        row.add_widget(make_label('坐  向：'))
        zuoxiang_values = [f'{SHAN_24[i]}山{SHAN_24[(i + 12) % 24]}向' for i in ZUO_ORDER]
        self.zx_spinner = Spinner(
            text=zuoxiang_values[0],
            values=zuoxiang_values,
            size_hint_x=0.7,
            font_size=sp(13),
            font_name=CHINESE_FONT,
            background_color=(0.95, 0.95, 0.95, 1),
            background_normal='',
            color=(0, 0, 0, 1),
            option_cls='SpinnerOption'
        )
        with self.zx_spinner.canvas.after:
            Color(0.7, 0.7, 0.7, 1)
            self.zx_border = Line(rectangle=(self.zx_spinner.x, self.zx_spinner.y,
                                              self.zx_spinner.width, self.zx_spinner.height), width=dp(1))
        self.zx_spinner.bind(pos=lambda inst, val: setattr(self.zx_border, 'rectangle',
                             (val[0], val[1], inst.width, inst.height)),
                             size=lambda inst, val: setattr(self.zx_border, 'rectangle',
                             (inst.x, inst.y, val[0], val[1])))
        self.zx_spinner.bind(text=self.on_zuoxiang_change)
        row.add_widget(self.zx_spinner)
        params_container.add_widget(row)

        # 兼向
        row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(5))
        row.add_widget(make_label('正向/兼向：'))
        self.jian_spinner = Spinner(
            text='正向',
            values=['正向'],
            size_hint_x=0.7,
            font_size=sp(13),
            font_name=CHINESE_FONT,
            background_color=(0.95, 0.95, 0.95, 1),
            background_normal='',
            color=(0, 0, 0, 1),
            option_cls='SpinnerOption'
        )
        with self.jian_spinner.canvas.after:
            Color(0.7, 0.7, 0.7, 1)
            self.jian_border = Line(rectangle=(self.jian_spinner.x, self.jian_spinner.y,
                                                self.jian_spinner.width, self.jian_spinner.height), width=dp(1))
        self.jian_spinner.bind(pos=lambda inst, val: setattr(self.jian_border, 'rectangle',
                               (val[0], val[1], inst.width, inst.height)),
                               size=lambda inst, val: setattr(self.jian_border, 'rectangle',
                               (inst.x, inst.y, val[0], val[1])))
        self.jian_spinner.bind(text=self.on_jian_change)
        row.add_widget(self.jian_spinner)
        params_container.add_widget(row)

        # 度数
        row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(5))
        row.add_widget(make_label('坐山度数：'))
        self.deg_input = TextInput(
            text='345.0',
            multiline=False,
            size_hint_x=0.7,
            font_size=sp(13),
            font_name=CHINESE_FONT,
            background_color=(0.95, 0.95, 0.95, 1),
            foreground_color=(0, 0, 0, 1),
            cursor_color=(0, 0, 0, 1),
            input_filter='float'
        )
        row.add_widget(self.deg_input)
        params_container.add_widget(row)

        # 流年流月 - 横排
        row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(5))
        row.add_widget(make_label(''))
        year_month_container = BoxLayout(size_hint_x=0.7, orientation='horizontal', spacing=dp(5))
        
        year_label = Label(text='流年：', size_hint_x=None, width=dp(50), font_size=sp(13),
                           font_name=CHINESE_FONT, color=(0, 0, 0, 1), halign='left', valign='middle')
        year_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
        year_month_container.add_widget(year_label)
        
        # 生成年份列表，2025 在中间位置
        # 列表顺序：2100, 2099, ..., 2026, 2025, 2024, ..., 1900
        year_values = list(range(2100, 1899, -1))
        
        self.year_spinner = Spinner(
            text='2025',
            values=[str(y) for y in year_values],
            font_size=sp(13),
            font_name=CHINESE_FONT,
            background_color=(0.95, 0.95, 0.95, 1),
            background_normal='',
            color=(0, 0, 0, 1),
            option_cls='SpinnerOption'
        )
        # 绑定 Spinner 打开事件，自动滚动到 2025 年
        self.year_spinner.bind(is_open=self.on_year_spinner_open)
        with self.year_spinner.canvas.after:
            Color(0.7, 0.7, 0.7, 1)
            self.year_border = Line(rectangle=(self.year_spinner.x, self.year_spinner.y,
                                                self.year_spinner.width, self.year_spinner.height), width=dp(1))
        self.year_spinner.bind(pos=lambda inst, val: setattr(self.year_border, 'rectangle',
                               (val[0], val[1], inst.width, inst.height)),
                               size=lambda inst, val: setattr(self.year_border, 'rectangle',
                               (inst.x, inst.y, val[0], val[1])))
        year_month_container.add_widget(self.year_spinner)
        
        month_label = Label(text='流月：', size_hint_x=None, width=dp(50), font_size=sp(13),
                            font_name=CHINESE_FONT, color=(0, 0, 0, 1), halign='left', valign='middle')
        month_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
        year_month_container.add_widget(month_label)
        
        self.month_spinner = Spinner(
            text='1',
            values=[str(m) for m in range(1, 13)],
            font_size=sp(13),
            font_name=CHINESE_FONT,
            background_color=(0.95, 0.95, 0.95, 1),
            background_normal='',
            color=(0, 0, 0, 1),
            option_cls='SpinnerOption'
        )
        with self.month_spinner.canvas.after:
            Color(0.7, 0.7, 0.7, 1)
            self.month_border = Line(rectangle=(self.month_spinner.x, self.month_spinner.y,
                                                 self.month_spinner.width, self.month_spinner.height), width=dp(1))
        self.month_spinner.bind(pos=lambda inst, val: setattr(self.month_border, 'rectangle',
                                (val[0], val[1], inst.width, inst.height)),
                                size=lambda inst, val: setattr(self.month_border, 'rectangle',
                                (inst.x, inst.y, val[0], val[1])))
        year_month_container.add_widget(self.month_spinner)
        row.add_widget(year_month_container)
        params_container.add_widget(row)

        # 显示开关 - 三个选项排一行
        row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(5))
        self.show_year_check = CheckBox(active=False, size_hint_x=None, width=dp(25))
        self.show_year_check.bind(active=self.on_show_toggle)
        row.add_widget(self.show_year_check)
        lbl = Label(text='流年星', size_hint_x=0.25, font_size=sp(12),
                    font_name=CHINESE_FONT, color=(0, 0, 0, 1), halign="left", valign="middle")
        lbl.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        row.add_widget(lbl)
        self.show_month_check = CheckBox(active=False, size_hint_x=None, width=dp(25))
        self.show_month_check.bind(active=self.on_show_toggle)
        row.add_widget(self.show_month_check)
        lbl2 = Label(text='流月星', size_hint_x=0.25, font_size=sp(12),
                     font_name=CHINESE_FONT, color=(0, 0, 0, 1), halign="left", valign="middle")
        lbl2.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        row.add_widget(lbl2)
        self.lichun_check = CheckBox(active=False, size_hint_x=None, width=dp(25))
        self.lichun_check.bind(active=self.on_lichun_change)
        row.add_widget(self.lichun_check)
        lbl3 = Label(text='立春换年', size_hint_x=0.25, font_size=sp(12),
                     font_name=CHINESE_FONT, color=(0, 0, 0, 1), halign="left", valign="middle")
        lbl3.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        row.add_widget(lbl3)
        params_container.add_widget(row)

        scroll.add_widget(params_container)
        main_layout.add_widget(scroll)

        # 九宫格
        self.feixing_canvas = FeiXingCanvas(size_hint_y=0.4)
        main_layout.add_widget(self.feixing_canvas)

        # 状态栏
        self.status_label = Label(
            text='请选择参数后点击「排盘」',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(10),
            font_name=CHINESE_FONT,
            color=(0, 0, 0, 1),
            halign='left',
            valign='top',
            padding=(dp(5), dp(5))
        )
        self.status_label.bind(size=lambda instance, value: setattr(instance, 'text_size', (value[0], None)))
        with self.status_label.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self.status_bg = Rectangle(pos=self.status_label.pos, size=self.status_label.size)
        self.status_label.bind(pos=lambda inst, val: setattr(self.status_bg, 'pos', val),
                              size=lambda inst, val: setattr(self.status_bg, 'size', val))
        main_layout.add_widget(self.status_label)

        # 排盘按钮
        paipan_btn = Button(
            text='排  盘',
            size_hint_y=None,
            height=dp(45),
            background_color=(0.3, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size=sp(16),
            font_name=CHINESE_FONT,
            bold=True
        )
        paipan_btn.bind(on_press=self.do_paipan)
        main_layout.add_widget(paipan_btn)

        self.update_jian_options()
        return main_layout

    def get_zuo_idx(self):
        text = self.zx_spinner.text
        return SHAN_24.index(text[0])

    def on_zuoxiang_change(self, spinner, text):
        idx = self.get_zuo_idx()
        center = idx * 15
        self.deg_input.text = f'{center:.1f}'
        self.update_jian_options()

    def update_jian_options(self):
        idx = self.get_zuo_idx()
        li = (idx - 1) % 24
        ri = (idx + 1) % 24
        lz, lx = SHAN_24[li], SHAN_24[(li + 12) % 24]
        rz, rx = SHAN_24[ri], SHAN_24[(ri + 12) % 24]
        self.jian_spinner.values = ['正向', f'兼{lz}{lx}', f'兼{rz}{rx}']
        self.jian_spinner.text = '正向'

    def on_jian_change(self, spinner, text):
        idx = self.get_zuo_idx()
        center = idx * 15
        if text == '正向':
            self.deg_input.text = f'{center:.1f}'
        else:
            li = (idx - 1) % 24
            ri = (idx + 1) % 24
            lz, lx = SHAN_24[li], SHAN_24[(li + 12) % 24]
            rz, rx = SHAN_24[ri], SHAN_24[(ri + 12) % 24]
            if text == f'兼{lz}{lx}':
                self.deg_input.text = f'{(center - 6) % 360:.1f}'
            elif text == f'兼{rz}{rx}':
                self.deg_input.text = f'{(center + 6) % 360:.1f}'

    def on_year_spinner_open(self, spinner, is_open):
        if is_open:
            # 找到 2025 年在列表中的位置
            try:
                idx = spinner.values.index('2025')
                # 计算滚动位置，让 2025 年显示在中间
                # Spinner 的 _dropdown 包含 ScrollView
                if hasattr(spinner, '_dropdown') and spinner._dropdown:
                    dropdown = spinner._dropdown
                    if hasattr(dropdown, 'container'):
                        container = dropdown.container
                        # 计算每个选项的高度
                        item_height = dp(35)  # SpinnerOption 的高度
                        # 计算滚动偏移，让 2025 年在中间
                        scroll_to = idx * item_height - (dropdown.height / 2) + (item_height / 2)
                        if scroll_to < 0:
                            scroll_to = 0
                        # 使用 Clock 延迟执行，确保 dropdown 已经渲染
                        Clock.schedule_once(lambda dt: setattr(dropdown, 'scroll_y', 1 - scroll_to / max(container.height - dropdown.height, 1)), 0.1)
            except ValueError:
                pass

    def on_show_toggle(self, checkbox, value):
        if self.result is None:
            self.do_paipan()
            return
        self.result['show_year'] = self.show_year_check.active
        self.result['show_month'] = self.show_month_check.active
        if (self.result['show_year'] or self.result['show_month']) and 'year_pan' not in self.result:
            self.add_year_month_data()
        self.feixing_canvas.set_result(self.result)

    def on_lichun_change(self, checkbox, value):
        if self.result is None:
            return
        self.add_year_month_data()
        self.feixing_canvas.set_result(self.result)

    def add_year_month_data(self):
        try:
            year = int(self.year_spinner.text)
            month = int(self.month_spinner.text)
            lichun = self.lichun_check.active
            add_year_month(self.result, year, month, lichun=lichun)
            self.result['show_year'] = self.show_year_check.active
            self.result['show_month'] = self.show_month_check.active
        except:
            pass

    def do_paipan(self, instance=None):
        try:
            yun_text = self.yun_spinner.text
            yun_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
                       '六': 6, '七': 7, '八': 8, '九': 9}
            yun = yun_map[yun_text[0]]
        except:
            self.status_label.text = '错误：元运选择不正确'
            return

        try:
            deg = float(self.deg_input.text)
        except:
            self.status_label.text = '错误：度数格式不正确'
            return

        if not (0 <= deg < 360):
            self.status_label.text = '错误：度数必须在 0 到 360 之间'
            return

        try:
            year = int(self.year_spinner.text)
            month = int(self.month_spinner.text)
        except:
            self.status_label.text = '错误：流年/流月不正确'
            return

        lichun = self.lichun_check.active
        show_year = self.show_year_check.active
        show_month = self.show_month_check.active

        self.result = compute_feixing(yun, deg)
        add_year_month(self.result, year, month, lichun=lichun)
        self.result['show_year'] = show_year
        self.result['show_month'] = show_month

        self.feixing_canvas.set_result(self.result)

        idx = self.result['zuo_idx']
        z = SHAN_24[idx]
        x = SHAN_24[(idx + 12) % 24]
        jian = '兼向（替卦）' if self.result['is_jian'] else '正向（下卦）'

        lines = [
            f'{DAXIE[yun]}运 {z}山{x}向 {jian}',
            f'坐山{deg:.1f}° 向首{self.result["xiang_deg"]:.1f}°',
        ]

        if show_year:
            lines.append(f'流年{year}年 {DAXIE[self.result["year_star"]]}入中')
        if show_month:
            lines.append(f'流月{month}月 {DAXIE[self.result["month_star"]]}入中')

        self.status_label.text = ' | '.join(lines)


if __name__ == '__main__':
    LuopanApp().run()
