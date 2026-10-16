"""模拟流量分析：生成用户与服务器之间的通信报文序列。

参照 Wireshark 的报文展示方式：
- 每条报文带一棵可展开的分层字段树（Frame / Ethernet II / IPv4 / TCP|UDP / 应用层）
- 每个字段记录它在报文中的字节区间，前端 Hex 视图据此高亮对应字节
- 报文各协议头按真实结构逐字节构造，长度、校验和均真实计算
"""
from __future__ import annotations

import struct
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel, Field

from ..dependencies import get_current_user_optional
from ..models import User

router = APIRouter(prefix="/traffic", tags=["traffic"])

CLIENT_IP = "192.168.1.100"
SERVER_IP = "10.0.0.5"
CLIENT_MAC = "00:0c:29:26:7e:0e"
SERVER_MAC = "00:0c:29:84:86:5f"

_VENDOR = {"00:0c:29": "Vmware"}
_IP_PROTO = {"TCP": 6, "UDP": 17}
_TCP_BITS = {"FIN": 0, "SYN": 1, "RST": 2, "PSH": 3, "ACK": 4, "URG": 5}

# Wireshark 展示顺序：高位 → 低位
TCP_FLAG_LABELS = [
    (7, "Congestion Window Reduced (CWR)"),
    (6, "ECN-Echo"),
    (5, "Urgent"),
    (4, "Acknowledgment"),
    (3, "Push"),
    (2, "Reset"),
    (1, "Syn"),
    (0, "Fin"),
]

MAX_SEGMENTS = 800


class FieldNode(BaseModel):
    """协议字段树中的一个节点。"""

    name: str
    value: str = ""
    start: int | None = None
    length: int | None = None
    children: list["FieldNode"] = Field(default_factory=list)


class HexLine(BaseModel):
    offset: str
    hex_bytes: list[str]
    ascii: str


class PacketOut(BaseModel):
    no: int
    time: float
    src_ip: str
    dst_ip: str
    src_port: int | None
    dst_port: int | None
    protocol: str
    length: int
    info: str
    fields: list[FieldNode]
    hex_lines: list[HexLine]


FieldNode.model_rebuild()


# --------------------------------------------------------------------------- #
# 底层：把协议头拼接成真实字节
# --------------------------------------------------------------------------- #
def _ip_bytes(ip: str) -> bytes:
    return bytes(int(part) for part in ip.split("."))


def _mac_bytes(mac: str) -> bytes:
    return bytes(int(part, 16) for part in mac.split(":"))


def _internet_checksum(data: bytes) -> int:
    if len(data) % 2:
        data += b"\x00"
    total = 0
    for i in range(0, len(data), 2):
        total += (data[i] << 8) | data[i + 1]
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def _mac_label(mac: str) -> str:
    vendor = _VENDOR.get(mac[:8].lower())
    suffix = mac.replace(":", "")[-6:]
    pretty = ":".join(suffix[i : i + 2] for i in range(0, 6, 2))
    return f"{vendor}_{pretty} ({mac})" if vendor else mac


def _tcp_flags_byte(flags: str) -> int:
    value = 0
    for name, bit in _TCP_BITS.items():
        if name in flags:
            value |= 1 << bit
    return value


def _build_ethernet(src_mac: str, dst_mac: str) -> bytes:
    return _mac_bytes(dst_mac) + _mac_bytes(src_mac) + struct.pack("!H", 0x0800)


def _build_ipv4(src_ip: str, dst_ip: str, proto: int, segment: bytes, ttl: int = 64) -> tuple[bytes, int]:
    total_length = 20 + len(segment)
    header = (
        struct.pack("!BBHHHBBH", 0x45, 0x00, total_length, 0, 0x4000, ttl, proto, 0)
        + _ip_bytes(src_ip)
        + _ip_bytes(dst_ip)
    )
    checksum = _internet_checksum(header)
    header = (
        struct.pack("!BBHHHBBH", 0x45, 0x00, total_length, 0, 0x4000, ttl, proto, checksum)
        + _ip_bytes(src_ip)
        + _ip_bytes(dst_ip)
    )
    return header + segment, checksum


