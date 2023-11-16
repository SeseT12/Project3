from Utils import tlv
from Utils.tlv_types import TLVType
from Network.interest_packet import InterestPacket
from Network.data_packet import DataPacket


class ContentStore:
    def __init__(self):
        self.content = {}

    def get(self, interest_packet):
        tlv_data = InterestPacket.decode_tlv(interest_packet)
        name = tlv_data[TLVType.NAME_COMPONENT].decode()
        return self.content.get(name)

    def add_content(self, data_packet):
        tlv_data = DataPacket.decode_tlv(data_packet)
        name = tlv_data[TLVType.NAME_COMPONENT].decode()
        self.content[name] = data_packet

    def entry_exists(self, interest_packet):
        tlv_data = InterestPacket.decode_tlv(interest_packet)
        name = tlv_data[TLVType.NAME_COMPONENT].decode()
        if name in self.content.keys():
            return True
        return False
