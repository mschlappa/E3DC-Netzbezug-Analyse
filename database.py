import os
from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import streamlit as st

Base = declarative_base()

class EnergyData(Base):
    __tablename__ = 'energy_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    zeitstempel = Column(DateTime, unique=True, nullable=False, index=True)
    direktverbrauch = Column(Float, nullable=True)
    batterie_entladen = Column(Float, nullable=True)
    netzbezug = Column(Float, nullable=True)
    hausverbrauch = Column(Float, nullable=True)

@st.cache_resource
def get_database_engine():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine

def get_session():
    engine = get_database_engine()
    Session = sessionmaker(bind=engine)
    return Session()
