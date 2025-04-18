# client/Dockerfile
FROM node:18-alpine
WORKDIR /app

# 1️⃣ copy env *first* so CRA can read it at build‑time
COPY .env.production .env                

# 2️⃣ install deps & copy sources
COPY package.json package-lock.json ./
RUN npm install
COPY . .

# 3️⃣ build with the correct .env already in place
RUN npm run build

# 4️⃣ serve the static build
RUN npm install -g serve
CMD ["serve", "-s", "build", "-l", "3000"]
