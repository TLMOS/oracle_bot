import os
import json

class InvitationMessagePairs(object):
    def __init__(self, file_name):
        self.file_name = file_name
        if not os.path.exists(file_name):
            with open(file_name, 'w') as f:
                json.dump({}, f)
        with open(file_name, 'r') as f:
            self.id_pairs = json.load(f)

    def add_pair(self, message_id: int, room_id: int):
        self.id_pairs[str(message_id)] = int(room_id)
        with open(self.file_name, 'w') as f:
            json.dump(self.id_pairs, f)
   
    def get_room_id(self, message_id: int):
        return self.id_pairs[str(message_id)]
    
    def get_message_id(self, room_id: int):
        for message_id_, room_id_ in self.id_pairs.items():
            if room_id_ == room_id:
                return int(message_id_)

    def get_pairs(self):
        return self.id_pairs.items()
    
    def contains_room_id(self, room_id: int):
        for message_id_, room_id_ in self.id_pairs.items():
            if room_id_ == room_id:
                return True
        return False
    
    def contains_message_id(self, message_id: int):
        return str(message_id) in self.id_pairs
    
    def delete_pair(self, message_id: int):
        del self.id_pairs[str(message_id)]
        with open(self.file_name, 'w') as f:
            json.dump(self.id_pairs, f)