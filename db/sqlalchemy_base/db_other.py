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


class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True) 
    name: Mapped[str] = mapped_column(String(30))   # message.from_user.full_name
    telegram_name: Mapped[Optional[str]]            # 
    telegram_id: Mapped[Optional[str]]              # message.from_id
    phone: Mapped[Optional[str]]
    
    def __repr__(self) -> dict:
        return {
            "id":self.id, 
            "name":self.name, 
            "telegram_name": self.telegram_name,
            "telegram_id":self.telegram_id, 
            "phone":self.phone
        }

''' 
class Address(Base):
    __tablename__ = "address"
    id: Mapped[int] = mapped_column(primary_key=True)
    email_address: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    user: Mapped["User"] = relationship(back_populates="addresses")
    def __repr__(self) -> dict:
        return Address{"id":self.id, "user_id":self.user_id, "email_address":self.email_address} 
'''


class TattooOrders(Base):
    __tablename__ = "tattoo_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    tattoo_name: Mapped[str] = mapped_column(String(50))
    user_id: Mapped[str] = mapped_column(ForeignKey("user_account.id"))
    tattoo_photo : Mapped[List["TattooPhoto"]]= \
        relationship(back_populates="photo", cascade="all, delete-orphan") 
    
    tattoo_size: Mapped[Optional[str]]
    date_meeting: Mapped[Optional[str]]
    date_time : Mapped[Optional[str]]
    tattoo_note : Mapped[Optional[str]]
    order_note : Mapped[Optional[str]]
    order_state: Mapped[Optional[str]]
    tattoo_order_number: Mapped[Optional[str]]
    creation_date: Mapped[Optional[datetime]] # DATE,
    price: Mapped[Optional[str]]
    check_document: Mapped[List["CheckDocumentTattooOrders"]] = relationship(back_populates="doc", cascade="all, delete-orphan") # Mapped[Optional[str]]
    
    username: Mapped[Optional[str]] = relationship(back_populates="name") # message.from_user.full_name
    schedule_id: Mapped[Optional[str]]
    colored: Mapped[Optional[str]]
    details_number: Mapped[Optional[int]]
    bodyplace: Mapped[Optional[str]]
    tattoo_place_photo: Mapped[List["TattooPlacePhoto"]] = \
        relationship(back_populates="photo", cascade="all, delete-orphan") 
    
    tattoo_type: Mapped[Optional[str]]
    tattoo_place_video_note: Mapped[List["TattooPlaceVideoNote"]] = \
        relationship(back_populates="video", cascade="all, delete-orphan") 
    
    tattoo_place_video: Mapped[List["TattooPlaceVideo"]]= \
        relationship(back_populates="video", cascade="all, delete-orphan") 
    
    def __repr__(self) -> dict:
        return {
            "tattoo_order_number":  self.tattoo_order_number,
            "tattoo_type":          self.tattoo_type,
            "tattoo_name":          self.tattoo_name,
            "tattoo_size":          self.tattoo_size,
            "colored":              self.colored,
            "bodyplace":            self.bodyplace,
            "tattoo_note":          self.tattoo_note,
            "creation_date":        self.creation_date,
            "order_state":          self.order_state,
            'order_note':           self.order_note,
        }


class TattooPhoto(Base):
    __tablename__ = "tattoo_photo"
    id: Mapped[int] = mapped_column(primary_key=True)
    tattoo_order_id: Mapped[int] = mapped_column(ForeignKey("tattoo_orders.id"))
    tattoo_order_number: Mapped["TattooOrders"] = relationship(back_populates="tattoo_order_number")
    telegram_user_id: Mapped[int] # = mapped_column(ForeignKey("user.id")) # message.from_id
    photo: Mapped["TattooOrders"] = relationship(back_populates="tattoo_photo")
    
    def __repr__(self) -> dict:
        return {
            "id":                   self.id,
            "tattoo_order_id":      self.tattoo_order_id, 
            "tattoo_order_number":  self.tattoo_order_number, 
            "photo":                self.photo,
            "telegram_user_id":     self.telegram_user_id
        } 


class TattooPlacePhoto(Base):
    __tablename__ = "tattoo_place_photo"
    id: Mapped[int] = mapped_column(primary_key=True)
    tattoo_order_number: Mapped["TattooOrders"] = relationship(back_populates="tattoo_order_number")
    telegram_user_id: Mapped[int] # = mapped_column(ForeignKey("user.id"))
    photo: Mapped["TattooOrders"] = relationship(back_populates="tattoo_place_photo")
    
    def __repr__(self) -> dict:
        return {
            "id":                   self.id,
            "tattoo_order_number":  self.tattoo_order_number, 
            "photo":                self.photo,
            "telegram_user_id":     self.telegram_user_id
        } 


