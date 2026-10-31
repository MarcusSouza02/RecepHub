FROM node:24-bookworm-slim
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app
RUN chown node:node /app
COPY --chown=node:node package.json package-lock.json ./
USER node
RUN npm ci && mkdir -p .next
COPY --chown=node:node . .
EXPOSE 3000
CMD ["npm", "run", "dev"]
