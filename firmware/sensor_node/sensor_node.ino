// ============================================================
//  sensor_node.ino  –  공사장 소음 모니터링 센서 노드
//
//  하드웨어 구성:
//    D1 Mini (ESP8266)
//    ├─ I²C (D1=SCL, D2=SDA) ── ADS1115 ── 소음 센서 아날로그
//    └─ SoftwareSerial        ── E220-900T (LoRa 900 MHz)
//
//  라이브러리 (Arduino Library Manager):
//    - Adafruit ADS1X15  (Adafruit)
//    - EByte LoRa E220   (Renzo Mischianti) 또는 SoftwareSerial 직접 제어
// ============================================================
#include <Arduino.h>
#include <Wire.h>
#include <SoftwareSerial.h>
#include <Adafruit_ADS1X15.h>
#include "config.h"

// ── 전역 객체 ─────────────────────────────────────────────────
Adafruit_ADS1115 ads;
SoftwareSerial loraSerial(LORA_RX_PIN, LORA_TX_PIN);

// ── 패킷 구조 (총 13 바이트) ──────────────────────────────────
// [0]    HDR1  = 0xAA
// [1]    HDR2  = 0xBB
// [2]    VER   = 0x01
// [3]    NODE  = NODE_ID
// [4][5] DB    = uint16_t, 단위 0.1 dB  (예: 653 → 65.3 dB)
// [6][7] DBMAX = uint16_t, 측정 구간 최대값
// [8][9] DBMIN = uint16_t, 측정 구간 최솟값
// [10]   SEQ   = 패킷 시퀀스 (0~255 순환)
// [11][12] CRC16

#define PKT_LEN     13

static uint8_t  pktSeq = 0;
static uint32_t lastSendMs = 0;

// ── CRC-16/MODBUS ─────────────────────────────────────────────
uint16_t crc16(const uint8_t *buf, uint8_t len) {
    uint16_t crc = 0xFFFF;
    for (uint8_t i = 0; i < len; i++) {
        crc ^= (uint16_t)buf[i];
        for (uint8_t b = 0; b < 8; b++) {
            if (crc & 0x0001) crc = (crc >> 1) ^ 0xA001;
            else              crc >>= 1;
        }
    }
    return crc;
}

// ── E220-900T 초기화 ──────────────────────────────────────────
void loraSetMode(uint8_t m0, uint8_t m1) {
    digitalWrite(LORA_M0_PIN, m0);
    digitalWrite(LORA_M1_PIN, m1);
    delay(50);
    uint32_t t = millis();
    while (digitalRead(LORA_AUX_PIN) == LOW && millis() - t < 500) delay(5);
    delay(20);
}

void loraConfig() {
    loraSetMode(1, 1);
    delay(100);

    uint8_t cfg[] = {
        0xC0,
        0x00,
        0x06,
        LORA_ADDR_H,
        LORA_ADDR_L,
        0x00,
        0b00100000,
        0b00000000,
        LORA_CHANNEL
    };
    loraSerial.write(cfg, sizeof(cfg));
    delay(200);

    while (loraSerial.available()) loraSerial.read();
    loraSetMode(0, 0);
}

// ── ADS1115 에서 소음 레벨(dB) 읽기 ─────────────────────────
struct NoiseSample {
    float avg;
    float maxDb;
    float minDb;
};

NoiseSample sampleNoise() {
    float sumMv  = 0;
    float maxMv  = 0;
    float minMv  = 99999;

    for (int i = 0; i < SAMPLE_COUNT; i++) {
        int16_t raw = ads.readADC_SingleEnded(NOISE_CHANNEL);
        float mv = raw * 0.125f;
        if (mv < 0) mv = 0;
        sumMv += mv;
        if (mv > maxMv) maxMv = mv;
        if (mv < minMv) minMv = mv;
        delay(SAMPLE_INTERVAL_MS);
    }

    NoiseSample s;
    float avgMv = sumMv / SAMPLE_COUNT;
    s.avg   = constrain(NOISE_SLOPE * avgMv  + NOISE_OFFSET, NOISE_MIN_DB, NOISE_MAX_DB);
    s.maxDb = constrain(NOISE_SLOPE * maxMv  + NOISE_OFFSET, NOISE_MIN_DB, NOISE_MAX_DB);
    s.minDb = constrain(NOISE_SLOPE * minMv  + NOISE_OFFSET, NOISE_MIN_DB, NOISE_MAX_DB);
    return s;
}

// ── LoRa 패킷 전송 ────────────────────────────────────────────
void sendPacket(NoiseSample &ns) {
    uint8_t pkt[PKT_LEN];
    uint16_t dbAvg = (uint16_t)(ns.avg   * 10.0f + 0.5f);
    uint16_t dbMax = (uint16_t)(ns.maxDb * 10.0f + 0.5f);
    uint16_t dbMin = (uint16_t)(ns.minDb * 10.0f + 0.5f);

    pkt[0]  = PKT_HEADER_1;
    pkt[1]  = PKT_HEADER_2;
    pkt[2]  = PKT_VERSION;
    pkt[3]  = NODE_ID;
    pkt[4]  = (dbAvg >> 8) & 0xFF;
    pkt[5]  = dbAvg & 0xFF;
    pkt[6]  = (dbMax >> 8) & 0xFF;
    pkt[7]  = dbMax & 0xFF;
    pkt[8]  = (dbMin >> 8) & 0xFF;
    pkt[9]  = dbMin & 0xFF;
    pkt[10] = pktSeq++;

    uint16_t crc = crc16(pkt, 11);
    pkt[11] = (crc >> 8) & 0xFF;
    pkt[12] = crc & 0xFF;

    uint8_t header[3] = {GW_ADDR_H, GW_ADDR_L, LORA_CHANNEL};
    loraSerial.write(header, 3);
    loraSerial.write(pkt, PKT_LEN);

    Serial.printf("[TX] seq=%u avg=%.1f max=%.1f min=%.1f dB\n",
                  pkt[10], ns.avg, ns.maxDb, ns.minDb);
}

// ── setup / loop ──────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    Serial.println("\n[NoiseNode] 부팅 중...");

    pinMode(LORA_M0_PIN,  OUTPUT);
    pinMode(LORA_M1_PIN,  OUTPUT);
    pinMode(LORA_AUX_PIN, INPUT);
    loraSerial.begin(LORA_BAUDRATE);
    loraConfig();
    Serial.println("[LoRa] E220-900T 초기화 완료");

    Wire.begin();
    if (!ads.begin(ADS_I2C_ADDR)) {
        Serial.println("[ADS] 연결 실패! I2C 배선을 확인하세요.");
        while (1) delay(1000);
    }
    ads.setGain(ADS_GAIN);
    Serial.println("[ADS] ADS1115 초기화 완료");

    lastSendMs = millis();
    Serial.printf("[NoiseNode] ID=0x%02X, 전송 주기=%d ms\n",
                  NODE_ID, SEND_INTERVAL_MS);
}

void loop() {
    if (millis() - lastSendMs >= SEND_INTERVAL_MS) {
        lastSendMs = millis();
        NoiseSample ns = sampleNoise();
        sendPacket(ns);
    }

    while (loraSerial.available()) {
        uint8_t b = loraSerial.read();
        (void)b;
    }
}
