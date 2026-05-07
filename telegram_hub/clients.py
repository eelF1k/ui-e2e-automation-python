from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx


class BackendHub:
    def __init__(self, max_retries: int = 3, backoff_seconds: float = 0.5) -> None:
        self._max_retries = max(0, max_retries)
        self._backoff = max(0.05, backoff_seconds)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0, connect=15.0),
            headers={"User-Agent": "TelegramHeavyHub/2"},
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _with_retry(self, coro_factory):
        last: BaseException | None = None
        for attempt in range(self._max_retries + 1):
            try:
                return await coro_factory()
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
                last = exc
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code not in (
                    429,
                    500,
                    502,
                    503,
                    504,
                ):
                    raise
                if attempt >= self._max_retries:
                    raise
                await asyncio.sleep(self._backoff * (2**attempt))
        assert last is not None
        raise last

    async def http_get_json(self, url: str) -> Any:

        async def go():
            r = await self._client.get(url)
            r.raise_for_status()
            return r.json()

        return await self._with_retry(go)

    async def http_get_text(self, url: str) -> tuple[str, str]:

        async def go():
            r = await self._client.get(url)
            r.raise_for_status()
            return r.text, r.headers.get("content-type", "")

        return await self._with_retry(go)

    async def http_post_json(
        self, url: str, payload: dict[str, Any], headers: dict[str, str] | None = None
    ) -> Any:

        async def go():
            r = await self._client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            return r.json()

        return await self._with_retry(go)

    async def http_post_form(self, url: str, params: dict[str, Any]) -> Any:

        async def go():
            r = await self._client.post(url, params=params)
            r.raise_for_status()
            return r.json()

        return await self._with_retry(go)

    async def project2_list_invoices(self, base: str, jwt_token: str) -> Any:
        url = base.rstrip("/") + "/api/invoices/"
        headers = {"Authorization": f"Bearer {jwt_token}"}

        async def go():
            r = await self._client.get(url, headers=headers)
            r.raise_for_status()
            return r.json()

        return await self._with_retry(go)

    async def project3_health(self, base: str) -> Any:
        return await self.http_get_json(base.rstrip("/") + "/api/v1/health")

    async def project3_root(self, base: str) -> Any:
        return await self.http_get_json(base.rstrip("/") + "/")

    async def project4_health(self, base: str) -> Any:
        return await self.http_get_json(base.rstrip("/") + "/api/v1/health")

    async def project4_ready(self, base: str) -> Any:
        return await self.http_get_json(base.rstrip("/") + "/api/v1/ready")

    async def project4_metrics_plain(self, base: str) -> tuple[str, str]:
        url = base.rstrip("/") + "/api/v1/metrics"
        return await self.http_get_text(url)

    async def project4_search(self, base: str, q: str, limit: int = 5) -> Any:
        url = base.rstrip("/") + "/api/v1/search"

        async def go():
            r = await self._client.get(url, params={"q": q, "limit": limit})
            r.raise_for_status()
            return r.json()

        return await self._with_retry(go)

    async def project4_search_rerank(
        self, base: str, q: str, limit: int = 5, retrieval_limit: int = 15, strategy: str = "hybrid"
    ) -> Any:
        url = base.rstrip("/") + "/api/v1/search/rerank"

        async def go():
            r = await self._client.get(
                url,
                params={"q": q, "limit": limit, "retrieval_limit": retrieval_limit, "strategy": strategy},
            )
            r.raise_for_status()
            return r.json()

        return await self._with_retry(go)

    async def project4_rag(self, base: str, question: str, top_k: int = 5, strategy: str = "hybrid") -> Any:
        url = base.rstrip("/") + "/api/v1/rag/answer"
        body = {"question": question, "top_k": top_k, "strategy": strategy}
        return await self.http_post_json(url, body)

    async def project4_ingest(
        self,
        base: str,
        source_name: str,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> Any:
        url = base.rstrip("/") + "/api/v1/ingestion/text"
        body = {"source_name": source_name, "text": text, "chunk_size": chunk_size, "overlap": overlap}
        return await self.http_post_json(url, body)

    async def project4_ingest_async(
        self,
        base: str,
        source_name: str,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> Any:
        url = base.rstrip("/") + "/api/v1/ingestion/text/async"
        body = {"source_name": source_name, "text": text, "chunk_size": chunk_size, "overlap": overlap}
        return await self.http_post_json(url, body)

    async def project4_ops_jobs(self, base: str, limit: int = 10) -> Any:
        url = base.rstrip("/") + "/api/v1/ops/jobs"

        async def go():
            r = await self._client.get(url, params={"limit": limit})
            r.raise_for_status()
            return r.json()

        return await self._with_retry(go)

    async def project4_ops_audit(self, base: str, limit: int = 20) -> Any:
        url = base.rstrip("/") + "/api/v1/ops/audit"

        async def go():
            r = await self._client.get(url, params={"limit": limit})
            r.raise_for_status()
            return r.json()

        return await self._with_retry(go)

    async def project4_ops_create_job(self, base: str, source_name: str) -> Any:
        url = base.rstrip("/") + "/api/v1/ops/jobs"
        return await self.http_post_form(url, params={"source_name": source_name})

    async def project5_health(self, base: str) -> Any:
        return await self.http_get_json(base.rstrip("/") + "/api/v1/health")

    async def project5_metrics_plain(self, base: str) -> tuple[str, str]:
        return await self.http_get_text(base.rstrip("/") + "/api/v1/metrics")

    async def project5_revenue(self, base: str, days: int = 30) -> Any:
        url = base.rstrip("/") + "/api/v1/ops/revenue-by-store"

        async def go():
            r = await self._client.get(url, params={"days": days})
            r.raise_for_status()
            return r.json()

        return await self._with_retry(go)

    async def project5_top_skus(self, base: str, days: int = 30, limit: int = 10) -> Any:
        url = base.rstrip("/") + "/api/v1/ops/top-skus"

        async def go():
            r = await self._client.get(url, params={"days": days, "limit": limit})
            r.raise_for_status()
            return r.json()

        return await self._with_retry(go)

    async def project5_safe_sql(self, base: str, sql: str, max_rows: int = 50) -> Any:
        url = base.rstrip("/") + "/api/v1/ops/safe-sql"
        return await self.http_post_json(url, {"sql": sql, "max_rows": max_rows})

    async def project5_nl_sql(self, base: str, question: str, max_rows: int = 100) -> Any:
        url = base.rstrip("/") + "/api/v1/ops/nl-sql"
        return await self.http_post_json(url, {"question": question, "max_rows": max_rows})

    async def project5_rag(self, base: str, question: str, top_k: int = 4) -> Any:
        url = base.rstrip("/") + "/api/v1/ops/rag/answer"
        return await self.http_post_json(url, {"question": question, "top_k": top_k})

    async def project5_prompt_run(self, base: str, task: str, context: str = "", temperature: float = 0.2) -> Any:
        url = base.rstrip("/") + "/api/v1/ops/prompt/run"
        body = {"task": task, "context": context, "temperature": temperature}
        return await self.http_post_json(url, body)

    async def project5_prompt_compare(self, base: str, task: str, context: str, providers: list[str]) -> Any:
        url = base.rstrip("/") + "/api/v1/ops/prompt/compare"
        body = {"task": task, "context": context, "providers": providers, "temperature": 0.2}
        return await self.http_post_json(url, body)


def pretty_json(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    except Exception:
        return repr(obj)
