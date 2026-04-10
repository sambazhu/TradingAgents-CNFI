#!/usr/bin/env python3
"""
前端调用链 E2E 测试脚本

目标：
1. 按前端真实调用链验证单股分析
2. 使用数据库中的 Gildata 配置，而不是命令行注入 token
3. 保存完整请求、响应、轮询与结果日志
"""

from __future__ import annotations

import json
import random
import time
import argparse
from datetime import date, timedelta
from pathlib import Path

import requests


BASE_URL = "http://127.0.0.1:8010"
USERNAME = "admin"
PASSWORD = "admin123"
POLL_INTERVAL_SECONDS = 5
MAX_WAIT_SECONDS = 1800
SUBMIT_TIMEOUT_SECONDS = 180

CANDIDATE_STOCKS = [
    ("000001", "平安银行"),
    ("000651", "格力电器"),
    ("600036", "招商银行"),
    ("600519", "贵州茅台"),
    ("600900", "长江电力"),
]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2))


def parse_args():
    parser = argparse.ArgumentParser(description="前端调用链 E2E 测试脚本")
    parser.add_argument("--stock-code", dest="stock_code", help="指定股票代码")
    parser.add_argument("--stock-name", dest="stock_name", default="", help="指定股票名称")
    parser.add_argument("--analysis-date", dest="analysis_date", help="指定分析日期，格式 YYYY-MM-DD")
    parser.add_argument(
        "--selected-analysts",
        dest="selected_analysts",
        default="market,fundamentals",
        help="分析师列表，逗号分隔，如 market,fundamentals,news,social",
    )
    parser.add_argument(
        "--include-sentiment",
        dest="include_sentiment",
        choices=["true", "false"],
        default="true",
        help="是否启用情绪链路",
    )
    parser.add_argument(
        "--include-risk",
        dest="include_risk",
        choices=["true", "false"],
        default="true",
        help="是否启用风险链路",
    )
    parser.add_argument(
        "--tag",
        dest="tag",
        default="",
        help="结果目录附加标签",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    today = date.today()
    analysis_date = (
        date.fromisoformat(args.analysis_date)
        if args.analysis_date
        else today - timedelta(days=1)
    )

    if args.stock_code:
        stock_code = args.stock_code
        stock_name = args.stock_name or args.stock_code
    else:
        stock_code, stock_name = random.choice(CANDIDATE_STOCKS)

    selected_analysts = [item.strip() for item in args.selected_analysts.split(",") if item.strip()]
    include_sentiment = args.include_sentiment == "true"
    include_risk = args.include_risk == "true"
    run_id = time.strftime("%Y%m%d_%H%M%S")
    tag_suffix = f"_{args.tag}" if args.tag else ""
    out_dir = Path("results") / f"e2e_frontend_chain_{run_id}{tag_suffix}"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "base_url": BASE_URL,
        "username": USERNAME,
        "stock_code": stock_code,
        "stock_name": stock_name,
        "analysis_date": analysis_date.isoformat(),
        "selected_analysts": selected_analysts,
        "include_sentiment": include_sentiment,
        "include_risk": include_risk,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "notes": [
            "backend started on 8010",
            "expected gildata token source: mongodb active system_configs",
            "provider/model: dashscope / kimi-k2.5",
        ],
    }
    write_json(out_dir / "run_summary.json", summary)
    write_text(out_dir / "selected_stock.env", f"STOCK_CODE={stock_code}\nSTOCK_NAME={stock_name}\nANALYSIS_DATE={analysis_date.isoformat()}\n")

    session = requests.Session()
    session.trust_env = False
    session.headers.update({"Content-Type": "application/json"})

    login_payload = {"username": USERNAME, "password": PASSWORD}
    write_json(out_dir / "login_request.json", login_payload)
    login_resp = session.post(f"{BASE_URL}/api/auth/login", json=login_payload, timeout=30)
    login_data = login_resp.json()
    write_json(out_dir / "login_response.json", login_data)
    login_resp.raise_for_status()

    token = login_data["data"]["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})

    submit_payload = {
        "symbol": stock_code,
        "stock_code": stock_code,
        "parameters": {
            "market_type": "A股",
            "analysis_date": analysis_date.isoformat(),
            "research_depth": "标准",
            "selected_analysts": selected_analysts,
            "include_sentiment": include_sentiment,
            "include_risk": include_risk,
            "language": "zh-CN",
            "quick_analysis_model": "kimi-k2.5",
            "deep_analysis_model": "kimi-k2.5",
        },
    }
    write_json(out_dir / "submit_request.json", submit_payload)
    submit_resp = session.post(
        f"{BASE_URL}/api/analysis/single",
        json=submit_payload,
        timeout=SUBMIT_TIMEOUT_SECONDS,
    )
    submit_data = submit_resp.json()
    write_json(out_dir / "submit_response.json", submit_data)
    submit_resp.raise_for_status()

    task_id = submit_data["data"]["task_id"]
    write_text(out_dir / "task_id.env", f"TASK_ID={task_id}\n")

    status_log_path = out_dir / "status_poll.log"
    started = time.time()
    final_status = None

    while time.time() - started < MAX_WAIT_SECONDS:
        status_resp = session.get(f"{BASE_URL}/api/analysis/tasks/{task_id}/status", timeout=30)
        status_data = status_resp.json()
        status_resp.raise_for_status()

        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        line = json.dumps(
            {
                "time": now_str,
                "status": status_data.get("data", {}).get("status"),
                "progress": status_data.get("data", {}).get("progress"),
                "current_step": status_data.get("data", {}).get("current_step"),
                "message": status_data.get("data", {}).get("message"),
            },
            ensure_ascii=False,
        )
        with status_log_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

        final_status = status_data.get("data", {}).get("status")
        if final_status in {"completed", "failed", "cancelled"}:
            write_json(out_dir / "last_status_response.json", status_data)
            break

        time.sleep(POLL_INTERVAL_SECONDS)

    if final_status != "completed":
        write_text(out_dir / "final_status.env", f"FINAL_STATUS={final_status}\n")
        raise SystemExit(f"Task did not complete successfully, final status={final_status}")

    result_resp = session.get(f"{BASE_URL}/api/analysis/tasks/{task_id}/result", timeout=60)
    result_data = result_resp.json()
    write_json(out_dir / "result_response.json", result_data)
    result_resp.raise_for_status()

    final_status_summary = {
        "task_id": task_id,
        "final_status": final_status,
        "finished_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "stock_code": stock_code,
        "stock_name": stock_name,
        "analysis_date": analysis_date.isoformat(),
        "decision": result_data.get("data", {}).get("decision"),
    }
    write_json(out_dir / "final_status.json", final_status_summary)
    write_text(out_dir / "final_status.env", f"FINAL_STATUS={final_status}\nTASK_ID={task_id}\n")

    print(json.dumps(final_status_summary, ensure_ascii=False, indent=2))
    print(str(out_dir.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
