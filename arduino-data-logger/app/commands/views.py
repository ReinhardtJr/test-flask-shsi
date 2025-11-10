from . import commands_bp
from app.extensions import mongo

@commands_bp.cli.command('init_db')
def init_db():
    """ Creates a database """
    print(f"Create database")
    mongo.db.create_collection("dht22", timeseries={'timeField': 'timestamp', 'metaField': 'metadata', 'granularity': 'minutes' })