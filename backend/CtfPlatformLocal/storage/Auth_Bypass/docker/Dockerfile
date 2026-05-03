FROM node:20-alpine

# Stwórz użytkownika nie-root (bezpieczeństwo)
RUN addgroup -g 1001 -S nodejs && \
    adduser -S -u 1001 -G nodejs nodejs

WORKDIR /app

# Skopiuj pliki package.json i zainstaluj zależności
COPY docker/package*.json ./
RUN npm install --only=production

# Skopiuj resztę aplikacji
COPY docker/ ./

# Ustaw właściciela plików
RUN chown -R nodejs:nodejs /app

# Przełącz na użytkownika nie-root
USER nodejs

# Port będzie konfigurowany przez zmienną środowiskową
ENV PORT=80

# Expose port (dla dokumentacji)
EXPOSE $PORT

# Uruchom aplikację (nasłuchuje na 0.0.0.0)
CMD ["node", "app.js"]