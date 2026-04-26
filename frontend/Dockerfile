FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml* ./
RUN corepack enable && \
    if [ -f pnpm-lock.yaml ]; then pnpm install --frozen-lockfile; else pnpm install; fi

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN corepack enable && pnpm build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
RUN mkdir -p ./public
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
