# encoding=utf-8

import os
import base64
# import string
# import random
import hashlib
import time
import struct
import xml.etree.cElementTree as ET
import socket

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import (
    Cipher, algorithms, modes
)

WXBizMsgCrypt_OK = 0
WXBizMsgCrypt_ValidateSignature_Error = -40001
WXBizMsgCrypt_ParseXml_Error = -40002
WXBizMsgCrypt_ComputeSignature_Error = -40003
WXBizMsgCrypt_IllegalAesKey = -40004
WXBizMsgCrypt_ValidateAppidOrCorpid_Error = -40005
WXBizMsgCrypt_EncryptAES_Error = -40006
WXBizMsgCrypt_DecryptAES_Error = -40007
WXBizMsgCrypt_IllegalBuffer = -40008
WXBizMsgCrypt_EncodeBase64_Error = -40009
WXBizMsgCrypt_DecodeBase64_Error = -40010
WXBizMsgCrypt_GenReturnXml_Error = -40011


class FormatException(Exception):
    pass


def throw_exception(message, exception_class=FormatException):
    """my define raise exception function"""
    raise exception_class(message)


class SHA1:
    """计算公众平台的消息签名接口"""

    def getSHA1(self, token, timestamp, nonce, encrypt):
        """用SHA1算法生成安全签名
        @param token:  票据
        @param timestamp: 时间戳
        @param encrypt: 密文
        @param nonce: 随机字符串
        @return: 安全签名
        """
        try:
            sortlist = [token, timestamp, nonce, encrypt]
            sortlist.sort()
            sha = hashlib.sha1()
            sha.update("".join(sortlist))
            return WXBizMsgCrypt_OK, sha.hexdigest()
        except Exception:
            return WXBizMsgCrypt_ComputeSignature_Error, None


class XMLParse:
    """提供提取消息格式中的密文及生成回复消息格式的接口"""
    AES_TEXT_RESPONSE_TEMPLATE = """<xml>
<Encrypt><![CDATA[%(msg_encrypt)s]]></Encrypt>
<MsgSignature><![CDATA[%(msg_signaturet)s]]></MsgSignature>
<TimeStamp>%(timestamp)s</TimeStamp>
<Nonce><![CDATA[%(nonce)s]]></Nonce>
</xml>"""

    def extract(self, xmltext):
        """提取出xml数据包中的加密消息
        @param xmltext: 待提取的xml字符串
        @return: 提取出的加密消息字符串
        """
        try:
            xml_tree = ET.fromstring(xmltext)
            encrypt = xml_tree.find("Encrypt")
            touser_name = xml_tree.find("ToUserName")
            if touser_name is not None:
                touser_name = touser_name.text
            return WXBizMsgCrypt_OK, encrypt.text, touser_name
        except Exception:
            return WXBizMsgCrypt_ParseXml_Error, None, None

    def generate(self, encrypt, signature, timestamp, nonce):
        """生成xml消息
        @param encrypt: 加密后的消息密文
        @param signature: 安全签名
        @param timestamp: 时间戳
        @param nonce: 随机字符串
        @return: 生成的xml字符串
        """
        resp_dict = {
            'msg_encrypt': encrypt,
            'msg_signaturet': signature,
            'timestamp': timestamp,
            'nonce': nonce,
            }
        resp_xml = self.AES_TEXT_RESPONSE_TEMPLATE % resp_dict
        return resp_xml


# class PKCS7Encoder():
#     """提供基于PKCS7算法的加解密接口"""
#     block_size = 32
# 
#     def encode(self, text):
#         """ 对需要加密的明文进行填充补位
#         @param text: 需要进行填充补位操作的明文
#         @return: 补齐明文字符串
#         """
#         text_length = len(text)
#         # 计算需要填充的位数
#         amount_to_pad = self.block_size - (text_length % self.block_size)
#         if amount_to_pad == 0:
#             amount_to_pad = self.block_size
#         # 获得补位所用的字符
#         pad = chr(amount_to_pad)
#         return text + pad * amount_to_pad
# 
#     def decode(self, decrypted):
#         """删除解密后明文的补位字符
#         @param decrypted: 解密后的明文
#         @return: 删除补位字符后的明文
#         """
#         pad = ord(decrypted[-1])
#         if pad < 1 or pad > 32:
#             pad = 0
#         return decrypted[:-pad]


