

class ForwardingInformationBase:
    def __init__(self):
        self.entries = []

    def add_entry(self, name_prefix, nodes):
        self.entries.append((name_prefix, nodes))

    def get_forwarding_nodes(self, name_prefix):
        for entry in self.entries:
            if entry[0] == name_prefix:
                return entry[1]