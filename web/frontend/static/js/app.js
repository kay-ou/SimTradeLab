// SimTradeLab Web 前端JavaScript
// 主要功能：页面切换、API调用、数据可视化

// 全局变量
let currentTab = 'dashboard';
let strategyEditor = null;
let currentJobId = null;
let parameterRowCount = 1;
let dataFilesInfo = {}; // 存储数据文件的详细信息

// API基础URL
const API_BASE = '/api';

// 移动端侧边栏切换功能
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('show');
    
    // 点击外部区域关闭侧边栏
    if (sidebar.classList.contains('show')) {
        document.addEventListener('click', closeSidebarOnOutsideClick);
    } else {
        document.removeEventListener('click', closeSidebarOnOutsideClick);
    }
}

function closeSidebarOnOutsideClick(event) {
    const sidebar = document.querySelector('.sidebar');
    const toggleButton = document.querySelector('.sidebar-toggle');
    
    if (!sidebar.contains(event.target) && !toggleButton.contains(event.target)) {
        sidebar.classList.remove('show');
        document.removeEventListener('click', closeSidebarOnOutsideClick);
    }
}

// 初始化代码编辑器
function initCodeEditor() {
    if (strategyEditor) {
        strategyEditor.destroy();
    }
    
    const editorElement = document.getElementById('strategy-code-editor');
    if (editorElement) {
        strategyEditor = ace.edit('strategy-code-editor');
        strategyEditor.setTheme('ace/theme/monokai');
        strategyEditor.session.setMode('ace/mode/python');
        strategyEditor.setOptions({
            fontSize: 14,
            showPrintMargin: false,
            highlightActiveLine: true,
            enableBasicAutocompletion: true,
            enableSnippets: true,
            enableLiveAutocompletion: true,
            wrap: true,
            autoScrollEditorIntoView: true,
            fontFamily: 'JetBrains Mono, Fira Code, Consolas, Monaco, Courier New, monospace'
        });
        
        // 设置默认模板
        strategyEditor.setValue(`# -*- coding: utf-8 -*-
"""
策略模板 - 请在此编写您的交易策略
"""

def initialize(context):
    """
    策略初始化函数
    """
    # 设置基准和股票池
    context.benchmark = '000300.SH'  # 沪深300指数
    context.stocks = ['000001.SZ', '000002.SZ']  # 股票池
    
    # 策略参数
    context.short_window = 5   # 短期均线
    context.long_window = 20   # 长期均线
    
    # 其他初始化逻辑
    pass

def handle_data(context, data):
    """
    每个交易日都会调用的函数
    """
    for stock in context.stocks:
        # 获取历史价格数据
        hist = get_history(context, stock, count=context.long_window, fields=['close'])
        
        if len(hist) < context.long_window:
            continue
            
        # 计算移动平均线
        short_ma = hist['close'].tail(context.short_window).mean()
        long_ma = hist['close'].tail(context.long_window).mean()
        current_price = hist['close'].iloc[-1]
        
        # 获取当前持仓
        current_position = get_position(context, stock)
        
        # 交易逻辑：金叉买入，死叉卖出
        if short_ma > long_ma and current_position == 0:
            # 买入信号
            order_target_percent(context, stock, 0.5)  # 使用50%资金买入
            
        elif short_ma < long_ma and current_position > 0:
            # 卖出信号
            order_target_percent(context, stock, 0)  # 全部卖出

def before_trading_start(context, data):
    """
    每日开盘前调用
    """
    pass

def after_trading_end(context, data):
    """
    每日收盘后调用
    """
    pass
`, 1);
        
        // 同步到hidden textarea
        strategyEditor.on('change', function() {
            document.getElementById('strategy-code').value = strategyEditor.getValue();
        });
        
        // 初始化可调整大小功能
        initResizableEditor();
        
        // 自动调整编辑器大小到窗口
        autoResizeEditor();
        
        // 监听窗口大小变化
        window.addEventListener('resize', autoResizeEditor);
    }
}

// 自动调整编辑器大小
function autoResizeEditor() {
    const container = document.querySelector('.editor-container');
    if (container && !container.classList.contains('editor-fullscreen')) {
        const windowHeight = window.innerHeight;
        const containerTop = container.getBoundingClientRect().top;
        
        // 计算可用高度：窗口高度 - 容器顶部位置 - 底部留白
        const availableHeight = windowHeight - containerTop - 50;
        
        // 设置最小高度为500px，充分利用可用空间
        const targetHeight = Math.max(500, Math.min(availableHeight, windowHeight * 0.7));
        
        container.style.height = targetHeight + 'px';
        container.style.width = '100%'; // 确保宽度充分利用
        
        if (strategyEditor) {
            // 强制编辑器重新计算和渲染
            setTimeout(() => {
                strategyEditor.resize(true);
                strategyEditor.renderer.updateFull(true);
                strategyEditor.renderer.onResize();
            }, 10);
        }
    }
}

// 初始化可调整大小功能
function initResizableEditor() {
    const container = document.querySelector('.editor-container');
    const resizeHandle = document.getElementById('resize-handle');
    
    if (!container || !resizeHandle) return;
    
    let isResizing = false;
    let startX, startY, startWidth, startHeight;
    
    resizeHandle.addEventListener('mousedown', (e) => {
        isResizing = true;
        startX = e.clientX;
        startY = e.clientY;
        startWidth = parseInt(document.defaultView.getComputedStyle(container).width, 10);
        startHeight = parseInt(document.defaultView.getComputedStyle(container).height, 10);
        
        document.addEventListener('mousemove', handleResize);
        document.addEventListener('mouseup', stopResize);
        e.preventDefault();
    });
    
    function handleResize(e) {
        if (!isResizing) return;
        
        const newWidth = startWidth + e.clientX - startX;
        const newHeight = startHeight + e.clientY - startY;
        
        // 设置最小和最大尺寸
        const minWidth = 300;
        const minHeight = 200;
        const maxWidth = window.innerWidth - 100;
        const maxHeight = window.innerHeight - 100;
        
        const finalWidth = Math.max(minWidth, Math.min(maxWidth, newWidth));
        const finalHeight = Math.max(minHeight, Math.min(maxHeight, newHeight));
        
        container.style.width = finalWidth + 'px';
        container.style.height = finalHeight + 'px';
        
        // 确保编辑器内容跟随容器大小变化
        if (strategyEditor) {
            // 延迟执行确保DOM更新完成
            setTimeout(() => {
                strategyEditor.resize(true); // 强制重新计算尺寸
                strategyEditor.renderer.updateFull(true); // 强制重新渲染
                strategyEditor.renderer.onResize(); // 触发resize事件
            }, 10);
        }
    }
    
    function stopResize() {
        isResizing = false;
        document.removeEventListener('mousemove', handleResize);
        document.removeEventListener('mouseup', stopResize);
    }
}

// 切换全屏模式
function toggleEditorFullscreen() {
    const container = document.querySelector('.editor-container');
    const icon = document.getElementById('fullscreen-icon');
    
    if (container.classList.contains('editor-fullscreen')) {
        exitFullscreen();
    } else {
        enterFullscreen();
    }
}

// 进入全屏模式
function enterFullscreen() {
    const container = document.querySelector('.editor-container');
    const icon = document.getElementById('fullscreen-icon');
    
    // 平滑过渡到全屏
    container.style.transition = 'all 0.3s ease';
    container.classList.add('editor-fullscreen');
    icon.className = 'fas fa-compress';
    
    // 创建全屏控制栏
    const overlay = document.createElement('div');
    overlay.className = 'fullscreen-overlay';
    overlay.innerHTML = `
        <div>
            <h5 class="mb-0"><i class="fas fa-code"></i> 策略编辑器 - 全屏模式</h5>
        </div>
        <div class="fullscreen-controls">
            <button onclick="resetEditorSize()" title="重置大小">
                <i class="fas fa-compress-arrows-alt"></i> 重置
            </button>
            <button onclick="saveCurrentStrategy()" title="保存策略">
                <i class="fas fa-save"></i> 保存
            </button>
            <button onclick="exitFullscreen()" title="退出全屏">
                <i class="fas fa-times"></i> 退出全屏
            </button>
        </div>
    `;
    
    document.body.appendChild(overlay);
    
    // 设置全屏样式
    setTimeout(() => {
        container.style.top = '60px';
        container.style.height = 'calc(100vh - 60px)';
        container.style.transition = ''; // 移除过渡效果
        
        if (strategyEditor) {
            setTimeout(() => {
                strategyEditor.resize(true);
                strategyEditor.renderer.updateFull(true);
                strategyEditor.renderer.onResize();
            }, 50);
        }
    }, 10);
    
    // ESC键退出全屏
    document.addEventListener('keydown', handleEscapeKey);
}

