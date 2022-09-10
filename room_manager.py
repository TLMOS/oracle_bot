from email import message
from database import Database
import os

class Room():
    def __init__(self, channel_id: int, message_id: int, author_id: int):
        self.channel_id = channel_id
        self.message_id = message_id
        self.author_id = author_id

class RoomManager():
    def __init__(self, db_path: str):
        needs_init = not os.path.exists(db_path)
        self._db = Database(db_path)
        if needs_init:
            self._db.execute("""
            CREATE TABLE general
            (
                channel_id BIGINT unsigned NOT NULL,
                message_id BIGINT unsigned NOT NULL,
                author_id BIGINT unsigned NOT NULL,
                PRIMARY KEY (channel_id) );
            """)
            self._db.execute("""
            CREATE TABLE campaign
            (
                channel_id BIGINT unsigned NOT NULL,
                message_id BIGINT unsigned NOT NULL,
                author_id BIGINT unsigned NOT NULL,
                PRIMARY KEY (channel_id) );
            """)
            self._db.commit()

    def add_room(self, table:str, channel_id: int, message_id: int, author_id: int) -> None:
        sql = f'INSERT INTO {table} (channel_id, message_id, author_id) VALUES (?, ?, ?)'
        self._db.execute(sql, (channel_id, message_id, author_id))
        self._db.commit()

    def get_room_by_mid(self, table:str, message_id:int) -> Room:
        sql = f'SELECT  * FROM {table} WHERE message_id={message_id}'
        self._db.execute(sql)
        res = self._db.fetchall()
        if res:
            return Room(*res[0])

    def get_room_by_cid(self, table:str, channel_id:int) -> Room:
        sql = f'SELECT  * FROM {table} WHERE channel_id={channel_id}'
        self._db.execute(sql)
        res = self._db.fetchall()
        if res:
            return Room(*res[0])

    def delete_room(self, table:str, room:Room) -> None:
        sql = f'DELETE FROM {table} WHERE channel_id={room.channel_id}'
        self._db.execute(sql)
        self._db.commit()
