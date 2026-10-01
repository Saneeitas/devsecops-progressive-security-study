FROM node:22-alpine3.22 AS build
WORKDIR /app
RUN test -s /usr/local/bin/node && node --version && npm --version
COPY package*.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src ./src
RUN npm run build && test -f dist/server.js

FROM node:22-alpine3.22 AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY --chown=node:node --from=build /app/dist ./dist
COPY --chown=node:node --from=build /app/src/db/schema.sql ./dist/db/schema.sql
USER node
EXPOSE 3000
CMD ["node", "dist/server.js"]
