FROM docker.io/library/node:24-alpine

RUN apk add --no-cache git \
    && addgroup -S worker \
    && adduser -S -G worker worker

WORKDIR /app

COPY package.json ./
RUN npm install --include=dev --no-audit --no-fund

COPY tsconfig.json wrangler.jsonc ./
COPY src ./src

USER worker

EXPOSE 8787

CMD ["npx", "wrangler", "dev", "--ip", "0.0.0.0", "--port", "8787"]
