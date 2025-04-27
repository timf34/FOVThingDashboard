cat > /etc/nginx/sites-available/fovdashboard <<'EOF'
server {
    listen 80;
    server_name aviva.fovdashboard.com;
    return 301 https://$host$request_uri;         # force HTTPS
}

server {
    listen 443 ssl http2;
    server_name aviva.fovdashboard.com;

    # --- LetsEncrypt certs will be dropped here in the next step ---
    ssl_certificate     /etc/letsencrypt/live/aviva.fovdashboard.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aviva.fovdashboard.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # static React build
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # FastAPI REST
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # FastAPI Web-Sockets
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout   3600s;           # keep dashboards open for a long time
        proxy_send_timeout   3600s;
        proxy_buffering off;                  # disable buffers for WS
    }
}
EOF

ln -sf /etc/nginx/sites-available/fovdashboard /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

apt install -y certbot python3-certbot-nginx
certbot --nginx -d aviva.fovdashboard.com --non-interactive --agree-tos -m you@example.com

ufw allow OpenSSH
ufw allow 'Nginx Full'    # ports 80 & 443
ufw --force enable
