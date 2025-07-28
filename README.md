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
### 1. 프로젝트 Clone 및 컨테이너 생성
```powershell
# 작업 디렉터리 설정
cd ~

# 1. 프로젝트 클론
git clone https://github.com/QHIANA7/bigdataPersonalLab.git
cd ~\bigdataPersonalLab

# 2-1. hnet 컨테이너 네트워크 생성
docker network create hnet

# 2-2. Docker Compose 수행
cd ~\bigdataPersonalLab\hadoopInstall
docker-compose down --volumes
docker-compose up --build -d
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
```