import time
from datetime import datetime
from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import col, row_number
from pyspark.sql.types import StructType, StringType, IntegerType, DoubleType, BooleanType
from prometheus_client import start_http_server, Gauge

# --- 설정 ---
PROMETHEUS_PORT = 9993
REFRESH_INTERVAL_SECONDS = 30
HDFS_BASE = "hdfs://s1:9000"

# --- 프로메테우스 메트릭 정의 ---
METRIC_LABELS = ['device_id']
RAW_METRICS = {
    'sensor1': Gauge('fms_raw_latest_sensor1', 'Latest raw value of sensor1', METRIC_LABELS),
    'sensor2': Gauge('fms_raw_latest_sensor2', 'Latest raw value of sensor2', METRIC_LABELS),
    'sensor3': Gauge('fms_raw_latest_sensor3', 'Latest raw value of sensor3', METRIC_LABELS),
    'motor1': Gauge('fms_raw_latest_motor1', 'Latest raw value of motor1', METRIC_LABELS),
    'motor2': Gauge('fms_raw_latest_motor2', 'Latest raw value of motor2', METRIC_LABELS),
    'motor3': Gauge('fms_raw_latest_motor3', 'Latest raw value of motor3', METRIC_LABELS),
}

# --- JSON 데이터 스키마 ---
JSON_SCHEMA = StructType() \
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

def update_raw_metrics(spark):
    now = datetime.now()
    partition_path = f"{HDFS_BASE}/fms/raw-data/year={now.year}/month={now.month}/day={now.day}/hour={now.hour}/"
    print(f"🔄 최신 'raw' 데이터를 찾습니다... (경로: {partition_path})")

    try:
        # 1. HDFS 경로의 JSON 파일 읽기
        df_raw = spark.read.schema(JSON_SCHEMA).option("multiline", "true").json(partition_path)

        if df_raw.rdd.isEmpty():
            print("✅ 처리할 최신 'raw' 데이터가 없습니다.")
            for gauge in RAW_METRICS.values():
                gauge.clear()
            return

        # 2. 각 DeviceId에서 최신 레코드 찾기
        window_spec = Window.partitionBy("DeviceId").orderBy(col("time").desc())
        df_latest = df_raw.withColumn("rank", row_number().over(window_spec)) \
                          .filter(col("rank") == 1) \
                          .select("DeviceId", "sensor1", "sensor2", "sensor3", "motor1", "motor2", "motor3")

        # 3. 프로메테우스 메트릭 업데이트
        for gauge in RAW_METRICS.values():
            gauge.clear()

        for row in df_latest.collect():
            labels = {"device_id": str(row["DeviceId"])}
            for metric_name, gauge in RAW_METRICS.items():
                value = row[metric_name]
                if value is not None:
                    gauge.labels(**labels).set(float(value))

        print(f"✅ {df_latest.count()}개 'raw' 장비의 최신 메트릭을 성공적으로 업데이트했습니다.")

    except Exception as e:
        if "Path does not exist" in str(e):
            print(f"⚠️ HDFS 경로를 찾을 수 없습니다: {partition_path}. 'raw' 데이터가 아직 없을 수 있습니다.")
        else:
            print(f"❌ 데이터 처리 중 오류가 발생했습니다: {e}")

def main():
    spark = SparkSession.builder \
        .appName("FMS HDFS Raw to Prometheus") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    print(f"🚀 'raw' 데이터 프로메테우스 메트릭 서버를 시작합니다. (포트: {PROMETHEUS_PORT})")
    start_http_server(PROMETHEUS_PORT)
    print(f"🔗 메트릭 확인: http://<your-spark-driver-ip>:{PROMETHEUS_PORT}")

    try:
        while True:
            update_raw_metrics(spark)
            print(f"🕒 다음 업데이트까지 {REFRESH_INTERVAL_SECONDS}초 대기합니다...")
            time.sleep(REFRESH_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n🛑 스크립트를 종료합니다.")
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
