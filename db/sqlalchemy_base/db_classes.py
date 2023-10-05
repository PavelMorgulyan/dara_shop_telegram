from typing import List, Optional
from sqlalchemy import ForeignKey, String, DateTime, TIMESTAMP
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    declarative_base,
)
from sqlalchemy.dialects.mssql import DATETIME
from datetime import datetime
import typing
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session


""" class Base(DeclarativeBase):
    pass """

engine = create_engine("sqlite:///db_dara_store_telegram.db", echo=True)

Base = declarative_base()


class User(Base):
    __tablename__ = "user_account"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] #  = mapped_column(String(30)) # message.from_user.full_name
    telegram_name: Mapped[Optional[str]]  #
    telegram_id: Mapped[Optional[str]]  # message.from_id
    phone: Mapped[Optional[str]]
    status: Mapped[Optional[str]] # Активный, Админ, Забанен

    def __repr__(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "telegram_name": self.telegram_name,
            "telegram_id": self.telegram_id,
            "phone": self.phone,
            "status": self.status
        }


class ScheduleCalendar(Base):
    __tablename__ = "schedule_calendar"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    start_datetime: Mapped[Optional[datetime]]
    end_datetime: Mapped[Optional[datetime]]
    status: Mapped[Optional[str]]  # Свободен, Занят, Закрыт
    event_type: Mapped[Optional[str]] # тату заказ, коррекция, консультация

    def __repr__(self) -> dict:
        return {
            "id": self.id,
            "start_datetime": self.start_datetime,
            "end_datetime": self.end_datetime,
            "status": self.status,
            "event_type": self.event_type,
        }


class ScheduleCalendarItems(Base):
    __tablename__ = "schedule_calendar_order_items"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    # schedulecalendar_mapped_id: Mapped["ScheduleCalendar"] = mapped_column(ForeignKey("schedule_calendar.id"))
    schedule_id: Mapped[int]
    order_number: Mapped[int]  # = relationship(back_populates="order_number")
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    schedule_mapped_id: Mapped["Orders"] = relationship(back_populates="schedule_id")

    def __repr__(self) -> str:
        return {
            "id": self.id,
            "schedule_id": self.schedule_id,
            "order_number": self.order_number,
        }


class TattooItems(Base):
    __tablename__ = "tattoo_items"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]]
    photos: Mapped[List["TattooItemPhoto"]] = relationship(
        back_populates="photo_id", cascade="all, delete-orphan"
    )
    price: Mapped[Optional[int]]
    colored: Mapped[Optional[str]]
    note: Mapped[Optional[str]]
    creator: Mapped[Optional[str]]

    def __repr__(self) -> str:
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "colored": self.colored,
            "note": self.note,
            "creator": self.creator,
        }

        """ return f"TattooItems(id={self.id!r}, \
            name={self.name!r},\
            price={self.price!r},\
            colored={self.colored!r},\
            note={self.note!r},\
            creator={self.creator!r})" """


class TattooItemPhoto(Base):
    __tablename__ = "tattoo_items_photo"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tattoo_item_id: Mapped[int] = mapped_column(ForeignKey("tattoo_items.id"))
    photo: Mapped[str]
    tattoo_item_name: Mapped[Optional[str]]
    photo_id: Mapped["TattooItems"] = relationship(back_populates="photos")

    def __repr__(self) -> str:
        return {
            "id": self.id,
            "tattoo_item_name": self.tattoo_item_name,
            "photo": self.photo,
        }
        # return f"TattooItemPhoto(id={self.id!r}, tattoo_item_name={self.tattoo_item_name!r}, photo={self.photo!r})"


""" Статусы заказа:
    Открыт — заказ был создан в базе данных, но ещё не был обработан.
    Обработан — оплата была получена.
    Выполнен — вся работа по заказу завершена.
    Отклонен — заказ отклонен админом.
    Отложен — заказ ещё не обработан, так как в нём содержатся товары, которых нет в наличии. Только для гифтбокса
    Аннулирован — заказ был отменён покупателем.
    Ожидает ответа — заказ был создан, когда покупатель оформил заявку на обратный ответ.
"""


