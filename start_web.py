#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SimTradeLab Web 界面启动脚本
"""
import os
import sys
import warnings
import webbrowser
import time
from pathlib import Path

# 抑制pkg_resources废弃警告
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
warnings.filterwarnings("ignore", category=UserWarning, module="py_mini_racer")

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """启动Web界面"""
    print("🚀 启动 SimTradeLab Web 界面...")
    
    # 检查依赖
    try:
        import uvicorn
        import fastapi
        print("✅ FastAPI 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: poetry install --with web")
        return
    
    # 确保必要目录存在
    directories = [
        project_root / "web" / "uploads",
        project_root / "strategies", 
        project_root / "data",
        project_root / "reports"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"📁 确保目录存在: {directory}")
    
    # 启动服务器
    app_path = project_root / "web" / "backend" / "app.py"
    
    print("\n🌐 启动Web服务器...")
    print("📍 访问地址: http://localhost:8000")
    print("🔧 API文档: http://localhost:8000/docs")
    print("⏹️  按 Ctrl+C 停止服务器\n")
    
    # 延迟后自动打开浏览器
    def open_browser():
        time.sleep(2)
        webbrowser.open('http://localhost:8000')
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # 启动服务器
    os.chdir(project_root)
    os.system(f"python {app_path}")

if __name__ == "__main__":
    main()