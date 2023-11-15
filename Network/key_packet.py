from Utils import tlv
from Utils.tlv_types import TLVType

class KeyPacket:

    @staticmethod
    def encode_key(name, keydata, signature):
        name_component_tlv = tlv.encode_tlv(TLVType.NAME_COMPONENT, name) # actually id of the node:w
        name_tlv = tlv.encode_tlv(TLVType.NAME, name_component_tlv)
        key_tlv = tlv.encode_tlv(TLVType.CONTENT, keydata)
        signature_tlv = tlv.encode_tlv(TLVType.SIGNATURE, signature)
        it_packet_tlv = tlv.encode_tlv(TLVType.KEY_PACKET, key_tlv + name_tlv + signature_tlv)

        return it_packet_tlv

    @staticmethod
    def encode_request(name, node, signature):
        name_component_tlv = tlv.encode_tlv(TLVType.NAME_COMPONENT, name)
        name_tlv = tlv.encode_tlv(TLVType.NAME, name_component_tlv)
        id_tlv = tlv.encode_tlv(TLVType.CONTENT, str(node).encode())
        signature_tlv = tlv.encode_tlv(TLVType.SIGNATURE, signature)
        it_packet_tlv = tlv.encode_tlv(TLVType.KEY_REQUEST_PACKET, id_tlv + name_tlv + signature_tlv)

        return it_packet_tlv

    @staticmethod
    def decode_tlv(tlv_string):
        decoded_data = {}
        tlv.decode_tlv(tlv_string, decoded_data)
        return decoded_data
