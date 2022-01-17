import pandas as pd
import os
import psycopg2
import sys


"""

This file can be used when fact_shows gets messed up and we need to regenerate it based on the snapshots

Dedupe fact_shows by running the code below
ALTER TABLE fact_shows ADD COLUMN id SERIAL PRIMARY KEY;
delete
from fact_shows
using (
    select snapshot_timestamp
        , showtime_id
        , comedian_name
        , id
        , row_number() over (partition by snapshot_timestamp, showtime_id, comedian_name order by id) as r
    from fact_shows
) ranked_shows
where fact_shows.snapshot_timestamp = ranked_shows.snapshot_timestamp
    and fact_shows.showtime_id = ranked_shows.showtime_id
    and fact_shows.comedian_name = ranked_shows.comedian_name
    and fact_shows.id = ranked_shows.id
    and r > 1;
ALTER TABLE fact_shows DROP COLUMN id;

Apply is_most_recent_snapshot with the code below
with agg_shows as (
    select showtime_id
        , max(snapshot_timestamp) as mr_snapshot
    from fact_shows
    group by showtime_id
)

update fact_shows
set is_most_recent_snapshot = true
from agg_shows
where fact_shows.snapshot_timestamp = agg_shows.mr_snapshot
    and fact_shows.showtime_id = agg_shows.showtime_id;

with agg_shows as (
    select showtime_id
        , max(snapshot_timestamp) as mr_snapshot
    from fact_shows
    group by showtime_id
)

update fact_shows
set is_most_recent_snapshot = false
from agg_shows
where fact_shows.snapshot_timestamp <> agg_shows.mr_snapshot
    and fact_shows.showtime_id = agg_shows.showtime_id;

"""


pd.set_option('mode.chained_assignment', None)

LOCAL_DATABASE_URL = "postgresql://localhost/cellar_scraper"

local_conn = psycopg2.connect(LOCAL_DATABASE_URL)
local_cursor = local_conn.cursor()

directory = 'fact_shows'

for filename in os.listdir(directory):
    if filename != ".DS_Store":
        filepath = 'fact_shows/' + filename
        
        # copy the CSV to the local fact_shows table
        sys.stdin = open(filepath)
        local_cursor.copy_expert("COPY fact_shows FROM STDIN WITH (FORMAT CSV)", sys.stdin)

        local_conn.commit()

        print("added file ", filename)

local_cursor.close()
local_conn.close()



