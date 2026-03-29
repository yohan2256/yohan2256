# 배선 가이드

## 센서 노드 (D1 Mini + ADS1115 + E220-900T)

### ADS1115 ↔ D1 Mini (I²C)

| ADS1115 | D1 Mini | 비고 |
|---------|---------|------|
| VDD     | 3.3V    |      |
| GND     | GND     |      |
| SCL     | D1 (GPIO5) | I²C 클럭 |
| SDA     | D2 (GPIO4) | I²C 데이터 |
| ADDR    | GND     | I²C 주소 0x48 |
| A0      | 소음 센서 OUT | 아날로그 입력 |

> 소음 센서 VCC → 5V, GND → GND 연결 (센서 사양에 따라 조정)

### E220-900T ↔ D1 Mini (UART + 제어 핀)

| E220-900T | D1 Mini | 비고 |
|-----------|---------|------|
| VCC       | 3.3V    | 최대 500mA 필요 → 별도 3.3V 레귤레이터 권장 |
| GND       | GND     |      |
| TXD       | D6 (GPIO12) | D1 Mini RX |
| RXD       | D5 (GPIO14) | D1 Mini TX |
| M0        | D7 (GPIO13) |      |
| M1        | D8 (GPIO15) |      |
| AUX       | D0 (GPIO16) | 풀업 저항 10kΩ 권장 |

> **주의**: E220-900T 는 3.3V 신호 레벨. D1 Mini 5V 핀 절대 연결 금지.

---

## 게이트웨이 (Raspberry Pi + E220-900T)

### E220-900T ↔ Raspberry Pi (UART + GPIO)

| E220-900T | RPi GPIO (BCM) | 비고 |
|-----------|----------------|------|
| VCC       | 3.3V (Pin 1)   |      |
| GND       | GND (Pin 6)    |      |
| TXD       | GPIO15 / RXD (Pin 10) | RPi UART RX |
| RXD       | GPIO14 / TXD (Pin 8)  | RPi UART TX |
| M0        | GPIO17 (Pin 11) |      |
| M1        | GPIO27 (Pin 13) |      |
| AUX       | GPIO22 (Pin 15) |      |

RPi UART 활성화:
```bash
sudo raspi-config → Interface Options → Serial Port → No shell, Yes hardware
```

---

## 시스템 구성도

```
[공사장 현장]                          [사무소/서버실]
  소음 센서
    │ (아날로그)
  ADS1115
    │ (I²C)
  D1 Mini ──(소프트웨어시리얼)── E220-900T ))))  LoRa 900MHz  (((( E220-900T ── Raspberry Pi
                                                                                    │ (HTTP POST)
                                                                               Flask 웹서버
                                                                                    │
                                                                                 SQLite DB
                                                                                    │
                                                                               대시보드 (브라우저)
```

---

## 주요 파라미터

| 항목 | 값 |
|------|-|
| LoRa 주파수 | 920.125 MHz (CH 06, KR 920) |
| Air Rate | 2.4 kbps |
| TX 출력 | 22 dBm |
| 전송 주기 | 10 초 |
| 패킷 크기 | 13 바이트 |
| 소음 단위 | 0.1 dB (uint16) |