def _build_tcp(
    src_ip: str,
    dst_ip: str,
    sport: int,
    dport: int,
    seq: int,
    ack: int,
    flags: str,
    window: int,
    payload: bytes,
) -> tuple[bytes, int]:
    data_offset = 5 << 4  # 头部 20 字节
    flags_byte = _tcp_flags_byte(flags)
    base = struct.pack("!HHIIBBHHH", sport, dport, seq, ack, data_offset, flags_byte, window, 0, 0)
    pseudo = _ip_bytes(src_ip) + _ip_bytes(dst_ip) + struct.pack("!BBH", 0, 6, len(base) + len(payload))
    checksum = _internet_checksum(pseudo + base + payload)
    header = struct.pack("!HHIIBBHHH", sport, dport, seq, ack, data_offset, flags_byte, window, checksum, 0)
    return header + payload, checksum


def _build_udp(src_ip: str, dst_ip: str, sport: int, dport: int, payload: bytes) -> tuple[bytes, int]:
    length = 8 + len(payload)
    base = struct.pack("!HHHH", sport, dport, length, 0)
    pseudo = _ip_bytes(src_ip) + _ip_bytes(dst_ip) + struct.pack("!BBH", 0, 17, length)
    checksum = _internet_checksum(pseudo + base + payload) or 0xFFFF
    header = struct.pack("!HHHH", sport, dport, length, checksum)
    return header + payload, checksum


def _hex_lines(data: bytes) -> list[HexLine]:
    lines: list[HexLine] = []
    for i in range(0, len(data), 16):
        chunk = data[i : i + 16]
        hex_bytes = [f"{b:02x}" for b in chunk] + [""] * (16 - len(chunk))
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(HexLine(offset=f"{i:04x}", hex_bytes=hex_bytes, ascii=ascii_part))
    return lines


def _arrival_time(t: float) -> str:
    moment = datetime(1970, 1, 1) + timedelta(hours=8, seconds=t)
    nanos = int(round((t % 1) * 1e9))
    if nanos >= 1_000_000_000:
        nanos -= 1_000_000_000
    return (
        f"{moment.strftime('%b')} {moment.day:2d}, {moment.year} "
        f"{moment.strftime('%H:%M:%S')}.{nanos:09d} 中国标准时间"
    )


def _flag_bit_str(byte: int, target: int) -> str:
    cells = [str((byte >> i) & 1) if i == target else "." for i in range(7, -1, -1)]
    text = "".join(cells)
    return f"{text[:4]} {text[4:]}"


# --------------------------------------------------------------------------- #
# 字段树
# --------------------------------------------------------------------------- #
def _frame_node(no: int, t: float, prev_time: float, frame_len: int, protocol: str, layers: str) -> FieldNode:
    bits = frame_len * 8
    node = FieldNode(
        name=f"Frame {no}",
        value=f"{frame_len} bytes on wire ({bits} bits), {frame_len} bytes captured ({bits} bits)",
        start=0,
        length=frame_len,
    )
    node.children = [
        FieldNode(name="Encapsulation type", value="Ethernet (1)"),
        FieldNode(name="Arrival Time", value=_arrival_time(t)),
        FieldNode(name="Epoch Time", value=f"{t:.9f} seconds"),
        FieldNode(name="[Time delta from previous captured frame", value=f"{t - prev_time:.9f} seconds]"),
        FieldNode(name="[Time delta from previous displayed frame", value=f"{t - prev_time:.9f} seconds]"),
        FieldNode(name="[Time since reference or first frame", value=f"{t:.9f} seconds]"),
        FieldNode(name="Frame Number", value=str(no)),
        FieldNode(name="Frame Length", value=f"{frame_len} bytes ({bits} bits)"),
        FieldNode(name="Capture Length", value=f"{frame_len} bytes ({bits} bits)"),
        FieldNode(name="[Frame is marked", value="False]"),
        FieldNode(name="[Frame is ignored", value="False]"),
        FieldNode(name="[Protocols in frame", value=f"{layers}]"),
        FieldNode(name="[Coloring Rule Name", value=f"{protocol}]"),
        FieldNode(name="[Coloring Rule String", value=f"{protocol.lower()}]"),
    ]
    return node


