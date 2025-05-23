import pandas as pd
from flask import Flask, render_template, request
from main import generate_routes_and_map

app = Flask(__name__, template_folder="templates", static_folder="static")

# Load SCATS Nicknames once
scats_df = pd.read_csv("datasets/processed/SCATS_Nicknames.csv")  # adjust path if needed
scats_options = [
    {"id": int(row["SCATS Number"]), "name": f"{row['SCATS Number']} - {row['Nickname']}"}
    for _, row in scats_df.iterrows()
]

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        origin = int(request.form['origin'])
        destination = int(request.form['destination'])
        time_input = request.form['time']
        datetime_str = f"2006-10-31 {time_input}"
        routes, map_path = generate_routes_and_map(origin, destination, datetime_str)
        return render_template('result.html', routes=routes, map_path=map_path)

    return render_template('index.html', scats_options=scats_options)

if __name__ == '__main__':
    app.run(debug=True)
