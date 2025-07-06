#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SimTradeLab Web 界面启动脚本
增强版：支持更多配置选项和更好的错误处理
"""
import os
import sys
import warnings
import webbrowser
import time
import argparse
import subprocess
from pathlib import Path

# 抑制pkg_resources废弃警告
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
warnings.filterwarnings("ignore", category=UserWarning, module="py_mini_racer")

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """检查必要的依赖是否已安装"""
    missing_deps = []
    
    try:
        import uvicorn
    except ImportError:
        missing_deps.append("uvicorn")
    
    try:
        import fastapi
    except ImportError:
        missing_deps.append("fastapi")
    
    if missing_deps:
        print(f"❌ 缺少依赖: {', '.join(missing_deps)}")
        print("请运行以下命令安装依赖:")
        print("poetry install --with data")
        print("或者：pip install uvicorn fastapi python-multipart")
        return False
    
    print("✅ FastAPI 依赖检查通过")
    return True

def setup_directories():
    """确保必要目录存在"""
    directories = [
        project_root / "web" / "uploads",
        project_root / "strategies", 
        project_root / "data",
        project_root / "reports",
        project_root / "cache",
        project_root / "logs"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"📁 确保目录存在: {directory}")

def start_server(host="0.0.0.0", port=8000, reload=False, workers=1):
    """启动Web服务器"""
    print(f"\n🌐 启动Web服务器...")
    print(f"📍 内部地址: http://{host}:{port}")
    print(f"📍 外部访问: http://localhost:{port}")
    print(f"🔧 API文档: http://localhost:{port}/docs")
    print(f"⏹️  按 Ctrl+C 停止服务器\n")
    
    # 只在非Docker环境且未禁用浏览器时才自动打开
    should_open_browser = (
        not os.environ.get('SIMTRADELAB_NO_BROWSER') and 
        not os.path.exists('/.dockerenv') and  # Docker环境检测
        host not in ['0.0.0.0']
    )
    
    if should_open_browser:
        # 延迟后自动打开浏览器
        def open_browser():
            time.sleep(2)
            try:
                browser_url = f'http://localhost:{port}' if host == '0.0.0.0' else f'http://{host}:{port}'
                webbrowser.open(browser_url)
            except Exception as e:
                print(f"⚠️  无法自动打开浏览器: {e}")
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
    
    # 启动服务器
    os.chdir(project_root)
    
    try:
        import uvicorn
        from web.backend.app import app
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,
            log_level="info"
        )
    except ImportError:
        # 备用方案：直接运行Python文件
        app_path = project_root / "web" / "backend" / "app.py"
        subprocess.run([sys.executable, str(app_path)], cwd=project_root)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="SimTradeLab Web 界面启动器")
    parser.add_argument("--host", default="0.0.0.0", help="服务器地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口 (默认: 8000)")
    parser.add_argument("--reload", action="store_true", help="启用热重载 (开发模式)")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数 (生产模式)")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    
    args = parser.parse_args()
    
    print("🚀 启动 SimTradeLab Web 界面...")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    # 确保必要目录存在
    setup_directories()
    
    # 如果指定不打开浏览器，则设置环境变量
    if args.no_browser:
        os.environ['SIMTRADELAB_NO_BROWSER'] = '1'
    
    # 启动服务器
    try:
        start_server(
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers
        )
    except KeyboardInterrupt:
        print("\n\n🛑 用户中断，正在关闭服务器...")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())