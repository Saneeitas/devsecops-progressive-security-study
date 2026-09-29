FROM node:22-alpine3.22 AS build
WORKDIR /app
RUN test -s /usr/local/bin/node && node --version && npm --version
COPY package*.json ./
RUN npm install
COPY tsconfig.json ./
COPY src ./src
RUN npm run build && test -f dist/server.js

FROM node:22-alpine3.22 AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm install --omit=dev
COPY --from=build /app/dist ./dist
EXPOSE 3000
CMD ["node", "dist/server.js"]
