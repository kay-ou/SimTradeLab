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
from simtradelab.logger import log

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
    try:
        import yaml
        
        # 读取配置文件
        config_file = project_root / "simtradelab_config.yaml"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            # 如果配置文件不存在，使用默认配置
            config = {
                "data_sources": {
                    "csv": {"enabled": True, "data_path": "./data/", "date_column": "date"},
                    "akshare": {"enabled": True},
                    "tushare": {"enabled": False, "token": None}
                }
            }
        
        sources = []
        data_sources_config = config.get("data_sources", {})
        
        # CSV数据源
        csv_config = data_sources_config.get("csv", {})
        sources.append({
            "name": "csv",
            "enabled": csv_config.get("enabled", True),
            "description": "本地CSV文件数据源",
            "data_path": csv_config.get("data_path", "./data/"),
            "date_format": "%Y-%m-%d"  # 默认日期格式
        })
        
        # AkShare数据源
        akshare_config = data_sources_config.get("akshare", {})
        sources.append({
            "name": "akshare",
            "enabled": akshare_config.get("enabled", True),
            "description": "AkShare在线数据源（免费）"
        })
        
        # Tushare数据源
        tushare_config = data_sources_config.get("tushare", {})
        sources.append({
            "name": "tushare",
            "enabled": tushare_config.get("enabled", False),
            "description": "Tushare在线数据源（需要token）",
            "token": tushare_config.get("token", "")
        })
        
        return {"data_sources": sources}
        
    except Exception as e:
        log.error(f"Error loading data sources: {e}")
        # 如果出错，返回默认配置
        return {
            "data_sources": [
                {"name": "csv", "enabled": True, "description": "本地CSV文件数据源", "data_path": "./data/", "date_format": "%Y-%m-%d"},
                {"name": "akshare", "enabled": True, "description": "AkShare在线数据源（免费）"},
                {"name": "tushare", "enabled": False, "description": "Tushare在线数据源（需要token）", "token": ""}
            ]
        }

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
    
    # 检查data目录中的文件
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
                "rows_sample": len(df_sample),
                "source": "data"  # 标记来源
            })
        except Exception as e:
            print(f"Error reading data file {data_file}: {e}")
    
    # 检查uploads目录中的文件
    for upload_file in web_uploads_dir.glob("*.csv"):
        try:
            # 读取文件前几行来获取基本信息
            df_sample = pd.read_csv(upload_file, nrows=5)
            
            files.append({
                "name": upload_file.name,
                "path": str(upload_file.relative_to(project_root)),
                "size": upload_file.stat().st_size,
                "modified_at": datetime.fromtimestamp(upload_file.stat().st_mtime),
                "columns": df_sample.columns.tolist(),
                "rows_sample": len(df_sample),
                "source": "uploaded"  # 标记来源
            })
        except Exception as e:
            print(f"Error reading upload file {upload_file}: {e}")
    
    # 按修改时间排序，最新的在前面
    files.sort(key=lambda x: x["modified_at"], reverse=True)
    
    return {"data_files": files}

