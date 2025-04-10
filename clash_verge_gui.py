#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Clash Verge GUI工具 - 提供图形化界面
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
from pathlib import Path
from datetime import datetime

# 导入核心模块
from clash_verge_core import (
    find_backup_files, 
    extract_backup_time, 
    get_original_name,
    restore_backup
)

# 导入Adobe屏蔽模块
from clash_verge_adobe_block import (
    modify_clash_verge_script,
    download_adobe_block_list,
    try_download_with_custom_proxy,
    BUILTIN_ADOBE_DOMAINS
)

# 设置GUI样式
ttk_style = None
try:
    # 尝试导入sun-valley-ttk主题
    import sv_ttk
    has_sv_ttk = True
except ImportError:
    has_sv_ttk = False

class RedirectText:
    """重定向文本到Tkinter文本控件"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""

    def write(self, string):
        self.buffer += string
        if self.text_widget:
            self.text_widget.configure(state="normal")
            self.text_widget.insert(tk.END, string)
            self.text_widget.see(tk.END)
            self.text_widget.configure(state="disabled")
            self.text_widget.update()

    def flush(self):
        pass

class ManualDomainsDialog:
    """手动输入域名对话框"""
    def __init__(self, parent):
        self.domains = []
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("手动输入域名")
        self.dialog.geometry("500x400")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        ttk.Label(self.dialog, text="请输入Adobe域名列表，每行一个域名：").pack(pady=(10, 5))
        
        frame = ttk.Frame(self.dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.text = scrolledtext.ScrolledText(frame)
        self.text.pack(fill=tk.BOTH, expand=True)
        
        # 预填充内置域名以方便用户编辑
        for domain in BUILTIN_ADOBE_DOMAINS:
            self.text.insert(tk.END, domain + "\n")
        
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="确定", command=self.on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.on_cancel).pack(side=tk.RIGHT, padx=5)
        
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        parent.wait_window(self.dialog)
    
    def on_ok(self):
        text = self.text.get("1.0", tk.END).strip()
        if text:
            self.domains = [line.strip() for line in text.split("\n") if line.strip()]
        self.dialog.destroy()
    
    def on_cancel(self):
        self.dialog.destroy()

class ClashVergeApp:
    """Clash Verge GUI应用"""
    def __init__(self, root):
        self.root = root
        self.root.title("Clash Verge 工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置应用图标
        try:
            # 这里可以添加图标
            pass
        except:
            pass
        
        # 创建输出重定向
        self.text_redirect = RedirectText(None)
        
        # 创建状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        
        # 创建选项卡
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建Adobe屏蔽选项卡
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="Adobe屏蔽")
        self.init_adobe_tab()
        
        # 创建还原备份选项卡
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="还原备份")
        self.init_restore_tab()
    
    def init_adobe_tab(self):
        """初始化Adobe屏蔽选项卡"""
        frame = ttk.Frame(self.tab1, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="应用Adobe屏蔽规则", command=self.apply_adobe_block).pack(side=tk.LEFT, padx=5)
        
        # 创建输出区域
        output_frame = ttk.LabelFrame(frame, text="输出日志")
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.adobe_text = scrolledtext.ScrolledText(output_frame, state="disabled")
        self.adobe_text.pack(fill=tk.BOTH, expand=True)
        
        # 更新输出重定向
        self.text_redirect.text_widget = self.adobe_text
    
    def init_restore_tab(self):
        """初始化还原备份选项卡"""
        frame = ttk.Frame(self.tab2, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建备份列表
        list_frame = ttk.LabelFrame(frame, text="备份文件")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建Treeview显示备份列表
        columns = ("文件名", "备份时间", "文件大小", "修改时间")
        self.backup_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列
        for col in columns:
            self.backup_tree.heading(col, text=col)
        
        self.backup_tree.column("文件名", width=250)
        self.backup_tree.column("备份时间", width=150)
        self.backup_tree.column("文件大小", width=100)
        self.backup_tree.column("修改时间", width=150)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=scrollbar.set)
        
        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="刷新列表", command=self.refresh_backup_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="还原选中备份", command=self.restore_backup).pack(side=tk.LEFT, padx=5)
        
        # 创建输出区域
        output_frame = ttk.LabelFrame(frame, text="输出日志")
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.restore_text = scrolledtext.ScrolledText(output_frame, state="disabled")
        self.restore_text.pack(fill=tk.BOTH, expand=True)
        
        # 初始加载备份列表
        self.refresh_backup_list()
    
    def show_message(self, title, message):
        """显示消息框"""
        messagebox.showinfo(title, message)
    
    def apply_adobe_block(self):
        """应用Adobe屏蔽规则"""
        # 禁用按钮
        for widget in self.tab1.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        child.configure(state="disabled")
        
        self.status_var.set("正在应用Adobe屏蔽规则...")
        
        # 在新线程中运行，避免界面冻结
        def run_block():
            try:
                # 保存原始输出并重定向
                old_stdout = sys.stdout
                sys.stdout = self.text_redirect
                
                print("正在下载Adobe屏蔽列表...")
                
                # 下载Adobe屏蔽列表
                domains = download_adobe_block_list()
                if not domains:
                    # 如果内置代理都失败，询问用户
                    print("无法通过内置代理下载Adobe屏蔽名单。")
                    if messagebox.askyesno("下载失败", "无法通过内置代理下载Adobe屏蔽名单。\n是否输入自定义GitHub代理地址？"):
                        custom_proxy = simpledialog.askstring("输入代理", "请输入GitHub代理地址（例如：https://example.com/）:")
                        if custom_proxy:
                            print(f"尝试使用自定义代理: {custom_proxy}")
                            domains = try_download_with_custom_proxy(custom_proxy)
                    
                    # 如果依然失败，询问用户是否手动输入
                    if not domains:
                        print("无法下载Adobe屏蔽名单。")
                        if messagebox.askyesno("下载失败", "无法下载Adobe屏蔽名单。\n是否手动输入域名列表？"):
                            dialog = ManualDomainsDialog(self.root)
                            domains = dialog.domains
                            if domains:
                                print(f"已手动输入 {len(domains)} 个域名")
                    
                    # 如果用户没有输入域名，使用内置域名
                    if not domains:
                        print("使用内置的Adobe域名列表")
                        domains = BUILTIN_ADOBE_DOMAINS
                
                print(f"成功获取到 {len(domains)} 个Adobe相关域名")
                
                # 应用Adobe屏蔽规则
                print("正在应用Adobe屏蔽规则...")
                success, message = modify_clash_verge_script(domains)
                
                if success:
                    print(message)
                    print("Adobe屏蔽规则已应用。请重启Clash Verge以生效。")
                    self.show_message("成功", "Adobe屏蔽规则已应用。\n请重启Clash Verge以生效。")
                    
                    # 刷新备份列表
                    self.refresh_backup_list()
                else:
                    print(f"错误: {message}")
                    self.show_message("错误", message)
            
            except Exception as e:
                print(f"发生错误: {e}")
                self.show_message("错误", f"发生错误: {e}")
            
            finally:
                # 恢复标准输出
                sys.stdout = old_stdout
                
                # 恢复按钮状态
                def enable_buttons():
                    for widget in self.tab1.winfo_children():
                        if isinstance(widget, ttk.Frame):
                            for child in widget.winfo_children():
                                if isinstance(child, ttk.Button):
                                    child.configure(state="normal")
                    self.status_var.set("就绪")
                
                # 在主线程中恢复按钮状态
                self.root.after(0, enable_buttons)
        
        # 启动线程
        threading.Thread(target=run_block, daemon=True).start()
    
    def refresh_backup_list(self):
        """刷新备份文件列表"""
        # 清空当前列表
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        # 获取备份文件
        backup_files = find_backup_files()
        
        # 如果没有找到备份文件
        if not backup_files:
            self.status_var.set("未找到备份文件")
            return
        
        # 显示备份文件
        for backup_file in backup_files:
            backup_time = extract_backup_time(backup_file)
            
            # 获取文件大小
            file_size = os.path.getsize(backup_file)
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            
            # 获取修改时间
            mtime = os.path.getmtime(backup_file)
            mod_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            self.backup_tree.insert("", "end", values=(backup_file.name, backup_time, size_str, mod_time), tags=(str(backup_file),))
        
        self.status_var.set(f"找到 {len(backup_files)} 个备份文件")
    
    def restore_backup(self):
        """还原选中的备份"""
        # 获取选中的项
        selected = self.backup_tree.selection()
        if not selected:
            self.show_message("提示", "请先选择要还原的备份文件")
            return
        
        # 获取备份文件路径
        selected_item = selected[0]
        backup_name = self.backup_tree.item(selected_item)['values'][0]
        backup_path = None
        
        # 查找对应的备份文件
        for file in find_backup_files():
            if file.name == backup_name:
                backup_path = file
                break
        
        if not backup_path:
            self.show_message("错误", f"找不到备份文件: {backup_name}")
            return
        
        # 确认还原
        if not messagebox.askyesno("确认", f"确定要还原备份文件 {backup_name} 吗？"):
            return
        
        # 禁用按钮
        for widget in self.tab2.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        child.configure(state="disabled")
        
        self.status_var.set("正在还原备份...")
        
        # 在新线程中运行，避免界面冻结
        def run_restore():
            try:
                # 重定向输出
                old_stdout = sys.stdout
                sys.stdout = RedirectText(self.restore_text)
                
                print(f"正在还原备份: {backup_name}")
                
                # 还原备份
                success, message = restore_backup(backup_path)
                
                if success:
                    print(message)
                    print("请重启Clash Verge以应用更改")
                    self.show_message("成功", f"{message}\n请重启Clash Verge以应用更改")
                else:
                    print(f"还原失败: {message}")
                    self.show_message("错误", f"还原失败: {message}")
            
            except Exception as e:
                import traceback
                error_msg = traceback.format_exc()
                print(f"执行还原脚本时出错: {e}")
                print(error_msg)
                self.show_message("错误", f"执行还原脚本时出错:\n{str(e)}")
            
            finally:
                # 恢复标准输出
                sys.stdout = old_stdout
                
                # 恢复按钮状态
                def enable_buttons():
                    for widget in self.tab2.winfo_children():
                        if isinstance(widget, ttk.Frame):
                            for child in widget.winfo_children():
                                if isinstance(child, ttk.Button):
                                    child.configure(state="normal")
                    self.status_var.set("就绪")
                
                # 在主线程中恢复按钮状态
                self.root.after(0, enable_buttons)
        
        # 启动线程
        threading.Thread(target=run_restore, daemon=True).start()

def main():
    """主函数"""
    root = tk.Tk()
    
    # 应用主题
    global ttk_style
    ttk_style = ttk.Style()
    if has_sv_ttk:
        sv_ttk.set_theme("dark")
    
    # 创建应用
    app = ClashVergeApp(root)
    
    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    main()