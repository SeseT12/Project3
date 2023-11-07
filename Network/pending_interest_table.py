

class PendingInterestTable:
    def __init__(self):
        self.pending_interests = {}

    def add_interest(self, node_id, name):
        #check if key exists
        self.pending_interests[name.decode()].append(node_id)