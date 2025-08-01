# FMS 시스템을 위한 환경 구성
## Docker 기반 클러스터 환경 설계
### 1. 전체 아키텍처
```
┌──────────────────────────────────────────────────┐
│              Docker Network (hnet)               │
├──────────────────────────────────────────────────┤
│                                                  │
│ ┌────────────┐   ┌────────────┐  ┌────────────┐  │
│ │i1 Container│   │     p1     │  │     g1     │  │
│ │ (Ansible)  │   │   (TSDB)   │  │ (visualize)│  │
│ │(Management)│   │            │  │ (alerting) │  │
│ │ ┌────────┐ │   │            │>>│            │  │
│ │ │  Kafka │ │   │┌──────────┐│  │┌──────────┐│  │
│ │ │Producer│ │   ││Prometheus││  ││  Grafana ││  │
│ │ │ :9092  │ │   ││   :9090  ││  ││   :3000  ││  │
│ │ └────────┘ │   │└──────────┘│  │└──────────┘│  │
│ └────────────┘   └────────────┘  └────────────┘  │
│       ↓                ↑                         │
│     Manage          Metrics                      │
│       ↓                ↑                         │
│ ┌──────────────────────────────────────────────┐ │
│ │             Hadoop/Spark Cluster             │ │
│ │                                              │ │
│ │  ┌──────────┐   ┌──────────┐   ┌──────────┐  │ │
│ │  │    s1    │   │    s2    │   │    s3    │  │ │
│ │  │ (Master) │   │ (Worker) │   │ (Worker) │  │ │
│ │  │  Kafka   │   │          │   │          │  │ │
│ │  │ Consumer │   │          │   │          │  │ │
│ │  │ NameNode │   │DataNode  │   │DataNode  │  │ │
│ │  │  :9870   │   │ :9864    │   │ :9864    │  │ │
│ │  │          │   │          │   │          │  │ │
│ │  │ ResrcMgr │   │NodeMgr   │   │NodeMgr   │  │ │
│ │  │  :8088   │   │ :8042    │   │ :8042    │  │ │
│ │  │          │   │          │   │          │  │ │
│ │  │ SprkMstr │   │SprkWrkr  │   │SprkWrkr  │  │ │
│ │  │  :8080   │   │ :8081    │   │ :8081    │  │ │
│ │  └──────────┘   └──────────┘   └──────────┘  │ │
│ └──────────────────────────────────────────────┘ │
│                                                  │
└──────────────────────────────────────────────────┘
``` 

## Container Provisioning
* docker-compose 로 i1,s1,s2,s3,p1,g1 컨테이너를 생성합니다. 
```powershell
# Windows OS에서 수행
git clone https://github.com/QHIANA7/bigdataPersonalLab.git
cd ~\bigdataPersonalLab\hadoopInstall
. .\do.ps1
```

