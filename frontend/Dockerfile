# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# F5 RiskAI — frontend (Vue 3 + Vite) image, multi-stage.
#
# Stage 1 (build): installs dependencies and runs `npm run build`.
#   VITE_API_URL is a Vite BUILD-TIME variable: it is baked into the bundle
#   during `npm run build`. It is passed as `ARG VITE_API_URL` so that the
#   same Dockerfile works in local Docker (http://localhost:8000) and in
#   Render (https://<api>.onrender.com) by rebuilding with a different ARG.
#
# Stage 2 (serve): a minimal Nginx serves frontend/dist with SPA fallback.
# The nginx config is a template (`listen ${NGINX_PORT}`); the container
# entrypoint substitutes `${NGINX_PORT}` from the `PORT` variable injected
# by Render (default 80 locally), so the same image works on Docker Compose
# and on Render without changes.
# ---------------------------------------------------------------------------
FROM node:22-alpine AS build

WORKDIR /app

# Cache-friendly dependency install (package-lock.json is committed).
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# The API base URL used by the browser at runtime (baked at build time).
# Render passes service env vars to Docker builds automatically, so
# `VITE_API_URL` defined for the frontend service reaches this ARG at build
# time without any extra configuration.
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

COPY frontend/ ./
RUN npm run build

# ---------------------------------------------------------------------------
FROM nginx:stable-alpine

# SPA with client-side routing: serve the built files and fall back to
# index.html for any non-file route (vue-router history mode).
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf.template
COPY docker/frontend-entrypoint.sh /docker/frontend-entrypoint.sh
COPY --from=build /app/dist /usr/share/nginx/html

RUN chmod +x /docker/frontend-entrypoint.sh

EXPOSE 80

CMD ["/docker/frontend-entrypoint.sh"]