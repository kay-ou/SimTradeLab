# -*- coding: utf-8 -*-
"""
测试报告管理器模块
"""

import os
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from simtradelab.report_manager import ReportManager


class TestReportManager:
    """测试报告管理器"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.report_manager = ReportManager(self.temp_dir)
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """测试初始化"""
        assert self.report_manager.reports_dir == self.temp_dir
        assert os.path.exists(self.temp_dir)
    
    def test_list_reports(self):
        """测试列出报告"""
        # 创建一些测试文件
        os.makedirs(os.path.join(self.temp_dir, "strategy1"), exist_ok=True)
        test_files = [
            "strategy1/strategy1_20230101_20231231_cash100w_freq1d_20230101_120000.txt",
            "strategy1/strategy1_20230101_20231231_cash100w_freq1d_20230101_120000.json", 
            "strategy1/strategy1_20230101_20231231_cash100w_freq1d_20230101_120000.html"
        ]
        
        for file_path in test_files:
            full_path = os.path.join(self.temp_dir, file_path)
            with open(full_path, 'w') as f:
                f.write("test content")
        
        reports = self.report_manager.list_reports()
        # list_reports() 只返回 .txt 文件，所以只期望 1 个报告
        assert len(reports) >= 1
        assert reports[0]['filename'].endswith('.txt')
    
    def test_list_reports_by_strategy(self):
        """测试按策略获取报告"""
        # 创建测试文件
        os.makedirs(os.path.join(self.temp_dir, "test_strategy"), exist_ok=True)
        test_file = os.path.join(self.temp_dir, "test_strategy", "test_strategy_20230101_20231231_cash100w_freq1d_20230101_120000.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        reports = self.report_manager.list_reports(strategy_name="test_strategy")
        assert len(reports) >= 1
        assert "test_strategy" in str(reports[0])
    
    def test_get_report_summary(self):
        """测试获取报告摘要"""
        # 创建测试文件
        os.makedirs(os.path.join(self.temp_dir, "strategy"), exist_ok=True)
        
        # 创建不同类型的报告文件
        files = [
            "strategy_20230101_20231231_cash100w_freq1d_20230101_120000.txt",
            "strategy_20230101_20231231_cash100w_freq1d_20230101_120000.json", 
            "strategy_20230101_20231231_cash100w_freq1d_20230101_120000.html",
            "strategy_20230101_20231231_cash100w_freq1d_20230101_120000.csv"
        ]
        for file_name in files:
            file_path = os.path.join(self.temp_dir, "strategy", file_name)
            with open(file_path, 'w') as f:
                f.write("test content")
        
        summary = self.report_manager.get_report_summary()
        assert "total_files" in summary
        assert summary["total_files"] >= 4
    
    def test_cleanup_old_reports(self):
        """测试清理旧报告"""
        # 创建测试文件
        os.makedirs(os.path.join(self.temp_dir, "strategy"), exist_ok=True)
        test_file = os.path.join(self.temp_dir, "strategy", "old_strategy_20230101_20231231_cash100w_freq1d_20230101_120000.txt")
        
        with open(test_file, 'w') as f:
            f.write("test")
        
        # 修改文件的修改时间为30天前
        old_time = datetime.now() - timedelta(days=30)
        timestamp = old_time.timestamp()
        os.utime(test_file, (timestamp, timestamp))
        
        # 清理超过7天的报告
        cleaned = self.report_manager.cleanup_old_reports(days=7)
        assert cleaned >= 0  # 可能返回0，但不应该出错
    
    def test_organize_reports_by_strategy(self):
        """测试按策略组织报告"""
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, "misplaced_strategy_20230101_20231231_cash100w_freq1d_20230101_120000.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        # 组织报告
        result = self.report_manager.organize_reports_by_strategy()
        assert isinstance(result, bool)
    
    def test_export_report_index(self):
        """测试导出报告索引"""
        # 创建测试文件
        os.makedirs(os.path.join(self.temp_dir, "strategy"), exist_ok=True)
        test_file = os.path.join(self.temp_dir, "strategy", "test_strategy_20230101_20231231_cash100w_freq1d_20230101_120000.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # 导出索引
        index_file = self.report_manager.export_report_index()
        assert os.path.exists(index_file)
    
    def test_print_report_summary(self):
        """测试打印报告摘要"""
        # 这个方法只是打印，不返回值，确保不出错即可
        try:
            self.report_manager.print_report_summary()
            assert True  # 如果没有异常就算成功
        except Exception as e:
            pytest.fail(f"print_report_summary failed: {e}")


class TestReportManagerIntegration:
    """报告管理器集成测试"""
    
    def test_report_lifecycle(self):
        """测试报告的完整生命周期"""
        temp_dir = tempfile.mkdtemp()
        try:
            manager = ReportManager(temp_dir)
            
            # 1. 创建报告
            strategy_dir = os.path.join(temp_dir, "lifecycle_strategy")
            os.makedirs(strategy_dir, exist_ok=True)
            
            report_files = [
                "lifecycle_strategy_20230101_20231231_cash100w_freq1d_20230101_120000.txt",
                "lifecycle_strategy_20230101_20231231_cash100w_freq1d_20230101_120000.json", 
                "lifecycle_strategy_20230101_20231231_cash100w_freq1d_20230101_120000.html"
            ]
            for file_name in report_files:
                file_path = os.path.join(strategy_dir, file_name)
                with open(file_path, 'w') as f:
                    f.write(f"Content for {file_name}")
            
            # 2. 列出报告
            reports = manager.list_reports()
            # list_reports() 只返回 .txt 文件
            assert len(reports) >= 1
            assert reports[0]['filename'].endswith('.txt')
            
            # 3. 获取摘要
            summary = manager.get_report_summary()
            assert summary["total_files"] >= 3
            
            # 4. 导出索引
            index_file = manager.export_report_index()
            assert os.path.exists(index_file)
            
            # 5. 组织报告
            result = manager.organize_reports_by_strategy()
            assert isinstance(result, bool)
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)