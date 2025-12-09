# syntax=docker/dockerfile:1.7

FROM golang:1.24-alpine AS builder

WORKDIR /app

ENV CGO_ENABLED=0 \
    GOOS=linux \
    GOARCH=amd64 \
    GOTOOLCHAIN=local \
    GONOSUMDB=* \
    GOFLAGS=-mod=mod

RUN apk add --no-cache ca-certificates

COPY go.mod ./
COPY . .

RUN go build \
    -ldflags="-s -w -buildid=" \
    -trimpath \
    -o agent-node main.go

FROM alpine:3.18

WORKDIR /app

RUN apk add --no-cache ca-certificates && \
    addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

COPY --from=builder /app/agent-node .

RUN chown appuser:appuser ./agent-node

USER appuser

ENV NODE_NAME="nano-node-01" \
    BRAIN_URL="http://platform-agentic-ai:3000/v1/incidents/report" \
    COMMAND_PORT="8080" \
    MONITOR_INTERVAL="30s" \
    LOG_TAIL_LINES="100" \
    ENV="production"

EXPOSE 8080 8081

ENTRYPOINT ["./agent-node"]