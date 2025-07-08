# SimTradeLab 完整插件化架构设计文档 v4.0

## 1. 架构总览

### 1.1 设计原则

基于PTrade API深入分析和实际生产需求，本架构遵循以下核心原则：

1. **性能优先**：核心交易功能不使用插件，确保最佳性能
2. **完全兼容**：100%遵循PTrade官方API文档规范
3. **合理插件化**：每个插件都有充分的技术和业务理由
4. **生产就绪**：支持企业级部署和多平台扩展
5. **开发友好**：提供完整的开发工具链和调试支持
6. **动态可控**：支持插件热插拔和运行时配置更新
7. **安全隔离**：多级沙箱机制保障系统安全性

### 1.2 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    平台适配层                                │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │   PTrade适配器   │    │  掘金适配器      │                 │
│  │   adapter.py    │    │  adapter.py     │                 │
│  └─────────────────┘    └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    核心框架层                                │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │   核心引擎       │    │   插件管理器     │                 │
│  │   engine.py     │    │   plugin_mgr.py │                 │
│  └─────────────────┘    └─────────────────┘                 │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ 生命周期管理器   │    │   安全沙箱       │                 │
│  │ lifecycle_mgr.py│    │   sandbox.py    │                 │
│  └─────────────────┘    └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    插件扩展层                                │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│  │   数据     │ │   策略     │ │   分析     │ │   集成     │   │
│  │   插件     │ │   插件     │ │   插件     │ │   插件     │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│  │ 监控告警   │ │ 配置中心   │ │ 分布式     │ │ 可视化     │   │
│  │   插件     │ │   插件     │ │ 缓存插件   │ │   插件     │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 v4.0新增特性

**🔥 插件生命周期管理**
- 热插拔支持：无需重启系统即可加载/卸载插件
- 版本升级：支持插件在线升级和回滚
- 状态迁移：插件重载时保持运行状态

**🔒 多级安全隔离**
- 线程级隔离：轻量级隔离适用于可信插件
- 进程级隔离：中等安全级别，独立进程运行
- 容器级隔离：最高安全级别，Docker容器隔离

**📊 动态配置中心**
- 实时配置更新：运行时修改插件配置
- 配置历史追踪：完整的配置变更记录
- 配置回滚：支持配置快速回滚到历史版本

**🚀 智能数据分层**
- 冷热数据分离：热数据内存缓存，冷数据归档存储
- 分布式缓存：多节点缓存集群支持动态扩展
- 智能迁移：基于访问模式自动数据迁移

## 2. PTrade实盘/回测模式区分设计

### 2.1 模式感知适配器

```python
# src/simtradelab/adapters/ptrade/adapter.py
class PTradeAdapter:
    """PTrade模式感知适配器"""
    
    def __init__(self, core_engine, mode='backtest'):
        self.core = core_engine
        self.mode = mode  # 'backtest' | 'live'
        self.api_router = self._init_api_router()
    
    def _init_api_router(self):
        """初始化API路由器"""
        if self.mode == 'backtest':
            return BacktestAPIRouter(self.core)
        else:
            return LiveTradingAPIRouter(self.core)
    
    # === 统一接口，内部路由到不同实现 ===
    def handle_data(self, context, data):
        """主策略函数 - 统一接口"""
        return self.api_router.handle_data(context, data)
    
    def order(self, security, amount, limit_price=None):
        """下单 - 根据模式路由"""
        return self.api_router.order(security, amount, limit_price)
```

### 2.2 设计优缺点分析

| 优点 | 缺点 |
|------|------|
| ✅ 统一API接口，策略代码无需修改 | ⚠️ 增加了一层抽象复杂度 |
| ✅ 模式切换简单，只需改配置 | ⚠️ 调试时需要明确当前模式 |
| ✅ 避免了模式特定代码分支 | ⚠️ 某些实盘专用功能在回测中无意义 |
| ✅ 便于单元测试和模式验证 | ⚠️ 性能开销（路由层） |

**选择理由**：这种设计最大化了代码复用，同时保持了清晰的模式边界。

## 3. 插件生命周期管理和热插拔

### 3.1 插件生命周期管理器

```python
# src/simtradelab/plugins/lifecycle/plugin_lifecycle_manager.py
class PluginLifecycleManager(BasePlugin):
    """插件生命周期管理器 - 支持热插拔和动态加载"""
    
    def __init__(self, config):
        super().__init__(config)
        self.loaded_plugins = {}
        self.plugin_dependencies = {}
        self.plugin_states = {}
        self.event_bus = EventBus()
        
    def load_plugin(self, plugin_name, plugin_config, hot_load=True):
        """动态加载插件"""
        try:
            # 检查依赖关系
            if not self._check_dependencies(plugin_name, plugin_config):
                raise PluginDependencyError(f"Plugin {plugin_name} dependencies not satisfied")
            
            # 加载插件模块
            plugin_module = importlib.import_module(plugin_config['module_path'])
            plugin_class = getattr(plugin_module, plugin_config['class_name'])
            
            # 创建插件实例
            plugin_instance = plugin_class(plugin_config.get('config', {}))
            
            # 如果是热加载，需要进行状态迁移
            if hot_load and plugin_name in self.loaded_plugins:
                self._migrate_plugin_state(plugin_name, plugin_instance)
            
            # 注册插件
            self.loaded_plugins[plugin_name] = plugin_instance
            self.plugin_states[plugin_name] = 'loaded'
            
            # 发送插件加载事件
            self.event_bus.emit('plugin_loaded', {
                'plugin_name': plugin_name,
                'plugin_instance': plugin_instance,
                'timestamp': datetime.now()
            })
            
            logger.info(f"Plugin {plugin_name} loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name, graceful=True):
        """卸载插件"""
        if plugin_name not in self.loaded_plugins:
            logger.warning(f"Plugin {plugin_name} not found")
            return False
        
        try:
            plugin_instance = self.loaded_plugins[plugin_name]
            
            # 优雅关闭：保存状态，清理资源
            if graceful and hasattr(plugin_instance, 'cleanup'):
                plugin_instance.cleanup()
            
            # 检查依赖关系，确保没有其他插件依赖此插件
            dependents = self._get_plugin_dependents(plugin_name)
            if dependents:
                logger.warning(f"Plugin {plugin_name} has dependents: {dependents}")
                if not graceful:
                    # 强制卸载依赖插件
                    for dependent in dependents:
                        self.unload_plugin(dependent, graceful=False)
            
            # 移除插件
            del self.loaded_plugins[plugin_name]
            self.plugin_states[plugin_name] = 'unloaded'
            
            # 发送插件卸载事件
            self.event_bus.emit('plugin_unloaded', {
                'plugin_name': plugin_name,
                'timestamp': datetime.now()
            })
            
            logger.info(f"Plugin {plugin_name} unloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False
    
    def reload_plugin(self, plugin_name):
        """重新加载插件"""
        if plugin_name not in self.loaded_plugins:
            logger.warning(f"Plugin {plugin_name} not loaded")
            return False
        
        # 获取当前配置
        current_config = self.loaded_plugins[plugin_name].config
        
        # 卸载并重新加载
        if self.unload_plugin(plugin_name):
            return self.load_plugin(plugin_name, current_config)
        
        return False
    
    def upgrade_plugin(self, plugin_name, new_version_config):
        """升级插件版本"""
        old_plugin = self.loaded_plugins.get(plugin_name)
        if not old_plugin:
            logger.warning(f"Plugin {plugin_name} not found for upgrade")
            return False
        
        try:
            # 备份当前状态
            backup_state = self._backup_plugin_state(plugin_name)
            
            # 卸载旧版本
            if not self.unload_plugin(plugin_name):
                return False
            
            # 加载新版本
            if self.load_plugin(plugin_name, new_version_config):
                # 迁移状态
                self._restore_plugin_state(plugin_name, backup_state)
                logger.info(f"Plugin {plugin_name} upgraded successfully")
                return True
            else:
                # 升级失败，回滚
                self.load_plugin(plugin_name, old_plugin.config)
                self._restore_plugin_state(plugin_name, backup_state)
                logger.error(f"Plugin {plugin_name} upgrade failed, rolled back")
                return False
                
        except Exception as e:
            logger.error(f"Plugin {plugin_name} upgrade error: {e}")
            return False
    
    def get_plugin_info(self, plugin_name):
        """获取插件信息"""
        if plugin_name not in self.loaded_plugins:
            return None
        
        plugin = self.loaded_plugins[plugin_name]
        return {
            'name': plugin_name,
            'version': getattr(plugin, 'version', '1.0.0'),
            'status': self.plugin_states[plugin_name],
            'dependencies': self.plugin_dependencies.get(plugin_name, []),
            'memory_usage': self._get_plugin_memory_usage(plugin_name),
            'cpu_usage': self._get_plugin_cpu_usage(plugin_name),
            'uptime': self._get_plugin_uptime(plugin_name)
        }
```

### 3.2 插件状态迁移

```python
def _migrate_plugin_state(self, plugin_name, new_plugin_instance):
    """迁移插件状态"""
    old_plugin = self.loaded_plugins.get(plugin_name)
    if old_plugin and hasattr(old_plugin, 'get_state'):
        old_state = old_plugin.get_state()
        if hasattr(new_plugin_instance, 'set_state'):
            new_plugin_instance.set_state(old_state)
            logger.info(f"Migrated state for plugin {plugin_name}")

def _backup_plugin_state(self, plugin_name):
    """备份插件状态"""
    plugin = self.loaded_plugins.get(plugin_name)
    if plugin and hasattr(plugin, 'get_state'):
        return plugin.get_state()
    return None

def _restore_plugin_state(self, plugin_name, backup_state):
    """恢复插件状态"""
    if backup_state is None:
        return
    
    plugin = self.loaded_plugins.get(plugin_name)
    if plugin and hasattr(plugin, 'set_state'):
        plugin.set_state(backup_state)
        logger.info(f"Restored state for plugin {plugin_name}")
```

### 3.3 依赖关系管理

```python
def _check_dependencies(self, plugin_name, plugin_config):
    """检查插件依赖关系"""
    dependencies = plugin_config.get('dependencies', [])
    for dep in dependencies:
        if dep not in self.loaded_plugins:
            logger.error(f"Dependency {dep} not loaded for plugin {plugin_name}")
            return False
        
        # 检查依赖版本兼容性
        dep_version = getattr(self.loaded_plugins[dep], 'version', '1.0.0')
        required_version = plugin_config.get('dependency_versions', {}).get(dep)
        
        if required_version and not self._is_version_compatible(dep_version, required_version):
            logger.error(f"Dependency {dep} version {dep_version} not compatible with required {required_version}")
            return False
    
    return True

def _get_plugin_dependents(self, plugin_name):
    """获取依赖某个插件的其他插件"""
    dependents = []
    for name, dependencies in self.plugin_dependencies.items():
        if plugin_name in dependencies:
            dependents.append(name)
    return dependents
```

## 4. 插件隔离和安全（沙箱）

### 4.1 多级沙箱系统

```python
# src/simtradelab/plugins/security/plugin_sandbox.py
class PluginSandbox:
    """插件沙箱系统 - 提供多级隔离机制"""
    
    def __init__(self, isolation_level='process'):
        self.isolation_level = isolation_level  # 'thread', 'process', 'container'
        self.resource_limits = {}
        self.permission_manager = PermissionManager()
        self.sandboxed_plugins = {}
        
    def create_sandbox(self, plugin_name, plugin_config):
        """创建插件沙箱"""
        if self.isolation_level == 'thread':
            return self._create_thread_sandbox(plugin_name, plugin_config)
        elif self.isolation_level == 'process':
            return self._create_process_sandbox(plugin_name, plugin_config)
        elif self.isolation_level == 'container':
            return self._create_container_sandbox(plugin_name, plugin_config)
        else:
            raise ValueError(f"Unsupported isolation level: {self.isolation_level}")
    
    def _create_thread_sandbox(self, plugin_name, plugin_config):
        """创建线程级沙箱"""
        import threading
        from concurrent.futures import ThreadPoolExecutor
        
        # 创建专用线程池
        executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix=f"plugin_{plugin_name}"
        )
        
        # 设置资源限制
        resource_monitor = ResourceMonitor()
        resource_monitor.set_limits(
            memory_limit=plugin_config.get('memory_limit', '256MB'),
            cpu_limit=plugin_config.get('cpu_limit', '50%')
        )
        
        sandbox = {
            'type': 'thread',
            'executor': executor,
            'resource_monitor': resource_monitor,
            'permissions': self.permission_manager.get_permissions(plugin_name)
        }
        
        self.sandboxed_plugins[plugin_name] = sandbox
        return sandbox
    
    def _create_process_sandbox(self, plugin_name, plugin_config):
        """创建进程级沙箱"""
        import multiprocessing
        import subprocess
        
        # 创建独立进程
        process_config = {
            'memory_limit': plugin_config.get('memory_limit', '512MB'),
            'cpu_limit': plugin_config.get('cpu_limit', '30%'),
            'network_access': plugin_config.get('network_access', False),
            'file_system_access': plugin_config.get('file_system_access', 'read-only')
        }
        
        # 启动沙箱进程
        process = subprocess.Popen([
            'python', '-m', 'simtradelab.plugins.security.sandbox_runner',
            '--plugin-name', plugin_name,
            '--config', json.dumps(process_config)
        ], 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
        )
        
        sandbox = {
            'type': 'process',
            'process': process,
            'config': process_config,
            'permissions': self.permission_manager.get_permissions(plugin_name)
        }
        
        self.sandboxed_plugins[plugin_name] = sandbox
        return sandbox
    
    def _create_container_sandbox(self, plugin_name, plugin_config):
        """创建容器级沙箱"""
        import docker
        
        client = docker.from_env()
        
        # 创建Docker容器
        container_config = {
            'image': 'simtradelab/plugin-sandbox:latest',
            'command': ['python', '-m', 'simtradelab.plugins.security.container_runner'],
            'environment': {
                'PLUGIN_NAME': plugin_name,
                'PLUGIN_CONFIG': json.dumps(plugin_config)
            },
            'mem_limit': plugin_config.get('memory_limit', '512m'),
            'cpu_quota': int(plugin_config.get('cpu_limit', '50000')),  # 50% CPU
            'network_mode': 'none' if not plugin_config.get('network_access', False) else 'bridge',
            'read_only': plugin_config.get('file_system_access', 'read-only') == 'read-only'
        }
        
        container = client.containers.run(
            **container_config,
            detach=True,
            name=f"plugin_{plugin_name}"
        )
        
        sandbox = {
            'type': 'container',
            'container': container,
            'config': container_config,
            'permissions': self.permission_manager.get_permissions(plugin_name)
        }
        
        self.sandboxed_plugins[plugin_name] = sandbox
        return sandbox
```

### 4.2 权限管理系统

```python
class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        self.permissions = {}
        self.default_permissions = {
            'data_access': ['read'],
            'trading': ['view'],
            'system': [],
            'network': []
        }
    
    def set_plugin_permissions(self, plugin_name, permissions):
        """设置插件权限"""
        self.permissions[plugin_name] = permissions
    
    def check_permission(self, plugin_name, operation):
        """检查插件权限"""
        plugin_permissions = self.permissions.get(plugin_name, self.default_permissions)
        
        # 根据操作类型检查权限
        if operation.startswith('get_') or operation.startswith('read_'):
            return 'read' in plugin_permissions.get('data_access', [])
        elif operation.startswith('order') or operation.startswith('trade'):
            return 'execute' in plugin_permissions.get('trading', [])
        elif operation.startswith('system_'):
            return 'admin' in plugin_permissions.get('system', [])
        elif operation.startswith('network_'):
            return 'access' in plugin_permissions.get('network', [])
        
        return False
    
    def get_permissions(self, plugin_name):
        """获取插件权限"""
        return self.permissions.get(plugin_name, self.default_permissions)
```

### 4.3 沙箱执行和监控

```python
def execute_in_sandbox(self, plugin_name, method_name, *args, **kwargs):
    """在沙箱中执行插件方法"""
    if plugin_name not in self.sandboxed_plugins:
        raise PluginNotFoundError(f"Plugin {plugin_name} not in sandbox")
    
    sandbox = self.sandboxed_plugins[plugin_name]
    
    # 检查权限
    if not self.permission_manager.check_permission(plugin_name, method_name):
        raise PermissionError(f"Plugin {plugin_name} not allowed to execute {method_name}")
    
    # 根据沙箱类型执行
    if sandbox['type'] == 'thread':
        return self._execute_in_thread_sandbox(sandbox, method_name, *args, **kwargs)
    elif sandbox['type'] == 'process':
        return self._execute_in_process_sandbox(sandbox, method_name, *args, **kwargs)
    elif sandbox['type'] == 'container':
        return self._execute_in_container_sandbox(sandbox, method_name, *args, **kwargs)

def monitor_sandbox_resources(self, plugin_name):
    """监控沙箱资源使用"""
    if plugin_name not in self.sandboxed_plugins:
        return None
    
    sandbox = self.sandboxed_plugins[plugin_name]
    
    if sandbox['type'] == 'thread':
        return sandbox['resource_monitor'].get_current_usage()
    elif sandbox['type'] == 'process':
        return self._get_process_resource_usage(sandbox['process'])
    elif sandbox['type'] == 'container':
        return self._get_container_resource_usage(sandbox['container'])

def cleanup_sandbox(self, plugin_name):
    """清理沙箱资源"""
    if plugin_name not in self.sandboxed_plugins:
        return
    
    sandbox = self.sandboxed_plugins[plugin_name]
    
    if sandbox['type'] == 'thread':
        sandbox['executor'].shutdown(wait=True)
    elif sandbox['type'] == 'process':
        sandbox['process'].terminate()
        sandbox['process'].wait(timeout=30)
    elif sandbox['type'] == 'container':
        sandbox['container'].stop()
        sandbox['container'].remove()
    
    del self.sandboxed_plugins[plugin_name]
```

## 5. 动态配置中心和监控系统

### 5.1 动态配置中心

```python
# src/simtradelab/plugins/config/dynamic_config_center.py
class DynamicConfigCenter:
    """动态配置中心 - 支持运行时配置更新"""
    
    def __init__(self, config_source='file'):
        self.config_source = config_source
        self.config_cache = {}
        self.config_watchers = {}
        self.update_callbacks = defaultdict(list)
        self.config_history = []
        
        # 启动配置监听器
        self.start_config_watcher()
    
    def get_config(self, plugin_name, key=None, default=None):
        """获取配置"""
        if plugin_name not in self.config_cache:
            self.load_plugin_config(plugin_name)
        
        plugin_config = self.config_cache.get(plugin_name, {})
        
        if key is None:
            return plugin_config
        
        return plugin_config.get(key, default)
    
    def update_config(self, plugin_name, key, value, notify=True):
        """更新配置"""
        if plugin_name not in self.config_cache:
            self.config_cache[plugin_name] = {}
        
        old_value = self.config_cache[plugin_name].get(key)
        self.config_cache[plugin_name][key] = value
        
        # 记录配置变更历史
        self.config_history.append({
            'timestamp': datetime.now(),
            'plugin': plugin_name,
            'key': key,
            'old_value': old_value,
            'new_value': value,
            'operation': 'update'
        })
        
        # 持久化配置
        self.persist_config(plugin_name)
        
        # 通知相关组件
        if notify:
            self.notify_config_change(plugin_name, key, old_value, value)
    
    def batch_update_config(self, plugin_name, updates):
        """批量更新配置"""
        if plugin_name not in self.config_cache:
            self.config_cache[plugin_name] = {}
        
        changes = []
        
        for key, value in updates.items():
            old_value = self.config_cache[plugin_name].get(key)
            self.config_cache[plugin_name][key] = value
            
            changes.append({
                'key': key,
                'old_value': old_value,
                'new_value': value
            })
        
        # 记录配置变更历史
        self.config_history.append({
            'timestamp': datetime.now(),
            'plugin': plugin_name,
            'changes': changes,
            'operation': 'batch_update'
        })
        
        # 持久化配置
        self.persist_config(plugin_name)
        
        # 通知配置变更
        self.notify_batch_config_change(plugin_name, changes)
    
    def register_config_callback(self, plugin_name, callback):
        """注册配置变更回调"""
        self.update_callbacks[plugin_name].append(callback)
    
    def start_config_watcher(self):
        """启动配置文件监听器"""
        if self.config_source == 'file':
            self.file_watcher = FileWatcher()
            self.file_watcher.watch_directory(
                './config/plugins',
                on_change=self.on_config_file_change
            )
        elif self.config_source == 'etcd':
            self.etcd_watcher = EtcdWatcher()
            self.etcd_watcher.watch_prefix(
                '/simtradelab/plugins/',
                on_change=self.on_etcd_config_change
            )
    
    def on_config_file_change(self, filepath):
        """配置文件变更处理"""
        plugin_name = os.path.basename(filepath).replace('.yaml', '')
        
        try:
            with open(filepath, 'r') as f:
                new_config = yaml.safe_load(f)
            
            old_config = self.config_cache.get(plugin_name, {})
            
            # 比较配置差异
            changes = self.compare_configs(old_config, new_config)
            
            if changes:
                self.config_cache[plugin_name] = new_config
                
                # 通知配置变更
                for change in changes:
                    self.notify_config_change(
                        plugin_name,
                        change['key'],
                        change['old_value'],
                        change['new_value']
                    )
                
                logger.info(f"Configuration updated for plugin {plugin_name}")
        
        except Exception as e:
            logger.error(f"Failed to reload config for {plugin_name}: {e}")
    
    def get_config_history(self, plugin_name=None, limit=100):
        """获取配置变更历史"""
        if plugin_name:
            history = [h for h in self.config_history if h.get('plugin') == plugin_name]
        else:
            history = self.config_history
        
        return history[-limit:]
    
    def rollback_config(self, plugin_name, timestamp):
        """回滚配置到指定时间点"""
        # 找到指定时间点的配置
        target_config = None
        for entry in reversed(self.config_history):
            if entry['plugin'] == plugin_name and entry['timestamp'] <= timestamp:
                target_config = entry
                break
        
        if target_config:
            # 恢复配置
            self.config_cache[plugin_name] = target_config.get('config_snapshot', {})
            self.persist_config(plugin_name)
            
            # 通知配置变更
            self.notify_config_rollback(plugin_name, timestamp)
            
            return True
        
        return False
    
    def compare_configs(self, old_config, new_config):
        """比较配置差异"""
        changes = []
        
        # 检查新增和修改的配置
        for key, value in new_config.items():
            if key not in old_config:
                changes.append({
                    'key': key,
                    'old_value': None,
                    'new_value': value,
                    'operation': 'add'
                })
            elif old_config[key] != value:
                changes.append({
                    'key': key,
                    'old_value': old_config[key],
                    'new_value': value,
                    'operation': 'modify'
                })
        
        # 检查删除的配置
        for key in old_config:
            if key not in new_config:
                changes.append({
                    'key': key,
                    'old_value': old_config[key],
                    'new_value': None,
                    'operation': 'delete'
                })
        
        return changes
    
    def notify_config_change(self, plugin_name, key, old_value, new_value):
        """通知配置变更"""
        callbacks = self.update_callbacks.get(plugin_name, [])
        
        for callback in callbacks:
            try:
                callback(key, old_value, new_value)
            except Exception as e:
                logger.error(f"Config callback error for {plugin_name}: {e}")
        
        # 发送系统事件
        self.event_bus.emit('config_changed', {
            'plugin': plugin_name,
            'key': key,
            'old_value': old_value,
            'new_value': new_value,
            'timestamp': datetime.now()
        })
```