// 退出全屏模式
function exitFullscreen() {
    const container = document.querySelector('.editor-container');
    const icon = document.getElementById('fullscreen-icon');
    const overlay = document.querySelector('.fullscreen-overlay');
    
    // 平滑过渡退出全屏
    container.style.transition = 'all 0.3s ease';
    container.classList.remove('editor-fullscreen');
    icon.className = 'fas fa-expand';
    
    if (overlay) {
        overlay.remove();
    }
    
    // 重置样式
    setTimeout(() => {
        container.style.top = '';
        container.style.height = '';
        container.style.transition = ''; // 移除过渡效果
        
        if (strategyEditor) {
            setTimeout(() => {
                strategyEditor.resize(true);
                strategyEditor.renderer.updateFull(true);
                strategyEditor.renderer.onResize();
            }, 50);
        }
    }, 10);
    
    document.removeEventListener('keydown', handleEscapeKey);
}

// ESC键处理
function handleEscapeKey(e) {
    if (e.key === 'Escape') {
        exitFullscreen();
    }
}

// 重置编辑器大小
function resetEditorSize() {
    const container = document.querySelector('.editor-container');
    
    if (container.classList.contains('editor-fullscreen')) {
        exitFullscreen();
    }
    
    container.style.width = '';
    container.style.height = '400px';
    
    if (strategyEditor) {
        strategyEditor.resize();
    }
}

// 工具函数
function showMessage(message, type = 'success') {
    const alertClass = type === 'success' ? 'alert-success' : 
                      type === 'error' ? 'alert-danger' : 'alert-info';
    
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // 临时显示消息
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = alertHtml;
    document.body.prepend(tempDiv.firstElementChild);
    
    // 3秒后自动消失
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) alert.remove();
    }, 3000);
}

