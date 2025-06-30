import os
import json
from typing import Optional
from redis import Redis, ConnectionError  # type: ignore

from .models import JobInfo, JobStatus


class _InMemoryStore:
    def __init__(self):
        self._data = {}

    def get(self, job_id: str) -> Optional[JobInfo]:
        raw = self._data.get(job_id)
        if raw is None:
            return None
        return JobInfo(**raw)

    def set(self, job: JobInfo):
        self._data[job.job_id] = job.model_dump()

    def update(self, job_id: str, **kwargs):
        if job_id not in self._data:
            return
        self._data[job_id].update(kwargs)


class _RedisStore:
    def __init__(self, url: str):
        self._redis = Redis.from_url(url, decode_responses=True)

    def _key(self, job_id: str) -> str:
        return f"payperuse:{job_id}"

    def get(self, job_id: str) -> Optional[JobInfo]:
        data = self._redis.get(self._key(job_id))
        if not data:
            return None
        return JobInfo(**json.loads(data))

    def set(self, job: JobInfo):
        self._redis.set(self._key(job.job_id), job.model_dump_json(), ex=60 * 60 * 24)

    def update(self, job_id: str, **kwargs):
        key = self._key(job_id)
        pipe = self._redis.pipeline()
        pipe.get(key)
        data = pipe.execute()[0]
        if not data:
            return
        obj = json.loads(data)
        obj.update(kwargs)
        pipe.set(key, json.dumps(obj), ex=60 * 60 * 24)
        pipe.execute()


# Select backend
_redis_url = os.getenv("REDIS_URL")
_store = None
if _redis_url:
    try:
        _store = _RedisStore(_redis_url)
    except ConnectionError:
        _store = _InMemoryStore()
else:
    _store = _InMemoryStore()


class JobStore:
    """Facade for job persistence."""

    def get(self, job_id: str) -> Optional[JobInfo]:
        return _store.get(job_id)

    def save(self, job: JobInfo):
        _store.set(job)

    def update(self, job_id: str, **kwargs):
        _store.update(job_id, **kwargs)


global_job_store = JobStore() 