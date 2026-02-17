FROM node:20-alpine AS build

# Work in /repo/frontend to mirror your host layout
WORKDIR /repo/frontend

# Install deps
COPY frontend/package*.json ./
RUN npm ci

# Copy sources
COPY frontend/ ./

# Copy contracts as a sibling folder of frontend
COPY contracts/ /repo/contracts/

# Build
RUN npm run build

FROM nginx:alpine
COPY --from=build /repo/frontend/dist /usr/share/nginx/html

# Nginx config is in frontend/
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
