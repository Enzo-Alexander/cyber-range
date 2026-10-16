"""模拟流量分析：生成用户与服务器之间的通信报文序列。"""
import os

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel

from ..dependencies import get_current_user_optional
from ..models import User

router = APIRouter(prefix="/traffic", tags=["traffic"])


class PacketField(BaseModel):
    name: str
    value: str
    detail: str = ""


class PacketDetail(BaseModel):
    layers: list[PacketField]  # 展开后的协议字段树


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
    detail: PacketDetail
    hex_dump: str


def _hex_dump(data: bytes) -> str:
    lines = []
    for i in range(0, len(data), 16):
        chunk = data[i : i + 16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{i:04x}  {hex_part:<47s}  {ascii_part}")
    return "\n".join(lines)


def _make_packet(
    no: int,
    time: float,
    src_ip: str,
    dst_ip: str,
    src_port: int | None,
    dst_port: int | None,
    protocol: str,
    payload: bytes,
    info: str,
    eth_type: str = "IPv4",
    ttl: int = 64,
    tcp_flags: str = "",
) -> PacketOut:
    # 简化：以太网头 14 + IP头 20 + TCP头 20
    total_len = 14 + 20 + 20 + len(payload) if dst_port else 14 + 20 + len(payload)

    layers = []
    layers.append(PacketField(name="Ethernet II", value=f"Src: 00:1a:2b:3c:4d:5e, Dst: 52:54:00:12:34:56", detail="以太网帧头"))
    layers.append(PacketField(name="Internet Protocol Version 4", value=f"Src: {src_ip}, Dst: {dst_ip}", detail=f"TTL={ttl}, Proto={protocol}"))
    if src_port and dst_port:
        if protocol == "TCP":
            layers.append(PacketField(
                name="Transmission Control Protocol",
                value=f"Src Port: {src_port}, Dst Port: {dst_port}, Len: {len(payload)}",
                detail=f"Flags: {tcp_flags or 'ACK'}",
            ))
        elif protocol == "UDP":
            layers.append(PacketField(
                name="User Datagram Protocol",
                value=f"Src Port: {src_port}, Dst Port: {dst_port}, Len: {len(payload)}",
            ))

    # 应用层
    if payload:
        try:
            text = payload.decode("utf-8", errors="replace")
            first_line = text.split("\r\n")[0] if "\r\n" in text else text[:80]
            layers.append(PacketField(name="Application Data", value=first_line, detail=text[:200]))
        except Exception:
            layers.append(PacketField(name="Application Data", value=f"{len(payload)} bytes binary data"))

    return PacketOut(
        no=no,
        time=round(time, 6),
        src_ip=src_ip,
        dst_ip=dst_ip,
        src_port=src_port,
        dst_port=dst_port,
        protocol=protocol,
        length=total_len,
        info=info,
        detail=PacketDetail(layers=layers),
        hex_dump=_hex_dump(payload),
    )


@router.get("/capture", response_model=list[PacketOut])
def get_capture(_user: User | None = Depends(get_current_user_optional)):
    """返回一组模拟通信报文：TCP握手 → HTTP请求 → 上传 → 下载 → 挥手。"""
    client = "192.168.1.100"
    server = "10.0.0.5"
    packets: list[PacketOut] = []
    t = 0.0

    # 1. TCP 三次握手
    packets.append(_make_packet(1, t, client, server, 51234, 80, "TCP", b"", "51234 → 80 [SYN] Seq=0 Win=64240", tcp_flags="SYN"))
    t += 0.001
    packets.append(_make_packet(2, t, server, client, 80, 51234, "TCP", b"", "80 → 51234 [SYN, ACK] Seq=0 Ack=1 Win=65535", tcp_flags="SYN, ACK"))
    t += 0.001
    packets.append(_make_packet(3, t, client, server, 51234, 80, "TCP", b"", "51234 → 80 [ACK] Seq=1 Ack=1 Win=64240", tcp_flags="ACK"))

    # 2. HTTP GET 请求
    t += 0.002
    http_get = (
        "GET /api/challenges HTTP/1.1\r\n"
        "Host: cyberrange.local\r\n"
        "Authorization: Bearer eyJhbGciOi...\r\n"
        "Accept: application/json\r\n"
        "Connection: keep-alive\r\n"
        "\r\n"
    ).encode()
    packets.append(_make_packet(4, t, client, server, 51234, 80, "HTTP", http_get, "GET /api/challenges HTTP/1.1"))

    # 3. HTTP 响应
    t += 0.015
    http_resp = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: 256\r\n"
        "\r\n"
        '{"total":13,"challenges":[{"id":1,"title":"栈溢出入门","points":300}]}'
    ).encode()
    packets.append(_make_packet(5, t, server, client, 80, 51234, "HTTP", http_resp, "HTTP/1.1 200 OK  (application/json)"))

    # 4. 文件上传 POST
    t += 0.05
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
        "PK\\x03\\x04" + "\\x00" * 50 + "stack0 binary data..."
    ).encode()
    packets.append(_make_packet(6, t, client, server, 51235, 80, "HTTP", http_post, "POST /api/admin/attachments (upload stack0.zip)"))

    # 5. 上传响应
    t += 0.020
    upload_resp = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/json\r\n"
        "\r\n"
        '{"filename":"a1b2c3d4.zip","size":8192}'
    ).encode()
    packets.append(_make_packet(7, t, server, client, 80, 51235, "HTTP", upload_resp, "HTTP/1.1 200 OK  upload success"))

    # 6. 文件下载
    t += 0.08
    http_dl = (
        "GET /uploads/a1b2c3d4.zip HTTP/1.1\r\n"
        "Host: cyberrange.local\r\n"
        "Range: bytes=0-\r\n"
        "\r\n"
    ).encode()
    packets.append(_make_packet(8, t, client, server, 51236, 80, "HTTP", http_dl, "GET /uploads/a1b2c3d4.zip (download)"))

    t += 0.030
    dl_resp = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/zip\r\n"
        "Content-Length: 8192\r\n"
        "\r\n"
        "PK\\x03\\x04" + "\\x00" * 80 + "ELF binary challenge data..."
    ).encode()
    packets.append(_make_packet(9, t, server, client, 80, 51236, "HTTP", dl_resp, "HTTP/1.1 200 OK  (application/zip, 8192 bytes)"))

    # 7. DNS 查询（UDP）
    t += 0.001
    dns_query = b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07cyberrange\x05local\x00\x00\x01\x00\x01"
    packets.append(_make_packet(10, t, client, server, 54321, 53, "DNS", dns_query, "Standard query 0x1234 A cyberrange.local"))

    t += 0.002
    dns_resp = b"\x12\x34\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00\x07cyberrange\x05local\x00\x00\x01\x00\x01\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04\x0a\x00\x00\x05"
    packets.append(_make_packet(11, t, server, client, 53, 54321, "DNS", dns_resp, "Standard query response 0x1234 A 10.0.0.5"))

    # 8. TCP 四次挥手
    t += 0.1
    packets.append(_make_packet(12, t, client, server, 51234, 80, "TCP", b"", "51234 → 80 [FIN, ACK] Seq=1000 Ack=500 Win=64240", tcp_flags="FIN, ACK"))
    t += 0.001
    packets.append(_make_packet(13, t, server, client, 80, 51234, "TCP", b"", "80 → 51234 [ACK] Seq=500 Ack=1001 Win=65535", tcp_flags="ACK"))
    t += 0.001
    packets.append(_make_packet(14, t, server, client, 80, 51234, "TCP", b"", "80 → 51234 [FIN, ACK] Seq=500 Ack=1001 Win=65535", tcp_flags="FIN, ACK"))
    t += 0.001
    packets.append(_make_packet(15, t, client, server, 51234, 80, "TCP", b"", "51234 → 80 [ACK] Seq=1001 Ack=501 Win=64240", tcp_flags="ACK"))

    return packets


