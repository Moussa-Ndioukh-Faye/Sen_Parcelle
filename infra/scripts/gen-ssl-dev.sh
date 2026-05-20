#!/bin/bash
# Génération de certificats SSL auto-signés pour développement local
set -euo pipefail

SSL_DIR="$(dirname "$0")/../nginx/ssl"
DAYS=3650  # 10 ans pour dev

echo "🔐 Génération des certificats SSL auto-signés..."
echo "   📁 Dossier : $SSL_DIR"

mkdir -p "$SSL_DIR"

# Générer la clé privée et le certificat auto-signé
openssl req -x509 \
    -newkey rsa:4096 \
    -keyout "$SSL_DIR/sen-parcelle-dev.key" \
    -out "$SSL_DIR/sen-parcelle-dev.crt" \
    -days "$DAYS" \
    -nodes \
    -subj "/C=SN/ST=Dakar/L=Dakar/O=Sen_Parcelle/OU=Development/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:api.sen-parcelle.sn,DNS:admin.sen-parcelle.sn,IP:127.0.0.1"

echo "✅ Certificats générés :"
echo "   - $SSL_DIR/sen-parcelle-dev.crt"
echo "   - $SSL_DIR/sen-parcelle-dev.key"
echo ""
echo "⚠️  Pour utiliser en local : ajoutez le .crt à votre magasin de confiance"
