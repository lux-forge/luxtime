FROM node:22-alpine AS web-build

WORKDIR /build/web
RUN corepack enable
COPY web/package.json web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY web/ ./
RUN pnpm build

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/luxtime
COPY pyproject.toml README.md ./
COPY app/ ./app/
RUN python -m pip install --no-cache-dir .
COPY --from=web-build /build/web/dist ./web-dist/

EXPOSE 52020
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "52020"]
