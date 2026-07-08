#!/bin/bash
set -e

# 1. Secret 생성 (인증서 + SSL 설정 통합)
kubectl create secret generic mariadb-tls \
  --from-file=server.cas=/root/server.cas \
  --from-file=server.crt=/root/server.crt \
  --from-file=server.key=/root/server.key \
  --from-literal=ssl.cnf='[mysqld]
ssl-ca=/etc/mysql/tls/server.cas
ssl-cert=/etc/mysql/tls/server.crt
ssl-key=/etc/mysql/tls/server.key
require_secure_transport=ON'

# 2. Deployment에 마운트 추가
kubectl patch deployment library-db --type='json' -p='[
  {"op": "add", "path": "/spec/template/spec/containers/0/volumeMounts/-", "value": {"name": "tls-certs", "mountPath": "/etc/mysql/tls", "readOnly": true}},
  {"op": "add", "path": "/spec/template/spec/containers/0/volumeMounts/-", "value": {"name": "ssl-conf", "mountPath": "/etc/mysql/conf.d"}},
  {"op": "add", "path": "/spec/template/spec/volumes/-", "value": {"name": "tls-certs", "secret": {"secretName": "mariadb-tls"}}},
  {"op": "add", "path": "/spec/template/spec/volumes/-", "value": {"name": "ssl-conf", "secret": {"secretName": "mariadb-tls", "items": [{"key": "ssl.cnf", "path": "ssl.cnf"}]}}}
]'

# 3. 파드가 뜰 때까지 대기
kubectl rollout status deployment/library-db --timeout=120s

# MariaDB가 실제로 ready될 때까지 대기
echo "Waiting for MariaDB to be ready..."
for i in $(seq 1 30); do
  kubectl exec deploy/library-db -- mysql -h 127.0.0.1 -u root -prootpass1234 -e "SELECT 1" > /dev/null 2>&1 && break
  sleep 3
done

# 4. libuser를 X.509 인증서 기반 계정으로 재생성
kubectl exec deploy/library-db -- mysql -h 127.0.0.1 -u root -prootpass1234 -e "
DROP USER IF EXISTS 'libuser'@'%';
CREATE USER 'libuser'@'%' REQUIRE SUBJECT '/CN=libuser';
GRANT ALL PRIVILEGES ON librarydb.* TO 'libuser'@'%';
FLUSH PRIVILEGES;
"

echo "=== MariaDB mTLS 설정 완료 ==="
