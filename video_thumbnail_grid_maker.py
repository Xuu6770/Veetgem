import argparse
import os
import cv2
from PIL import Image, ImageDraw, ImageFont


# 为截图添加圆角效果
def create_rounded_rectangle(image, radius):
    # 创建一个与帧图像相同大小的黑色矩形，L 模式表示 8 位像素
    mask = Image.new("L", image.size, 0)

    # 创建一个与帧图像相同大小的白色圆角矩形，黑白两个图像形成掩码
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), image.size], radius=radius, fill=255)

    # 应用透明度并返回图像
    image.putalpha(mask)
    return image


# 在截图上标注其所对应的时间
def add_time_text_to_frame(img, font_size, text):
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=font_size)

    # 获取图片尺寸
    img_w, img_h = img.size

    # 计算文本尺寸
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # 计算文本位置（居中偏下）
    text_position = ((img_w - text_w) / 2, (img_h - text_h) / 2 + img_h / 4)

    # 绘制文本
    draw.text(text_position, text, font=font, fill=(255, 255, 255))  # 白色字体

    return img


def create_thumbnail_grid(video_path,
                          output_image_path,
                          cols_and_rows,
                          screenshot_padding=30,
                          screenshot_corner_radius=0,
                          final_pic_width=1920,
                          font_size=100,
                          bg_color=(255, 255, 255),
                          info_bar_height=100):
    # 载入视频，如果无法读取则抛出异常
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("无法读取视频文件，请检查视频路径是否正确或视频格式是否合法。")

    # 计算视频总帧数和帧间隔，用于均匀地从视频中提取帧
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = total_frames // (cols_and_rows[0] * cols_and_rows[1])

    # 将从视频中提取的指定数量的帧存储在 frames 列表中
    frames = []
    # 每一帧对应其在视频中的时间存储在 frame_times 列表中
    frame_times = []

    # 开始提取指定数量的帧
    for i in range(cols_and_rows[0] * cols_and_rows[1]):
        # 考虑到大部分影片的开头可能都是黑色过渡或者是只有制作方 Logo 等没有意义的画面，
        # 故而对于第一张图片，将不会直接在 00:00 截取，而是往后推移帧间隔的 1/3 再截取。
        if i == 0:
            first_screenshot_frame = frame_interval // 3
            # 将视频的当前位置设置到特定帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, first_screenshot_frame)
            frame_times.append(first_screenshot_frame)
        else:
            cap.set(cv2.CAP_PROP_POS_FRAMES, i * frame_interval)
            frame_times.append(i * frame_interval)

        # 读取当前位置的视频帧，ret 表示是否成功读取帧，frame 是读取到的帧图像数据
        ret, frame = cap.read()
        # 如果读取失败意味着可能已到达视频末尾，那么就跳出循环
        if not ret:
            break

        # 将帧的颜色空间从 BGR（OpenCV 默认）转换为 RGB ，因为大多数图像处理库使用 RGB 格式
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # 将转换后的帧转换为 PIL 的 Image 对象，并添加到 frames 列表中
        frames.append(Image.fromarray(frame))

    if not frames:
        raise ValueError("未能从视频中提取到帧。")

    # 记录单帧宽度和高度
    width, height = frames[0].size
    # 计算拼接完成后的图像的宽度和高度
    grid_width = width * cols_and_rows[1] + screenshot_padding * (cols_and_rows[1] + 1)
    grid_height = height * cols_and_rows[0] + \
                  screenshot_padding * (cols_and_rows[0] + 1) + info_bar_height
    # 创建一张背景板
    grid_image = Image.new("RGBA", (grid_width, grid_height), bg_color)

    # 将每一帧放置到背景板中适当的位置
    for idx, frame in enumerate(frames):
        # 计算当前帧在背景板中的位置
        row = idx // cols_and_rows[1]
        col = idx % cols_and_rows[1]
        x = col * (width + screenshot_padding) + screenshot_padding
        y = row * (height + screenshot_padding) + screenshot_padding + info_bar_height

        # 如果用户设置了圆角的大小，则需要对图片进行圆角处理
        if screenshot_corner_radius > 0:
            frame = create_rounded_rectangle(
                frame.convert("RGBA"), radius=screenshot_corner_radius)

        # 获取视频的 FPS
        fps = cap.get(cv2.CAP_PROP_FPS)
        # 计算当前帧在视频中对应的时间（单位：秒）
        time_in_seconds = frame_times[idx] / fps
        # 转换为分钟和秒并格式化
        minutes = int(time_in_seconds // 60)
        seconds = int(time_in_seconds % 60)
        time_of_the_frame = f"{minutes:02d}:{seconds:02d}"
        # 为截图标注其对应的时间
        frame = add_time_text_to_frame(frame, font_size, time_of_the_frame)

        # 根据 frame 的模式决定如何粘贴
        if frame.mode == 'RGBA':
            # 如果 frame 是 RGBA (例如有圆角)，使用其 alpha 通道作为蒙版
            grid_image.paste(frame, (x, y), frame)
        elif frame.mode == 'RGB':
            # 如果 frame 是 RGB (例如无圆角的普通帧)，直接粘贴，不需要蒙版
            grid_image.paste(frame, (x, y))
        else:
            # 对于其他可能的模式，或者为了保险，可以先转换为 RGBA 再粘贴
            # (通常 OpenCV 转过来的帧在处理后会是 RGB 或 RGBA)
            print(f"警告: 帧的模式是 {frame.mode}，尝试转换为 RGBA 进行粘贴。")
            grid_image.paste(frame.convert("RGBA"), (x, y))

    # 在背景板顶部添加视频的分辨率和帧率信息
    draw = ImageDraw.Draw(grid_image)
    font = ImageFont.load_default(size=font_size)
    # 获取视频的分辨率和帧率信息
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_resolution = f"{video_width} X {video_height}"
    video_fps = f"{cap.get(cv2.CAP_PROP_FPS):.2f} FPS"
    video_info = f"{video_resolution} | {video_fps}"
    # 设置分辨率和帧率信息文本的展示位置
    text_x = screenshot_padding
    text_y = (info_bar_height - font_size) // 2  # 文本垂直居中
    # 绘制文本
    draw.text((text_x, text_y), video_info, fill=(0, 0, 0), font=font)

    # 根据设置的参数对最终图片的大小进行等比例缩放
    if final_pic_width > 0:
        scale_factor = final_pic_width / grid_width
        new_grid_width = final_pic_width
        new_grid_height = int(grid_height * scale_factor)

        # 调整图像的最终大小
        grid_image = grid_image.resize((new_grid_width, new_grid_height))
        grid_image = grid_image.convert("RGB")

    # 输出最终的图片
    grid_image.save(output_image_path)
    print(f"图片保存至: {output_image_path}")

    # 释放资源
    cap.release()


# 自定义类型转换函数，用于将 "R,G,B" 字符串转为元组
def rgb_color_type(value):
    try:
        r, g, b = map(int, value.split(','))
        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            raise ValueError("RGB颜色值必须在 0-255 之间。")
        return r, g, b
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"无效的颜色格式 '{value}'. 请使用 'R,G,B' (例如 '255,255,255'). {e}")


