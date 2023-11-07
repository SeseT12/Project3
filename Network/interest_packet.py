from Utils import tlv
from Utils.tlv_types import TLVType


class InterestPacket:

    @staticmethod
    def encode(name, node_id):
        name_component_tlv = tlv.encode_tlv(TLVType.NAME_COMPONENT, name)
        name_tlv = tlv.encode_tlv(TLVType.NAME, name_component_tlv)
        id_tlv = tlv.encode_tlv(TLVType.ID, str(node_id).encode())
        it_packet_tlv = tlv.encode_tlv(TLVType.INTEREST_PACKET, id_tlv + name_tlv)

        return it_packet_tlv

    @staticmethod
    def decode_tlv(tlv_string):
        decoded_data = {}
        tlv.decode_tlv(tlv_string, decoded_data)
        return decoded_data
