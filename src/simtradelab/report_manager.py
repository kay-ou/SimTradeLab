# -*- coding: utf-8 -*-
"""
报告管理器模块

提供报告文件的管理、分类、搜索和清理功能
"""

import os
import glob
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

from .logger import log


class ReportManager:
    """报告管理器"""
    
    def __init__(self, reports_dir: str = "reports"):
        """
        初始化报告管理器
        
        Args:
            reports_dir: 报告目录
        """
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)
    
    def list_reports(self, strategy_name: Optional[str] = None, 
                    days: Optional[int] = None) -> List[Dict]:
        """
        列出报告文件
        
        Args:
            strategy_name: 策略名称过滤
            days: 最近天数过滤
            
        Returns:
            List[Dict]: 报告文件信息列表
        """
        reports = []
        
        # 获取所有报告文件
        pattern = os.path.join(self.reports_dir, "**", "*.txt")
        if strategy_name:
            pattern = os.path.join(self.reports_dir, strategy_name, "*.txt")
        
        for file_path in glob.glob(pattern, recursive=True):
            if 'summary' in file_path:  # 跳过摘要文件
                continue
                
            file_info = self._parse_report_filename(file_path)
            if file_info:
                # 日期过滤
                if days:
                    file_date = datetime.strptime(file_info['timestamp'], '%Y%m%d_%H%M%S')
                    if (datetime.now() - file_date).days > days:
                        continue
                
                # 获取文件大小
                file_info['size'] = os.path.getsize(file_path)
                file_info['size_mb'] = file_info['size'] / (1024 * 1024)
                
                # 获取修改时间
                file_info['modified'] = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                reports.append(file_info)
        
        # 按时间排序
        reports.sort(key=lambda x: x['modified'], reverse=True)
        return reports
    
    def get_report_summary(self) -> Dict:
        """
        获取报告统计摘要
        
        Returns:
            Dict: 报告统计信息
        """
        all_files = glob.glob(os.path.join(self.reports_dir, "**", "*"), recursive=True)
        all_files = [f for f in all_files if os.path.isfile(f)]  # 只包含文件，不包含目录
        
        summary = {
            'total_files': len(all_files),
            'total_size_mb': sum(os.path.getsize(f) for f in all_files) / (1024 * 1024),
            'file_types': {},
            'strategies': set(),
            'date_range': {'earliest': None, 'latest': None}
        }
        
        for file_path in all_files:
            # 文件类型统计
            ext = os.path.splitext(file_path)[1]
            summary['file_types'][ext] = summary['file_types'].get(ext, 0) + 1
            
            # 策略统计
            file_info = self._parse_report_filename(file_path)
            if file_info:
                summary['strategies'].add(file_info['strategy_name'])
                
                # 日期范围
                file_date = datetime.strptime(file_info['timestamp'], '%Y%m%d_%H%M%S')
                if not summary['date_range']['earliest'] or file_date < summary['date_range']['earliest']:
                    summary['date_range']['earliest'] = file_date
                if not summary['date_range']['latest'] or file_date > summary['date_range']['latest']:
                    summary['date_range']['latest'] = file_date
        
        summary['strategies'] = list(summary['strategies'])
        return summary
    
    def cleanup_old_reports(self, days: int = 30, keep_latest: int = 5) -> int:
        """
        清理旧报告文件
        
        Args:
            days: 保留最近多少天的报告
            keep_latest: 每个策略至少保留多少个最新报告
            
        Returns:
            int: 删除的文件数量
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        # 按策略分组
        strategy_reports = {}
        for file_path in glob.glob(os.path.join(self.reports_dir, "*")):
            file_info = self._parse_report_filename(file_path)
            if file_info:
                strategy_name = file_info['strategy_name']
                if strategy_name not in strategy_reports:
                    strategy_reports[strategy_name] = []
                
                file_info['full_path'] = file_path
                file_info['file_date'] = datetime.strptime(file_info['timestamp'], '%Y%m%d_%H%M%S')
                strategy_reports[strategy_name].append(file_info)
        
        # 对每个策略进行清理
        for strategy_name, reports in strategy_reports.items():
            # 按时间排序
            reports.sort(key=lambda x: x['file_date'], reverse=True)
            
            # 保留最新的几个报告
            to_keep = reports[:keep_latest]
            to_check = reports[keep_latest:]
            
            # 检查剩余报告是否超过时间限制
            for report in to_check:
                if report['file_date'] < cutoff_date:
                    try:
                        # 删除所有相关文件（txt, json, csv等）
                        base_name = os.path.splitext(report['full_path'])[0]
                        related_files = glob.glob(f"{base_name}.*")
                        
                        for related_file in related_files:
                            os.remove(related_file)
                            deleted_count += 1
                            log.info(f"删除旧报告文件: {os.path.basename(related_file)}")
                            
                    except Exception as e:
                        log.warning(f"删除文件失败 {report['full_path']}: {e}")
        
        return deleted_count
    
    def organize_reports_by_strategy(self) -> bool:
        """
        按策略名称组织报告文件到子目录
        
        Returns:
            bool: 是否成功
        """
        try:
            reports = self.list_reports()
            
            for report in reports:
                strategy_name = report['strategy_name']
                strategy_dir = os.path.join(self.reports_dir, strategy_name)
                os.makedirs(strategy_dir, exist_ok=True)
                
                # 移动所有相关文件
                base_name = os.path.splitext(report['full_path'])[0]
                related_files = glob.glob(f"{base_name}.*")
                
                for file_path in related_files:
                    filename = os.path.basename(file_path)
                    new_path = os.path.join(strategy_dir, filename)
                    
                    if not os.path.exists(new_path):
                        shutil.move(file_path, new_path)
                        log.info(f"移动文件: {filename} -> {strategy_name}/")
            
            return True
            
        except Exception as e:
            log.error(f"组织报告文件失败: {e}")
            return False
    
    def export_report_index(self, output_file: str = "report_index.json") -> str:
        """
        导出报告索引文件
        
        Args:
            output_file: 输出文件名
            
        Returns:
            str: 索引文件路径
        """
        reports = self.list_reports()
        summary = self.get_report_summary()
        
        index_data = {
            'generated_at': datetime.now().isoformat(),
            'summary': summary,
            'reports': reports
        }
        
        # 处理不可序列化的对象
        for report in index_data['reports']:
            if 'modified' in report:
                report['modified'] = report['modified'].isoformat()
        
        if 'date_range' in index_data['summary']:
            date_range = index_data['summary']['date_range']
            if date_range['earliest']:
                date_range['earliest'] = date_range['earliest'].isoformat()
            if date_range['latest']:
                date_range['latest'] = date_range['latest'].isoformat()
        
        output_path = os.path.join(self.reports_dir, output_file)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            
            log.info(f"报告索引已导出到: {output_path}")
            return output_path
            
        except Exception as e:
            log.error(f"导出报告索引失败: {e}")
            return None
    
    def _parse_report_filename(self, file_path: str) -> Optional[Dict]:
        """
        解析报告文件名
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[Dict]: 解析结果
        """
        filename = os.path.basename(file_path)
        
        # 移除扩展名
        name_without_ext = os.path.splitext(filename)[0]
        
        # 解析文件名格式: strategy_name_startdate_enddate_params_timestamp
        parts = name_without_ext.split('_')
        
        if len(parts) < 4:
            return None
        
        try:
            # 查找时间戳（最后两部分：YYYYMMDD_HHMMSS）
            timestamp_parts = parts[-2:]
            timestamp = '_'.join(timestamp_parts)
            
            # 验证时间戳格式
            datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
            
            # 提取其他部分
            remaining_parts = parts[:-2]
            
            # 策略名称（第一部分）
            strategy_name = remaining_parts[0]
            
            # 日期范围（如果存在）
            start_date = None
            end_date = None
            if len(remaining_parts) >= 3:
                try:
                    start_date = remaining_parts[1]
                    end_date = remaining_parts[2]
                    # 验证日期格式
                    datetime.strptime(start_date, '%Y%m%d')
                    datetime.strptime(end_date, '%Y%m%d')
                except:
                    start_date = None
                    end_date = None
            
            # 参数部分
            params = []
            if start_date and end_date:
                params = remaining_parts[3:]
            else:
                params = remaining_parts[1:]
            
            return {
                'full_path': file_path,
                'filename': filename,
                'strategy_name': strategy_name,
                'start_date': start_date,
                'end_date': end_date,
                'params': params,
                'timestamp': timestamp
            }
            
        except Exception:
            return None
    
    def print_report_summary(self):
        """打印报告摘要信息"""
        summary = self.get_report_summary()
        
        print("\n📊 报告文件统计")
        print("=" * 50)
        print(f"📁 报告目录: {self.reports_dir}")
        print(f"📄 总文件数: {summary['total_files']}")
        print(f"💾 总大小: {summary['total_size_mb']:.2f} MB")
        
        if summary['strategies']:
            print(f"🎯 策略数量: {len(summary['strategies'])}")
            print(f"📋 策略列表: {', '.join(summary['strategies'])}")
        
        if summary['file_types']:
            print("\n📊 文件类型分布:")
            for ext, count in summary['file_types'].items():
                ext_name = ext or '无扩展名'
                print(f"   {ext_name}: {count} 个")
        
        if summary['date_range']['earliest'] and summary['date_range']['latest']:
            print(f"\n📅 时间范围:")
            print(f"   最早: {summary['date_range']['earliest'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   最新: {summary['date_range']['latest'].strftime('%Y-%m-%d %H:%M')}")
        
        print("=" * 50)
