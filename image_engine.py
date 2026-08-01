import os
from PIL import Image, ImageDraw, ImageFont


class ImageEngine:
    """负责预览图的拼接、绘制和保存"""

    # 浅色底 + 深色字：大小 / 分辨率 / 时长 / 视频编码 / 音频编码 / 帧率 / 比特率
    CHIP_COLORS = [
        ((227, 242, 253), (21, 101, 192)),    # 蓝
        ((243, 229, 245), (123, 31, 162)),    # 紫
        ((224, 242, 241), (0, 105, 92)),      # 青
        ((255, 243, 224), (230, 81, 0)),      # 橙 — 视频编码
        ((232, 234, 246), (63, 81, 181)),     # 靛 — 音频编码
        ((232, 245, 233), (46, 125, 50)),     # 绿
        ((252, 228, 236), (194, 24, 91)),     # 粉
    ]

    @staticmethod
    def get_font(size):
        """使用 Pillow 内置可缩放默认字体，仅需拉丁字符，跨平台一致。"""
        size = max(int(size), 1)
        try:
            # Pillow >= 10.1：内置可缩放字体
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()

    @staticmethod
    def format_time(seconds):
        """时长/时间戳：不足 1 小时为 M:SS，否则为 H:MM:SS。"""
        total = max(int(seconds), 0)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    def _build_header_chips(self, video_info, scale, font):
        """构建头部胶囊标签：只显示参数值，不显示字段名。"""
        items = [
            f"{video_info['size_mb']:.2f} MB",
            f"{video_info['width']} x {video_info['height']}",
            self.format_time(video_info['duration']),
            video_info['codec'].upper(),
            video_info.get('audio_codec', 'none').upper(),
            f"{video_info['fps']} fps",
            f"{video_info['bitrate_kbps']:.0f} kbps",
        ]

        tmp = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        pad_x = int(20 * scale)
        pad_y = int(12 * scale)

        chips = []
        for i, text in enumerate(items):
            bbox = tmp.textbbox((0, 0), text, font=font)
            tw = int(bbox[2] - bbox[0])
            th = int(bbox[3] - bbox[1])
            bg, fg = self.CHIP_COLORS[i % len(self.CHIP_COLORS)]
            chips.append({
                'text': text,
                'tw': tw,
                'th': th,
                'w': tw + pad_x * 2,
                'h': th + pad_y * 2,
                'bg': bg,
                'fg': fg,
                'pad_x': pad_x,
                'pad_y': pad_y,
            })
        return chips

    def _layout_chips(self, chips, available_width, gap, start_x):
        """将标签按行排布，超出宽度时自动换行。返回 (layout, total_height)。"""
        rows = []
        current_row = []
        current_w = 0
        chip_h = chips[0]['h'] if chips else 0

        for chip in chips:
            need = chip['w'] if not current_row else chip['w'] + gap
            if current_row and current_w + need > available_width:
                rows.append(current_row)
                current_row = [chip]
                current_w = chip['w']
            else:
                current_w += need
                current_row.append(chip)
        if current_row:
            rows.append(current_row)

        row_gap = gap
        total_height = len(rows) * chip_h + max(0, len(rows) - 1) * row_gap

        layout = []
        y = 0
        for row in rows:
            row_w = sum(c['w'] for c in row) + gap * (len(row) - 1)
            x = start_x + max(0, (available_width - row_w) // 2)
            for chip in row:
                layout.append((chip, x, y))
                x += chip['w'] + gap
            y += chip_h + row_gap

        return layout, total_height

    def _prepare_header(self, video_info, scale, margin, target_width):
        """预计算头部胶囊布局与高度，供画布尺寸与绘制共用。"""
        font = self.get_font(int(24 * scale))
        chips = self._build_header_chips(video_info, scale, font)
        side_pad = margin * 2
        gap = int(14 * scale)
        v_pad = int(22 * scale)
        layout, content_h = self._layout_chips(chips, target_width - side_pad * 2, gap, side_pad)
        return {
            'font': font,
            'layout': layout,
            'v_pad': v_pad,
            'height': content_h + v_pad * 2,
        }

    def _draw_header(self, draw, header, target_width, scale):
        """根据预计算结果绘制胶囊式元数据头部。"""
        header_height = header['height']
        font = header['font']
        v_pad = header['v_pad']

        draw.rectangle([0, 0, target_width, header_height], fill=(248, 249, 250))
        line_y = header_height - max(1, int(2 * scale))
        draw.rectangle([0, line_y, target_width, header_height], fill=(230, 232, 235))

        for chip, x, y_off in header['layout']:
            y = v_pad + y_off
            radius = chip['h'] // 2
            draw.rounded_rectangle(
                [x, y, x + chip['w'], y + chip['h']],
                radius=radius,
                fill=chip['bg'],
            )
            bbox = draw.textbbox((0, 0), chip['text'], font=font)
            text_x = x + chip['pad_x'] - bbox[0]
            text_y = y + (chip['h'] - chip['th']) // 2 - bbox[1]
            draw.text((text_x, text_y), chip['text'], font=font, fill=chip['fg'])

    def create_grid_preview(self, video_info, thumb_files, settings):
        """核心拼接逻辑"""
        rows, cols = settings.get('rows', 4), settings.get('cols', 4)
        target_width = settings.get('width', 1920)
        margin = settings.get('margin', 10)
        show_header = settings.get('show_header', True)
        show_timestamp = settings.get('show_timestamp', True)

        scale = target_width / 1920.0
        aspect_ratio = video_info['height'] / video_info['width']
        thumb_width = (target_width - (cols + 1) * margin) // cols
        thumb_height = int(thumb_width * aspect_ratio)

        header = None
        if show_header:
            header = self._prepare_header(video_info, scale, margin, target_width)
            header_height = header['height']
        else:
            header_height = 0

        total_height = rows * thumb_height + (rows + 1) * margin + header_height

        canvas = Image.new('RGB', (target_width, total_height), 'white')
        draw = ImageDraw.Draw(canvas)

        font_ts = self.get_font(int(28 * scale))

        if header is not None:
            self._draw_header(draw, header, target_width, scale)

        for i, (path, ts) in enumerate(thumb_files):
            if not os.path.exists(path):
                continue

            row, col = i // cols, i % cols
            x = col * (thumb_width + margin) + margin
            y = row * (thumb_height + margin) + margin + header_height

            with Image.open(path) as img:
                img = img.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                canvas.paste(img, (x, y))

            if show_timestamp:
                # FreeType 默认字体的 textbbox 在 (0,0) 下 top/left 可能非零；
                # 背景框必须按“墨水范围”尺寸计算，绘制时再减去 bearing 偏移。
                ts_text = self.format_time(ts)
                bbox = draw.textbbox((0, 0), ts_text, font=font_ts)
                ts_w = int(bbox[2] - bbox[0])
                ts_h = int(bbox[3] - bbox[1])
                pad_x = max(int(8 * scale), 6)
                pad_y = max(int(6 * scale), 4)
                edge = max(int(8 * scale), 6)

                box_w = ts_w + pad_x * 2
                box_h = ts_h + pad_y * 2
                box_x = x + thumb_width - box_w - edge
                box_y = y + thumb_height - box_h - edge

                overlay = Image.new('RGBA', (box_w, box_h), (0, 0, 0, 160))
                canvas.paste(overlay, (box_x, box_y), overlay)

                text_x = box_x + pad_x - bbox[0]
                text_y = box_y + pad_y - bbox[1]
                draw.text((text_x, text_y), ts_text, font=font_ts, fill="white")

            os.remove(path)

        output_dir = settings.get('output_dir') or os.path.dirname(thumb_files[0][0])
        custom_name = settings.get('custom_name', "")

        if not custom_name:
            base = os.path.splitext(video_info['filename'])[0]
            out_name = f"{base}_preview.jpg"
        else:
            out_name = custom_name if custom_name.lower().endswith(".jpg") else custom_name + ".jpg"

        final_path = os.path.join(output_dir, out_name)
        canvas.save(final_path, 'JPEG', quality=90)
        return final_path
