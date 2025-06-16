FROM node:23.3.0-slim

WORKDIR /app

COPY . .

# Enable pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Install deps and build
RUN pnpm install && pnpm build

EXPOSE 3000

# CMD is overridden by docker-compose
