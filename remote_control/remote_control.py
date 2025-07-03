from flask import Flask, request, render_template_string
import pyautogui
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Remote Control</title>
</head>
<body>
    <h2>Remote Control for PC</h2>
    <form method="POST" action="/type">
        <input name="text" placeholder="Type text on PC" />
        <button type="submit">Type</button>
    </form>
    <form method="POST" action="/command">
        <input name="cmd" placeholder="Run shell command" />
        <button type="submit">Run</button>
    </form>
    <form method="POST" action="/mouse">
        <button name="move" value="left">Left</button>
        <button name="move" value="right">Right</button>
        <button name="move" value="up">Up</button>
        <button name="move" value="down">Down</button>
    </form>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)

@app.route("/type", methods=["POST"])
def type_text():
    text = request.form.get("text", "")
    pyautogui.typewrite(text)
    return "Typed: " + text + "<br><a href='/'>Back</a>"

@app.route("/command", methods=["POST"])
def run_command():
    cmd = request.form.get("cmd", "")
    output = os.popen(cmd).read()
    return f"Command: {cmd}<br>Output:<pre>{output}</pre><br><a href='/'>Back</a>"

@app.route("/mouse", methods=["POST"])
def move_mouse():
    move = request.form.get("move")
    x, y = pyautogui.position()
    if move == "left":
        pyautogui.moveTo(x-50, y)
    elif move == "right":
        pyautogui.moveTo(x+50, y)
    elif move == "up":
        pyautogui.moveTo(x, y-50)
    elif move == "down":
        pyautogui.moveTo(x, y+50)
    return f"Moved mouse {move}.<br><a href='/'>Back</a>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000) 