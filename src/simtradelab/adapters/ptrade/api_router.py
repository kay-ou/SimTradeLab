# -*- coding: utf-8 -*-
"""
PTrade API 路由系统

提供智能的API路由、负载均衡、故障转移和性能监控功能。
支持多个PTrade适配器实例之间的动态路由和负载分配。
"""

import asyncio
import time
import threading
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union, Tuple
from datetime import datetime, timedelta
import logging
import weakref
import hashlib

from ...core.event_bus import EventBus, Event, EventPriority
from ...plugins.base import BasePlugin, PluginMetadata, PluginConfig, PluginState
from ...exceptions import SimTradeLabError
from .adapter import PTradeAdapter, PTradeMode


class APIRouterError(SimTradeLabError):
    """API路由器异常"""
    pass


class RouteError(APIRouterError):
    """路由异常"""
    pass


class LoadBalancerError(APIRouterError):
    """负载均衡器异常"""
    pass


class HealthCheckError(APIRouterError):
    """健康检查异常"""
    pass


class RoutingStrategy(Enum):
    """路由策略"""
    ROUND_ROBIN = "round_robin"          # 轮询
    WEIGHTED_ROUND_ROBIN = "weighted_rr"  # 加权轮询
    LEAST_CONNECTIONS = "least_conn"      # 最少连接数
    LEAST_RESPONSE_TIME = "least_rt"      # 最短响应时间
    CONSISTENT_HASH = "consistent_hash"   # 一致性哈希
    RANDOM = "random"                     # 随机
    FAILOVER = "failover"                 # 故障转移


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class APIEndpoint:
    """API端点信息"""
    adapter_id: str
    adapter: PTradeAdapter
    weight: int = 1
    max_connections: int = 100
    timeout: float = 30.0
    priority: int = 0  # 优先级，数字越小优先级越高
    
    # 运行时状态
    current_connections: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    health_status: HealthStatus = HealthStatus.UNKNOWN
    last_health_check: Optional[datetime] = None


@dataclass
class APIRoute:
    """API路由配置"""
    api_name: str
    endpoints: List[APIEndpoint] = field(default_factory=list)
    strategy: RoutingStrategy = RoutingStrategy.ROUND_ROBIN
    sticky_session: bool = False  # 会话保持
    retry_count: int = 3
    circuit_breaker_threshold: float = 0.5  # 熔断阈值
    circuit_breaker_timeout: float = 60.0   # 熔断恢复时间
    
    # 运行时状态
    current_endpoint_index: int = 0
    session_map: Dict[str, str] = field(default_factory=dict)  # session_id -> adapter_id
    circuit_breaker_open: bool = False
    circuit_breaker_last_failure: Optional[datetime] = None


