"""
protocol.py  –  E220-900T LoRa 패킷 파서
패킷 구조 (13 바이트):
  [0]      HDR1  = 0xAA
  [1]      HDR2  = 0xBB
  [2]      VER   = 0x01
  [3]      NODE  = 노드 ID
  [4][5]   DBAVG = uint16 (단위 0.1 dB)
  [6][7]   DBMAX = uint16 (단위 0.1 dB)
  [8][9]   DBMIN = uint16 (단위 0.1 dB)
  [10]     SEQ   = 시퀀스 번호
  [11][12] CRC16 = CRC-16/MODBUS
"""
import struct
from dataclasses import dataclass

PKT_LEN    = 13
HDR1       = 0xAA
HDR2       = 0xBB
SUPPORTED_VER = 0x01


@dataclass
class NoisePacket:
    node_id: int
    db_avg: float      # dB
    db_max: float      # dB
    db_min: float      # dB
    seq: int
    rssi: int = 0      # 게이트웨이에서 추가 (dBm)


def _crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def parse_packet(raw: bytes, rssi: int = 0) -> NoisePacket | None:
    """13 바이트 원시 패킷을 파싱해 NoisePacket 반환. 실패 시 None."""
    if len(raw) < PKT_LEN:
        return None
    if raw[0] != HDR1 or raw[1] != HDR2:
        return None
    if raw[2] != SUPPORTED_VER:
        return None

    crc_recv = (raw[11] << 8) | raw[12]
    crc_calc = _crc16_modbus(raw[:11])
    if crc_recv != crc_calc:
        return None

    node_id = raw[3]
    db_avg  = struct.unpack(">H", raw[4:6])[0] / 10.0
    db_max  = struct.unpack(">H", raw[6:8])[0] / 10.0
    db_min  = struct.unpack(">H", raw[8:10])[0] / 10.0
    seq     = raw[10]

    return NoisePacket(
        node_id=node_id,
        db_avg=db_avg,
        db_max=db_max,
        db_min=db_min,
        seq=seq,
        rssi=rssi,
    )


def find_packet_in_stream(buf: bytearray) -> tuple[NoisePacket | None, int]:
    """
    바이트 스트림 버퍼에서 첫 번째 유효 패킷을 찾아 반환.
    Returns: (packet_or_None, bytes_consumed)
    """
    while len(buf) >= PKT_LEN:
        if buf[0] != HDR1:
            buf.pop(0)
            continue
        if buf[1] != HDR2:
            buf.pop(0)
            continue

        raw = bytes(buf[:PKT_LEN])
        pkt = parse_packet(raw)
        if pkt is not None:
            del buf[:PKT_LEN]
            return pkt, PKT_LEN
        else:
            buf.pop(0)

    return None, 0
