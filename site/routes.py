from flask import Flask, render_template, redirect, url_for, request, session, flash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import os
import sqlalchemy
from sqlalchemy import create_engine, MetaData, select, Table
import jsonify
import json

app = Flask(__name__)

# CONFIG
# app.config.from_object(os.environ['APP_SETTINGS'])

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://localhost/mlm603"

db = SQLAlchemy(app)

# ---------------

db.init_app(app)

result = db.session.execute("""
							SELECT id
								, show_timestamp::varchar(255)
								, location
								, comedian_name
								, comedian_description 
							FROM dim_shows
						""")

# If no rows were returned (e.g., an UPDATE or DELETE), return an empty list
if result.returns_rows == False:
    response = []

# Convert the response to a plain list of dicts
else:
    response = [dict(row.items()) for row in result]

# Output the query result as JSON
# print(json.dumps(response))
# ------------------------------

# class dim_shows(db.Model):
# 	__tablename__ = 'dim_shows'
# 	id = db.Column(db.Integer, primary_key = True)
# 	show_timestamp = db.Column(db.DateTime)
# 	location = db.Column(db.String(100))
# 	comedian_name = db.Column(db.String(100))
# 	comedian_description = db.Column(db.Text)

@app.route("/")
def index():
	# shows = dim_shows.query.all()
	return render_template("index.html", shows=response)

if __name__ == "__main__":
	app.run(host=os.getenv('IP', '0.0.0.0'), 
            port=int(os.getenv('PORT', 4444)),
            debug=True)