def _ethernet_node(src_mac: str, dst_mac: str) -> FieldNode:
    node = FieldNode(
        name="Ethernet II",
        value=f"Src: {_mac_label(src_mac)}, Dst: {_mac_label(dst_mac)}",
        start=0,
        length=14,
    )
    node.children = [
        FieldNode(name="Destination", value=_mac_label(dst_mac), start=0, length=6),
        FieldNode(name="Source", value=_mac_label(src_mac), start=6, length=6),
        FieldNode(name="Type", value="IPv4 (0x0800)", start=12, length=2),
    ]
    return node


def _ipv4_node(src_ip: str, dst_ip: str, proto: int, total_length: int, checksum: int, base: int) -> FieldNode:
    proto_name = "TCP (6)" if proto == 6 else "UDP (17)"
    node = FieldNode(
        name="Internet Protocol Version 4",
        value=f"Src: {src_ip}, Dst: {dst_ip}",
        start=base,
        length=20,
    )
    node.children = [
        FieldNode(name="0100 .... = Version", value="4", start=base, length=1),
        FieldNode(name=".... 0101 = Header Length", value="20 bytes (5)", start=base, length=1),
        FieldNode(name="Differentiated Services Field", value="0x00 (Not ECN-Capable Transport)", start=base + 1, length=1),
        FieldNode(name="Total Length", value=str(total_length), start=base + 2, length=2),
        FieldNode(name="Identification", value="0x0000 (0)", start=base + 4, length=2),
        FieldNode(name="Flags", value="0x40, Don't fragment", start=base + 6, length=2),
        FieldNode(name="Fragment offset", value="0", start=base + 6, length=2),
        FieldNode(name="Time to live", value="64", start=base + 8, length=1),
        FieldNode(name="Protocol", value=proto_name, start=base + 9, length=1),
        FieldNode(name="Header checksum", value=f"0x{checksum:04x} [validation disabled]", start=base + 10, length=2),
        FieldNode(name="Source Address", value=src_ip, start=base + 12, length=4),
        FieldNode(name="Destination Address", value=dst_ip, start=base + 14, length=4),
    ]
    return node


def _tcp_node(
    sport: int,
    dport: int,
    seq: int,
    ack: int,
    flags: str,
    window: int,
    checksum: int,
    payload_len: int,
    base: int,
) -> FieldNode:
    flags_byte = _tcp_flags_byte(flags)
    names = [label for bit, label in TCP_FLAG_LABELS if flags_byte >> bit & 1]
    node = FieldNode(
        name="Transmission Control Protocol",
        value=f"Src Port: {sport}, Dst Port: {dport}, Seq: {seq}, Ack: {ack}, Len: {payload_len}",
        start=base,
        length=20 + payload_len,
    )
    flags_node = FieldNode(
        name="Flags",
        value=f"0x{flags_byte:03x} ({', '.join(names)})" if names else f"0x{flags_byte:03x}",
        start=base + 12,
        length=2,
    )
    flags_node.children = [
        FieldNode(
            name=_flag_bit_str(flags_byte, bit),
            value=f"{label}: {'Set' if flags_byte >> bit & 1 else 'Not set'}",
        )
        for bit, label in TCP_FLAG_LABELS
    ]
    node.children = [
        FieldNode(name="Source Port", value=str(sport), start=base, length=2),
        FieldNode(name="Destination Port", value=str(dport), start=base + 2, length=2),
        FieldNode(name="[Stream index", value="0]"),
        FieldNode(name="[TCP Segment Len", value=f"{payload_len}]"),
        FieldNode(name="Sequence Number", value=str(seq), start=base + 4, length=4),
        FieldNode(name="Acknowledgment Number", value=str(ack), start=base + 8, length=4),
        FieldNode(name="0101 .... = Header Length", value="20 bytes (5)", start=base + 12, length=1),
        flags_node,
        FieldNode(name="Window", value=str(window), start=base + 14, length=2),
        FieldNode(name="Checksum", value=f"0x{checksum:04x} [unverified]", start=base + 16, length=2),
        FieldNode(name="Urgent Pointer", value="0", start=base + 18, length=2),
    ]
    return node


