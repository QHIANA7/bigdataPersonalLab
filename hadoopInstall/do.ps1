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
docker-compose down --volumes
docker-compose up --build -d
docker exec -it i1 bash