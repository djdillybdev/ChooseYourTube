FROM node:22-bookworm-slim AS deps

WORKDIR /app

ENV PNPM_HOME=/pnpm \
    PATH="/pnpm:$PATH"

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile --ignore-scripts

FROM deps AS build

WORKDIR /app
COPY . .
RUN pnpm build && pnpm prune --prod

FROM node:22-bookworm-slim AS runtime

WORKDIR /app

ENV NODE_ENV=production

RUN useradd --create-home --uid 10001 appuser

COPY --from=build /app/build /app/build
COPY --from=build /app/node_modules /app/node_modules
COPY --from=build /app/package.json /app/package.json

USER appuser

EXPOSE 5173

CMD ["node", "build"]

FROM deps AS dev

WORKDIR /app
COPY . .

EXPOSE 5173

CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "5173"]
