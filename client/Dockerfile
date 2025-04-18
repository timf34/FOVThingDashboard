# Frontend Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json ./

# Copy .env.production explicitly
COPY .env.production .env

RUN npm install



COPY . .

# Build the React app
RUN npm run build

# Serve the app using a static server
RUN npm install -g serve
CMD ["serve", "-s", "build", "-l", "3000"]
