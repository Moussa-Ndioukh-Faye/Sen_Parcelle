#!/bin/bash
# Vérification d'un certificat sur la blockchain Polygon
set -euo pipefail

CONTRACT_ADDRESS="${POLYGON_CONTRACT_ADDRESS:-}"
RPC_URL="${POLYGON_RPC_URL:-https://polygon-rpc.com}"
HASH="${1:-}"

if [ -z "$HASH" ]; then
    echo "Usage: $0 <document-hash>"
    echo "   ou: POLYGON_CONTRACT_ADDRESS=0x... $0 <hash>"
    exit 1
fi

if [ -z "$CONTRACT_ADDRESS" ]; then
    echo "❌ POLYGON_CONTRACT_ADDRESS non défini"
    exit 1
fi

echo "🔍 Vérification du certificat: $HASH"
echo "   Contrat: $CONTRACT_ADDRESS"
echo "   RPC: $RPC_URL"
echo ""

# Appel via cast (foundry) ou curl vers un node RPC
if command -v cast &> /dev/null; then
    RESULT=$(cast call "$CONTRACT_ADDRESS" "verifyDocument(bytes32)" "$HASH" --rpc-url "$RPC_URL")
    echo "Résultat: $RESULT"
else
    echo "ℹ️  Installer Foundry (cast) pour une vérification directe:"
    echo "   curl -L https://foundry.paradigm.xyz | bash"
    echo ""
    echo "   Ou utilisez l'API:"
    echo "   curl https://api.sen-parcelle.sn/api/blockchain/verify/$HASH/"
fi