class Orders(Base):
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    order_type: Mapped[
        str
    ]  # тип заказа - постоянное тату, переводное тату, эскиз, гифтбокс, сертификат
    order_name: Mapped[Optional[str]]  # = mapped_column(String(50))
    user_id: Mapped[
        str
    ] #  = mapped_column(ForeignKey("user_account.id")), user.from_id
    order_photo: Mapped[List["OrderPhoto"]] = relationship(
        back_populates="photo_id", cascade="all, delete-orphan"
    )
    tattoo_size: Mapped[Optional[str]]  # только для заказа тату - размер тату
    tattoo_note: Mapped[Optional[str]]  # только для заказа тату - описание тату
    order_note: Mapped[Optional[str]]
    order_state: Mapped[
        Optional[str]
    ]  # Открыт, Обработан, Выполнен, Отклонен, Отложен, Аннулирован, Ожидает ответа
    order_number: Mapped[Optional[str]]
    creation_date: Mapped[Optional[datetime]]
    price: Mapped[Optional[int]]
    check_document: Mapped[List["CheckDocument"]] = relationship(
        back_populates="doc_id"
    )
    username: Mapped[
        Optional[str]
    ]  #  = relationship(back_populates="name") # message.from_user.full_name
    schedule_id: Mapped[List["ScheduleCalendarItems"]] = relationship(
        back_populates="schedule_mapped_id", cascade="all, delete-orphan"
    )
    colored: Mapped[Optional[str]]
    # details_number: Mapped[Optional[int]]
    bodyplace: Mapped[Optional[str]]
    tattoo_place_photo: Mapped[List["TattooPlacePhoto"]] = relationship(
        back_populates="photo_id", cascade="all, delete-orphan"
    )  #
    tattoo_place_video_note: Mapped[List["TattooPlaceVideoNote"]] = \
        relationship(
            back_populates="video_id", cascade="all, delete-orphan"
        )  # только для заказа тату - видео записка тела тату
    tattoo_place_video: Mapped[List["TattooPlaceVideo"]] = relationship(
        back_populates="video_id", cascade="all, delete-orphan"
    )  # только для заказа тату - видео тела тату
    code: Mapped[Optional[str]]  # только для заказа сертификата - код сертификата

    def __repr__(self) -> dict:
        return {
            "order_number": self.order_number,
            "order_type": self.order_type,
            "order_name": self.order_name,
            "tattoo_size": self.tattoo_size,
            "price": self.price,
            "colored": self.colored,
            "bodyplace": self.bodyplace,
            "tattoo_note": self.tattoo_note,
            "creation_date": self.creation_date,
            "order_state": self.order_state,
            "order_note": self.order_note,
            "code": self.code,
        }


class OrderPhoto(Base):
    __tablename__ = "tattoo_photo"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id"))
    order_number: Mapped[
        Optional[int]
    ]  # Mapped["TattooOrders"]# = relationship(back_populates="tattoo_order_number")
    telegram_user_id: Mapped[
        Optional[int]
    ]  # = mapped_column(ForeignKey("user.id")) # message.from_id
    photo: Mapped[Optional[str]]
    photo_id: Mapped["Orders"] = relationship(back_populates="order_photo")

    def __repr__(self) -> dict:
        return {
            "id": self.id,
            "order_number": self.order_number,
            "photo": self.photo,
            "telegram_user_id": self.telegram_user_id,
        }


class TattooPlacePhoto(Base):
    __tablename__ = "tattoo_place_photo"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id"))
    order_number: Mapped[Optional[int]]
    telegram_user_id: Mapped[Optional[int]]
    photo: Mapped[Optional[str]]
    photo_id: Mapped["Orders"] = relationship(
        back_populates="tattoo_place_photo"
    )

    def __repr__(self) -> dict:
        return {
            "id": self.id,
            "order_number": self.order_number,
            "photo": self.photo,
            "telegram_user_id": self.telegram_user_id,
        }


class TattooPlaceVideoNote(Base):
    __tablename__ = "tattoo_place_video_note"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id")) 
    order_number: Mapped[
        Optional[int]
    ]  # Mapped["TattooOrders"] = relationship(back_populates="tattoo_order_number")
    telegram_user_id: Mapped[Optional[int]]  # = mapped_column(ForeignKey("user.id"))
    video: Mapped[Optional[str]]
    video_id: Mapped["Orders"] = relationship(
        back_populates="tattoo_place_video_note"
    )

    def __repr__(self) -> dict:
        return {
            "id": self.id,
            "order_number": self.order_number,
            "video": self.video,
            "telegram_user_id": self.telegram_user_id,
        }


