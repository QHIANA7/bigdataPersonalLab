import time
from datetime import datetime
from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import col, row_number, to_timestamp, current_timestamp, expr
from pyspark.sql.types import StructType, StringType, IntegerType, DoubleType, BooleanType
from prometheus_client import start_http_server, Gauge

# --- 설정 ---
PROMETHEUS_PORT = 9991
REFRESH_INTERVAL_SECONDS = 30
HDFS_BASE = "hdfs://s1:9000"

# --- 프로메테우스 메트릭 정의 ---
METRIC_LABELS = ['device_id']
ERROR_METRICS = {
    'sensor1': Gauge('fms_error_count_per_hour', 'fms_error_count_per_hour', METRIC_LABELS)
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

def update_error_metrics(spark):
    now = datetime.now()
    partition_path = f"{HDFS_BASE}/fms/dataerr/year={now.year}/month={now.month}/day={now.day}/hour={now.hour}/"
    print(f"🔄 최신 'error' 데이터를 찾습니다... (경로: {partition_path})")

    try:
        # 1. HDFS 경로의 JSON 파일 읽기
        df_err = spark.read.schema(JSON_SCHEMA).option("multiline", "true").json(partition_path)

        if df_err.rdd.isEmpty():
            print("✅ 처리할 최신 'error' 데이터가 없습니다.")
            for gauge in ERROR_METRICS.values():
                gauge.clear()
            return

        # 2-1. collected_at -> 타임스탬프 변환
        df_err = df_err.withColumn("collected_at_ts", to_timestamp("collected_at"))

        # 2-2. 최근 1시간 + 유효 데이터 필터링
        df_err = df_err.filter(col("collected_at_ts") >= current_timestamp() - expr("INTERVAL 1 HOUR"))

        # 2-3. DeviceId별 카운트
        device_counts = df_err.groupBy("DeviceId").count().collect()

        # 3. 프로메테우스 메트릭 업데이트
        for gauge in ERROR_METRICS.values():
            gauge.clear()

        for row in device_counts:
            labels = {"device_id": str(row["DeviceId"])}
            for metric_name, gauge in ERROR_METRICS.items():
                value = row["count"]
                if value is not None:
                    gauge.labels(**labels).set(value)

        print(f"✅ {df_latest.count()}개 'error' 장비의 최신 메트릭을 성공적으로 업데이트했습니다.")

    except Exception as e:
        if "Path does not exist" in str(e):
            print(f"⚠️ HDFS 경로를 찾을 수 없습니다: {partition_path}. 'error' 데이터가 아직 없을 수 있습니다.")
        else:
            print(f"❌ 데이터 처리 중 오류가 발생했습니다: {e}")

def main():
    spark = SparkSession.builder \
        .appName("FMS HDFS Error to Prometheus") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    print(f"🚀 'error' 데이터 프로메테우스 메트릭 서버를 시작합니다. (포트: {PROMETHEUS_PORT})")
    start_http_server(PROMETHEUS_PORT)
    print(f"🔗 메트릭 확인: http://<your-spark-driver-ip>:{PROMETHEUS_PORT}")

    try:
        while True:
            update_error_metrics(spark)
            print(f"🕒 다음 업데이트까지 {REFRESH_INTERVAL_SECONDS}초 대기합니다...")
            time.sleep(REFRESH_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n🛑 스크립트를 종료합니다.")
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
