from Utils.tlv_types import TLVType

def encode_tlv(tlv_type, value):
    length = len(value)
    # TLV format: Type (1 byte), Length (1-4 bytes), Value (variable length)
    # Encode Type
    encoded = bytes([tlv_type])

    # Encode Length field
    if length < 128:  # If the length fits in 1 byte
        encoded += bytes([length])
    else:
        # If length doesn't fit in a single byte, use multiple bytes for length
        length_bytes = length.to_bytes((length.bit_length() + 7) // 8, 'big')
        encoded += bytes([0x80 | len(length_bytes)])  # Set the MSB to indicate multi-byte length
        encoded += length_bytes

    # Encode Value field
    encoded += value  # Convert value to bytes (assuming it's a string)

    return encoded


def decode_tlv(tlv_string, decoded_data):
    index = 0

    while index < len(tlv_string) and tlv_string[index] in set(TLVType):
        tlv_type = tlv_string[index]
        index += 1

        if tlv_string[index] & 0x80:  # Handling multi-byte length
            length_bytes = tlv_string[index] & 0x7F
            index += 1
            length = int.from_bytes(tlv_string[index:index + length_bytes], 'big')
            index += length_bytes
        else:
            length = tlv_string[index]
            index += 1

        # Decode Value field
        value = tlv_string[index:index + length]
        index += length

        # Check if the value is another TLV
        # if tlv_type in set(TLVType):  # Assuming it's a constructed type (nested TLV)
        decode_tlv(value, decoded_data)  # Recursively decode the nested TLV

        decoded_data[tlv_type] = value
    return decoded_data
