""" Packet definitions
"""
import struct


class Packable(float):

    def __index__(self):
        return int(self)


class Packet(object):
    """Instantiates a packet definition

    :param dict definition: Dictionary defining data in a packet
    :returns: Packet instance

    Suitable metadata can be passed in and this class will perform
    necessary pre-compute steps and create a usable packet instance for
    a specific data source.
    """

    # This header is consistant across messages
    header = struct.Struct('!4sHLH')

    def __init__(self, definition):
        self.name = definition['name']
        self.fourcc = definition['fourcc']

        # Pre-compute struct for fixed size packets
        self.members = {}
        self.cdefs = []
        if definition['size'] == "Fixed":
            struct_string = definition['endianness']
            for i, member in enumerate(definition['members']):
                self.members[member['key']] = {'loc': i, 'units': member['units']}
                self.cdefs.append({'key': member['key'].lower(), 'type': member['ctype']})
                struct_string += member['stype']
            self.struct = struct.Struct(struct_string)


    def __repr__(self):
        return "{0} packet [{1}]".format(self.name, self.fourcc.decode("utf-8"))

    def encode(self, data, timestamp=None):
        """Encode a set of data into binary

        :param dict data: A dictionary of values to encode
        :param int timestamp: Time since boot in nanoseconds
        :returns: Binary ecoded data

        Uses the struct package to encode data. Objects should match keys in
        the members list.
        """

        # Make header if given timestamp
        head = b''
        if timestamp is not None:
            timestamp_hi = (timestamp >> 32) & 0xffff
            timestamp_lo = timestamp & 0xffffffff
            head = self.header.pack(self.fourcc, timestamp_hi, timestamp_lo, self.struct.size)

        # Initilize as zeros
        values = [0]*len(self.members)

        # Lookup corisponding metadata
        for key, value in data.items():
            m = self.members[key]
            units = m['units']
            v = (value - units.get('bias', 0)) / units.get('scaleby', 1)
            values[m['loc']] = Packable(v)

        return head + self.struct.pack(*values)

    def typedef(self):
        """Autogen c style typedef structs

        :returns: String c code for the data and header for this packet
        """

        # Header comment
        typestruct = """/*! \\typedef
 * {0} data
 */
typedef struct {{\n""".format(self.name)

        # data
        for line in self.cdefs:
            typestruct += "\t{0} {1}_{2};\n".format(line['type'], self.fourcc.decode("utf-8").lower(), line['key'])

        typestruct += "}} __attribute__((packed)) {0}Data;\n".format(self.name)

        typestruct += """\ntypedef struct {{
	char     ID[4];
	uint8_t  timestamp[6];
	uint16_t data_length;
	{0}Data data;
}} __attribute__((packed)) {0}Message;\n""".format(self.name)
        
        return typestruct


ADIS = Packet({
    'name': "ADIS16405",
    'fourcc': b'ADIS',
    'size': "Fixed",
    'endianness': '!',
    'members': [
        {'key': "VCC",     'stype': "h", 'ctype': 'uint16_t', 'units': {'mks': "volt",      'scaleby': 0.002418}},
        {'key': "Gyro_X",  'stype': "h", 'ctype': 'int16_t',  'units': {'mks': "hertz",     'scaleby': 0.05}},
        {'key': "Gyro_Y",  'stype': "h", 'ctype': 'int16_t',  'units': {'mks': "hertz",     'scaleby': 0.05}},
        {'key': "Gyro_Z",  'stype': "h", 'ctype': 'int16_t',  'units': {'mks': "hertz",     'scaleby': 0.05}},
        {'key': "Acc_X",   'stype': "h", 'ctype': 'int16_t',  'units': {'mks': "meter/s/s", 'scaleby': 0.0333}},
        {'key': "Acc_Y",   'stype': "h", 'ctype': 'int16_t',  'units': {'mks': "meter/s/s", 'scaleby': 0.0333}},
        {'key': "Acc_Z",   'stype': "h", 'ctype': 'int16_t',  'units': {'mks': "meter/s/s", 'scaleby': 0.0333}},
        {'key': "Magn_X",  'stype': "h", 'ctype': 'int16_t',  'units': {'mks': "tesla",     'scaleby': 0.05}},
        {'key': "Magn_Y",  'stype': "h", 'ctype': 'int16_t',  'units': {'mks': "tesla",     'scaleby': 0.05}},
        {'key': "Magn_Z",  'stype': "h", 'ctype': 'int16_t',  'units': {'mks': "tesla",     'scaleby': 0.05}},
        {'key': "Temp",    'stype': "h", 'ctype': 'int16_t',  'units': {'mks': "degree c",  'scaleby': 0.14, 'bias': 25}},
        {'key': "Aux_ADC", 'stype': "h", 'ctype': 'int16_t',  'units': {'mks': "volt",      'scaleby': 806}},
    ]
})
