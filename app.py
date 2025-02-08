from flask import Flask, request, jsonify
from latex2html.latex2html import convert_latex_to_html

app = Flask(__name__)

@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return jsonify({"error": "请上传 LaTeX 文件"}), 400
    
    file = request.files["file"]
    format_type = request.form.get("format", "html")

    try:
        latex_content = file.read().decode("utf-8")

        if format_type == "html":
            converted_content = convert_latex_to_html(latex_content)
        else:
            converted_content = "功能还没写完！"

        return jsonify({"result": converted_content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
