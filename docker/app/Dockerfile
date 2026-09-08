# syntax=docker/dockerfile:1
#
# Build context is docker/ itself (see the "repo" additional context in
# compose.yml) - app/, web/, pyproject.toml, and README.md are pulled in
# explicitly via `COPY --from=repo` rather than assumed to be sitting next to
# this Dockerfile, so this file and its context stay self-contained under
# docker/. pyproject.toml/README.md are only ever read inside the
# python-build stage; nothing after it carries them into the runtime image.

FROM node:22-alpine AS web-build

WORKDIR /build/web
RUN corepack enable
COPY --from=repo web/package.json web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY --from=repo web/ ./
RUN pnpm build

FROM python:3.13-slim AS python-build

WORKDIR /build
COPY --from=repo pyproject.toml README.md VERSION ./
COPY --from=repo app/ ./app/
RUN python -m pip install --no-cache-dir --target /build/site-packages .

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/luxtime/site-packages

WORKDIR /opt/luxtime
COPY --from=python-build /build/site-packages ./site-packages/
COPY --from=web-build /build/web/dist ./web-dist/

EXPOSE 52020
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "52020"]
