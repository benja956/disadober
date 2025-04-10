#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Clash Verge核心模块 - 提供所有通用功能
"""

import os
import platform
import shutil
from pathlib import Path
from datetime import datetime

def get_clash_verge_directory():
    """获取Clash Verge配置文件目录"""
    system = platform.system()
    home = Path.home()
    
    if system == "Windows":
        return home / "AppData" / "Roaming" / "io.github.clash-verge-rev.clash-verge-rev"
    elif system == "Darwin":  # macOS
        return home / "Library" / "Application Support" / "io.github.clash-verge-rev"
    elif system == "Linux":
        return home / ".config" / "clash-verge"
    else:
        raise OSError(f"不支持的操作系统: {system}")

def get_profiles_directory():
    """获取Clash Verge配置文件的profiles目录"""
    return get_clash_verge_directory() / "profiles"

def find_global_script():
    """查找Clash Verge的全局脚本"""
    profiles_dir = get_profiles_directory()
    
    if not profiles_dir.exists():
        return None
    
    script_files = []
    
    # 查找名为 "script.js" 的全局脚本文件
    for file in profiles_dir.glob("*.js"):
        if file.name.lower() == "script.js":
            script_files.append(file)
    
    # 如果没有找到 script.js，则查找其他可能的脚本文件
    if not script_files:
        for file in profiles_dir.glob("*.js"):
            script_files.append(file)
    
    if not script_files:
        return None
    
    return script_files[0]

def backup_file(file_path):
    """备份文件，返回备份后的文件路径或None（如果失败）"""
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
        
    if not file_path.exists():
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = file_path.with_suffix(f".bak.{timestamp}")
    shutil.copy2(str(file_path), str(backup_path))
    return backup_path

def find_backup_files():
    """查找所有备份文件，返回列表[(文件路径, 备份时间)]"""
    profiles_dir = get_profiles_directory()
    
    if not profiles_dir.exists():
        return []
    
    backups = []
    for file in profiles_dir.glob("*.bak.*"):
        backups.append(file)
    
    return backups

def extract_backup_time(backup_file):
    """从备份文件名中提取备份时间"""
    try:
        if isinstance(backup_file, str):
            backup_file = Path(backup_file)
            
        # 从文件名中提取时间戳
        timestamp = backup_file.suffix.split('.')[-1]
        # 将时间戳转换为datetime对象
        dt = datetime.strptime(timestamp, "%Y%m%d%H%M%S")
        # 格式化为可读字符串
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "未知时间"

def get_original_name(backup_name):
    """从备份文件名中提取原始文件名"""
    # 移除 .bak.时间戳 后缀
    return backup_name.split(".bak.")[0]

def restore_backup(backup_path, auto_backup=True):
    """还原备份文件
    
    参数:
        backup_path: 要还原的备份文件路径
        auto_backup: 是否自动备份当前文件
        
    返回:
        (成功状态, 信息消息)
    """
    try:
        if isinstance(backup_path, str):
            backup_path = Path(backup_path)
            
        if not backup_path.exists():
            return False, f"备份文件不存在: {backup_path}"
        
        # 获取原始文件名和目标路径
        original_name = get_original_name(backup_path.name)
        destination = backup_path.parent / original_name
        
        # 备份当前文件
        if auto_backup and destination.exists():
            # 这里不再有变量名冲突，直接调用backup_file函数
            current_backup = backup_file(destination)
            if current_backup is None:
                return False, f"无法备份当前文件: {destination}"
        
        # 复制文件
        shutil.copy2(str(backup_path), str(destination))
        return True, f"已成功还原文件: {original_name}"
    
    except Exception as e:
        return False, f"还原备份时出错: {e}" 