## Hadoop Cluster Install
* Hadoop cluster install on oraclelinux9 docker
* 주의1 : 하둡파일(https://downloads.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz)이 /df/i1에 있어야 작동함.
```bash
# docker exec -it i1  bash
ansible-playbook --flush-cache -i /df/ansible-hadoop/hosts /df/ansible-hadoop/hadoop_install.yml
```

## Spark Cluster Install
* Spark cluster install on oraclelinux9 docker
* 주의1 : 스파크파일(https://dlcdn.apache.org/spark/spark-3.5.6/spark-3.5.6-bin-hadoop3.tgz)이 /df/i1에 있어야 작동함.
```bash
# docker exec -it i1  bash
ansible-playbook --flush-cache -i /df/ansible-spark/hosts /df/ansible-spark/spark_install.yml -e ansible_python_interpreter=/usr/bin/python3.12
```

## Kafka Cluster Install
* Kafka cluster install on oraclelinux9 docker
* 주의1 : 카프카파일(https://dlcdn.apache.org/kafka/3.9.0/kafka_2.12-3.9.0.tgz)이 /df/i1에 있어야 작동함.
```bash
# docker exec -it i1  bash
ansible-playbook -i /df/ansible-kafka/hosts /df/ansible-kafka/kafka_install.yml -e ansible_python_interpreter=/usr/bin/python3.12
```

## Node Exporter Cluster Install
* Node Exporter cluster install on oraclelinux9 docker
```bash
# docker exec -it i1  bash
ansible-playbook -i /df/ansible-node-exporter/hosts /df/ansible-node-exporter/node_exporter_install.yml
```

# Start/Stop Service
* i1에서 실행
## Start all node
```bash
# Alias : startAll
# HDFS 데몬 시작
ansible namenodes -i /df/ansible-hadoop/hosts -m shell -a "nohup hdfs --daemon start namenode &" -u root && \
ansible datanodes -i /df/ansible-hadoop/hosts -m shell -a "nohup hdfs --daemon start datanode &" -u root && \
# YARN 데몬 시작
ansible namenodes -i /df/ansible-hadoop/hosts -m shell -a "nohup yarn --daemon start resourcemanager &" -u root && \
ansible datanodes -i /df/ansible-hadoop/hosts -m shell -a "nohup yarn --daemon start nodemanager &" -u root && \

# MapReduce HistoryServer 시작 (선택 사항)
ansible namenodes -i /df/ansible-hadoop/hosts -m shell -a "nohup mapred --daemon start historyserver &" -u root && \

# Safe Mode off
ansible namenodes -i /df/ansible-hadoop/hosts -m shell -a "hdfs dfsadmin -safemode leave &" -u root --become

# Kafka Zookeeper 시작
ssh s1 tmux new-session -d -s zookeeper "zookeeper-server-start.sh /opt/kafka/config/zookeeper.properties"
sleep 10

# Kafka 시작
ssh s1 tmux new-session -d -s kafka "kafka-server-start.sh /opt/kafka/config/server.properties"
ssh s2 tmux new-session -d -s kafka "kafka-server-start.sh /opt/kafka/config/server.properties"
ssh s3 tmux new-session -d -s kafka "kafka-server-start.sh /opt/kafka/config/server.properties"
```

### Stop all node
```bash
# Alias : stopAll
# HDFS 데몬 종료
ansible namenodes -i /df/ansible-hadoop/hosts -m shell -a "hdfs --daemon stop namenode" -u root && \
ansible datanodes -i /df/ansible-hadoop/hosts -m shell -a "hdfs --daemon stop datanode" -u root && \

# YARN 데몬 종료
ansible namenodes -i /df/ansible-hadoop/hosts -m shell -a "yarn --daemon stop resourcemanager" -u root && \
ansible datanodes -i /df/ansible-hadoop/hosts -m shell -a "yarn --daemon stop nodemanager" -u root && \

# MapReduce HistoryServer 종료 (선택 사항)
ansible namenodes -i /df/ansible-hadoop/hosts -m shell -a "mapred --daemon stop historyserver" -u root

# Kafka Zookeeper 종료
ssh s1 tmux kill-session -t zookeeper

sleep 10

# Kafka 종료
ssh s1 tmux kill-session -t kafka
ssh s2 tmux kill-session -t kafka
ssh s3 tmux kill-session -t kafka
```

# Spark Check
## Service Start and Stop
```
# Spark 재시작
$SPARK_HOME/sbin/stop-all.sh
$SPARK_HOME/sbin/start-all.sh
```

## pySpark shell 실행 
```
# ssh s1
pyspark
```

## Example Code 
```
from pyspark import SparkContext, SparkConf

# Spark 설정
conf = SparkConf().setAppName("TaskDistribution").setMaster("spark://s1:7077")
sc = SparkContext(conf=conf)

# 데이터 생성
data = range(100)
rdd = sc.parallelize(data, 1000).repartition(3)

# 각 파티션의 실행 노드 확인
def log_partition(index, iterator):
    import socket
    hostname = socket.gethostname()
    print(f"Partition {index} is running on {hostname}")
    return iterator

result = rdd.mapPartitionsWithIndex(log_partition).collect()

# 결과 출력
print(result)

# SparkContext 종료
sc.stop()

```
