# Contributor(s): sregitz
from Utils import tlv
from Utils.tlv_types import TLVType


class PacketEncoder:
    @staticmethod
    def encode_adj_list_packet(data):
        adj_list_packet_tlv = tlv.encode_tlv(TLVType.ADJ_LIST, data)
        return adj_list_packet_tlv

    @staticmethod
    def encode_fib_packet(data):
        fib_packet_tlv = tlv.encode_tlv(TLVType.FIB, data)
        return fib_packet_tlv
