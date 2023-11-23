# Contributor(s): sregitz
class ForwardingInformationBase:
    def __init__(self):
        self.entries = []

    def add_entry(self, name_prefix, nodes):
        self.entries.append((name_prefix, nodes))

    def get_forwarding_nodes(self, name_prefix):
        forwarding_nodes = []

        matching_entries = [prefix[1] for prefix in self.entries if name_prefix.startswith(prefix[0])]
        if len(matching_entries) > 0:
            forwarding_nodes = max(matching_entries, key=len)

        return forwarding_nodes
        """""""""
        for entry in self.entries:
            if entry[0] == name_prefix:
                return entry[1]

        return []
        """""""""
