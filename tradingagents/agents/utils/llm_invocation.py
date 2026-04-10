import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Optional


def resolve_llm_timeout(llm: Any, fallback: int = 180) -> int:
    """尽量从 LLM 实例中解析超时时间，解析失败时回退到默认值。"""
    for attr in ("request_timeout", "timeout"):
        value = getattr(llm, attr, None)
        if value is None:
            continue

        if isinstance(value, (list, tuple)):
            numeric_values = [float(item) for item in value if isinstance(item, (int, float))]
            if numeric_values:
                return int(max(numeric_values))
            continue

        if hasattr(value, "total_seconds"):
            try:
                return int(value.total_seconds())
            except Exception:
                continue

        if isinstance(value, (int, float)):
            return int(value)

    return fallback


def trim_prompt_text(
    text: Optional[str],
    max_chars: int,
    *,
    label: str,
    logger: Any,
) -> str:
    """裁剪超长文本，优先保留最新上下文，降低长 prompt 带来的阻塞风险。"""
    text = text or ""
    if len(text) <= max_chars:
        return text

    logger.info(
        f"✂️ [{label}] 输入过长，已裁剪: {len(text):,} -> {max_chars:,} 字符"
    )
    return f"[{label} 已截断，仅保留最近 {max_chars} 字符]\n{text[-max_chars:]}"


def invoke_llm_with_retry(
    llm: Any,
    prompt: str,
    *,
    logger: Any,
    role_name: str,
    max_retries: int = 2,
    timeout: Optional[int] = None,
    retry_delay: float = 2.0,
    min_content_length: int = 10,
):
    """为同步 LLM 调用增加硬超时、重试和详细日志。"""
    resolved_timeout = timeout or resolve_llm_timeout(llm)
    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        start_time = time.time()
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(llm.invoke, prompt)

        try:
            logger.info(
                f"🔄 [{role_name}] 调用LLM (尝试 {attempt}/{max_retries}, 超时 {resolved_timeout}s)"
            )
            response = future.result(timeout=resolved_timeout)
            elapsed = time.time() - start_time

            content = getattr(response, "content", "") or ""
            logger.info(f"⏱️ [{role_name}] LLM调用完成，耗时: {elapsed:.2f}秒")

            if len(content.strip()) < min_content_length:
                last_error = ValueError(f"{role_name} 响应内容过短")
                logger.warning(
                    f"⚠️ [{role_name}] 响应内容过短: {len(content.strip())} 字符"
                )
            else:
                return response

        except FutureTimeoutError:
            elapsed = time.time() - start_time
            last_error = TimeoutError(
                f"{role_name} LLM调用超过 {resolved_timeout} 秒，已触发硬超时"
            )
            logger.error(f"❌ [{role_name}] LLM调用超时，耗时: {elapsed:.2f}秒")
            future.cancel()
        except Exception as exc:
            elapsed = time.time() - start_time
            last_error = exc
            logger.error(
                f"❌ [{role_name}] LLM调用失败 (耗时: {elapsed:.2f}秒): {exc}"
            )
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        if attempt < max_retries:
            logger.info(f"🔄 [{role_name}] {retry_delay:.0f}秒后重试...")
            time.sleep(retry_delay)

    raise last_error or RuntimeError(f"{role_name} LLM调用失败")
