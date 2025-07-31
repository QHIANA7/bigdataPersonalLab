#!/bin/bash

# Grafana 서버 정보
GRAFANA_URL="http://g1:3000"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="admin"

# Prometheus 데이터 소스 정보
DATASOURCE_NAME="Prometheus"
PROMETHEUS_URL="http://p1:9090"

# 데이터 소스 확인
curl -X GET "$GRAFANA_URL/api/datasources" \
  -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \

# 데이터 소스 추가
curl -X POST "$GRAFANA_URL/api/datasources" \
  -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"$DATASOURCE_NAME\",
    \"type\": \"prometheus\",
    \"access\": \"proxy\",
    \"url\": \"$PROMETHEUS_URL\",
    \"basicAuth\": false,
    \"isDefault\": true
  }"