class TattooPlaceVideoNote(Base):
    __tablename__ = "tattoo_place_video_note"
    id: Mapped[int] = mapped_column(primary_key=True)
    tattoo_order_number: Mapped["TattooOrders"] = relationship(back_populates="tattoo_order_number")
    telegram_user_id: Mapped[int] # = mapped_column(ForeignKey("user.id"))
    video: Mapped["TattooOrders"] = relationship(back_populates="tattoo_place_video_note")
    
    def __repr__(self) -> dict:
        return {
            "id":self.id,
            "tattoo_order_number":  self.tattoo_order_number, 
            "video":                self.video,
            "telegram_user_id":     self.telegram_user_id
        }


class TattooPlaceVideo(Base):
    __tablename__ = "tattoo_place_video"
    id: Mapped[int] = mapped_column(primary_key=True)
    tattoo_order_number: Mapped["TattooOrders"] = relationship(back_populates="tattoo_order_number")
    telegram_user_id: Mapped[int] # = mapped_column(ForeignKey("user.id"))
    video: Mapped["TattooOrders"] = relationship(back_populates="tattoo_place_video")
    
    def __repr__(self) -> dict:
        return {
            "id":self.id,
            "tattoo_order_number":  self.tattoo_order_number, 
            "video":                self.video,
            "telegram_user_id":     self.telegram_user_id
        }


class TattooSketchOrders(Base):
    __tablename__ = "tattoo_sketch_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    sketch_order_number: Mapped[int]
    desc: Mapped[Optional[str]] 
    photo: Mapped[List["SketchPhoto"]]= \
        relationship(back_populates="photo", cascade="all, delete-orphan")  
    telegram_user_id: Mapped[int]
    creation_time: Mapped[Optional[str]] 
    order_state: Mapped[Optional[str]] 
    check_document: Mapped[typing.List['CheckDocumentTattooSketchOrders']] = relationship(back_populates="doc", cascade="all, delete-orphan")
    # = mapped_column("check_document_tattoo_sketch_orders.doc")
    price: Mapped[Optional[str]]

    def __repr__(self) -> dict:
        return {
            "id":                   self.id,
            "sketch_order_number":  self.sketch_order_number,
            "desc":                 self.desc,
            "photo":                self.photo,
            "telegram_user_id":     self.telegram_user_id,
            "creation_time":        self.creation_time,
            "order_state":          self.order_state,
            "price":                self.price,
            "check_document":       self.check_document
        }


class CheckDocumentTattooSketchOrders(Base):
    __tablename__ = "check_document_tattoo_sketch_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[int] = mapped_column(ForeignKey("tattoo_sketch_orders.id"))
    telegram_user_id: Mapped[int] # = mapped_column(ForeignKey("user.id"))
    doc: Mapped[Optional[str]]
    
    def __repr__(self) -> dict:
        return {"id":self.id, "telegram_user_id":self.telegram_user_id, "order_number":self.order_number, "doc":self.doc} 


class CheckDocumentTattooOrders(Base):
    __tablename__ = "check_document_tattoo_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[int] = mapped_column(ForeignKey("tattoo_orders.id"))
    telegram_user_id: Mapped[int] # = mapped_column(ForeignKey("user.id"))
    doc: Mapped[Optional[str]]= \
        relationship(back_populates="check_document", cascade="all, delete-orphan")
    
    def __repr__(self) -> dict:
        return {"id":self.id, "telegram_user_id":self.telegram_user_id, "order_number":self.order_number, "doc":self.doc} 


class CheckDocumentGiftboxOrders(Base):
    __tablename__ = "check_document_giftbox_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[int] = mapped_column(ForeignKey("giftbox_orders.id"))
    telegram_user_id: Mapped[int] # = mapped_column(ForeignKey("user.id"))
    doc: Mapped[Optional[str]]= \
        relationship(back_populates="check_document", cascade="all, delete-orphan")
    
    def __repr__(self) -> dict:
        return {"id":self.id, "telegram_user_id":self.telegram_user_id, "order_number":self.order_number, "doc":self.doc} 


