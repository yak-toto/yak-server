from collections.abc import Awaitable
from pathlib import Path
from typing import TYPE_CHECKING, Callable
from uuid import uuid4

from fastapi import FastAPI

from yak_server import create_app as create_yak_app

try:
    import yappi
except ImportError:  # pragma: no cover
    # Very common pattern for optional dependency imports
    yappi = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from fastapi import Request, Response


def set_yappi_profiler(app: "FastAPI") -> None:
    if yappi is None:
        msg = "Profiling is not available without yappi installed."
        raise NotImplementedError(msg)

    @app.middleware("http")
    async def profile_process_time(
        request: "Request",
        call_next: Callable[["Request"], Awaitable["Response"]],
    ) -> "Response":
        yappi.clear_stats()
        yappi.set_clock_type("cpu")
        yappi.start()

        response = await call_next(request)

        yappi.stop()

        folder_location = Path(__file__).parents[1] / "profiling"
        folder_location.mkdir(parents=True, exist_ok=True)

        profiling_log_id = uuid4()

        yappi.convert2pstats(yappi.get_func_stats()).dump_stats(
            folder_location / f"{profiling_log_id}.pstats"
        )

        response.headers["profiling-log-id"] = str(profiling_log_id)

        return response


def create_app() -> FastAPI:
    app = create_yak_app()

    set_yappi_profiler(app)

    return app
