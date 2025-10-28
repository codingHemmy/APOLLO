FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install --legacy-peer-deps || npm install --legacy-peer-deps

COPY . .

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
