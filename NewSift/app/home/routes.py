# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from app.home import blueprint
from flask import render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from app import login_manager
from jinja2 import TemplateNotFound
import markdown
from pymongo import MongoClient, DESCENDING, ASCENDING
from bson import ObjectId
from bs4 import BeautifulSoup
import re

client = MongoClient("mongodb://localhost:27017/")
db = client["twitter_data"]

@blueprint.route('/index')
@login_required
def index():
    return redirect(url_for('home_blueprint.news_reports'))

priority_order = {
    "Critical": 1,
    "High Priority": 2,
    "Medium Priority": 3,
    "Low Priority": 4
}

def sort_priority(report):
    return priority_order[report["priority"]]

@blueprint.route('/news_reports')
@login_required
def news_reports():
    sort_by = request.args.get('sort', 'created_at_desc')

    if sort_by == "created_at_asc":
        news_reports = db.news_report.find().sort("created_at", ASCENDING)
    elif sort_by == "priority":
        news_reports = sorted(list(db.news_report.find()), key=sort_priority)
    else:
        news_reports = db.news_report.find().sort("created_at", DESCENDING)

    return render_template('news_reports.html', segment='news_reports', news_reports=news_reports, sort_by=sort_by)

@blueprint.route('/report_details/<report_id>')
@login_required
def report_details(report_id):
    report = db.news_report.find_one({"_id": ObjectId(report_id)})
    summary_html = markdown.markdown(report["summary"])
    
    soup = BeautifulSoup(summary_html, 'html.parser')
    first_tag = soup.find()
    first_tag.extract()
    summary_html = str(soup)

    locations  = db.tweet_filtered.distinct("ner.Location", {"topic_label": report["topic_label"]})
    report_status = db.topic_status_change.find_one({"topic_label": report["topic_label"]}, {"size": 1, "keywords": 1, "time": 1, "_id": 0})
    if report is None:
        abort(404)
    return render_template('report_details.html', segment='report_details', report=report, summary_html=summary_html, locations=locations, report_status=report_status)


def find_url(text):
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    urls = re.findall(url_pattern, text)
    return urls[0] if urls else None

@blueprint.route('/report_details/<report_id>/src', methods=['GET', 'POST'])
@login_required
def report_src(report_id):
    topic_label = db.news_report.find_one({"_id": ObjectId(report_id)})["topic_label"]
    title =   db.news_report.find_one({"_id": ObjectId(report_id)})["title"]
    tweets = db.tweet_filtered.find({"topic_label": topic_label})
    tweets_list = []

    for tweet in tweets:
        url = find_url(tweet['text'])
        if url:
            tweet['text'] = tweet['text'].replace(url, '').strip()
            tweet['url'] = url
        tweets_list.append(tweet)

    if not tweets_list:
        abort(404)
    return render_template('report_src.html', segment='report_src', tweets=tweets_list, title = title)

@blueprint.route('/report_details/<report_id>/feedback', methods=['POST'])
@login_required
def save_feedback(report_id):
    feedback = request.form.get('feedback')
    if feedback:
        db.report_feedback.insert_one({
            'report_id': ObjectId(report_id),
            'feedback': feedback
        })
        flash('Thank you for your feedback!', 'success')
    else:
        flash('Please provide some feedback before submitting.', 'danger')
    return redirect(url_for('home_blueprint.report_details', report_id=report_id))



@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith( '.html' ):
            template += '.html'

        # Detect the current page
        segment = get_segment( request )

        # Serve the file (if exists) from app/templates/FILE.html
        return render_template( template, segment=segment )

    except TemplateNotFound:
        return render_template('page-404.html'), 404
    
    except:
        return render_template('page-500.html'), 500

# Helper - Extract current page name from request 
def get_segment( request ): 

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment    

    except:
        return None  

'''
@blueprint.route('news_report')
@login_required
def news_report():
    md_string = "** A Series of Tragic Events: Lives Lost and Remembered**"

    html_string = markdown.markdown(md_string)
    return render_template('news_report.html', segment='news_report', html_string=html_string)
'''