### 5.2 插件监控系统

```python
# src/simtradelab/plugins/monitoring/plugin_monitor.py
class PluginMonitor:
    """插件监控系统"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.monitoring_tasks = {}
        self.performance_history = defaultdict(list)
        
    def start_monitoring(self, plugin_name):
        """开始监控插件"""
        if plugin_name in self.monitoring_tasks:
            logger.warning(f"Plugin {plugin_name} already being monitored")
            return
        
        # 启动监控任务
        task = asyncio.create_task(self._monitor_plugin(plugin_name))
        self.monitoring_tasks[plugin_name] = task
        
        logger.info(f"Started monitoring plugin {plugin_name}")
    
    async def _monitor_plugin(self, plugin_name):
        """监控插件性能和状态"""
        while plugin_name in self.monitoring_tasks:
            try:
                # 收集插件指标
                metrics = self.metrics_collector.collect_plugin_metrics(plugin_name)
                
                # 记录性能历史
                self.performance_history[plugin_name].append({
                    'timestamp': datetime.now(),
                    'metrics': metrics
                })
                
                # 检查告警条件
                self._check_alerts(plugin_name, metrics)
                
                # 清理过期数据
                self._cleanup_old_metrics(plugin_name)
                
                await asyncio.sleep(10)  # 每10秒收集一次
                
            except Exception as e:
                logger.error(f"Error monitoring plugin {plugin_name}: {e}")
                await asyncio.sleep(30)  # 出错时等待更长时间
    
    def _check_alerts(self, plugin_name, metrics):
        """检查告警条件"""
        # CPU使用率告警
        if metrics.get('cpu_usage', 0) > 80:
            self.alert_manager.trigger_alert(
                'high_cpu_usage',
                f"Plugin {plugin_name} CPU usage: {metrics['cpu_usage']:.1f}%",
                severity='warning'
            )
        
        # 内存使用率告警
        if metrics.get('memory_usage', 0) > 90:
            self.alert_manager.trigger_alert(
                'high_memory_usage',
                f"Plugin {plugin_name} memory usage: {metrics['memory_usage']:.1f}%",
                severity='critical'
            )
        
        # 错误率告警
        if metrics.get('error_rate', 0) > 5:
            self.alert_manager.trigger_alert(
                'high_error_rate',
                f"Plugin {plugin_name} error rate: {metrics['error_rate']:.1f}%",
                severity='warning'
            )
        
        # 响应时间告警
        if metrics.get('avg_response_time', 0) > 1000:
            self.alert_manager.trigger_alert(
                'slow_response',
                f"Plugin {plugin_name} slow response: {metrics['avg_response_time']:.0f}ms",
                severity='warning'
            )
    
    def get_plugin_metrics(self, plugin_name, time_range='1h'):
        """获取插件指标"""
        if plugin_name not in self.performance_history:
            return None
        
        history = self.performance_history[plugin_name]
        
        # 根据时间范围过滤
        cutoff_time = datetime.now() - self._parse_time_range(time_range)
        filtered_history = [h for h in history if h['timestamp'] >= cutoff_time]
        
        return {
            'plugin_name': plugin_name,
            'time_range': time_range,
            'data_points': len(filtered_history),
            'metrics': filtered_history
        }
    
    def generate_monitoring_report(self, plugin_names=None, time_range='24h'):
        """生成监控报告"""
        if plugin_names is None:
            plugin_names = list(self.performance_history.keys())
        
        report = {
            'timestamp': datetime.now(),
            'time_range': time_range,
            'plugins': {}
        }
        
        for plugin_name in plugin_names:
            metrics = self.get_plugin_metrics(plugin_name, time_range)
            if metrics:
                # 计算统计信息
                stats = self._calculate_metrics_stats(metrics['metrics'])
                report['plugins'][plugin_name] = {
                    'data_points': metrics['data_points'],
                    'statistics': stats,
                    'alerts': self.alert_manager.get_plugin_alerts(plugin_name)
                }
        
        return report
    
    def _calculate_metrics_stats(self, metrics_data):
        """计算指标统计信息"""
        if not metrics_data:
            return {}
        
        stats = {}
        
        # 计算各指标的统计信息
        metric_keys = ['cpu_usage', 'memory_usage', 'response_time', 'error_rate']
        
        for key in metric_keys:
            values = [m['metrics'].get(key, 0) for m in metrics_data]
            if values:
                stats[key] = {
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'std': self._calculate_std(values)
                }
        
        return stats
    
    def _cleanup_old_metrics(self, plugin_name):
        """清理过期指标数据"""
        if plugin_name not in self.performance_history:
            return
        
        # 只保留最近24小时的数据
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        self.performance_history[plugin_name] = [
            h for h in self.performance_history[plugin_name]
            if h['timestamp'] >= cutoff_time
        ]
    
    def _parse_time_range(self, time_range):
        """解析时间范围"""
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
            return timedelta(hours=hours)
        elif time_range.endswith('d'):
            days = int(time_range[:-1])
            return timedelta(days=days)
        elif time_range.endswith('m'):
            minutes = int(time_range[:-1])
            return timedelta(minutes=minutes)
        else:
            return timedelta(hours=1)  # 默认1小时
```

### 5.3 告警管理器

```python
# src/simtradelab/plugins/monitoring/alert_manager.py
class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.alert_rules = {}
        self.active_alerts = {}
        self.alert_history = []
        self.notification_channels = {}
        
    def add_alert_rule(self, rule_name, rule_config):
        """添加告警规则"""
        self.alert_rules[rule_name] = {
            'condition': rule_config['condition'],
            'threshold': rule_config['threshold'],
            'duration': rule_config.get('duration', 0),
            'severity': rule_config.get('severity', 'warning'),
            'notification_channels': rule_config.get('notification_channels', ['default'])
        }
        
        logger.info(f"Added alert rule: {rule_name}")
    
    def trigger_alert(self, alert_type, message, severity='warning', plugin_name=None):
        """触发告警"""
        alert_id = f"{alert_type}_{plugin_name}_{int(time.time())}"
        
        alert = {
            'id': alert_id,
            'type': alert_type,
            'message': message,
            'severity': severity,
            'plugin_name': plugin_name,
            'timestamp': datetime.now(),
            'status': 'active'
        }
        
        # 记录活跃告警
        self.active_alerts[alert_id] = alert
        
        # 记录告警历史
        self.alert_history.append(alert)
        
        # 发送通知
        self._send_alert_notification(alert)
        
        logger.warning(f"Alert triggered: {alert_type} - {message}")
        
        return alert_id
    
    def resolve_alert(self, alert_id):
        """解决告警"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id]['status'] = 'resolved'
            self.active_alerts[alert_id]['resolved_at'] = datetime.now()
            
            # 从活跃告警中移除
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert resolved: {alert_id}")
            return True
        
        return False
    
    def get_active_alerts(self, plugin_name=None):
        """获取活跃告警"""
        if plugin_name:
            return {
                k: v for k, v in self.active_alerts.items()
                if v.get('plugin_name') == plugin_name
            }
        
        return self.active_alerts
    
    def get_plugin_alerts(self, plugin_name):
        """获取特定插件的告警"""
        plugin_alerts = []
        
        for alert in self.alert_history:
            if alert.get('plugin_name') == plugin_name:
                plugin_alerts.append(alert)
        
        # 返回最近的告警
        return plugin_alerts[-10:]
    
    def _send_alert_notification(self, alert):
        """发送告警通知"""
        rule_name = alert['type']
        rule = self.alert_rules.get(rule_name, {})
        
        channels = rule.get('notification_channels', ['default'])
        
        for channel in channels:
            if channel in self.notification_channels:
                try:
                    self.notification_channels[channel].send_alert(alert)
                except Exception as e:
                    logger.error(f"Failed to send alert to {channel}: {e}")
    
    def add_notification_channel(self, channel_name, channel_config):
        """添加通知渠道"""
        if channel_config['type'] == 'email':
            channel = EmailNotificationChannel(channel_config)
        elif channel_config['type'] == 'slack':
            channel = SlackNotificationChannel(channel_config)
        elif channel_config['type'] == 'webhook':
            channel = WebhookNotificationChannel(channel_config)
        else:
            channel = DefaultNotificationChannel(channel_config)
        
        self.notification_channels[channel_name] = channel
        logger.info(f"Added notification channel: {channel_name}")
```

### 5.4 指标收集器

```python
# src/simtradelab/plugins/monitoring/metrics_collector.py
class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.plugin_monitors = {}
        
    def collect_plugin_metrics(self, plugin_name):
        """收集插件指标"""
        if plugin_name not in self.plugin_monitors:
            self.plugin_monitors[plugin_name] = PluginMetricsMonitor(plugin_name)
        
        monitor = self.plugin_monitors[plugin_name]
        
        metrics = {
            'plugin_name': plugin_name,
            'timestamp': datetime.now(),
            
            # 系统资源指标
            'cpu_usage': monitor.get_cpu_usage(),
            'memory_usage': monitor.get_memory_usage(),
            'disk_usage': monitor.get_disk_usage(),
            'network_usage': monitor.get_network_usage(),
            
            # 性能指标
            'response_time': monitor.get_avg_response_time(),
            'throughput': monitor.get_throughput(),
            'error_rate': monitor.get_error_rate(),
            'success_rate': monitor.get_success_rate(),
            
            # 业务指标
            'active_connections': monitor.get_active_connections(),
            'queue_size': monitor.get_queue_size(),
            'cache_hit_rate': monitor.get_cache_hit_rate(),
            
            # 自定义指标
            'custom_metrics': monitor.get_custom_metrics()
        }
        
        return metrics
    
    def collect_system_metrics(self):
        """收集系统指标"""
        return {
            'timestamp': datetime.now(),
            'cpu_usage': self.system_monitor.get_cpu_usage(),
            'memory_usage': self.system_monitor.get_memory_usage(),
            'disk_usage': self.system_monitor.get_disk_usage(),
            'network_usage': self.system_monitor.get_network_usage(),
            'load_average': self.system_monitor.get_load_average(),
            'uptime': self.system_monitor.get_uptime()
        }

class PluginMetricsMonitor:
    """插件指标监控器"""
    
    def __init__(self, plugin_name):
        self.plugin_name = plugin_name
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        
    def record_request(self, response_time, success=True):
        """记录请求"""
        self.request_count += 1
        self.response_times.append(response_time)
        
        if not success:
            self.error_count += 1
        
        # 只保留最近1000个响应时间
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def get_avg_response_time(self):
        """获取平均响应时间"""
        if not self.response_times:
            return 0
        
        return sum(self.response_times) / len(self.response_times)
    
    def get_throughput(self):
        """获取吞吐量（请求/秒）"""
        elapsed_time = time.time() - self.start_time
        if elapsed_time == 0:
            return 0
        
        return self.request_count / elapsed_time
    
    def get_error_rate(self):
        """获取错误率"""
        if self.request_count == 0:
            return 0
        
        return (self.error_count / self.request_count) * 100
    
    def get_success_rate(self):
        """获取成功率"""
        return 100 - self.get_error_rate()
    
    def get_cpu_usage(self):
        """获取CPU使用率"""
        # 实现CPU使用率监控
        try:
            import psutil
            process = psutil.Process()
            return process.cpu_percent()
        except ImportError:
            return 0
    
    def get_memory_usage(self):
        """获取内存使用率"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return (memory_info.rss / psutil.virtual_memory().total) * 100
        except ImportError:
            return 0
```

## 6. 数据系统优化（冷热数据分离、分布式缓存）

### 6.1 智能数据分层管理

```python
# src/simtradelab/plugins/data/cold_hot_data_manager.py
class ColdHotDataManager:
    """冷热数据管理器 - 智能数据分层存储"""
    
    def __init__(self, config):
        self.config = config
        self.hot_storage = HotDataStorage(config['hot_storage'])
        self.warm_storage = WarmDataStorage(config['warm_storage'])
        self.cold_storage = ColdDataStorage(config['cold_storage'])
        self.access_tracker = DataAccessTracker()
        self.migration_scheduler = DataMigrationScheduler()
        
    def get_data(self, request: DataRequest) -> pd.DataFrame:
        """智能数据获取 - 根据访问模式选择最优存储层"""
        # 记录数据访问
        self.access_tracker.record_access(request)
        
        # 尝试从热存储获取
        if self.hot_storage.has_data(request):
            return self.hot_storage.get_data(request)
        
        # 尝试从温存储获取
        if self.warm_storage.has_data(request):
            data = self.warm_storage.get_data(request)
            
            # 如果频繁访问，提升到热存储
            if self.access_tracker.is_hot_data(request):
                self.hot_storage.store_data(request, data)
            
            return data
        
        # 从冷存储获取
        if self.cold_storage.has_data(request):
            data = self.cold_storage.get_data(request)
            
            # 根据访问频率决定存储层级
            if self.access_tracker.is_hot_data(request):
                self.hot_storage.store_data(request, data)
            elif self.access_tracker.is_warm_data(request):
                self.warm_storage.store_data(request, data)
            
            return data
        
        # 数据不存在，从远程获取
        data = self._fetch_from_remote(request)
        
        # 根据数据特征选择存储层
        if self._is_frequently_accessed(request):
            self.hot_storage.store_data(request, data)
        elif self._is_occasionally_accessed(request):
            self.warm_storage.store_data(request, data)
        else:
            self.cold_storage.store_data(request, data)
        
        return data
    
    def store_data(self, request: DataRequest, data: pd.DataFrame):
        """存储数据到适当的存储层"""
        # 根据数据特征和访问模式选择存储层
        if self._should_store_in_hot(request, data):
            self.hot_storage.store_data(request, data)
        elif self._should_store_in_warm(request, data):
            self.warm_storage.store_data(request, data)
        else:
            self.cold_storage.store_data(request, data)
    
    def migrate_data(self):
        """数据迁移 - 根据访问模式在存储层间移动数据"""
        # 从热存储迁移到温存储
        hot_data_keys = self.hot_storage.get_all_keys()
        for key in hot_data_keys:
            if not self.access_tracker.is_hot_data_by_key(key):
                data = self.hot_storage.get_data_by_key(key)
                self.warm_storage.store_data_by_key(key, data)
                self.hot_storage.remove_data_by_key(key)
        
        # 从温存储迁移到冷存储
        warm_data_keys = self.warm_storage.get_all_keys()
        for key in warm_data_keys:
            if not self.access_tracker.is_warm_data_by_key(key):
                data = self.warm_storage.get_data_by_key(key)
                self.cold_storage.store_data_by_key(key, data)
                self.warm_storage.remove_data_by_key(key)
        
        # 从冷存储清理过期数据
        self.cold_storage.cleanup_expired_data()
    
    def get_storage_stats(self):
        """获取存储统计信息"""
        return {
            'hot_storage': self.hot_storage.get_stats(),
            'warm_storage': self.warm_storage.get_stats(),
            'cold_storage': self.cold_storage.get_stats(),
            'access_stats': self.access_tracker.get_stats()
        }
    
    def _should_store_in_hot(self, request, data):
        """判断是否应该存储在热存储"""
        # 最近数据
        if self._is_recent_data(request):
            return True
        
        # 小数据量
        if len(data) < 10000:
            return True
        
        # 频繁访问的数据
        if self.access_tracker.is_hot_data(request):
            return True
        
        return False
    
    def _should_store_in_warm(self, request, data):
        """判断是否应该存储在温存储"""
        # 中等频率访问
        if self.access_tracker.is_warm_data(request):
            return True
        
        # 中等大小数据
        if 10000 <= len(data) <= 100000:
            return True
        
        return False

class HotDataStorage:
    """热数据存储 - 内存 + SSD缓存"""
    
    def __init__(self, config):
        self.memory_cache = MemoryCache(config['memory_size'])
        self.ssd_cache = SSDCache(config['ssd_path'])
        self.ttl = config.get('ttl', 3600)  # 1小时TTL
        
    def get_data(self, request: DataRequest) -> pd.DataFrame:
        # 先从内存获取
        if self.memory_cache.has_data(request):
            return self.memory_cache.get_data(request)
        
        # 再从SSD获取
        if self.ssd_cache.has_data(request):
            data = self.ssd_cache.get_data(request)
            # 提升到内存缓存
            self.memory_cache.store_data(request, data)
            return data
        
        return None
    
    def store_data(self, request: DataRequest, data: pd.DataFrame):
        # 同时存储到内存和SSD
        self.memory_cache.store_data(request, data)
        self.ssd_cache.store_data(request, data)
    
    def get_stats(self):
        """获取存储统计"""
        return {
            'memory_cache': self.memory_cache.get_stats(),
            'ssd_cache': self.ssd_cache.get_stats(),
            'total_items': self.memory_cache.size() + self.ssd_cache.size()
        }

class WarmDataStorage:
    """温数据存储 - SSD + 数据库"""
    
    def __init__(self, config):
        self.ssd_cache = SSDCache(config['ssd_path'])
        self.database = Database(config['db_config'])
        self.ttl = config.get('ttl', 86400)  # 24小时TTL
        
    def get_data(self, request: DataRequest) -> pd.DataFrame:
        # 先从SSD获取
        if self.ssd_cache.has_data(request):
            return self.ssd_cache.get_data(request)
        
        # 再从数据库获取
        if self.database.has_data(request):
            data = self.database.get_data(request)
            # 提升到SSD缓存
            self.ssd_cache.store_data(request, data)
            return data
        
        return None
    
    def store_data(self, request: DataRequest, data: pd.DataFrame):
        # 存储到SSD和数据库
        self.ssd_cache.store_data(request, data)
        self.database.store_data(request, data)

class ColdDataStorage:
    """冷数据存储 - 对象存储 + 归档"""
    
    def __init__(self, config):
        self.object_storage = ObjectStorage(config['object_storage'])
        self.archive_storage = ArchiveStorage(config['archive_storage'])
        self.ttl = config.get('ttl', 31536000)  # 1年TTL
        
    def get_data(self, request: DataRequest) -> pd.DataFrame:
        # 先从对象存储获取
        if self.object_storage.has_data(request):
            return self.object_storage.get_data(request)
        
        # 再从归档存储获取
        if self.archive_storage.has_data(request):
            data = self.archive_storage.get_data(request)
            # 提升到对象存储
            self.object_storage.store_data(request, data)
            return data
        
        return None
    
    def cleanup_expired_data(self):
        """清理过期数据"""
        cutoff_time = datetime.now() - timedelta(seconds=self.ttl)
        
        # 清理对象存储中的过期数据
        self.object_storage.cleanup_before(cutoff_time)
        
        # 将对象存储中的旧数据迁移到归档存储
        old_data = self.object_storage.get_data_before(cutoff_time)
        for key, data in old_data.items():
            self.archive_storage.store_data_by_key(key, data)
            self.object_storage.remove_data_by_key(key)
```

