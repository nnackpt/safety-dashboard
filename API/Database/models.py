from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from Database.database import Base

class EmailMaster(Base):
    __tablename__ = "sys_EmailMaster"
    __table_args__ = {'schema': 'dbo'}
    
    EmailID = Column(Integer, primary_key=True, autoincrement=True)
    EmailAddress = Column(String(255), nullable=False)
    Name = Column(String(255))
    Role = Column(String(100))
    IsActive = Column(Boolean, default=True)

class RuleMaster(Base):
    __tablename__ = "ppe_RuleMaster"
    __table_args__ = {'schema': 'dbo'}
    
    RuleID = Column(Integer, primary_key=True, autoincrement=True)
    RuleName = Column(String(255), nullable=False)
    RuleDescription = Column(Text)
    IsRequired = Column(Boolean, default=True)
    Status = Column(String(50))
    
    tickets = relationship("NGTicket", back_populates="rule")

class NGTicket(Base):
    __tablename__ = "ppe_NGTicket"
    __table_args__ = {'schema': 'dbo'}
    
    TicketID = Column(Integer, primary_key=True, autoincrement=True)
    DetectedTime = Column(DateTime, default=datetime.now)
    Location = Column(String(255))
    RuleID = Column(Integer, ForeignKey('dbo.ppe_RuleMaster.RuleID'))
    Severity = Column(String(50))
    Status = Column(String(50))
    NotifiedEmail = Column(String(500))
    CreatedBy = Column(String(255))
    CreatedAt = Column(DateTime, default=datetime.now)
    
    rule = relationship("RuleMaster", back_populates="tickets")
    evidences = relationship("NGEvidence", back_populates="ticket")

class NGEvidence(Base):
    __tablename__ = "ppe_NGEvidence"
    __table_args__ = {'schema': 'dbo'}
    
    EvidenceID = Column(Integer, primary_key=True, autoincrement=True)
    TicketID = Column(Integer, ForeignKey('dbo.ppe_NGTicket.TicketID'))
    FilePath = Column(String(500))
    FileType = Column(String(50))
    CreatedAt = Column(DateTime, default=datetime.now)
    
    ticket = relationship("NGTicket", back_populates="evidences")