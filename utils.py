# utils.py

import socket

def get_local_ip():
    """获取本机局域网IP地址"""
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        if s:
            s.close()
    return ip

def mix_colors(color1_hex, color2_hex, weight1=0.8):
    """混合两种十六进制颜色"""
    try:
        r1, g1, b1 = int(color1_hex[1:3], 16), int(color1_hex[3:5], 16), int(color1_hex[5:7], 16)
        r2, g2, b2 = int(color2_hex[1:3], 16), int(color2_hex[3:5], 16), int(color2_hex[5:7], 16)
        weight2 = 1.0 - weight1
        r = int(r1 * weight1 + r2 * weight2)
        g = int(g1 * weight1 + g2 * weight2)
        b = int(b1 * weight1 + b2 * weight2)
        return f'#{r:02x}{g:02x}{b:02x}'
    except (ValueError, IndexError):
        # Fallback in case of invalid hex
        return color2_hex