def main():
    # 配置 argparse
    parser = argparse.ArgumentParser(description="为视频文件生成预览网格图。",
                                     # 对帮助信息进行格式化以显示我所设置的默认值
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-i", "--input", required=True, help="视频文件路径。")
    parser.add_argument("-o", "--output", default=None,
                        help="图片保存路径。如未提供，将保存在视频文件所在目录下，并以视频文件名命名。如提供，请确保路径结尾包含文件名及后缀。")
    parser.add_argument("--number", nargs=2, default=[4, 4], type=int,
                        help="输入两个数字表示截图的行数和列数并以空格分开。默认为 4 行 4 列总计 16 张。",
                        metavar=("ROWS", "COLS"))
    parser.add_argument("--padding", default=30, type=int, help="截图之间的距离。")
    parser.add_argument("--radius", default=0, type=int, help="截图的圆角效果（设为 0 即无圆角效果）。")
    parser.add_argument("-w", "--width", default=1920, type=int,
                        help="输出图片的最终宽度（像素），高度将等比缩放。设为 0 则不缩放。", dest="final_pic_width")
    parser.add_argument("--font_size", default=100, type=int, help="标记截图时间和在顶部显示视频信息的字体的大小。")
    parser.add_argument("--bg_color", default=(255, 255, 255), type=rgb_color_type,
                        help="图片背景颜色 (RGB格式，例如 255,255,255 )。", metavar="R,G,B")
    parser.add_argument("--info_bar_height", default=100, type=int, help="顶部视频信息栏的高度。")

    args = parser.parse_args()

    # 处理默认输出路径
    output_path = args.output
    if output_path is None or output_path.strip() == "":
        video_dir = os.path.dirname(args.input)
        video_filename_without_ext = os.path.splitext(os.path.basename(args.input))[0]
        output_path = os.path.join(video_dir, f"{video_filename_without_ext}.jpg")

    # 调用创建缩略图网格的函数并传入参数
    create_thumbnail_grid(video_path=args.input,
                          output_image_path=output_path,
                          cols_and_rows=args.number,
                          screenshot_padding=args.padding,
                          screenshot_corner_radius=args.radius,
                          final_pic_width=args.final_pic_width,
                          font_size=args.font_size,
                          bg_color=args.bg_color,
                          info_bar_height=args.info_bar_height)


if __name__ == "__main__":
    main()