### 6.2 分布式缓存系统

```python
# src/simtradelab/plugins/data/distributed_cache.py
class DistributedCacheManager:
    """分布式缓存管理器"""
    
    def __init__(self, config):
        self.config = config
        self.cache_nodes = self._init_cache_nodes()
        self.consistent_hash = ConsistentHash(self.cache_nodes)
        self.replication_factor = config.get('replication_factor', 2)
        self.connection_pool = ConnectionPool()
        
    def _init_cache_nodes(self):
        """初始化缓存节点"""
        nodes = []
        for node_config in self.config['nodes']:
            if node_config['type'] == 'redis':
                node = RedisNode(node_config)
            elif node_config['type'] == 'memcached':
                node = MemcachedNode(node_config)
            else:
                node = GenericCacheNode(node_config)
            
            nodes.append(node)
        
        return nodes
    
    def get_data(self, key: str) -> Any:
        """获取缓存数据"""
        # 根据一致性哈希找到对应节点
        primary_node = self.consistent_hash.get_node(key)
        
        try:
            # 尝试从主节点获取
            data = primary_node.get(key)
            if data is not None:
                return data
        except Exception as e:
            logger.warning(f"Primary node {primary_node.id} failed: {e}")
        
        # 尝试从副本节点获取
        replica_nodes = self.consistent_hash.get_replica_nodes(key, self.replication_factor)
        
        for node in replica_nodes:
            try:
                data = node.get(key)
                if data is not None:
                    # 异步修复主节点
                    asyncio.create_task(self._repair_primary_node(primary_node, key, data))
                    return data
            except Exception as e:
                logger.warning(f"Replica node {node.id} failed: {e}")
        
        return None
    
    def set_data(self, key: str, value: Any, ttl: int = None):
        """设置缓存数据"""
        # 获取主节点和副本节点
        primary_node = self.consistent_hash.get_node(key)
        replica_nodes = self.consistent_hash.get_replica_nodes(key, self.replication_factor)
        
        # 写入主节点
        success_count = 0
        try:
            primary_node.set(key, value, ttl)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to write to primary node {primary_node.id}: {e}")
        
        # 写入副本节点
        for node in replica_nodes:
            try:
                node.set(key, value, ttl)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to write to replica node {node.id}: {e}")
        
        # 检查写入成功率
        total_nodes = 1 + len(replica_nodes)
        if success_count < total_nodes / 2:
            logger.error(f"Write failed for key {key}, only {success_count}/{total_nodes} nodes succeeded")
            return False
        
        return True
    
    def delete_data(self, key: str):
        """删除缓存数据"""
        # 获取所有相关节点
        primary_node = self.consistent_hash.get_node(key)
        replica_nodes = self.consistent_hash.get_replica_nodes(key, self.replication_factor)
        
        all_nodes = [primary_node] + replica_nodes
        
        # 从所有节点删除
        for node in all_nodes:
            try:
                node.delete(key)
            except Exception as e:
                logger.error(f"Failed to delete from node {node.id}: {e}")
    
    def get_cache_stats(self):
        """获取缓存统计信息"""
        stats = {
            'total_nodes': len(self.cache_nodes),
            'healthy_nodes': 0,
            'total_memory': 0,
            'used_memory': 0,
            'hit_rate': 0,
            'node_stats': []
        }
        
        for node in self.cache_nodes:
            try:
                node_stats = node.get_stats()
                stats['node_stats'].append(node_stats)
                
                if node_stats['healthy']:
                    stats['healthy_nodes'] += 1
                    stats['total_memory'] += node_stats['total_memory']
                    stats['used_memory'] += node_stats['used_memory']
                    stats['hit_rate'] += node_stats['hit_rate']
            except Exception as e:
                logger.error(f"Failed to get stats from node {node.id}: {e}")
        
        if stats['healthy_nodes'] > 0:
            stats['hit_rate'] /= stats['healthy_nodes']
        
        return stats
    
    def scale_cache_cluster(self, new_nodes_config):
        """动态扩展缓存集群"""
        # 添加新节点
        new_nodes = []
        for node_config in new_nodes_config:
            if node_config['type'] == 'redis':
                node = RedisNode(node_config)
            elif node_config['type'] == 'memcached':
                node = MemcachedNode(node_config)
            else:
                node = GenericCacheNode(node_config)
            
            new_nodes.append(node)
        
        # 更新一致性哈希环
        old_hash = self.consistent_hash
        self.cache_nodes.extend(new_nodes)
        self.consistent_hash = ConsistentHash(self.cache_nodes)
        
        # 数据迁移
        self._migrate_data(old_hash, self.consistent_hash)
        
        logger.info(f"Scaled cache cluster, added {len(new_nodes)} nodes")
    
    async def _repair_primary_node(self, primary_node, key, value):
        """修复主节点数据"""
        try:
            await primary_node.set_async(key, value)
            logger.info(f"Repaired primary node {primary_node.id} for key {key}")
        except Exception as e:
            logger.error(f"Failed to repair primary node {primary_node.id}: {e}")
    
    def _migrate_data(self, old_hash, new_hash):
        """数据迁移"""
        # 这里实现数据迁移逻辑
        # 对于每个键，检查是否需要迁移到新节点
        pass

class ConsistentHash:
    """一致性哈希算法"""
    
    def __init__(self, nodes, virtual_nodes=150):
        self.nodes = nodes
        self.virtual_nodes = virtual_nodes
        self.ring = {}
        self.sorted_keys = []
        
        self._build_ring()
    
    def _build_ring(self):
        """构建哈希环"""
        self.ring = {}
        
        for node in self.nodes:
            for i in range(self.virtual_nodes):
                key = self._hash(f"{node.id}:{i}")
                self.ring[key] = node
        
        self.sorted_keys = sorted(self.ring.keys())
    
    def _hash(self, key):
        """哈希函数"""
        import hashlib
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def get_node(self, key):
        """获取键对应的节点"""
        if not self.ring:
            return None
        
        key_hash = self._hash(key)
        
        # 查找第一个大于等于key_hash的节点
        for ring_key in self.sorted_keys:
            if ring_key >= key_hash:
                return self.ring[ring_key]
        
        # 如果没找到，返回第一个节点（环形结构）
        return self.ring[self.sorted_keys[0]]
    
    def get_replica_nodes(self, key, replica_count):
        """获取副本节点"""
        if not self.ring or replica_count <= 0:
            return []
        
        key_hash = self._hash(key)
        replica_nodes = []
        
        # 从主节点开始，按顺序找到副本节点
        start_index = 0
        for i, ring_key in enumerate(self.sorted_keys):
            if ring_key >= key_hash:
                start_index = i
                break
        
        # 跳过主节点，找到不同的副本节点
        added_nodes = set()
        current_index = start_index
        
        while len(replica_nodes) < replica_count and len(added_nodes) < len(self.nodes):
            current_index = (current_index + 1) % len(self.sorted_keys)
            ring_key = self.sorted_keys[current_index]
            node = self.ring[ring_key]
            
            if node.id not in added_nodes:
                replica_nodes.append(node)
                added_nodes.add(node.id)
        
        return replica_nodes

class RedisNode:
    """Redis缓存节点"""
    
    def __init__(self, config):
        self.id = config['id']
        self.host = config['host']
        self.port = config['port']
        self.password = config.get('password')
        self.db = config.get('db', 0)
        
        import redis
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            password=self.password,
            db=self.db,
            decode_responses=True
        )
    
    def get(self, key):
        """获取数据"""
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    def set(self, key, value, ttl=None):
        """设置数据"""
        try:
            data = json.dumps(value)
            if ttl:
                self.client.setex(key, ttl, data)
            else:
                self.client.set(key, data)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    def delete(self, key):
        """删除数据"""
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    def get_stats(self):
        """获取节点统计"""
        try:
            info = self.client.info('memory')
            return {
                'id': self.id,
                'healthy': True,
                'total_memory': info.get('maxmemory', 0),
                'used_memory': info.get('used_memory', 0),
                'hit_rate': info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {
                'id': self.id,
                'healthy': False,
                'total_memory': 0,
                'used_memory': 0,
                'hit_rate': 0
            }
    
    async def set_async(self, key, value, ttl=None):
        """异步设置数据"""
        return self.set(key, value, ttl)
```

### 6.3 数据访问追踪器

```python
# src/simtradelab/plugins/data/access_tracker.py
class DataAccessTracker:
    """数据访问追踪器"""
    
    def __init__(self):
        self.access_history = defaultdict(list)
        self.access_stats = defaultdict(dict)
        self.hot_threshold = 10  # 1小时内访问10次认为是热数据
        self.warm_threshold = 5   # 1天内访问5次认为是温数据
        
    def record_access(self, request: DataRequest):
        """记录数据访问"""
        key = self._generate_key(request)
        timestamp = datetime.now()
        
        self.access_history[key].append(timestamp)
        
        # 清理过期的访问记录
        self._cleanup_old_access(key)
        
        # 更新访问统计
        self._update_access_stats(key)
    
    def is_hot_data(self, request: DataRequest):
        """判断是否为热数据"""
        key = self._generate_key(request)
        return self.is_hot_data_by_key(key)
    
    def is_hot_data_by_key(self, key):
        """根据键判断是否为热数据"""
        # 1小时内的访问次数
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_access = [
            t for t in self.access_history[key]
            if t >= one_hour_ago
        ]
        
        return len(recent_access) >= self.hot_threshold
    
    def is_warm_data(self, request: DataRequest):
        """判断是否为温数据"""
        key = self._generate_key(request)
        return self.is_warm_data_by_key(key)
    
    def is_warm_data_by_key(self, key):
        """根据键判断是否为温数据"""
        # 1天内的访问次数
        one_day_ago = datetime.now() - timedelta(days=1)
        recent_access = [
            t for t in self.access_history[key]
            if t >= one_day_ago
        ]
        
        return len(recent_access) >= self.warm_threshold
    
    def get_access_pattern(self, request: DataRequest):
        """获取访问模式"""
        key = self._generate_key(request)
        
        if key not in self.access_history:
            return 'new'
        
        if self.is_hot_data_by_key(key):
            return 'hot'
        elif self.is_warm_data_by_key(key):
            return 'warm'
        else:
            return 'cold'
    
    def get_stats(self):
        """获取访问统计"""
        hot_count = 0
        warm_count = 0
        cold_count = 0
        
        for key in self.access_history:
            if self.is_hot_data_by_key(key):
                hot_count += 1
            elif self.is_warm_data_by_key(key):
                warm_count += 1
            else:
                cold_count += 1
        
        return {
            'hot_data_count': hot_count,
            'warm_data_count': warm_count,
            'cold_data_count': cold_count,
            'total_keys': len(self.access_history)
        }
    
    def _generate_key(self, request: DataRequest):
        """生成请求键"""
        # 根据请求参数生成唯一键
        key_parts = [
            request.security if hasattr(request, 'security') else '',
            request.start_date if hasattr(request, 'start_date') else '',
            request.end_date if hasattr(request, 'end_date') else '',
            request.frequency if hasattr(request, 'frequency') else ''
        ]
        
        return ':'.join(str(part) for part in key_parts)
    
    def _cleanup_old_access(self, key):
        """清理过期的访问记录"""
        # 只保留最近7天的访问记录
        one_week_ago = datetime.now() - timedelta(days=7)
        
        self.access_history[key] = [
            t for t in self.access_history[key]
            if t >= one_week_ago
        ]
        
        # 如果没有访问记录，删除键
        if not self.access_history[key]:
            del self.access_history[key]
    
    def _update_access_stats(self, key):
        """更新访问统计"""
        access_times = self.access_history[key]
        
        if not access_times:
            return
        
        # 计算访问频率
        if len(access_times) >= 2:
            time_diffs = [
                (access_times[i] - access_times[i-1]).total_seconds()
                for i in range(1, len(access_times))
            ]
            avg_interval = sum(time_diffs) / len(time_diffs)
        else:
            avg_interval = 0
        
        self.access_stats[key] = {
            'total_access': len(access_times),
            'first_access': access_times[0],
            'last_access': access_times[-1],
            'avg_interval': avg_interval,
            'pattern': self.get_access_pattern_by_key(key)
        }
    
    def get_access_pattern_by_key(self, key):
        """根据键获取访问模式"""
        if self.is_hot_data_by_key(key):
            return 'hot'
        elif self.is_warm_data_by_key(key):
            return 'warm'
        else:
            return 'cold'
```

## 7. 多策略协同和动态权重调整

### 7.1 多策略协调管理器

```python
# src/simtradelab/plugins/strategy/multi_strategy_coordinator.py
class MultiStrategyCoordinator:
    """多策略协调管理器 - 支持动态权重调整"""
    
    def __init__(self, config):
        self.strategies = {}
        self.weight_manager = DynamicWeightManager(config.get('weight_config', {}))
        self.performance_tracker = StrategyPerformanceTracker()
        self.risk_manager = PortfolioRiskManager(config.get('risk_config', {}))
        self.rebalance_frequency = config.get('rebalance_frequency', 'daily')
        self.allocation_method = config.get('allocation_method', 'adaptive')
        
    def register_strategy(self, strategy_name, strategy_module, initial_weight=None):
        """注册策略"""
        self.strategies[strategy_name] = {
            'module': strategy_module,
            'weight': initial_weight or (1.0 / len(self.strategies) if self.strategies else 1.0),
            'performance': StrategyPerformance(),
            'positions': {},
            'orders': [],
            'status': 'active'
        }
        
        # 重新计算权重
        if initial_weight is None:
            self._rebalance_weights()
        
        logger.info(f"Strategy {strategy_name} registered with weight {self.strategies[strategy_name]['weight']}")
    
    def coordinate_strategies(self, context, data):
        """协调多个策略"""
        strategy_signals = {}
        
        # 1. 执行各个策略并收集信号
        for strategy_name, strategy_info in self.strategies.items():
            if strategy_info['status'] != 'active':
                continue
                
            try:
                # 执行策略
                signal = self._execute_strategy(strategy_name, strategy_info, context, data)
                strategy_signals[strategy_name] = signal
                
                # 记录性能数据
                self.performance_tracker.record_strategy_performance(
                    strategy_name, signal, context.portfolio
                )
                
            except Exception as e:
                logger.error(f"Strategy {strategy_name} execution failed: {e}")
                # 暂停有问题的策略
                strategy_info['status'] = 'error'
                continue
        
        # 2. 动态调整权重
        if self.allocation_method == 'adaptive':
            self.weight_manager.update_weights(self.strategies, self.performance_tracker)
        
        # 3. 计算组合信号
        combined_signal = self._combine_signals(strategy_signals)
        
        # 4. 风险控制
        risk_adjusted_signal = self.risk_manager.apply_risk_control(combined_signal, context)
        
        # 5. 执行交易
        self._execute_combined_trades(risk_adjusted_signal, context)
        
        # 6. 记录组合性能
        self.performance_tracker.record_portfolio_performance(context.portfolio)
        
        return risk_adjusted_signal
    
    def _execute_strategy(self, strategy_name, strategy_info, context, data):
        """执行单个策略"""
        strategy_module = strategy_info['module']
        
        # 创建策略专用的上下文
        strategy_context = self._create_strategy_context(context, strategy_name)
        
        # 执行策略的handle_data函数
        if hasattr(strategy_module, 'handle_data'):
            strategy_module.handle_data(strategy_context, data)
        
        # 收集策略信号
        signal = {
            'strategy_name': strategy_name,
            'positions': strategy_context.target_positions,
            'orders': strategy_context.pending_orders,
            'cash_usage': strategy_context.cash_usage,
            'confidence': strategy_context.confidence if hasattr(strategy_context, 'confidence') else 0.5
        }
        
        return signal
    
    def _combine_signals(self, strategy_signals):
        """组合多个策略信号"""
        combined_positions = {}
        total_weight = sum(info['weight'] for info in self.strategies.values() if info['status'] == 'active')
        
        for strategy_name, signal in strategy_signals.items():
            strategy_weight = self.strategies[strategy_name]['weight']
            normalized_weight = strategy_weight / total_weight if total_weight > 0 else 0
            
            # 加权合并持仓
            for security, target_amount in signal.get('positions', {}).items():
                if security not in combined_positions:
                    combined_positions[security] = 0
                
                combined_positions[security] += target_amount * normalized_weight
        
        return {
            'positions': combined_positions,
            'strategy_weights': {name: info['weight'] for name, info in self.strategies.items()},
            'active_strategies': list(strategy_signals.keys())
        }
    
    def _execute_combined_trades(self, combined_signal, context):
        """执行组合交易"""
        target_positions = combined_signal['positions']
        
        # 获取当前持仓
        current_positions = {pos.security: pos.amount for pos in context.portfolio.positions.values()}
        
        # 计算需要调整的持仓
        for security, target_amount in target_positions.items():
            current_amount = current_positions.get(security, 0)
            trade_amount = target_amount - current_amount
            
            if abs(trade_amount) > 0.01:  # 避免微小调整
                # 执行交易
                order_id = order(security, trade_amount)
                if order_id:
                    logger.info(f"Portfolio rebalance: {security} {trade_amount:+.0f} shares")
        
        # 清理不再需要的持仓
        for security, current_amount in current_positions.items():
            if security not in target_positions and current_amount != 0:
                order_id = order(security, -current_amount)
                if order_id:
                    logger.info(f"Portfolio cleanup: {security} {-current_amount:+.0f} shares")
    
    def _rebalance_weights(self):
        """重新平衡权重"""
        active_strategies = [name for name, info in self.strategies.items() if info['status'] == 'active']
        
        if not active_strategies:
            return
        
        # 均等分配权重
        equal_weight = 1.0 / len(active_strategies)
        
        for strategy_name in active_strategies:
            self.strategies[strategy_name]['weight'] = equal_weight
        
        # 非活跃策略权重设为0
        for strategy_name, info in self.strategies.items():
            if info['status'] != 'active':
                info['weight'] = 0
    
    def get_strategy_performance(self, strategy_name=None):
        """获取策略性能"""
        if strategy_name:
            return self.performance_tracker.get_strategy_performance(strategy_name)
        else:
            return self.performance_tracker.get_all_strategies_performance()
    
    def update_strategy_status(self, strategy_name, status):
        """更新策略状态"""
        if strategy_name in self.strategies:
            old_status = self.strategies[strategy_name]['status']
            self.strategies[strategy_name]['status'] = status
            
            logger.info(f"Strategy {strategy_name} status changed: {old_status} -> {status}")
            
            # 重新平衡权重
            if status in ['active', 'inactive', 'error']:
                self._rebalance_weights()
    
    def _create_strategy_context(self, global_context, strategy_name):
        """创建策略专用上下文"""
        strategy_context = copy.deepcopy(global_context)
        strategy_context.strategy_name = strategy_name
        strategy_context.target_positions = {}
        strategy_context.pending_orders = []
        strategy_context.cash_usage = 0
        
        return strategy_context
```

### 7.2 动态权重管理器

