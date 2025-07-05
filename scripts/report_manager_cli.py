#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告管理命令行工具

提供报告文件的管理、查看、清理等功能

使用方法:
    poetry run python report_manager_cli.py --help
    poetry run python report_manager_cli.py list
    poetry run python report_manager_cli.py summary
    poetry run python report_manager_cli.py cleanup --days 30
    poetry run python report_manager_cli.py organize
"""

import sys
import os
import argparse
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from src.ptradesim.report_manager import ReportManager


def cmd_list(args):
    """列出报告文件"""
    manager = ReportManager(args.reports_dir)
    reports = manager.list_reports(strategy_name=args.strategy, days=args.days)
    
    if not reports:
        print("📭 没有找到报告文件")
        return
    
    print(f"\n📋 找到 {len(reports)} 个报告文件:")
    print("=" * 80)
    print(f"{'策略名称':<25} {'日期范围':<20} {'大小':<10} {'修改时间':<20}")
    print("-" * 80)
    
    for report in reports:
        strategy_name = report['strategy_name']
        date_range = f"{report['start_date']}-{report['end_date']}" if report['start_date'] else "N/A"
        size = f"{report['size_mb']:.2f}MB"
        modified = report['modified'].strftime('%Y-%m-%d %H:%M')
        
        print(f"{strategy_name:<25} {date_range:<20} {size:<10} {modified:<20}")
    
    print("=" * 80)


def cmd_summary(args):
    """显示报告摘要"""
    manager = ReportManager(args.reports_dir)
    manager.print_report_summary()


def cmd_cleanup(args):
    """清理旧报告"""
    manager = ReportManager(args.reports_dir)
    
    print(f"🧹 开始清理报告文件...")
    print(f"   保留最近 {args.days} 天的报告")
    print(f"   每个策略至少保留 {args.keep} 个最新报告")
    
    if not args.force:
        confirm = input("\n确认执行清理操作? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ 操作已取消")
            return
    
    deleted_count = manager.cleanup_old_reports(days=args.days, keep_latest=args.keep)
    
    if deleted_count > 0:
        print(f"✅ 清理完成，删除了 {deleted_count} 个文件")
    else:
        print("✅ 没有需要清理的文件")


def cmd_organize(args):
    """组织报告文件"""
    manager = ReportManager(args.reports_dir)
    
    print("📁 开始组织报告文件...")
    
    if not args.force:
        confirm = input("确认将报告文件按策略分类到子目录? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ 操作已取消")
            return
    
    success = manager.organize_reports_by_strategy()
    
    if success:
        print("✅ 报告文件组织完成")
    else:
        print("❌ 报告文件组织失败")


def cmd_export(args):
    """导出报告索引"""
    manager = ReportManager(args.reports_dir)
    
    print("📤 导出报告索引...")
    
    index_file = manager.export_report_index(args.output)
    
    if index_file:
        print(f"✅ 报告索引已导出到: {index_file}")
    else:
        print("❌ 导出报告索引失败")


def cmd_open(args):
    """打开报告文件"""
    manager = ReportManager(args.reports_dir)
    reports = manager.list_reports(strategy_name=args.strategy)
    
    if not reports:
        print("📭 没有找到报告文件")
        return
    
    # 找到最新的报告
    latest_report = reports[0]  # 已按时间排序
    
    # 根据类型选择文件
    base_name = os.path.splitext(latest_report['full_path'])[0]
    
    if args.type == 'html':
        file_path = f"{base_name}.html"
    elif args.type == 'json':
        file_path = f"{base_name}.json"
    elif args.type == 'csv':
        file_path = f"{base_name}.csv"
    elif args.type == 'summary':
        file_path = f"{base_name}.summary.txt"
    else:  # txt
        file_path = f"{base_name}.txt"
    
    if os.path.exists(file_path):
        print(f"📖 打开报告文件: {os.path.basename(file_path)}")
        
        if args.type == 'html':
            # 在浏览器中打开HTML文件
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(file_path)}")
        else:
            # 在终端中显示文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 限制显示长度
            if len(content) > 5000 and not args.full:
                content = content[:5000] + "\n\n... (内容已截断，使用 --full 查看完整内容)"
            
            print(content)
    else:
        print(f"❌ 文件不存在: {os.path.basename(file_path)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ptradeSim 报告管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s list                          # 列出所有报告
  %(prog)s list --strategy buy_and_hold  # 列出特定策略的报告
  %(prog)s list --days 7                 # 列出最近7天的报告
  %(prog)s summary                       # 显示报告统计摘要
  %(prog)s cleanup --days 30 --keep 5    # 清理30天前的报告，每策略保留5个
  %(prog)s organize                      # 按策略组织报告到子目录
  %(prog)s export --output index.json    # 导出报告索引
  %(prog)s open --strategy buy_and_hold --type html  # 打开HTML报告
        """
    )
    
    parser.add_argument('--reports-dir', default='reports',
                       help='报告目录路径 (默认: reports)')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出报告文件')
    list_parser.add_argument('--strategy', help='过滤策略名称')
    list_parser.add_argument('--days', type=int, help='最近天数过滤')
    list_parser.set_defaults(func=cmd_list)
    
    # summary 命令
    summary_parser = subparsers.add_parser('summary', help='显示报告摘要')
    summary_parser.set_defaults(func=cmd_summary)
    
    # cleanup 命令
    cleanup_parser = subparsers.add_parser('cleanup', help='清理旧报告')
    cleanup_parser.add_argument('--days', type=int, default=30,
                               help='保留最近多少天的报告 (默认: 30)')
    cleanup_parser.add_argument('--keep', type=int, default=5,
                               help='每个策略至少保留多少个最新报告 (默认: 5)')
    cleanup_parser.add_argument('--force', action='store_true',
                               help='强制执行，不询问确认')
    cleanup_parser.set_defaults(func=cmd_cleanup)
    
    # organize 命令
    organize_parser = subparsers.add_parser('organize', help='组织报告文件')
    organize_parser.add_argument('--force', action='store_true',
                                help='强制执行，不询问确认')
    organize_parser.set_defaults(func=cmd_organize)
    
    # export 命令
    export_parser = subparsers.add_parser('export', help='导出报告索引')
    export_parser.add_argument('--output', default='report_index.json',
                              help='输出文件名 (默认: report_index.json)')
    export_parser.set_defaults(func=cmd_export)
    
    # open 命令
    open_parser = subparsers.add_parser('open', help='打开报告文件')
    open_parser.add_argument('--strategy', required=True, help='策略名称')
    open_parser.add_argument('--type', choices=['txt', 'html', 'json', 'csv', 'summary'],
                            default='html', help='报告类型 (默认: html)')
    open_parser.add_argument('--full', action='store_true',
                            help='显示完整内容（仅对文本文件有效）')
    open_parser.set_defaults(func=cmd_open)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n❌ 操作被用户中断")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
