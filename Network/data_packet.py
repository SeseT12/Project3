from Utils import tlv
from Utils.tlv_types import TLVType

class DataPacket:
    @staticmethod
    def encode(name, content_data):
        name_component_tlv = tlv.encode_tlv(TLVType.NAME_COMPONENT, name)
        name_tlv = tlv.encode_tlv(TLVType.NAME, name_component_tlv)
        #id_tlv = tlv.encode_tlv(TLVType.ID, str(node_id).encode())
        content_tlv = tlv.encode_tlv(TLVType.CONTENT, content_data)
        print(content_tlv)
        data_packet_tlv = tlv.encode_tlv(TLVType.DATA_PACKET, content_tlv + name_tlv)

        return data_packet_tlv

    @staticmethod
    def decode_tlv(tlv_string):
        decoded_data = {}
        tlv.decode_tlv(tlv_string, decoded_data)
        return decoded_data