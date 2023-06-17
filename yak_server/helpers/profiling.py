import sys
from pathlib import Path
from typing import TYPE_CHECKING, Callable
from uuid import uuid4

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources

import yappi

if TYPE_CHECKING:
    from fastapi import FastAPI, Request, Response


def set_yappi_profiler(app: "FastAPI") -> None:
    @app.middleware("http")
    async def profile_process_time(
        request: "Request",
        call_next: Callable[["Request"], "Response"],
    ) -> "Response":
        yappi.set_clock_type("cpu")
        yappi.start()

        response = await call_next(request)

        yappi.stop()

        with resources.as_file(resources.files("yak_server") / ".." / "profiling") as path:
            folder_location = path

        folder_location.mkdir(parents=True, exist_ok=True)
        profiling_log_id = uuid4()

        with Path(f"{folder_location}/{profiling_log_id}.log") as path, path.open(mode="w") as file:
            stats = yappi.get_func_stats()
            stats.print_all(
                out=file,
                columns={
                    0: ("name", 180),
                    1: ("ncall", 8),
                    2: ("tsub", 8),
                    3: ("ttot", 8),
                    4: ("tavg", 8),
                },
            )

            response.headers["profiling-log-id"] = str(profiling_log_id)

        return response
