# -*- coding: utf-8 -*-
"""
依赖解析引擎

提供插件依赖分析、冲突检测、加载顺序计算等功能。
"""

import logging
from typing import Dict, List, Set, Optional
from packaging import version, specifiers
import networkx as nx

from .manifest import PluginManifest


class DependencyError(Exception):
    """依赖管理基础异常"""
    pass


class DependencyConflictError(DependencyError):
    """依赖冲突异常"""
    pass


class CircularDependencyError(DependencyError):
    """循环依赖异常"""
    pass


class MissingDependencyError(DependencyError):
    """缺失依赖异常"""
    pass


class VersionConflictError(DependencyError):
    """版本冲突异常"""
    pass


class DependencyResolver:
    """
    插件依赖解析引擎
    
    负责分析插件依赖关系、检测冲突、计算加载顺序等。
    """
    
    def __init__(self, plugin_registry=None):
        """
        初始化依赖解析器
        
        Args:
            plugin_registry: 插件注册表
        """
        self.registry = plugin_registry
        self.dependency_graph = nx.DiGraph()
        self.logger = logging.getLogger(__name__)
        
        # 缓存
        self._resolution_cache: Dict[str, List[str]] = {}
        self._conflict_cache: Dict[str, bool] = {}
    
    def resolve_dependencies(self, target_plugins: List[str]) -> List[str]:
        """
        解析插件依赖，返回正确的加载顺序
        
        Args:
            target_plugins: 目标插件列表
            
        Returns:
            按依赖顺序排列的插件列表
            
        Raises:
            DependencyConflictError: 存在依赖冲突
            CircularDependencyError: 存在循环依赖
            MissingDependencyError: 缺少必需的依赖
            VersionConflictError: 版本冲突
        """
        # 生成缓存键
        cache_key = "|".join(sorted(target_plugins))
        if cache_key in self._resolution_cache:
            self.logger.debug(f"使用缓存的依赖解析结果: {target_plugins}")
            return self._resolution_cache[cache_key].copy()
        
        self.logger.info(f"开始解析插件依赖: {target_plugins}")
        
        try:
            # 1. 收集所有需要的插件及其依赖
            all_plugins = self._collect_all_dependencies(target_plugins)
            self.logger.debug(f"收集到的所有插件: {all_plugins}")
            
            # 2. 检查插件存在性
            self._validate_plugin_existence(all_plugins)
            
            # 3. 检查版本兼容性
            self._validate_version_compatibility(all_plugins)
            
            # 4. 检查冲突
            self._check_conflicts(all_plugins)
            
            # 5. 构建依赖图
            self._build_dependency_graph(all_plugins)
            
            # 6. 检查循环依赖
            if not nx.is_directed_acyclic_graph(self.dependency_graph):
                cycles = list(nx.simple_cycles(self.dependency_graph))
                raise CircularDependencyError(f"检测到循环依赖: {cycles}")
            
            # 7. 拓扑排序得到加载顺序
            load_order = list(nx.topological_sort(self.dependency_graph))
            
            # 缓存结果
            self._resolution_cache[cache_key] = load_order.copy()
            
            self.logger.info(f"依赖解析完成，加载顺序: {load_order}")
            return load_order
            
        except Exception as e:
            self.logger.error(f"依赖解析失败: {e}")
            raise
    
    def check_compatibility(self, plugin_manifests: List[PluginManifest]) -> Dict[str, List[str]]:
        """
        检查一组插件的兼容性
        
        Args:
            plugin_manifests: 插件清单列表
            
        Returns:
            兼容性报告 {plugin_name: [error_messages]}
        """
        compatibility_report = {}
        
        for manifest in plugin_manifests:
            errors = []
            
            # 检查与其他插件的冲突
            for other_manifest in plugin_manifests:
                if manifest.name == other_manifest.name:
                    continue
                
                if not manifest.is_compatible_with(other_manifest):
                    errors.append(f"与插件 {other_manifest.name} 存在冲突")
            
            # 检查依赖是否满足
            for dep_name, version_spec in manifest.dependencies.items():
                dep_manifest = next(
                    (m for m in plugin_manifests if m.name == dep_name), None
                )
                if not dep_manifest:
                    errors.append(f"缺少依赖: {dep_name}")
                else:
                    try:
                        dep_version = version.parse(dep_manifest.version)
                        spec = specifiers.SpecifierSet(version_spec)
                        if dep_version not in spec:
                            errors.append(
                                f"依赖版本不匹配: 需要 {dep_name} {version_spec}, "
                                f"但找到 {dep_manifest.version}"
                            )
                    except Exception as e:
                        errors.append(f"依赖版本验证失败: {dep_name} - {e}")
            
            compatibility_report[manifest.name] = errors
        
        return compatibility_report
    
    def get_dependency_tree(self, plugin_name: str, max_depth: int = 10) -> Dict:
        """
        获取插件的依赖树
        
        Args:
            plugin_name: 插件名称
            max_depth: 最大深度
            
        Returns:
            依赖树字典
        """
        def build_tree(name: str, depth: int = 0) -> Dict:
            if depth >= max_depth:
                return {"name": name, "children": [], "truncated": True}
            
            if not self.registry:
                return {"name": name, "children": [], "error": "No registry"}
            
            manifest = self.registry.get_manifest(name)
            if not manifest:
                return {"name": name, "children": [], "error": "Manifest not found"}
            
            children = []
            for dep_name in manifest.dependencies.keys():
                children.append(build_tree(dep_name, depth + 1))
            
            return {"name": name, "children": children, "version": manifest.version}
        
        return build_tree(plugin_name)
    
    def find_update_path(self, current_plugins: List[str], target_plugins: List[str]) -> Dict[str, str]:
        """
        找到从当前插件配置到目标配置的更新路径
        
        Args:
            current_plugins: 当前插件列表
            target_plugins: 目标插件列表
            
        Returns:
            更新计划 {"add": [...], "remove": [...], "update": [...]}
        """
        current_set = set(current_plugins)
        target_set = set(target_plugins)
        
        to_add = target_set - current_set
        to_remove = current_set - target_set
        common = current_set & target_set
        
        update_plan = {
            "add": list(to_add),
            "remove": list(to_remove),
            "keep": list(common),
            "sequence": []
        }
        
        # 计算安全的更新序列
        if to_remove:
            # 先卸载不需要的插件（按依赖关系逆序）
            try:
                remove_order = self.resolve_dependencies(list(to_remove))
                update_plan["sequence"].extend([("remove", p) for p in reversed(remove_order)])
            except Exception:
                # 如果无法解析，按原序列卸载
                update_plan["sequence"].extend([("remove", p) for p in to_remove])
        
        if to_add:
            # 再加载新插件（按依赖关系正序）
            try:
                add_order = self.resolve_dependencies(list(to_add))
                update_plan["sequence"].extend([("add", p) for p in add_order])
            except Exception:
                # 如果无法解析，按原序列加载
                update_plan["sequence"].extend([("add", p) for p in to_add])
        
        return update_plan
    
    def _collect_all_dependencies(self, plugins: List[str], collected: Optional[Set[str]] = None) -> Set[str]:
        """递归收集所有依赖的插件"""
        if collected is None:
            collected = set()
        
        for plugin_name in plugins:
            if plugin_name in collected:
                continue
                
            collected.add(plugin_name)
            
            if self.registry:
                manifest = self.registry.get_manifest(plugin_name)
                if manifest and manifest.dependencies:
                    deps = list(manifest.dependencies.keys())
                    self._collect_all_dependencies(deps, collected)
        
        return collected
    
    def _validate_plugin_existence(self, plugins: Set[str]) -> None:
        """验证插件是否存在"""
        if not self.registry:
            return  # 如果没有注册表，跳过验证
        
        for plugin_name in plugins:
            if not self.registry.has_plugin(plugin_name):
                raise MissingDependencyError(f"插件不存在: {plugin_name}")
    
    def _validate_version_compatibility(self, plugins: Set[str]) -> None:
        """验证版本兼容性"""
        if not self.registry:
            return  # 如果没有注册表，跳过验证
        
        for plugin_name in plugins:
            manifest = self.registry.get_manifest(plugin_name)
            if not manifest:
                raise MissingDependencyError(f"插件清单未找到: {plugin_name}")
            
            for dep_name, version_spec in manifest.dependencies.items():
                if dep_name not in plugins:
                    raise MissingDependencyError(f"缺少依赖: {dep_name}")
                
                dep_manifest = self.registry.get_manifest(dep_name)
                if not dep_manifest:
                    raise MissingDependencyError(f"依赖插件清单未找到: {dep_name}")
                
                try:
                    dep_version = version.parse(dep_manifest.version)
                    spec = specifiers.SpecifierSet(version_spec)
                    
                    if dep_version not in spec:
                        raise VersionConflictError(
                            f"版本冲突: {plugin_name} 需要 {dep_name} {version_spec}, "
                            f"但找到 {dep_manifest.version}"
                        )
                except Exception as e:
                    raise VersionConflictError(f"版本验证失败 {plugin_name}->{dep_name}: {e}")
    
    def _check_conflicts(self, plugins: Set[str]) -> None:
        """检查插件冲突"""
        if not self.registry:
            return  # 如果没有注册表，跳过验证
        
        # 构建插件清单映射
        manifests = {}
        for plugin_name in plugins:
            manifest = self.registry.get_manifest(plugin_name)
            if manifest:
                manifests[plugin_name] = manifest
        
        # 检查显式冲突
        for plugin_name, manifest in manifests.items():
            for conflict_name in manifest.conflicts:
                if conflict_name in plugins:
                    raise DependencyConflictError(
                        f"插件冲突: {plugin_name} 与 {conflict_name} 不兼容"
                    )
        
        # 检查服务提供冲突
        provides_map = {}
        for plugin_name, manifest in manifests.items():
            for service in manifest.provides:
                if service in provides_map:
                    raise DependencyConflictError(
                        f"服务冲突: {plugin_name} 和 {provides_map[service]} "
                        f"都提供服务 '{service}'"
                    )
                provides_map[service] = plugin_name
    
    def _build_dependency_graph(self, plugins: Set[str]) -> None:
        """构建依赖图"""
        self.dependency_graph.clear()
        
        # 添加所有插件作为节点
        for plugin_name in plugins:
            self.dependency_graph.add_node(plugin_name)
        
        if not self.registry:
            return  # 如果没有注册表，只添加节点
        
        # 添加依赖关系作为边
        for plugin_name in plugins:
            manifest = self.registry.get_manifest(plugin_name)
            if manifest:
                for dep_name in manifest.dependencies.keys():
                    if dep_name in plugins:
                        # 添加从依赖到插件的边（依赖必须先加载）
                        self.dependency_graph.add_edge(dep_name, plugin_name)
    
    def clear_cache(self) -> None:
        """清除缓存"""
        self._resolution_cache.clear()
        self._conflict_cache.clear()
        self.logger.debug("依赖解析缓存已清除")
    
    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            "cached_resolutions": len(self._resolution_cache),
            "graph_nodes": self.dependency_graph.number_of_nodes(),
            "graph_edges": self.dependency_graph.number_of_edges(),
        }