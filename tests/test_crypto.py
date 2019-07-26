from __future__ import print_function

import os
import socket
import struct

from wechat.crypt import Prpcrypt


key = os.urandom(32)
text = sReplyMsg = b'hello'
appid = m_sCorpid = b'10001'

pc = Prpcrypt(key)

text = pc.get_random_str() + struct.pack("I", socket.htonl(len(text))) + text + appid
print(text)
content = text[16:]
print(content)
xml_len = socket.ntohl(struct.unpack("I", content[:4])[0])
print(xml_len)
xml_content = content[4:xml_len+4]
print(xml_content)
from_appid = content[xml_len+4:]
print(from_appid)

ret, encrypt = pc.encrypt(sReplyMsg, m_sCorpid)

ret, xml_content = pc.decrypt(encrypt, m_sCorpid)
print('decrypted:', xml_content)