function formatDateTime(dateStr) {
    return new Date(dateStr).toLocaleString('zh-CN');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showLoading(elementId) {
    document.getElementById(elementId).innerHTML = '<div class="text-center"><div class="loading-spinner"></div> 加载中...</div>';
}

// 页面切换功能
function showTab(tabName) {
    // 隐藏所有标签页
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    
    // 移除所有导航链接的active类
    document.querySelectorAll('.sidebar .nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // 显示目标标签页
    document.getElementById(tabName + '-tab').style.display = 'block';
    
    // 添加active类到对应导航链接
    event.target.classList.add('active');
    
    currentTab = tabName;
    
    // 在移动端切换页面时自动隐藏侧边栏
    if (window.innerWidth <= 768) {
        const sidebar = document.querySelector('.sidebar');
        sidebar.classList.remove('show');
        document.removeEventListener('click', closeSidebarOnOutsideClick);
    }
    
    // 根据不同页面加载对应数据
    switch(tabName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'strategies':
            loadStrategies();
            // 延迟初始化代码编辑器，确保DOM已渲染
            setTimeout(() => {
                initCodeEditor();
            }, 100);
            break;
        case 'data':
            loadDataSources();
            break;
        case 'backtest':
            loadBacktestOptions();
            break;
        case 'batch':
            loadBatchTestOptions();
            break;
        case 'results':
            loadJobResults();
            break;
    }
}

// 仪表盘功能
async function loadDashboard() {
    try {
        // 加载统计数据
        const [strategies, dataFiles, jobs, reports] = await Promise.all([
            fetch(`${API_BASE}/strategies`).then(r => r.json()),
            fetch(`${API_BASE}/data/files`).then(r => r.json()),
            fetch(`${API_BASE}/jobs`).then(r => r.json()),
            fetch(`${API_BASE}/reports`).then(r => r.json())
        ]);
        
        document.getElementById('strategy-count').textContent = strategies.strategies.length;
        document.getElementById('data-count').textContent = dataFiles.data_files.length;
        document.getElementById('job-count').textContent = jobs.jobs.filter(j => j.status === 'running').length;
        document.getElementById('report-count').textContent = reports.reports.length;
        
        // 显示最近任务
        const recentJobs = jobs.jobs.slice(-5).reverse();
        const jobsHtml = recentJobs.map(job => `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <div>
                    <small class="text-muted">${job.type}</small>
                    <div class="fw-bold">${job.message}</div>
                </div>
                <span class="status-badge status-${job.status}">${job.status}</span>
            </div>
        `).join('');
        document.getElementById('recent-jobs').innerHTML = jobsHtml || '<p class="text-muted">暂无任务</p>';
        
        // 显示数据源状态
        const config = await fetch(`${API_BASE}/config`).then(r => r.json());
        const dataSourceHtml = Object.entries(config.data_sources).map(([name, info]) => `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <small>${name}</small>
                <span class="badge ${info.enabled ? 'bg-success' : 'bg-secondary'}">${info.enabled ? '可用' : '禁用'}</span>
            </div>
        `).join('');
        document.getElementById('data-source-status').innerHTML = dataSourceHtml;
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showMessage('加载仪表盘数据失败', 'error');
    }
}

function refreshDashboard() {
    loadDashboard();
    showMessage('仪表盘已刷新');
}

// 策略管理功能
async function loadStrategies() {
    try {
        showLoading('strategy-list');
        const response = await fetch(`${API_BASE}/strategies`);
        const data = await response.json();
        
        const strategiesHtml = data.strategies.map(strategy => `
            <div class="list-group-item list-group-item-action" onclick="loadStrategy('${strategy.name}')">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${strategy.name}</h6>
                    <small>${formatFileSize(strategy.size)}</small>
                </div>
                <p class="mb-1 text-muted small">${strategy.description || '无描述'}</p>
                <small class="text-muted">修改时间: ${formatDateTime(strategy.modified_at)}</small>
            </div>
        `).join('');
        
        document.getElementById('strategy-list').innerHTML = strategiesHtml || '<p class="text-muted">暂无策略</p>';
        
        // 初始化代码编辑器
        if (!strategyEditor) {
            strategyEditor = CodeMirror.fromTextArea(document.getElementById('strategy-code'), {
                mode: 'python',
                theme: 'material',
                lineNumbers: true,
                lineWrapping: true,
                autoCloseBrackets: true,
                matchBrackets: true,
                indentUnit: 4,
                indentWithTabs: false
            });
        }
        
    } catch (error) {
        console.error('Error loading strategies:', error);
        showMessage('加载策略失败', 'error');
    }
}

async function loadStrategy(strategyName) {
    try {
        const response = await fetch(`${API_BASE}/strategies/${strategyName}`);
        const strategy = await response.json();
        
        document.getElementById('strategy-name').value = strategy.name;
        document.getElementById('strategy-description').value = strategy.description || '';
        strategyEditor.setValue(strategy.code);
        
        // 高亮选中的策略
        document.querySelectorAll('#strategy-list .list-group-item').forEach(item => {
            item.classList.remove('active');
        });
        event.target.classList.add('active');
        
    } catch (error) {
        console.error('Error loading strategy:', error);
        showMessage('加载策略失败', 'error');
    }
}

function createNewStrategy() {
    document.getElementById('strategy-name').value = '';
    document.getElementById('strategy-description').value = '';
    
    const defaultCode = `def initialize(context):
    """策略初始化"""
    # 设置股票池
    g.security = '000001.SZ'
    log.info("策略初始化完成")

def handle_data(context, data):
    """主策略逻辑"""
    security = g.security
    
    # 获取当前价格
    if security in data:
        current_price = data[security]['close']
        log.info(f"当前价格: {current_price}")
        
        # 这里添加你的策略逻辑
        # 例如：order(security, 100)  # 买入100股

def after_trading_end(context, data):
    """盘后处理"""
    total_value = context.portfolio.total_value
    log.info(f"总资产: {total_value}")
`;
    
    strategyEditor.setValue(defaultCode);
    showMessage('已创建新策略模板');
}

async function saveCurrentStrategy() {
    const name = document.getElementById('strategy-name').value.trim();
    const description = document.getElementById('strategy-description').value.trim();
    const code = strategyEditor.getValue();
    
    if (!name) {
        showMessage('请输入策略名称', 'error');
        return;
    }
    
    if (!code.trim()) {
        showMessage('策略代码不能为空', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/strategies`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                description: description,
                code: code
            })
        });
        
        if (response.ok) {
            showMessage('策略保存成功');
            loadStrategies(); // 刷新策略列表
        } else {
            const error = await response.json();
            showMessage(`保存失败: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error saving strategy:', error);
        showMessage('保存策略失败', 'error');
    }
}

async function deleteCurrentStrategy() {
    const name = document.getElementById('strategy-name').value.trim();
    
    if (!name) {
        showMessage('请先选择要删除的策略', 'error');
        return;
    }
    
    if (!confirm(`确定要删除策略 "${name}" 吗？此操作不可恢复。`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/strategies/${name}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showMessage('策略删除成功');
            document.getElementById('strategy-name').value = '';
            document.getElementById('strategy-description').value = '';
            strategyEditor.setValue('');
            loadStrategies(); // 刷新策略列表
        } else {
            const error = await response.json();
            showMessage(`删除失败: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error deleting strategy:', error);
        showMessage('删除策略失败', 'error');
    }
}

// 数据管理功能
let currentDataSources = {};

async function loadDataSources() {
    try {
        const [sources, files] = await Promise.all([
            fetch(`${API_BASE}/data/sources`).then(r => r.json()),
            fetch(`${API_BASE}/data/files`).then(r => r.json())
        ]);
        
        // 保存当前数据源配置
        currentDataSources = sources.data_sources;
        
        // 显示可编辑的数据源配置
        const sourcesHtml = sources.data_sources.map(source => `
            <div class="mb-3 p-3 border rounded data-source-config" data-source="${source.name}">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div>
                        <h6 class="mb-1">${source.name.toUpperCase()}</h6>
                        <small class="text-muted">${source.description}</small>
                    </div>
                    <div class="form-check form-switch">
                        <input class="form-check-input" type="checkbox" id="enable-${source.name}" 
                               ${source.enabled ? 'checked' : ''} 
                               onchange="toggleDataSource('${source.name}', this.checked)">
                        <label class="form-check-label" for="enable-${source.name}">
                            ${source.enabled ? '已启用' : '已禁用'}
                        </label>
                    </div>
                </div>
                ${getDataSourceConfigFields(source)}
            </div>
        `).join('');
        document.getElementById('data-sources-list').innerHTML = sourcesHtml;
        
        // 显示数据文件
        const filesHtml = files.data_files.map(file => `
            <div class="d-flex justify-content-between align-items-center mb-2 p-2 border rounded ${file.source === 'uploaded' ? 'border-success' : ''}">
                <div>
                    <h6 class="mb-1">
                        ${file.source === 'uploaded' ? '<i class="fas fa-upload text-success me-1"></i>' : '<i class="fas fa-file-csv text-primary me-1"></i>'}
                        ${file.name}
                    </h6>
                    <small class="text-muted">列: ${file.columns.join(', ')}</small>
                    <br><small class="text-muted">修改时间: ${formatDateTime(file.modified_at)}</small>
                    ${file.source === 'uploaded' ? '<br><small class="text-success"><i class="fas fa-check"></i> 已上传</small>' : ''}
                </div>
                <div class="text-end">
                    <div><small class="fw-bold">${formatFileSize(file.size)}</small></div>
                    <div class="btn-group-vertical btn-group-sm mt-1">
                        <button class="btn btn-outline-primary" onclick="previewDataFile('${file.name}')">
                            <i class="fas fa-eye"></i> 预览
                        </button>
                        <button class="btn btn-outline-success" onclick="downloadDataFile('${file.name}')">
                            <i class="fas fa-download"></i> 下载
                        </button>
                        <button class="btn btn-outline-danger" onclick="deleteDataFile('${file.name}')">
                            <i class="fas fa-trash"></i> 删除
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
        document.getElementById('data-files-list').innerHTML = filesHtml || '<p class="text-muted">暂无数据文件</p>';
        
    } catch (error) {
        console.error('Error loading data sources:', error);
        showMessage('加载数据源失败', 'error');
    }
}

// 获取数据源配置字段
function getDataSourceConfigFields(source) {
    switch(source.name) {
        case 'tushare':
            return `
                <div class="row">
                    <div class="col-md-12">
                        <label class="form-label">Tushare Token</label>
                        <div class="input-group">
                            <input type="password" class="form-control" id="tushare-token" 
                                   placeholder="请输入Tushare API Token" 
                                   value="${source.token || ''}">
                            <button class="btn btn-outline-secondary" type="button" onclick="togglePasswordVisibility('tushare-token')">
                                <i class="fas fa-eye"></i>
                            </button>
                        </div>
                        <small class="text-muted">
                            请到 <a href="https://tushare.pro/" target="_blank">Tushare官网</a> 注册获取免费Token
                        </small>
                    </div>
                </div>
            `;
        case 'csv':
            return `
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">数据目录</label>
                        <input type="text" class="form-control" id="csv-data-path" 
                               value="${source.data_path || 'data/'}" 
                               placeholder="CSV文件存储目录">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">日期格式</label>
                        <select class="form-select" id="csv-date-format">
                            <option value="%Y-%m-%d" ${(source.date_format === '%Y-%m-%d') ? 'selected' : ''}>YYYY-MM-DD</option>
                            <option value="%Y/%m/%d" ${(source.date_format === '%Y/%m/%d') ? 'selected' : ''}>YYYY/MM/DD</option>
                            <option value="%Y%m%d" ${(source.date_format === '%Y%m%d') ? 'selected' : ''}>YYYYMMDD</option>
                        </select>
                    </div>
                </div>
            `;
        case 'akshare':
            return `
                <div class="row">
                    <div class="col-md-12">
                        <div class="alert alert-info mb-0">
                            <i class="fas fa-info-circle"></i>
                            AkShare是免费的数据源，无需额外配置。支持获取中国股票市场的实时和历史数据。
                        </div>
                    </div>
                </div>
            `;
        default:
            return '';
    }
}

// 切换数据源启用状态
function toggleDataSource(sourceName, enabled) {
    const label = document.querySelector(`label[for="enable-${sourceName}"]`);
    label.textContent = enabled ? '已启用' : '已禁用';
    
    // 更新本地配置
    const source = currentDataSources.find(s => s.name === sourceName);
    if (source) {
        source.enabled = enabled;
    }
}

// 切换密码可见性
function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    const icon = input.nextElementSibling.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

// 保存数据源配置
async function saveDataSourceConfig() {
    try {
        const config = {};
        
        // 收集所有数据源配置
        currentDataSources.forEach(source => {
            const sourceConfig = { ...source };
            
            // 根据数据源类型收集特定配置
            switch(source.name) {
                case 'tushare':
                    const token = document.getElementById('tushare-token')?.value;
                    if (token) {
                        sourceConfig.token = token;
                    }
                    break;
                case 'csv':
                    const dataPath = document.getElementById('csv-data-path')?.value;
                    const dateFormat = document.getElementById('csv-date-format')?.value;
                    if (dataPath) sourceConfig.data_path = dataPath;
                    if (dateFormat) sourceConfig.date_format = dateFormat;
                    break;
            }
            
            config[source.name] = sourceConfig;
        });
        
        console.log('Saving config:', config); // Debug log
        
        // 发送配置到后端
        const response = await fetch(`${API_BASE}/config/data-sources`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('Save result:', result); // Debug log
            showMessage('数据源配置保存成功');
        } else {
            const error = await response.json();
            console.error('Save error:', error);
            showMessage(`保存失败: ${error.detail}`, 'error');
        }
        
    } catch (error) {
        console.error('Error saving data source config:', error);
        showMessage('保存数据源配置失败', 'error');
    }
}

// 预览数据文件
async function previewDataFile(filename) {
    try {
        const response = await fetch(`${API_BASE}/data/files/${filename}/preview`);
        if (response.ok) {
            const data = await response.json();
            showDataPreviewModal(filename, data);
        } else {
            showMessage('无法预览文件', 'error');
        }
    } catch (error) {
        console.error('Error previewing file:', error);
        showMessage('预览文件失败', 'error');
    }
}

// 显示数据预览模态框
function showDataPreviewModal(filename, data) {
    const modalHtml = `
        <div class="modal fade" id="dataPreviewModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="fas fa-file-csv"></i> 数据预览: ${filename}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <strong>文件信息:</strong><br>
                                行数: ${data.total_rows}<br>
                                列数: ${data.columns.length}
                            </div>
                            <div class="col-md-4">
                                <strong>日期范围:</strong><br>
                                开始: ${data.date_range?.start || 'N/A'}<br>
                                结束: ${data.date_range?.end || 'N/A'}
                            </div>
                            <div class="col-md-4">
                                <strong>股票代码:</strong><br>
                                ${data.securities?.join(', ') || 'N/A'}
                            </div>
                        </div>
                        <div class="table-responsive">
                            <table class="table table-striped table-sm">
                                <thead>
                                    <tr>
                                        ${data.columns.map(col => `<th>${col}</th>`).join('')}
                                    </tr>
                                </thead>
                                <tbody>
                                    ${data.preview_data.map(row => `
                                        <tr>
                                            ${row.map(cell => `<td>${cell}</td>`).join('')}
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除已存在的模态框
    const existingModal = document.getElementById('dataPreviewModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('dataPreviewModal'));
    modal.show();
}

// 下载数据文件
function downloadDataFile(filename) {
    const downloadUrl = `${API_BASE}/data/files/${filename}/download`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showMessage(`开始下载文件: ${filename}`);
}

// 删除数据文件
async function deleteDataFile(filename) {
    if (!confirm(`确定要删除文件 "${filename}" 吗？此操作不可恢复。`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/data/files/${filename}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            const result = await response.json();
            showMessage(`文件删除成功: ${filename}`);
            console.log('Delete result:', result);
            loadDataSources(); // 刷新文件列表
        } else {
            const error = await response.json();
            showMessage(`删除失败: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error deleting file:', error);
        showMessage('删除文件失败', 'error');
    }
}

async function uploadDataFile(input) {
    const file = input.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE}/data/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            showMessage(`文件上传成功：${result.filename} (${formatFileSize(result.file_size)})`);
            console.log('Upload result:', result);
            loadDataSources(); // 刷新文件列表
        } else {
            const error = await response.json();
            showMessage(`上传失败: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error uploading file:', error);
        showMessage('文件上传失败', 'error');
    }
    
    // 清空文件选择
    input.value = '';
}

// 回测执行功能
async function loadBacktestOptions() {
    try {
        const [strategies, dataFiles] = await Promise.all([
            fetch(`${API_BASE}/strategies`).then(r => r.json()),
            fetch(`${API_BASE}/data/files`).then(r => r.json())
        ]);
        
        // 存储数据文件信息
        dataFilesInfo = {};
        dataFiles.data_files.forEach(file => {
            dataFilesInfo[file.name] = file;
        });
        
        // 填充策略选择器
        const strategySelect = document.getElementById('backtest-strategy');
        strategySelect.innerHTML = '<option value="">请选择策略</option>' +
            strategies.strategies.map(s => `<option value="${s.name}">${s.name}</option>`).join('');
        
        // 填充数据文件选择器
        const dataFileSelect = document.getElementById('backtest-data-file');
        dataFileSelect.innerHTML = '<option value="">请选择数据文件</option>' +
            dataFiles.data_files.map(f => `<option value="${f.name}">${f.name} (${f.columns.includes('date') || f.columns.includes('datetime') ? '包含日期' : '无日期列'})</option>`).join('');
        
        // 设置默认日期
        const today = new Date();
        const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
        
        document.getElementById('backtest-start-date').value = oneYearAgo.toISOString().split('T')[0];
        document.getElementById('backtest-end-date').value = today.toISOString().split('T')[0];
        
    } catch (error) {
        console.error('Error loading backtest options:', error);
        showMessage('加载回测选项失败', 'error');
    }
}

// 当数据文件选择改变时的处理
async function onDataFileChange() {
    const selectedFile = document.getElementById('backtest-data-file').value;
    const infoDiv = document.getElementById('csv-file-info');
    const infoText = document.getElementById('csv-info-text');
    
    if (!selectedFile) {
        infoDiv.style.display = 'none';
        return;
    }
    
    try {
        // 首先尝试获取文件的详细信息（包括日期范围）
        const response = await fetch(`${API_BASE}/data/files/${selectedFile}/info`);
        if (response.ok) {
            const fileInfo = await response.json();
            
            // 显示文件信息
            infoText.innerHTML = `
                文件包含 ${fileInfo.total_rows} 行数据，
                ${fileInfo.securities?.length || 0} 个股票代码
                ${fileInfo.date_range ? `，日期范围: ${fileInfo.date_range.start} 至 ${fileInfo.date_range.end}` : ''}
            `;
            infoDiv.style.display = 'block';
            
            // 自动填充日期范围
            if (fileInfo.date_range) {
                document.getElementById('backtest-start-date').value = fileInfo.date_range.start;
                document.getElementById('backtest-end-date').value = fileInfo.date_range.end;
                
                showMessage(`已自动设置日期范围: ${fileInfo.date_range.start} 至 ${fileInfo.date_range.end}`, 'info');
            }
            return;
        }
    } catch (error) {
        console.error('API not available, trying fallback method:', error);
    }
    
    // 如果API不可用，尝试基于本地文件信息进行简单的日期推测
    const fileInfo = dataFilesInfo[selectedFile];
    if (fileInfo) {
        infoText.innerHTML = `
            文件大小: ${formatFileSize(fileInfo.size)}，
            列: ${fileInfo.columns.join(', ')}
        `;
        infoDiv.style.display = 'block';
        
        // 尝试基于文件名猜测日期范围
        const dateGuess = guessDateRangeFromFilename(selectedFile);
        if (dateGuess) {
            document.getElementById('backtest-start-date').value = dateGuess.start;
            document.getElementById('backtest-end-date').value = dateGuess.end;
            showMessage(`根据文件名推测日期范围: ${dateGuess.start} 至 ${dateGuess.end}`, 'info');
        } else {
            // 如果无法猜测，设置一个合理的默认范围
            const today = new Date();
            const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
            document.getElementById('backtest-start-date').value = oneYearAgo.toISOString().split('T')[0];
            document.getElementById('backtest-end-date').value = today.toISOString().split('T')[0];
        }
    }
}

// 根据文件名猜测日期范围的辅助函数
function guessDateRangeFromFilename(filename) {
    // 尝试从文件名中提取日期信息
    const datePatterns = [
        // 匹配 YYYY-MM-DD 格式
        /(\d{4}-\d{2}-\d{2})/g,
        // 匹配 YYYYMMDD 格式
        /(\d{8})/g,
        // 匹配 YYYY_MM_DD 格式
        /(\d{4}_\d{2}_\d{2})/g
    ];
    
    for (const pattern of datePatterns) {
        const matches = filename.match(pattern);
        if (matches && matches.length >= 2) {
            // 假设第一个是开始日期，最后一个是结束日期
            let startDate = matches[0];
            let endDate = matches[matches.length - 1];
            
            // 标准化日期格式为 YYYY-MM-DD
            startDate = startDate.replace(/_/g, '-').replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3');
            endDate = endDate.replace(/_/g, '-').replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3');
            
            // 验证日期格式
            if (isValidDate(startDate) && isValidDate(endDate)) {
                return { start: startDate, end: endDate };
            }
        } else if (matches && matches.length === 1) {
            // 只有一个日期，作为结束日期，开始日期设为一年前
            let endDate = matches[0];
            endDate = endDate.replace(/_/g, '-').replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3');
            
            if (isValidDate(endDate)) {
                const end = new Date(endDate);
                const start = new Date(end.getFullYear() - 1, end.getMonth(), end.getDate());
                return { 
                    start: start.toISOString().split('T')[0], 
                    end: endDate 
                };
            }
        }
    }
    
    return null;
}

// 验证日期格式的辅助函数
function isValidDate(dateString) {
    const date = new Date(dateString);
    return date instanceof Date && !isNaN(date) && dateString.match(/^\d{4}-\d{2}-\d{2}$/);
}

function toggleDataSourceOptions() {
    const dataSource = document.getElementById('backtest-data-source').value;
    const csvOptions = document.getElementById('csv-options');
    const onlineOptions = document.getElementById('online-options');
    
    if (dataSource === 'csv') {
        csvOptions.style.display = 'block';
        onlineOptions.style.display = 'none';
        // 当切换到CSV时，如果已选择文件，则触发文件信息加载
        onDataFileChange();
    } else {
        csvOptions.style.display = 'none';
        onlineOptions.style.display = 'block';
        // 清除CSV文件信息显示
        document.getElementById('csv-file-info').style.display = 'none';
    }
}

// 回测表单提交
document.addEventListener('DOMContentLoaded', function() {
    const backtestForm = document.getElementById('backtest-form');
    if (backtestForm) {
        backtestForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                strategy_name: document.getElementById('backtest-strategy').value,
                data_source: document.getElementById('backtest-data-source').value,
                start_date: document.getElementById('backtest-start-date').value,
                end_date: document.getElementById('backtest-end-date').value,
                initial_cash: parseFloat(document.getElementById('backtest-initial-cash').value),
                commission_rate: parseFloat(document.getElementById('backtest-commission').value)
            };
            
            if (formData.data_source === 'csv') {
                formData.data_file = document.getElementById('backtest-data-file').value;
            } else {
                const securities = document.getElementById('backtest-securities').value;
                formData.securities = securities ? securities.split(',').map(s => s.trim()) : ['000001.SZ'];
            }
            
            try {
                const response = await fetch(`${API_BASE}/backtest`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    currentJobId = result.job_id;
                    showMessage('回测已开始，请在运行状态中查看进度');
                    monitorJob(currentJobId);
                } else {
                    const error = await response.json();
                    showMessage(`回测启动失败: ${error.detail}`, 'error');
                }
            } catch (error) {
                console.error('Error starting backtest:', error);
                showMessage('回测启动失败', 'error');
            }
        });
    }
});

async function monitorJob(jobId) {
    const statusDiv = document.getElementById('backtest-status');
    
    const updateStatus = async () => {
        try {
            const response = await fetch(`${API_BASE}/jobs/${jobId}`);
            const job = await response.json();
            
            const statusHtml = `
                <div class="mb-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6>任务状态</h6>
                        <span class="status-badge status-${job.status}">${job.status}</span>
                    </div>
                    <div class="progress mt-2">
                        <div class="progress-bar" style="width: ${job.progress}%">${job.progress.toFixed(1)}%</div>
                    </div>
                </div>
                <div class="mb-3">
                    <small class="text-muted">消息：${job.message}</small>
                </div>
                <div>
                    <small class="text-muted">创建时间：${formatDateTime(job.created_at)}</small>
                    ${job.completed_at ? `<br><small class="text-muted">完成时间：${formatDateTime(job.completed_at)}</small>` : ''}
                </div>
            `;
            
            statusDiv.innerHTML = statusHtml;
            
            if (job.status === 'completed') {
                showMessage('回测完成！请到结果分析页面查看详细结果');
                return; // 停止监控
            } else if (job.status === 'failed') {
                showMessage(`回测失败: ${job.message}`, 'error');
                return; // 停止监控
            }
            
            // 如果任务仍在运行，继续监控
            if (job.status === 'running' || job.status === 'pending') {
                setTimeout(updateStatus, 2000); // 2秒后再次检查
            }
            
        } catch (error) {
            console.error('Error monitoring job:', error);
        }
    };
    
    updateStatus();
}

// 批量测试功能
async function loadBatchTestOptions() {
    try {
        const strategies = await fetch(`${API_BASE}/strategies`).then(r => r.json());
        
        // 填充策略选择器
        const strategySelect = document.getElementById('batch-strategy');
        strategySelect.innerHTML = '<option value="">请选择策略</option>' +
            strategies.strategies.map(s => `<option value="${s.name}">${s.name}</option>`).join('');
        
        // 设置默认日期
        const today = new Date();
        const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
        
        document.getElementById('batch-start-date').value = oneYearAgo.toISOString().split('T')[0];
        document.getElementById('batch-end-date').value = today.toISOString().split('T')[0];
        
    } catch (error) {
        console.error('Error loading batch test options:', error);
        showMessage('加载批量测试选项失败', 'error');
    }
}

function addParameterRow() {
    const container = document.getElementById('parameter-ranges');
    const rowHtml = `
        <div class="row mb-2">
            <div class="col-md-4">
                <input type="text" class="form-control" placeholder="参数名" id="param-name-${parameterRowCount}">
            </div>
            <div class="col-md-6">
                <input type="text" class="form-control" placeholder="取值列表，用逗号分隔" id="param-values-${parameterRowCount}">
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-outline-danger" onclick="removeParameterRow(${parameterRowCount})">删除</button>
            </div>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', rowHtml);
    parameterRowCount++;
}

function removeParameterRow(index) {
    const rows = document.querySelectorAll('#parameter-ranges .row');
    if (rows.length > 1) { // 至少保留一行
        document.getElementById(`param-name-${index}`).closest('.row').remove();
    }
}

// 结果分析功能
let allJobs = [];
// 工具函数：优雅地截断文本
function truncateText(text, maxLength = 30, breakWords = true) {
    if (!text || text.length <= maxLength) return text;
    
    if (breakWords) {
        // 在单词边界处截断
        const truncated = text.substring(0, maxLength);
        const lastSpace = truncated.lastIndexOf(' ');
        const lastUnderscore = truncated.lastIndexOf('_');
        const lastDot = truncated.lastIndexOf('.');
        const breakPoint = Math.max(lastSpace, lastUnderscore, lastDot);
        
        if (breakPoint > maxLength * 0.6) { // 如果截断点不会太短
            return text.substring(0, breakPoint) + '...';
        }
    }
    
    return text.substring(0, maxLength - 3) + '...';
}

// 工具函数：为长文件名生成带tooltip的HTML
function createTruncatedElement(text, maxLength = 25, className = '') {
    const truncated = truncateText(text, maxLength);
    const needsTruncation = text.length > maxLength;
    
    if (needsTruncation) {
        return `<span class="${className}" title="${text}" data-bs-toggle="tooltip">${truncated}</span>`;
    }
    return `<span class="${className}">${text}</span>`;
}

// 工具函数：智能截断策略名称（保留关键信息）
function truncateStrategyName(strategyName, maxLength = 20) {
    if (!strategyName || strategyName.length <= maxLength) return strategyName;
    
    // 移除常见后缀
    const cleanName = strategyName.replace(/_strategy$/i, '').replace(/strategy$/i, '');
    
    // 如果清理后的名称足够短，就使用它
    if (cleanName.length <= maxLength) {
        return cleanName;
    }
    
    // 否则智能截断
    return truncateText(cleanName, maxLength, true);
}

let filteredJobs = [];
let selectedJob = null;

async function loadJobResults() {
    try {
        showLoading('job-results-list');
        const [jobsResponse, reportsResponse] = await Promise.all([
            fetch(`${API_BASE}/jobs`),
            fetch(`${API_BASE}/reports`)
        ]);
        
        const jobsData = await jobsResponse.json();
        const reportsData = await reportsResponse.json();
        
        // 合并回测任务和已有报告
        allJobs = jobsData.jobs.filter(job => job.status === 'completed');
        
        // 将已有报告转换为伪任务对象，与回测任务统一显示
        const reportJobs = (reportsData.reports || []).map(report => {
            // 使用从后端加载的真实数据
            let summaryData = report.summary || {
                total_return: 0,
                annual_return: 0,
                max_drawdown: 0,
                sharpe_ratio: 0,
                volatility: 0,
                win_rate: 0,
                total_trades: 0
            };
            
            return {
                job_id: 'report_' + report.strategy_name + '_' + report.session_id,
                type: 'backtest',
                status: 'completed',
                created_at: report.created_at,
                completed_at: report.created_at,
                request: {
                    strategy_name: report.strategy_name,
                    start_date: '历史数据',
                    end_date: '历史数据'
                },
                result: {
                    summary: summaryData,
                    report_files: report.files.map(f => `reports/${report.strategy_name}/${f.name}`)
                },
                _isHistoricalReport: true, // 标记为历史报告
                _strategyName: report.strategy_name,
                _sessionId: report.session_id
            };
        });
        
        // 合并所有任务（回测任务 + 报告）
        allJobs = [...allJobs, ...reportJobs];
        filteredJobs = [...allJobs];
        
        displayJobResults();
        updateJobsCount();
        
    } catch (error) {
        console.error('Error loading job results:', error);
        showMessage('加载任务结果失败', 'error');
        document.getElementById('job-results-list').innerHTML = '<p class="text-muted">加载失败</p>';
    }
}

function displayJobResults() {
    const jobsHtml = filteredJobs.map(job => {
        const strategyName = job.request?.strategy_name || 'Unknown Strategy';
        const truncatedStrategyName = truncateStrategyName(strategyName, 18);
        const needsTooltip = strategyName !== truncatedStrategyName;
        
        const timeRange = job.request ? `${job.request.start_date} ~ ${job.request.end_date}` : '';
        const isSelected = selectedJob && selectedJob.job_id === job.job_id;
        const isHistorical = job._isHistoricalReport;
        
        return `
            <div class="job-result-card mb-3 p-3 border rounded ${isSelected ? 'border-primary' : ''} ${isHistorical ? 'bg-light border-info' : ''}" 
                 onclick="selectJobResult('${job.job_id}')" style="cursor: pointer;">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1 min-w-0"> <!-- min-w-0 for text overflow -->
                        <h6 class="mb-1 fw-bold d-flex align-items-center">
                            ${isHistorical ? '<i class="fas fa-folder-open text-info me-1 flex-shrink-0"></i>' : ''}
                            <span class="text-truncate" ${needsTooltip ? `title="${strategyName}" data-bs-toggle="tooltip"` : ''}>
                                ${truncatedStrategyName}
                            </span>
                        </h6>
                        <small class="text-muted d-block text-truncate">${isHistorical ? '历史报告' : timeRange}</small>
                        <small class="text-muted">${formatDateTime(job.completed_at)}</small>
                    </div>
                    <div class="text-end flex-shrink-0 ms-2">
                        <span class="badge ${isHistorical ? 'bg-info' : 'bg-success'} mb-1">
                            ${isHistorical ? '历史报告' : '已完成'}
                        </span>
                        ${job.result?.summary && !isHistorical ? `
                            <div class="small text-success">
                                <i class="fas fa-arrow-up"></i> ${((job.result.summary.total_return || 0) * 100).toFixed(1)}%
                            </div>
                        ` : ''}
                        ${isHistorical && job.result?.report_files ? `
                            <div class="small text-info">
                                <i class="fas fa-file-alt"></i> ${job.result.report_files.length} 个文件
                            </div>
                        ` : ''}
                    </div>
                </div>
                <div class="mt-2">
                    <div class="btn-group btn-group-sm w-100" role="group">
                        <button class="btn ${isHistorical ? 'btn-outline-info' : 'btn-outline-primary'}" onclick="event.stopPropagation(); viewJobDetails('${job.job_id}')">
                            <i class="fas fa-eye"></i> <span class="d-none d-sm-inline">查看</span>
                        </button>
                        <button class="btn btn-outline-success" onclick="event.stopPropagation(); downloadJobReports('${job.job_id}')">
                            <i class="fas fa-download"></i> <span class="d-none d-sm-inline">下载</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    document.getElementById('job-results-list').innerHTML = jobsHtml || 
        '<div class="text-center py-4"><i class="fas fa-inbox fa-2x text-muted mb-2"></i><p class="text-muted">暂无已完成的任务</p></div>';
    
    // 初始化 Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function updateJobsCount() {
    document.getElementById('total-jobs-count').textContent = filteredJobs.length;
}

function filterJobResults() {
    const searchTerm = document.getElementById('job-search').value.toLowerCase();
    filteredJobs = allJobs.filter(job => {
        const strategyName = (job.request?.strategy_name || '').toLowerCase();
        return strategyName.includes(searchTerm);
    });
    displayJobResults();
    updateJobsCount();
}

async function selectJobResult(jobId) {
    try {
        // Check if this is a historical report
        if (jobId.startsWith('report_')) {
            // Find the job in our local array (historical reports)
            selectedJob = allJobs.find(job => job.job_id === jobId);
            if (selectedJob && selectedJob._isHistoricalReport) {
                // Load detailed historical data including portfolio history
                try {
                    const response = await fetch(`${API_BASE}/reports/${selectedJob._strategyName}/data/${selectedJob._sessionId}`);
                    if (response.ok) {
                        const historicalData = await response.json();
                        // Merge the detailed data into the selected job
                        selectedJob.result.summary = historicalData.data.summary || selectedJob.result.summary;
                        selectedJob.result.portfolio_history = historicalData.data.portfolio_history || [];
                        selectedJob.result.backtest_config = historicalData.data.backtest_config || {};
                        selectedJob.result.trade_summary = historicalData.data.trade_summary || {};
                        selectedJob.result.final_positions = historicalData.data.final_positions || {};
                        
                        console.log('Loaded historical data:', historicalData.data);
                    }
                } catch (error) {
                    console.error('Error loading detailed historical data:', error);
                    // Continue with existing data if detailed load fails
                }
                
                displayJobResults(); // 刷新列表以显示选中状态
                showJobAnalysis(selectedJob);
                document.getElementById('analysis-controls').style.display = 'block';
                return;
            } else {
                showMessage('报告不存在', 'error');
                return;
            }
        }
        
        // Regular backtest job - fetch from API
        const response = await fetch(`${API_BASE}/jobs/${jobId}`);
        if (response.ok) {
            selectedJob = await response.json();
            
            displayJobResults(); // 刷新列表以显示选中状态
            showJobAnalysis(selectedJob);
            document.getElementById('analysis-controls').style.display = 'block';
        } else {
            showMessage('加载任务详情失败', 'error');
        }
        
    } catch (error) {
        console.error('Error selecting job result:', error);
        showMessage('加载任务详情失败', 'error');
    }
}

function showJobAnalysis(job) {
    const visualizationDiv = document.getElementById('result-visualization');
    
    console.log('Showing job analysis for:', job); // Debug log
    
    if (job.type === 'backtest' && job.result) {
        const result = job.result;
        const summary = result.summary || {};
        const performance = result.performance || {};
        
        console.log('Job result:', result); // Debug log
        console.log('Summary data:', summary); // Debug log
        
        const resultHtml = `
            <div class="analysis-header mb-4">
                <h5 class="fw-bold d-flex align-items-center flex-wrap">
                    ${job._isHistoricalReport ? '<i class="fas fa-folder-open text-info me-2 flex-shrink-0"></i>' : ''}
                    <span class="text-truncate" title="${job.request.strategy_name}" data-bs-toggle="tooltip">
                        ${truncateStrategyName(job.request.strategy_name, 25)}
                    </span>
                    <span class="badge ${job._isHistoricalReport ? 'bg-info' : 'bg-primary'} ms-2 flex-shrink-0">
                        ${job._isHistoricalReport ? '历史报告' : '分析报告'}
                    </span>
                </h5>
                <p class="text-muted mb-0 small">${job._isHistoricalReport ? '历史报告数据' : `回测期间：${job.request.start_date} 至 ${job.request.end_date}`}</p>
            </div>
            
            <!-- 关键指标卡片 -->
            <div class="row mb-4">
                <div class="col-lg-3 col-md-6 col-6 mb-3">
                    <div class="metric-card bg-primary text-white p-3 rounded text-center">
                        <div class="metric-value h5 mb-1">${((summary.total_return || 0) * 100).toFixed(2)}%</div>
                        <div class="metric-label small">总收益率</div>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 col-6 mb-3">
                    <div class="metric-card bg-success text-white p-3 rounded text-center">
                        <div class="metric-value h5 mb-1">${((summary.annual_return || 0) * 100).toFixed(2)}%</div>
                        <div class="metric-label small">年化收益率</div>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 col-6 mb-3">
                    <div class="metric-card bg-warning text-white p-3 rounded text-center">
                        <div class="metric-value h5 mb-1">${((summary.max_drawdown || 0) * 100).toFixed(2)}%</div>
                        <div class="metric-label small">最大回撤</div>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 col-6 mb-3">
                    <div class="metric-card bg-info text-white p-3 rounded text-center">
                        <div class="metric-value h5 mb-1">${(summary.sharpe_ratio || 0).toFixed(2)}</div>
                        <div class="metric-label small">夏普比率</div>
                    </div>
                </div>
            </div>
            
            <!-- 详细分析表格 -->
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card h-100">
                        <div class="card-header bg-light">
                            <h6 class="mb-0"><i class="fas fa-chart-line"></i> 收益分析</h6>
                        </div>
                        <div class="card-body">
                            <table class="table table-sm table-borderless">
                                <tr><td class="fw-bold">初始资金</td><td>¥${(job.request.initial_cash || 1000000).toLocaleString()}</td></tr>
                                <tr><td class="fw-bold">最终资金</td><td>¥${(((job.request.initial_cash || 1000000) * (1 + (summary.total_return || 0)))).toLocaleString()}</td></tr>
                                <tr><td class="fw-bold">绝对收益</td><td class="${(summary.total_return || 0) >= 0 ? 'text-success' : 'text-danger'}">
                                    ¥${(((job.request.initial_cash || 1000000) * (summary.total_return || 0))).toLocaleString()}</td></tr>
                                <tr><td class="fw-bold">日均收益率</td><td>${(((summary.annual_return || 0) / 365) * 100).toFixed(4)}%</td></tr>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card h-100">
                        <div class="card-header bg-light">
                            <h6 class="mb-0"><i class="fas fa-shield-alt"></i> 风险分析</h6>
                        </div>
                        <div class="card-body">
                            <table class="table table-sm table-borderless">
                                <tr><td class="fw-bold">波动率</td><td>${((summary.volatility || 0) * 100).toFixed(2)}%</td></tr>
                                <tr><td class="fw-bold">胜率</td><td>${((summary.win_rate || 0) * 100).toFixed(1)}%</td></tr>
                                <tr><td class="fw-bold">交易次数</td><td>${summary.total_trades || 0} 次</td></tr>
                                <tr><td class="fw-bold">数据源</td><td class="text-capitalize">${job.request.data_source}</td></tr>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 收益曲线图表 -->
            <div class="card mb-4">
                <div class="card-header bg-light">
                    <h6 class="mb-0"><i class="fas fa-chart-area"></i> 收益曲线 (Web界面实时绘制)</h6>
                </div>
                <div class="card-body">
                    <div class="chart-container">
                        <canvas id="returns-chart-${job.job_id}" width="800" height="400"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- 报告文件下载 -->
            <div class="card">
                <div class="card-header bg-light">
                    <h6 class="mb-0"><i class="fas fa-file-download"></i> 回测报告文件</h6>
                </div>
                <div class="card-body">
                    ${result.report_files && result.report_files.length > 0 ? `
                        <div class="row">
                            ${(() => {
                                // 按文件类型分组报告文件
                                const fileGroups = {};
                                result.report_files.forEach(file => {
                                    const fileName = file.split('/').pop();
                                    const fileType = fileName.split('.').pop().toLowerCase();
                                    if (!fileGroups[fileType]) fileGroups[fileType] = [];
                                    fileGroups[fileType].push({file, fileName, fileType});
                                });
                                
                                const typeOrder = ['json', 'txt', 'csv']; // 优先显示顺序
                                const sortedTypes = typeOrder.filter(type => fileGroups[type]);
                                
                                return sortedTypes.map(fileType => {
                                    const files = fileGroups[fileType];
                                    const typeIcons = {
                                        'json': 'file-code',
                                        'csv': 'file-csv', 
                                        'txt': 'file-alt'
                                    };
                                    const typeColors = {
                                        'json': 'primary',
                                        'csv': 'success',
                                        'txt': 'secondary'
                                    };
                                    const typeNames = {
                                        'json': 'JSON数据报告',
                                        'csv': 'CSV数据报告',
                                        'txt': '文本报告'
                                    };
                                    
                                    return `
                                        <div class="col-md-12 mb-3">
                                            <div class="card">
                                                <div class="card-header bg-${typeColors[fileType]} text-white">
                                                    <h6 class="mb-0">
                                                        <i class="fas fa-${typeIcons[fileType]}"></i> 
                                                        ${typeNames[fileType]} (${files.length} 个文件)
                                                    </h6>
                                                </div>
                                                <div class="card-body p-2">
                                                    <div class="row">
                                                        ${files.map(({file, fileName}) => {
                                                            // 智能截断文件名
                                                            const maxFileNameLength = window.innerWidth < 768 ? 20 : 35; // 移动端更短
                                                            const truncatedFileName = truncateText(fileName, maxFileNameLength, true);
                                                            const needsFileTooltip = fileName !== truncatedFileName;
                                                            
                                                            return `
                                                            <div class="col-lg-6 col-12 mb-2">
                                                                <div class="d-flex justify-content-between align-items-center p-2 border rounded">
                                                                    <span class="small text-truncate flex-grow-1 me-2" 
                                                                          ${needsFileTooltip ? `title="${fileName}" data-bs-toggle="tooltip"` : ''}>
                                                                        ${truncatedFileName}
                                                                    </span>
                                                                    <div class="btn-group btn-group-sm flex-shrink-0">
                                                                        <button class="btn btn-outline-${typeColors[fileType]} btn-sm" 
                                                                                onclick="previewReportFile('${job.request.strategy_name}', '${fileName}')"
                                                                                title="预览文件" data-bs-toggle="tooltip">
                                                                            <i class="fas fa-eye"></i>
                                                                        </button>
                                                                        <a href="/api/reports/${job.request.strategy_name}/${fileName}" 
                                                                           class="btn btn-${typeColors[fileType]} btn-sm" 
                                                                           download="${fileName}"
                                                                           title="下载文件" data-bs-toggle="tooltip">
                                                                            <i class="fas fa-download"></i>
                                                                        </a>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        `;}).join('')}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                }).join('');
                            })()}
                        </div>
                    ` : '<p class="text-muted">暂无报告文件</p>'}
                </div>
            </div>
        `;
        
        visualizationDiv.innerHTML = resultHtml;
        
        // 绘制收益曲线图
        setTimeout(() => drawReturnsChart(job), 100);
        
        // 重新初始化tooltips
        setTimeout(() => {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }, 150);
        
    } else if (job.type === 'batch_test' && job.result) {
        // 批量测试结果
        showBatchTestResults(job);
    }
}

function drawReturnsChart(job) {
    const canvas = document.getElementById(`returns-chart-${job.job_id}`);
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // 使用真实的投资组合历史数据绘制收益曲线
    const summary = job.result.summary || {};
    const portfolioHistory = job.result.portfolio_history || [];
    const totalReturn = summary.total_return || 0;
    
    let labels = [];
    let returns = [];
    let chartTitle = '回测收益曲线';
    
    if (portfolioHistory.length > 0) {
        // 使用真实的投资组合历史数据
        const initialValue = summary.initial_value || portfolioHistory[0]?.total_value || 1000000;
        
        labels = portfolioHistory.map(item => {
            const date = new Date(item.date || item.datetime);
            return date.toLocaleDateString();
        });
        
        returns = portfolioHistory.map(item => {
            const currentValue = item.total_value || 0;
            return ((currentValue - initialValue) / initialValue) * 100;
        });
        
        chartTitle = job._isHistoricalReport ? '历史报告收益曲线 (真实数据)' : '回测收益曲线 (真实数据)';
        
        console.log('Drawing chart with real portfolio data:', {
            portfolioHistory: portfolioHistory.length,
            labels: labels.length,
            returns: returns.length
        });
    } else {
        // 回退到模拟数据
        const days = getDaysBetweenDates(job.request.start_date, job.request.end_date);
        const maxDataPoints = Math.min(50, Math.max(10, days)); // 10-50个数据点
        
        for (let i = 0; i <= maxDataPoints; i++) {
            const progress = i / maxDataPoints;
            const dayOffset = Math.floor(days * progress);
            
            const date = new Date(job.request.start_date);
            date.setDate(date.getDate() + dayOffset);
            labels.push(date.toLocaleDateString());
            
            // 基于实际收益率生成累计收益曲线
            const baseReturn = totalReturn * progress;
            const volatility = summary.volatility || 0.15;
            const randomFactor = (Math.random() - 0.5) * volatility * 0.3; // 添加波动
            returns.push((baseReturn + randomFactor) * 100);
        }
        
        // 确保最后一个点是准确的总收益率
        returns[returns.length - 1] = totalReturn * 100;
        chartTitle = job._isHistoricalReport ? '历史报告收益曲线 (模拟)' : '回测收益曲线 (模拟)';
    }
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '策略收益率 (%)',
                data: returns,
                borderColor: job._isHistoricalReport ? '#17a2b8' : '#667eea',
                backgroundColor: job._isHistoricalReport ? 'rgba(23, 162, 184, 0.1)' : 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                title: {
                    display: true,
                    text: chartTitle
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '累计收益率 (%)'
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '日期'
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                }
            }
        }
    });
}

function getDaysBetweenDates(startDate, endDate) {
    // 对于历史报告，使用默认时间跨度
    if (startDate === '历史数据' || endDate === '历史数据') {
        return 252; // 一年的交易日
    }
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

// 指南和帮助功能
function showResultsGuide() {
    document.getElementById('results-guide').style.display = 'block';
}

function hideResultsGuide() {
    document.getElementById('results-guide').style.display = 'none';
}

// 其他功能
function viewJobDetails(jobId) {
    selectJobResult(jobId);
}

function downloadJobReports(jobId) {
    const job = allJobs.find(j => j.job_id === jobId);
    if (job && job.result && job.result.report_files) {
        // 如果是历史报告，直接下载报告文件
        if (job._isHistoricalReport) {
            const strategyName = job.request.strategy_name;
            fetch(`${API_BASE}/reports`)
                .then(r => r.json())
                .then(data => {
                    const report = data.reports.find(r => r.strategy_name === strategyName);
                    if (report && report.files) {
                        report.files.forEach(file => {
                            const link = document.createElement('a');
                            link.href = `/api/reports/${strategyName}/${file.name}`;
                            link.download = file.name;
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                        });
                        showMessage(`开始下载 ${report.files.length} 个报告文件`);
                    }
                })
                .catch(error => {
                    console.error('Error downloading reports:', error);
                    showMessage('下载报告失败', 'error');
                });
        } else {
            // 普通回测任务的下载逻辑
            job.result.report_files.forEach(file => {
                const fileName = file.split('/').pop();
                const link = document.createElement('a');
                link.href = `/api/reports/${job.request.strategy_name}/${fileName}`;
                link.download = fileName;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            });
            showMessage('开始下载报告文件');
        }
    }
}

function exportAnalysisData() {
    if (!selectedJob) return;
    
    const data = {
        job_id: selectedJob.job_id,
        strategy_name: selectedJob.request.strategy_name,
        backtest_period: `${selectedJob.request.start_date} to ${selectedJob.request.end_date}`,
        summary: selectedJob.result.summary,
        performance: selectedJob.result.performance
    };
    
    const dataStr = JSON.stringify(data, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${selectedJob.request.strategy_name}_analysis.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

function compareStrategies() {
    // 显示对比分析模态框
    const modal = new bootstrap.Modal(document.getElementById('compareModal'));
    modal.show();
    
    // 这里可以实现多策略对比功能
    showMessage('对比分析功能正在开发中', 'info');
}

function generateComparisonReport() {
    showMessage('对比报告生成功能正在开发中', 'info');
}

// 预览报告文件
async function previewReportFile(strategyName, fileName) {
    try {
        const response = await fetch(`${API_BASE}/reports/${strategyName}/${fileName}/preview`);
        if (response.ok) {
            const data = await response.json();
            showReportPreviewModal(data);
        } else {
            showMessage('无法预览文件', 'error');
        }
    } catch (error) {
        console.error('Error previewing report file:', error);
        showMessage('预览文件失败', 'error');
    }
}

// 显示报告预览模态框
function showReportPreviewModal(data) {
    let contentHtml = '';
    
    if (data.preview) {
        if (data.type === 'csv') {
            // CSV表格预览
            contentHtml = `
                <div class="mb-3">
                    <strong>文件信息:</strong> ${data.rows} 行, ${data.columns.length} 列
                </div>
                <div class="table-responsive">
                    <table class="table table-striped table-sm">
                        <thead>
                            <tr>
                                ${data.columns.map(col => `<th>${col}</th>`).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${data.preview_data.map(row => `
                                <tr>
                                    ${row.map(cell => `<td>${cell}</td>`).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            // 文本内容预览
            contentHtml = `
                <div class="mb-3">
                    <strong>文件类型:</strong> ${data.type.toUpperCase()}<br>
                    <strong>文件大小:</strong> ${formatFileSize(data.size)}
                </div>
                <pre class="bg-light p-3 rounded" style="max-height: 400px; overflow-y: auto; font-family: 'JetBrains Mono', monospace; font-size: 12px;">${data.content}</pre>
            `;
        }
    } else {
        contentHtml = `
            <div class="text-center py-4">
                <i class="fas fa-file-alt fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">${data.message || '无法预览此文件类型'}</h5>
                <p class="text-muted">文件大小: ${formatFileSize(data.size)}</p>
            </div>
        `;
    }
    
    const modalHtml = `
        <div class="modal fade" id="reportPreviewModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-file-alt"></i> 
                            报告预览: ${data.filename}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${contentHtml}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        <a href="/api/reports/${data.filename.split('_')[0] || 'unknown'}/${data.filename}" 
                           class="btn btn-primary" download="${data.filename}">
                            <i class="fas fa-download"></i> 下载完整文件
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除已存在的模态框
    const existingModal = document.getElementById('reportPreviewModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('reportPreviewModal'));
    modal.show();
}

// 显示批量测试结果
function showBatchTestResults(job) {
    const visualizationDiv = document.getElementById('result-visualization');
    const result = job.result;
    
    // 创建参数优化图表
    if (result.results && result.results.length > 0) {
        visualizationDiv.innerHTML = `
            <h6>批量测试结果 (${result.completed_combinations}/${result.total_combinations})</h6>
            <div class="chart-container">
                <canvas id="batch-results-chart"></canvas>
            </div>
            <div class="mt-3">
                <h6>最佳参数组合</h6>
                <div class="alert alert-success">
                    <strong>参数:</strong> ${JSON.stringify(result.best_result.parameters)}<br>
                    <strong>总收益率:</strong> ${(result.best_result.total_return * 100).toFixed(2)}%<br>
                    <strong>最大回撤:</strong> ${(result.best_result.max_drawdown * 100).toFixed(2)}%<br>
                    <strong>夏普比率:</strong> ${result.best_result.sharpe_ratio.toFixed(2)}
                </div>
            </div>
        `;
        
        // 创建散点图
        const ctx = document.getElementById('batch-results-chart').getContext('2d');
        new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: '参数组合结果',
                    data: result.results.map((r, i) => ({
                        x: r.total_return * 100,
                        y: r.max_drawdown * 100,
                        label: `组合${i+1}: ${JSON.stringify(r.parameters)}`
                    })),
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '总收益率 (%)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: '最大回撤 (%)'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.raw.label;
                            }
                        }
                    }
                }
            }
        });
    }
}

// 批量测试表单提交
document.addEventListener('DOMContentLoaded', function() {
    const batchForm = document.getElementById('batch-test-form');
    if (batchForm) {
        batchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // 收集参数范围
            const parameterRanges = {};
            const rows = document.querySelectorAll('#parameter-ranges .row');
            
            rows.forEach((row, index) => {
                const nameInput = row.querySelector(`input[id^="param-name-"]`);
                const valuesInput = row.querySelector(`input[id^="param-values-"]`);
                
                if (nameInput && valuesInput && nameInput.value.trim() && valuesInput.value.trim()) {
                    const paramName = nameInput.value.trim();
                    const paramValues = valuesInput.value.split(',').map(v => {
                        const trimmed = v.trim();
                        // 尝试转换为数字，如果失败则保持为字符串
                        const num = parseFloat(trimmed);
                        return isNaN(num) ? trimmed : num;
                    });
                    parameterRanges[paramName] = paramValues;
                }
            });
            
            if (Object.keys(parameterRanges).length === 0) {
                showMessage('请至少添加一个参数范围', 'error');
                return;
            }
            
            const formData = {
                strategy_name: document.getElementById('batch-strategy').value,
                parameter_ranges: parameterRanges,
                data_source: 'csv',
                start_date: document.getElementById('batch-start-date').value,
                end_date: document.getElementById('batch-end-date').value,
                initial_cash: 1000000.0
            };
            
            try {
                const response = await fetch(`${API_BASE}/batch-test`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    currentJobId = result.job_id;
                    showMessage('批量测试已开始');
                    monitorBatchTest(currentJobId);
                } else {
                    const error = await response.json();
                    showMessage(`批量测试启动失败: ${error.detail}`, 'error');
                }
            } catch (error) {
                console.error('Error starting batch test:', error);
                showMessage('批量测试启动失败', 'error');
            }
        });
    }
});

async function monitorBatchTest(jobId) {
    const statusDiv = document.getElementById('batch-test-status');
    
    const updateStatus = async () => {
        try {
            const response = await fetch(`${API_BASE}/jobs/${jobId}`);
            const job = await response.json();
            
            const statusHtml = `
                <div class="mb-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6>测试进度</h6>
                        <span class="status-badge status-${job.status}">${job.status}</span>
                    </div>
                    <div class="progress mt-2">
                        <div class="progress-bar bg-warning" style="width: ${job.progress}%">${job.progress.toFixed(1)}%</div>
                    </div>
                </div>
                <div class="mb-3">
                    <small class="text-muted">状态：${job.message}</small>
                </div>
                ${job.result ? `
                    <div class="mb-3">
                        <small class="text-success">已完成 ${job.result.completed_combinations}/${job.result.total_combinations} 个参数组合</small>
                    </div>
                ` : ''}
            `;
            
            statusDiv.innerHTML = statusHtml;
            
            if (job.status === 'completed') {
                showMessage('批量测试完成！请到结果分析页面查看详细结果');
                return;
            } else if (job.status === 'failed') {
                showMessage(`批量测试失败: ${job.message}`, 'error');
                return;
            }
            
            if (job.status === 'running' || job.status === 'pending') {
                setTimeout(updateStatus, 3000); // 3秒后再次检查
            }
            
        } catch (error) {
            console.error('Error monitoring batch test:', error);
        }
    };
    
    updateStatus();
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 加载仪表盘
    loadDashboard();
    
    // 设置默认选中第一个导航项
    document.querySelector('.sidebar .nav-link').classList.add('active');
});