# Serves the Star Drift game as a static site with nginx on ports 80 and 3000.
# In Coolify: Build Pack = Dockerfile, Base Directory = /, Ports Exposes = 80 or 3000.
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY star-drift/ /usr/share/nginx/html/

EXPOSE 80 3000

# Busybox wget ships with nginx:alpine, so no extra packages are needed.
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1/health.json | grep -q '"ok"' || exit 1
