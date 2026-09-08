#!/bin/sh
# F5 RiskAI frontend entrypoint (Nginx, Docker).
#
# Renders /etc/nginx/conf.d/default.conf from the nginx.conf.template with
# `${NGINX_PORT}` substituted, then starts Nginx in the foreground.
#
# The port honours the `PORT` variable injected by Render for web services
# (default 10000 there); when unset it falls back to 80, keeping the local
# Docker Compose layout (frontend on 8080:80) unchanged.
set -e

: "${PORT:=80}"
NGINX_PORT="$PORT"
export NGINX_PORT

envsubst '${NGINX_PORT}' \
    < /etc/nginx/conf.d/default.conf.template \
    > /etc/nginx/conf.d/default.conf

echo "[entrypoint] Nginx listening on 0.0.0.0:${NGINX_PORT} (from PORT=${PORT})"
exec nginx -g "daemon off;"