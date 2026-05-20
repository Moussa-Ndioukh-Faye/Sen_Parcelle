#!/bin/bash
# Script de déploiement et vérification du smart contrat SenParcelle
set -euo pipefail

NETWORK="${1:-mumbai}"
CONTRACT="contracts/SenParcelle.sol"

echo "🚀 Déploiement sur $NETWORK..."

cd "$(dirname "$0")/../blockchain"

# 1. Compiler
echo "🔧 Compilation..."
npx hardhat compile

# 2. Déployer
echo "📦 Déploiement du contrat..."
DEPLOY_OUTPUT=$(npx hardhat run scripts/deploy.js --network "$NETWORK")
echo "$DEPLOY_OUTPUT"

# Extraire l'adresse du contrat
CONTRACT_ADDRESS=$(echo "$DEPLOY_OUTPUT" | grep -oP '0x[a-fA-F0-9]{40}')
echo "📍 Adresse du contrat: $CONTRACT_ADDRESS"

# 3. Vérifier sur Polygonscan
if [ "$NETWORK" = "polygon" ]; then
    echo "🔍 Vérification sur Polygonscan..."
    npx hardhat verify --network "$NETWORK" "$CONTRACT_ADDRESS"
elif [ "$NETWORK" = "mumbai" ]; then
    echo "🔍 Vérification sur Mumbai Polygonscan..."
    npx hardhat verify --network "$NETWORK" "$CONTRACT_ADDRESS"
fi

# 4. Tests
echo "🧪 Exécution des tests..."
npx hardhat test

echo ""
echo "✅ Déploiement terminé sur $NETWORK"
echo "   Contract: $CONTRACT_ADDRESS"
