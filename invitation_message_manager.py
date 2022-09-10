import os
import json

class InvitationMessage(object):
    def __init__(self, message_id, room_id, author_id):
        self.id = message_id
        self.room_id = room_id
        self.author_id = author_id

class InvitationMessageManager(object):
    def __init__(self, file_name):
        self.file_name = file_name
        if not os.path.exists(file_name):
            with open(file_name, 'w') as f:
                json.dump({}, f)
        with open(file_name, 'r') as f:
            self.messages = json.load(f)

    def add_message(self, message_id: int, room_id: int, author_id: int):
        self.messages[str(message_id)] = {'room_id': room_id, 'author_id': author_id} 
        with open(self.file_name, 'w') as f:
            json.dump(self.messages, f)
   
    def get_message(self, message_id: int):
        if str(message_id) in self.messages:
            message_data = self.messages[str(message_id)]
            return InvitationMessage(message_id, message_data['room_id'], message_data['author_id'])
    
    def get_message_by_room_id(self, room_id: int):
        for message_id, message_data in self.messages.items():
            if message_data['room_id'] == room_id:
                return InvitationMessage(message_id, message_data['room_id'], message_data['author_id'])

    def get_messages(self):
        messages = []
        for message_id, message_data in self.messages.items():
            messages.add(InvitationMessage(message_id, message_data['room_id'], message_data['author_id']))
        return messages
    
    def contains_message(self, message_id: int):
        return str(message_id) in self.messages
    
    def delete_message(self, message_id: int):
        del self.messages[str(message_id)]
        with open(self.file_name, 'w') as f:
            json.dump(self.messages, f)