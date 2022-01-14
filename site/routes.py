import json
import json_log_formatter
import logging
import os
import pytz
import sys

from datetime import datetime
from flask import Flask, jsonify, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy

from signups import signup_email

app = Flask(__name__)


# CONFIG
# app.config.from_object(os.environ['APP_SETTINGS'])
if os.environ['FLASK_ENVIRONMENT'] == 'development':
	print("Using local PSQL db")
	app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/cellar_scraper'
else:
	print("Using heroku PSQL db")
	app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False;

# if sys.argv[1] == "staging":
# else:

db = SQLAlchemy(app)

# ---------------

db.init_app(app)

formatter = json_log_formatter.JSONFormatter()
json_handler = logging.StreamHandler(sys.stdout)
json_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(json_handler)
logger.setLevel(logging.INFO)

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

total_comedians = db.session.execute('''
											SELECT COUNT(DISTINCT comedian_name) AS total_comedians
											FROM dim_comedian_stats
										''')

total_upcoming_shows = db.session.execute('''
											SELECT COUNT(DISTINCT showtime_id) AS total_upcoming_shows
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

summary_stats = make_dict(summary_stats)

day_of_week_stats = make_dict(day_of_week_stats)

upcoming_shows = make_dict(upcoming_shows)

total_comedians = make_dict(total_comedians)

total_upcoming_shows = make_dict(total_upcoming_shows)

@app.route('/', methods=['GET','POST'])
def index():
	if request.method == 'POST':
		signup_timestamp = datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S.%f')
		subscription = request.get_json()
		email = subscription['email']
		comedians = subscription['comedians']
		logger.info('%s added a new subscription!', email, extra={'email': email, 'subscription_type': 'new'})
		for comedian_name in comedians:
			statement = "INSERT INTO dim_subscriptions VALUES('" + email + "', '" + comedian_name + "', '" + signup_timestamp + "')"
			db.session.execute(statement)
			db.session.commit()
		signup_email(email, comedians)
	return render_template('home_page_index.html'
						, frequent_comedians=frequent_comedians_results
						, unique_comedians=unique_comedians_results
						, total_comedians=total_comedians
						, total_upcoming_shows=total_upcoming_shows
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
		logger.info('%s unsubscribed', email, extra={'email': email, 'subscription_type': 'unsubscribe'})
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