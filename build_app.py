import os
import shutil
import subprocess


def build():
    # 1. 寻找 ffmpeg 和 ffprobe 路径
    ffmpeg_path = shutil.which('ffmpeg')
    ffprobe_path = shutil.which('ffprobe')

    if not ffmpeg_path or not ffprobe_path:
        print("错误: 未在系统中找到 ffmpeg 或 ffprobe。请确保已安装。")
        return

    print(f"找到 ffmpeg: {ffmpeg_path}")
    print(f"找到 ffprobe: {ffprobe_path}")

    # 2. 准备打包参数
    # --onedir: 解决启动慢的问题
    # --noconfirm: 自动覆盖
    # --windowed: 无控制台
    # --add-binary: 将 ffmpeg 打包进去

    cmd = [
        'pyinstaller',
        '--noconfirm',
        '--onedir',
        '--windowed',
        '--name', 'Veetgem',
        f'--add-binary={ffmpeg_path}:.',
        f'--add-binary={ffprobe_path}:.',
        '--clean',
        'main.py'
    ]

    print("开始打包...")
    subprocess.run(cmd)

    # 3. 整理结果 (macOS 特定)
    dist_path = os.path.join('dist', 'Veetgem.app')
    if os.path.exists(dist_path):
        print(f"\n打包成功! 你的软件位于: {os.path.abspath(dist_path)}")
        print("提示: 这个 .app 已经包含了 ffmpeg，且启动速度会非常快。")
    else:
        print("\n打包过程中可能出现了问题，请检查 dist 文件夹。")


if __name__ == "__main__":
    build()
