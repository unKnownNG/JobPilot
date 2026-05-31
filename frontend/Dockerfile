# =============================================================================
# Frontend Dockerfile — Next.js (Multi-Stage Build)
# =============================================================================
# This uses a "multi-stage build" to create a tiny production image.
#
# WHAT IS A MULTI-STAGE BUILD?
# Instead of one big image that includes npm, source code, AND the build
# output, we use three stages:
#
#   Stage 1 (deps):    Install node_modules
#   Stage 2 (builder): Build the Next.js app (npm run build)
#   Stage 3 (runner):  Copy ONLY the compiled output into a clean image
#
# This results in a final image of ~200 MB instead of ~1.5 GB.
#
# WHY DOES THIS MATTER?
# Your friends download a smaller image, and it starts faster.
# =============================================================================

# ─── Stage 1: Install Dependencies ──────────────────────────────────────────
# This stage installs all npm packages. It's cached separately so that
# if you only change source code (not package.json), Docker skips this step.
FROM node:20-alpine AS deps

WORKDIR /app

# Copy package files first (for caching)
COPY package.json package-lock.json ./

# npm ci = "clean install" — faster and more reliable than npm install.
# It reads package-lock.json exactly, ensuring everyone gets the same versions.
RUN npm ci


# ─── Stage 2: Build the Application ─────────────────────────────────────────
# This stage compiles TypeScript, optimizes CSS, and creates the production
# build output in .next/standalone.
FROM node:20-alpine AS builder

WORKDIR /app

# Copy node_modules from Stage 1
COPY --from=deps /app/node_modules ./node_modules

# Copy all source files
COPY . .

# Build the Next.js production app
# This creates .next/standalone/ which contains a self-contained server.
RUN npm run build


# ─── Stage 3: Production Runner ─────────────────────────────────────────────
# This is the final, minimal image that actually runs in production.
# It contains ONLY the compiled app — no source code, no dev tools.
FROM node:20-alpine AS runner

WORKDIR /app

# Set to production mode for performance optimizations
ENV NODE_ENV=production

# Create a non-root user for security
# (Running as root inside a container is a security risk)
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy the standalone server from the builder stage
# This is the magic of `output: "standalone"` in next.config.ts
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Switch to the non-root user
USER nextjs

# Expose port 3000
EXPOSE 3000

# Set the hostname to 0.0.0.0 so Docker can route traffic into the container
ENV HOSTNAME="0.0.0.0"
ENV PORT=3000

# Start the standalone Next.js server
CMD ["node", "server.js"]
