from pathlib import Path
from typing import TYPE_CHECKING, Callable
from uuid import uuid4

try:
    import yappi
except ImportError as import_error:  # pragma: no cover
    msg = (
        "Profiling is not available without yappi installed. "
        "Either install it or disable profiling."
    )
    raise ImportError(msg) from import_error

if TYPE_CHECKING:
    from fastapi import FastAPI, Request, Response


def set_yappi_profiler(app: "FastAPI") -> None:
    @app.middleware("http")
    async def profile_process_time(
        request: "Request",
        call_next: Callable[["Request"], "Response"],
    ) -> "Response":
        yappi.clear_stats()
        yappi.set_clock_type("cpu")
        yappi.start()

        response = await call_next(request)

        yappi.stop()

        folder_location = Path(__file__).parents[2] / "profiling"
        folder_location.mkdir(parents=True, exist_ok=True)

        profiling_log_id = uuid4()

        yappi.convert2pstats(yappi.get_func_stats()).dump_stats(
            f"{folder_location}/{profiling_log_id}.pstats",
        )

        response.headers["profiling-log-id"] = str(profiling_log_id)

        return response
