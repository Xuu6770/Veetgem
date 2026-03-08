import os
import subprocess
import json
import sys


class VideoEngine:
    """负责视频元数据获取和 FFmpeg 帧提取"""

    @staticmethod
    def get_bin_path(name):
        """获取二进制文件路径：兼容开发环境和打包环境"""
        if getattr(sys, 'frozen', False):
            # 打包后的路径 (macOS .app 内部资源目录)
            # PyInstaller 打包后的资源路径在 sys._MEIPASS
            base_path = sys._MEIPASS
            return os.path.join(base_path, name)
        return name  # 开发环境直接用系统 PATH

    @staticmethod
    def get_video_info(video_path):
        """使用 ffprobe 获取视频元数据"""
        ffprobe_path = VideoEngine.get_bin_path('ffprobe')
        cmd = [
            ffprobe_path, '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to read video info: {video_path}")

        data = json.loads(result.stdout)
        video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
        format_info = data['format']

        if not video_stream:
            raise Exception("No video stream found.")

        # 计算帧率
        fps_str = video_stream.get('avg_frame_rate', '0/0')
        try:
            num, den = map(int, fps_str.split('/'))
            fps = num / den if den != 0 else 0
        except Exception:
            fps = 0

        return {
            'duration': float(format_info.get('duration', 0)),
            'width': int(video_stream.get('width', 0)),
            'height': int(video_stream.get('height', 0)),
            'filename': os.path.basename(video_path),
            'size_mb': os.path.getsize(video_path) / (1024 * 1024),
            'codec': video_stream.get('codec_name', 'unknown'),
            'fps': round(fps, 2),
            'bitrate_kbps': int(format_info.get('bit_rate', 0)) / 1000
        }

    @staticmethod
    def extract_frame(video_path, timestamp, output_path):
        """使用 FFmpeg 提取单帧，启用 Apple Silicon 硬件加速"""
        ffmpeg_path = VideoEngine.get_bin_path('ffmpeg')
        cmd = [
            ffmpeg_path, '-y',
            '-hwaccel', 'videotoolbox',
            '-ss', str(timestamp),
            '-i', video_path,
            '-frames:v', '1',
            '-q:v', '2',
            output_path
        ]
        subprocess.run(cmd, capture_output=True)
