from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
from app.models.user import *
from app.models.trade import *
from  app.models.stock import *
from  app.models.index import *
from  app.models.fraud import *
from  app.models.forex import *
from  app.models.mbti import *