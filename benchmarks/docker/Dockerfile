FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev
COPY server.js ./
RUN node --check server.js

FROM node:22-alpine AS runtime
WORKDIR /app
COPY --from=builder /app /app
EXPOSE 3000
CMD ["node", "server.js"]
