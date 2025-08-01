# bigdataPersonalLab
빅데이터 파이프라인 개인 실습 과제

## 프로젝트 개요
* 데이터 파이프라인 실습 과정의 전체 흐름을 직접 경험하여 **실무 대응력** 및 **기술 통합 역량** 강화가 목적
* 실습에 사용한 아키텍처, 코드, 설정 값 등을 **문서화 및 재현 가능**한 형태로 구성

## 프로젝트 범위
5개 장비의 센서 데이터를 실시간으로 수집, 처리, 저장하고 모니터링하는 완전한 데이터 파이프라인을 구현

## 기술활용
* 인프라 관리 : Docker
* 데이터 수집 : Python Collector + FMS API
* 메시지 큐 : Apache Kafka (2 Node)
* 스트림 처리 : Apache Spark Streaming
* 분산 저장 : Hadoop HDFS
* 모니터링 : Prometheus, Grafana

## 빠른시작
### 1. 컨테이너 생성을 위한 프로젝트 Clone 및 구성
```powershell
# 작업 디렉터리 설정
cd ~

# 1. 프로젝트 클론
git clone https://github.com/QHIANA7/bigdataPersonalLab.git
cd ~\bigdataPersonalLab

# 2-1. Hadoop 패키지 다운로드
if($false -eq (Test-Path .\hadoopInstall\df\i1\hadoop-3.3.6.tar.gz)) {
    curl https://downloads.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz -o ./hadoopInstall/df/i1/hadoop-3.3.6.tar.gz
}

# 2-2. Spark 패키지 다운로드
if($false -eq (Test-Path .\hadoopInstall\df\i1\spark-3.5.6-bin-hadoop3.tgz)) {
    curl https://dlcdn.apache.org/spark/spark-3.5.6/spark-3.5.6-bin-hadoop3.tgz -o ./hadoopInstall/df/i1/spark-3.5.6-bin-hadoop3.tgz
}

# 2-3. Kafka 패키지 다운로드
if($false -eq (Test-Path .\hadoopInstall\df\i1\kafka_2.12-3.9.0.tgz)) {
    curl https://dlcdn.apache.org/kafka/3.9.0/kafka_2.12-3.9.0.tgz -o ./hadoopInstall/df/i1/kafka_2.12-3.9.0.tgz
}

# 3-1. hnet 컨테이너 네트워크 생성
docker network create hnet

# 3-2. Docker Compose 수행
cd ~\bigdataPersonalLab\hadoopInstall
docker compose down --volumes
docker compose build i1i3
docker compose up --build -d
docker exec -it i1 bash
```

### 2. 클러스터 구성을 위한 프로젝트 Clone 및 구성
```bash
# 작업 디렉터리 설정
cd ~

# 1. 프로젝트 클론
git clone https://github.com/QHIANA7/bigdataPersonalLab.git
cd ~/bigdataPersonalLab

# 2. Hadoop 설치 수행
# hadoop-3.3.6.tar.gz 파일을 미리 df 폴더에 위치
cd ~/bigdataPersonalLab/hadoopInstall
ansible-playbook --flush-cache -i /df/ansible-hadoop/hosts /df/ansible-hadoop/hadoop_install.yml

# 3. Spark 설치 수행
# spark-3.5.6-bin-hadoop3.tgz 파일을 미리 df 폴더에 위치
cd ~/bigdataPersonalLab/hadoopInstall
ansible-playbook --flush-cache -i /df/ansible-spark/hosts /df/ansible-spark/spark_install.yml -e ansible_python_interpreter=/usr/bin/python3.12

# 4. Kafka 설치 수행
# kafka_2.12-3.9.0.tgz 파일을 미리 df 폴더에 위치
cd ~/bigdataPersonalLab/hadoopInstall
ansible-playbook -i /df/ansible-kafka/hosts /df/ansible-kafka/kafka_install.yml -e ansible_python_interpreter=/usr/bin/python3.12

# 5. node_exporter 설치 수행
cd ~/bigdataPersonalLab/hadoopInstall
ansible-playbook -i /df/ansible-node-exporter/hosts /df/ansible-node-exporter/node_exporter_install.yml
```

### 3. 실시간 스트리밍 파이프라인 실행
```bash
# 작업 디렉터리 설정
cd ~

# 1. HDFS, Spark, Kafka 기동
startAll

# 2. 스크립트 복사
ssh s1 "mkdir -p pipeline"
scp ~/bigdataPersonalLab/StreamingPipeLine/producer.py s1:pipeline/producer.py
scp ~/bigdataPersonalLab/StreamingPipeLine/consumer.py s1:pipeline/consumer.py
scp ~/bigdataPersonalLab/StreamingPipeLine/streaming.py s1:pipeline/streaming.py

# 3. 기존 파이프라인 종료
ssh s1 tmux kill-session -t producer
ssh s1 tmux kill-session -t consumer

# 4. 파이프라인 실행
ssh s1 tmux new-session -d -s producer 'python3 ~/pipeline/producer.py'
ssh s1 tmux new-session -d -s consumer 'spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.6 --conf spark.metrics.conf=/usr/local/spark/conf/metrics.properties --conf spark.metrics.namespace=sparkstreaming --conf spark.ui.prometheus.enabled=true --conf spark.sql.streaming.metricsEnabled=true ~/pipeline/streaming.py'

```

### 4. 모니터링 실행
```bash
# 작업 디렉터리 설정
cd ~

# 1. 스크립트 복사
ssh s1 "mkdir -p visualization"

scp ~/bigdataPersonalLab/Visualization/fms_monitoring.py s1:visualization/fms_monitoring.py
scp ~/bigdataPersonalLab/Visualization/err_monitoring.py s1:visualization/err_monitoring.py
scp ~/bigdataPersonalLab/Visualization/raw_monitoring.py s1:visualization/raw_monitoring.py

# 2. 기존 모니터링 종료
ssh s1 tmux kill-session -t fms_monitor
ssh s1 tmux kill-session -t err_monitor
ssh s1 tmux kill-session -t raw_monitor

# 3. 모니터링 시작
ssh s1 tmux new-session -d -s fms_monitor 'spark-submit ~/visualization/fms_monitoring.py'
ssh s1 tmux new-session -d -s err_monitor 'spark-submit ~/visualization/err_monitoring.py'
ssh s1 tmux new-session -d -s raw_monitor 'spark-submit ~/visualization/raw_monitoring.py'
```