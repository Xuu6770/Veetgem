<h1 align = "center">Veetgem</h1>

<p align = "center">
    A video thumbnail grid maker to quickly preview multiple frames of a movie.
</p>

<p align = "center">
    <a href = "README.md" target = "_blank">EN</a> | <a href = "README_CN.md" target = "_blank">CN</a>
</p>

## Features

- [x] Supports common video formats such as `mp4`, `mkv`, and `avi`.
- [x] Each screenshot in the grid is labeled with its corresponding time in the video.
- [x] Customize the number of screenshots, such as 3 rows and 3 columns for a total of 9 screenshots, or 4 rows and 4 columns for a total of 16 screenshots.
- [x] Customize the width of the final image (height will be automatically adjusted proportionally).
- [x] Customize the distance between screenshots.
- [x] Customize the rounded corners of screenshots.

## Use

Currently, only executable files that run on macOS on Apple Silicon have been compiled and can be downloaded from the [release](https://github.com/Xuu6770/Veetgem/releases) page.

After downloading, open the terminal and `cd` to the directory where the executable file is located. Use the following command to generate the thumbnail grid:

```shell
./Veetgem -i "Video file path"
```

In addition to using the compiled executable file as described above, you can also use it by running the source code or compiling it yourself. We will not go into further detail here.

### Parameters

In addition to the `-i` parameter demonstrated above for specifying the video file path, the program has other optional parameters:

- `-i` or `--input`: Video file path, **required**. (Default: None)
- `-o` or `--output`: The save path for the image. If not specified, it will be saved in the same directory as the video file with the same name. If specified, make sure the path ends with the file name and extension. (Default: None)
- `--number`: Enter two numbers representing the number of rows and columns of the screenshot, separated by a space. The default is 4 rows and 4 columns, for a total of 16 images. (Default: [4, 4])
- `--padding`: The distance between screenshots. (Default: 30)
- `--radius`: Rounded corners effect for screenshots (set to 0 for no rounded corners effect). (Default: 0)
- `-w` or `--width`: The final width (in pixels) of the output image. The height will be scaled proportionally. Set to 0 to not scale. (Default: 1920)
- `--font_size`: Specifies the font size for marking the screenshot time and displaying video information at the top. (Default: 100)
- `--bg_color`: Image background color (RGB format, e.g., 255,255,255). (Default: (255, 255, 255))
- `--info_bar_height`: Height of the top video information bar. (Default: 100)

## Development

### Environment

- Python 3.13
- PyCharm 2025.1.1.1

### Dependencies

- opencv-python
- pillow

```shell
pip3 install opencv-python pillow
```

### Packaging

Install PyInstaller:

```shell
pip3 install pyinstaller
```

`cd` to the directory where the `video_thumbnail_grid_maker.py` file is located, and execute:

```shell
pyinstaller --name Veetgem --onefile video_thumbnail_grid_maker.py
```

This should package an executable file that runs on the current platform.

## Demo

|  Demo of the final generated grid thumbnail  |
|:--------------------------------------------:|
|             ![](output_demo.jpg)             |
| Screenshot from 《My Undead Yokai Girlfriend》 | 

## Todo

- [ ] If the video has embedded subtitles, you can choose whether to include the subtitles when taking a screenshot.