```python
# src/simtradelab/plugins/strategy/dynamic_weight_manager.py
class DynamicWeightManager:
    """动态权重管理器"""
    
    def __init__(self, config):
        self.config = config
        self.adjustment_method = config.get('method', 'performance_based')
        self.lookback_period = config.get('lookback_period', 30)  # 30天
        self.min_weight = config.get('min_weight', 0.05)  # 最小权重5%
        self.max_weight = config.get('max_weight', 0.50)  # 最大权重50%
        self.rebalance_threshold = config.get('rebalance_threshold', 0.05)  # 5%阈值
        self.weight_history = defaultdict(list)
        
    def update_weights(self, strategies, performance_tracker):
        """更新策略权重"""
        if self.adjustment_method == 'performance_based':
            new_weights = self._calculate_performance_based_weights(strategies, performance_tracker)
        elif self.adjustment_method == 'risk_parity':
            new_weights = self._calculate_risk_parity_weights(strategies, performance_tracker)
        elif self.adjustment_method == 'sharpe_ratio':
            new_weights = self._calculate_sharpe_ratio_weights(strategies, performance_tracker)
        elif self.adjustment_method == 'kelly_criterion':
            new_weights = self._calculate_kelly_weights(strategies, performance_tracker)
        else:
            new_weights = self._calculate_equal_weights(strategies)
        
        # 应用权重约束
        new_weights = self._apply_weight_constraints(new_weights)
        
        # 检查是否需要重新平衡
        if self._should_rebalance(strategies, new_weights):
            self._apply_new_weights(strategies, new_weights)
            logger.info(f"Strategy weights updated: {new_weights}")
    
    def _calculate_performance_based_weights(self, strategies, performance_tracker):
        """基于性能的权重计算"""
        weights = {}
        active_strategies = [name for name, info in strategies.items() if info['status'] == 'active']
        
        if not active_strategies:
            return weights
        
        # 获取策略性能数据
        performance_scores = {}
        for strategy_name in active_strategies:
            perf_data = performance_tracker.get_strategy_performance(strategy_name)
            
            if perf_data and len(perf_data) >= self.lookback_period:
                # 计算综合性能得分
                recent_returns = perf_data[-self.lookback_period:]
                avg_return = np.mean(recent_returns)
                volatility = np.std(recent_returns)
                sharpe_ratio = avg_return / volatility if volatility > 0 else 0
                
                # 综合得分：收益 * 0.4 + 夏普比率 * 0.4 + 稳定性 * 0.2
                stability_score = 1 / (1 + volatility)  # 波动率越小，稳定性越高
                performance_scores[strategy_name] = avg_return * 0.4 + sharpe_ratio * 0.4 + stability_score * 0.2
            else:
                # 新策略或数据不足，给予平均权重
                performance_scores[strategy_name] = 0.5
        
        # 归一化性能得分
        min_score = min(performance_scores.values())
        max_score = max(performance_scores.values())
        
        if max_score > min_score:
            normalized_scores = {
                name: (score - min_score) / (max_score - min_score) + 0.1  # 加0.1避免权重为0
                for name, score in performance_scores.items()
            }
        else:
            normalized_scores = {name: 1.0 for name in performance_scores}
        
        # 计算权重
        total_score = sum(normalized_scores.values())
        weights = {name: score / total_score for name, score in normalized_scores.items()}
        
        return weights
    
    def _calculate_risk_parity_weights(self, strategies, performance_tracker):
        """风险平价权重计算"""
        weights = {}
        active_strategies = [name for name, info in strategies.items() if info['status'] == 'active']
        
        if not active_strategies:
            return weights
        
        # 计算各策略的风险（用波动率衡量）
        risk_measures = {}
        for strategy_name in active_strategies:
            perf_data = performance_tracker.get_strategy_performance(strategy_name)
            
            if perf_data and len(perf_data) >= self.lookback_period:
                recent_returns = perf_data[-self.lookback_period:]
                volatility = np.std(recent_returns)
                risk_measures[strategy_name] = volatility if volatility > 0 else 0.01
            else:
                risk_measures[strategy_name] = 0.01  # 默认风险
        
        # 风险平价：权重与风险成反比
        inverse_risks = {name: 1.0 / risk for name, risk in risk_measures.items()}
        total_inverse_risk = sum(inverse_risks.values())
        
        weights = {name: inv_risk / total_inverse_risk for name, inv_risk in inverse_risks.items()}
        
        return weights
    
    def _calculate_sharpe_ratio_weights(self, strategies, performance_tracker):
        """基于夏普比率的权重计算"""
        weights = {}
        active_strategies = [name for name, info in strategies.items() if info['status'] == 'active']
        
        if not active_strategies:
            return weights
        
        # 计算各策略的夏普比率
        sharpe_ratios = {}
        for strategy_name in active_strategies:
            perf_data = performance_tracker.get_strategy_performance(strategy_name)
            
            if perf_data and len(perf_data) >= self.lookback_period:
                recent_returns = perf_data[-self.lookback_period:]
                avg_return = np.mean(recent_returns)
                volatility = np.std(recent_returns)
                sharpe_ratio = avg_return / volatility if volatility > 0 else 0
                sharpe_ratios[strategy_name] = max(sharpe_ratio, 0.1)  # 最小值0.1
            else:
                sharpe_ratios[strategy_name] = 0.1
        
        # 按夏普比率分配权重
        total_sharpe = sum(sharpe_ratios.values())
        weights = {name: sharpe / total_sharpe for name, sharpe in sharpe_ratios.items()}
        
        return weights
    
    def _calculate_kelly_weights(self, strategies, performance_tracker):
        """Kelly准则权重计算"""
        weights = {}
        active_strategies = [name for name, info in strategies.items() if info['status'] == 'active']
        
        if not active_strategies:
            return weights
        
        # 计算Kelly权重
        kelly_weights = {}
        for strategy_name in active_strategies:
            perf_data = performance_tracker.get_strategy_performance(strategy_name)
            
            if perf_data and len(perf_data) >= self.lookback_period:
                recent_returns = perf_data[-self.lookback_period:]
                avg_return = np.mean(recent_returns)
                variance = np.var(recent_returns)
                
                # Kelly公式：f = μ / σ²
                if variance > 0:
                    kelly_weight = avg_return / variance
                    kelly_weights[strategy_name] = max(kelly_weight, 0.01)  # 最小值0.01
                else:
                    kelly_weights[strategy_name] = 0.01
            else:
                kelly_weights[strategy_name] = 0.01
        
        # 归一化Kelly权重
        total_kelly = sum(kelly_weights.values())
        weights = {name: kelly / total_kelly for name, kelly in kelly_weights.items()}
        
        return weights
    
    def _calculate_equal_weights(self, strategies):
        """等权重计算"""
        active_strategies = [name for name, info in strategies.items() if info['status'] == 'active']
        
        if not active_strategies:
            return {}
        
        equal_weight = 1.0 / len(active_strategies)
        return {name: equal_weight for name in active_strategies}
    
    def _apply_weight_constraints(self, weights):
        """应用权重约束"""
        # 应用最小和最大权重限制
        constrained_weights = {}
        total_adjustment = 0
        
        for name, weight in weights.items():
            if weight < self.min_weight:
                constrained_weights[name] = self.min_weight
                total_adjustment += self.min_weight - weight
            elif weight > self.max_weight:
                constrained_weights[name] = self.max_weight
                total_adjustment += self.max_weight - weight
            else:
                constrained_weights[name] = weight
        
        # 如果有调整，重新归一化
        if abs(total_adjustment) > 1e-6:
            total_weight = sum(constrained_weights.values())
            constrained_weights = {name: w / total_weight for name, w in constrained_weights.items()}
        
        return constrained_weights
    
    def _should_rebalance(self, strategies, new_weights):
        """检查是否需要重新平衡"""
        for strategy_name, new_weight in new_weights.items():
            current_weight = strategies[strategy_name]['weight']
            
            if abs(new_weight - current_weight) > self.rebalance_threshold:
                return True
        
        return False
    
    def _apply_new_weights(self, strategies, new_weights):
        """应用新权重"""
        for strategy_name, new_weight in new_weights.items():
            old_weight = strategies[strategy_name]['weight']
            strategies[strategy_name]['weight'] = new_weight
            
            # 记录权重历史
            self.weight_history[strategy_name].append({
                'timestamp': datetime.now(),
                'weight': new_weight,
                'change': new_weight - old_weight
            })
    
    def get_weight_history(self, strategy_name=None):
        """获取权重历史"""
        if strategy_name:
            return self.weight_history.get(strategy_name, [])
        else:
            return dict(self.weight_history)
```

## 8. 自定义风险控制规则引擎

### 8.1 规则引擎核心

```python
# src/simtradelab/plugins/risk/rule_engine.py
class RiskControlRuleEngine:
    """自定义风险控制规则引擎"""
    
    def __init__(self, config):
        self.config = config
        self.rules = {}
        self.rule_groups = {}
        self.rule_execution_history = []
        self.rule_performance_stats = defaultdict(dict)
        self.event_bus = EventBus()
        
    def register_rule(self, rule_name, rule_definition):
        """注册风险控制规则"""
        rule = RiskControlRule(rule_name, rule_definition)
        self.rules[rule_name] = rule
        
        # 添加到规则组
        group_name = rule_definition.get('group', 'default')
        if group_name not in self.rule_groups:
            self.rule_groups[group_name] = []
        self.rule_groups[group_name].append(rule_name)
        
        logger.info(f"Risk control rule registered: {rule_name}")
        
    def register_rule_group(self, group_name, rule_names, execution_strategy='all'):
        """注册规则组"""
        self.rule_groups[group_name] = {
            'rules': rule_names,
            'execution_strategy': execution_strategy,  # 'all', 'any', 'majority'
            'enabled': True
        }
        
    def evaluate_portfolio_risk(self, portfolio, market_data, context):
        """评估投资组合风险"""
        risk_assessment = {
            'timestamp': datetime.now(),
            'portfolio_value': portfolio.total_value,
            'risk_level': 'low',
            'triggered_rules': [],
            'risk_metrics': {},
            'recommendations': []
        }
        
        # 执行所有启用的规则
        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue
                
            try:
                rule_result = rule.evaluate(portfolio, market_data, context)
                
                # 记录规则执行历史
                self.rule_execution_history.append({
                    'timestamp': datetime.now(),
                    'rule_name': rule_name,
                    'result': rule_result,
                    'portfolio_value': portfolio.total_value
                })
                
                # 更新规则性能统计
                self._update_rule_performance_stats(rule_name, rule_result)
                
                # 处理规则结果
                if rule_result['triggered']:
                    risk_assessment['triggered_rules'].append({
                        'rule_name': rule_name,
                        'severity': rule_result['severity'],
                        'message': rule_result['message'],
                        'recommended_action': rule_result.get('recommended_action'),
                        'risk_score': rule_result.get('risk_score', 0)
                    })
                
                # 更新风险指标
                if 'metrics' in rule_result:
                    risk_assessment['risk_metrics'].update(rule_result['metrics'])
                    
            except Exception as e:
                logger.error(f"Rule {rule_name} evaluation failed: {e}")
                continue
        
        # 计算综合风险等级
        risk_assessment['risk_level'] = self._calculate_overall_risk_level(risk_assessment)
        
        # 生成风险建议
        risk_assessment['recommendations'] = self._generate_risk_recommendations(risk_assessment)
        
        # 发送风险事件
        self.event_bus.emit('risk_assessment_completed', risk_assessment)
        
        return risk_assessment
    
    def evaluate_order_risk(self, order, portfolio, market_data, context):
        """评估订单风险"""
        order_risk = {
            'order_id': order.id if hasattr(order, 'id') else 'unknown',
            'security': order.security,
            'amount': order.amount,
            'risk_level': 'low',
            'triggered_rules': [],
            'allowed': True,
            'modifications': {}
        }
        
        # 执行订单相关的风险规则
        for rule_name, rule in self.rules.items():
            if not rule.enabled or not rule.applies_to_orders:
                continue
                
            try:
                rule_result = rule.evaluate_order(order, portfolio, market_data, context)
                
                if rule_result['triggered']:
                    order_risk['triggered_rules'].append({
                        'rule_name': rule_name,
                        'severity': rule_result['severity'],
                        'message': rule_result['message'],
                        'action': rule_result.get('action', 'block')
                    })
                    
                    # 根据规则动作决定是否允许订单
                    if rule_result.get('action') == 'block':
                        order_risk['allowed'] = False
                    elif rule_result.get('action') == 'modify':
                        order_risk['modifications'].update(rule_result.get('modifications', {}))
                        
            except Exception as e:
                logger.error(f"Order rule {rule_name} evaluation failed: {e}")
                continue
        
        # 计算订单风险等级
        order_risk['risk_level'] = self._calculate_order_risk_level(order_risk)
        
        return order_risk
    
    def _calculate_overall_risk_level(self, risk_assessment):
        """计算综合风险等级"""
        if not risk_assessment['triggered_rules']:
            return 'low'
        
        max_severity = max(rule['severity'] for rule in risk_assessment['triggered_rules'])
        high_severity_count = sum(1 for rule in risk_assessment['triggered_rules'] if rule['severity'] == 'high')
        
        if max_severity == 'critical' or high_severity_count >= 2:
            return 'critical'
        elif max_severity == 'high':
            return 'high'
        elif max_severity == 'medium':
            return 'medium'
        else:
            return 'low'
    
    def _generate_risk_recommendations(self, risk_assessment):
        """生成风险建议"""
        recommendations = []
        
        for rule_info in risk_assessment['triggered_rules']:
            if rule_info.get('recommended_action'):
                recommendations.append({
                    'rule_name': rule_info['rule_name'],
                    'action': rule_info['recommended_action'],
                    'priority': rule_info['severity'],
                    'description': rule_info['message']
                })
        
        # 添加通用建议
        if risk_assessment['risk_level'] == 'critical':
            recommendations.append({
                'rule_name': 'system',
                'action': 'reduce_exposure',
                'priority': 'critical',
                'description': 'Critical risk level detected, consider reducing overall exposure'
            })
        
        return recommendations
    
    def _update_rule_performance_stats(self, rule_name, rule_result):
        """更新规则性能统计"""
        if rule_name not in self.rule_performance_stats:
            self.rule_performance_stats[rule_name] = {
                'total_evaluations': 0,
                'triggered_count': 0,
                'accuracy_score': 0,
                'last_triggered': None
            }
        
        stats = self.rule_performance_stats[rule_name]
        stats['total_evaluations'] += 1
        
        if rule_result['triggered']:
            stats['triggered_count'] += 1
            stats['last_triggered'] = datetime.now()
        
        # 计算准确率（这里简化为触发率）
        stats['accuracy_score'] = stats['triggered_count'] / stats['total_evaluations']
    
    def get_rule_performance_stats(self):
        """获取规则性能统计"""
        return dict(self.rule_performance_stats)
    
    def enable_rule(self, rule_name):
        """启用规则"""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = True
            logger.info(f"Rule {rule_name} enabled")
    
    def disable_rule(self, rule_name):
        """禁用规则"""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = False
            logger.info(f"Rule {rule_name} disabled")
    
    def get_rule_execution_history(self, rule_name=None, limit=100):
        """获取规则执行历史"""
        if rule_name:
            history = [h for h in self.rule_execution_history if h['rule_name'] == rule_name]
        else:
            history = self.rule_execution_history
        
        return history[-limit:]

class RiskControlRule:
    """风险控制规则"""
    
    def __init__(self, name, definition):
        self.name = name
        self.definition = definition
        self.enabled = definition.get('enabled', True)
        self.applies_to_orders = definition.get('applies_to_orders', True)
        self.severity = definition.get('severity', 'medium')
        self.condition = definition['condition']
        self.action = definition.get('action', 'alert')
        self.parameters = definition.get('parameters', {})
        
    def evaluate(self, portfolio, market_data, context):
        """评估规则"""
        try:
            # 根据条件类型执行不同的评估逻辑
            if self.condition['type'] == 'position_concentration':
                return self._evaluate_position_concentration(portfolio, market_data, context)
            elif self.condition['type'] == 'portfolio_drawdown':
                return self._evaluate_portfolio_drawdown(portfolio, market_data, context)
            elif self.condition['type'] == 'sector_exposure':
                return self._evaluate_sector_exposure(portfolio, market_data, context)
            elif self.condition['type'] == 'volatility_limit':
                return self._evaluate_volatility_limit(portfolio, market_data, context)
            elif self.condition['type'] == 'leverage_limit':
                return self._evaluate_leverage_limit(portfolio, market_data, context)
            elif self.condition['type'] == 'custom_expression':
                return self._evaluate_custom_expression(portfolio, market_data, context)
            else:
                return {'triggered': False, 'message': 'Unknown condition type'}
                
        except Exception as e:
            logger.error(f"Rule {self.name} evaluation error: {e}")
            return {'triggered': False, 'message': f'Evaluation error: {e}'}
    
    def evaluate_order(self, order, portfolio, market_data, context):
        """评估订单风险"""
        try:
            # 模拟订单执行后的投资组合状态
            simulated_portfolio = self._simulate_order_execution(order, portfolio)
            
            # 使用模拟的投资组合状态评估风险
            result = self.evaluate(simulated_portfolio, market_data, context)
            
            # 为订单评估添加特定的动作
            if result['triggered']:
                if self.action == 'block':
                    result['action'] = 'block'
                elif self.action == 'modify':
                    result['action'] = 'modify'
                    result['modifications'] = self._generate_order_modifications(order, result)
                else:
                    result['action'] = 'alert'
            
            return result
            
        except Exception as e:
            logger.error(f"Order rule {self.name} evaluation error: {e}")
            return {'triggered': False, 'message': f'Order evaluation error: {e}'}
    
    def _evaluate_position_concentration(self, portfolio, market_data, context):
        """评估持仓集中度"""
        max_concentration = self.parameters.get('max_concentration', 0.2)
        
        if portfolio.total_value == 0:
            return {'triggered': False, 'message': 'Portfolio is empty'}
        
        max_position_ratio = 0
        max_position_security = None
        
        for security, position in portfolio.positions.items():
            position_ratio = position.value / portfolio.total_value
            if position_ratio > max_position_ratio:
                max_position_ratio = position_ratio
                max_position_security = security
        
        if max_position_ratio > max_concentration:
            return {
                'triggered': True,
                'severity': self.severity,
                'message': f'Position concentration exceeded: {max_position_security} = {max_position_ratio:.2%} > {max_concentration:.2%}',
                'recommended_action': 'reduce_position',
                'risk_score': (max_position_ratio - max_concentration) / max_concentration,
                'metrics': {
                    'max_position_ratio': max_position_ratio,
                    'max_position_security': max_position_security
                }
            }
        
        return {'triggered': False, 'message': 'Position concentration within limits'}
    
    def _evaluate_portfolio_drawdown(self, portfolio, market_data, context):
        """评估投资组合回撤"""
        max_drawdown = self.parameters.get('max_drawdown', 0.15)
        
        # 获取历史净值数据
        portfolio_history = getattr(context, 'portfolio_history', [])
        
        if len(portfolio_history) < 2:
            return {'triggered': False, 'message': 'Insufficient portfolio history'}
        
        # 计算当前回撤
        peak_value = max(portfolio_history)
        current_value = portfolio.total_value
        current_drawdown = (peak_value - current_value) / peak_value
        
        if current_drawdown > max_drawdown:
            return {
                'triggered': True,
                'severity': self.severity,
                'message': f'Portfolio drawdown exceeded: {current_drawdown:.2%} > {max_drawdown:.2%}',
                'recommended_action': 'reduce_risk',
                'risk_score': (current_drawdown - max_drawdown) / max_drawdown,
                'metrics': {
                    'current_drawdown': current_drawdown,
                    'peak_value': peak_value,
                    'current_value': current_value
                }
            }
        
        return {'triggered': False, 'message': 'Portfolio drawdown within limits'}
    
    def _evaluate_sector_exposure(self, portfolio, market_data, context):
        """评估行业暴露度"""
        max_sector_exposure = self.parameters.get('max_sector_exposure', 0.3)
        
        # 获取持仓的行业分布
        sector_exposure = self._calculate_sector_exposure(portfolio)
        
        for sector, exposure in sector_exposure.items():
            if exposure > max_sector_exposure:
                return {
                    'triggered': True,
                    'severity': self.severity,
                    'message': f'Sector exposure exceeded: {sector} = {exposure:.2%} > {max_sector_exposure:.2%}',
                    'recommended_action': 'reduce_sector_exposure',
                    'risk_score': (exposure - max_sector_exposure) / max_sector_exposure,
                    'metrics': {
                        'sector_exposure': sector_exposure,
                        'max_sector': sector,
                        'max_exposure': exposure
                    }
                }
        
        return {'triggered': False, 'message': 'Sector exposure within limits'}
    
    def _evaluate_volatility_limit(self, portfolio, market_data, context):
        """评估波动率限制"""
        max_volatility = self.parameters.get('max_volatility', 0.2)
        lookback_period = self.parameters.get('lookback_period', 30)
        
        # 计算投资组合历史波动率
        portfolio_history = getattr(context, 'portfolio_history', [])
        
        if len(portfolio_history) < lookback_period:
            return {'triggered': False, 'message': 'Insufficient data for volatility calculation'}
        
        returns = [
            (portfolio_history[i] - portfolio_history[i-1]) / portfolio_history[i-1]
            for i in range(1, len(portfolio_history))
        ]
        
        recent_returns = returns[-lookback_period:]
        volatility = np.std(recent_returns) * np.sqrt(252)  # 年化波动率
        
        if volatility > max_volatility:
            return {
                'triggered': True,
                'severity': self.severity,
                'message': f'Portfolio volatility exceeded: {volatility:.2%} > {max_volatility:.2%}',
                'recommended_action': 'reduce_volatility',
                'risk_score': (volatility - max_volatility) / max_volatility,
                'metrics': {
                    'portfolio_volatility': volatility,
                    'lookback_period': lookback_period
                }
            }
        
        return {'triggered': False, 'message': 'Portfolio volatility within limits'}
    
    def _evaluate_leverage_limit(self, portfolio, market_data, context):
        """评估杠杆限制"""
        max_leverage = self.parameters.get('max_leverage', 1.0)
        
        # 计算当前杠杆率
        total_position_value = sum(abs(position.value) for position in portfolio.positions.values())
        current_leverage = total_position_value / portfolio.total_value if portfolio.total_value > 0 else 0
        
        if current_leverage > max_leverage:
            return {
                'triggered': True,
                'severity': self.severity,
                'message': f'Leverage exceeded: {current_leverage:.2f}x > {max_leverage:.2f}x',
                'recommended_action': 'reduce_leverage',
                'risk_score': (current_leverage - max_leverage) / max_leverage,
                'metrics': {
                    'current_leverage': current_leverage,
                    'total_position_value': total_position_value,
                    'portfolio_value': portfolio.total_value
                }
            }
        
        return {'triggered': False, 'message': 'Leverage within limits'}
    
    def _evaluate_custom_expression(self, portfolio, market_data, context):
        """评估自定义表达式"""
        expression = self.condition.get('expression', '')
        
        if not expression:
            return {'triggered': False, 'message': 'No expression provided'}
        
        try:
            # 创建安全的评估环境
            eval_globals = {
                'portfolio': portfolio,
                'market_data': market_data,
                'context': context,
                'np': np,
                'pd': pd,
                'datetime': datetime,
                'abs': abs,
                'max': max,
                'min': min,
                'sum': sum,
                'len': len
            }
            
            # 评估表达式
            result = eval(expression, eval_globals)
            
            if result:
                return {
                    'triggered': True,
                    'severity': self.severity,
                    'message': f'Custom rule triggered: {expression}',
                    'recommended_action': self.parameters.get('recommended_action', 'review'),
                    'risk_score': 1.0,
                    'metrics': {
                        'expression': expression,
                        'result': result
                    }
                }
            else:
                return {'triggered': False, 'message': f'Custom rule not triggered: {expression}'}
                
        except Exception as e:
            return {'triggered': False, 'message': f'Expression evaluation error: {e}'}
    
    def _calculate_sector_exposure(self, portfolio):
        """计算行业暴露度"""
        # 这里需要实际的行业分类数据
        # 简化实现，假设从证券代码推断行业
        sector_exposure = defaultdict(float)
        
        for security, position in portfolio.positions.items():
            # 简化的行业分类逻辑
            if security.startswith('00'):
                sector = 'Technology'
            elif security.startswith('30'):
                sector = 'Growth'
            elif security.startswith('60'):
                sector = 'Traditional'
            else:
                sector = 'Other'
            
            sector_exposure[sector] += position.value / portfolio.total_value
        
        return dict(sector_exposure)
    
    def _simulate_order_execution(self, order, portfolio):
        """模拟订单执行"""
        # 创建投资组合副本
        simulated_portfolio = copy.deepcopy(portfolio)
        
        # 模拟订单执行
        if order.security in simulated_portfolio.positions:
            simulated_portfolio.positions[order.security].amount += order.amount
        else:
            # 创建新持仓
            simulated_portfolio.positions[order.security] = Position(
                security=order.security,
                amount=order.amount,
                cost_basis=order.price if hasattr(order, 'price') else 0
            )
        
        return simulated_portfolio
    
    def _generate_order_modifications(self, order, rule_result):
        """生成订单修改建议"""
        modifications = {}
        
        if rule_result.get('metrics', {}).get('max_position_ratio', 0) > 0:
            # 减少订单数量以控制持仓集中度
            reduction_factor = 0.8
            modifications['amount'] = int(order.amount * reduction_factor)
        
        return modifications
```

