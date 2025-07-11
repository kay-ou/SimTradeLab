# -*- coding: utf-8 -*-
"""
插件注册表

提供插件清单的注册、查询、管理功能。
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict
from datetime import datetime

from .manifest import PluginManifest, ManifestValidator, PluginCategory


class PluginRegistry:
    """
    插件注册表
    
    负责插件清单的注册、查询、分类管理等功能。
    """
    
    def __init__(self):
        """初始化插件注册表"""
        self.logger = logging.getLogger(__name__)
        
        # 插件清单存储
        self._manifests: Dict[str, PluginManifest] = {}
        
        # 索引
        self._by_category: Dict[PluginCategory, Set[str]] = defaultdict(set)
        self._by_author: Dict[str, Set[str]] = defaultdict(set)
        self._by_tag: Dict[str, Set[str]] = defaultdict(set)
        self._providers: Dict[str, Set[str]] = defaultdict(set)  # service -> plugins
        
        # 路径映射
        self._plugin_paths: Dict[str, Path] = {}
        
        self.logger.info("插件注册表已初始化")
    
    def register_plugin(self, manifest: PluginManifest, plugin_path: Optional[Path] = None) -> bool:
        """
        注册插件
        
        Args:
            manifest: 插件清单
            plugin_path: 插件路径
            
        Returns:
            注册是否成功
        """
        try:
            # 验证清单
            errors = ManifestValidator.validate_manifest(manifest)
            if errors:
                self.logger.error(f"插件清单验证失败 {manifest.name}: {errors}")
                return False
            
            # 检查名称冲突
            if manifest.name in self._manifests:
                existing = self._manifests[manifest.name]
                self.logger.warning(
                    f"插件 {manifest.name} 已存在 (版本: {existing.version}), "
                    f"将被替换为新版本 {manifest.version}"
                )
                self._unregister_plugin(manifest.name)
            
            # 注册插件
            self._manifests[manifest.name] = manifest
            
            # 更新索引
            self._by_category[manifest.category].add(manifest.name)
            self._by_author[manifest.author].add(manifest.name)
            
            for tag in manifest.tags:
                self._by_tag[tag].add(manifest.name)
            
            for service in manifest.provides:
                self._providers[service].add(manifest.name)
            
            if plugin_path:
                self._plugin_paths[manifest.name] = plugin_path
            
            self.logger.info(f"插件 {manifest.name} v{manifest.version} 注册成功")
            return True
            
        except Exception as e:
            self.logger.error(f"注册插件失败 {manifest.name}: {e}")
            return False
    
    def register_from_directory(self, directory: Path, recursive: bool = True) -> int:
        """
        从目录注册插件
        
        Args:
            directory: 插件目录
            recursive: 是否递归扫描
            
        Returns:
            成功注册的插件数量
        """
        if not directory.exists() or not directory.is_dir():
            self.logger.error(f"插件目录不存在: {directory}")
            return 0
        
        registered_count = 0
        manifest_files = []
        
        # 查找清单文件
        if recursive:
            manifest_files.extend(directory.rglob("plugin_manifest.yaml"))
            manifest_files.extend(directory.rglob("plugin_manifest.yml"))
            manifest_files.extend(directory.rglob("plugin_manifest.json"))
        else:
            manifest_files.extend(directory.glob("*/plugin_manifest.yaml"))
            manifest_files.extend(directory.glob("*/plugin_manifest.yml"))
            manifest_files.extend(directory.glob("*/plugin_manifest.json"))
        
        self.logger.info(f"在 {directory} 中找到 {len(manifest_files)} 个插件清单文件")
        
        for manifest_file in manifest_files:
            try:
                manifest = ManifestValidator.load_from_file(manifest_file)
                plugin_path = manifest_file.parent
                
                if self.register_plugin(manifest, plugin_path):
                    registered_count += 1
                    
            except Exception as e:
                self.logger.error(f"加载插件清单失败 {manifest_file}: {e}")
        
        self.logger.info(f"从 {directory} 成功注册了 {registered_count} 个插件")
        return registered_count
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        注销插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            注销是否成功
        """
        if plugin_name not in self._manifests:
            self.logger.warning(f"尝试注销不存在的插件: {plugin_name}")
            return False
        
        try:
            self._unregister_plugin(plugin_name)
            self.logger.info(f"插件 {plugin_name} 注销成功")
            return True
            
        except Exception as e:
            self.logger.error(f"注销插件失败 {plugin_name}: {e}")
            return False
    
    def get_manifest(self, plugin_name: str) -> Optional[PluginManifest]:
        """获取插件清单"""
        return self._manifests.get(plugin_name)
    
    def has_plugin(self, plugin_name: str) -> bool:
        """检查插件是否存在"""
        return plugin_name in self._manifests
    
    def get_plugin_path(self, plugin_name: str) -> Optional[Path]:
        """获取插件路径"""
        return self._plugin_paths.get(plugin_name)
    
    def list_plugins(self, category: Optional[PluginCategory] = None) -> List[str]:
        """
        列出插件
        
        Args:
            category: 插件类别筛选
            
        Returns:
            插件名称列表
        """
        if category:
            return list(self._by_category.get(category, set()))
        return list(self._manifests.keys())
    
    def search_plugins(self, 
                      keyword: Optional[str] = None,
                      category: Optional[PluginCategory] = None,
                      author: Optional[str] = None,
                      tag: Optional[str] = None) -> List[PluginManifest]:
        """
        搜索插件
        
        Args:
            keyword: 关键词（名称、描述）
            category: 类别
            author: 作者
            tag: 标签
            
        Returns:
            匹配的插件清单列表
        """
        candidates = set(self._manifests.keys())
        
        # 按类别筛选
        if category:
            candidates &= self._by_category.get(category, set())
        
        # 按作者筛选
        if author:
            candidates &= self._by_author.get(author, set())
        
        # 按标签筛选
        if tag:
            candidates &= self._by_tag.get(tag, set())
        
        # 按关键词筛选
        if keyword:
            keyword_lower = keyword.lower()
            filtered = set()
            for plugin_name in candidates:
                manifest = self._manifests[plugin_name]
                if (keyword_lower in manifest.name.lower() or
                    keyword_lower in manifest.description.lower() or
                    any(keyword_lower in kw.lower() for kw in manifest.keywords)):
                    filtered.add(plugin_name)
            candidates = filtered
        
        return [self._manifests[name] for name in candidates]
    
    def get_plugins_by_service(self, service: str) -> List[str]:
        """获取提供特定服务的插件"""
        return list(self._providers.get(service, set()))
    
    def get_plugin_dependencies(self, plugin_name: str) -> Dict[str, str]:
        """获取插件的直接依赖"""
        manifest = self.get_manifest(plugin_name)
        return manifest.dependencies if manifest else {}
    
    def get_plugin_dependents(self, plugin_name: str) -> List[str]:
        """获取依赖于指定插件的其他插件"""
        dependents = []
        for name, manifest in self._manifests.items():
            if plugin_name in manifest.dependencies:
                dependents.append(name)
        return dependents
    
    def get_statistics(self) -> Dict[str, any]:
        """获取注册表统计信息"""
        stats = {
            "total_plugins": len(self._manifests),
            "by_category": {cat.value: len(plugins) for cat, plugins in self._by_category.items()},
            "by_author": {author: len(plugins) for author, plugins in self._by_author.items()},
            "top_tags": [],
            "services_provided": len(self._providers),
        }
        
        # 统计最常用的标签
        tag_counts = [(tag, len(plugins)) for tag, plugins in self._by_tag.items()]
        stats["top_tags"] = sorted(tag_counts, key=lambda x: x[1], reverse=True)[:10]
        
        return stats
    
    def validate_registry(self) -> Dict[str, List[str]]:
        """验证注册表中所有插件的完整性"""
        validation_report = {}
        
        for plugin_name, manifest in self._manifests.items():
            errors = ManifestValidator.validate_manifest(manifest)
            
            # 检查依赖是否存在
            for dep_name in manifest.dependencies.keys():
                if not self.has_plugin(dep_name):
                    errors.append(f"依赖插件不存在: {dep_name}")
            
            # 检查冲突插件是否真的存在
            for conflict_name in manifest.conflicts:
                if self.has_plugin(conflict_name):
                    errors.append(f"存在冲突插件: {conflict_name}")
            
            if errors:
                validation_report[plugin_name] = errors
        
        return validation_report
    
    def export_registry(self, export_path: Path, format: str = "yaml") -> bool:
        """
        导出注册表
        
        Args:
            export_path: 导出路径
            format: 导出格式 (yaml/json)
            
        Returns:
            导出是否成功
        """
        try:
            # 将插件清单转换为纯Python字典
            plugins_data = {}
            for name, manifest in self._manifests.items():
                plugins_data[name] = manifest.model_dump(mode='json')
            
            export_data = {
                "registry_version": "1.0",
                "exported_at": self.get_current_time(),
                "plugins": plugins_data
            }
            
            # 处理datetime对象和其他特殊类型
            def convert_objects_to_serializable(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, str):
                    # 如果已经是字符串（比如mock返回的），直接返回
                    return obj
                elif hasattr(obj, 'value'):
                    # 处理枚举类型
                    return obj.value
                elif isinstance(obj, dict):
                    return {k: convert_objects_to_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_objects_to_serializable(item) for item in obj]
                return obj
            
            export_data = convert_objects_to_serializable(export_data)
            
            if format.lower() == "yaml":
                import yaml
                with open(export_path, 'w', encoding='utf-8') as f:
                    yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True, indent=2)
            elif format.lower() == "json":
                import json
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            else:
                raise ValueError(f"不支持的导出格式: {format}")
            
            self.logger.info(f"注册表已导出到 {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出注册表失败: {e}")
            return False
    
    def clear(self) -> None:
        """清空注册表"""
        self._manifests.clear()
        self._by_category.clear()
        self._by_author.clear()
        self._by_tag.clear()
        self._providers.clear()
        self._plugin_paths.clear()
        
        self.logger.info("注册表已清空")
    
    def _unregister_plugin(self, plugin_name: str) -> None:
        """内部注销插件方法"""
        manifest = self._manifests[plugin_name]
        
        # 从索引中移除
        self._by_category[manifest.category].discard(plugin_name)
        self._by_author[manifest.author].discard(plugin_name)
        
        for tag in manifest.tags:
            self._by_tag[tag].discard(plugin_name)
        
        for service in manifest.provides:
            self._providers[service].discard(plugin_name)
        
        # 清理空集合
        if not self._by_category[manifest.category]:
            del self._by_category[manifest.category]
        if not self._by_author[manifest.author]:
            del self._by_author[manifest.author]
        
        # 移除主记录
        del self._manifests[plugin_name]
        self._plugin_paths.pop(plugin_name, None)
    
    @staticmethod
    def get_current_time():
        """获取当前时间（用于测试覆盖）"""
        from datetime import datetime
        return datetime.now()