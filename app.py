from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow CORS for all domains, adjust if necessary

# Set up MongoDB connection
client = MongoClient('mongodb://localhost:27017')
db = client['webhook_db']
events = db['events']

@app.route('/webhook', methods=['POST'])
def github_webhook():
    payload = request.json
    event_type = request.headers.get('X-GitHub-Event')
    event_data = {}

    # Handle "Push" event
    if event_type == "push":
        event_data = {
            "author": payload['pusher']['name'],
            "to_branch": payload['ref'].split('/')[-1],  # Extract the branch name from the ref
            "event_type": "push",
            "message": f"{payload['pusher']['name']} pushed to {payload['ref'].split('/')[-1]}",
            "timestamp": datetime.utcnow()
        }

    # Handle "Pull Request" event
    elif event_type == "pull_request":
        pr_action = payload['action']
        # Handle both opening and merging
        if pr_action == "opened":
            event_data = {
                "author": payload['pull_request']['user']['login'],
                "from_branch": payload['pull_request']['head']['ref'],
                "to_branch": payload['pull_request']['base']['ref'],
                "event_type": "pull_request",
                "message": f"{payload['pull_request']['user']['login']} submitted a pull request from {payload['pull_request']['head']['ref']} to {payload['pull_request']['base']['ref']}",
                "timestamp": datetime.utcnow()
            }
        elif pr_action == "closed" and payload['pull_request']['merged']:
            event_data = {
                "author": payload['pull_request']['user']['login'],
                "from_branch": payload['pull_request']['head']['ref'],
                "to_branch": payload['pull_request']['base']['ref'],
                "event_type": "merge",
                "message": f"{payload['pull_request']['user']['login']} merged branch {payload['pull_request']['head']['ref']} to {payload['pull_request']['base']['ref']}",
                "timestamp": datetime.utcnow()
            }

    # Store event data in MongoDB
    if event_data:
        events.insert_one(event_data)
        return jsonify({"message": "Event received and processed!"}), 200
    else:
        return jsonify({"error": "Unrecognized event type or action."}), 400


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/events', methods=['GET'])
def get_events():
    all_events = list(events.find().sort("timestamp", -1))  # Sort by latest timestamp
    for event in all_events:
        event['_id'] = str(event['_id'])  # Convert ObjectId to string for the frontend
    return jsonify(all_events)


from gevent.pywsgi import WSGIServer

if __name__ == '__main__':
    app.run(debug=True, port=5000)