### 8.2 预定义风险规则库

```python
# src/simtradelab/plugins/risk/predefined_rules.py
class PredefinedRiskRules:
    """预定义风险规则库"""
    
    @staticmethod
    def get_basic_risk_rules():
        """获取基础风险规则"""
        return {
            'position_concentration_limit': {
                'condition': {'type': 'position_concentration'},
                'parameters': {'max_concentration': 0.15},
                'severity': 'high',
                'action': 'alert',
                'description': '单一持仓不超过15%'
            },
            
            'portfolio_drawdown_limit': {
                'condition': {'type': 'portfolio_drawdown'},
                'parameters': {'max_drawdown': 0.10},
                'severity': 'critical',
                'action': 'block',
                'description': '投资组合回撤不超过10%'
            },
            
            'sector_exposure_limit': {
                'condition': {'type': 'sector_exposure'},
                'parameters': {'max_sector_exposure': 0.25},
                'severity': 'medium',
                'action': 'alert',
                'description': '单一行业暴露度不超过25%'
            },
            
            'volatility_limit': {
                'condition': {'type': 'volatility_limit'},
                'parameters': {
                    'max_volatility': 0.18,
                    'lookback_period': 30
                },
                'severity': 'medium',
                'action': 'alert',
                'description': '投资组合年化波动率不超过18%'
            },
            
            'leverage_limit': {
                'condition': {'type': 'leverage_limit'},
                'parameters': {'max_leverage': 1.0},
                'severity': 'high',
                'action': 'block',
                'description': '杠杆率不超过1倍'
            }
        }
    
    @staticmethod
    def get_advanced_risk_rules():
        """获取高级风险规则"""
        return {
            'correlation_limit': {
                'condition': {
                    'type': 'custom_expression',
                    'expression': 'len([s for s in portfolio.positions.keys() if s.startswith("00")]) > 5'
                },
                'parameters': {'recommended_action': 'diversify'},
                'severity': 'medium',
                'action': 'alert',
                'description': '同类股票持仓数量限制'
            },
            
            'cash_ratio_limit': {
                'condition': {
                    'type': 'custom_expression',
                    'expression': 'portfolio.cash / portfolio.total_value < 0.05'
                },
                'parameters': {'recommended_action': 'increase_cash'},
                'severity': 'medium',
                'action': 'alert',
                'description': '现金比例不低于5%'
            },
            
            'order_size_limit': {
                'condition': {
                    'type': 'custom_expression',
                    'expression': 'abs(context.current_order.amount * context.current_order.price) > portfolio.total_value * 0.1'
                },
                'parameters': {'recommended_action': 'reduce_order_size'},
                'severity': 'high',
                'action': 'modify',
                'description': '单笔订单不超过总资产的10%',
                'applies_to_orders': True
            },
            
            'daily_loss_limit': {
                'condition': {
                    'type': 'custom_expression',
                    'expression': 'len(context.portfolio_history) > 0 and (portfolio.total_value - context.portfolio_history[-1]) / context.portfolio_history[-1] < -0.03'
                },
                'parameters': {'recommended_action': 'stop_trading'},
                'severity': 'critical',
                'action': 'block',
                'description': '单日亏损不超过3%'
            }
        }
    
    @staticmethod
    def get_market_condition_rules():
        """获取市场条件相关规则"""
        return {
            'high_volatility_protection': {
                'condition': {
                    'type': 'custom_expression',
                    'expression': 'market_data.get("market_volatility", 0) > 0.25'
                },
                'parameters': {'recommended_action': 'reduce_exposure'},
                'severity': 'high',
                'action': 'alert',
                'description': '市场高波动期保护'
            },
            
            'market_crash_protection': {
                'condition': {
                    'type': 'custom_expression',
                    'expression': 'market_data.get("market_return", 0) < -0.05'
                },
                'parameters': {'recommended_action': 'defensive_position'},
                'severity': 'critical',
                'action': 'block',
                'description': '市场暴跌保护'
            },
            
            'low_liquidity_warning': {
                'condition': {
                    'type': 'custom_expression',
                    'expression': 'any(market_data.get(security, {}).get("volume", 0) < 1000000 for security in portfolio.positions.keys())'
                },
                'parameters': {'recommended_action': 'check_liquidity'},
                'severity': 'medium',
                'action': 'alert',
                'description': '低流动性持仓警告'
            }
        }
```

### 8.3 风险规则管理器

```python
# src/simtradelab/plugins/risk/rule_manager.py
class RiskRuleManager:
    """风险规则管理器"""
    
    def __init__(self, rule_engine):
        self.rule_engine = rule_engine
        self.rule_templates = {}
        self.rule_presets = {}
        self.load_predefined_rules()
        
    def load_predefined_rules(self):
        """加载预定义规则"""
        basic_rules = PredefinedRiskRules.get_basic_risk_rules()
        advanced_rules = PredefinedRiskRules.get_advanced_risk_rules()
        market_rules = PredefinedRiskRules.get_market_condition_rules()
        
        all_rules = {**basic_rules, **advanced_rules, **market_rules}
        
        for rule_name, rule_def in all_rules.items():
            self.rule_engine.register_rule(rule_name, rule_def)
    
    def create_rule_preset(self, preset_name, rule_names, description=""):
        """创建规则预设"""
        self.rule_presets[preset_name] = {
            'rules': rule_names,
            'description': description,
            'created_at': datetime.now()
        }
        
        logger.info(f"Rule preset created: {preset_name}")
    
    def apply_rule_preset(self, preset_name):
        """应用规则预设"""
        if preset_name not in self.rule_presets:
            raise ValueError(f"Rule preset {preset_name} not found")
        
        preset = self.rule_presets[preset_name]
        
        # 禁用所有规则
        for rule_name in self.rule_engine.rules:
            self.rule_engine.disable_rule(rule_name)
        
        # 启用预设中的规则
        for rule_name in preset['rules']:
            self.rule_engine.enable_rule(rule_name)
        
        logger.info(f"Applied rule preset: {preset_name}")
    
    def get_rule_presets(self):
        """获取所有规则预设"""
        return {
            'conservative': {
                'rules': [
                    'position_concentration_limit',
                    'portfolio_drawdown_limit',
                    'sector_exposure_limit',
                    'leverage_limit',
                    'cash_ratio_limit',
                    'daily_loss_limit'
                ],
                'description': '保守型风险控制'
            },
            'aggressive': {
                'rules': [
                    'portfolio_drawdown_limit',
                    'leverage_limit',
                    'daily_loss_limit'
                ],
                'description': '激进型风险控制'
            },
            'balanced': {
                'rules': [
                    'position_concentration_limit',
                    'portfolio_drawdown_limit',
                    'sector_exposure_limit',
                    'volatility_limit',
                    'leverage_limit'
                ],
                'description': '平衡型风险控制'
            },
            'market_sensitive': {
                'rules': [
                    'position_concentration_limit',
                    'portfolio_drawdown_limit',
                    'high_volatility_protection',
                    'market_crash_protection',
                    'low_liquidity_warning'
                ],
                'description': '市场敏感型风险控制'
            }
        }
    
    def create_custom_rule(self, rule_name, rule_config):
        """创建自定义规则"""
        # 验证规则配置
        required_fields = ['condition', 'severity', 'action']
        for field in required_fields:
            if field not in rule_config:
                raise ValueError(f"Missing required field: {field}")
        
        # 注册规则
        self.rule_engine.register_rule(rule_name, rule_config)
        
        logger.info(f"Custom rule created: {rule_name}")
    
    def modify_rule_parameters(self, rule_name, new_parameters):
        """修改规则参数"""
        if rule_name not in self.rule_engine.rules:
            raise ValueError(f"Rule {rule_name} not found")
        
        rule = self.rule_engine.rules[rule_name]
        old_parameters = rule.parameters.copy()
        
        rule.parameters.update(new_parameters)
        
        logger.info(f"Rule {rule_name} parameters updated: {old_parameters} -> {rule.parameters}")
    
    def get_rule_effectiveness_report(self):
        """获取规则有效性报告"""
        stats = self.rule_engine.get_rule_performance_stats()
        
        report = {
            'total_rules': len(self.rule_engine.rules),
            'enabled_rules': sum(1 for rule in self.rule_engine.rules.values() if rule.enabled),
            'rule_performance': []
        }
        
        for rule_name, rule_stats in stats.items():
            rule_perf = {
                'rule_name': rule_name,
                'total_evaluations': rule_stats.get('total_evaluations', 0),
                'triggered_count': rule_stats.get('triggered_count', 0),
                'trigger_rate': rule_stats.get('accuracy_score', 0),
                'last_triggered': rule_stats.get('last_triggered'),
                'effectiveness': self._calculate_rule_effectiveness(rule_name, rule_stats)
            }
            report['rule_performance'].append(rule_perf)
        
        return report
    
    def _calculate_rule_effectiveness(self, rule_name, rule_stats):
        """计算规则有效性"""
        total_evaluations = rule_stats.get('total_evaluations', 0)
        triggered_count = rule_stats.get('triggered_count', 0)
        
        if total_evaluations == 0:
            return 0
        
        trigger_rate = triggered_count / total_evaluations
        
        # 简化的有效性计算
        # 触发率在5%-15%之间认为是有效的
        if 0.05 <= trigger_rate <= 0.15:
            return 1.0
        elif trigger_rate < 0.05:
            return trigger_rate / 0.05  # 触发率过低
        else:
            return 0.15 / trigger_rate  # 触发率过高
```

## 9. 插件可扩展可视化系统

### 9.1 可视化插件基类

```python
# src/simtradelab/plugins/visualization/base_visualization.py
class BaseVisualizationPlugin(BasePlugin):
    """可视化插件基类"""
    
    def __init__(self, config):
        super().__init__(config)
        self.backend = config.get('backend', 'plotly')
        self.theme = config.get('theme', 'default')
        self.export_formats = config.get('export_formats', ['html', 'png'])
        self.chart_cache = {}
        
    def create_chart(self, chart_type, data, **kwargs):
        """创建图表"""
        if self.backend == 'plotly':
            return self._create_plotly_chart(chart_type, data, **kwargs)
        elif self.backend == 'matplotlib':
            return self._create_matplotlib_chart(chart_type, data, **kwargs)
        elif self.backend == 'bokeh':
            return self._create_bokeh_chart(chart_type, data, **kwargs)
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")
    
    def _create_plotly_chart(self, chart_type, data, **kwargs):
        """创建Plotly图表"""
        import plotly.graph_objects as go
        import plotly.express as px
        
        if chart_type == 'line':
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data['x'], y=data['y'], mode='lines'))
        elif chart_type == 'candlestick':
            fig = go.Figure(data=go.Candlestick(
                x=data['x'],
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close']
            ))
        elif chart_type == 'bar':
            fig = go.Figure(data=go.Bar(x=data['x'], y=data['y']))
        elif chart_type == 'scatter':
            fig = go.Figure(data=go.Scatter(x=data['x'], y=data['y'], mode='markers'))
        elif chart_type == 'heatmap':
            fig = go.Figure(data=go.Heatmap(z=data['z'], x=data['x'], y=data['y']))
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        # 应用主题
        self._apply_plotly_theme(fig)
        
        return fig
    
    def _create_matplotlib_chart(self, chart_type, data, **kwargs):
        """创建Matplotlib图表"""
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=kwargs.get('figsize', (10, 6)))
        
        if chart_type == 'line':
            ax.plot(data['x'], data['y'])
        elif chart_type == 'bar':
            ax.bar(data['x'], data['y'])
        elif chart_type == 'scatter':
            ax.scatter(data['x'], data['y'])
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        # 应用主题
        self._apply_matplotlib_theme(ax)
        
        return fig
    
    def _apply_plotly_theme(self, fig):
        """应用Plotly主题"""
        if self.theme == 'dark':
            fig.update_layout(
                template='plotly_dark',
                font=dict(color='white'),
                paper_bgcolor='rgb(30, 30, 30)',
                plot_bgcolor='rgb(30, 30, 30)'
            )
        elif self.theme == 'white':
            fig.update_layout(
                template='plotly_white',
                font=dict(color='black'),
                paper_bgcolor='white',
                plot_bgcolor='white'
            )
    
    def _apply_matplotlib_theme(self, ax):
        """应用Matplotlib主题"""
        if self.theme == 'dark':
            ax.set_facecolor('black')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
    
    def export_chart(self, chart, filename, format='html'):
        """导出图表"""
        if self.backend == 'plotly':
            if format == 'html':
                chart.write_html(filename)
            elif format == 'png':
                chart.write_image(filename)
            elif format == 'pdf':
                chart.write_image(filename)
        elif self.backend == 'matplotlib':
            if format == 'png':
                chart.savefig(filename, format='png')
            elif format == 'pdf':
                chart.savefig(filename, format='pdf')
    
    def register_chart_type(self, chart_type, create_func):
        """注册自定义图表类型"""
        setattr(self, f'_create_{chart_type}_chart', create_func)
        
    def get_supported_chart_types(self):
        """获取支持的图表类型"""
        return ['line', 'candlestick', 'bar', 'scatter', 'heatmap']
```

### 9.2 策略性能可视化插件

```python
# src/simtradelab/plugins/visualization/strategy_performance_viz.py
class StrategyPerformanceVisualization(BaseVisualizationPlugin):
    """策略性能可视化插件"""
    
    def create_performance_dashboard(self, strategy_results, benchmark_data=None):
        """创建策略性能仪表板"""
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # 创建子图布局
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=[
                '累计收益曲线', '每日收益分布',
                '回撤分析', '滚动夏普比率',
                '月度收益热力图', '风险收益散点图'
            ],
            specs=[
                [{"secondary_y": True}, {"type": "histogram"}],
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"type": "heatmap"}, {"type": "scatter"}]
            ]
        )
        
        # 1. 累计收益曲线
        dates = strategy_results['dates']
        cumulative_returns = strategy_results['cumulative_returns']
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=cumulative_returns,
                name='策略收益',
                line=dict(color='blue', width=2)
            ),
            row=1, col=1
        )
        
        if benchmark_data:
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=benchmark_data['cumulative_returns'],
                    name='基准收益',
                    line=dict(color='gray', width=1, dash='dash')
                ),
                row=1, col=1
            )
        
        # 2. 每日收益分布
        daily_returns = strategy_results['daily_returns']
        fig.add_trace(
            go.Histogram(
                x=daily_returns,
                nbinsx=50,
                name='收益分布',
                marker_color='lightblue'
            ),
            row=1, col=2
        )
        
        # 3. 回撤分析
        drawdown = strategy_results['drawdown']
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=drawdown,
                fill='tozeroy',
                name='回撤',
                line=dict(color='red')
            ),
            row=2, col=1
        )
        
        # 4. 滚动夏普比率
        rolling_sharpe = strategy_results['rolling_sharpe']
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=rolling_sharpe,
                name='滚动夏普比率',
                line=dict(color='green')
            ),
            row=2, col=2
        )
        
        # 5. 月度收益热力图
        monthly_returns = strategy_results['monthly_returns']
        fig.add_trace(
            go.Heatmap(
                z=monthly_returns['values'],
                x=monthly_returns['months'],
                y=monthly_returns['years'],
                colorscale='RdYlGn',
                name='月度收益'
            ),
            row=3, col=1
        )
        
        # 6. 风险收益散点图
        if 'risk_return_data' in strategy_results:
            risk_data = strategy_results['risk_return_data']
            fig.add_trace(
                go.Scatter(
                    x=risk_data['risk'],
                    y=risk_data['return'],
                    mode='markers',
                    name='风险收益',
                    marker=dict(size=8, color='purple')
                ),
                row=3, col=2
            )
        
        # 更新布局
        fig.update_layout(
            title='策略性能分析仪表板',
            showlegend=True,
            height=1200,
            template=self.theme
        )
        
        return fig
    
    def create_real_time_monitoring_dashboard(self, portfolio, strategy_metrics):
        """创建实时监控仪表板"""
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=[
                '实时P&L', '风险监控', '策略状态',
                '资金使用率', '持仓分布', '交易活动'
            ]
        )
        
        # 实时P&L曲线
        fig.add_trace(
            go.Scatter(
                x=portfolio['timestamp'],
                y=portfolio['pnl'],
                mode='lines',
                name='实时P&L',
                line=dict(color='green', width=2)
            ),
            row=1, col=1
        )
        
        # 风险监控指标
        fig.add_trace(
            go.Scatter(
                x=strategy_metrics['timestamp'],
                y=strategy_metrics['drawdown'],
                mode='lines',
                name='回撤',
                line=dict(color='red', width=2)
            ),
            row=1, col=2
        )
        
        # 策略状态监控
        fig.add_trace(
            go.Scatter(
                x=strategy_metrics['timestamp'],
                y=strategy_metrics['signal_strength'],
                mode='lines+markers',
                name='信号强度',
                line=dict(color='blue', width=2)
            ),
            row=1, col=3
        )
        
        # 资金使用率
        fig.add_trace(
            go.Scatter(
                x=portfolio['timestamp'],
                y=portfolio['cash_usage_ratio'],
                mode='lines',
                name='资金使用率',
                line=dict(color='orange', width=2)
            ),
            row=2, col=1
        )
        
        # 持仓分布（饼图）
        fig.add_trace(
            go.Pie(
                labels=portfolio['position_symbols'],
                values=portfolio['position_values'],
                name='持仓分布'
            ),
            row=2, col=2
        )
        
        # 交易活动热力图
        fig.add_trace(
            go.Heatmap(
                z=strategy_metrics['trading_activity'],
                colorscale='Viridis',
                name='交易活动'
            ),
            row=2, col=3
        )
        
        fig.update_layout(
            title='实时策略监控仪表板',
            showlegend=True,
            height=800
        )
        
        return fig
    
    def create_risk_analysis_chart(self, risk_metrics):
        """创建风险分析图表"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'VaR分析', '相关性矩阵',
                '波动率分析', '压力测试结果'
            ]
        )
        
        # VaR分析
        fig.add_trace(
            go.Scatter(
                x=risk_metrics['dates'],
                y=risk_metrics['var_95'],
                name='95% VaR',
                line=dict(color='red', width=2)
            ),
            row=1, col=1
        )
        
        # 相关性矩阵
        fig.add_trace(
            go.Heatmap(
                z=risk_metrics['correlation_matrix'],
                x=risk_metrics['symbols'],
                y=risk_metrics['symbols'],
                colorscale='RdBu',
                name='相关性'
            ),
            row=1, col=2
        )
        
        # 波动率分析
        fig.add_trace(
            go.Scatter(
                x=risk_metrics['dates'],
                y=risk_metrics['volatility'],
                name='波动率',
                line=dict(color='blue', width=2)
            ),
            row=2, col=1
        )
        
        # 压力测试结果
        fig.add_trace(
            go.Bar(
                x=risk_metrics['stress_scenarios'],
                y=risk_metrics['stress_results'],
                name='压力测试',
                marker_color='orange'
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title='风险分析报告',
            showlegend=True,
            height=800
        )
        
        return fig
```