def _udp_node(sport: int, dport: int, checksum: int, payload_len: int, base: int) -> FieldNode:
    node = FieldNode(
        name="User Datagram Protocol",
        value=f"Source Port: {sport}, Destination Port: {dport}",
        start=base,
        length=8 + payload_len,
    )
    node.children = [
        FieldNode(name="Source Port", value=str(sport), start=base, length=2),
        FieldNode(name="Destination Port", value=str(dport), start=base + 2, length=2),
        FieldNode(name="Length", value=str(8 + payload_len), start=base + 4, length=2),
        FieldNode(name="Checksum", value=f"0x{checksum:04x} [unverified]", start=base + 6, length=2),
    ]
    return node


def _http_node(payload: bytes, base: int) -> FieldNode:
    text = payload.decode("utf-8", errors="replace")
    lines = text.split("\r\n")
    node = FieldNode(
        name="Hypertext Transfer Protocol",
        value=lines[0] if lines else "",
        start=base,
        length=len(payload),
    )
    offset = base
    for line in lines:
        size = len(line.encode("utf-8", errors="replace"))
        if line:
            node.children.append(FieldNode(name=line, value="", start=offset, length=size))
        offset += size + 2
    return node


def _data_node(payload: bytes, base: int) -> FieldNode:
    node = FieldNode(name="Data", value=f"{len(payload)} bytes", start=base, length=len(payload))
    preview = payload[:160].decode("utf-8", errors="replace")
    if preview.strip():
        node.children = [FieldNode(name=line, value="") for line in preview.split("\r\n") if line][:12]
    return node


def _dns_node(payload: bytes, base: int, response: bool) -> FieldNode:
    tid, flags = struct.unpack("!HH", payload[:4])
    node = FieldNode(
        name="Domain Name System" + (" (response)" if response else " (query)"),
        value=f"{'Standard query response' if response else 'Standard query'} 0x{tid:04x}",
        start=base,
        length=len(payload),
    )
    node.children = [
        FieldNode(name="Transaction ID", value=f"0x{tid:04x}", start=base, length=2),
        FieldNode(
            name="Flags",
            value=f"0x{flags:04x} {'Standard query response' if response else 'Standard query'}",
            start=base + 2,
            length=2,
        ),
        FieldNode(name="Questions", value=str(struct.unpack("!H", payload[4:6])[0]), start=base + 4, length=2),
        FieldNode(name="Answer RRs", value=str(struct.unpack("!H", payload[6:8])[0]), start=base + 6, length=2),
        FieldNode(name="Authority RRs", value="0", start=base + 8, length=2),
        FieldNode(name="Additional RRs", value="0", start=base + 10, length=2),
        FieldNode(
            name="Queries",
            value="cyberrange.local: type A, class IN",
            start=base + 12,
            length=len(payload) - 12,
        ),
    ]
    if response:
        node.children.append(
            FieldNode(
                name="Answers",
                value="cyberrange.local: type A, class IN, addr 10.0.0.5",
                start=base + 12,
                length=len(payload) - 12,
            )
        )
    return node


