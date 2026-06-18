FROM nginx:1.27-alpine

RUN addgroup -S appgroup && adduser -S appuser -G appgroup && \
    chown -R appuser:appgroup /var/cache/nginx /var/log/nginx /etc/nginx/conf.d && \
    mkdir -p /var/run/nginx && chown appuser:appgroup /var/run/nginx

COPY default.conf /etc/nginx/conf.d/default.conf

USER appuser

CMD ["nginx", "-g", "daemon off;"]
