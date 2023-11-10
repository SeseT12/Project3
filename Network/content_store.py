

class ContentStore:
    def __init__(self):
        self.content = {}

    def add_content(self, name, data):
        self.content[name] = data

    def entry_exists(self, name):
        if name in self.content.keys():
            return True

        return False
