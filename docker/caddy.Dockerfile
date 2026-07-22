# --- build the Vue frontend pointing at the same-origin /api ---
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
ENV VITE_API_BASE_URL=/api/
RUN npm run build

# --- Caddy serves the static site + reverse-proxies the backend (auto HTTPS) ---
FROM caddy:2-alpine
COPY --from=build /app/dist /srv
COPY docker/Caddyfile /etc/caddy/Caddyfile
