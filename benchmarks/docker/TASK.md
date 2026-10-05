# Docker fixture — production-ready image (files: Dockerfile, compose.yml)
#
# Task prompt for the agent:
#   implementar: el Dockerfile actual corre como root, sin healthcheck y sin
#   .dockerignore. Agregá: usuario no-root (node), HEALTHCHECK con wget o
#   node, y un .dockerignore que excluya node_modules y .git. En compose.yml
#   agregá restart: unless-stopped. Verificá con docker compose config y
#   docker build.
#
# Verify: docker compose config && docker build -t fixture-api .  -> exit 0
docker compose config && docker build -t fixture-api .
