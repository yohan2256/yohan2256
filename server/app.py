#!/usr/bin/env python3
"""
server/app.py  –  공사장 소음 모니터링 웹 서버 (Flask)

엔드포인트:
  POST /api/v1/noise          게이트웨이 → 소음 데이터 수신
  GET  /api/v1/noise          최근 레코드 조회 (JSON)
  GET  /api/v1/nodes          노드 목록
  GET  /api/v1/stats          노드별 통계
  GET  /                      대시보드 HTML
"""
import os
from datetime import datetime, timezone, timedelta

from flask import Flask, jsonify, request, render_template, abort
from flask_sqlalchemy import SQLAlchemy

from config import config
from models import db, NoiseRecord, Node


def create_app(env: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[env])

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route("/api/v1/noise", methods=["POST"])
    def ingest():
        data = request.get_json(force=True, silent=True)
        if not data:
            abort(400, "JSON 바디가 필요합니다.")

        required = ("node_id", "db_avg", "db_max", "db_min", "seq")
        missing = [k for k in required if k not in data]
        if missing:
            abort(400, f"필드 누락: {missing}")

        try:
            received_at = (
                datetime.fromisoformat(data["received_at"])
                if "received_at" in data
                else datetime.now(timezone.utc)
            )
        except ValueError:
            received_at = datetime.now(timezone.utc)

        record = NoiseRecord(
            node_id     = int(data["node_id"]),
            db_avg      = float(data["db_avg"]),
            db_max      = float(data["db_max"]),
            db_min      = float(data["db_min"]),
            seq         = int(data["seq"]),
            rssi        = int(data.get("rssi", 0)),
            received_at = received_at,
        )
        db.session.add(record)

        node = Node.query.filter_by(node_id=record.node_id).first()
        if node is None:
            node = Node(node_id=record.node_id,
                        name=f"Node-{record.node_id:02X}",
                        location="미등록")
            db.session.add(node)
        node.last_seen = received_at
        db.session.commit()

        cfg = app.config
        hour = received_at.hour
        if 7 <= hour < 18:
            limit = cfg["NOISE_ALERT_DAY"]
        elif 18 <= hour < 22:
            limit = cfg["NOISE_ALERT_EVENING"]
        else:
            limit = cfg["NOISE_ALERT_NIGHT"]

        if record.db_avg > limit:
            app.logger.warning(
                "[경고] Node %d: %.1f dB > 기준 %.1f dB",
                record.node_id, record.db_avg, limit
            )

        return jsonify(record.to_dict()), 201

    @app.route("/api/v1/noise", methods=["GET"])
    def get_noise():
        node_id  = request.args.get("node_id",  type=int)
        hours    = request.args.get("hours",    type=int, default=1)
        limit    = request.args.get("limit",    type=int,
                                    default=app.config["PAGE_SIZE"])

        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        q = NoiseRecord.query.filter(NoiseRecord.received_at >= since)
        if node_id is not None:
            q = q.filter_by(node_id=node_id)
        records = (q.order_by(NoiseRecord.received_at.desc())
                    .limit(limit)
                    .all())
        return jsonify([r.to_dict() for r in records])

    @app.route("/api/v1/nodes", methods=["GET"])
    def get_nodes():
        nodes = Node.query.order_by(Node.node_id).all()
        return jsonify([n.to_dict() for n in nodes])

    @app.route("/api/v1/stats", methods=["GET"])
    def get_stats():
        hours = request.args.get("hours", type=int, default=1)
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        rows = (
            db.session.query(
                NoiseRecord.node_id,
                db.func.avg(NoiseRecord.db_avg).label("avg"),
                db.func.max(NoiseRecord.db_max).label("max"),
                db.func.min(NoiseRecord.db_min).label("min"),
                db.func.count(NoiseRecord.id).label("count"),
            )
            .filter(NoiseRecord.received_at >= since)
            .group_by(NoiseRecord.node_id)
            .all()
        )

        return jsonify([
            {"node_id": r.node_id, "avg": round(r.avg, 1),
             "max": round(r.max, 1), "min": round(r.min, 1), "count": r.count}
            for r in rows
        ])

    @app.route("/")
    def dashboard():
        return render_template("dashboard.html")

    return app


if __name__ == "__main__":
    env = os.environ.get("FLASK_ENV", "development")
    app = create_app(env)
    app.run(host="0.0.0.0", port=5000, debug=(env == "development"))
