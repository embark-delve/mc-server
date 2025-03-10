#!/bin/bash

# Minecraft Server Kubernetes Deployment Script
# This script helps deploy the Minecraft server to a Kubernetes cluster

set -e

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
NAMESPACE=${1:-minecraft}

# Create namespace if it doesn't exist
if ! kubectl get namespace ${NAMESPACE} > /dev/null 2>&1; then
    echo "Creating namespace ${NAMESPACE}..."
    kubectl create namespace ${NAMESPACE}
fi

# Deploy Minecraft server
echo "Deploying Minecraft server to namespace ${NAMESPACE}..."
kubectl apply -f ${SCRIPT_DIR}/minecraft-deployment.yml -n ${NAMESPACE}

# Wait for deployment to be ready
echo "Waiting for deployment to be ready..."
kubectl rollout status deployment/minecraft-server -n ${NAMESPACE}

# Get service details
echo "Getting service details..."
if kubectl get service minecraft-server -n ${NAMESPACE} | grep -q LoadBalancer; then
    echo "Waiting for LoadBalancer IP/hostname (this may take a moment)..."
    sleep 10
    
    EXTERNAL_IP=""
    while [ -z "$EXTERNAL_IP" ]; do
        EXTERNAL_IP=$(kubectl get service minecraft-server -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        if [ -z "$EXTERNAL_IP" ]; then
            EXTERNAL_IP=$(kubectl get service minecraft-server -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
        fi
        
        if [ -z "$EXTERNAL_IP" ]; then
            echo "Waiting for external IP/hostname..."
            sleep 10
        fi
    done
    
    echo ""
    echo "Minecraft server is ready!"
    echo "Connect to your server at: ${EXTERNAL_IP}:25565"
else
    echo ""
    echo "Minecraft server is ready!"
    echo "Since you're not using a LoadBalancer, access your server using NodePort or port-forwarding."
    echo "To port-forward for local testing:"
    echo "kubectl port-forward service/minecraft-server 25565:25565 -n ${NAMESPACE}"
fi

echo ""
echo "To check server status:"
echo "kubectl get pods -n ${NAMESPACE}"
echo ""
echo "To view server logs:"
echo "kubectl logs -f deployment/minecraft-server -n ${NAMESPACE}" 