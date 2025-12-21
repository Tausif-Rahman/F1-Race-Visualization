from flask import Flask, jsonify, render_template
from flask_cors import CORS
import sys
import os

# Add project root to path to import from src
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import the load_race_data function
from src.data_loader import load_race_data
import fastf1 as ff1
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # Enable CORS for local development

@app.route('/api/race/<int:year>/<int:race_num>/<int:num_laps>')
def get_race_data(year, race_num, num_laps):
    """Get race data for visualization"""
    try:
        drivers, max_laps, event_info = load_race_data(year, race_num, num_laps)
        
        # Convert data to JSON-serializable format
        serialized_drivers = []
        for driver in drivers:
            serialized_laps = {}
            for lap_num, lap_data in driver['laps'].items():
                # Convert DataFrame to list of dicts
                laps_list = []
                for _, row in lap_data.iterrows():
                    # Convert Time (timedelta) to milliseconds if needed
                    time_val = row['Time']
                    if hasattr(time_val, 'total_seconds'):
                        time_ms = int(time_val.total_seconds() * 1000)
                    else:
                        time_ms = int(time_val)
                    
                    laps_list.append({
                        'X': float(row['X']),
                        'Y': float(row['Y']),
                        'Time': time_ms
                    })
                serialized_laps[str(lap_num)] = laps_list
            
            serialized_drivers.append({
                'code': driver['code'],
                'abbr': driver['abbr'],
                'team': driver['team'],
                'color': driver['color'],
                'laps': serialized_laps,
                'lap_times': {str(k): float(v) for k, v in driver['lap_times'].items()}
            })
        
        return jsonify({
            'drivers': serialized_drivers,
            'max_laps': max_laps,
            'event_info': event_info
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

@app.route('/')
def index():
    """Serve the visualization page"""
    return render_template('index.html')

@app.route('/api/season/<int:year>')
def season_info(year: int):
    """Return season schedule info: max round and current round."""
    try:
        schedule = ff1.get_event_schedule(year)
        # Ensure EventDate is datetime
        today = datetime.utcnow().date()
        schedule_dates = schedule["EventDate"].dt.date if hasattr(schedule["EventDate"], 'dt') else schedule["EventDate"]
        # Max round number in schedule
        max_round = int(schedule["RoundNumber"].max()) if "RoundNumber" in schedule.columns else int(len(schedule))
        # Current round = latest round whose date <= today
        past_events = schedule[schedule_dates <= today]
        current_round = int(past_events["RoundNumber"].max()) if len(past_events) and "RoundNumber" in past_events.columns else 1
        return jsonify({
            'year': year,
            'max_round': max_round,
            'current_round': current_round
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting F1 Data API server...")
    print("API will be available at http://localhost:3000")
    app.run(host='127.0.0.1', port=3000, debug=False)
