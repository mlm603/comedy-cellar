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
import os
from signups import signup_email

app = Flask(__name__)


# CONFIG
# app.config.from_object(os.environ['APP_SETTINGS'])
if os.environ['FLASK_ENVIRONMENT'] == 'development':
	print("Using local PSQL db")
	app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/cellar_scraper'
else:
	print("Using heroku PSQL db")
	app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL = os.environ['DATABASE_URL']

# if sys.argv[1] == "staging":
# else:

db = SQLAlchemy(app)

# ---------------

db.init_app(app)

frequent_comedians = db.session.execute('''
											SELECT comedian_name
												, show_count
											FROM dim_comedian_stats
											ORDER BY show_count DESC
											LIMIT 10				
										''')

unique_comedians = db.session.execute('''
											SELECT DISTINCT comedian_name
											FROM dim_comedian_stats
											ORDER BY comedian_name ASC		
										''')

dry_spell_comedians = db.session.execute('''
											SELECT comedian_name
											  , last_show
											  , days_since_last_show
											FROM dim_comedian_stats
											WHERE comedian_name <> 'MORE TO BE ANNOUNCED'
											ORDER BY 3 desc
											LIMIT 10
										''')

summary_stats = db.session.execute('''
											SELECT comedian_name
												, previous_shows
												, upcoming_shows
												, most_recent_show_timestamp
											FROM dim_comedian_stats
										''')

day_of_week_stats = db.session.execute('''
											SELECT comedian_name
												, show_day_of_week
												, show_count
											FROM dim_comedian_dow_stats
										''')

upcoming_shows = db.session.execute('''
											SELECT *
											FROM dim_upcoming_shows
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

summary_stats = make_dict(summary_stats)

day_of_week_stats = make_dict(day_of_week_stats)

upcoming_shows = make_dict(upcoming_shows)

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
		signup_email(email, comedians)
	return render_template('home_page_index.html'
						, frequent_comedians=frequent_comedians_results
						, unique_comedians=unique_comedians_results
						, dry_spell_comedians=dry_spell_comedians
				)

@app.route('/trends', methods=['GET'])
def trends_index():
	return render_template('trends_index.html'
						, unique_comedians=unique_comedians_results
						, summary_stats=summary_stats
						, day_of_week_stats=day_of_week_stats
						, upcoming_shows=upcoming_shows
				)

@app.route('/unsubscribe', methods=['GET','POST'])
def unsubscribe():
	if request.method == 'POST':
		unsubscribed_timestamp = datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S.%f')
		unsubscribe_comeds = request.get_json()
		email = unsubscribe_comeds['email']
		comedians = unsubscribe_comeds['comedians']
		for comedian_name in comedians:
			statement = "UPDATE dim_subscriptions SET unsubscribed_timestamp = '" + unsubscribed_timestamp + "' WHERE email = '" + email + "' AND comedian_name = '" + comedian_name + "'; "
			print(statement)
			db.session.execute(statement)
			db.session.commit()
		return redirect(url_for('unsubscribe_success'))
	else:
		email = request.args.get('email')
		# gets the subscriptions for the email address in the URL
		subscriptions = db.session.execute('''
												SELECT DISTINCT comedian_name
												FROM dim_subscriptions
												WHERE unsubscribed_timestamp IS NULL
													AND email =
											'''
											+ "'" + email + "'")
		subscriptions = make_dict(subscriptions)
		return render_template('unsubscribe.html'
							, email=email
							, subscriptions=subscriptions
					)

if __name__ == '__main__':
	app.run(host=os.getenv('IP', '0.0.0.0'), 
            port=int(os.getenv('PORT', 4444)),
            debug=True
            )

@app.route('/unsubscribe_success', methods=['GET'])
def unsubscribe_success():
	return render_template('unsubscribe_success.html')