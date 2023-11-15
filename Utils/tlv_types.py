from enum import IntEnum


class TLVType(IntEnum):
    INTEREST_PACKET = int(0X05)
    DATA_PACKET = int(0x06)
    NAME = int(0X07)
    NAME_COMPONENT = int(0X08)
    ID = int(0x01)
    CONTENT = int(0x15)
    ADJ_LIST = int(0x03)
