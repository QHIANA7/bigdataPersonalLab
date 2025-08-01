import subprocess
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp, date_format, year, month, dayofmonth, hour
from pyspark.sql.types import StructType, StringType, IntegerType, DoubleType, BooleanType
from pyspark.sql.streaming import StreamingQueryListener

class ThroughputListener(StreamingQueryListener):
    def onQueryStarted(self, event):
        print(f"✅ 쿼리 시작됨: {event.id}")

    def onQueryProgress(self, event):
        progress = event.progress
        name = progress.name
        inputRows = progress.numInputRows
        duration = progress.durationMs["addBatch"]
        processingRate = progress.inputRowsPerSecond

        logger.info(f"⚡ [Query: {name}] 처리 건수: {inputRows}, 소요 시간: {duration}ms, 처리 속도: {processingRate} rows/sec")

    def onQueryTerminated(self, event):
        print(f"⛔ 쿼리 종료됨: {event.id}")

# 설정
BROKER = "s1:9092,s2:9092,s3:9092"
TOPIC = "topic1"
GROUP_ID = "fms-data-processor"
FETCH_INTERVAL = 30
HDFS_DIR = "/fms"

# 로깅
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 0. HDFS 디렉토리 생성 확인
"""HDFS 디렉토리가 없으면 생성"""
try:
    result = subprocess.run(
        ["hdfs", "dfs", "-test", "-d", HDFS_DIR],
        check=False
    )
    if result.returncode != 0:
        # 디렉토리 없으면 생성
        subprocess.run(
            ["hdfs", "dfs", "-mkdir", "-p", HDFS_DIR],
            check=True
        )
        logger.info(f"📁 HDFS 디렉토리 생성됨: {HDFS_DIR}")
    else:
        logger.info(f"✅ HDFS 디렉토리 존재 확인됨: {HDFS_DIR}")
except Exception as e:
    logger.error(f"HDFS 디렉토리 생성 중 오류 발생: {e}")

# 1. Spark 세션 생성
spark = SparkSession.builder \
    .appName("KafkaSparkStreamingPreprocessing") \
    .getOrCreate()

# 1-1. 처리량 모니터링
spark.streams.addListener(ThroughputListener())

# 2. Kafka 메시지 스키마 정의
schema = StructType() \
    .add("time", StringType()) \
    .add("DeviceId", IntegerType()) \
    .add("sensor1", DoubleType()) \
    .add("sensor2", DoubleType()) \
    .add("sensor3", DoubleType()) \
    .add("motor1", DoubleType()) \
    .add("motor2", DoubleType()) \
    .add("motor3", DoubleType()) \
    .add("isFail", BooleanType()) \
    .add("collected_at", StringType())

# 3. Kafka에서 읽기
df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", BROKER) \
    .option("subscribe", TOPIC) \
    .load()

# 4. JSON 파싱 및 컬럼 추출
df_json = df_raw.selectExpr("CAST(value AS STRING)") \
    .select(from_json("value", schema).alias("data")) \
    .select("data.*")

# 4-1. null 제거 (전 컬럼 또는 특정 컬럼만)
df_json = df_json.dropna(subset=[
    "sensor1", "sensor2", "sensor3",
    "motor1", "motor2", "motor3",
    "isFail", "DeviceId", "collected_at"
])

# 5. timestamp 및 파티션 컬럼 추가
df = df_json \
    .withColumn("ts", to_timestamp(col("collected_at"))) \
    .withColumn("year", year("ts")) \
    .withColumn("month", month("ts")) \
    .withColumn("day", dayofmonth("ts")) \
    .withColumn("hour", hour("ts"))

# 5-1. 중복 제거
df = df.dropDuplicates([
    "DeviceId", "sensor1", "sensor2", "sensor3",
    "motor1", "motor2", "motor3", "isFail"
])

# 6. 유효성 조건 정의
valid_range = (
    (col("sensor1").between(0, 100)) &
    (col("sensor2").between(0, 100)) &
    (col("sensor3").between(0, 150)) &
    (col("motor1").between(0, 2000)) &
    (col("motor2").between(0, 1500)) &
    (col("motor3").between(0, 1800)) &
    (col("DeviceId").between(1, 100)) &
    (col("isFail").isin(True, False))
)

# 7. 데이터 분기
df_fail     = df.filter(col("isFail") == True)
df_dataerr  = df.filter((col("isFail") == False) & (~valid_range))
df_correct  = df.filter((col("isFail") == False) & valid_range)

# 8. 저장 함수 정의 (HDFS)
def write_stream(target_df, base_path, query_name):
    return target_df \
        .writeStream \
        .queryName(query_name) \
        .format("json") \
        .outputMode("append") \
        .option("path", base_path) \
        .option("checkpointLocation", base_path + "_checkpoint") \
        .partitionBy("year", "month", "day", "hour") \
        .trigger(processingTime="30 seconds") \
        .start()

# 9. 경로 설정 (HDFS)
HDFS_BASE = "hdfs://s1:9000"
query_raw  = write_stream(df, f"{HDFS_BASE}{HDFS_DIR}/raw-data", "raw-data-stream")
query_fail = write_stream(df_fail,    f"{HDFS_BASE}{HDFS_DIR}/fail", "fail-data-stream")
query_err  = write_stream(df_dataerr, f"{HDFS_BASE}{HDFS_DIR}/dataerr", "error-data-stream")
query_ok   = write_stream(df_correct, f"{HDFS_BASE}{HDFS_DIR}/data", "processed-data-stream")

# 10. 실행 유지
query_raw.awaitTermination()
query_fail.awaitTermination()
query_err.awaitTermination()
query_ok.awaitTermination()