class TattooPlaceVideo(Base):
    __tablename__ = "tattoo_place_video"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    order_number: Mapped[
        int
    ]  # Mapped["TattooOrders"] = relationship(back_populates="tattoo_order_number")
    telegram_user_id: Mapped[int]  # = mapped_column(ForeignKey("user.id"))
    video: Mapped[str]
    video_id: Mapped["Orders"] = relationship(
        back_populates="tattoo_place_video"
    )

    def __repr__(self) -> dict:
        return {
            "id": self.id,
            "order_number": self.order_number,
            "video": self.video,
            "telegram_user_id": self.telegram_user_id,
        }


class CheckDocument(Base):
    __tablename__ = "check_document"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[int]
    order_number_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    doc: Mapped[Optional[str]]
    doc_id: Mapped["Orders"] = relationship(back_populates="check_document")

    def __repr__(self) -> dict:
        return {
            "id": self.id,
            "order_number": self.order_number,
            "doc": self.doc,
        }


class OrderPriceList(Base):
    __tablename__ = "price_list"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[
        Optional[str]
    ]  # Типы прайс-листов: 1) постоянное тату, 2) эскиз, 3) гифтбокс 4) переводное тату
    min_size: Mapped[Optional[int]]
    max_size: Mapped[Optional[int]]
    price: Mapped[Optional[int]]

    def __repr__(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "min_size": self.min_size,
            "max_size": self.max_size,
            "price": self.price,
        }


class SchedulePhoto(Base):
    __tablename__ = "schedule_photo"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]]
    photo: Mapped[Optional[str]]

    def __repr__(self) -> dict:
        return {"id": self.id, "name": self.name, "photo": self.photo}


class CandleItems(Base):
    __tablename__ = "candle_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]]
    photo: Mapped[Optional[str]]
    price: Mapped[Optional[int]]
    note: Mapped[Optional[str]]
    quantity: Mapped[Optional[int]]

    def __repr__(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "photo": self.photo,
            "price": self.price,
            "note": self.note,
            "quantity": self.quantity,
        }


class SequinsItems(Base):
    __tablename__ = "sequins_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]]
    quantity: Mapped[Optional[int]]
    photo: Mapped[Optional[str]]
    price: Mapped[Optional[int]]

    def __repr__(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "quantity": self.quantity,
            "photo": self.photo,
            "price": self.price,
        }


class GiftboxItemsPhoto(Base):
    __tablename__ = "giftbox_item_photo"
    id: Mapped[int] = mapped_column(primary_key=True)
    giftbox_id: Mapped[int] = mapped_column(ForeignKey("giftbox_items.id"))
    photo: Mapped[Optional[str]]
    item_mapped_id: Mapped["GiftboxItems"] = relationship(
        back_populates="photo"
    )

    def __repr__(self) -> dict:
        return {"id": self.id, "photo": self.photo}


class GiftboxItems(Base):
    __tablename__ = "giftbox_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]]
    photo: Mapped[List["GiftboxItemsPhoto"]] = relationship(
        back_populates="item_mapped_id", cascade="all, delete-orphan"
    )
    price: Mapped[Optional[str]]
    giftbox_note: Mapped[Optional[str]]
    candle_id: Mapped[Optional[str]]
    tattoo_theme: Mapped[Optional[str]]
    tattoo_note: Mapped[Optional[str]]
    tattoo_quantity: Mapped[Optional[int]]
    sequins_id: Mapped[Optional[str]]  # Mapped["SequinsItems"] = relationship(back_populates= "type")
    # sequins_state : # Mapped["SequinsItems"] = relationship(back_populates= "state")

    def __repr__(self) -> dict:
        return {
            "id": self.id,
            "photo": self.photo,
            "price": self.price,
            "giftbox_note": self.giftbox_note,
            "tattoo_note": self.tattoo_note,
            "tattoo_quantity": self.tattoo_quantity,
            "sequins_id": self.sequins_id,
            "candle_id": self.candle_id,
        }


Base.metadata.create_all(engine)
# session = scoped_session(sessionmaker(bind=engine))
# Base.query = session.query_property()