@dataclass
class APICallMetrics:
    """API调用指标"""
    api_name: str
    adapter_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None
    response_time: float = 0.0


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, check_interval: float = 30.0):
        self.check_interval = check_interval
        self._running = False
        self._check_thread: Optional[threading.Thread] = None
        self._endpoints: List[APIEndpoint] = []
        self._lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
    
    def add_endpoint(self, endpoint: APIEndpoint) -> None:
        """添加需要健康检查的端点"""
        with self._lock:
            if endpoint not in self._endpoints:
                self._endpoints.append(endpoint)
    
    def remove_endpoint(self, endpoint: APIEndpoint) -> None:
        """移除端点"""
        with self._lock:
            if endpoint in self._endpoints:
                self._endpoints.remove(endpoint)
    
    def start(self) -> None:
        """启动健康检查"""
        if self._running:
            return
        
        self._running = True
        self._check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self._check_thread.start()
        self.logger.info("Health checker started")
    
    def stop(self) -> None:
        """停止健康检查"""
        self._running = False
        if self._check_thread and self._check_thread.is_alive():
            self._check_thread.join(timeout=5.0)
        self.logger.info("Health checker stopped")
    
    def _health_check_loop(self) -> None:
        """健康检查循环"""
        while self._running:
            try:
                self._perform_health_checks()
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
    
    def _perform_health_checks(self) -> None:
        """执行健康检查"""
        with self._lock:
            endpoints_copy = self._endpoints.copy()
        
        for endpoint in endpoints_copy:
            try:
                self._check_endpoint_health(endpoint)
            except Exception as e:
                self.logger.error(f"Health check failed for endpoint {endpoint.adapter_id}: {e}")
                endpoint.health_status = HealthStatus.UNHEALTHY
    
    def _check_endpoint_health(self, endpoint: APIEndpoint) -> None:
        """检查单个端点的健康状态"""
        try:
            adapter = endpoint.adapter
            if not adapter or adapter.get_state() != PluginState.STARTED:
                endpoint.health_status = HealthStatus.UNHEALTHY
                return
            
            # 计算成功率
            total_requests = endpoint.total_requests
            if total_requests > 0:
                success_rate = endpoint.successful_requests / total_requests
                avg_response_time = endpoint.total_response_time / endpoint.successful_requests if endpoint.successful_requests > 0 else 0
                
                # 根据成功率和响应时间判断健康状态
                if success_rate >= 0.95 and avg_response_time < 1.0:
                    endpoint.health_status = HealthStatus.HEALTHY
                elif success_rate >= 0.8 and avg_response_time < 3.0:
                    endpoint.health_status = HealthStatus.DEGRADED
                else:
                    endpoint.health_status = HealthStatus.UNHEALTHY
            else:
                endpoint.health_status = HealthStatus.HEALTHY  # 新端点默认健康
            
            endpoint.last_health_check = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Health check error for {endpoint.adapter_id}: {e}")
            endpoint.health_status = HealthStatus.UNHEALTHY


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)
    
    def select_endpoint(self, route: APIRoute, session_id: Optional[str] = None) -> Optional[APIEndpoint]:
        """选择端点"""
        healthy_endpoints = [ep for ep in route.endpoints if ep.health_status == HealthStatus.HEALTHY]
        
        if not healthy_endpoints:
            # 如果没有健康的端点，尝试使用状态为DEGRADED的端点
            degraded_endpoints = [ep for ep in route.endpoints if ep.health_status == HealthStatus.DEGRADED]
            if degraded_endpoints:
                healthy_endpoints = degraded_endpoints
            else:
                return None
        
        # 检查熔断器状态
        if route.circuit_breaker_open:
            if (route.circuit_breaker_last_failure and 
                datetime.now() - route.circuit_breaker_last_failure > timedelta(seconds=route.circuit_breaker_timeout)):
                route.circuit_breaker_open = False
                self.logger.info(f"Circuit breaker reset for route {route.api_name}")
            else:
                return None
        
        # 会话保持
        if route.sticky_session and session_id and session_id in route.session_map:
            adapter_id = route.session_map[session_id]
            for endpoint in healthy_endpoints:
                if endpoint.adapter_id == adapter_id:
                    return endpoint
        
        # 根据策略选择端点
        if self.strategy == RoutingStrategy.ROUND_ROBIN:
            return self._round_robin_select(route, healthy_endpoints)
        elif self.strategy == RoutingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(route, healthy_endpoints)
        elif self.strategy == RoutingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(healthy_endpoints)
        elif self.strategy == RoutingStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time_select(healthy_endpoints)
        elif self.strategy == RoutingStrategy.CONSISTENT_HASH:
            return self._consistent_hash_select(route, healthy_endpoints, session_id)
        elif self.strategy == RoutingStrategy.RANDOM:
            return self._random_select(healthy_endpoints)
        elif self.strategy == RoutingStrategy.FAILOVER:
            return self._failover_select(healthy_endpoints)
        else:
            return self._round_robin_select(route, healthy_endpoints)
    
    def _round_robin_select(self, route: APIRoute, endpoints: List[APIEndpoint]) -> APIEndpoint:
        """轮询选择"""
        if not endpoints:
            raise LoadBalancerError("No available endpoints")
        
        endpoint = endpoints[route.current_endpoint_index % len(endpoints)]
        route.current_endpoint_index = (route.current_endpoint_index + 1) % len(endpoints)
        return endpoint
    
    def _weighted_round_robin_select(self, route: APIRoute, endpoints: List[APIEndpoint]) -> APIEndpoint:
        """加权轮询选择"""
        if not endpoints:
            raise LoadBalancerError("No available endpoints")
        
        # 计算权重总和
        total_weight = sum(ep.weight for ep in endpoints)
        if total_weight <= 0:
            return self._round_robin_select(route, endpoints)
        
        # 基于权重选择
        target = route.current_endpoint_index % total_weight
        current_weight = 0
        
        for endpoint in endpoints:
            current_weight += endpoint.weight
            if target < current_weight:
                route.current_endpoint_index += 1
                return endpoint
        
        # 回退到轮询
        return self._round_robin_select(route, endpoints)
    
    def _least_connections_select(self, endpoints: List[APIEndpoint]) -> APIEndpoint:
        """最少连接数选择"""
        if not endpoints:
            raise LoadBalancerError("No available endpoints")
        
        return min(endpoints, key=lambda ep: ep.current_connections)
    
    def _least_response_time_select(self, endpoints: List[APIEndpoint]) -> APIEndpoint:
        """最短响应时间选择"""
        if not endpoints:
            raise LoadBalancerError("No available endpoints")
        
        def avg_response_time(ep: APIEndpoint) -> float:
            if ep.successful_requests > 0:
                return ep.total_response_time / ep.successful_requests
            return 0.0
        
        return min(endpoints, key=avg_response_time)
    
    def _consistent_hash_select(self, route: APIRoute, endpoints: List[APIEndpoint], 
                               session_id: Optional[str]) -> APIEndpoint:
        """一致性哈希选择"""
        if not endpoints:
            raise LoadBalancerError("No available endpoints")
        
        # 使用API名称和会话ID计算哈希
        hash_input = f"{route.api_name}:{session_id or ''}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        return endpoints[hash_value % len(endpoints)]
    
    def _random_select(self, endpoints: List[APIEndpoint]) -> APIEndpoint:
        """随机选择"""
        if not endpoints:
            raise LoadBalancerError("No available endpoints")
        
        import random
        return random.choice(endpoints)
    
    def _failover_select(self, endpoints: List[APIEndpoint]) -> APIEndpoint:
        """故障转移选择（按优先级）"""
        if not endpoints:
            raise LoadBalancerError("No available endpoints")
        
        # 按优先级排序，选择优先级最高的健康端点
        sorted_endpoints = sorted(endpoints, key=lambda ep: ep.priority)
        return sorted_endpoints[0]