class CheckDocumentCertOrders(Base):
    __tablename__ = "check_document_cert_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[int]= mapped_column(ForeignKey("сert_orders.id"))
    telegram_user_id: Mapped[int] # = mapped_column(ForeignKey("user.id"))
    doc: Mapped[Optional[str]]= \
        relationship(back_populates="check_document", cascade="all, delete-orphan")
    
    def __repr__(self) -> dict:
        return {"id":self.id, "telegram_user_id":self.telegram_user_id, "order_number":self.order_number, "doc":self.doc} 


class SketchPhoto(Base):
    __tablename__ = "sketch_photo"
    id: Mapped[int] = mapped_column(primary_key=True)
    tattoo_sketch_order_number: Mapped[int] #  mapped_column(ForeignKey("tattoo_sketch_orders.img_id"))
    telegram_user_id: Mapped[int] #  # = mapped_column(ForeignKey("user.id"))
    photo: Mapped["TattooSketchOrders"]= \
        relationship(back_populates="photo", cascade="all, delete-orphan")
    
    def __repr__(self) -> dict:
        return {"id": self.id, "tattoo_sketch_order_number": self.tattoo_sketch_order_number,
            "photo":self.photo, "telegram_user_id": self.telegram_user_id} 


class TattooOrderPriceList(Base):
    __tablename__ = "tattoo_order_price_list"
    id: Mapped[int] = mapped_column(primary_key=True)
    min_size: Mapped[Optional[int]]
    max_size: Mapped[Optional[int]] 
    price: Mapped[Optional[str]] 
    
    def __repr__(self) -> dict:
        return {"id": self.id, "min_size": self.min_size,
            "max_size":self.max_size, "price":self.price}


class TattooThemes(Base):
    __tablename__ = "tattoo_themes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]]
    
    def __repr__(self) -> dict:
        return {"id": self.id, "name":self.name}


class CandleItems(Base):
    __tablename__ = "candle_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped["GiftboxItems"] = relationship(back_populates= "candle_name")
    photo: Mapped["GiftboxItems"] = relationship(back_populates= "candle_photo")
    price: Mapped["GiftboxItems"] = relationship(back_populates= "candle_price")
    note: Mapped["GiftboxItems"] = relationship(back_populates= "candle_note")
    state: Mapped["GiftboxItems"] = relationship(back_populates= "candle_state")
    quantity: Mapped[Optional[int]]
    
    def __repr__(self) -> dict:
        return {
            "id":self.id,
            "name":self.name,
            "photo":self.photo,
            "price":self.price,
            "note":self.note,
            "state":self.state,
            "quantity":self.quantity
        }


class GiftboxOrders(Base):
    __tablename__ = "giftbox_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_note: Mapped[Optional[str]]
    order_number: Mapped[Optional[str]]
    creation_date: Mapped[Optional[str]]
    telegram_user_id: Mapped[Optional[int]] # = mapped_column(ForeignKey("user_account.id"))
    check_document: Mapped[List["CheckDocumentGiftboxOrders"]]  = relationship(back_populates="doc", cascade="all, delete-orphan")# = mapped_column("check_document_tattoo_orders.doc") 
    # = relationship(back_populates= "doc", cascade= "all, delete-orphan")
    
    order_state : Mapped[Optional[str]]
    price: Mapped[Optional[str]]
    
    def __repr__(self) -> dict:
        return {
            "id":self.id,
            "order_note":self.order_note,
            "order_number":self.order_number,
            "creation_date":self.creation_date,
            "telegram_user_id":self.telegram_user_id,
            "order_state":self.order_state,
            "price":self.price,
            "check_document":self.check_document
        }


class SequinsItems(Base):
    __tablename__ = "sequins_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped["GiftboxItems"] = relationship(back_populates= "sequins_type")
    state: Mapped["GiftboxItems"] = relationship(back_populates= "sequins_state")
    photo: Mapped[Optional[str]]
    
    def __repr__(self) -> dict:
        return {
            "id":self.id,
            "type":self.type,
            "state":self.state,
            "photo":self.photo
        }


