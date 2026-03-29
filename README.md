# lora-noise-monitor

공사장 소음 모니터링 시스템 — D1 Mini (ESP8266) + ADS1115 + E220-900T LoRa

## 구성

- `firmware/sensor_node/` — Arduino 펌웨어 (D1 Mini + ADS1115 + E220-900T)
- `gateway/` — Raspberry Pi LoRa 수신 게이트웨이 (Python)
- `server/` — Flask REST API + 대시보드
- `docs/` — 배선 가이드 및 문서

## 특징

- 5분 슬라이딩 등가소음도 (Leq) 1분 주기 전송
- DC Out 단자가 있는 모든 소음계 호환 (센서 타입 A–E)
- KR920 LoRa 대역 (920 MHz)
- SQLite + Flask 실시간 대시보드
