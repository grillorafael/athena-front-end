import datetime as dt
import re
import json
from flask import request


def utc_time_datetime_format(since_time_delta):
    return dt.datetime.utcnow() + dt.timedelta(int(since_time_delta))


def find_key(array_to_be_find, keys):
    for key in keys:
        if not any(d['status'] is key or d['status'] == key for d in array_to_be_find):
            array_to_be_find.append({'count': 0, 'status': key})


def start_day_string_time():
    return dt.datetime.strptime(request.args.get("startDate"), '%Y-%m-%d')


def end_date_string_time():
    return dt.datetime.strptime(request.args.get("endDate"), '%Y-%m-%d') + dt.timedelta(seconds=86399)


def fill_all_dates(day_in_range, collection_count_list):
    day = {}
    for y in collection_count_list:
        if y.get('date') == day_in_range:
            day['day'] = str(y.get('date').strftime('%a %d-%b'))
            day['count'] = int(y.get('count'))
            return day
    day['day'] = day_in_range.strftime('%a %d-%b')
    day['count'] = 0
    return day


def accumulator(days):
    value_accumulated = 0
    for day in days:
        if day["count"] > 0:
            value_accumulated += day["count"]
            day["count"] = value_accumulated
        else:
            day["count"] = value_accumulated
    return days


def process_data(db, db_collection, db_query, days_delta, start_date):
    count_list = db[db_collection].aggregate(db_query)
    count_list = [dict(i) for i in count_list]
    for count in count_list:
        count['date'] = dt.datetime(count['year'], count['month'], count['day'], 0, 0)
    range_days = [start_date + dt.timedelta(days=i) for i in range(days_delta.days + 1)]
    processed_list = [fill_all_dates(day, count_list) for day in range_days]
    return processed_list


def process_issues(db, db_collection, delta, start_date, created, closed):
    created_issues_list = process_data(db, db_collection, created, delta, start_date)
    created_issues_list = accumulator(created_issues_list)
    closed_issues_list = process_data(db, db_collection, closed, delta, start_date)
    closed_issues_list = accumulator(closed_issues_list)
    return json.dumps([closed_issues_list, created_issues_list])


def name_regex_search(db, collection_name, document_name):
    name = "^" + str(request.args.get("name"))
    compiled_name = re.compile(r'%s' % name, re.I)
    query_result = db[collection_name].find({document_name: {'$regex': compiled_name}},
                                            {'_id': 0, document_name: 1}).limit(6)
    result = [dict(i) for i in query_result]
    if not query_result:
        return json.dumps([{'response': 404}])
    return json.dumps(result)


def name_and_org_regex_search(db, collection_name, document_name):
    org = str(request.args.get("org"))
    db_last_updated = dt.datetime.utcnow() + dt.timedelta(hours=-5)
    name = "^" + str(request.args.get("name"))
    compiled_name = re.compile(r'%s' % name, re.I)
    query_result = db[collection_name].find({'org': org,'db_last_updated': {'$gte': db_last_updated},
                                             document_name: {'$regex': compiled_name}},
                                            {'_id': 0, document_name: 1}).limit(6)
    result = [dict(i) for i in query_result]
    if not query_result:
        return json.dumps([{'response': 404}])
    return json.dumps(result)


def last_updated_at(query):
    return round((dt.datetime.utcnow() - query).total_seconds() / 60)