# --------------------------------------------------------------------------- #
# 组装单条报文
# --------------------------------------------------------------------------- #
def _make_packet(
    no: int,
    t: float,
    src_ip: str,
    dst_ip: str,
    src_port: int | None,
    dst_port: int | None,
    protocol: str,
    payload: bytes,
    info: str,
    *,
    l4: str = "TCP",
    tcp_flags: str = "ACK",
    seq: int = 0,
    ack: int = 0,
    window: int = 64240,
    app: str = "auto",
    prev_time: float = 0.0,
) -> PacketOut:
    client_to_server = src_ip == CLIENT_IP
    src_mac, dst_mac = (CLIENT_MAC, SERVER_MAC) if client_to_server else (SERVER_MAC, CLIENT_MAC)

    sport = src_port or 0
    dport = dst_port or 0
    if l4 == "UDP":
        segment, l4_checksum = _build_udp(src_ip, dst_ip, sport, dport, payload)
    else:
        segment, l4_checksum = _build_tcp(src_ip, dst_ip, sport, dport, seq, ack, tcp_flags, window, payload)
    l4_len = len(segment) - len(payload)

    ip_datagram, ip_checksum = _build_ipv4(src_ip, dst_ip, _IP_PROTO[l4], segment)
    frame = _build_ethernet(src_mac, dst_mac) + ip_datagram

    ip_base = 14
    l4_base = ip_base + 20
    payload_base = l4_base + l4_len

    kind = app
    if kind == "auto":
        kind = {"http": "http", "dns": "dns_query"}.get(protocol.lower(), "none")
        if kind == "none" and payload and payload[:4] in (b"GET ", b"POST", b"HTTP"):
            kind = "http"

    layers = "eth:ethertype:ip:" + l4.lower()
    if kind in ("http",):
        layers += ":http"
    elif kind.startswith("dns"):
        layers += ":dns"
    elif kind == "data":
        layers += ":data"

    fields = [
        _frame_node(no, t, prev_time, len(frame), protocol, layers),
        _ethernet_node(src_mac, dst_mac),
        _ipv4_node(src_ip, dst_ip, _IP_PROTO[l4], 20 + len(segment), ip_checksum, ip_base),
    ]
    if l4 == "UDP":
        fields.append(_udp_node(sport, dport, l4_checksum, len(payload), l4_base))
    else:
        fields.append(_tcp_node(sport, dport, seq, ack, tcp_flags, window, l4_checksum, len(payload), l4_base))

    if payload:
        if kind == "http":
            fields.append(_http_node(payload, payload_base))
        elif kind == "dns_query":
            fields.append(_dns_node(payload, payload_base, response=False))
        elif kind == "dns_response":
            fields.append(_dns_node(payload, payload_base, response=True))
        else:
            fields.append(_data_node(payload, payload_base))

    return PacketOut(
        no=no,
        time=round(t, 6),
        src_ip=src_ip,
        dst_ip=dst_ip,
        src_port=src_port,
        dst_port=dst_port,
        protocol=protocol,
        length=len(frame),
        info=info,
        fields=fields,
        hex_lines=_hex_lines(frame),
    )


