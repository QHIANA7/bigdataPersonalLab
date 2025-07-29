import os
import subprocess
import tempfile
import time
import json
import aiohttp
import asyncio
import logging
from datetime import datetime
from confluent_kafka import Consumer, KafkaError

# 설정
BROKER = "s1:9092,s2:9092,s3:9092"
TOPIC = "topic1"
GROUP_ID = "fms-data-processor"
FETCH_INTERVAL = 30
HDFS_DIR = "/fms/raw-data/"

# 로깅
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AsyncFMSConsumer:
    def __init__(self):
        self.consumer = Consumer({
            'bootstrap.servers': BROKER,
            'group.id': GROUP_ID,
            'auto.offset.reset': 'earliest'
        })
        self.buffer = []
        self.last_flush_time = time.time()

        # HDFS 디렉토리 생성 확인
        self.ensure_hdfs_directory(HDFS_DIR)

    def ensure_hdfs_directory(self, path):
        """HDFS 디렉토리가 없으면 생성"""
        try:
            result = subprocess.run(
                ["hdfs", "dfs", "-test", "-d", path],
                check=False
            )
            if result.returncode != 0:
                # 디렉토리 없으면 생성
                subprocess.run(
                    ["hdfs", "dfs", "-mkdir", "-p", path],
                    check=True
                )
                logger.info(f"📁 HDFS 디렉토리 생성됨: {path}")
            else:
                logger.info(f"✅ HDFS 디렉토리 존재 확인됨: {path}")
        except Exception as e:
            logger.error(f"HDFS 디렉토리 생성 중 오류 발생: {e}")

    def write_buffer_to_hdfs(self):
        """버퍼 내용을 타임스탬프 파일로 HDFS에 저장"""
        if not self.buffer:
            return

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sensor-data-{timestamp_str}.jsonl"
        hdfs_path = os.path.join(HDFS_DIR, filename)

        try:
            with tempfile.NamedTemporaryFile('w', delete=False) as tmp:
                for record in self.buffer:
                    tmp.write(json.dumps(record) + '\n')
                tmp_path = tmp.name

            # HDFS로 업로드
            subprocess.run(
                ["hdfs", "dfs", "-put", "-f", tmp_path, hdfs_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"📤 HDFS 저장 완료: {hdfs_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"HDFS 저장 실패: {e.stderr.strip()}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            self.buffer.clear()
            self.last_flush_time = time.time()

    def process_message(self, msg):
        try:
            raw_value = msg.value().decode('utf-8')
            logger.info(f"[RAW INPUT] {raw_value}")
            data = json.loads(raw_value)
            self.buffer.append(data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")

    async def run(self):
        logger.info("FMS Data Consumer 시작... (HDFS 저장 모드)")
        logger.info(f"구독 토픽: {TOPIC}")

        self.consumer.subscribe([TOPIC])

        try:
            while True:
                msg = self.consumer.poll(1.0)

                if msg is None:
                    continue
                elif msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        logger.error(f"Consumer error: {msg.error()}")
                else:
                    self.process_message(msg)

                elapsed_time = max(0, FETCH_INTERVAL - (time.time() - self.last_flush_time))
                logger.info(f"🕒 다음 처리까지 {elapsed_time:.1f}초 남음... 현재 버퍼 수 {len(self.buffer)}")

                if elapsed_time <= 0:
                    self.write_buffer_to_hdfs()

                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단됨")
        finally:
            self.write_buffer_to_hdfs()
            self.consumer.close()
            logger.info("Consumer 종료")

def main():
    consumer = AsyncFMSConsumer()
    asyncio.run(consumer.run())

if __name__ == "__main__":
    main()