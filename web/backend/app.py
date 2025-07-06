# -*- coding: utf-8 -*-
"""
SimTradeLab Web 后端API服务
使用 FastAPI 提供RESTful API接口
"""
import os
import sys
import json
import uuid
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from simtradelab import BacktestEngine
from simtradelab.data_sources import CSVDataSource, AkshareDataSource
from simtradelab.config_manager import get_config

app = FastAPI(
    title="SimTradeLab Web API",
    description="SimTradeLab 策略回测平台 Web API",
    version="1.0.0"
)

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="web/frontend/static"), name="static")

# 全局状态管理
active_jobs: Dict[str, Dict] = {}
strategies_dir = project_root / "strategies"
data_dir = project_root / "data"
reports_dir = project_root / "reports"
web_uploads_dir = project_root / "web" / "uploads"

# 确保目录存在
for directory in [strategies_dir, data_dir, reports_dir, web_uploads_dir]:
    directory.mkdir(parents=True, exist_ok=True)

# Pydantic模型定义
class StrategyRequest(BaseModel):
    name: str
    code: str
    description: Optional[str] = ""

class BacktestRequest(BaseModel):
    strategy_name: str
    data_source: str = "csv"
    data_file: Optional[str] = None
    securities: Optional[List[str]] = None
    start_date: str
    end_date: str
    initial_cash: float = 1000000.0
    commission_rate: float = 0.0003
    min_commission: float = 5.0
    slippage: float = 0.001

class BatchTestRequest(BaseModel):
    strategy_name: str
    parameter_ranges: Dict[str, List[Any]]
    data_source: str = "csv"
    data_file: Optional[str] = None
    securities: Optional[List[str]] = None
    start_date: str
    end_date: str
    initial_cash: float = 1000000.0

class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed
    progress: float
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None

# API路由定义

@app.get("/")
async def root():
    """根路径，返回前端页面"""
    return FileResponse("web/frontend/index.html")

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now()}

# 策略管理相关API

