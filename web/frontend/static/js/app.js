// SimTradeLab Web 前端JavaScript
// 主要功能：页面切换、API调用、数据可视化

// 全局变量
let currentTab = 'dashboard';
let strategyEditor = null;
let currentJobId = null;
let parameterRowCount = 1;

// API基础URL
const API_BASE = '/api';

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
    
    // 根据不同页面加载对应数据
    switch(tabName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'strategies':
            loadStrategies();
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
        case 'reports':
            loadReports();
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
async function loadDataSources() {
    try {
        const [sources, files] = await Promise.all([
            fetch(`${API_BASE}/data/sources`).then(r => r.json()),
            fetch(`${API_BASE}/data/files`).then(r => r.json())
        ]);
        
        // 显示数据源
        const sourcesHtml = sources.data_sources.map(source => `
            <div class="d-flex justify-content-between align-items-center mb-3 p-3 border rounded">
                <div>
                    <h6 class="mb-1">${source.name}</h6>
                    <small class="text-muted">${source.description}</small>
                </div>
                <div>
                    <span class="badge ${source.enabled ? 'bg-success' : 'bg-secondary'}">
                        ${source.enabled ? '已启用' : '已禁用'}
                    </span>
                </div>
            </div>
        `).join('');
        document.getElementById('data-sources-list').innerHTML = sourcesHtml;
        
        // 显示数据文件
        const filesHtml = files.data_files.map(file => `
            <div class="d-flex justify-content-between align-items-center mb-2 p-2 border rounded">
                <div>
                    <h6 class="mb-1">${file.name}</h6>
                    <small class="text-muted">列: ${file.columns.join(', ')}</small>
                </div>
                <div class="text-end">
                    <div><small>${formatFileSize(file.size)}</small></div>
                    <div><small class="text-muted">${formatDateTime(file.modified_at)}</small></div>
                </div>
            </div>
        `).join('');
        document.getElementById('data-files-list').innerHTML = filesHtml || '<p class="text-muted">暂无数据文件</p>';
        
    } catch (error) {
        console.error('Error loading data sources:', error);
        showMessage('加载数据源失败', 'error');
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
            showMessage('文件上传成功');
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
        
        // 填充策略选择器
        const strategySelect = document.getElementById('backtest-strategy');
        strategySelect.innerHTML = '<option value="">请选择策略</option>' +
            strategies.strategies.map(s => `<option value="${s.name}">${s.name}</option>`).join('');
        
        // 填充数据文件选择器
        const dataFileSelect = document.getElementById('backtest-data-file');
        dataFileSelect.innerHTML = '<option value="">请选择数据文件</option>' +
            dataFiles.data_files.map(f => `<option value="${f.name}">${f.name}</option>`).join('');
        
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

function toggleDataSourceOptions() {
    const dataSource = document.getElementById('backtest-data-source').value;
    const csvOptions = document.getElementById('csv-options');
    const onlineOptions = document.getElementById('online-options');
    
    if (dataSource === 'csv') {
        csvOptions.style.display = 'block';
        onlineOptions.style.display = 'none';
    } else {
        csvOptions.style.display = 'none';
        onlineOptions.style.display = 'block';
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
async function loadJobResults() {
    try {
        showLoading('job-results-list');
        const response = await fetch(`${API_BASE}/jobs`);
        const data = await response.json();
        
        const completedJobs = data.jobs.filter(job => job.status === 'completed');
        
        const jobsHtml = completedJobs.map(job => `
            <div class="list-group-item list-group-item-action" onclick="showJobResult('${job.job_id}')">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${job.type}</h6>
                    <small>${formatDateTime(job.completed_at)}</small>
                </div>
                <p class="mb-1 small">${job.message}</p>
                <small class="text-muted">Job ID: ${job.job_id}</small>
            </div>
        `).join('');
        
        document.getElementById('job-results-list').innerHTML = jobsHtml || '<p class="text-muted">暂无已完成的任务</p>';
        
    } catch (error) {
        console.error('Error loading job results:', error);
        showMessage('加载任务结果失败', 'error');
    }
}

async function showJobResult(jobId) {
    try {
        const response = await fetch(`${API_BASE}/jobs/${jobId}`);
        const job = await response.json();
        
        const visualizationDiv = document.getElementById('result-visualization');
        
        if (job.type === 'backtest' && job.result) {
            // 显示回测结果
            const result = job.result;
            const summary = result.summary || {};
            const performance = result.performance || {};
            
            const resultHtml = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>基本信息</h6>
                        <table class="table table-sm">
                            <tr><td>策略名称</td><td>${job.request.strategy_name}</td></tr>
                            <tr><td>回测期间</td><td>${job.request.start_date} 至 ${job.request.end_date}</td></tr>
                            <tr><td>初始资金</td><td>¥${job.request.initial_cash.toLocaleString()}</td></tr>
                            <tr><td>数据源</td><td>${job.request.data_source}</td></tr>
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h6>收益指标</h6>
                        <table class="table table-sm">
                            <tr><td>总收益率</td><td>${(summary.total_return * 100 || 0).toFixed(2)}%</td></tr>
                            <tr><td>年化收益率</td><td>${(summary.annual_return * 100 || 0).toFixed(2)}%</td></tr>
                            <tr><td>最大回撤</td><td>${(summary.max_drawdown * 100 || 0).toFixed(2)}%</td></tr>
                            <tr><td>夏普比率</td><td>${(summary.sharpe_ratio || 0).toFixed(2)}</td></tr>
                        </table>
                    </div>
                </div>
                
                <div class="mt-4">
                    <h6>报告文件</h6>
                    <div class="row">
                        ${result.report_files ? result.report_files.map(file => {
                            const fileName = file.split('/').pop();
                            const fileType = fileName.split('.').pop();
                            return `<div class="col-md-3 mb-2">
                                <a href="${file}" target="_blank" class="btn btn-outline-primary btn-sm w-100">
                                    <i class="fas fa-file-${fileType === 'json' ? 'code' : fileType === 'csv' ? 'csv' : 'alt'}"></i>
                                    ${fileName}
                                </a>
                            </div>`;
                        }).join('') : ''}
                    </div>
                </div>
            `;
            
            visualizationDiv.innerHTML = resultHtml;
            
        } else if (job.type === 'batch_test' && job.result) {
            // 显示批量测试结果
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
        
        // 高亮选中的任务
        document.querySelectorAll('#job-results-list .list-group-item').forEach(item => {
            item.classList.remove('active');
        });
        event.target.classList.add('active');
        
    } catch (error) {
        console.error('Error showing job result:', error);
        showMessage('加载任务结果失败', 'error');
    }
}

// 报告中心功能
async function loadReports() {
    try {
        showLoading('reports-list');
        const response = await fetch(`${API_BASE}/reports`);
        const data = await response.json();
        
        const reportsHtml = data.reports.map(report => `
            <div class="card mb-3">
                <div class="card-header">
                    <h6 class="mb-0">
                        <i class="fas fa-folder"></i> ${report.strategy_name}
                        <small class="text-muted ms-2">${formatDateTime(report.created_at)}</small>
                    </h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        ${report.files.map(file => `
                            <div class="col-md-3 mb-2">
                                <a href="/api/reports/${report.strategy_name}/${file.name}" 
                                   target="_blank" 
                                   class="btn btn-outline-primary btn-sm w-100">
                                    <i class="fas fa-file-${file.type.replace('.', '')}"></i>
                                    ${file.name}
                                    <br><small>${formatFileSize(file.size)}</small>
                                </a>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `).join('');
        
        document.getElementById('reports-list').innerHTML = reportsHtml || '<p class="text-muted">暂无报告文件</p>';
        
    } catch (error) {
        console.error('Error loading reports:', error);
        showMessage('加载报告失败', 'error');
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