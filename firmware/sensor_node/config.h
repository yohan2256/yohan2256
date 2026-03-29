// ============================================================
//  config.h  –  공사장 소음 모니터링 센서 노드 설정
//  하드웨어: D1 Mini (ESP8266) + ADS1115 + E220-900T
// ============================================================
#pragma once

// ── Node 식별 ────────────────────────────────────────────────
#define NODE_ID         0x01        // 노드 ID (0x01 ~ 0xFF)
#define FIRMWARE_VER    "1.0.0"

// ── ADS1115 ──────────────────────────────────────────────────
#define ADS_I2C_ADDR    0x48        // ADDR핀 GND = 0x48
// 소음 센서 아날로그 출력 채널 (A0~A3)
#define NOISE_CHANNEL   0           // ADS1115 A0 채널

// ADS1115 PGA 설정: ±4.096V 기준
// LSB = 4.096 / 32768 = 0.125 mV
#define ADS_GAIN        GAIN_ONE    // ±4.096 V

// ── 소음 센서 보정 (선형 회귀: dB = SLOPE * mV + OFFSET) ────
// 사용 센서에 맞게 교정값 조정 (예: SEN0232 기준 초기값)
#define NOISE_SLOPE     0.1075f     // dB/mV
#define NOISE_OFFSET    44.0f       // dB (0 mV 기준)
#define NOISE_MIN_DB    30.0f       // 유효 최솟값 (dB)
#define NOISE_MAX_DB    130.0f      // 유효 최댓값 (dB)

// ── 샘플링 ───────────────────────────────────────────────────
#define SAMPLE_COUNT        50      // 평균 산출용 샘플 수
#define SAMPLE_INTERVAL_MS  20      // 샘플 간격 (ms) → 50 Hz
#define SEND_INTERVAL_MS  10000     // LoRa 전송 주기 (ms)

// ── E220-900T 핀 배치 (D1 Mini) ──────────────────────────────
// SoftwareSerial: D6=RX(GPIO12), D5=TX(GPIO14)
#define LORA_RX_PIN     12          // D6 ← E220 TX
#define LORA_TX_PIN     14          // D5 → E220 RX
#define LORA_M0_PIN     13          // D7
#define LORA_M1_PIN     15          // D8
#define LORA_AUX_PIN    16          // D0
#define LORA_BAUDRATE   9600

// ── LoRa 채널 / 주소 ─────────────────────────────────────────
#define LORA_CHANNEL    0x06        // 채널 06 = 920.125 MHz (KR 920)
#define LORA_ADDR_H     0x00        // 자신의 주소 상위
#define LORA_ADDR_L     NODE_ID     // 자신의 주소 하위
#define GW_ADDR_H       0x00        // 게이트웨이 주소 상위
#define GW_ADDR_L       0x00        // 게이트웨이 주소 하위

// ── 패킷 프로토콜 ─────────────────────────────────────────────
#define PKT_HEADER_1    0xAA
#define PKT_HEADER_2    0xBB
#define PKT_VERSION     0x01
