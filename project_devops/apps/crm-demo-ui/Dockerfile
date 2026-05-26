# TNT CRM Command Center — static build + nginx
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
# Empty = same-origin via nginx /api/ proxy (presenter hosts chỉ cần crm-demo)
ARG VITE_CRM_API_BASE=
ARG VITE_SSE_URL=
ARG VITE_DEMO_KEY=
ENV VITE_CRM_API_BASE=$VITE_CRM_API_BASE
ENV VITE_SSE_URL=$VITE_SSE_URL
ENV VITE_DEMO_KEY=$VITE_DEMO_KEY
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK CMD wget -qO /dev/null http://127.0.0.1/ || exit 1
