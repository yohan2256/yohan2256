"""server/models.py – SQLAlchemy 데이터 모델"""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class NoiseRecord(db.Model):
    __tablename__ = "noise_records"

    id          = db.Column(db.Integer,  primary_key=True)
    node_id     = db.Column(db.Integer,  nullable=False, index=True)
    db_avg      = db.Column(db.Float,    nullable=False)
    db_max      = db.Column(db.Float,    nullable=False)
    db_min      = db.Column(db.Float,    nullable=False)
    seq         = db.Column(db.Integer,  nullable=False)
    rssi        = db.Column(db.Integer,  default=0)
    received_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    created_at  = db.Column(db.DateTime(timezone=True),
                            default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id":          self.id,
            "node_id":     self.node_id,
            "db_avg":      self.db_avg,
            "db_max":      self.db_max,
            "db_min":      self.db_min,
            "seq":         self.seq,
            "rssi":        self.rssi,
            "received_at": self.received_at.isoformat() if self.received_at else None,
        }


class Node(db.Model):
    __tablename__ = "nodes"

    id          = db.Column(db.Integer, primary_key=True)
    node_id     = db.Column(db.Integer, unique=True, nullable=False)
    name        = db.Column(db.String(64), default="")
    location    = db.Column(db.String(128), default="")
    active      = db.Column(db.Boolean, default=True)
    last_seen   = db.Column(db.DateTime(timezone=True))

    def to_dict(self):
        return {
            "id":        self.id,
            "node_id":   self.node_id,
            "name":      self.name,
            "location":  self.location,
            "active":    self.active,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }
