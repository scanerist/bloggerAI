from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger
from sqlalchemy.orm import relationship, Mapped, mapped_column
from services.database.db import Base

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    source_channels : Mapped[list["SourceChannel"]] = relationship('SourceChannel', back_populates='user', cascade='all, delete-orphan')
    destination_channels : Mapped[list["DestinationChannel"]] = relationship('DestinationChannel', back_populates='user', cascade='all, delete-orphan')
    instructions: Mapped[list["Instruction"]] = relationship('Instruction', back_populates='user', cascade='all, delete-orphan')

class SourceChannel(Base):
    __tablename__ = 'source_channels'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_name: Mapped[str] = mapped_column(String, nullable=False)
    last_processed_message_id: Mapped[int] = mapped_column(Integer, default=None)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    user : Mapped[list["User"]] = relationship('User', back_populates='source_channels')

class DestinationChannel(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    __tablename__ = 'destination_channels'
    channel_name: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    user = relationship('User', back_populates='destination_channels')

class Instruction(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    __tablename__ = 'instructions'
    text: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    user = relationship('User', back_populates='instructions')