### 9.3 交互式K线图插件

```python
# src/simtradelab/plugins/visualization/interactive_kline.py
class InteractiveKLineChart(BaseVisualizationPlugin):
    """交互式K线图插件"""
    
    def create_enhanced_kline_chart(self, price_data, indicators=None, signals=None, volume=True):
        """创建增强K线图"""
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # 创建子图（K线图和成交量）
        if volume:
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.1,
                subplot_titles=['价格', '成交量'],
                row_heights=[0.7, 0.3]
            )
        else:
            fig = go.Figure()
        
        # 添加K线图
        fig.add_trace(
            go.Candlestick(
                x=price_data['datetime'],
                open=price_data['open'],
                high=price_data['high'],
                low=price_data['low'],
                close=price_data['close'],
                name='K线',
                increasing_line_color='red',
                decreasing_line_color='green'
            ),
            row=1, col=1
        )
        
        # 添加技术指标
        if indicators:
            for indicator_name, indicator_data in indicators.items():
                if indicator_name == 'MA':
                    for period, ma_data in indicator_data.items():
                        fig.add_trace(
                            go.Scatter(
                                x=price_data['datetime'],
                                y=ma_data,
                                mode='lines',
                                name=f'MA{period}',
                                line=dict(width=1)
                            ),
                            row=1, col=1
                        )
                elif indicator_name == 'BOLLINGER':
                    fig.add_trace(
                        go.Scatter(
                            x=price_data['datetime'],
                            y=indicator_data['upper'],
                            mode='lines',
                            name='布林上轨',
                            line=dict(color='rgba(255,0,0,0.5)', width=1)
                        ),
                        row=1, col=1
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=price_data['datetime'],
                            y=indicator_data['lower'],
                            mode='lines',
                            name='布林下轨',
                            line=dict(color='rgba(255,0,0,0.5)', width=1),
                            fill='tonexty'
                        ),
                        row=1, col=1
                    )
        
        # 添加交易信号
        if signals:
            buy_signals = signals[signals['action'] == 'buy']
            sell_signals = signals[signals['action'] == 'sell']
            
            # 买入信号
            fig.add_trace(
                go.Scatter(
                    x=buy_signals['datetime'],
                    y=buy_signals['price'],
                    mode='markers',
                    marker=dict(
                        symbol='triangle-up',
                        size=12,
                        color='red',
                        line=dict(width=2, color='darkred')
                    ),
                    name='买入信号',
                    text=buy_signals['reason'],
                    textposition='top center'
                ),
                row=1, col=1
            )
            
            # 卖出信号
            fig.add_trace(
                go.Scatter(
                    x=sell_signals['datetime'],
                    y=sell_signals['price'],
                    mode='markers',
                    marker=dict(
                        symbol='triangle-down',
                        size=12,
                        color='green',
                        line=dict(width=2, color='darkgreen')
                    ),
                    name='卖出信号',
                    text=sell_signals['reason'],
                    textposition='bottom center'
                ),
                row=1, col=1
            )
        
        # 添加成交量
        if volume:
            colors = ['red' if close >= open else 'green' 
                     for close, open in zip(price_data['close'], price_data['open'])]
            
            fig.add_trace(
                go.Bar(
                    x=price_data['datetime'],
                    y=price_data['volume'],
                    name='成交量',
                    marker_color=colors,
                    opacity=0.7
                ),
                row=2, col=1
            )
        
        # 更新布局
        fig.update_layout(
            title='交互式K线图',
            xaxis_rangeslider_visible=False,
            height=600 if volume else 400,
            showlegend=True
        )
        
        # 添加交互功能
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label='1D', step='day', stepmode='backward'),
                        dict(count=7, label='7D', step='day', stepmode='backward'),
                        dict(count=30, label='30D', step='day', stepmode='backward'),
                        dict(count=90, label='3M', step='day', stepmode='backward'),
                        dict(step='all')
                    ])
                ),
                rangeslider=dict(visible=False),
                type='date'
            )
        )
        
        return fig
    
    def add_drawing_tools(self, fig):
        """添加绘图工具"""
        fig.update_layout(
            dragmode='drawline',
            newshape=dict(
                line_color='yellow',
                line_width=3,
                opacity=0.8
            )
        )
        
        # 配置绘图工具
        config = {
            'modeBarButtonsToAdd': [
                'drawline',
                'drawopenpath',
                'drawclosedpath',
                'drawcircle',
                'drawrect',
                'eraseshape'
            ]
        }
        
        return fig, config
    
    def create_multi_timeframe_chart(self, price_data_dict):
        """创建多时间周期图表"""
        from plotly.subplots import make_subplots
        
        timeframes = list(price_data_dict.keys())
        rows = len(timeframes)
        
        fig = make_subplots(
            rows=rows, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=[f'{tf} 周期' for tf in timeframes]
        )
        
        for i, (timeframe, data) in enumerate(price_data_dict.items(), 1):
            fig.add_trace(
                go.Candlestick(
                    x=data['datetime'],
                    open=data['open'],
                    high=data['high'],
                    low=data['low'],
                    close=data['close'],
                    name=f'{timeframe}',
                    increasing_line_color='red',
                    decreasing_line_color='green'
                ),
                row=i, col=1
            )
        
        fig.update_layout(
            title='多时间周期分析',
            height=200 * rows,
            showlegend=True
        )
        
        return fig
```

## 10. API安全服务和开发者生态

### 10.1 OAuth2/JWT认证系统

```python
# src/simtradelab/plugins/security/auth_service.py
class AuthenticationService:
    """认证服务 - 支持OAuth2和JWT"""
    
    def __init__(self, config):
        self.config = config
        self.jwt_secret = config.get('jwt_secret', 'default_secret')
        self.jwt_algorithm = config.get('jwt_algorithm', 'HS256')
        self.jwt_expiration = config.get('jwt_expiration', 3600)  # 1小时
        self.oauth2_providers = config.get('oauth2_providers', {})
        self.user_store = UserStore(config.get('user_store', {}))
        self.rate_limiter = RateLimiter(config.get('rate_limit', {}))
        
    def create_jwt_token(self, user_id, permissions=None):
        """创建JWT令牌"""
        import jwt
        from datetime import datetime, timedelta
        
        payload = {
            'user_id': user_id,
            'permissions': permissions or [],
            'exp': datetime.utcnow() + timedelta(seconds=self.jwt_expiration),
            'iat': datetime.utcnow(),
            'iss': 'simtradelab'
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token
    
    def verify_jwt_token(self, token):
        """验证JWT令牌"""
        import jwt
        
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return {
                'valid': True,
                'user_id': payload.get('user_id'),
                'permissions': payload.get('permissions', []),
                'exp': payload.get('exp')
            }
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'valid': False, 'error': 'Invalid token'}
    
    def authenticate_user(self, username, password):
        """用户认证"""
        user = self.user_store.get_user(username)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        if not self._verify_password(password, user['password_hash']):
            return {'success': False, 'error': 'Invalid password'}
        
        # 检查用户状态
        if not user.get('active', True):
            return {'success': False, 'error': 'Account deactivated'}
        
        # 生成JWT令牌
        token = self.create_jwt_token(user['id'], user.get('permissions', []))
        
        return {
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'permissions': user.get('permissions', [])
            }
        }
    
    def oauth2_authorize(self, provider, auth_code):
        """OAuth2授权"""
        if provider not in self.oauth2_providers:
            return {'success': False, 'error': 'Unsupported provider'}
        
        provider_config = self.oauth2_providers[provider]
        
        # 获取访问令牌
        token_response = self._exchange_auth_code(provider_config, auth_code)
        if not token_response.get('success'):
            return token_response
        
        # 获取用户信息
        user_info = self._get_user_info(provider_config, token_response['access_token'])
        if not user_info.get('success'):
            return user_info
        
        # 创建或更新用户
        user = self._create_or_update_oauth_user(provider, user_info['user_data'])
        
        # 生成JWT令牌
        token = self.create_jwt_token(user['id'], user.get('permissions', []))
        
        return {
            'success': True,
            'token': token,
            'user': user
        }
    
    def refresh_token(self, refresh_token):
        """刷新令牌"""
        # 验证refresh token
        refresh_data = self.verify_jwt_token(refresh_token)
        if not refresh_data['valid']:
            return {'success': False, 'error': 'Invalid refresh token'}
        
        # 生成新的访问令牌
        new_token = self.create_jwt_token(
            refresh_data['user_id'],
            refresh_data['permissions']
        )
        
        return {
            'success': True,
            'token': new_token
        }
    
    def check_rate_limit(self, user_id, endpoint):
        """检查访问频率限制"""
        return self.rate_limiter.check_limit(user_id, endpoint)
    
    def _verify_password(self, password, password_hash):
        """验证密码"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _exchange_auth_code(self, provider_config, auth_code):
        """交换授权码获取访问令牌"""
        import requests
        
        token_url = provider_config['token_url']
        client_id = provider_config['client_id']
        client_secret = provider_config['client_secret']
        redirect_uri = provider_config['redirect_uri']
        
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            return {
                'success': True,
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token'),
                'expires_in': token_data.get('expires_in')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_user_info(self, provider_config, access_token):
        """获取用户信息"""
        import requests
        
        user_info_url = provider_config['user_info_url']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        try:
            response = requests.get(user_info_url, headers=headers)
            response.raise_for_status()
            
            user_data = response.json()
            return {
                'success': True,
                'user_data': user_data
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_or_update_oauth_user(self, provider, user_data):
        """创建或更新OAuth用户"""
        oauth_id = user_data.get('id')
        email = user_data.get('email')
        username = user_data.get('login') or user_data.get('username')
        
        # 查找现有用户
        existing_user = self.user_store.find_oauth_user(provider, oauth_id)
        
        if existing_user:
            # 更新用户信息
            existing_user.update({
                'email': email,
                'username': username,
                'last_login': datetime.now()
            })
            self.user_store.update_user(existing_user)
            return existing_user
        else:
            # 创建新用户
            new_user = {
                'id': self.user_store.generate_user_id(),
                'username': username,
                'email': email,
                'oauth_provider': provider,
                'oauth_id': oauth_id,
                'permissions': ['read', 'backtest'],  # 默认权限
                'created_at': datetime.now(),
                'last_login': datetime.now(),
                'active': True
            }
            self.user_store.create_user(new_user)
            return new_user

class RateLimiter:
    """访问频率限制器"""
    
    def __init__(self, config):
        self.limits = config.get('limits', {})
        self.redis_client = self._init_redis(config.get('redis'))
        self.default_limit = config.get('default_limit', {'requests': 100, 'window': 3600})
        
    def check_limit(self, user_id, endpoint):
        """检查访问频率限制"""
        limit_key = f"rate_limit:{user_id}:{endpoint}"
        
        # 获取端点限制配置
        endpoint_limit = self.limits.get(endpoint, self.default_limit)
        max_requests = endpoint_limit['requests']
        window_seconds = endpoint_limit['window']
        
        # 使用Redis滑动窗口算法
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # 删除过期的请求记录
        self.redis_client.zremrangebyscore(limit_key, 0, window_start)
        
        # 获取当前窗口内的请求数量
        current_requests = self.redis_client.zcard(limit_key)
        
        if current_requests >= max_requests:
            return {
                'allowed': False,
                'limit': max_requests,
                'window': window_seconds,
                'current': current_requests,
                'reset_time': window_start + window_seconds
            }
        
        # 记录当前请求
        self.redis_client.zadd(limit_key, {str(current_time): current_time})
        self.redis_client.expire(limit_key, window_seconds)
        
        return {
            'allowed': True,
            'limit': max_requests,
            'window': window_seconds,
            'current': current_requests + 1,
            'remaining': max_requests - current_requests - 1
        }
    
    def _init_redis(self, redis_config):
        """初始化Redis客户端"""
        if redis_config:
            import redis
            return redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                password=redis_config.get('password')
            )
        else:
            # 使用内存实现（仅用于开发）
            return MemoryRateLimitStore()

class UserStore:
    """用户存储"""
    
    def __init__(self, config):
        self.config = config
        self.storage_type = config.get('type', 'memory')
        
        if self.storage_type == 'database':
            self.db = Database(config.get('database'))
        else:
            self.users = {}
            self.oauth_users = {}
    
    def get_user(self, username):
        """获取用户"""
        if self.storage_type == 'database':
            return self.db.get_user_by_username(username)
        else:
            return self.users.get(username)
    
    def create_user(self, user_data):
        """创建用户"""
        if self.storage_type == 'database':
            return self.db.create_user(user_data)
        else:
            user_id = user_data['id']
            username = user_data['username']
            self.users[username] = user_data
            
            # 如果是OAuth用户，同时记录到OAuth索引
            if 'oauth_provider' in user_data:
                provider = user_data['oauth_provider']
                oauth_id = user_data['oauth_id']
                if provider not in self.oauth_users:
                    self.oauth_users[provider] = {}
                self.oauth_users[provider][oauth_id] = user_data
            
            return user_data
    
    def update_user(self, user_data):
        """更新用户"""
        if self.storage_type == 'database':
            return self.db.update_user(user_data)
        else:
            username = user_data['username']
            if username in self.users:
                self.users[username].update(user_data)
            return user_data
    
    def find_oauth_user(self, provider, oauth_id):
        """查找OAuth用户"""
        if self.storage_type == 'database':
            return self.db.find_oauth_user(provider, oauth_id)
        else:
            return self.oauth_users.get(provider, {}).get(oauth_id)
    
    def generate_user_id(self):
        """生成用户ID"""
        import uuid
        return str(uuid.uuid4())
```

### 10.2 API网关和权限管理

```python
# src/simtradelab/plugins/security/api_gateway.py
class APIGateway:
    """API网关 - 统一入口和权限控制"""
    
    def __init__(self, config):
        self.config = config
        self.auth_service = AuthenticationService(config.get('auth', {}))
        self.permission_manager = PermissionManager(config.get('permissions', {}))
        self.api_registry = APIRegistry()
        self.middleware_chain = self._init_middleware_chain()
        
    def register_api(self, path, handler, methods=['GET'], permissions=None):
        """注册API端点"""
        self.api_registry.register(path, handler, methods, permissions or [])
    
    def handle_request(self, request):
        """处理API请求"""
        # 执行中间件链
        for middleware in self.middleware_chain:
            result = middleware.process_request(request)
            if result.get('stop', False):
                return result['response']
        
        # 路由到具体处理器
        handler = self.api_registry.get_handler(request.path, request.method)
        if not handler:
            return {'error': 'API not found', 'status': 404}
        
        # 检查权限
        required_permissions = handler.get('permissions', [])
        if required_permissions:
            if not hasattr(request, 'user') or not request.user:
                return {'error': 'Authentication required', 'status': 401}
            
            user_permissions = request.user.get('permissions', [])
            if not self.permission_manager.check_permissions(user_permissions, required_permissions):
                return {'error': 'Insufficient permissions', 'status': 403}
        
        # 执行处理器
        try:
            response = handler['handler'](request)
            return response
        except Exception as e:
            logger.error(f"API handler error: {e}")
            return {'error': 'Internal server error', 'status': 500}
    
    def _init_middleware_chain(self):
        """初始化中间件链"""
        middleware_classes = [
            CORSMiddleware,
            AuthenticationMiddleware,
            RateLimitMiddleware,
            LoggingMiddleware
        ]
        
        middleware_chain = []
        for middleware_class in middleware_classes:
            middleware = middleware_class(self.config.get(middleware_class.__name__.lower(), {}))
            middleware.set_auth_service(self.auth_service)
            middleware_chain.append(middleware)
        
        return middleware_chain

class CORSMiddleware:
    """CORS中间件"""
    
    def __init__(self, config):
        self.allowed_origins = config.get('allowed_origins', ['*'])
        self.allowed_methods = config.get('allowed_methods', ['GET', 'POST', 'PUT', 'DELETE'])
        self.allowed_headers = config.get('allowed_headers', ['*'])
        
    def process_request(self, request):
        """处理CORS请求"""
        origin = request.headers.get('Origin')
        
        if origin and (self.allowed_origins == ['*'] or origin in self.allowed_origins):
            # 设置CORS头
            cors_headers = {
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Methods': ', '.join(self.allowed_methods),
                'Access-Control-Allow-Headers': ', '.join(self.allowed_headers),
                'Access-Control-Max-Age': '86400'  # 24小时
            }
            
            # 处理预检请求
            if request.method == 'OPTIONS':
                return {
                    'stop': True,
                    'response': {
                        'status': 200,
                        'headers': cors_headers
                    }
                }
            
            # 添加CORS头到请求上下文
            request.cors_headers = cors_headers
        
        return {'stop': False}

class AuthenticationMiddleware:
    """认证中间件"""
    
    def __init__(self, config):
        self.config = config
        self.auth_service = None
        
    def set_auth_service(self, auth_service):
        """设置认证服务"""
        self.auth_service = auth_service
        
    def process_request(self, request):
        """处理认证"""
        # 跳过不需要认证的路径
        skip_paths = self.config.get('skip_paths', ['/health', '/docs'])
        if request.path in skip_paths:
            return {'stop': False}
        
        # 获取认证令牌
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return {'stop': False}  # 让具体的API处理器决定是否需要认证
        
        if not auth_header.startswith('Bearer '):
            return {
                'stop': True,
                'response': {'error': 'Invalid authorization header format', 'status': 401}
            }
        
        token = auth_header[7:]  # 移除 'Bearer ' 前缀
        
        # 验证令牌
        token_data = self.auth_service.verify_jwt_token(token)
        if not token_data['valid']:
            return {
                'stop': True,
                'response': {'error': token_data['error'], 'status': 401}
            }
        
        # 将用户信息添加到请求上下文
        request.user = {
            'id': token_data['user_id'],
            'permissions': token_data['permissions']
        }
        
        return {'stop': False}

class RateLimitMiddleware:
    """访问频率限制中间件"""
    
    def __init__(self, config):
        self.config = config
        self.auth_service = None
        
    def set_auth_service(self, auth_service):
        """设置认证服务"""
        self.auth_service = auth_service
        
    def process_request(self, request):
        """处理访问频率限制"""
        # 获取用户ID
        user_id = 'anonymous'
        if hasattr(request, 'user') and request.user:
            user_id = request.user['id']
        
        # 检查访问频率限制
        rate_limit_result = self.auth_service.check_rate_limit(user_id, request.path)
        
        if not rate_limit_result['allowed']:
            return {
                'stop': True,
                'response': {
                    'error': 'Rate limit exceeded',
                    'status': 429,
                    'headers': {
                        'X-RateLimit-Limit': str(rate_limit_result['limit']),
                        'X-RateLimit-Remaining': '0',
                        'X-RateLimit-Reset': str(int(rate_limit_result['reset_time']))
                    }
                }
            }
        
        # 添加访问频率限制头
        request.rate_limit_headers = {
            'X-RateLimit-Limit': str(rate_limit_result['limit']),
            'X-RateLimit-Remaining': str(rate_limit_result['remaining']),
            'X-RateLimit-Reset': str(int(time.time() + rate_limit_result['window']))
        }
        
        return {'stop': False}

class LoggingMiddleware:
    """日志记录中间件"""
    
    def __init__(self, config):
        self.config = config
        self.log_level = config.get('log_level', 'INFO')
        
    def process_request(self, request):
        """记录请求日志"""
        # 记录请求信息
        logger.info(f"API Request: {request.method} {request.path}")
        
        # 记录用户信息（如果有）
        if hasattr(request, 'user') and request.user:
            logger.info(f"User: {request.user['id']}")
        
        # 记录请求时间
        request.start_time = time.time()
        
        return {'stop': False}

class PermissionManager:
    """权限管理器"""
    
    def __init__(self, config):
        self.config = config
        self.permissions = config.get('permissions', {})
        self.roles = config.get('roles', {})
        
    def check_permissions(self, user_permissions, required_permissions):
        """检查用户权限"""
        # 如果没有权限要求，允许访问
        if not required_permissions:
            return True
        
        # 检查用户是否有所有必需的权限
        for permission in required_permissions:
            if permission not in user_permissions:
                return False
        
        return True
    
    def expand_role_permissions(self, roles):
        """展开角色权限"""
        permissions = set()
        
        for role in roles:
            if role in self.roles:
                role_permissions = self.roles[role]
                permissions.update(role_permissions)
        
        return list(permissions)

class APIRegistry:
    """API注册表"""
    
    def __init__(self):
        self.routes = {}
        
    def register(self, path, handler, methods, permissions):
        """注册API端点"""
        for method in methods:
            route_key = f"{method}:{path}"
            self.routes[route_key] = {
                'handler': handler,
                'permissions': permissions
            }
    
    def get_handler(self, path, method):
        """获取处理器"""
        route_key = f"{method}:{path}"
        return self.routes.get(route_key)
```

### 10.3 插件SDK和开发者文档

