"""FastAPI application entrypoint for the Internship Copilot backend."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from career_agent.api.routes import applications, browser, health, jobs, knowledge, messages


def create_app() -> FastAPI:
    app = FastAPI(
        title="Internship Copilot API",
        version="1.3",
        description="FastAPI backend for the evidence-grounded Internship Copilot prototype.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(jobs.router)
    app.include_router(messages.router)
    app.include_router(applications.router)
    app.include_router(knowledge.router)
    app.include_router(browser.router)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):  # noqa: ARG001
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "code": "internal_error"},
        )

    return app


app = create_app()
