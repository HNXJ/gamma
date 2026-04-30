#!/bin/bash
export PATH=$PATH:/Users/hamednejat/.nvm/versions/node/v24.14.0/bin
export NODE_PATH=/Users/hamednejat/.nvm/versions/node/v24.14.0/lib/node_modules

echo "STAGING: Lateral Bootstrap of gamma-arena..."
cd ../gamma-arena || exit 1

echo "CHECK: Current Directory: $(pwd)"
echo "CHECK: NPM Version: $(npm --version)"

echo "ACTION: Installing dependencies..."
npm install

echo "ACTION: Executing build..."
npm run build

echo "SUCCESS: Bootstrap complete."
