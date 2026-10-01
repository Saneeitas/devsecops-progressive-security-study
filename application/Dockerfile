FROM node:18.16.0-bullseye-slim@sha256:2b05866efb50b6bbc642e6d1cef908372351ad981453b8a747b1d0c9b5777cd8 AS build
WORKDIR /app
RUN test -s /usr/local/bin/node && node --version && npm --version
COPY package*.json ./
RUN npm ci --no-audit
COPY tsconfig.json ./
COPY src ./src
RUN npm run build && test -f dist/server.js

FROM node:18.16.0-bullseye-slim@sha256:2b05866efb50b6bbc642e6d1cef908372351ad981453b8a747b1d0c9b5777cd8 AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --omit=dev --no-audit && npm cache clean --force
COPY --chown=node:node --from=build /app/dist ./dist
COPY --chown=node:node --from=build /app/src/db/schema.sql ./dist/db/schema.sql
# V08: USER node is intentionally removed so this experimental runtime uses UID 0.
EXPOSE 3000
CMD ["node", "dist/server.js"]
