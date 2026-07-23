# Plain Caddy (no Node build) — the frontend lives on Netlify.
FROM caddy:2-alpine
COPY docker/Caddyfile.api /etc/caddy/Caddyfile
