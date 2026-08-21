# Use the official Node.js 20 image
FROM node:20-alpine

# Create app directory
WORKDIR /usr/src/app

# Copy dependency files first (for efficient Docker caching)
COPY package*.json ./

# Install dependencies (only production dependencies to keep image small)
RUN npm ci --only=production

# Copy the rest of the application code
COPY . .

# Expose the Gateway Port
EXPOSE 3000

# Start the Gateway
CMD ["node", "server.mjs"]