# --------------------------------------------------------------------------- #
# 路由
# --------------------------------------------------------------------------- #
@router.get("/capture", response_model=list[PacketOut])
def get_capture(_user: User | None = Depends(get_current_user_optional)):
    """返回一组模拟通信报文：TCP 握手 → HTTP 请求/响应 → 上传 → 下载 → 挥手。"""
    packets: list[PacketOut] = []
    state = {"t": 0.0, "prev": 0.0}

    def add(**kwargs) -> None:
        packets.append(
            _make_packet(no=len(packets) + 1, t=state["t"], prev_time=state["prev"], **kwargs)
        )
        state["prev"] = state["t"]

    add(src_ip=CLIENT_IP, dst_ip=SERVER_IP, src_port=51234, dst_port=80, protocol="TCP",
        payload=b"", info="51234 → 80 [SYN] Seq=0 Win=64240", tcp_flags="SYN", seq=0)
    state["t"] += 0.001
    add(src_ip=SERVER_IP, dst_ip=CLIENT_IP, src_port=80, dst_port=51234, protocol="TCP",
        payload=b"", info="80 → 51234 [SYN, ACK] Seq=0 Ack=1 Win=65535", tcp_flags="SYN, ACK", seq=0, ack=1, window=65535)
    state["t"] += 0.001
    add(src_ip=CLIENT_IP, dst_ip=SERVER_IP, src_port=51234, dst_port=80, protocol="TCP",
        payload=b"", info="51234 → 80 [ACK] Seq=1 Ack=1 Win=64240", tcp_flags="ACK", seq=1, ack=1)

    state["t"] += 0.002
    http_get = (
        "GET /api/challenges HTTP/1.1\r\n"
        "Host: cyberrange.local\r\n"
        "Authorization: Bearer eyJhbGciOi...\r\n"
        "Accept: application/json\r\n"
        "Connection: keep-alive\r\n"
        "\r\n"
    ).encode()
    add(src_ip=CLIENT_IP, dst_ip=SERVER_IP, src_port=51234, dst_port=80, protocol="HTTP",
        payload=http_get, info="GET /api/challenges HTTP/1.1", tcp_flags="PSH, ACK", seq=1, ack=1)

    state["t"] += 0.015
    http_resp = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: 256\r\n"
        "\r\n"
        '{"total":13,"challenges":[{"id":1,"title":"stack overflow","points":300}]}'
    ).encode()
    add(src_ip=SERVER_IP, dst_ip=CLIENT_IP, src_port=80, dst_port=51234, protocol="HTTP",
        payload=http_resp, info="HTTP/1.1 200 OK  (application/json)", tcp_flags="PSH, ACK",
        seq=1, ack=len(http_get) + 1, window=65535)

    state["t"] += 0.05
    http_post = (
        "POST /api/admin/attachments HTTP/1.1\r\n"
        "Host: cyberrange.local\r\n"
        "Content-Type: multipart/form-data; boundary=----WebKitFormBoundary\r\n"
        "Content-Length: 8192\r\n"
        "\r\n"
        "------WebKitFormBoundary\r\n"
        'Content-Disposition: form-data; name="file"; filename="stack0.zip"\r\n'
        "Content-Type: application/zip\r\n"
        "\r\n"
        "PK\x03\x04" + "\x00" * 40 + "stack0 binary data..."
    ).encode()
    add(src_ip=CLIENT_IP, dst_ip=SERVER_IP, src_port=51235, dst_port=80, protocol="HTTP",
        payload=http_post, info="POST /api/admin/attachments (upload stack0.zip)",
        tcp_flags="PSH, ACK", seq=1, ack=len(http_resp) + 1)

    state["t"] += 0.020
    upload_resp = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/json\r\n"
        "\r\n"
        '{"filename":"a1b2c3d4.zip","size":8192}'
    ).encode()
    add(src_ip=SERVER_IP, dst_ip=CLIENT_IP, src_port=80, dst_port=51235, protocol="HTTP",
        payload=upload_resp, info="HTTP/1.1 200 OK  upload success", tcp_flags="PSH, ACK",
        seq=1, ack=len(http_post) + 1, window=65535)

    state["t"] += 0.08
    http_dl = (
        "GET /uploads/a1b2c3d4.zip HTTP/1.1\r\n"
        "Host: cyberrange.local\r\n"
        "Range: bytes=0-\r\n"
        "\r\n"
    ).encode()
    add(src_ip=CLIENT_IP, dst_ip=SERVER_IP, src_port=51236, dst_port=80, protocol="HTTP",
        payload=http_dl, info="GET /uploads/a1b2c3d4.zip (download)", tcp_flags="PSH, ACK",
        seq=1, ack=len(upload_resp) + 1)

    state["t"] += 0.030
    dl_resp = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/zip\r\n"
        "Content-Length: 8192\r\n"
        "\r\n"
        "PK\x03\x04" + "\x00" * 80 + "ELF binary challenge data..."
    ).encode()
    add(src_ip=SERVER_IP, dst_ip=CLIENT_IP, src_port=80, dst_port=51236, protocol="HTTP",
        payload=dl_resp, info="HTTP/1.1 200 OK  (application/zip, 8192 bytes)", tcp_flags="PSH, ACK",
        seq=1, ack=len(http_dl) + 1, window=65535)

    state["t"] += 0.001
    dns_qname = b"\x07cyberrange\x05local\x00"
    dns_query = struct.pack("!HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0) + dns_qname + struct.pack("!HH", 1, 1)
    add(src_ip=CLIENT_IP, dst_ip=SERVER_IP, src_port=54321, dst_port=53, protocol="DNS",
        payload=dns_query, info="Standard query 0x1234 A cyberrange.local", l4="UDP", app="dns_query")

    state["t"] += 0.002
    dns_resp = (
        struct.pack("!HHHHHH", 0x1234, 0x8180, 1, 1, 0, 0)
        + dns_qname
        + struct.pack("!HH", 1, 1)
        + b"\xc0\x0c"
        + struct.pack("!HHIH", 1, 1, 60, 4)
        + _ip_bytes(SERVER_IP)
    )
    add(src_ip=SERVER_IP, dst_ip=CLIENT_IP, src_port=53, dst_port=54321, protocol="DNS",
        payload=dns_resp, info="Standard query response 0x1234 A 10.0.0.5", l4="UDP", app="dns_response")

    state["t"] += 0.1
    add(src_ip=CLIENT_IP, dst_ip=SERVER_IP, src_port=51234, dst_port=80, protocol="TCP",
        payload=b"", info="51234 → 80 [FIN, ACK] Seq=1000 Ack=500 Win=64240", tcp_flags="FIN, ACK", seq=1000, ack=500)
    state["t"] += 0.001
    add(src_ip=SERVER_IP, dst_ip=CLIENT_IP, src_port=80, dst_port=51234, protocol="TCP",
        payload=b"", info="80 → 51234 [ACK] Seq=500 Ack=1001 Win=65535", tcp_flags="ACK", seq=500, ack=1001, window=65535)
    state["t"] += 0.001
    add(src_ip=SERVER_IP, dst_ip=CLIENT_IP, src_port=80, dst_port=51234, protocol="TCP",
        payload=b"", info="80 → 51234 [FIN, ACK] Seq=500 Ack=1001 Win=65535", tcp_flags="FIN, ACK", seq=500, ack=1001, window=65535)
    state["t"] += 0.001
    add(src_ip=CLIENT_IP, dst_ip=SERVER_IP, src_port=51234, dst_port=80, protocol="TCP",
        payload=b"", info="51234 → 80 [ACK] Seq=1001 Ack=501 Win=64240", tcp_flags="ACK", seq=1001, ack=501)

    return packets


@router.post("/upload-capture", response_model=list[PacketOut])
async def upload_capture(
    file: UploadFile = File(...),
    _user: User | None = Depends(get_current_user_optional),
):
    """用户上传文件，返回模拟这次上传产生的完整报文流。"""
    port = 54321
    packets: list[PacketOut] = []
    state = {"t": 0.0, "prev": 0.0}

    filename = file.filename or "unknown.bin"
    content_type = file.content_type or "application/octet-stream"
    file_data = await file.read()
    file_size = len(file_data)

    def add(**kwargs) -> None:
        packets.append(
            _make_packet(no=len(packets) + 1, t=state["t"], prev_time=state["prev"], **kwargs)
        )
        state["prev"] = state["t"]

    # 1. TCP 三次握手
    add(src_ip=CLIENT_IP, dst_ip=SERVER_IP, src_port=port, dst_port=80, protocol="TCP",
        payload=b"", info=f"{port} → 80 [SYN] Seq=0 Win=64240", tcp_flags="SYN", seq=0)
    state["t"] += 0.001
    add(src_ip=SERVER_IP, dst_ip=CLIENT_IP, src_port=80, dst_port=port, protocol="TCP",
        payload=b"", info=f"80 → {port} [SYN, ACK] Seq=0 Ack=1 Win=65535", tcp_flags="SYN, ACK", seq=0, ack=1, window=65535)
    state["t"] += 0.001
    add(src_ip=CLIENT_IP, dst_ip=SERVER_IP, src_port=port, dst_port=80, protocol="TCP",
        payload=b"", info=f"{port} → 80 [ACK] Seq=1 Ack=1 Win=64240", tcp_flags="ACK", seq=1, ack=1)

    # 2. HTTP POST 请求头（multipart 开头）
    state["t"] += 0.002
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    post_header = (
        f"POST /api/upload HTTP/1.1\r\n"
        f"Host: cyberrange.local\r\n"
        f"User-Agent: CyberRange/1.0\r\n"
        f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
        f"Content-Length: {file_size + 200}\r\n"
        f"Connection: keep-alive\r\n"
        f"\r\n"
        f"------{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n"
        f"\r\n"
    ).encode()
    add(src_ip=CLIENT_IP, dst_ip=SERVER_IP, src_port=port, dst_port=80, protocol="HTTP",
        payload=post_header, info=f"POST /api/upload (upload {filename}, {file_size} bytes)",
        tcp_flags="PSH, ACK", seq=1, ack=1)

    # 3. 文件数据按真实 MSS(1460) 分块传输
    seq = 1 + len(post_header)
    offset = 0
    chunk_size = 1460
    truncated = False
    while offset < file_size:
        if len(packets) >= MAX_SEGMENTS:
            truncated = True
            break
        chunk = file_data[offset : offset + chunk_size]
        state["t"] += 0.001 + (len(chunk) / max(file_size, 1)) * 0.05
        add(src_ip=CLIENT_IP, dst_ip=SERVER_IP, src_port=port, dst_port=80, protocol="HTTP",
            payload=chunk,
            info=f"[TCP segment of a reassembled PDU]  {len(chunk)} bytes (offset {offset}/{file_size})",
            tcp_flags="PSH, ACK", seq=seq, ack=1, app="data")
        offset += chunk_size
        seq += len(chunk)

    # 4. multipart 结束标记
    state["t"] += 0.002
    end_boundary = f"\r\n------{boundary}--\r\n".encode()
    add(src_ip=CLIENT_IP, dst_ip=SERVER_IP, src_port=port, dst_port=80, protocol="HTTP",
        payload=end_boundary, info="End of multipart/form-data", tcp_flags="PSH, ACK", seq=seq, ack=1)
    seq += len(end_boundary)

    # 5. 服务器响应
    state["t"] += 0.015
    resp_body = f'{{"success":true,"filename":"{filename}","size":{file_size},"message":"Upload completed"}}'.encode()
    http_resp = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: " + str(len(resp_body)).encode() + b"\r\n"
        b"\r\n" + resp_body
    )
    resp_info = "HTTP/1.1 200 OK  Upload completed"
    if truncated:
        resp_info += f"  [capture truncated at {MAX_SEGMENTS} packets]"
    add(src_ip=SERVER_IP, dst_ip=CLIENT_IP, src_port=80, dst_port=port, protocol="HTTP",
        payload=http_resp, info=resp_info, tcp_flags="PSH, ACK",
        seq=1, ack=seq + 1, window=65535)

    # 6. TCP 四次挥手
    state["t"] += 0.05
    add(src_ip=CLIENT_IP, dst_ip=SERVER_IP, src_port=port, dst_port=80, protocol="TCP",
        payload=b"", info=f"{port} → 80 [FIN, ACK] Seq={seq} Ack={len(http_resp) + 1} Win=64240",
        tcp_flags="FIN, ACK", seq=seq, ack=len(http_resp) + 1)
    state["t"] += 0.001
    add(src_ip=SERVER_IP, dst_ip=CLIENT_IP, src_port=80, dst_port=port, protocol="TCP",
        payload=b"", info=f"80 → {port} [ACK] Seq={len(http_resp) + 1} Ack={seq + 1} Win=65535",
        tcp_flags="ACK", seq=len(http_resp) + 1, ack=seq + 1, window=65535)
    state["t"] += 0.001
    add(src_ip=SERVER_IP, dst_ip=CLIENT_IP, src_port=80, dst_port=port, protocol="TCP",
        payload=b"", info=f"80 → {port} [FIN, ACK] Seq={len(http_resp) + 1} Ack={seq + 1} Win=65535",
        tcp_flags="FIN, ACK", seq=len(http_resp) + 1, ack=seq + 1, window=65535)
    state["t"] += 0.001
    add(src_ip=CLIENT_IP, dst_ip=SERVER_IP, src_port=port, dst_port=80, protocol="TCP",
        payload=b"", info=f"{port} → 80 [ACK] Seq={seq + 1} Ack={len(http_resp) + 2} Win=64240",
        tcp_flags="ACK", seq=seq + 1, ack=len(http_resp) + 2)

    return packets
