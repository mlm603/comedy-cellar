from flask import Flask, render_template, redirect, url_for, request, session, flash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import os
import sqlalchemy
from sqlalchemy import create_engine, MetaData, select, Table
from flask import jsonify
from datetime import datetime
import pytz
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

dry_spell_comedians = db.session.execute('''
											SELECT comedian_name
											  , MAX(show_timestamp) AS last_show
											  , DATE_PART('day', NOW() - MAX(show_timestamp)) AS days_since_last_show
											FROM dim_shows 
											WHERE comedian_name <> 'MORE TO BE ANNOUNCED'
											GROUP BY 1 
											ORDER BY 3 desc
											LIMIT 10;
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

dry_spell_comedians = make_dict(dry_spell_comedians)

@app.route('/', methods=['GET','POST'])
def index():
	if request.method == 'POST':
		signup_timestamp = datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S.%f')
		subscription = request.get_json()
		email = subscription['email']
		comedians = subscription['comedians']
		for comedian_name in comedians:
			statement = "INSERT INTO dim_subscriptions VALUES('" + email + "', '" + comedian_name + "', '" + signup_timestamp + "')"
			db.session.execute(statement)
			db.session.commit()
	return render_template('home_page_index.html'
						, frequent_comedians=frequent_comedians_results
						, unique_comedians=unique_comedians_results
						, dry_spell_comedians=dry_spell_comedians
				)

if __name__ == '__main__':
	app.run(host=os.getenv('IP', '0.0.0.0'), 
            port=int(os.getenv('PORT', 4444)),
            debug=True)