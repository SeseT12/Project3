# Contributor(s): alammu, sregitz
import time
from datetime import datetime
class PendingInterestTable:
    def __init__(self):
        self.pending_interests = {}
        self.pending_interests_timer = {}

    def add_interest(self, node_id, name):
        if name.decode() not in self.pending_interests.keys():
            self.pending_interests[name.decode()] = []
            self.pending_interests_timer[name.decode()] = []
        self.pending_interests[name.decode()].append(int(node_id.decode()))
        self.pending_interests_timer[name.decode()].append((int(node_id.decode()), self.current_time()))

    def node_interest_exists(self, node_id, name):
        if self.interest_exists(name) and int(node_id.decode()) in self.pending_interests[name.decode()]:
            return True

        return False

    def interest_exists(self, name):
        if name.decode() in self.pending_interests.keys():
            return True

        return False

    def remove_interest(self, name):
        if name in self.pending_interests.keys():
            del self.pending_interests[name]
            # REMOVE FROM pending_interests_timer too?
    def current_time(self):
        return time.time()

    def is_old(self, timestamp):
        return self.current_time() - timestamp > 500

    def get_old_pending_interests(self):
        output = []
        for name in list(self.pending_interests.keys()):
            for (node_id, timestamp) in self.pending_interests_timer[name]:
                if self.is_old(timestamp):
                    output.append((node_id, name))
        return output

    def update_interest_time(self, node_id, name):
        # Is running decode() twice an issue?
        self.pending_interests_timer[name.decode()].remove([x for x in self.pending_interests_timer[name.decode()] if x[0] == int(node_id.decode())])
        self.pending_interests_timer[name.decode()].append((int(node_id.decode()), self.current_time()))
