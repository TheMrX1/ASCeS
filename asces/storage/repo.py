from sqlalchemy.orm import Session
from .models import Alert
from typing import List, Optional
from datetime import datetime

class AlertRepo:
    def __init__(self, session: Session):
        self.session = session

    def create_alert(self, alert_data: dict):
        alert = Alert(**alert_data)
        self.session.add(alert)
        self.session.commit()
        self.session.refresh(alert)
        return alert

    def get_alerts(self, limit: int = 100, level: Optional[str] = None):
        query = self.session.query(Alert).order_by(Alert.timestamp.desc())
        if level:
            query = query.filter(Alert.level == level)
        return query.limit(limit).all()
