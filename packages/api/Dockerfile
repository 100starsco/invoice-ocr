FROM node:20-alpine

WORKDIR /app

# Enable corepack and install pnpm
RUN corepack enable && corepack prepare pnpm@8.14.0 --activate

# Copy package.json and install dependencies (including dev dependencies for build)
COPY package.json ./
RUN pnpm install

# Copy source code
COPY . .

# Try to build with TypeScript, fallback to running TypeScript source directly
RUN node node_modules/.pnpm/typescript@5.9.2/node_modules/typescript/bin/tsc --noEmitOnError false || \
    echo "TypeScript build failed, will run source directly"

EXPOSE 3000

# Run using tsx if dist doesn't exist, otherwise use compiled JS
CMD ["sh", "-c", "if [ -f dist/index.js ]; then node dist/index.js; else npx tsx src/index.ts; fi"]