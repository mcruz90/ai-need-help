# Dockerfile for ai-assistant (frontend)
# syntax=docker/dockerfile:1

ARG NODE_VERSION=20.18.0
FROM node:23-alpine

# Set NODE_ENV to development for live reloading
ENV NODE_ENV development

WORKDIR /app

# Copy the package.json and package-lock.json files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the source files
COPY . .

# Expose the port the Next.js application will run on
EXPOSE 3000

# Start the development server
RUN npm run dev
