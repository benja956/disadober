#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Clash Verge Adobe屏蔽模块 - 提供Adobe屏蔽相关功能
"""

import urllib.request
import urllib.error

# 导入核心模块
from clash_verge_core import (
    find_global_script,
    backup_file
)

# 内置的Adobe域名列表
BUILTIN_ADOBE_DOMAINS = [
    "activate.adobe.com",
    "practivate.adobe.com",
    "ereg.adobe.com",
    "wip.adobe.com",
    "activate.wip.adobe.com",
    "3dns.adobe.com",
    "3dns-1.adobe.com",
    "3dns-2.adobe.com",
    "3dns-3.adobe.com",
    "3dns-4.adobe.com",
    "adobe-dns.adobe.com",
    "adobe-dns-1.adobe.com",
    "adobe-dns-2.adobe.com",
    "adobe-dns-3.adobe.com",
    "adobe-dns-4.adobe.com",
    "lm.licenses.adobe.com",
    "lmlicenses.wip4.adobe.com", 
    "na1r.services.adobe.com",
    "hlrcv.stage.adobe.com",
    "adobeereg.com",
    "www.adobeereg.com"
]

# 内置的GitHub代理列表
GITHUB_PROXIES = [
    "https://raw.githubusercontent.com",  # 原始地址
    "https://ghfast.top/raw.githubusercontent.com",
    "https://gh-proxy.com/https://raw.githubusercontent.com",
    "https://mirror.ghproxy.com/https://raw.githubusercontent.com"
]

def try_download_with_proxies():
    """尝试使用内置代理下载"""
    tried_urls = []
    for proxy in GITHUB_PROXIES:
        url = f"{proxy}/ignaciocastro/a-dove-is-dumb/main/127.txt"
        tried_urls.append(url)
        print(f"尝试使用代理URL: {url}")
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    content = response.read().decode('utf-8')
                    domains = extract_adobe_domains(content)
                    if domains:
                        return domains, tried_urls
        except Exception as e:
            print(f"通过代理 {proxy} 下载失败: {e}")
    
    print("所有内置代理均下载失败")
    return None, tried_urls

def try_download_with_custom_proxy(proxy):
    """尝试使用用户自定义代理下载"""
    if not proxy.endswith('/'):
        proxy += '/'
    
    url = f"{proxy}https://raw.githubusercontent.com/ignaciocastro/a-dove-is-dumb/main/127.txt"
    
    try:
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                content = response.read().decode('utf-8')
                domains = extract_adobe_domains(content)
                if domains:
                    return domains
    except Exception:
        pass
    
    return None

def extract_adobe_domains(content):
    """从下载内容中提取Adobe相关域名"""
    domains = []
    for line in content.splitlines():
        line = line.strip()
        if line and line.startswith("127.0.0.1 "):
            domain = line.split(" ")[1]
            if "adobe" in domain.lower():
                domains.append(domain)
    return domains

def download_adobe_block_list():
    """下载Adobe屏蔽名单"""
    # 依次尝试各个代理
    domains, tried_urls = try_download_with_proxies()
    if domains:
        return domains
    
    # 如果内置代理都失败，打印尝试过的URL
    print("\n已尝试过以下代理URL:")
    for url in tried_urls:
        print(f"- {url}")
    print()
    
    # 如果内置代理都失败，返回None
    return None

def create_adobe_block_script(domains):
    """创建Adobe屏蔽脚本"""
    # 安全的脚本模板
    script_template = """// Adobe屏蔽规则 - 由 clash_verge_adobe_block.py 生成
function main(config) {
  // 确保配置对象存在
  if (!config) {
    config = {};
  }
  
  // 确保rules数组存在
  if (!config.rules) {
    config.rules = [];
  }
  
  // Adobe屏蔽规则 - 允许photo-api
  const adobe_rules = [
    "DOMAIN-SUFFIX,photo-api.adobe.io,DIRECT"
  ];
  
  // Adobe屏蔽规则 - 固定规则
  adobe_rules.push("DOMAIN-SUFFIX,adobe.io,REJECT");
  adobe_rules.push("DOMAIN-SUFFIX,adobestats.io,REJECT");
  
  // Adobe屏蔽规则 - 从屏蔽列表生成
%s
  
  // 将规则添加到配置的开头
  config.rules = adobe_rules.concat(config.rules);
  
  return config;
}
"""
    
    # 生成域名规则代码
    domain_rules = []
    for domain in domains:
        if "adobe" in domain.lower() and "adobe.io" not in domain:
            domain_rules.append(f'  adobe_rules.push("DOMAIN-SUFFIX,{domain},REJECT");')
    
    # 插入域名规则
    domain_rules_str = "\n".join(domain_rules)
    return script_template % domain_rules_str

def modify_clash_verge_script(domains=None):
    """修改Clash Verge脚本添加Adobe屏蔽规则
    
    参数:
        domains: 可选的域名列表，如果为None则会尝试下载
        
    返回:
        (成功状态, 信息消息)
    """
    try:
        # 查找脚本文件
        script_path = find_global_script()
        if not script_path:
            return False, "无法找到全局脚本文件"
        
        # 如果没有提供域名列表，尝试下载
        if domains is None:
            domains = download_adobe_block_list()
            if not domains:
                domains = BUILTIN_ADOBE_DOMAINS
        
        # 创建安全的脚本
        new_script = create_adobe_block_script(domains)
        
        # 备份原文件
        backup_result = backup_file(script_path)
        if not backup_result:
            return False, "备份文件失败"
        
        # 写入新脚本
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(new_script)
        
        return True, f"已成功修改脚本: {script_path.name}"
        
    except Exception as e:
        return False, f"应用Adobe屏蔽规则时出错: {e}"

if __name__ == "__main__":
    try:
        print("Clash Verge Adobe屏蔽工具")
        print("-" * 50)
        success, message = modify_clash_verge_script()
        if success:
            print(f"{message}\nAdobe屏蔽规则已应用。请重启Clash Verge以生效。")
        else:
            print(f"错误: {message}")
    except Exception as e:
        print(f"发生错误: {e}") 