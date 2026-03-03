# Proposed Improvements & New Features

## High Priority — Bugs / Security Issues

~~**1. Wrong HTTP status code on locked bets** ✓ Done~~

~~`yak_server/v1/helpers/errors.py:108-115` — `LockedScoreBet` and `LockedBinaryBet` both return `HTTP_401_UNAUTHORIZED`. Locking is an authorization concern, not authentication. These should return `HTTP_403_FORBIDDEN`. Returning 401 tells clients to "try re-authenticating," which is misleading.~~

~~**2. `UserModel.password` column is too narrow** ✓ Done~~

~~`yak_server/database/models.py:37` — `sa.String(100)` for the password field. Argon2 hashes are typically 95–97 characters, but the spec allows longer outputs and future-proofing. A minimum of `String(200)` or `String(255)` is safer.~~

~~**3. No rate limiting on auth endpoints** ✓ Done~~

~~`yak_server/v1/routers/users.py:62-202` — `/login` and `/signup` have no throttling. A brute-force attack against `/login` is trivially possible. Adding `slowapi` (Starlette-compatible `limits` wrapper) as a middleware would take ~20 lines.~~

**4. Old revoked refresh tokens are never cleaned up**

`yak_server/database/models.py:144-160` — Every login, signup, and refresh adds a `RefreshTokenModel` row. Revoked tokens are marked but never deleted. Over time this table grows unboundedly. Add a CLI command (or background task) to purge tokens older than `jwt_refresh_expiration_time`.

**14. Division by zero in points computation with a single player**

`yak_server/helpers/rules/compute_points.py:205-215` — The scoring formula divides by `(numbers_of_players - 1)`. If exactly one non-admin user exists, this is a division by zero crash. Needs a guard: `if numbers_of_players <= 1: return`.

**15. `StopIteration` crash in `winner_from_user` when no final match exists**

`yak_server/helpers/rules/compute_points.py:146-158` — `next(iter(...))` raises `StopIteration` if no bet with group code `"1"` (the final) exists for the user. This happens whenever `compute_points` is called before the final match is set up. Fix: `next(iter(...), None)` and return early if `None`.

**16. Knockout bonus points hardcoded, not configurable**

`yak_server/helpers/rules/compute_points.py:238-241` — Quarter-final, semi-final, final, and winner bonuses are hardcoded as `30`, `60`, `120`, `200`. The `RuleComputePoints` config model has fields for score/result/group bonuses but not for these. Changing them requires a code edit rather than a competition data file update.

______________________________________________________________________

## Medium Priority — Missing Features

**5. Password reset flow**

Currently only an admin can change a user's password (`PATCH /users/{id}`). There's no self-service password reset. The minimum viable addition:

- `POST /users/request-password-reset` — generates a signed, short-lived token
- `POST /users/reset-password` — validates token and sets new password

This avoids needing email infrastructure if the token is returned synchronously (e.g., shown to user after admin verification).

**6. Missing DB indices on foreign keys**

`yak_server/database/models.py` — `MatchModel.user_id`, `MatchModel.group_id`, `GroupPositionModel.user_id`, `GroupPositionModel.group_id`, `RefreshTokenModel.user_id` all lack explicit `sa.Index(...)` definitions. PostgreSQL creates indices on PKs automatically but not on FK columns. These are heavily filtered in queries (e.g., all matches for a user) so missing indices hurt at scale.

**7. Bulk bet update endpoint**

Currently bets are updated one-at-a-time with `PATCH /score_bets/{id}` and `PATCH /binary_bets/{id}`. A user filling out 48 group-stage matches makes 48 round trips. A `PATCH /bets/bulk` accepting a list of `{id, score1, score2}` would reduce this dramatically.

**8. HTTP caching on read-only endpoints**

Endpoints like `GET /teams`, `GET /phases`, `GET /groups`, `GET /rules`, and `GET /competition` return static data that changes only when the competition changes. Adding `Cache-Control: public, max-age=3600` and `ETag` headers would let clients and reverse proxies cache these aggressively.

**17. `group_rank` SQLAlchemy query iterated three times in `get_group_rank_with_code`**

`yak_server/helpers/group_position.py:117-143` — The `group_rank` query object is iterated in the `any(...)` check (line 124), then passed to `compute_group_rank` where it is iterated again (line 143), and sorted once more after returning. Each iteration re-executes the SQL. Materializing the query once with `.all()` would halve the number of queries on this hot path.

**18. Hardcoded group codes couple scoring to data schema**

`yak_server/helpers/rules/compute_points.py:187-189` — Group codes `"4"`, `"2"`, `"1"` (quarter-finals, semi-finals, final) are string literals embedded in the scoring logic. If a competition uses different codes, scoring silently computes zero for these phases. These should come from the competition rules config.

______________________________________________________________________

## Low Priority — Code Quality & Observability

**9. Structured (JSON) logging**

`yak_server/helpers/` — Logs are plain text strings. Replacing them with structured JSON logs (using `python-json-logger` or `structlog`) would make them far easier to parse in log aggregators (Datadog, Loki, CloudWatch, etc.).

**10. `is_one_won` field name**

`yak_server/database/models.py:236` — `BinaryBetModel.is_one_won` is ambiguous. `team1_won` would be self-documenting. This requires a migration and a search-and-replace across the codebase but has no functional impact.

**11. Expose `error_code` as a string slug, not just an integer**

`yak_server/v1/helpers/errors.py:189-196` — The error response has `error_code: 401` but no machine-readable slug like `"invalid_credentials"`. Clients currently have to parse the `description` string to distinguish error types within the same HTTP status. Adding an `error_slug` field to the error response model (e.g., `"locked_bet"`, `"expired_token"`) would let frontends display localized messages without string matching.

**12. OpenAPI tags and descriptions**

`yak_server/app.py:37-45` — The Swagger UI at `/api/docs` has no tag descriptions or grouping metadata. Adding a `openapi_tags` list to `FastAPI(...)` with descriptions for each router tag would make the auto-generated docs much more useful for frontend developers.

**13. Test for the full signup → bet → score flow**

The test suite tests individual endpoints in isolation, but there's no end-to-end integration test that: signs up a user → retrieves their bets → places a prediction → verifies points are computed. This kind of test would catch regressions in the cross-cutting business logic.

______________________________________________________________________

## Summary Table

| # | Area | Effort | Impact |
|---|------|--------|--------|
| ~~1~~ | ~~Fix 401→403 on locked bets~~ | ~~XS~~ | ~~Medium~~ ✓ |
| ~~2~~ | ~~Widen password column~~ | ~~XS~~ | ~~High (data safety)~~ ✓ |
| ~~3~~ | ~~Rate limiting on auth~~ | ~~S~~ | ~~High~~ ✓ |
| 4 | Refresh token cleanup | S | Medium |
| 5 | Password reset flow | M | High |
| 6 | DB indices on FKs | S | High (performance) |
| 7 | Bulk bet update | M | Medium |
| 8 | HTTP caching headers | S | Medium |
| 9 | Structured logging | S | Medium |
| 10 | Rename `is_one_won` | M (migration) | Low |
| 11 | Error slug in responses | S | Medium |
| 12 | OpenAPI tag descriptions | XS | Low |
| 13 | E2E integration test | M | High |
| 14 | Division by zero in scoring (1 player) | XS | High (crash) |
| 15 | StopIteration crash in winner_from_user | XS | High (crash) |
| 16 | Hardcode knockout bonus points | S | Medium |
| 17 | Group rank query iterated 3× | XS | Medium (perf) |
| 18 | Hardcoded group codes in scoring | S | Medium |
