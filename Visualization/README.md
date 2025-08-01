# 시각화 및 알림 시스템

## Grafana 대시보드 구성
### [1] 실시간 모니터링 대시보드
* **센서 실시간 차트**: 온도/습도/압력 시계열 그래프  
* **모터 성능 모니터링**: 3개 모터 RPM 실시간 추적
* **장애건수 통계**: 1시간 단위 장애 발생 건수 표시
* **대시보드 설정**: [`fms-dashboard.json`](../hadoopInstall/df/g1/provisioning/dashboards/fms_dashboard.json)

* **핵심 시각화 패널**

| 패널 유형  | 메트릭      | 임계값                | 업데이트 주기 |
| ---------- | ----------- | ----------------------| ------------- |
| Stat       | 장비 장애건수| 시간 당 100건 이하 정상 | 10초          |
| TimeSeries | 센서 값     |                       | 10초          |

* **대시보드 미리보기**
<img width="2871" height="1508" alt="image" src="https://github.com/user-attachments/assets/7b32a8e0-a0ea-423d-a2c8-c09740b1e899" />


### [2] 구조적 스트리밍 성능 모니터링 대시보드
* **스트리밍 성능 통계** : 배치당 처리 레코드 수, 소요시간 표시
* **대시보드 설정**: [`fms_performance.json`](../hadoopInstall/df/g1/provisioning/dashboards/fms_performance.json)

* **핵심 시각화 패널**

| 패널 유형  | 메트릭               | 임계값                 | 업데이트 주기 |
| ---------- | ------------------- | ----------------------| ------------- |
| TimeSeries | 배치당 처리 레코드 수 | 추후 지정             | 10초          |
| TimeSeries | 배치당 처리 소요 시간 | 추후 지정             | 10초          |

* **대시보드 미리보기**
<img width="2853" height="1580" alt="image" src="https://github.com/user-attachments/assets/d030ca1f-0098-4018-a157-1ebc392a7f2d" />


### [3] 노드 모니터링 대시보드
* **클러스터 성능 통계** : 클러스터당 CPU, 메모리, 스토리지, 네트워크 성능 표시
* **대시보드 설정**: [`1860_custom.json`](../hadoopInstall/df/g1/provisioning/dashboards/1860_custom.json)
* **대시보드 미리보기**
<img width="2850" height="1635" alt="image" src="https://github.com/user-attachments/assets/48cbe40c-d2ce-4cb4-a664-5751337b6849" />


## 알림 시스템 설계
### Webex채널 알림 시스템
* **Webex 알림**: 실시간 채팅 기반 즉시 알림
* **알림 템플릿**: Webex 메시지 형태에 구조화된 메시지
* **알림 관리자**: [`alerting.yaml`](../hadoopInstall/df/g1/provisioning/alerting/alerting.yaml)

### 알림 규칙 및 임계값
* **센서/모터 이상**: 온도 0~100°C, 습도 0~100%, 압력 0~150 PSI, RPM 기준값 범위 이외의 값이 시간당 100건 이상 발생 시
* **시스템 장애**: 클러스터 노드 당 메모리 점유율 75%초과 1분 이상 지속 시

### 알림 메시지 샘플
<img width="1112" height="1055" alt="image" src="https://github.com/user-attachments/assets/52e55576-ea62-484d-8808-95e1878e8ed4" />


## 운영 대시보드 기능
### 관리자 대시보드
* **시스템 상태**: 클러스터 전체 헬스 상태
* **성능 메트릭**: 처리량, 지연시간, 리소스 사용률
* **에러 추적**: 최근 에러 발생 현황 및 트렌드
* **용량 관리**: 디스크, 메모리 사용량 모니터링

## 주요 기술 특징
* **실시간 업데이트**: 10초 간격 자동 새로고침
* **알림 통합**: Grafana + Prometheus + 외부 시스템
* **프로비저닝 기술**: 컨테이너 생성 시 데이터소스(프로메테우스)와 설정 대시보드 자동 구성
* **프로비저닝 예시** : 프로비저닝된 경고 규칙 [`alerting.yaml`](../hadoopInstall/df/g1/provisioning/alerting/alerting.yaml)
<img width="2424" height="642" alt="image" src="https://github.com/user-attachments/assets/95f26024-027f-45e7-8b05-2267851db798" />

## 주요 산출물
* Grafana 실시간 모니터링 대시보드
* 경고 알림 및 알림 채널 설정
* 운영 관리 대시보드