class APIRouter(BasePlugin):
    """
    PTrade API 路由器
    
    提供智能API路由、负载均衡、故障转移和性能监控功能。
    """
    
    METADATA = PluginMetadata(
        name="ptrade_api_router",
        version="1.0.0",
        description="PTrade API Router with Load Balancing and Failover",
        author="SimTradeLab",
        dependencies=["ptrade_complete_adapter"],
        tags=["ptrade", "router", "load_balancer", "failover"],
        category="infrastructure",
        priority=5  # 中等优先级
    )
    
    def __init__(self, metadata: PluginMetadata, config: Optional[PluginConfig] = None):
        super().__init__(metadata, config)
        
        # 路由表
        self._routes: Dict[str, APIRoute] = {}
        self._adapters: Dict[str, PTradeAdapter] = {}
        
        # 负载均衡器
        self._load_balancer = LoadBalancer(
            strategy=RoutingStrategy(self._config.config.get('routing_strategy', 'round_robin'))
        )
        
        # 健康检查器
        self._health_checker = HealthChecker(
            check_interval=self._config.config.get('health_check_interval', 30.0)
        )
        
        # 性能监控
        self._metrics: List[APICallMetrics] = []
        self._metrics_lock = threading.RLock()
        self._max_metrics = self._config.config.get('max_metrics', 10000)
        
        # 会话管理
        self._sessions: Dict[str, datetime] = {}
        self._session_timeout = self._config.config.get('session_timeout', 3600)  # 1小时
        
        # 统计信息
        self._stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'circuit_breaker_trips': 0
        }
    
    def _on_initialize(self) -> None:
        """初始化路由器"""
        self._logger.info("Initializing PTrade API Router")
        
        # 启动健康检查器
        self._health_checker.start()
        
        # 设置会话清理定时器
        self._setup_session_cleanup()
        
        self._logger.info("PTrade API Router initialized")
    
    def _on_start(self) -> None:
        """启动路由器"""
        self._logger.info("Starting PTrade API Router")
        
        # 发布路由器启动事件
        if hasattr(self, '_event_bus'):
            self._event_bus.publish(
                "ptrade.router.started",
                data={'router': self, 'routes_count': len(self._routes)},
                source="ptrade_router"
            )
    
    def _on_stop(self) -> None:
        """停止路由器"""
        self._logger.info("Stopping PTrade API Router")
        
        # 停止健康检查器
        self._health_checker.stop()
        
        # 清理资源
        self._cleanup_resources()
    
    def register_adapter(self, adapter: PTradeAdapter, weight: int = 1, 
                        max_connections: int = 100, priority: int = 0) -> str:
        """
        注册PTrade适配器
        
        Args:
            adapter: PTrade适配器实例
            weight: 权重
            max_connections: 最大连接数
            priority: 优先级
            
        Returns:
            适配器ID
        """
        adapter_id = f"{adapter.get_metadata().name}_{id(adapter)}"
        
        if adapter_id in self._adapters:
            raise APIRouterError(f"Adapter {adapter_id} already registered")
        
        self._adapters[adapter_id] = adapter
        
        # 创建端点
        endpoint = APIEndpoint(
            adapter_id=adapter_id,
            adapter=adapter,
            weight=weight,
            max_connections=max_connections,
            priority=priority
        )
        
        # 添加到健康检查
        self._health_checker.add_endpoint(endpoint)
        
        # 为所有API创建路由
        self._create_routes_for_adapter(adapter_id, endpoint)
        
        self._logger.info(f"Registered adapter {adapter_id} with {len(self._routes)} routes")
        return adapter_id
    
    def unregister_adapter(self, adapter_id: str) -> bool:
        """
        注销PTrade适配器
        
        Args:
            adapter_id: 适配器ID
            
        Returns:
            是否成功注销
        """
        if adapter_id not in self._adapters:
            return False
        
        # 从所有路由中移除此适配器
        for route in self._routes.values():
            route.endpoints = [ep for ep in route.endpoints if ep.adapter_id != adapter_id]
        
        # 移除空路由
        empty_routes = [api_name for api_name, route in self._routes.items() if not route.endpoints]
        for api_name in empty_routes:
            del self._routes[api_name]
        
        # 从健康检查中移除
        adapter = self._adapters[adapter_id]
        endpoints_to_remove = [ep for route in self._routes.values() for ep in route.endpoints if ep.adapter_id == adapter_id]
        for endpoint in endpoints_to_remove:
            self._health_checker.remove_endpoint(endpoint)
        
        del self._adapters[adapter_id]
        
        self._logger.info(f"Unregistered adapter {adapter_id}")
        return True
    
    def _create_routes_for_adapter(self, adapter_id: str, endpoint: APIEndpoint) -> None:
        """为适配器创建路由"""
        adapter = self._adapters[adapter_id]
        
        # 获取适配器支持的所有API
        if hasattr(adapter, '_api_registry'):
            api_names = adapter._api_registry.list_all_apis()
            
            for api_name in api_names:
                if api_name not in self._routes:
                    # 创建新路由
                    self._routes[api_name] = APIRoute(
                        api_name=api_name,
                        endpoints=[endpoint],
                        strategy=self._load_balancer.strategy
                    )
                else:
                    # 添加到现有路由
                    route = self._routes[api_name]
                    if not any(ep.adapter_id == adapter_id for ep in route.endpoints):
                        route.endpoints.append(endpoint)
    
    def call_api(self, api_name: str, *args, session_id: Optional[str] = None, **kwargs) -> Any:
        """
        调用API
        
        Args:
            api_name: API名称
            *args: 位置参数
            session_id: 会话ID（用于会话保持）
            **kwargs: 关键字参数
            
        Returns:
            API调用结果
        """
        if api_name not in self._routes:
            raise RouteError(f"No route found for API: {api_name}")
        
        route = self._routes[api_name]
        start_time = datetime.now()
        
        # 更新会话
        if session_id:
            self._sessions[session_id] = start_time
        
        # 重试逻辑
        last_error = None
        for attempt in range(route.retry_count + 1):
            try:
                # 选择端点
                endpoint = self._load_balancer.select_endpoint(route, session_id)
                if not endpoint:
                    if route.circuit_breaker_open:
                        raise RouteError(f"Circuit breaker is open for API: {api_name}")
                    else:
                        raise RouteError(f"No available endpoints for API: {api_name}")
                
                # 检查连接数限制
                if endpoint.current_connections >= endpoint.max_connections:
                    if attempt < route.retry_count:
                        continue
                    raise RouteError(f"Endpoint {endpoint.adapter_id} connection limit exceeded")
                
                # 执行API调用
                result = self._execute_api_call(endpoint, api_name, *args, **kwargs)
                
                # 记录成功指标
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                self._record_metrics(APICallMetrics(
                    api_name=api_name,
                    adapter_id=endpoint.adapter_id,
                    start_time=start_time,
                    end_time=end_time,
                    success=True,
                    response_time=response_time
                ))
                
                self._update_endpoint_stats(endpoint, True, response_time)
                
                # 更新会话映射
                if route.sticky_session and session_id:
                    route.session_map[session_id] = endpoint.adapter_id
                
                return result
                
            except Exception as e:
                last_error = e
                self._logger.warning(f"API call failed (attempt {attempt + 1}): {api_name} - {e}")
                
                if endpoint:
                    self._update_endpoint_stats(endpoint, False, 0.0)
                    
                    # 检查是否需要触发熔断器
                    self._check_circuit_breaker(route, endpoint)
                
                if attempt < route.retry_count:
                    time.sleep(0.1 * (2 ** attempt))  # 指数退避
                else:
                    # 记录失败指标
                    self._record_metrics(APICallMetrics(
                        api_name=api_name,
                        adapter_id=endpoint.adapter_id if endpoint else "unknown",
                        start_time=start_time,
                        end_time=datetime.now(),
                        success=False,
                        error_message=str(e)
                    ))
        
        # 所有重试都失败了
        raise RouteError(f"API call failed after {route.retry_count + 1} attempts: {last_error}")
    
    def _execute_api_call(self, endpoint: APIEndpoint, api_name: str, *args, **kwargs) -> Any:
        """执行API调用"""
        endpoint.current_connections += 1
        endpoint.total_requests += 1
        endpoint.last_request_time = datetime.now()
        
        try:
            adapter = endpoint.adapter
            
            # 检查适配器状态
            if adapter.get_state() != PluginState.STARTED:
                raise RouteError(f"Adapter {endpoint.adapter_id} is not started")
            
            # 检查API可用性
            if hasattr(adapter, '_check_api_availability'):
                adapter._check_api_availability(api_name)
            
            # 获取API函数
            api_registry = getattr(adapter, '_api_registry', None)
            if not api_registry:
                raise RouteError(f"No API registry found in adapter {endpoint.adapter_id}")
            
            api_func = api_registry.get_api(api_name)
            if not api_func:
                raise RouteError(f"API {api_name} not found in adapter {endpoint.adapter_id}")
            
            # 执行API调用
            result = api_func(*args, **kwargs)
            return result
            
        finally:
            endpoint.current_connections -= 1
    
    def _update_endpoint_stats(self, endpoint: APIEndpoint, success: bool, response_time: float) -> None:
        """更新端点统计信息"""
        if success:
            endpoint.successful_requests += 1
            endpoint.total_response_time += response_time
        else:
            endpoint.failed_requests += 1
        
        # 更新全局统计
        self._stats['total_requests'] += 1
        if success:
            self._stats['successful_requests'] += 1
            self._stats['total_response_time'] += response_time
        else:
            self._stats['failed_requests'] += 1
    
    def _check_circuit_breaker(self, route: APIRoute, endpoint: APIEndpoint) -> None:
        """检查熔断器"""
        if endpoint.total_requests < 10:  # 最少10个请求才考虑熔断
            return
        
        error_rate = endpoint.failed_requests / endpoint.total_requests
        if error_rate >= route.circuit_breaker_threshold:
            route.circuit_breaker_open = True
            route.circuit_breaker_last_failure = datetime.now()
            self._stats['circuit_breaker_trips'] += 1
            self._logger.warning(f"Circuit breaker opened for route {route.api_name}, error rate: {error_rate:.2%}")
    
    def _record_metrics(self, metrics: APICallMetrics) -> None:
        """记录指标"""
        with self._metrics_lock:
            self._metrics.append(metrics)
            
            # 限制指标数量
            if len(self._metrics) > self._max_metrics:
                self._metrics = self._metrics[-self._max_metrics:]
    
    def _setup_session_cleanup(self) -> None:
        """设置会话清理"""
        def cleanup_sessions():
            while True:
                try:
                    now = datetime.now()
                    expired_sessions = [
                        session_id for session_id, last_access in self._sessions.items()
                        if (now - last_access).total_seconds() > self._session_timeout
                    ]
                    
                    for session_id in expired_sessions:
                        del self._sessions[session_id]
                        
                        # 清理路由中的会话映射
                        for route in self._routes.values():
                            if session_id in route.session_map:
                                del route.session_map[session_id]
                    
                    if expired_sessions:
                        self._logger.debug(f"Cleaned up {len(expired_sessions)} expired sessions")
                    
                    time.sleep(300)  # 每5分钟清理一次
                    
                except Exception as e:
                    self._logger.error(f"Session cleanup error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_sessions, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_resources(self) -> None:
        """清理资源"""
        self._routes.clear()
        self._adapters.clear()
        self._sessions.clear()
        
        with self._metrics_lock:
            self._metrics.clear()
    
    # =========================================
    # 公共接口
    # =========================================
    
    def get_route_stats(self, api_name: Optional[str] = None) -> Dict[str, Any]:
        """获取路由统计信息"""
        if api_name:
            if api_name not in self._routes:
                return {}
            
            route = self._routes[api_name]
            return {
                'api_name': api_name,
                'endpoints_count': len(route.endpoints),
                'strategy': route.strategy.value,
                'circuit_breaker_open': route.circuit_breaker_open,
                'endpoints': [
                    {
                        'adapter_id': ep.adapter_id,
                        'weight': ep.weight,
                        'health_status': ep.health_status.value,
                        'current_connections': ep.current_connections,
                        'total_requests': ep.total_requests,
                        'successful_requests': ep.successful_requests,
                        'failed_requests': ep.failed_requests,
                        'avg_response_time': ep.total_response_time / ep.successful_requests if ep.successful_requests > 0 else 0,
                        'success_rate': ep.successful_requests / ep.total_requests if ep.total_requests > 0 else 0
                    }
                    for ep in route.endpoints
                ]
            }
        else:
            return {
                'total_routes': len(self._routes),
                'total_adapters': len(self._adapters),
                'global_stats': self._stats.copy(),
                'routes': [self.get_route_stats(name) for name in self._routes.keys()]
            }
    
    def get_performance_metrics(self, api_name: Optional[str] = None, 
                               time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """获取性能指标"""
        with self._metrics_lock:
            metrics = self._metrics.copy()
        
        # 时间窗口过滤
        if time_window:
            cutoff_time = datetime.now() - time_window
            metrics = [m for m in metrics if m.start_time >= cutoff_time]
        
        # API过滤
        if api_name:
            metrics = [m for m in metrics if m.api_name == api_name]
        
        if not metrics:
            return {}
        
        # 计算统计信息
        successful_metrics = [m for m in metrics if m.success]
        failed_metrics = [m for m in metrics if not m.success]
        
        response_times = [m.response_time for m in successful_metrics]
        
        return {
            'total_calls': len(metrics),
            'successful_calls': len(successful_metrics),
            'failed_calls': len(failed_metrics),
            'success_rate': len(successful_metrics) / len(metrics) if metrics else 0,
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'p95_response_time': statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else (max(response_times) if response_times else 0),
            'error_distribution': self._get_error_distribution(failed_metrics)
        }
    
    def _get_error_distribution(self, failed_metrics: List[APICallMetrics]) -> Dict[str, int]:
        """获取错误分布"""
        error_counts = defaultdict(int)
        for metrics in failed_metrics:
            error_type = type(Exception(metrics.error_message or "unknown")).__name__
            error_counts[error_type] += 1
        return dict(error_counts)
    
    def update_routing_strategy(self, strategy: RoutingStrategy) -> None:
        """更新路由策略"""
        self._load_balancer.strategy = strategy
        for route in self._routes.values():
            route.strategy = strategy
        
        self._logger.info(f"Updated routing strategy to {strategy.value}")
    
    def reset_circuit_breaker(self, api_name: str) -> bool:
        """重置熔断器"""
        if api_name not in self._routes:
            return False
        
        route = self._routes[api_name]
        route.circuit_breaker_open = False
        route.circuit_breaker_last_failure = None
        
        self._logger.info(f"Circuit breaker reset for API {api_name}")
        return True
    
    def get_adapter_health(self) -> Dict[str, Dict[str, Any]]:
        """获取适配器健康状态"""
        health_status = {}
        
        for route in self._routes.values():
            for endpoint in route.endpoints:
                if endpoint.adapter_id not in health_status:
                    health_status[endpoint.adapter_id] = {
                        'health_status': endpoint.health_status.value,
                        'total_requests': endpoint.total_requests,
                        'successful_requests': endpoint.successful_requests,
                        'failed_requests': endpoint.failed_requests,
                        'current_connections': endpoint.current_connections,
                        'last_health_check': endpoint.last_health_check.isoformat() if endpoint.last_health_check else None,
                        'avg_response_time': endpoint.total_response_time / endpoint.successful_requests if endpoint.successful_requests > 0 else 0
                    }
        
        return health_status