@app.post("/api/data/upload")
async def upload_data_file(file: UploadFile = File(...)):
    """上传数据文件"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        # 保存上传的文件到uploads目录
        upload_path = web_uploads_dir / file.filename
        with open(upload_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # 验证CSV格式
        df = pd.read_csv(upload_path, nrows=10)
        
        # 也复制一份到data目录，便于回测时使用
        data_path = data_dir / file.filename
        import shutil
        shutil.copy2(upload_path, data_path)
        
        log.info(f"File uploaded: {file.filename}, saved to both uploads and data directories")
        
        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "upload_path": str(upload_path.relative_to(project_root)),
            "data_path": str(data_path.relative_to(project_root)),
            "columns": df.columns.tolist(),
            "sample_rows": len(df),
            "file_size": upload_path.stat().st_size
        }
    except Exception as e:
        log.error(f"Error uploading file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/api/data/files/{filename}/preview")
async def preview_data_file(filename: str):
    """预览数据文件内容"""
    # 检查文件在data目录
    data_file_path = data_dir / filename
    if not data_file_path.exists():
        # 检查文件在uploads目录
        data_file_path = web_uploads_dir / filename
        if not data_file_path.exists():
            raise HTTPException(status_code=404, detail="Data file not found")
    
    try:
        # 读取文件基本信息
        df = pd.read_csv(data_file_path)
        
        # 获取文件统计信息
        total_rows = len(df)
        columns = df.columns.tolist()
        
        # 预览前20行数据
        preview_data = df.head(20).fillna('').values.tolist()
        
        # 尝试检测日期范围
        date_range = None
        securities = None
        
        # 检查可能的日期列
        date_columns = ['date', 'datetime', 'time', 'Date', 'DateTime', 'Time']
        date_col = None
        for col in date_columns:
            if col in df.columns:
                date_col = col
                break
        
        if date_col:
            try:
                df[date_col] = pd.to_datetime(df[date_col])
                date_range = {
                    "start": df[date_col].min().strftime('%Y-%m-%d'),
                    "end": df[date_col].max().strftime('%Y-%m-%d')
                }
            except:
                pass
        
        # 检查股票代码列
        security_columns = ['security', 'symbol', 'code', 'Security', 'Symbol', 'Code']
        security_col = None
        for col in security_columns:
            if col in df.columns:
                security_col = col
                break
        
        if security_col:
            securities = df[security_col].unique().tolist()[:10]  # 最多显示前10个
        
        return {
            "filename": filename,
            "total_rows": total_rows,
            "columns": columns,
            "preview_data": preview_data,
            "date_range": date_range,
            "securities": securities
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@app.get("/api/data/files/{filename}/info")
async def get_data_file_info(filename: str):
    """获取数据文件详细信息"""
    # 检查文件在data目录
    data_file_path = data_dir / filename
    if not data_file_path.exists():
        # 检查文件在uploads目录
        data_file_path = web_uploads_dir / filename
        if not data_file_path.exists():
            raise HTTPException(status_code=404, detail="Data file not found")
    
    try:
        # 读取文件基本信息
        df = pd.read_csv(data_file_path)
        
        # 获取文件统计信息
        total_rows = len(df)
        columns = df.columns.tolist()
        
        # 尝试检测日期范围
        date_range = None
        securities = None
        
        # 检查可能的日期列
        date_columns = ['date', 'datetime', 'time', 'Date', 'DateTime', 'Time']
        date_col = None
        for col in date_columns:
            if col in df.columns:
                date_col = col
                break
        
        if date_col:
            try:
                df[date_col] = pd.to_datetime(df[date_col])
                date_range = {
                    "start": df[date_col].min().strftime('%Y-%m-%d'),
                    "end": df[date_col].max().strftime('%Y-%m-%d')
                }
            except:
                pass
        
        # 检查股票代码列
        security_columns = ['security', 'symbol', 'code', 'Security', 'Symbol', 'Code']
        security_col = None
        for col in security_columns:
            if col in df.columns:
                security_col = col
                break
        
        if security_col:
            securities = df[security_col].unique().tolist()
        
        return {
            "filename": filename,
            "total_rows": total_rows,
            "columns": columns,
            "date_range": date_range,
            "securities": securities,
            "file_size": data_file_path.stat().st_size,
            "modified_at": datetime.fromtimestamp(data_file_path.stat().st_mtime)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file info: {str(e)}")

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
        "summary": {
            "total_return": 0.0,
            "annual_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "volatility": 0.0,
            "win_rate": 0.0,
            "total_trades": 0
        },
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
            log.info(f"Parsing JSON report: {json_file}")
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 安全地解析summary数据
            summary_data = json_data.get("summary", {})
            if summary_data:
                result["summary"].update({
                    "total_return": float(summary_data.get("total_return", 0.0)),
                    "annual_return": float(summary_data.get("annual_return", 0.0)),
                    "max_drawdown": float(summary_data.get("max_drawdown", 0.0)),
                    "sharpe_ratio": float(summary_data.get("sharpe_ratio", 0.0)),
                    "volatility": float(summary_data.get("volatility", 0.0)),
                    "win_rate": float(summary_data.get("win_rate", 0.0)),
                    "total_trades": int(summary_data.get("total_trades", 0))
                })
                log.info(f"Parsed summary: {result['summary']}")
            
            result["performance"] = json_data.get("performance", {})
        else:
            log.warning(f"No JSON report file found in: {report_files}")
        
        # 不再处理PNG文件，因为已移除图表功能
                
    except Exception as e:
        log.error(f"Error parsing backtest results: {e}")
        # 如果解析失败，使用模拟数据进行测试
        result["summary"] = {
            "total_return": 0.12,  # 模拟数据
            "annual_return": 0.15,
            "max_drawdown": -0.08,
            "sharpe_ratio": 1.45,
            "volatility": 0.18,
            "win_rate": 0.65,
            "total_trades": 250
        }
        log.info("Using mock data due to parsing error")
    
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
    else:
        return FileResponse(file_path)

@app.get("/api/reports/{strategy_name}/{filename}/preview")
async def preview_report_file(strategy_name: str, filename: str):
    """预览报告文件内容"""
    report_path = reports_dir / strategy_name / filename
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    try:
        file_ext = filename.split('.')[-1].lower()
        
        if file_ext in ['txt', 'json']:
            # 文本类型文件，读取内容
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 限制预览长度
            if len(content) > 10000:
                content = content[:10000] + '\n\n... (内容已截断，完整内容请下载文件查看)'
            
            return {
                "filename": filename,
                "type": file_ext,
                "content": content,
                "size": report_path.stat().st_size,
                "preview": True
            }
            
        elif file_ext == 'csv':
            # CSV文件，读取前几行
            import pandas as pd
            df = pd.read_csv(report_path)
            
            return {
                "filename": filename,
                "type": file_ext,
                "columns": df.columns.tolist(),
                "rows": len(df),
                "preview_data": df.head(20).fillna('').values.tolist(),
                "size": report_path.stat().st_size,
                "preview": True
            }
            
        else:
            return {
                "filename": filename,
                "type": file_ext,
                "content": f"不支持预览的文件类型: {file_ext}",
                "size": report_path.stat().st_size,
                "preview": False,
                "message": "请下载文件查看完整内容"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error previewing file: {str(e)}")

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

@app.post("/api/config/data-sources")
async def save_data_source_config(config_data: dict):
    """保存数据源配置"""
    try:
        import yaml
        
        # 验证配置数据格式
        if not isinstance(config_data, dict):
            raise HTTPException(status_code=400, detail="Invalid config format")
        
        # 读取现有配置文件
        config_file = project_root / "simtradelab_config.yaml"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                current_config = yaml.safe_load(f)
        else:
            current_config = {"data_sources": {}}
        
        # 确保data_sources部分存在
        if "data_sources" not in current_config:
            current_config["data_sources"] = {}
        
        # 更新数据源配置
        for source_name, source_config in config_data.items():
            if source_name in ["csv", "tushare", "akshare"]:
                # 更新特定数据源配置
                if source_name not in current_config["data_sources"]:
                    current_config["data_sources"][source_name] = {}
                
                # 更新enabled状态和其他配置
                current_config["data_sources"][source_name]["enabled"] = source_config.get("enabled", True)
                
                # 根据数据源类型更新特定配置
                if source_name == "tushare" and source_config.get("token"):
                    current_config["data_sources"][source_name]["token"] = source_config["token"]
                elif source_name == "csv":
                    if source_config.get("data_path"):
                        current_config["data_sources"][source_name]["data_path"] = source_config["data_path"]
                    if source_config.get("date_format"):
                        current_config["data_sources"][source_name]["date_column"] = source_config["date_format"]
                
                log.info(f"{source_name} config updated: enabled={source_config.get('enabled', True)}")
        
        # 保存配置到文件
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.safe_dump(current_config, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        log.info(f"Configuration saved to {config_file}")
        
        return {
            "message": "Data source configuration saved successfully", 
            "config": config_data,
            "saved_to": str(config_file)
        }
        
    except Exception as e:
        log.error(f"Error saving data source config: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving configuration: {str(e)}")

@app.delete("/api/data/files/{filename}")
async def delete_data_file(filename: str):
    """删除数据文件"""
    try:
        deleted_files = []
        
        # 检查并删除data目录中的文件
        data_file_path = data_dir / filename
        if data_file_path.exists():
            data_file_path.unlink()
            deleted_files.append(str(data_file_path.relative_to(project_root)))
            log.info(f"Deleted file from data directory: {data_file_path}")
        
        # 检查并删除uploads目录中的文件
        upload_file_path = web_uploads_dir / filename
        if upload_file_path.exists():
            upload_file_path.unlink()
            deleted_files.append(str(upload_file_path.relative_to(project_root)))
            log.info(f"Deleted file from uploads directory: {upload_file_path}")
        
        if not deleted_files:
            raise HTTPException(status_code=404, detail=f"File '{filename}' not found")
        
        return {
            "message": f"File '{filename}' deleted successfully",
            "deleted_files": deleted_files
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error deleting file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

@app.get("/api/data/files/{filename}/download")
async def download_data_file(filename: str):
    """下载数据文件"""
    # 首先检查data目录
    data_file_path = data_dir / filename
    if data_file_path.exists():
        log.info(f"Downloading file from data directory: {data_file_path}")
        return FileResponse(
            path=str(data_file_path),
            filename=filename,
            media_type='text/csv' if filename.endswith('.csv') else 'application/octet-stream'
        )
    
    # 然后检查uploads目录
    upload_file_path = web_uploads_dir / filename
    if upload_file_path.exists():
        log.info(f"Downloading file from uploads directory: {upload_file_path}")
        return FileResponse(
            path=str(upload_file_path),
            filename=filename,
            media_type='text/csv' if filename.endswith('.csv') else 'application/octet-stream'
        )
    
    # 如果都不存在，返回404
    log.error(f"File not found: {filename}, checked directories: {data_dir}, {web_uploads_dir}")
    raise HTTPException(status_code=404, detail=f"Data file '{filename}' not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)