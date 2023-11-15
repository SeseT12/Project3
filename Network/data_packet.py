from Utils import tlv
from Utils.tlv_types import TLVType

class DataPacket:
    @staticmethod
    def encode(name, network_id, node_id, content_data, signature=b'NOSIG'):
        name_component_tlv = tlv.encode_tlv(TLVType.NAME_COMPONENT, name)
        name_tlv = tlv.encode_tlv(TLVType.NAME, name_component_tlv)
        network_name_id = str(network_id) + str(node_id)
        id_tlv = tlv.encode_tlv(TLVType.ID, network_name_id.encode())
        content_tlv = tlv.encode_tlv(TLVType.CONTENT, content_data)
        signature_tlv = tlv.encode_tlv(TLVType.SIGNATURE, signature)
        data_packet_tlv = tlv.encode_tlv(TLVType.DATA_PACKET, content_tlv + name_tlv + signature_tlv + id_tlv)
        return data_packet_tlv

    @staticmethod
    def decode_tlv(tlv_string):
        decoded_data = {}
        tlv.decode_tlv(tlv_string, decoded_data)
        return decoded_data