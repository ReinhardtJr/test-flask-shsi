from . import api_bp
from flask import jsonify, request, send_file, current_app, Response
import datetime
import csv
from io import BytesIO
from app.extensions import mongo

@api_bp.post('/sensors')
def add_sensor_reads():
    dht22 = request.get_json()

    sensor_id = dht22['sensor_id']
    temperature_in_c = dht22['temperature_in_c']
    temperature_in_f = dht22['temperature_in_f']
    humidity = dht22['humidity']
    heat_index_in_c = dht22['heat_index_in_c']
    heat_index_in_f = dht22['heat_index_in_f']
    
    current_app.logger.info(f"dht22 : {dht22}")
    
    dht22 = {
        "timestamp": datetime.datetime.now(),
        "metadata": {"sensor_id": sensor_id},
        "temperature_in_c": temperature_in_c,
        "temperature_in_f": temperature_in_f,
        "humidity": humidity,
        "heat_index_in_c": heat_index_in_c,
        "heat_index_in_f": heat_index_in_f
    }
    
    mongo.db.dht22.insert_one(dht22)
    
    return jsonify({"Status": "OK", "Message": "Successfully saved sensor records!"})


@api_bp.get('/latest')
def get_latest_reading():
    latest_doc = mongo.db.dht22.find_one(sort=[("_id", -1)])

    if not latest_doc:
        return jsonify({"error": "No data found"}), 404

    result = {
        "timestamp": latest_doc["timestamp"].isoformat() if "timestamp" in latest_doc else None,
        "temperature_in_c": latest_doc.get("temperature_in_c"),
        "temperature_in_f": latest_doc.get("temperature_in_f"),
        "humidity": latest_doc.get("humidity"),
        "heat_index_in_c": latest_doc.get("heat_index_in_c"),
        "heat_index_in_f": latest_doc.get("heat_index_in_f")
    }

    return jsonify(result)


@api_bp.get('/history')
def get_history():
    range_map = {
        "1h": datetime.timedelta(hours=1),
        "1d": datetime.timedelta(days=1),
        "3d": datetime.timedelta(days=3),
        "7d": datetime.timedelta(days=7),
        "1m": datetime.timedelta(days=30),
        "3m": datetime.timedelta(days=90),
        "6m": datetime.timedelta(days=180),
        "1y": datetime.timedelta(days=365)
    }

    range_key = request.args.get("range", "1d")
    time_limit = datetime.datetime.now() - range_map.get(range_key, datetime.timedelta(days=1))

    cursor = mongo.db.dht22.find(
        {"timestamp": {"$gte": time_limit}}
    ).sort("timestamp", 1)

    data = [
        {
            "timestamp": doc["timestamp"].isoformat(),
            "temperature_in_c": doc["temperature_in_c"],
            "humidity": doc["humidity"]
        } for doc in cursor
    ]

    return jsonify(data)

@api_bp.get('/export')
def export_data():
    """
    Export DHT22 data to CSV for a given time range (same as /history)
    Supports: 1h, 1d, 3d, 7d, 1m, 3m, 6m, 1y
    """
    try:
        range_map = {
            "1h": datetime.timedelta(hours=1),
            "1d": datetime.timedelta(days=1),
            "3d": datetime.timedelta(days=3),
            "7d": datetime.timedelta(days=7),
            "1m": datetime.timedelta(days=30),
            "3m": datetime.timedelta(days=90),
            "6m": datetime.timedelta(days=180),
            "1y": datetime.timedelta(days=365)
        }

        range_key = request.args.get("range", "1d")
        time_limit = datetime.datetime.now() - range_map.get(range_key, datetime.timedelta(days=1))
        cursor = mongo.db.dht22.find({"timestamp": {"$gte": time_limit}}).sort("timestamp", 1)

        def generate():
            """Stream CSV rows as they’re read from MongoDB."""
            header = ["timestamp", "temperature_in_c", "temperature_in_f", "humidity", "heat_index_in_c", "heat_index_in_f"]
            yield ','.join(header) + '\n'

            for doc in cursor:
                ts = doc.get("timestamp").isoformat() if doc.get("timestamp") else ""
                row = [
                    ts,
                    str(doc.get("temperature_in_c", "")),
                    str(doc.get("temperature_in_f", "")),
                    str(doc.get("humidity", "")),
                    str(doc.get("heat_index_in_c", "")),
                    str(doc.get("heat_index_in_f", "")),
                ]
                yield ','.join(row) + '\n'

        filename = f"export_{range_key}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/csv",
        }

        return Response(generate(), headers=headers)

    except Exception as e:
        current_app.logger.exception("Failed to export CSV")
        return jsonify({"error": True, "message": "Failed to export data"}), 500
