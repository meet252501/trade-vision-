# Base Node.js image
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application source
COPY . .

# Build the frontend and backend bundle
RUN npm run build

# Expose port
EXPOSE 3000

# Start server
CMD ["npm", "start"]