```python
# src/simtradelab/plugins/sdk/plugin_sdk.py
class PluginSDK:
    """插件开发SDK"""
    
    def __init__(self):
        self.base_classes = {
            'BasePlugin': BasePlugin,
            'BaseVisualizationPlugin': BaseVisualizationPlugin,
            'BaseDataSourcePlugin': BaseDataSourcePlugin,
            'BaseRiskPlugin': BaseRiskPlugin
        }
        self.utilities = {
            'EventBus': EventBus,
            'ConfigManager': ConfigManager,
            'Logger': Logger
        }
        self.examples = self._load_examples()
        
    def create_plugin_template(self, plugin_type, plugin_name):
        """创建插件模板"""
        templates = {
            'data_source': self._create_data_source_template,
            'visualization': self._create_visualization_template,
            'risk_control': self._create_risk_control_template,
            'strategy': self._create_strategy_template
        }
        
        if plugin_type not in templates:
            raise ValueError(f"Unsupported plugin type: {plugin_type}")
        
        return templates[plugin_type](plugin_name)
    
    def _create_data_source_template(self, plugin_name):
        """创建数据源插件模板"""
        template = f'''
# {plugin_name} Data Source Plugin
from simtradelab.plugins.base import BaseDataSourcePlugin
import pandas as pd

class {plugin_name}DataSource(BaseDataSourcePlugin):
    """
    {plugin_name} 数据源插件
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.example.com')
        
    def get_data(self, request):
        """获取数据"""
        # 实现数据获取逻辑
        security = request.security
        start_date = request.start_date
        end_date = request.end_date
        
        # 调用API获取数据
        data = self._fetch_data(security, start_date, end_date)
        
        # 转换为标准格式
        return self._normalize_data(data)
    
    def _fetch_data(self, security, start_date, end_date):
        """从API获取数据"""
        # 实现API调用逻辑
        pass
    
    def _normalize_data(self, raw_data):
        """标准化数据格式"""
        # 转换为标准的DataFrame格式
        return pd.DataFrame(raw_data)
    
    def get_supported_securities(self):
        """获取支持的证券列表"""
        # 返回支持的证券代码列表
        return []
    
    def validate_security(self, security):
        """验证证券代码"""
        return security in self.get_supported_securities()

# 插件注册
plugin_class = {plugin_name}DataSource
plugin_info = {{
    'name': '{plugin_name.lower()}_data_source',
    'version': '1.0.0',
    'description': '{plugin_name} 数据源插件',
    'author': 'Your Name',
    'dependencies': ['pandas', 'requests']
}}
'''
        return template
    
    def _create_visualization_template(self, plugin_name):
        """创建可视化插件模板"""
        template = f'''
# {plugin_name} Visualization Plugin
from simtradelab.plugins.visualization.base_visualization import BaseVisualizationPlugin
import plotly.graph_objects as go

class {plugin_name}Visualization(BaseVisualizationPlugin):
    """
    {plugin_name} 可视化插件
    """
    
    def __init__(self, config):
        super().__init__(config)
        
    def create_custom_chart(self, data, **kwargs):
        """创建自定义图表"""
        # 实现自定义图表逻辑
        fig = go.Figure()
        
        # 添加数据
        fig.add_trace(go.Scatter(
            x=data['x'],
            y=data['y'],
            mode='lines+markers',
            name='{plugin_name} Chart'
        ))
        
        # 设置布局
        fig.update_layout(
            title='{plugin_name} 自定义图表',
            xaxis_title='X轴',
            yaxis_title='Y轴'
        )
        
        return fig
    
    def get_supported_chart_types(self):
        """获取支持的图表类型"""
        return super().get_supported_chart_types() + ['custom']

# 插件注册
plugin_class = {plugin_name}Visualization
plugin_info = {{
    'name': '{plugin_name.lower()}_visualization',
    'version': '1.0.0',
    'description': '{plugin_name} 可视化插件',
    'author': 'Your Name',
    'dependencies': ['plotly']
}}
'''
        return template
    
    def generate_plugin_documentation(self, plugin_class):
        """生成插件文档"""
        doc = {
            'name': plugin_class.__name__,
            'description': plugin_class.__doc__ or 'No description available',
            'methods': [],
            'configuration': {},
            'examples': []
        }
        
        # 提取方法信息
        for method_name in dir(plugin_class):
            if not method_name.startswith('_'):
                method = getattr(plugin_class, method_name)
                if callable(method):
                    doc['methods'].append({
                        'name': method_name,
                        'description': method.__doc__ or 'No description available',
                        'parameters': self._extract_method_parameters(method)
                    })
        
        return doc
    
    def _extract_method_parameters(self, method):
        """提取方法参数"""
        import inspect
        
        sig = inspect.signature(method)
        parameters = []
        
        for param_name, param in sig.parameters.items():
            if param_name != 'self':
                parameters.append({
                    'name': param_name,
                    'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any',
                    'default': str(param.default) if param.default != inspect.Parameter.empty else None
                })
        
        return parameters
    
    def _load_examples(self):
        """加载示例代码"""
        return {
            'basic_plugin': '''
from simtradelab.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self, config):
        super().__init__(config)
        self.my_setting = config.get('my_setting', 'default_value')
    
    def process_data(self, data):
        # 处理数据的逻辑
        return data
''',
            'data_source_plugin': '''
from simtradelab.plugins.base import BaseDataSourcePlugin

class MyDataSource(BaseDataSourcePlugin):
    def get_data(self, request):
        # 获取数据的逻辑
        return pd.DataFrame()
''',
            'visualization_plugin': '''
from simtradelab.plugins.visualization.base_visualization import BaseVisualizationPlugin

class MyVisualization(BaseVisualizationPlugin):
    def create_custom_chart(self, data):
        # 创建图表的逻辑
        return self.create_chart('line', data)
'''
        }
    
    def get_plugin_examples(self):
        """获取插件示例"""
        return self.examples
    
    def validate_plugin(self, plugin_code):
        """验证插件代码"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # 基本语法检查
            compile(plugin_code, '<string>', 'exec')
            
            # 检查必需的组件
            if 'plugin_class' not in plugin_code:
                validation_result['errors'].append('Missing plugin_class definition')
            
            if 'plugin_info' not in plugin_code:
                validation_result['errors'].append('Missing plugin_info definition')
            
            # 检查基类继承
            if 'BasePlugin' not in plugin_code:
                validation_result['warnings'].append('Plugin should inherit from BasePlugin')
            
        except SyntaxError as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f'Syntax error: {e}')
        
        return validation_result
```

### 10.4 插件市场和生态系统

```python
# src/simtradelab/plugins/marketplace/plugin_marketplace.py
class PluginMarketplace:
    """插件市场"""
    
    def __init__(self, config):
        self.config = config
        self.registry_url = config.get('registry_url', 'https://plugins.simtradelab.com')
        self.local_plugins = {}
        self.remote_plugins = {}
        self.installed_plugins = self._load_installed_plugins()
        
    def search_plugins(self, query, category=None, sort_by='popularity'):
        """搜索插件"""
        # 搜索本地插件
        local_results = self._search_local_plugins(query, category)
        
        # 搜索远程插件
        remote_results = self._search_remote_plugins(query, category, sort_by)
        
        # 合并结果
        all_results = local_results + remote_results
        
        # 去重和排序
        unique_results = self._deduplicate_results(all_results)
        sorted_results = self._sort_results(unique_results, sort_by)
        
        return sorted_results
    
    def install_plugin(self, plugin_name, version=None):
        """安装插件"""
        # 检查插件是否已安装
        if plugin_name in self.installed_plugins:
            installed_version = self.installed_plugins[plugin_name]['version']
            if version and installed_version != version:
                return self._upgrade_plugin(plugin_name, version)
            else:
                return {'success': True, 'message': 'Plugin already installed'}
        
        # 获取插件信息
        plugin_info = self._get_plugin_info(plugin_name, version)
        if not plugin_info:
            return {'success': False, 'error': 'Plugin not found'}
        
        # 检查依赖
        dependencies = plugin_info.get('dependencies', [])
        dependency_result = self._check_dependencies(dependencies)
        if not dependency_result['satisfied']:
            return {'success': False, 'error': 'Dependency check failed', 'details': dependency_result}
        
        # 下载插件
        download_result = self._download_plugin(plugin_name, version)
        if not download_result['success']:
            return download_result
        
        # 安装插件
        install_result = self._install_plugin_files(plugin_name, download_result['files'])
        if not install_result['success']:
            return install_result
        
        # 更新安装记录
        self.installed_plugins[plugin_name] = {
            'version': version or plugin_info['version'],
            'installed_at': datetime.now(),
            'info': plugin_info
        }
        self._save_installed_plugins()
        
        return {'success': True, 'message': f'Plugin {plugin_name} installed successfully'}
    
    def uninstall_plugin(self, plugin_name):
        """卸载插件"""
        if plugin_name not in self.installed_plugins:
            return {'success': False, 'error': 'Plugin not installed'}
        
        # 检查依赖关系
        dependents = self._get_plugin_dependents(plugin_name)
        if dependents:
            return {
                'success': False,
                'error': 'Cannot uninstall plugin with dependents',
                'dependents': dependents
            }
        
        # 卸载插件文件
        uninstall_result = self._uninstall_plugin_files(plugin_name)
        if not uninstall_result['success']:
            return uninstall_result
        
        # 更新安装记录
        del self.installed_plugins[plugin_name]
        self._save_installed_plugins()
        
        return {'success': True, 'message': f'Plugin {plugin_name} uninstalled successfully'}
    
    def update_plugin(self, plugin_name):
        """更新插件"""
        if plugin_name not in self.installed_plugins:
            return {'success': False, 'error': 'Plugin not installed'}
        
        # 获取最新版本信息
        latest_info = self._get_plugin_info(plugin_name)
        if not latest_info:
            return {'success': False, 'error': 'Plugin not found in registry'}
        
        current_version = self.installed_plugins[plugin_name]['version']
        latest_version = latest_info['version']
        
        if current_version == latest_version:
            return {'success': True, 'message': 'Plugin is already up to date'}
        
        # 执行更新
        return self._upgrade_plugin(plugin_name, latest_version)
    
    def list_installed_plugins(self):
        """列出已安装插件"""
        return dict(self.installed_plugins)
    
    def get_plugin_info(self, plugin_name):
        """获取插件详细信息"""
        # 先查找本地
        if plugin_name in self.installed_plugins:
            return self.installed_plugins[plugin_name]['info']
        
        # 查找远程
        return self._get_plugin_info(plugin_name)
    
    def publish_plugin(self, plugin_package):
        """发布插件"""
        # 验证插件包
        validation_result = self._validate_plugin_package(plugin_package)
        if not validation_result['valid']:
            return {'success': False, 'error': 'Plugin validation failed', 'details': validation_result}
        
        # 上传插件
        upload_result = self._upload_plugin(plugin_package)
        if not upload_result['success']:
            return upload_result
        
        # 更新本地注册表
        self._update_local_registry(plugin_package)
        
        return {'success': True, 'message': 'Plugin published successfully'}
    
    def _search_local_plugins(self, query, category):
        """搜索本地插件"""
        results = []
        
        for plugin_name, plugin_info in self.local_plugins.items():
            if self._matches_search(plugin_info, query, category):
                results.append({
                    'name': plugin_name,
                    'info': plugin_info,
                    'source': 'local'
                })
        
        return results
    
    def _search_remote_plugins(self, query, category, sort_by):
        """搜索远程插件"""
        try:
            import requests
            
            params = {
                'q': query,
                'category': category,
                'sort': sort_by
            }
            
            response = requests.get(f"{self.registry_url}/search", params=params)
            response.raise_for_status()
            
            remote_results = response.json()
            
            return [
                {
                    'name': result['name'],
                    'info': result,
                    'source': 'remote'
                }
                for result in remote_results
            ]
        except Exception as e:
            logger.error(f"Failed to search remote plugins: {e}")
            return []
    
    def _matches_search(self, plugin_info, query, category):
        """检查插件是否匹配搜索条件"""
        # 检查分类
        if category and plugin_info.get('category') != category:
            return False
        
        # 检查查询词
        if query:
            searchable_text = ' '.join([
                plugin_info.get('name', ''),
                plugin_info.get('description', ''),
                ' '.join(plugin_info.get('tags', []))
            ]).lower()
            
            if query.lower() not in searchable_text:
                return False
        
        return True
    
    def _get_plugin_info(self, plugin_name, version=None):
        """获取插件信息"""
        try:
            import requests
            
            url = f"{self.registry_url}/plugins/{plugin_name}"
            if version:
                url += f"/{version}"
            
            response = requests.get(url)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get plugin info: {e}")
            return None
    
    def _check_dependencies(self, dependencies):
        """检查依赖关系"""
        satisfied = True
        missing = []
        
        for dependency in dependencies:
            if isinstance(dependency, str):
                # 简单依赖
                if not self._is_dependency_satisfied(dependency):
                    satisfied = False
                    missing.append(dependency)
            elif isinstance(dependency, dict):
                # 复杂依赖
                name = dependency['name']
                version = dependency.get('version')
                
                if not self._is_dependency_satisfied(name, version):
                    satisfied = False
                    missing.append(dependency)
        
        return {
            'satisfied': satisfied,
            'missing': missing
        }
    
    def _is_dependency_satisfied(self, name, version=None):
        """检查单个依赖是否满足"""
        # 检查是否为已安装的插件
        if name in self.installed_plugins:
            if version:
                installed_version = self.installed_plugins[name]['version']
                return self._version_matches(installed_version, version)
            return True
        
        # 检查是否为系统依赖
        try:
            import importlib
            importlib.import_module(name)
            return True
        except ImportError:
            return False
    
    def _version_matches(self, installed_version, required_version):
        """检查版本是否匹配"""
        # 简化的版本比较
        return installed_version == required_version
    
    def _download_plugin(self, plugin_name, version):
        """下载插件"""
        try:
            import requests
            
            url = f"{self.registry_url}/plugins/{plugin_name}/download"
            if version:
                url += f"/{version}"
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # 保存到临时文件
            import tempfile
            import zipfile
            
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            # 解压文件
            with zipfile.ZipFile(tmp_file_path, 'r') as zip_ref:
                files = {}
                for file_info in zip_ref.infolist():
                    if not file_info.is_dir():
                        files[file_info.filename] = zip_ref.read(file_info)
            
            # 清理临时文件
            os.unlink(tmp_file_path)
            
            return {'success': True, 'files': files}
        except Exception as e:
            logger.error(f"Failed to download plugin: {e}")
            return {'success': False, 'error': str(e)}
    
    def _install_plugin_files(self, plugin_name, files):
        """安装插件文件"""
        try:
            plugin_dir = os.path.join(self.config.get('plugins_dir', './plugins'), plugin_name)
            os.makedirs(plugin_dir, exist_ok=True)
            
            for file_path, file_content in files.items():
                full_path = os.path.join(plugin_dir, file_path)
                
                # 创建目录
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # 写入文件
                with open(full_path, 'wb') as f:
                    f.write(file_content)
            
            return {'success': True}
        except Exception as e:
            logger.error(f"Failed to install plugin files: {e}")
            return {'success': False, 'error': str(e)}
    
    def _load_installed_plugins(self):
        """加载已安装插件记录"""
        try:
            registry_file = os.path.join(
                self.config.get('plugins_dir', './plugins'),
                'installed_plugins.json'
            )
            
            if os.path.exists(registry_file):
                with open(registry_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load installed plugins: {e}")
        
        return {}
    
    def _save_installed_plugins(self):
        """保存已安装插件记录"""
        try:
            registry_file = os.path.join(
                self.config.get('plugins_dir', './plugins'),
                'installed_plugins.json'
            )
            
            os.makedirs(os.path.dirname(registry_file), exist_ok=True)
            
            with open(registry_file, 'w') as f:
                json.dump(self.installed_plugins, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save installed plugins: {e}")
```

## 11. 完整目录结构

```
src/simtradelab/
├── core/                           # 核心框架
│   ├── __init__.py
│   ├── engine.py                   # 核心引擎
│   ├── context.py                  # 上下文管理
│   ├── portfolio.py                # 投资组合
│   ├── trading.py                  # 基础交易
│   ├── plugin_manager.py           # 插件管理器
│   └── event_bus.py                # 事件总线
├── adapters/                       # 平台适配层
│   ├── __init__.py
│   ├── ptrade/                     # PTrade适配器
│   │   ├── __init__.py
│   │   ├── adapter.py              # PTrade API适配器
│   │   ├── compatibility.py        # 版本兼容处理
│   │   └── api_router.py           # API路由器
│   └── goldminer/                  # 掘金适配器（预留）
│       ├── __init__.py
│       └── adapter.py              # 掘金API适配器
├── plugins/                        # 插件系统
│   ├── __init__.py
│   ├── base.py                     # 插件基类
│   ├── lifecycle/                  # 生命周期管理
│   │   ├── __init__.py
│   │   ├── plugin_lifecycle_manager.py  # 生命周期管理器
│   │   └── state_manager.py        # 状态管理器
│   ├── security/                   # 安全和认证
│   │   ├── __init__.py
│   │   ├── plugin_sandbox.py       # 沙箱系统
│   │   ├── auth_service.py         # 认证服务
│   │   ├── api_gateway.py          # API网关
│   │   └── permission_manager.py   # 权限管理
│   ├── config/                     # 配置管理
│   │   ├── __init__.py
│   │   ├── dynamic_config_center.py  # 动态配置中心
│   │   └── config_watcher.py       # 配置监听器
│   ├── monitoring/                 # 监控系统
│   │   ├── __init__.py
│   │   ├── plugin_monitor.py       # 插件监控
│   │   ├── alert_manager.py        # 告警管理
│   │   └── metrics_collector.py    # 指标收集器
│   ├── data/                       # 数据系统
│   │   ├── __init__.py
│   │   ├── cold_hot_data_manager.py  # 冷热数据管理
│   │   ├── distributed_cache.py    # 分布式缓存
│   │   ├── access_tracker.py       # 访问追踪
│   │   └── data_sources/           # 数据源插件
│   │       ├── __init__.py
│   │       ├── base.py             # 数据源基类
│   │       ├── akshare_plugin.py   # AkShare数据源
│   │       ├── tushare_plugin.py   # Tushare数据源
│   │       └── csv_plugin.py       # CSV数据源
│   ├── strategy/                   # 策略系统
│   │   ├── __init__.py
│   │   ├── multi_strategy_coordinator.py  # 多策略协调
│   │   ├── dynamic_weight_manager.py  # 动态权重管理
│   │   ├── strategy_performance_tracker.py  # 性能追踪
│   │   └── template_generator.py   # 模板生成器
│   ├── risk/                       # 风险管理
│   │   ├── __init__.py
│   │   ├── rule_engine.py          # 规则引擎
│   │   ├── predefined_rules.py     # 预定义规则
│   │   ├── rule_manager.py         # 规则管理器
│   │   └── portfolio_risk_manager.py  # 投资组合风险管理
│   ├── visualization/              # 可视化系统
│   │   ├── __init__.py
│   │   ├── base_visualization.py   # 可视化基类
│   │   ├── strategy_performance_viz.py  # 策略性能可视化
│   │   ├── interactive_kline.py    # 交互式K线图
│   │   ├── risk_visualization.py   # 风险可视化
│   │   └── dashboard_generator.py  # 仪表板生成器
│   ├── integration/                # 集成插件
│   │   ├── __init__.py
│   │   ├── api_service.py          # API服务接口
│   │   ├── web_bridge.py           # Web前端桥接
│   │   ├── export_tools.py         # 数据导出工具
│   │   └── third_party_integrations.py  # 第三方集成
│   ├── sdk/                        # 开发SDK
│   │   ├── __init__.py
│   │   ├── plugin_sdk.py           # 插件SDK
│   │   ├── template_generator.py   # 模板生成器
│   │   └── validator.py            # 验证器
│   └── marketplace/                # 插件市场
│       ├── __init__.py
│       ├── plugin_marketplace.py   # 插件市场
│       ├── registry.py             # 插件注册表
│       └── package_manager.py      # 包管理器
├── config/                         # 配置管理
│   ├── __init__.py
│   ├── config_manager.py           # 配置管理器
│   ├── plugin_config.py            # 插件配置
│   └── schema_validator.py         # 配置模式验证
├── utils/                          # 工具类
│   ├── __init__.py
│   ├── exceptions.py               # 异常定义
│   ├── validators.py               # 数据验证
│   ├── cache.py                    # 缓存工具
│   ├── logger.py                   # 日志工具
│   └── helpers.py                  # 辅助函数
├── tests/                          # 测试代码
│   ├── __init__.py
│   ├── test_core/                  # 核心测试
│   │   ├── test_engine.py
│   │   ├── test_context.py
│   │   └── test_plugin_manager.py
│   ├── test_plugins/               # 插件测试
│   │   ├── test_lifecycle.py
│   │   ├── test_security.py
│   │   ├── test_data.py
│   │   ├── test_strategy.py
│   │   ├── test_risk.py
│   │   └── test_visualization.py
│   ├── test_adapters/              # 适配器测试
│   │   └── test_ptrade_adapter.py
│   └── test_integration/           # 集成测试
│       ├── test_api_service.py
│       └── test_end_to_end.py
└── docs/                           # 文档
    ├── __init__.py
    ├── plugin_development_guide.md
    ├── api_reference.md
    ├── configuration_guide.md
    └── examples/
        ├── basic_plugin.py
        ├── data_source_plugin.py
        └── visualization_plugin.py
```

