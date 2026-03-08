import os
from datetime import timedelta
from PIL import Image, ImageDraw, ImageFont
from i18n import TRANSLATIONS


class ImageEngine:
    """负责预览图的拼接、绘制和保存"""

    def __init__(self):
        # 字体检测路径
        self.font_paths = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/Library/Fonts/Arial Unicode.ttf"
        ]

    def get_font(self, size):
        for p in self.font_paths:
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size, index=0)
                except Exception:
                    continue
        return ImageFont.load_default()

    @staticmethod
    def format_time(seconds):
        td = timedelta(seconds=int(seconds))
        return str(td)

    def create_grid_preview(self, video_info, thumb_files, settings):
        """核心拼接逻辑"""
        # 参数解析
        rows, cols = settings.get('rows', 4), settings.get('cols', 4)
        target_width = settings.get('width', 1920)
        margin = settings.get('margin', 10)
        show_header = settings.get('show_header', True)
        show_timestamp = settings.get('show_timestamp', True)
        lang = settings.get('lang', 'zh')

        scale = target_width / 1920.0
        aspect_ratio = video_info['height'] / video_info['width']
        thumb_width = (target_width - (cols + 1) * margin) // cols
        thumb_height = int(thumb_width * aspect_ratio)

        # 画布与头部高度
        header_height = int(115 * scale) if show_header else 0
        total_height = rows * thumb_height + (rows + 1) * margin + header_height

        canvas = Image.new('RGB', (target_width, total_height), 'white')
        draw = ImageDraw.Draw(canvas)

        font_info = self.get_font(int(28 * scale))
        font_ts = self.get_font(int(28 * scale))

        # 1. 绘制头部
        if show_header:
            t = TRANSLATIONS[lang]
            header_text = [
                f"{t['info_size']}: {video_info['size_mb']:.2f} MB  |  {t['info_res']}: {video_info['width']}x{video_info['height']}  |  {t['info_duration']}: {self.format_time(video_info['duration'])}",
                f"{t['info_codec']}: {video_info['codec'].upper()}  |  {t['info_fps']}: {video_info['fps']} fps  |  {t['info_bitrate']}: {video_info['bitrate_kbps']:.0f} kbps"
            ]
            y_cursor = int(30 * scale)
            draw.text((margin * 2, y_cursor), header_text[0], font=font_info, fill="black")
            y_cursor += int(45 * scale)
            draw.text((margin * 2, y_cursor), header_text[1], font=font_info, fill="black")

        # 2. 拼接缩略图
        for i, (path, ts) in enumerate(thumb_files):
            if not os.path.exists(path): continue

            row, col = i // cols, i % cols
            x = col * (thumb_width + margin) + margin
            y = row * (thumb_height + margin) + margin + header_height

            with Image.open(path) as img:
                img = img.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                canvas.paste(img, (x, y))

            # 绘制时间戳
            if show_timestamp:
                ts_text = self.format_time(ts)
                bbox = draw.textbbox((0, 0), ts_text, font=font_ts)
                # 从源头转换为整数
                ts_w = int(bbox[2] - bbox[0])
                ts_h = int(bbox[3] - bbox[1])
                ts_margin = int(12 * scale)

                # 现在所有的参与运算的变量都是 int
                tx = x + thumb_width - ts_w - ts_margin * 2
                ty = y + thumb_height - ts_h - ts_margin * 2

                # 半透明遮罩 (尺寸和坐标现在都是纯正的 int 组成的 tuple)
                overlay = Image.new('RGBA', (ts_w + 16, ts_h + 12), (0, 0, 0, 160))
                canvas.paste(overlay, (tx - 8, ty - 4), overlay)
                draw.text((tx, ty), ts_text, font=font_ts, fill="white")

            os.remove(path)

        # 3. 保存
        output_dir = settings.get('output_dir') or os.path.dirname(thumb_files[0][0])  # 临时修正 fallback
        custom_name = settings.get('custom_name', "")

        if not custom_name:
            base = os.path.splitext(video_info['filename'])[0]
            out_name = f"{base}_preview.jpg"
        else:
            out_name = custom_name if custom_name.lower().endswith(".jpg") else custom_name + ".jpg"

        final_path = os.path.join(output_dir, out_name)
        canvas.save(final_path, 'JPEG', quality=90)
        return final_path
