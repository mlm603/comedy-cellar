from flask import Flask, render_template, redirect, url_for, request, session, flash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import os
import sqlalchemy
from sqlalchemy import create_engine, MetaData, select, Table
from flask import jsonify
import json

app = Flask(__name__)


# CONFIG
# app.config.from_object(os.environ['APP_SETTINGS'])

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/mlm603'

db = SQLAlchemy(app)

# ---------------

db.init_app(app)

frequent_comedians = db.session.execute('''
											SELECT comedian_name
												, count(*)::integer AS show_count
											FROM dim_shows
											GROUP BY comedian_name
											ORDER BY count(*) DESC
											LIMIT 10				
										''')

unique_comedians = db.session.execute('''
											SELECT DISTINCT comedian_name
											FROM dim_shows
											ORDER BY comedian_name ASC		
										''')

# frequent_comedians_results = []

def make_dict(result):
  # If no rows were returned (e.g., an UPDATE or DELETE), return an empty list
	if result.returns_rows == False:
	  return []
	# Convert the response to a plain list of dicts
	else: 
		return [dict(row.items()) for row in result]


frequent_comedians_results = make_dict(frequent_comedians)

unique_comedians_results = make_dict(unique_comedians)

@app.route('/')
def index():
	# shows = dim_shows.query.all()
	return render_template('index.html', frequent_comedians=frequent_comedians_results, unique_comedians=unique_comedians_results)

if __name__ == '__main__':
	app.run(host=os.getenv('IP', '0.0.0.0'), 
            port=int(os.getenv('PORT', 4444)),
            debug=True)