#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
这是一个Clash Verge脚本还原工具，用于还原备份的全局脚本
"""

import os
from pathlib import Path

# 导入核心模块
from clash_verge_core import (
    get_profiles_directory,
    find_backup_files,
    extract_backup_time,
    get_original_name,
    restore_backup
)

def interactive_restore():
    """交互式还原备份"""
    print("Clash Verge备份还原工具")
    print("-" * 50)
    
    backups = find_backup_files()
    if not backups:
        print("未找到备份文件")
        return
    
    print("找到以下备份文件:")
    for i, file_path in enumerate(backups, 1):
        time_str = extract_backup_time(file_path)
        print(f"{i}. {file_path.name} (备份于 {time_str})")
    
    choice = input("请选择要还原的备份文件 (输入编号，或输入q取消): ")
    if choice.lower() == 'q':
        print("取消还原操作")
        return
    
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(backups):
            print("无效的选择")
            return
        
        backup_file = backups[idx]
        
        # 确认还原
        confirm = input(f"确定要还原 {backup_file.name} 吗? (y/n): ")
        if confirm.lower() != 'y':
            print("取消还原操作")
            return
            
        # 还原备份
        success, message = restore_backup(backup_file)
        if success:
            print(f"{message}")
            print("请重启Clash Verge以应用更改")
        else:
            print(f"还原失败: {message}")
    
    except Exception as e:
        print(f"发生错误: {e}")

def restore_backup_by_index(idx):
    """通过索引还原备份
    
    参数:
        idx: 备份文件的索引（从1开始）
        
    返回:
        (成功状态, 信息消息)
    """
    try:
        backups = find_backup_files()
        if not backups:
            return False, "未找到备份文件"
        
        if idx < 1 or idx > len(backups):
            return False, "无效的备份索引"
        
        backup_file = backups[idx - 1]
        return restore_backup(backup_file)
        
    except Exception as e:
        return False, f"还原备份时出错: {e}"

def restore_backup_by_name(backup_name):
    """通过文件名还原备份
    
    参数:
        backup_name: 备份文件名
        
    返回:
        (成功状态, 信息消息)
    """
    try:
        profiles_dir = get_profiles_directory()
        backup_file = profiles_dir / backup_name
        
        if not backup_file.exists():
            return False, f"备份文件不存在: {backup_name}"
        
        return restore_backup(backup_file)
        
    except Exception as e:
        return False, f"还原备份时出错: {e}"

def main():
    """主函数"""
    try:
        import sys
        
        # 如果提供了备份索引，直接还原
        if len(sys.argv) > 1:
            try:
                idx = int(sys.argv[1])
                success, message = restore_backup_by_index(idx)
                if success:
                    print(f"{message}")
                    print("请重启Clash Verge以应用更改")
                else:
                    print(f"还原失败: {message}")
                return
            except ValueError:
                # 如果不是数字，当作文件名处理
                backup_name = sys.argv[1]
                success, message = restore_backup_by_name(backup_name)
                if success:
                    print(f"{message}")
                    print("请重启Clash Verge以应用更改")
                else:
                    print(f"还原失败: {message}")
                return
        
        # 交互式还原
        interactive_restore()
        
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main() 