class Prpcrypt(object):
    """提供接收和推送给公众平台消息的加解密接口"""

    def __init__(self, key):
        #self.key = base64.b64decode(key+"=")
        self.key = key
        # # 设置加解密模式为AES的CBC模式
        # self.mode = AES.MODE_CBC

    def encrypt(self, text, appid):
        """对明文进行加密
        @param text: 需要加密的明文
        @return: 加密得到的字符串
        """
        # 16位随机字符串添加到明文开头
        text = self.get_random_str() + struct.pack(
            "I", socket.htonl(len(text))) + text + appid
        # 加密
        encryptor = Cipher(
            algorithms.AES(self.key),
            modes.CBC(self.key[:16]),
            backend=default_backend()
        ).encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        try:
            ciphertext = encryptor.update(padder.update(text) + padder.finalize()) + encryptor.finalize()
            # 使用BASE64对加密后的字符串进行编码
            return WXBizMsgCrypt_OK, base64.b64encode(ciphertext)
        except Exception:
            return WXBizMsgCrypt_EncryptAES_Error, None

    def decrypt(self, text, appid):
        """对解密后的明文进行补位删除
        @param text: 密文
        @return: 删除填充补位后的明文
        """
        decryptor = Cipher(
            algorithms.AES(self.key),
            modes.CBC(self.key[:16]),
            backend=default_backend()
        ).decryptor()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        try:
            # 使用BASE64对密文进行解码，然后AES-CBC解密
            plain_text = unpadder.update(decryptor.update(base64.b64decode(text)) + decryptor.finalize()) + unpadder.finalize()
        except Exception:
            return WXBizMsgCrypt_DecryptAES_Error, None
        try:
            # 去除16位随机字符串
            content = plain_text[16:]
            xml_len = socket.ntohl(struct.unpack("I", content[:4])[0])
            xml_content = content[4:xml_len+4]
            from_appid = content[xml_len+4:]
        except Exception:
            return WXBizMsgCrypt_IllegalBuffer, None
        if from_appid != appid:
            return WXBizMsgCrypt_ValidateAppidOrCorpid_Error, None
        return 0, xml_content

    def get_random_str(self):
        """ 随机生成16位字符串
        @return: 16位字符串
        """
        # rule = string.ascii_letters + string.digits
        # s = random.sample(rule, 16)
        # return "".join(s)
        return os.urandom(16)


class WXBizMsgCrypt(object):
    def __init__(self, sToken, sEncodingAESKey, sCorpId):
        try:
            self.key = base64.b64decode(sEncodingAESKey+"=")
            assert len(self.key) == 32
        except:
            throw_exception("[error]: EncodingAESKey unvalid !",
                            FormatException)
           #return WXBizMsgCrypt_IllegalAesKey)
        self.m_sToken = sToken
        self.m_sCorpid = sCorpId

    def VerifyURL(self, sMsgSignature, sTimeStamp, sNonce, sEchoStr):
        sha1 = SHA1()
        ret, signature = sha1.getSHA1(self.m_sToken,
                                      sTimeStamp, sNonce, sEchoStr)
        if ret != 0:
            return ret, None
        if not signature == sMsgSignature:
            return WXBizMsgCrypt_ValidateSignature_Error, None
        pc = Prpcrypt(self.key)
        ret, sReplyEchoStr = pc.decrypt(sEchoStr, self.m_sCorpid)
        return ret, sReplyEchoStr

    def EncryptMsg(self, sReplyMsg, sNonce, timestamp=None):
        pc = Prpcrypt(self.key)
        ret, encrypt = pc.encrypt(sReplyMsg, self.m_sCorpid)
        if ret != 0:
            return ret, None
        if timestamp is None:
            timestamp = str(int(time.time()))
        # 生成安全签名
        sha1 = SHA1()
        ret, signature = sha1.getSHA1(self.m_sToken, timestamp,
                                      sNonce, encrypt)
        if ret != 0:
            return ret, None
        xmlParse = XMLParse()
        return ret, xmlParse.generate(encrypt, signature, timestamp, sNonce)

    def DecryptMsg(self, sPostData, sMsgSignature, sTimeStamp, sNonce):
        xmlParse = XMLParse()
        ret, encrypt, touser_name = xmlParse.extract(sPostData)
        if ret != 0:
            return ret, None
        sha1 = SHA1()
        ret, signature = sha1.getSHA1(self.m_sToken, sTimeStamp,
                                      sNonce, encrypt)
        if ret != 0:
            return ret, None
        if not signature == sMsgSignature:
            return WXBizMsgCrypt_ValidateSignature_Error, None
        pc = Prpcrypt(self.key)
        ret, xml_content = pc.decrypt(encrypt, self.m_sCorpid)
        return ret, xml_content
