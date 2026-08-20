FROM node:22-alpine

RUN apk add --no-cache openssl

WORKDIR /app

# Copy package files and install
COPY package.json package-lock.json ./
RUN npm ci --production && npm cache clean --force

# Copy source
COPY . .

# Generate HTTPS self-signed certs
RUN mkdir -p /app/certs && \
    openssl req -x509 -nodes -days 3650 -newkey rsa:4096 \
      -keyout /app/certs/key.pem \
      -out /app/certs/cert.pem \
      -subj "/C=CH/L=Zurich/O=MultiAgentChat/CN=localhost" \
      -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" 2>/dev/null

EXPOSE 5555

# Run setup on first start (creates DB + users if not exist)
# Then start the server
CMD node server/setup.js && node server/index.js
