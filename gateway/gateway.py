#!/usr/bin/env python3
"""
gateway.py  –  LoRa 게이트웨이 (Raspberry Pi / PC)

E220-900T UART 수신 → 패킷 파싱 → 웹 서버 HTTP POST

실행 예시:
    python gateway.py --port /dev/ttyAMA0 --server http://192.168.1.100:5000
"""
import argparse
import logging
import time
from datetime import datetime, timezone

import requests
import serial

from lora.protocol import find_packet_in_stream, NoisePacket

# ── 기본 설정 ──────────────────────────────────────────────────
DEFAULT_PORT     = "/dev/ttyAMA0"
DEFAULT_BAUDRATE = 9600
DEFAULT_SERVER   = "http://127.0.0.1:5000"
API_ENDPOINT     = "/api/v1/noise"
RETRY_INTERVAL   = 5
MAX_RETRIES      = 3
RX_TIMEOUT       = 2.0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("gateway")


def init_lora_gpio(m0_pin: int = 17, m1_pin: int = 27, aux_pin: int = 22):
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(m0_pin,  GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(m1_pin,  GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(aux_pin, GPIO.IN)
        GPIO.output(m0_pin, GPIO.LOW)
        GPIO.output(m1_pin, GPIO.LOW)
        time.sleep(0.1)
        log.info("E220 GPIO 초기화 완료 (M0=%d M1=%d AUX=%d)", m0_pin, m1_pin, aux_pin)
        return GPIO
    except ImportError:
        log.warning("RPi.GPIO 없음 – GPIO 제어 건너뜀 (개발 PC 모드)")
        return None


def upload(server: str, pkt: NoisePacket, received_at: str, retries: int = MAX_RETRIES):
    url = server.rstrip("/") + API_ENDPOINT
    payload = {
        "node_id":     pkt.node_id,
        "db_avg":      pkt.db_avg,
        "db_max":      pkt.db_max,
        "db_min":      pkt.db_min,
        "seq":         pkt.seq,
        "rssi":        pkt.rssi,
        "received_at": received_at,
    }
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(url, json=payload, timeout=5)
            if resp.status_code == 201:
                log.info("업로드 성공 | node=%d seq=%d avg=%.1f dB",
                         pkt.node_id, pkt.seq, pkt.db_avg)
                return True
            else:
                log.warning("서버 응답 %d: %s", resp.status_code, resp.text[:120])
        except requests.RequestException as e:
            log.error("업로드 실패 (%d/%d): %s", attempt, retries, e)
            if attempt < retries:
                time.sleep(RETRY_INTERVAL)
    return False


def run(port: str, baudrate: int, server: str, m0: int, m1: int, aux: int):
    init_lora_gpio(m0, m1, aux)
    log.info("시리얼 포트 열기: %s @ %d baud", port, baudrate)
    ser = serial.Serial(port, baudrate, timeout=RX_TIMEOUT)
    buf = bytearray()
    log.info("게이트웨이 시작 – 서버: %s", server)

    while True:
        chunk = ser.read(64)
        if chunk:
            buf.extend(chunk)
        while True:
            pkt, consumed = find_packet_in_stream(buf)
            if pkt is None:
                break
            ts = datetime.now(timezone.utc).isoformat()
            log.info("수신 | node=0x%02X seq=%d avg=%.1f dB max=%.1f dB min=%.1f dB",
                     pkt.node_id, pkt.seq, pkt.db_avg, pkt.db_max, pkt.db_min)
            upload(server, pkt, ts)


def main():
    parser = argparse.ArgumentParser(description="LoRa 소음 모니터링 게이트웨이")
    parser.add_argument("--port",     default=DEFAULT_PORT)
    parser.add_argument("--baudrate", default=DEFAULT_BAUDRATE, type=int)
    parser.add_argument("--server",   default=DEFAULT_SERVER)
    parser.add_argument("--m0-pin",   default=17, type=int)
    parser.add_argument("--m1-pin",   default=27, type=int)
    parser.add_argument("--aux-pin",  default=22, type=int)
    args = parser.parse_args()

    try:
        run(args.port, args.baudrate, args.server, args.m0_pin, args.m1_pin, args.aux_pin)
    except KeyboardInterrupt:
        log.info("게이트웨이 종료")
    except serial.SerialException as e:
        log.error("시리얼 오류: %s", e)


if __name__ == "__main__":
    main()
