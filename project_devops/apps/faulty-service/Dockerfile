FROM node:20-alpine

# Cài đặt curl để tiện cho việc test thủ công tại Prod
RUN apk add --no-cache curl

WORKDIR /app

COPY package*.json ./
RUN npm install --omit=dev

COPY . .

# Metadata cho Ghost Engineer
LABEL com.ghost-engineer.managed="true"
LABEL com.github.repo="nano-devops/faulty-service"
LABEL version="2.0.0-buggy"

EXPOSE 8080

# Chạy với cờ --trace-warnings để AI dễ soi log
CMD ["node", "--trace-warnings", "server.js"]
