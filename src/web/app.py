"""A deliberately small local control surface; never exposes the Docker API."""

import asyncio
import json
import secrets
import time
from collections import deque
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Route

from src.minecraft_server_manager import MinecraftServerManager
from src.utils.file_manager import FileManager

STATIC = Path(__file__).parent / "static"


def create_app(
    manager: MinecraftServerManager,
    *,
    admin_token: str,
    port: int = 8765,
) -> Starlette:
    """Bind one fixed profile; tokens are ephemeral and supplied by the launcher."""
    if len(admin_token) < 32:
        raise ValueError("A strong admin access token is required")
    origin = f"http://127.0.0.1:{port}"
    operation: dict[str, Any] = {"state": "idle"}
    task: asyncio.Task[None] | None = None
    sessions: dict[str, dict[str, Any]] = {}
    attempts: deque[float] = deque(maxlen=8)
    login_lock = asyncio.Lock()

    @asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        yield
        # Never cancel a world-saving thread during ordinary shutdown.
        if task is not None:
            await task

    def role(request: Request) -> str | None:
        authorization = request.headers.get("authorization", "")
        if not authorization.startswith("Bearer "):
            return None
        supplied = authorization[7:]
        if not supplied.isascii() or len(supplied) > 128:
            return None
        if secrets.compare_digest(supplied, admin_token):
            return "admin"
        session = sessions.get(supplied)
        if session and session["expires"] > time.monotonic():
            return manager.accounts.valid_session(
                session["username"], session["revision"]
            )
        sessions.pop(supplied, None)
        return None

    async def payload(request: Request) -> dict[str, Any]:
        if request.headers.get("origin") != origin:
            raise ValueError("Request origin refused")
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > 8192:
                raise ValueError("Request too large")
        value = json.loads(raw)
        if not isinstance(value, dict) or any(
            not isinstance(v, str) for v in value.values()
        ):
            raise ValueError("Expected text fields")
        return value

    async def login(request: Request) -> Response:
        try:
            body = await payload(request)
        except (ValueError, UnicodeError):
            return JSONResponse({"error": "Invalid login request."}, 400)
        now = time.monotonic()
        if login_lock.locked() or (len(attempts) == 8 and now - attempts[0] < 60):
            return JSONResponse(
                {"error": "Too many attempts. Wait a minute and try again."}, 429
            )
        attempts.append(now)
        async with login_lock:
            user = await run_in_threadpool(
                manager.accounts.authenticate,
                body.get("username", ""),
                body.get("password", ""),
            )
        if user is None:
            return JSONResponse(
                {
                    "error": "Username or password is incorrect, or access has been revoked."
                },
                401,
            )
        for key in list(sessions):
            if sessions[key]["expires"] <= now:
                del sessions[key]
        if len(sessions) >= 128:
            return JSONResponse(
                {
                    "error": "Session limit reached. Ask the owner to restart the manager."
                },
                429,
            )
        credential = secrets.token_urlsafe(32)
        sessions[credential] = {**user, "expires": now + 8 * 3600}
        return JSONResponse({"token": credential})

    async def logout(request: Request) -> Response:
        if request.headers.get("origin") != origin:
            return Response(status_code=403)
        sessions.pop(
            request.headers.get("authorization", "").removeprefix("Bearer "), None
        )
        return JSONResponse({"ok": True})

    async def players(request: Request) -> Response:
        if role(request) != "admin":
            return JSONResponse({"error": "Sign in as the server admin."}, 403)
        if request.method == "GET":
            return JSONResponse(
                {
                    "players": manager.accounts.players(
                        manager.config.get("server.allowlist")
                    )
                }
            )
        try:
            body = await payload(request)
            if request.headers.get("x-confirm-profile") != manager.config.get(
                "profile"
            ):
                return JSONResponse({"error": "Confirm the target world."}, 400)
            if task is not None and not task.done():
                return JSONResponse(
                    {"error": "Wait for the world operation to finish."}, 409
                )
            await run_in_threadpool(
                manager.change_player, body.get("minecraft", ""), body.get("action", "")
            )
            return JSONResponse({"ok": True})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, 400)
        except (OSError, RuntimeError):
            return JSONResponse(
                {
                    "error": "Player settings may be saved, but game synchronization did not finish. Stop the game and check the CLI before assuming access was revoked."
                },
                409,
            )

    async def mods(request: Request) -> Response:
        if role(request) != "admin":
            return JSONResponse({"error": "Sign in as the server admin."}, 403)
        try:
            body = await payload(request)
            if request.headers.get("x-confirm-profile") != manager.config.get(
                "profile"
            ):
                raise ValueError("Confirm the target world")
            if body.get("enabled") not in {"true", "false"}:
                raise ValueError("Choose enable or disable")
            if task is not None and not task.done():
                raise ValueError("Wait for the active world operation")
            await run_in_threadpool(
                manager.set_mod_enabled,
                body.get("filename", ""),
                body["enabled"] == "true",
            )
            return JSONResponse({"ok": True})
        except (ValueError, FileExistsError) as exc:
            return JSONResponse({"error": str(exc)}, 400)
        except (OSError, RuntimeError):
            return JSONResponse(
                {
                    "error": "Stop the world before changing mods. If it is already stopped, check the CLI for details."
                },
                409,
            )

    async def setup(request: Request) -> Response:
        if role(request) != "admin":
            return JSONResponse({"error": "Sign in as the server admin."}, 403)
        try:
            body = await payload(request)
            if body.get("accept_eula") != "true":
                raise ValueError("Read and explicitly accept the Minecraft EULA first")
            if manager.marker.exists():
                raise ValueError("This world is already set up")
            if task is not None and not task.done():
                raise ValueError("Wait for the active operation")
            await run_in_threadpool(
                manager.change_player, body.get("minecraft", ""), "add"
            )
            await run_in_threadpool(manager.initialize, True)
            return JSONResponse({"ok": True})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, 400)
        except (RuntimeError, OSError):
            return JSONResponse(
                {"error": "Setup could not finish. Check the local CLI for details."},
                409,
            )

    async def home(request: Request) -> Response:
        return FileResponse(STATIC / "index.html")

    async def asset(request: Request) -> Response:
        name = request.path_params["name"]
        if name not in {"app.js", "style.css", "landscape.svg"}:
            return Response(status_code=404)
        return FileResponse(STATIC / name)

    async def snapshot(request: Request) -> Response:
        access = role(request)
        if access is None:
            return JSONResponse({"error": "Open your private clubhouse link."}, 401)
        cfg = manager.config
        result: dict[str, Any] = {
            "role": access,
            "profile": cfg.get("profile"),
            "version": cfg.get("server.version"),
            "forge": cfg.get("server.forge_version"),
            "java": cfg.get("server.java_version"),
            "memory": cfg.get("server.memory"),
            "connection": f"127.0.0.1:{cfg.get('server.port')}",
            "operation": dict(operation),
            "backups": [],
            "mods": [],
            "initialized": (manager.base_dir / "profile.json").is_file(),
        }
        try:
            status = await run_in_threadpool(manager.get_status)
            result.update({key: status[key] for key in ("running", "state", "health")})
            result["available"] = True
            result["security_verified"] = False
            if status["running"] and status["health"] == "healthy":
                try:
                    security = await run_in_threadpool(manager.verify_security)
                    result["security_verified"] = security.get("verified") is True
                except (RuntimeError, OSError, ValueError, KeyError):
                    result["security_error"] = (
                        "Live access checks did not pass. Stop the world and run the CLI security check before playing."
                    )
        except (RuntimeError, OSError, ValueError):
            result.update(
                available=False, running=False, state="unavailable", health="unknown"
            )
        if access == "admin":
            try:
                result["backups"] = [
                    {"name": p.name, "bytes": p.stat().st_size}
                    for p in FileManager.list_backups(manager.backup_dir)[:20]
                ]
                result["mods"] = await run_in_threadpool(manager.list_mods)
            except (OSError, ValueError, RuntimeError):
                result["inventory_error"] = (
                    "Inventory could not be read. Check the profile locally."
                )
        return JSONResponse(result)

    async def perform(action: str) -> None:
        try:
            result = await run_in_threadpool(getattr(manager, action))
            if result is False:
                raise RuntimeError("Operation did not succeed")
            operation.update(
                state="done",
                message={
                    "start": "Your world is ready. Time to explore!",
                    "stop": "World saved. See you next adventure!",
                    "backup": "A new recovery copy is safely stored.",
                }[action],
            )
        except (
            Exception
        ):  # Keep paths, Docker output and secrets out of HTTP responses.
            operation.update(
                state="failed",
                message=(
                    "That did not finish. Check the local CLI for details. "
                    "We did not force-stop the server."
                ),
            )

    async def action(request: Request) -> Response:
        nonlocal task
        access = role(request)
        if access is None:
            return JSONResponse({"error": "Your private link is needed."}, 401)
        # Exact origin plus non-cookie credentials prevent cross-site form/CSRF requests.
        if request.headers.get("origin") != origin:
            return JSONResponse({"error": "Request origin refused."}, 403)
        selected = request.path_params["action"]
        if selected not in {"start", "stop", "backup"}:
            return JSONResponse({"error": "Unknown action."}, 404)
        if selected != "start" and access != "admin":
            return JSONResponse({"error": "Sign in as the server admin."}, 403)
        if selected != "start" and request.headers.get(
            "x-confirm-profile"
        ) != manager.config.get("profile"):
            return JSONResponse({"error": "Confirm the target world first."}, 400)
        if task is not None and not task.done():
            return JSONResponse({"error": "An operation is already in progress."}, 409)
        operation.clear()
        operation.update(
            state="working",
            action=selected,
            message={
                "start": "Waking up your world. The first visit can take several minutes.",
                "stop": "Saving everyone's adventure before closing…",
                "backup": "Making a recovery copy of your stopped world…",
            }[selected],
        )
        task = asyncio.create_task(perform(selected))
        return JSONResponse(dict(operation), 202)

    app = Starlette(
        routes=[
            Route("/", home),
            Route("/assets/{name}", asset),
            Route("/api/status", snapshot),
            Route("/api/login", login, methods=["POST"]),
            Route("/api/logout", logout, methods=["POST"]),
            Route("/api/players", players, methods=["GET", "POST"]),
            Route("/api/setup", setup, methods=["POST"]),
            Route("/api/mods", mods, methods=["POST"]),
            Route("/api/actions/{action}", action, methods=["POST"]),
        ],
        lifespan=lifespan,
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1"])

    async def security_headers(request: Request, call_next: Any) -> Response:
        response: Response = await call_next(request)
        response.headers.update(
            {
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Cache-Control": "no-store",
                "X-Frame-Options": "DENY",
                "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            }
        )
        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=security_headers)
    return app


def serve(manager: MinecraftServerManager, port: int = 8765) -> None:
    import uvicorn

    if not 1024 <= port <= 65535:
        raise ValueError("UI port must be between 1024 and 65535")
    admin = secrets.token_urlsafe(32)
    print(f"Admin sign-in: http://127.0.0.1:{port}/", flush=True)
    print(
        f"Local owner link (keep private): http://127.0.0.1:{port}/#token={admin}",
        flush=True,
    )
    print("Links expire when the manager exits. Only this laptop can connect.")
    uvicorn.run(
        create_app(manager, admin_token=admin, port=port),
        host="127.0.0.1",
        port=port,
        access_log=False,
        proxy_headers=False,
    )
