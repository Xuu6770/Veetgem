<h1 align = "center">Veetgem</h1>

<p align = "center">
    一个视频缩略图网格生成器，快速预览影片的多个画面。
</p>

<p align = "center">
    <a href = "README.md" target = "_blank">EN</a> | <a href = "README_CN.md" target = "_blank">CN</a>
</p>

## 特性

- [x] 支持`mp4`、`mkv`、`avi`等常见视频格式。
- [x] 网格中的每张截图都会标注其在视频中对应的时间。
- [x] 自定义截图的数量，例如 3 行 3 列共 9 张或 4 行 4 列共 16 张。
- [x] 自定义最终图片的宽度（高度将自动按比例调整）。
- [x] 自定义截图之间的距离。
- [x] 自定义截图的圆角。

## 使用

目前仅编译了在 Apple Silicon 的 macOS 上运行的可执行文件，可在 [release](https://github.com/Xuu6770/Veetgem/releases) 页面中下载。

下载完成后，打开终端并`cd`到可执行文件的所在目录，使用以下命令即可生成缩略图网格：

```shell
./Veetgem -i "视频文件路径"
```

除了按照上述方法使用编译好的可执行文件以外，还可以通过运行源码或者自行编译的方式来使用，这里就不再赘述了。

### 参数说明

除了上面演示的用于表示视频文件路径的`-i`参数外，程序还有其它的可选参数：

- `-i`或`--input`：视频文件路径，**必填**。 (默认: None)
- `-o`或`--output`：图片的保存路径。如未提供，其将被保存在视频文件所在目录下，并与视频文件同名。如提供，请确保路径结尾包含文件名及后缀。 (默认: None)
- `--number`：输入两个数字表示截图的行数和列数并以空格分开。默认为 4 行 4 列总计 16 张。 (默认: [4, 4])
- `--padding`：截图之间的距离。 (默认: 30)
- `--radius`：截图的圆角效果（设为 0 即无圆角效果）。 (默认: 0)
- `-w`或`--width`：输出图片的最终宽度（像素），高度将等比缩放。设为 0 则不缩放。 (默认: 1920)
- `--font_size`：标记截图时间和在顶部显示视频信息的字体的大小。 (默认: 100)
- `--bg_color`：图片背景颜色 (RGB格式，例如 255,255,255 )。 (默认: (255, 255, 255))
- `--info_bar_height`：顶部视频信息栏的高度。 (默认: 100)

## 开发

### 环境

- Python 3.13
- PyCharm 2025.1.1.1

### 依赖

- opencv-python
- pillow

```shell
pip3 install opencv-python pillow
```

### 打包

安装 PyInstaller ：

```shell
pip3 install pyinstaller
```

`cd`至`video_thumbnail_grid_maker.py`文件所在目录下，执行：

```shell
pyinstaller --name Veetgem --onefile video_thumbnail_grid_maker.py
```

应该就可以打包出运行在当前平台的可执行文件。

## 效果展示

|     最终生成的缩略图网格展示     |
|:--------------------:|
| ![](output_demo.jpg) |
|    截图来自《我的女友是妖怪》     |  

## 后续计划

- [ ] 若视频内嵌字幕，则截图时可选择是否包含字幕；
