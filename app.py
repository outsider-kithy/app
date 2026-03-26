from flask import Flask, render_template, request, send_file
from flask_httpauth import HTTPBasicAuth
import json
import subprocess
import os
import zipfile
import tempfile
from playwright.sync_api import sync_playwright
from PIL import Image
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")
STATIC_URL = os.getenv("STATIC_URL")
STATIC_PATH = os.getenv("STATIC_PATH")

app = Flask(__name__)

# BASIC認証
auth = HTTPBasicAuth()

def load_users():
    with open("users.json", "r", encoding="utf-8") as f:
        return json.load(f)

users = load_users()

@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None

@app.route("/")
@auth.login_required
def index():
    DEPLOY_DIR = request.args.get("deploy_dir")
    DEPLOY_URL = f"{STATIC_URL}/{DEPLOY_DIR}"
    REPOSITORY_DIR = DEPLOY_DIR.partition("/")[0]
    return render_template("index.html", deploy_url=DEPLOY_URL, repository_dir=REPOSITORY_DIR)

# @app.route("/deploy", methods=["POST"])
# def deploy():
#     REPOSITORY_DIR = request.args.get("repository_dir")
#     REPOSITORY_DIR_PATH = f"{STATIC_URL}/{REPOSITORY_DIR}"

#     try:
#         result = subprocess.run(
#             ["git", "ftp", "push", "-s", "pro"],
#             cwd=REPOSITORY_DIR_PATH,
#             capture_output=True,
#             text=True
#         )

#         return jsonify({
#             "success": result.returncode == 0,
#             "stdout": result.stdout,
#             "stderr": result.stderr
#         })

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@app.route("/download_diff", methods=["POST"])
@auth.login_required
def download_diff():
    REPOSITORY_DIR = request.args.get("repository_dir")
    REPOSITORY_DIR_PATH = f"{STATIC_PATH}/{REPOSITORY_DIR}"

    try:
        # ① 差分ファイル取得
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            cwd=REPOSITORY_DIR_PATH,
            capture_output=True,
            text=True
        )

        files = result.stdout.strip().split("\n")

        # ② 一時ディレクトリ作成
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "diff.zip")

        # ③ zip作成
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for file in files:
                file_path = os.path.join(REPOSITORY_DIR_PATH, file)

                if os.path.exists(file_path):
                    zipf.write(file_path, arcname=file)

        # ④ ダウンロード
        return send_file(zip_path, as_attachment=True)

    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/download_pdf", methods=["POST"])
@auth.login_required
def download_pdf():

    # 一時ファイル
    temp_dir = tempfile.mkdtemp()
    img_path = os.path.join(temp_dir, "screenshot.jpg")
    pdf_path = os.path.join(temp_dir, "output.pdf")

    try:
        # ① スクリーンショット
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page()
            page.goto("/")
            page.screenshot(path=img_path, full_page=True, type="jpeg", quality=90)

            browser.close()

        # ② JPG → PDF
        image = Image.open(img_path).convert("RGB")
        image.save(pdf_path, "PDF")

        # ③ ダウンロード
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)