import os
from PySide6.QtCore import QLocale

# 语言翻译字典
TRANSLATIONS = {
    'zh': {
        'window_title': "Veetgem - 视频网格预览图生成器",
        'file_list_label': "待处理视频 (拖拽文件或文件夹到此处):",
        'btn_add': "添加视频",
        'btn_remove': "移除选中",
        'btn_clear': "清空列表",
        'settings_group': "软件设置",
        'rows': "行数:",
        'cols': "列数:",
        'width': "输出宽度 (px):",
        'show_header': "显示视频基本信息",
        'show_timestamp': "显示截图时间戳",
        'margin': "间距 (px):",
        'output_path': "输出路径:",
        'browse': "浏览...",
        'custom_name': "自定义文件名:",
        'output_placeholder': "默认与原文件相同",
        'filename_placeholder': "默认: 原文件名_preview.jpg",
        'btn_start': "开始生成",
        'processing': "处理中...",
        'status_ready': "就绪",
        'status_done': "处理完成",
        'status_error': "出现错误",
        'msg_no_files': "请先添加视频文件！",
        'msg_success': "成功处理 {} 个视频！",
        'msg_error_title': "错误",
        'msg_error_content': "处理过程中出现错误:\n{}",
        'lang_btn': "English",
        'info_size': "大小",
        'info_res': "分辨率",
        'info_duration': "时长",
        'info_codec': "编码",
        'info_fps': "帧率",
        'info_bitrate': "比特率",
        'status_extracting': "正在提取第 {}/{} 张截图"
    },
    'en': {
        'window_title': "Veetgem - Video Thumbnail Grid Maker",
        'file_list_label': "Videos (Drag files or folders here):",
        'btn_add': "Add Videos",
        'btn_remove': "Remove Selected",
        'btn_clear': "Clear List",
        'settings_group': "Settings",
        'rows': "Rows:",
        'cols': "Cols:",
        'width': "Output Width (px):",
        'show_header': "Show Video Info Header",
        'show_timestamp': "Show Timestamps",
        'margin': "Margin (px):",
        'output_path': "Output Path:",
        'browse': "Browse...",
        'custom_name': "Custom Filename:",
        'output_placeholder': "Same as source folder",
        'filename_placeholder': "Default: original_name_preview.jpg",
        'btn_start': "Generate",
        'processing': "Processing...",
        'status_ready': "Ready",
        'status_done': "Finished",
        'status_error': "Error occurred",
        'msg_no_files': "Please add video files first!",
        'msg_success': "Successfully processed {} videos!",
        'msg_error_title': "Error",
        'msg_error_content': "An error occurred during processing:\n{}",
        'lang_btn': "中文",
        'info_size': "Size",
        'info_res': "Resolution",
        'info_duration': "Duration",
        'info_codec': "Codec",
        'info_fps': "FPS",
        'info_bitrate': "Bitrate",
        'status_extracting': "Extracting {}/{}"
    }
}


def detect_system_lang():
    """多级激进检测系统显示语言"""
    # 1. 尝试 Qt 标准 API
    loc = QLocale.system()
    if loc.language() == QLocale.Language.Chinese:
        return 'zh'
    if any('zh' in l.lower() for l in loc.uiLanguages()):
        return 'zh'

    # 2. 尝试系统环境变量 (针对 IDE 终端或特殊环境)
    for env_var in ['LANG', 'LANGUAGE', 'LC_ALL', 'LC_MESSAGES']:
        if 'zh' in os.environ.get(env_var, '').lower():
            return 'zh'

    # 3. 兜底方案：尝试通过 macOS defaults 命令识别
    try:
        import subprocess
        res = subprocess.run(['defaults', 'read', '-g', 'AppleLanguages'],
                             capture_output=True, text=True, timeout=1)
        if 'zh' in res.stdout.lower():
            return 'zh'
    except Exception:
        pass

    return 'en'
