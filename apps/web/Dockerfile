# VERA Next.js Production Dockerfile
FROM node:20-alpine AS base

FROM base AS builder
WORKDIR /app

COPY package.json ./
COPY packages/contracts/package.json ./packages/contracts/
COPY apps/web/package.json ./apps/web/

RUN npm install

COPY packages/contracts ./packages/contracts
COPY apps/web ./apps/web

RUN npm run build:contracts
RUN npm run build:web

FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

COPY --from=builder /app/apps/web/public ./apps/web/public
COPY --from=builder /app/apps/web/.next ./apps/web/.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/apps/web/package.json ./apps/web/package.json

EXPOSE 3000

CMD ["npm", "run", "start", "--workspace=@vera/web"]
