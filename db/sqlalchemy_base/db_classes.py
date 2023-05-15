from typing import List, Optional
from sqlalchemy import ForeignKey, String, DateTime, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, \
    relationship, declarative_base
from sqlalchemy.dialects.mssql import DATETIME
from datetime import datetime
import typing
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session 

''' class Base(DeclarativeBase):
    pass '''

engine = create_engine("sqlite:///db_dara_store_telegram.db", echo=True)

Base = declarative_base()

class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True) 
    name: Mapped[str] #  = mapped_column(String(30))   # message.from_user.full_name
    telegram_name: Mapped[Optional[str]]            # 
    telegram_id: Mapped[Optional[str]]              # message.from_id
    phone: Mapped[Optional[str]]
    
    def __repr__(self) -> dict:
        return {
            "id":            self.id, 
            "name":          self.name, 
            "telegram_name": self.telegram_name,
            "telegram_id":   self.telegram_id, 
            "phone":         self.phone
        }


class ScheduleCalendar(Base):
    __tablename__ = "schedule_calendar"
    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[Optional[str]]
    start_time: Mapped[Optional[str]]
    end_time: Mapped[Optional[str]]
    date: Mapped[Optional[datetime]]
    status: Mapped[Optional[str]]
    event_type: Mapped[Optional[str]]
    
    def __repr__(self) -> dict:
        return {
            "id":           self.id, 
            "schedule_id":  self.schedule_id,
            "start_time" :  self.start_time,
            "end_time" :    self.end_time,
            "date" :        self.date,
            "status" :      self.status,
            "event_type" :  self.event_type,
        }
        


class TattooItems(Base):
    __tablename__ = "tattoo_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]]
    photos: Mapped[List["TattooItemPhoto"]] = \
        relationship(back_populates="photo_id", cascade="all, delete-orphan") 
    price: Mapped[Optional[str]]
    colored: Mapped[Optional[str]]
    note: Mapped[Optional[str]]
    creator: Mapped[Optional[str]]
    
    def __repr__(self) -> str:
        ''' return {
            "id": self.id,
            "name":self.name,
            "photo":self.photo,
            "price":self.price,
            "colored":self.colored,
            "note":self.note,
            "creator":self.creator,
        } '''
        
        return f"TattooItems(id={self.id!r}, \
            name={self.name!r},\
            price={self.price!r},\
            colored={self.colored!r},\
            note={self.note!r},\
            creator={self.creator!r})"
        


class TattooItemPhoto(Base):
    __tablename__ = "tattoo_items_photo"
    id: Mapped[int] = mapped_column(primary_key=True)
    tattoo_item_id: Mapped[int] = mapped_column(ForeignKey("tattoo_items.id"))
    photo: Mapped[str]
    tattoo_item_name: Mapped[Optional[str]]
    photo_id: Mapped["TattooItems"] = relationship(back_populates="photos")
    
    def __repr__(self) -> str:
        # return {"id":self.id, "tattoo_item_name":self.tattoo_item_name, "photo": self.photo}
        return f"TattooItemPhoto(id={self.id!r}, tattoo_item_name={self.tattoo_item_name!r}, photo={self.photo!r})"


''' Статусы заказа:
    Открыт — заказ был создан в базе данных, но ещё не был обработан.
    Обработан — оплата была получена.
    Выполнен — вся работа по заказу завершена.
    Отклонен — заказ отклонен админом.
    Отложен — заказ ещё не обработан, так как в нём содержатся товары, которых нет в наличии. Только для гифтбокса
    Аннулирован — заказ был отменён покупателем.
    Ожидает ответа — заказ был создан, когда покупатель оформил заявку на обратный ответ.
'''
class Orders(Base):
    __tablename__ = "orders"
    id:             Mapped[int] = mapped_column(primary_key=True)
    order_type:     Mapped[Optional[str]] # тип заказа - постоянное тату, переводное тату, эскиз, гифтбокс, сертификат
    order_name:     Mapped[str] # = mapped_column(String(50))
    user_id:        Mapped[str] #  = mapped_column(ForeignKey("user_account.id"))
    order_photo :   Mapped[List["OrderPhoto"]]= relationship(back_populates="photo") 
    tattoo_size:    Mapped[Optional[str]] # только для заказа тату - размер тату
    date_meeting:   Mapped[Optional[str]]
    date_time :     Mapped[Optional[str]]
    tattoo_note :   Mapped[Optional[str]] # только для заказа тату - описание тату
    order_note :    Mapped[Optional[str]]
    order_state:    Mapped[Optional[str]] # Открыт, Обработан, Выполнен, Отклонен, Отложен, Аннулирован, Ожидает ответа
    order_number:   Mapped[Optional[str]]
    creation_date:  Mapped[Optional[datetime]] # DATE,
    price:          Mapped[Optional[str]]
    check_document: Mapped[List["CheckDocument"]] = \
        relationship(back_populates="doc_id") # Mapped[Optional[str]]
    username:       Mapped[Optional[str]] #  = relationship(back_populates="name") # message.from_user.full_name
    schedule_id:    Mapped[Optional[str]]
    colored:        Mapped[Optional[str]]
    # details_number: Mapped[Optional[int]]
    bodyplace:      Mapped[Optional[str]]
    tattoo_place_photo: Mapped[List["TattooPlacePhoto"]] = \
        relationship(back_populates="photo_id") # , cascade="all, delete-orphan"
    tattoo_place_video_note: Mapped[List["TattooPlaceVideoNote"]] = \
        relationship(back_populates="video_id") # только для заказа тату - видео записка тела тату
    tattoo_place_video: Mapped[List["TattooPlaceVideo"]]=\
        relationship(back_populates="video_id") # только для заказа тату - видео тела тату
    code:           Mapped[Optional[str]] # только для заказа сертификата - код сертификата
    
    def __repr__(self) -> dict:
        return {
            "order_number":     self.order_number,
            "order_type":       self.order_type,
            "order_name":       self.order_name,
            "tattoo_size":      self.tattoo_size,
            "colored":          self.colored,
            "bodyplace":        self.bodyplace,
            "tattoo_note":      self.tattoo_note,
            "creation_date":    self.creation_date,
            "order_state":      self.order_state,
            'order_note':       self.order_note,
            'code':             self.code
        }


