# 통합 데이터 파이프라인 모듈 개발

## Kafka-Spark Streaming 연동
### 실시간 스트리밍 처리 모듈
* **스트림 처리기**: Kafka → Spark Streaming 실시간 연동
* **데이터 파싱**: JSON 스키마 기반 검증 및 변환
* **체크포인트**: 장애 복구를 위한 상태 저장
* **실시간 처리기**: [`src/fms-realtime-processor.py`](src/fms-realtime-processor.py)

### 데이터 파티셔닝 전략
| 데이터 계층화   | 저장 위치        | 파티션 기준             | 보존 기간 |
| -------------- | ---------------- | ---------------------- | ------- |
| 원시 데이터     | `/fms/raw-data`  | year, month, day, hour | 미정    |
| 처리된 데이터   | `/fms/data`      | year, month, day, hour | 미정    |
| 이상 데이터     | `/fms/fail`      | year, month, day, hour | 미정    |
| 장비오류 데이터 | `/fms/dataerr`   | year, month, day, hour | 미정    |

## HDFS 저장 로직 구현
### 계층화 저장 시스템
* **원시 데이터**: JSON 형태, 30초 간격 실시간 저장
* **처리된 데이터**: JSON 형태, 30초 간격 실시간 저장
* **알림 데이터**: JSON 형태, 30초 간격 실시간 저장
* **파티셔닝**: 장비별, 시간별 효율적 분할

## 배치 처리 스케줄링
### 단순 스케줄러 기반 워크플로우
* **데이터 수집**: Kafka 토픽으로 부터 데이터 수집
* **스트림 처리**: Spark 애플리케이션 실행
* **품질 검사**: 데이터 품질 검증 및 리포트

## 파이프라인 아키텍처
```
FMS API → Kafka → Spark Streaming → HDFS
    ↓        ↓         ↓           ↓
  수집기    버퍼링    실시간처리   계층저장
    ↓        ↓         ↓           ↓
  에러처리  재전송    품질검증    백업/복제
```