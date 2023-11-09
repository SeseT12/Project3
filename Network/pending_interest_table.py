

class PendingInterestTable:
    def __init__(self):
        self.pending_interests = {}

    def add_interest(self, node_id, name):
        if name.decode() not in self.pending_interests.keys():
            self.pending_interests[name.decode()] = []
        self.pending_interests[name.decode()].append(int(node_id.decode()))

    def node_interest_exists(self, node_id, name):
        if self.interest_exists(name) and int(node_id.decode()) in self.pending_interests[name.decode()]:
            return True

        return False

    def interest_exists(self, name):
        if name.decode() in self.pending_interests.keys():
            return True

        return False

    def remove_interest(self, name):
        del self.pending_interests[name]
