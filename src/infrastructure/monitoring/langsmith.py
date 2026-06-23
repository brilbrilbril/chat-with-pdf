from __future__ import annotations
import os

LANGSMITH_ENABLED = bool(os.getenv("LANGCHAIN_API_KEY"))

if LANGSMITH_ENABLED:
    from langsmith import traceable
    from langsmith.wrappers import wrap_openai
else:
    def traceable(*args, **kwargs):
        def decorator(fn):
            return fn
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

    def wrap_openai(client):
        return client


def get_traced_client(client):
    if not LANGSMITH_ENABLED:
        return client
    return wrap_openai(client)