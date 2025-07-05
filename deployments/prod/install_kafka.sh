#!/bin/bash

kubectl create namespace strimzi
kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka' -n strimzi
kubectl apply -f manifests/kafka-c6c8.yaml