class OrderPhoto(Base):
    __tablename__ = "tattoo_photo"
    id:                 Mapped[int] = mapped_column(primary_key=True)
    order_id:           Mapped[int] = mapped_column(ForeignKey("orders.id"))
    order_number:       Mapped[int]# Mapped["TattooOrders"]# = relationship(back_populates="tattoo_order_number")
    telegram_user_id:   Mapped[int] # = mapped_column(ForeignKey("user.id")) # message.from_id
    photo:              Mapped["Orders"] = relationship(back_populates="order_photo")
    
    def __repr__(self) -> dict:
        return {
            "id":                   self.id,
            "order_id":             self.order_id, 
            "order_number":         self.order_number, 
            "photo":                self.photo,
            "telegram_user_id":     self.telegram_user_id
        }
        

class TattooPlacePhoto(Base):
    __tablename__ = "tattoo_place_photo"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id:  Mapped[int] = mapped_column(ForeignKey("orders.id"))
    order_number: Mapped[int]#Mapped["TattooOrders"] = relationship(back_populates="tattoo_order_number")
    telegram_user_id: Mapped[int] # = mapped_column(ForeignKey("user.id"))
    photo: Mapped[str]
    photo_id: Mapped["Orders"] = relationship(back_populates="tattoo_place_photo")
    
    def __repr__(self) -> dict:
        return {
            "id":                   self.id,
            "order_number":         self.order_number, 
            "photo":                self.photo,
            "telegram_user_id":     self.telegram_user_id
        } 


class TattooPlaceVideoNote(Base):
    __tablename__ = "tattoo_place_video_note"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id:  Mapped[int] = mapped_column(ForeignKey("orders.id"))
    order_number: Mapped[int]#Mapped["TattooOrders"] = relationship(back_populates="tattoo_order_number")
    telegram_user_id: Mapped[int] # = mapped_column(ForeignKey("user.id"))
    video: Mapped[str]
    video_id: Mapped["Orders"] = relationship(back_populates="tattoo_place_video_note")
    
    def __repr__(self) -> dict:
        return {
            "id":                   self.id,
            "order_number":         self.order_number, 
            "video":                self.video,
            "telegram_user_id":     self.telegram_user_id
        }


class TattooPlaceVideo(Base):
    __tablename__ = "tattoo_place_video"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id:  Mapped[int] = mapped_column(ForeignKey("orders.id"))
    order_number: Mapped[int]#Mapped["TattooOrders"] = relationship(back_populates="tattoo_order_number")
    telegram_user_id: Mapped[int] # = mapped_column(ForeignKey("user.id"))
    video: Mapped[str]
    video_id: Mapped["Orders"] = relationship(back_populates="tattoo_place_video")
    
    def __repr__(self) -> dict:
        return {
            "id":               self.id,
            "order_number":     self.order_number, 
            "video":            self.video,
            "telegram_user_id": self.telegram_user_id
        }


class CheckDocument(Base):
    __tablename__ = "check_document_tattoo_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[int]
    order_number_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    telegram_user_id: Mapped[int] # = mapped_column(ForeignKey("user.id"))
    doc: Mapped[Optional[str]]
    doc_id: Mapped["Orders"]= \
        relationship(back_populates="check_document")
    
    def __repr__(self) -> dict:
        return {
            "id":               self.id, 
            "order_number":     self.order_number,
            "telegram_user_id": self.telegram_user_id,
            "doc":              self.doc
        } 



class TattooOrderPriceList(Base):
    __tablename__ = "tattoo_order_price_list"
    id: Mapped[int] = mapped_column(primary_key=True)
    min_size: Mapped[Optional[int]]
    max_size: Mapped[Optional[int]] 
    price: Mapped[Optional[str]] 
    
    def __repr__(self) -> dict:
        return {
            "id":       self.id, 
            "min_size": self.min_size,
            "max_size": self.max_size, 
            "price":    self.price
        }



Base.metadata.create_all(engine)
session = scoped_session(sessionmaker(bind=engine))
Base.query = session.query_property()