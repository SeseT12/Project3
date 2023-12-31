# Contributor(s): cobreath, sregitz
from enum import IntEnum


class TLVType(IntEnum):
    INTEREST_PACKET = int(0X05)
    DATA_PACKET = int(0x06)
    NAME = int(0X07)
    NAME_COMPONENT = int(0X08)
    ID = int(0x01)
    CONTENT = int(0x15)
    ADJ_LIST = int(0x03)
    KEY_PACKET = int(0X0F)
    KEY_REQUEST_PACKET = int(0X0E)
    ACK_PACKET = int(0X0D)
    SIGNATURE = int(0X17)
    SOURCE = int(0X2E)
    FIB = int(0x04)