@app.get("/api/strategies")
async def list_strategies():
    """获取所有策略列表"""
    strategies = []
    for strategy_file in strategies_dir.glob("*.py"):
        try:
            with open(strategy_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单解析策略描述
            description = ""
            for line in content.split('\n'):
                if '"""' in line or "'''" in line:
                    description = line.strip(' "\'')
                    break
            
            strategies.append({
                "name": strategy_file.stem,
                "filename": strategy_file.name,
                "description": description,
                "modified_at": datetime.fromtimestamp(strategy_file.stat().st_mtime),
                "size": strategy_file.stat().st_size
            })
        except Exception as e:
            print(f"Error reading strategy {strategy_file}: {e}")
    
    return {"strategies": strategies}

@app.get("/api/strategies/{strategy_name}")
async def get_strategy(strategy_name: str):
    """获取指定策略的代码"""
    strategy_file = strategies_dir / f"{strategy_name}.py"
    if not strategy_file.exists():
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    try:
        with open(strategy_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "name": strategy_name,
            "code": content,
            "filename": strategy_file.name,
            "modified_at": datetime.fromtimestamp(strategy_file.stat().st_mtime)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading strategy: {str(e)}")

@app.post("/api/strategies")
async def save_strategy(strategy: StrategyRequest):
    """保存或更新策略"""
    strategy_file = strategies_dir / f"{strategy.name}.py"
    
    try:
        with open(strategy_file, 'w', encoding='utf-8') as f:
            f.write(strategy.code)
        
        return {
            "message": "Strategy saved successfully",
            "name": strategy.name,
            "filename": strategy_file.name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving strategy: {str(e)}")

@app.delete("/api/strategies/{strategy_name}")
async def delete_strategy(strategy_name: str):
    """删除指定策略"""
    strategy_file = strategies_dir / f"{strategy_name}.py"
    if not strategy_file.exists():
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    try:
        strategy_file.unlink()
        return {"message": "Strategy deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting strategy: {str(e)}")

# 数据管理相关API

@app.get("/api/data/sources")
async def list_data_sources():
    """获取可用的数据源列表"""
    config = get_config()
    sources = []
    
    for name, source_config in config.data_sources.items():
        sources.append({
            "name": name,
            "enabled": source_config.enabled,
            "type": type(source_config).__name__,
            "description": _get_data_source_description(name)
        })
    
    return {"data_sources": sources}

def _get_data_source_description(name: str) -> str:
    """获取数据源描述"""
    descriptions = {
        "csv": "本地CSV文件数据源",
        "akshare": "AkShare在线数据源（免费）",
        "tushare": "Tushare在线数据源（需要token）"
    }
    return descriptions.get(name, "未知数据源")

@app.get("/api/data/files")
async def list_data_files():
    """获取本地数据文件列表"""
    files = []
    for data_file in data_dir.glob("*.csv"):
        try:
            # 读取文件前几行来获取基本信息
            df_sample = pd.read_csv(data_file, nrows=5)
            
            files.append({
                "name": data_file.name,
                "path": str(data_file.relative_to(project_root)),
                "size": data_file.stat().st_size,
                "modified_at": datetime.fromtimestamp(data_file.stat().st_mtime),
                "columns": df_sample.columns.tolist(),
                "rows_sample": len(df_sample)
            })
        except Exception as e:
            print(f"Error reading data file {data_file}: {e}")
    
    return {"data_files": files}

@app.post("/api/data/upload")
async def upload_data_file(file: UploadFile = File(...)):
    """上传数据文件"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        # 保存上传的文件
        file_path = web_uploads_dir / file.filename
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # 验证CSV格式
        df = pd.read_csv(file_path, nrows=10)
        
        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "path": str(file_path.relative_to(project_root)),
            "columns": df.columns.tolist(),
            "sample_rows": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

# 回测相关API

@app.post("/api/backtest")
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """运行单次回测"""
    job_id = str(uuid.uuid4())
    
    # 创建任务记录
    active_jobs[job_id] = {
        "job_id": job_id,
        "type": "backtest",
        "status": "pending",
        "progress": 0.0,
        "message": "任务已创建，等待执行",
        "created_at": datetime.now(),
        "request": request.dict()
    }
    
    # 在后台执行回测
    background_tasks.add_task(_run_backtest_task, job_id, request)
    
    return {"job_id": job_id, "message": "Backtest started"}

async def _run_backtest_task(job_id: str, request: BacktestRequest):
    """后台执行回测任务"""
    try:
        # 更新状态为运行中
        active_jobs[job_id].update({
            "status": "running",
            "progress": 10.0,
            "message": "正在初始化回测引擎..."
        })
        
        # 构建策略文件路径
        strategy_file = strategies_dir / f"{request.strategy_name}.py"
        if not strategy_file.exists():
            raise ValueError(f"Strategy file not found: {request.strategy_name}")
        
        # 确定数据源
        if request.data_source == "csv":
            if request.data_file:
                data_path = data_dir / request.data_file
            else:
                data_path = data_dir / "sample_data.csv"
            
            if not data_path.exists():
                raise ValueError(f"Data file not found: {data_path}")
            
            active_jobs[job_id].update({
                "progress": 30.0,
                "message": f"使用CSV数据源: {data_path.name}"
            })
            
            # 创建引擎
            engine = BacktestEngine(
                strategy_file=str(strategy_file),
                data_path=str(data_path),
                start_date=request.start_date,
                end_date=request.end_date,
                initial_cash=request.initial_cash
            )
        else:
            # 使用在线数据源
            active_jobs[job_id].update({
                "progress": 30.0,
                "message": f"使用在线数据源: {request.data_source}"
            })
            
            from simtradelab.data_sources import AkshareDataSource
            data_source = AkshareDataSource()
            
            engine = BacktestEngine(
                strategy_file=str(strategy_file),
                data_source=data_source,
                securities=request.securities or ['000001.SZ'],
                start_date=request.start_date,
                end_date=request.end_date,
                initial_cash=request.initial_cash
            )
        
        # 设置参数
        if hasattr(engine, 'set_commission'):
            engine.set_commission(request.commission_rate, request.min_commission)
        if hasattr(engine, 'set_slippage'):
            engine.set_slippage(request.slippage)
        
        active_jobs[job_id].update({
            "progress": 50.0,
            "message": "正在执行回测..."
        })
        
        # 运行回测
        report_files = engine.run()
        
        active_jobs[job_id].update({
            "progress": 80.0,
            "message": "正在生成报告..."
        })
        
        # 解析结果
        result = _parse_backtest_results(report_files)
        
        # 完成任务
        active_jobs[job_id].update({
            "status": "completed",
            "progress": 100.0,
            "message": "回测完成",
            "completed_at": datetime.now(),
            "result": result
        })
        
    except Exception as e:
        active_jobs[job_id].update({
            "status": "failed",
            "progress": 0.0,
            "message": f"回测失败: {str(e)}",
            "completed_at": datetime.now()
        })

def _parse_backtest_results(report_files: List[str]) -> Dict:
    """解析回测结果"""
    result = {
        "report_files": report_files,
        "summary": {},
        "performance": {},
        "charts": {}
    }
    
    try:
        # 查找JSON报告文件
        json_file = None
        for file_path in report_files:
            if file_path.endswith('.json'):
                json_file = file_path
                break
        
        if json_file and os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            result["summary"] = json_data.get("summary", {})
            result["performance"] = json_data.get("performance", {})
            
        # 查找图表文件
        for file_path in report_files:
            if file_path.endswith('.png'):
                chart_name = Path(file_path).stem
                result["charts"][chart_name] = file_path
                
    except Exception as e:
        print(f"Error parsing backtest results: {e}")
    
    return result

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """获取任务状态"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return active_jobs[job_id]

@app.get("/api/jobs")
async def list_jobs():
    """获取所有任务列表"""
    return {"jobs": list(active_jobs.values())}

# 批量测试相关API

@app.post("/api/batch-test")
async def run_batch_test(request: BatchTestRequest, background_tasks: BackgroundTasks):
    """运行批量参数测试"""
    job_id = str(uuid.uuid4())
    
    # 创建任务记录
    active_jobs[job_id] = {
        "job_id": job_id,
        "type": "batch_test",
        "status": "pending",
        "progress": 0.0,
        "message": "批量测试任务已创建",
        "created_at": datetime.now(),
        "request": request.dict()
    }
    
    # 在后台执行批量测试
    background_tasks.add_task(_run_batch_test_task, job_id, request)
    
    return {"job_id": job_id, "message": "Batch test started"}

async def _run_batch_test_task(job_id: str, request: BatchTestRequest):
    """后台执行批量测试任务"""
    try:
        active_jobs[job_id].update({
            "status": "running",
            "progress": 10.0,
            "message": "正在生成参数组合..."
        })
        
        # 生成参数组合
        import itertools
        
        param_combinations = []
        param_names = list(request.parameter_ranges.keys())
        param_values = list(request.parameter_ranges.values())
        
        for combination in itertools.product(*param_values):
            param_dict = dict(zip(param_names, combination))
            param_combinations.append(param_dict)
        
        total_combinations = len(param_combinations)
        results = []
        
        active_jobs[job_id].update({
            "message": f"将执行 {total_combinations} 个参数组合的测试"
        })
        
        # 逐个执行参数组合测试
        for i, params in enumerate(param_combinations):
            active_jobs[job_id].update({
                "progress": 10.0 + (i / total_combinations) * 80.0,
                "message": f"正在测试参数组合 {i+1}/{total_combinations}: {params}"
            })
            
            try:
                # 这里应该实现具体的参数化回测逻辑
                # 现在先用模拟结果
                result = {
                    "parameters": params,
                    "total_return": 0.15 + (i % 10) * 0.01,  # 模拟结果
                    "max_drawdown": 0.05 + (i % 5) * 0.01,
                    "sharpe_ratio": 1.2 + (i % 8) * 0.1,
                    "win_rate": 0.6 + (i % 4) * 0.05
                }
                results.append(result)
                
            except Exception as e:
                print(f"Error in parameter combination {params}: {e}")
                continue
        
        # 完成任务
        active_jobs[job_id].update({
            "status": "completed",
            "progress": 100.0,
            "message": f"批量测试完成，共完成 {len(results)} 个组合",
            "completed_at": datetime.now(),
            "result": {
                "total_combinations": total_combinations,
                "completed_combinations": len(results),
                "results": results,
                "best_result": max(results, key=lambda x: x["total_return"]) if results else None
            }
        })
        
    except Exception as e:
        active_jobs[job_id].update({
            "status": "failed",
            "progress": 0.0,
            "message": f"批量测试失败: {str(e)}",
            "completed_at": datetime.now()
        })

# 报告相关API

@app.get("/api/reports")
async def list_reports():
    """获取所有报告列表"""
    reports = []
    
    for report_dir in reports_dir.iterdir():
        if report_dir.is_dir():
            report_files = []
            for file_path in report_dir.glob("*"):
                if file_path.is_file():
                    report_files.append({
                        "name": file_path.name,
                        "path": str(file_path.relative_to(project_root)),
                        "size": file_path.stat().st_size,
                        "type": file_path.suffix.lower()
                    })
            
            reports.append({
                "strategy_name": report_dir.name,
                "created_at": datetime.fromtimestamp(report_dir.stat().st_mtime),
                "files": report_files
            })
    
    return {"reports": reports}

@app.get("/api/reports/{strategy_name}/{filename}")
async def get_report_file(strategy_name: str, filename: str):
    """获取指定报告文件"""
    file_path = reports_dir / strategy_name / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    if filename.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        return content
    elif filename.endswith('.png'):
        return FileResponse(file_path, media_type='image/png')
    else:
        return FileResponse(file_path)

# 配置相关API

@app.get("/api/config")
async def get_app_config():
    """获取应用配置"""
    config = get_config()
    return {
        "data_sources": {name: {"enabled": source.enabled, "type": type(source).__name__} 
                        for name, source in config.data_sources.items()},
        "default_data_source": config.default_data_source,
        "backtest": {
            "initial_cash": config.backtest.initial_cash,
            "commission_rate": config.backtest.commission_rate,
            "min_commission": config.backtest.min_commission,
            "slippage": config.backtest.slippage
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)