class GiftboxItems(Base):
    __tablename__ = "giftbox_items"
    id:             Mapped[int] = mapped_column(primary_key=True)
    name:           Mapped[Optional[str]]
    photo:          Mapped[List["TattooPhoto"]] = \
        relationship(back_populates="photo", cascade="all, delete-orphan")  
    price:          Mapped[Optional[str]]
    giftbox_note:   Mapped[Optional[str]]
    candle_name:    Mapped["CandleItems"] = relationship(back_populates= "name")
    candle_photo :  Mapped["CandleItems"] = relationship(back_populates= "photo")
    candle_price:   Mapped["CandleItems"] = relationship(back_populates= "price")
    candle_note :   Mapped["CandleItems"] = relationship(back_populates= "note")
    candle_state :  Mapped["CandleItems"] = relationship(back_populates= "state")
    tattoo_theme:   Mapped[Optional[str]]
    tattoo_note:    Mapped[Optional[str]]
    tattoo_state:   Mapped[Optional[str]]
    sequins_type :  Mapped["SequinsItems"] = relationship(back_populates= "type")
    sequins_state : Mapped["SequinsItems"] = relationship(back_populates= "state")
    
    def __repr__(self) -> dict:
        return {
            "id":self.id,
            "photo":self.photo,
            "price":self.price,
            "giftbox_note":self.giftbox_note,
            "candle_name":self.candle_name,
            "candle_price":self.candle_price,
            "candle_note":self.candle_note,
            "candle_state":self.candle_state,
            "tattoo_note":self.tattoo_note,
            "tattoo_state":self.tattoo_state,
            "sequins_type":self.sequins_type,
            "sequins_state":self.sequins_state,
        }

'''
    giftbox_name = State()                  # назови гифтбокс
    giftbox_photo = State()                 # загрузи фото гифтбокс
    giftbox_price = State()                 # примерная цена на гифтбокс
    giftbox_note = State()                  # напиши описание гифтбокс
    giftbox_candle_choice = State()         # добавляем свечу в гифтбокс из готовых
    giftbox_candle_name = State()           # назови имя свечи
    giftbox_candle_photo = State()          # загрузи фото свечи
    giftbox_candle_price = State()          # если есть свеча, то какая цена свеча,если свеча нет, то цена 0
    giftbox_candle_note = State()           # описание свечи
    giftbox_candle_state = State()          # есть ли эти свечи сейчас в наличии или надо докупать      
    # giftbox_tattoo_state = State()        # есть ли тату в гифтбокс 
    giftbox_tattoo_theme = State()          # если есть тату, то какая тематика
    giftbox_tattoo_other_theme = State()    # если есть тату, то какая тематика
    giftbox_tattoo_note  = State()          # впиши описание тату
    giftbox_tattoo_state = State()          # есть ли эти тату сейчас в наличии или надо докупать
    giftbox_sequins_type = State()           # впиши тип блесток тату
    giftbox_sequins_state = State()          # есть ли эти блестки сейчас в наличии или надо докупать
'''


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
        


class SchedulePhoto(Base):
    __tablename__ = "schedule_photo"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]]
    photo: Mapped[Optional[str]]
    
    def __repr__(self) -> dict:
        return {
            "id":   self.id, 
            "name": self.name,
            "photo":self.photo,
        }


class CertificateOrders(Base):
    __tablename__ = "сert_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    # username TEXT NOT NULL,
    price: Mapped[Optional[str]]
    order_state: Mapped[Optional[str]]
    code: Mapped[Optional[str]] 
    creation_date: Mapped[Optional[datetime]]
    cert_order_number: Mapped[Optional[str]]
    check_document: Mapped[List["CheckDocumentCertOrders"]]  = relationship(back_populates="doc", cascade="all, delete-orphan")# = mapped_column("check_document_cert_orders.doc") 
    # =relationship(back_populates="doc", cascade="all, delete-orphan")
    telegram_user_id: Mapped["User"] = relationship(back_populates= "telegram_id")
    
    def __repr__(self) -> dict:
        return {
            "id":self.id,
            "telegram":self.telegram_user_id,
            "cert_order_number":self.cert_order_number,
            "creation_date":self.creation_date,
            "code":self.code,
            "order_state":self.order_state,
            "price":self.price,
        }


class TattooAI(Base):
    __tablename__ = "tattoo_ai"
    id: Mapped[int] = mapped_column(primary_key=True)
    img_id: Mapped[int]
    img_name: Mapped[Optional[str]]
    photo : Mapped[List["AIPhoto"]]= \
        relationship(back_populates="photo", cascade="all, delete-orphan") 
    state: Mapped[Optional[str]]
    author_name: Mapped[Optional[str]]
    
    def __repr__(self) -> dict:
        return {
            "id":self.id,
            "img_id":self.img_id,
            "img_name":self.img_name,
            "state":self.state,
            'author_name':self.author_name,
        }


class AIPhoto(Base):
    __tablename__ = "ai_photo"
    id: Mapped[int] = mapped_column(primary_key=True)
    photo: Mapped["TattooAI"] = relationship(back_populates="photo")
    
    def __repr__(self) -> dict:
        return {"id":self.id, "photo": self.photo}
