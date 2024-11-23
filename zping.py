from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    response_data = None
    user_id = ""

    if request.method == "POST":
        user_id = request.form.get("user_id", "")
        url = "https://shop.garena.my/api/auth/player_id_login"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "app_id": 100067,
            "login_id": user_id
        }

        try:
            response = requests.post(url, json=payload, headers=headers, verify=False)
            response_data = response.json()
        except Exception as e:
            response_data = {"error": str(e)}

    return render_template("index.html", user_id=user_id, response_data=response_data)

if __name__ == "__main__":
    app.run(debug=True)