## 12. 配置文件系统

### 12.1 主配置文件

```yaml
# config/simtradelab_v4_config.yaml
system:
  name: "SimTradeLab v4.0"
  version: "4.0.0"
  mode: "production"  # development, testing, production
  debug: false
  log_level: "INFO"

# 核心引擎配置
engine:
  max_concurrent_strategies: 10
  event_queue_size: 10000
  performance_mode: true
  optimization_level: "high"

# 插件系统配置
plugins:
  auto_load: true
  plugins_dir: "./plugins"
  hot_reload: true
  security_level: "high"  # low, medium, high
  
  # 插件生命周期管理
  lifecycle:
    enable_hot_plugging: true
    state_migration: true
    automatic_recovery: true
    max_retry_attempts: 3
    
  # 插件安全配置
  security:
    sandbox_mode: "process"  # thread, process, container
    default_permissions:
      - "read"
      - "compute"
    resource_limits:
      memory: "512MB"
      cpu: "50%"
      network: false
      
# 数据系统配置
data:
  # 冷热数据分离
  cold_hot_separation:
    enabled: true
    hot_storage:
      type: "memory+ssd"
      memory_size: "2GB"
      ssd_path: "./cache/hot"
      ttl: 3600
    warm_storage:
      type: "ssd+database"
      ssd_path: "./cache/warm"
      ttl: 86400
    cold_storage:
      type: "object+archive"
      object_storage_path: "./cache/cold"
      ttl: 31536000
      
  # 分布式缓存
  distributed_cache:
    enabled: true
    type: "redis"
    nodes:
      - id: "node1"
        host: "localhost"
        port: 6379
        type: "redis"
      - id: "node2"
        host: "localhost"
        port: 6380
        type: "redis"
    replication_factor: 2
    
# 动态配置中心
config_center:
  enabled: true
  source: "file"  # file, etcd, consul
  watch_enabled: true
  auto_reload: true
  backup_enabled: true
  history_limit: 100

# 监控系统
monitoring:
  enabled: true
  metrics_collection_interval: 10
  alert_thresholds:
    cpu_usage: 80
    memory_usage: 90
    error_rate: 5
    response_time: 1000
  notifications:
    email:
      enabled: false
      smtp_server: "smtp.example.com"
      smtp_port: 587
    slack:
      enabled: false
      webhook_url: "${SLACK_WEBHOOK_URL}"
      
# 多策略协调
multi_strategy:
  enabled: true
  max_strategies: 5
  weight_adjustment:
    method: "performance_based"  # performance_based, risk_parity, sharpe_ratio, kelly_criterion
    lookback_period: 30
    rebalance_threshold: 0.05
    min_weight: 0.05
    max_weight: 0.50
    
# 风险控制
risk_control:
  enabled: true
  rule_engine:
    enabled: true
    default_rules:
      - "position_concentration_limit"
      - "portfolio_drawdown_limit"
      - "leverage_limit"
    custom_rules: []
  real_time_monitoring: true
  
# 可视化系统
visualization:
  enabled: true
  backend: "plotly"  # plotly, matplotlib, bokeh
  theme: "default"  # default, dark, light
  export_formats: ["html", "png", "pdf"]
  interactive_features: true
  
# API服务
api_service:
  enabled: true
  host: "0.0.0.0"
  port: 8000
  
  # 认证配置
  authentication:
    enabled: true
    jwt_secret: "${JWT_SECRET}"
    jwt_expiration: 3600
    oauth2_providers:
      github:
        client_id: "${GITHUB_CLIENT_ID}"
        client_secret: "${GITHUB_CLIENT_SECRET}"
        
  # 访问频率限制
  rate_limiting:
    enabled: true
    default_limit:
      requests: 100
      window: 3600
    endpoints:
      "/api/data":
        requests: 50
        window: 60
      "/api/trading":
        requests: 20
        window: 60
        
# 插件市场
marketplace:
  enabled: true
  registry_url: "https://plugins.simtradelab.com"
  auto_update_check: true
  download_timeout: 300
  
# 第三方集成
integrations:
  streamlit:
    enabled: false
    port: 8501
    auto_launch: false
  jupyter:
    enabled: false
    port: 8888
  web_dashboard:
    enabled: false
    port: 8080
```

### 12.2 插件配置模板

```yaml
# config/plugin_templates/data_source_plugin.yaml
plugin_info:
  name: "example_data_source"
  version: "1.0.0"
  type: "data_source"
  description: "示例数据源插件"
  author: "Your Name"
  
config:
  # 数据源特定配置
  api_url: "https://api.example.com"
  api_key: "${API_KEY}"
  timeout: 30
  retry_attempts: 3
  
  # 缓存配置
  cache:
    enabled: true
    ttl: 3600
    max_size: "100MB"
    
  # 数据格式配置
  data_format:
    datetime_format: "%Y-%m-%d %H:%M:%S"
    decimal_places: 4
    
# 安全配置
security:
  permissions:
    - "data_access:read"
    - "network:access"
  resource_limits:
    memory: "256MB"
    cpu: "25%"
    network: true
    
# 监控配置
monitoring:
  enabled: true
  metrics:
    - "request_count"
    - "response_time"
    - "error_rate"
  alerts:
    - condition: "error_rate > 5"
      action: "disable"
```

## 13. 实施指南和最佳实践

### 13.1 分阶段实施计划

#### 第一阶段：核心基础设施（1-2个月）
1. **插件基础框架**
   - 实现BasePlugin和插件管理器
   - 建立事件总线系统
   - 实现基本的生命周期管理

2. **PTrade兼容层**
   - 完成PTrade适配器
   - 实现API路由系统
   - 保证100%兼容性

3. **配置管理系统**
   - 实现动态配置中心
   - 建立配置监听和热更新机制

#### 第二阶段：核心插件开发（2-3个月）
1. **数据系统插件**
   - 实现冷热数据分离
   - 建立分布式缓存系统
   - 完成数据访问追踪器

2. **监控和安全插件**
   - 实现插件监控系统
   - 建立沙箱安全机制
   - 完成告警管理器

3. **多策略协调插件**
   - 实现策略协调管理器
   - 建立动态权重调整机制

#### 第三阶段：高级功能（2个月）
1. **风险控制引擎**
   - 实现规则引擎
   - 建立预定义规则库
   - 完成自定义规则支持

2. **可视化系统**
   - 实现可视化插件基类
   - 建立交互式图表系统
   - 完成仪表板生成器

#### 第四阶段：生态系统（1-2个月）
1. **API安全服务**
   - 实现OAuth2/JWT认证
   - 建立API网关和权限管理
   - 完成访问频率限制

2. **开发者生态**
   - 实现插件SDK
   - 建立插件市场
   - 完成文档和示例

### 13.2 技术实施要点

#### 13.2.1 架构原则
```python
# 示例：插件架构原则实现
class ArchitecturalPrinciples:
    """架构原则指导"""
    
    PRINCIPLES = {
        'single_responsibility': '每个插件只负责一个功能域',
        'open_closed': '对扩展开放，对修改封闭',
        'dependency_inversion': '依赖抽象而非具体实现',
        'interface_segregation': '客户不应该依赖不需要的接口',
        'liskov_substitution': '子类必须能够替换其基类'
    }
    
    @staticmethod
    def validate_plugin_design(plugin_class):
        """验证插件设计是否符合架构原则"""
        violations = []
        
        # 检查单一职责原则
        if len(plugin_class.get_capabilities()) > 3:
            violations.append('违反单一职责原则：功能过多')
        
        # 检查接口隔离原则
        unused_methods = plugin_class.get_unused_interface_methods()
        if unused_methods:
            violations.append(f'违反接口隔离原则：未使用方法 {unused_methods}')
        
        return violations
```

#### 13.2.2 性能优化策略
```python
# 示例：性能优化实现
class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.connection_pool = ConnectionPool()
        self.async_executor = AsyncExecutor()
    
    def optimize_data_access(self, data_request):
        """优化数据访问"""
        # 1. 缓存检查
        cache_key = self._generate_cache_key(data_request)
        cached_data = self.cache_manager.get(cache_key)
        if cached_data:
            return cached_data
        
        # 2. 并发加载
        if data_request.supports_parallel_loading():
            return self._parallel_load_data(data_request)
        
        # 3. 异步处理
        return self.async_executor.submit(
            self._load_data_async,
            data_request
        )
    
    def _parallel_load_data(self, request):
        """并行加载数据"""
        from concurrent.futures import ThreadPoolExecutor
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            tasks = request.split_into_parallel_tasks()
            futures = [
                executor.submit(self._load_single_task, task)
                for task in tasks
            ]
            
            results = [future.result() for future in futures]
            return self._merge_results(results)
```

#### 13.2.3 错误处理和恢复
```python
# 示例：错误处理策略
class ErrorRecoveryManager:
    """错误恢复管理器"""
    
    def __init__(self):
        self.retry_policies = {}
        self.circuit_breakers = {}
        self.fallback_handlers = {}
    
    def handle_plugin_error(self, plugin_name, error, context):
        """处理插件错误"""
        error_type = type(error).__name__
        
        # 1. 记录错误
        self._log_error(plugin_name, error, context)
        
        # 2. 检查熔断器
        circuit_breaker = self.circuit_breakers.get(plugin_name)
        if circuit_breaker and circuit_breaker.is_open():
            return self._execute_fallback(plugin_name, context)
        
        # 3. 重试策略
        retry_policy = self.retry_policies.get(plugin_name)
        if retry_policy and retry_policy.should_retry(error):
            return self._retry_plugin_operation(plugin_name, context)
        
        # 4. 降级处理
        return self._degrade_service(plugin_name, error, context)
    
    def _retry_plugin_operation(self, plugin_name, context):
        """重试插件操作"""
        import time
        
        retry_policy = self.retry_policies[plugin_name]
        
        for attempt in range(retry_policy.max_attempts):
            try:
                time.sleep(retry_policy.get_delay(attempt))
                return self._execute_plugin(plugin_name, context)
            except Exception as e:
                if attempt == retry_policy.max_attempts - 1:
                    raise e
                continue
```

### 13.3 开发最佳实践

#### 13.3.1 插件开发规范
```python
# 示例：插件开发模板
class PluginDevelopmentTemplate:
    """插件开发模板"""
    
    PLUGIN_STRUCTURE = {
        'metadata': {
            'name': 'plugin_name',
            'version': '1.0.0',
            'description': 'Plugin description',
            'author': 'Author name',
            'dependencies': [],
            'permissions': []
        },
        'configuration': {
            'schema': {},
            'defaults': {},
            'validation': {}
        },
        'implementation': {
            'main_class': 'PluginClass',
            'interfaces': [],
            'callbacks': []
        },
        'testing': {
            'unit_tests': [],
            'integration_tests': [],
            'performance_tests': []
        },
        'documentation': {
            'readme': 'README.md',
            'api_docs': 'docs/api.md',
            'examples': 'examples/'
        }
    }
    
    @staticmethod
    def generate_plugin_scaffold(plugin_name, plugin_type):
        """生成插件脚手架"""
        scaffold = {
            'directory': f'plugins/{plugin_name}',
            'files': {}
        }
        
        # 生成主文件
        scaffold['files']['__init__.py'] = \
            PluginDevelopmentTemplate._generate_init_file(plugin_name)
        
        # 生成主类文件
        scaffold['files'][f'{plugin_name}.py'] = \
            PluginDevelopmentTemplate._generate_main_class(plugin_name, plugin_type)
        
        # 生成配置文件
        scaffold['files']['config.yaml'] = \
            PluginDevelopmentTemplate._generate_config_file(plugin_name)
        
        # 生成测试文件
        scaffold['files']['tests/test_main.py'] = \
            PluginDevelopmentTemplate._generate_test_file(plugin_name)
        
        return scaffold
```

#### 13.3.2 测试策略
```python
# 示例：测试框架
class PluginTestingFramework:
    """插件测试框架"""
    
    def __init__(self):
        self.test_environment = TestEnvironment()
        self.mock_factory = MockFactory()
        self.assertion_helpers = AssertionHelpers()
    
    def create_plugin_test_suite(self, plugin_class):
        """创建插件测试套件"""
        test_suite = TestSuite()
        
        # 1. 单元测试
        unit_tests = self._generate_unit_tests(plugin_class)
        test_suite.add_tests(unit_tests)
        
        # 2. 集成测试
        integration_tests = self._generate_integration_tests(plugin_class)
        test_suite.add_tests(integration_tests)
        
        # 3. 性能测试
        performance_tests = self._generate_performance_tests(plugin_class)
        test_suite.add_tests(performance_tests)
        
        return test_suite
    
    def _generate_unit_tests(self, plugin_class):
        """生成单元测试"""
        tests = []
        
        # 测试插件初始化
        tests.append(self._create_initialization_test(plugin_class))
        
        # 测试核心功能
        for method in plugin_class.get_public_methods():
            tests.append(self._create_method_test(plugin_class, method))
        
        # 测试错误处理
        tests.append(self._create_error_handling_test(plugin_class))
        
        return tests
```

### 13.4 部署和运维指南

#### 13.4.1 容器化部署
```dockerfile
# Dockerfile示例
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY config/ ./config/
COPY plugins/ ./plugins/

# 设置环境变量
ENV PYTHONPATH=/app/src
ENV SIMTRADELAB_CONFIG=/app/config/production.yaml

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "simtradelab.cli", "--mode", "production"]
```

#### 13.4.2 Kubernetes部署配置
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: simtradelab-v4
  labels:
    app: simtradelab
    version: v4.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: simtradelab
      version: v4.0
  template:
    metadata:
      labels:
        app: simtradelab
        version: v4.0
    spec:
      containers:
      - name: simtradelab
        image: simtradelab:v4.0
        ports:
        - containerPort: 8000
        env:
        - name: SIMTRADELAB_MODE
          value: "production"
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: simtradelab-secrets
              key: database-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: simtradelab-service
spec:
  selector:
    app: simtradelab
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### 13.4.3 监控和日志配置
```yaml
# monitoring-config.yaml
prometheus:
  enabled: true
  endpoint: "/metrics"
  scrape_interval: "30s"
  
grafana:
  enabled: true
  dashboards:
    - "simtradelab-system-metrics"
    - "simtradelab-plugin-metrics"
    - "simtradelab-business-metrics"
    
logging:
  level: "INFO"
  format: "json"
  outputs:
    - type: "file"
      path: "/var/log/simtradelab.log"
      rotation: "daily"
      retention: "30d"
    - type: "elasticsearch"
      url: "http://elasticsearch:9200"
      index: "simtradelab-logs"
    
tracing:
  enabled: true
  service_name: "simtradelab-v4"
  jaeger_endpoint: "http://jaeger:14268/api/traces"
```

### 13.5 迁移指南

#### 13.5.1 从v3.x到v4.0的迁移
```python
# 迁移工具示例
class MigrationTool:
    """v3.x到v4.0迁移工具"""
    
    def __init__(self):
        self.config_migrator = ConfigMigrator()
        self.strategy_migrator = StrategyMigrator()
        self.data_migrator = DataMigrator()
    
    def migrate_project(self, v3_project_path, v4_project_path):
        """迁移整个项目"""
        migration_plan = self._create_migration_plan(v3_project_path)
        
        for step in migration_plan:
            print(f"执行迁移步骤: {step.description}")
            
            if step.type == 'config':
                self.config_migrator.migrate(step.source, step.target)
            elif step.type == 'strategy':
                self.strategy_migrator.migrate(step.source, step.target)
            elif step.type == 'data':
                self.data_migrator.migrate(step.source, step.target)
            
            print(f"✅ {step.description} 完成")
        
        # 验证迁移结果
        validation_result = self._validate_migration(v4_project_path)
        return validation_result
    
    def _create_migration_plan(self, project_path):
        """创建迁移计划"""
        plan = []
        
        # 1. 配置迁移
        plan.append(MigrationStep(
            type='config',
            description='迁移配置文件',
            source=f'{project_path}/config.yaml',
            target='config/simtradelab_v4_config.yaml'
        ))
        
        # 2. 策略迁移
        strategy_files = glob.glob(f'{project_path}/strategies/*.py')
        for strategy_file in strategy_files:
            plan.append(MigrationStep(
                type='strategy',
                description=f'迁移策略文件 {os.path.basename(strategy_file)}',
                source=strategy_file,
                target=f'strategies/{os.path.basename(strategy_file)}'
            ))
        
        # 3. 数据迁移
        plan.append(MigrationStep(
            type='data',
            description='迁移历史数据',
            source=f'{project_path}/data',
            target='data'
        ))
        
        return plan
```

### 13.6 性能基准和监控

#### 13.6.1 性能基准
```python
# 性能基准测试
class PerformanceBenchmark:
    """性能基准测试"""
    
    BENCHMARKS = {
        'plugin_loading': {
            'target': '< 100ms per plugin',
            'description': '插件加载时间'
        },
        'data_access': {
            'target': '< 50ms for cached data',
            'description': '数据访问延迟'
        },
        'strategy_execution': {
            'target': '< 10ms per strategy per tick',
            'description': '策略执行时间'
        },
        'memory_usage': {
            'target': '< 1GB for 10 concurrent strategies',
            'description': '内存使用量'
        },
        'throughput': {
            'target': '> 1000 ticks/second',
            'description': '数据处理吞吐量'
        }
    }
    
    def run_benchmark_suite(self):
        """运行完整基准测试套件"""
        results = {}
        
        for benchmark_name, benchmark_config in self.BENCHMARKS.items():
            print(f"运行基准测试: {benchmark_name}")
            
            result = self._run_single_benchmark(benchmark_name)
            results[benchmark_name] = {
                'target': benchmark_config['target'],
                'actual': result,
                'passed': self._evaluate_result(result, benchmark_config['target'])
            }
            
            status = "✅ PASS" if results[benchmark_name]['passed'] else "❌ FAIL"
            print(f"  {status} - {result}")
        
        return results
```

## 14. 总结

### 14.1 v4.0架构核心优势

#### 🚀 **性能提升**
- **50-70%** 回测速度提升（通过向量化计算）
- **60-80%** 数据加载速度提升（并发加载）
- **30-40%** 内存使用减少（优化算法）
- **智能缓存**系统减少重复计算

#### 🔧 **插件化架构**
- **热插拔**支持，无需重启系统
- **多级安全沙箱**（线程/进程/容器）
- **动态权重调整**，策略自适应优化
- **分布式缓存**，支持集群扩展

#### 🛡️ **企业级特性**
- **OAuth2/JWT**认证体系
- **自定义风险规则引擎**
- **实时监控告警**系统
- **完整的API网关**和权限管理

#### 🔄 **100% PTrade兼容**
- **无缝迁移**现有策略代码
- **完整API覆盖**所有PTrade功能
- **向后兼容**保证升级平滑

### 14.2 技术创新点

1. **插件生命周期管理**：支持热插拔、版本升级、状态迁移
2. **冷热数据分离**：智能数据分层，访问模式自学习
3. **多策略协同**：动态权重调整，风险分散优化
4. **规则引擎**：可编程风险控制，实时策略保护
5. **开发者生态**：完整SDK、插件市场、模板系统

### 14.3 商业价值

#### 💼 **降本增效**
- 开发效率提升**3-5倍**
- 系统维护成本降低**60%**
- 硬件资源利用率提升**40%**

#### 📈 **业务增长**
- 支持更复杂的交易策略
- 实现真正的多策略组合管理
- 提供企业级风险控制能力

#### 🔮 **技术前瞻**
- 模块化架构便于功能扩展
- 云原生设计支持弹性伸缩
- 开放生态促进创新发展

### 14.4 发展路线图

#### 短期目标（3-6个月）
- 完成核心插件化架构
- 实现PTrade完全兼容
- 建立基础开发者工具链

#### 中期目标（6-12个月）
- 建设插件市场生态
- 完善监控和运维体系
- 支持更多数据源和交易平台

#### 长期愿景（1-2年）
- 成为量化交易领域标准框架
- 建设完整的开发者社区
- 支持人工智能策略开发

### 14.5 结语

SimTradeLab v4.0代表了量化交易框架的一次重大飞跃。通过完整的插件化架构重构，我们不仅解决了现有的技术债务和性能瓶颈，更为未来的发展奠定了坚实的技术基础。

这个架构设计充分体现了现代软件工程的最佳实践：
- **可扩展性**：插件化设计支持无限扩展
- **可维护性**：模块化架构便于维护升级  
- **可靠性**：多级安全机制保障系统稳定
- **可用性**：完整的文档和工具链降低使用门槛

我们相信，SimTradeLab v4.0将成为量化交易领域的新标杆，为广大量化开发者提供强大而灵活的技术平台，推动整个行业的技术进步和创新发展。

---

**🎯 SimTradeLab v4.0 - 重新定义量化交易框架**

*让量化交易开发更简单、更高效、更安全*

**📅 文档版本**：v4.0.0  
**📝 最后更新**：2024年12月  
**👥 贡献者**：SimTradeLab开发团队