@router.post("/upload-capture", response_model=list[PacketOut])
async def upload_capture(
    file: UploadFile = File(...),
    _user: User | None = Depends(get_current_user_optional),
):
    """用户上传文件，返回模拟这次上传产生的完整报文流。"""
    client = "192.168.1.100"
    server = "10.0.0.5"
    port = 54321
    packets: list[PacketOut] = []
    t = 0.0

    filename = file.filename or "unknown.bin"
    content_type = file.content_type or "application/octet-stream"
    file_data = await file.read()
    file_size = len(file_data)

    # 1. TCP 三次握手
    packets.append(_make_packet(1, t, client, server, port, 80, "TCP", b"", f"{port} → 80 [SYN] Seq=0 Win=64240", tcp_flags="SYN"))
    t += 0.001
    packets.append(_make_packet(2, t, server, client, 80, port, "TCP", b"", f"80 → {port} [SYN, ACK] Seq=0 Ack=1 Win=65535", tcp_flags="SYN, ACK"))
    t += 0.001
    packets.append(_make_packet(3, t, client, server, port, 80, "TCP", b"", f"{port} → 80 [ACK] Seq=1 Ack=1 Win=64240", tcp_flags="ACK"))

    # 2. HTTP POST 请求头（multipart 开头）
    t += 0.002
    post_header = (
        f"POST /api/upload HTTP/1.1\r\n"
        f"Host: cyberrange.local\r\n"
        f"User-Agent: CyberRange/1.0\r\n"
        f"Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW\r\n"
        f"Content-Length: {file_size + 200}\r\n"
        f"Connection: keep-alive\r\n"
        f"\r\n"
        f"------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n"
        f"\r\n"
    ).encode()
    packets.append(_make_packet(4, t, client, server, port, 80, "HTTP", post_header, f"POST /api/upload (upload {filename}, {file_size} bytes)"))

    # 3. 文件数据（分块传输，按真实 TCP MSS 1460 字节一块）
    seq = 5
    offset = 0
    chunk_size = 1460
    while offset < file_size:
        chunk = file_data[offset : offset + chunk_size]
        t += 0.001 + (len(chunk) / file_size) * 0.05
        packets.append(_make_packet(
            seq, t, client, server, port, 80, "TCP",
            chunk,
            f"[TCP Segment] Data: {len(chunk)} bytes (offset {offset}/{file_size})",
            tcp_flags="ACK",
        ))
        offset += chunk_size
        seq += 1

    # 4. multipart 结束标记
    t += 0.002
    end_boundary = b"\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n"
    packets.append(_make_packet(seq, t, client, server, port, 80, "HTTP", end_boundary, "End of multipart/form-data"))
    seq += 1

    # 5. 服务器响应
    t += 0.015
    resp_body = f'{{"success":true,"filename":"{filename}","size":{file_size},"message":"Upload completed"}}'.encode()
    http_resp = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: " + str(len(resp_body)).encode() + b"\r\n"
        b"\r\n" + resp_body
    )
    packets.append(_make_packet(seq, t, server, client, 80, port, "HTTP", http_resp, "HTTP/1.1 200 OK  Upload completed"))
    seq += 1

    # 6. TCP 四次挥手
    t += 0.05
    packets.append(_make_packet(seq, t, client, server, port, 80, "TCP", b"", f"{port} → 80 [FIN, ACK] Seq=... Ack=... Win=64240", tcp_flags="FIN, ACK"))
    seq += 1
    t += 0.001
    packets.append(_make_packet(seq, t, server, client, 80, port, "TCP", b"", f"80 → {port} [ACK] Seq=... Ack=... Win=65535", tcp_flags="ACK"))
    seq += 1
    t += 0.001
    packets.append(_make_packet(seq, t, server, client, 80, port, "TCP", b"", f"80 → {port} [FIN, ACK] Seq=... Ack=... Win=65535", tcp_flags="FIN, ACK"))
    seq += 1
    t += 0.001
    packets.append(_make_packet(seq, t, client, server, port, 80, "TCP", b"", f"{port} → 80 [ACK] Seq=... Ack=... Win=64240", tcp_flags="ACK"))

    return packets
