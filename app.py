import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "rpg_secret_launcher_key_2026")

GM_USERNAME = os.environ.get("GM_USERNAME", "admin")
GM_PASSWORD = os.environ.get("GM_PASSWORD", "rpgadmin123")

# 최신 빌드와 과거 빌드 이력을 누적 관리하는 구조로 고도화
app_data = {
    "current": {
        "version": "v3.3",
        "installer_id": "YOUR_INSTALLER_ZIP_DRIVE_ID",
        "update_id": "YOUR_UPDATE_ZIP_DRIVE_ID",
        "new_html": "game_v3.3.html"
    },
    # 과거 배포했던 구버전들이 쌓이는 공간
    "history": [
        {"version": "v3.2", "installer_id": "OLD_INSTALLER_ID_1", "update_id": "OLD_UPDATE_ID_1"},
        {"version": "v3.1", "installer_id": "OLD_INSTALLER_ID_2", "update_id": "OLD_UPDATE_ID_2"}
    ]
}

@app.route('/')
def index():
    return render_template('index.html', data=app_data)

@app.route('/download/<version>/<file_type>')
def download(version, file_type):
    file_id = None
    
    # 1. 현재 라이브 버전에서 찾는 경우
    if version == "current":
        if file_type == 'installer':
            file_id = app_data["current"]["installer_id"]
        elif file_type == 'updater':
            file_id = app_data["current"]["update_id"]
    # 2. 구버전 아카이브에서 찾는 경우
    else:
        for item in app_data["history"]:
            if item["version"] == version:
                if file_type == 'installer':
                    file_id = item["installer_id"]
                elif file_type == 'updater':
                    file_id = item["update_id"]
                break
                
    if not file_id or "DRIVE_ID" in str(file_id):
        return "등록된 구글 드라이브 파일 ID가 없거나 올바르지 않습니다.", 404
        
    direct_url = f"https://drive.google.com/uc?export=download&confirm=t&id={file_id}"
    return redirect(direct_url)

@app.route('/gm/login', methods=['GET', 'POST'])
def gm_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == GM_USERNAME and password == GM_PASSWORD:
            session['gm_logged_in'] = True
            return redirect(url_for('gm_dashboard'))
        return render_template('login.html', error="GM 계정 정보가 일치하지 않습니다.")
    return render_template('login.html')

@app.route('/gm/dashboard')
def gm_dashboard():
    if not session.get('gm_logged_in'):
        return redirect(url_for('gm_login'))
    return render_template('dashboard.html', data=app_data)

@app.route('/gm/deploy', methods=['POST'])
def gm_deploy():
    if not session.get('gm_logged_in'):
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    action = request.form.get('action')
    
    # [기능 1] 새 버전 릴리즈 (기존 버전은 히스토리로 자동 이동)
    if action == "release_new":
        old_current = app_data["current"].copy()
        
        app_data["current"] = {
            "version": request.form.get('current_version'),
            "installer_id": request.form.get('installer_id'),
            "update_id": request.form.get('update_id'),
            "new_html": request.form.get('new_html')
        }
        
        # 기존에 있던 최신 버전을 과거 히스토리 맨 앞으로 추가
        if old_current["version"] != app_data["current"]["version"]:
            app_data["history"].insert(0, {
                "version": old_current["version"],
                "installer_id": old_current["installer_id"],
                "update_id": old_current["update_id"]
            })
            
    # [기능 2] 히스토리에서 구버전 삭제
    elif action == "delete_history":
        target_version = request.form.get('target_version')
        app_data["history"] = [item for item in app_data["history"] if item["version"] != target_version]
        
    return redirect(url_for('gm_dashboard'))

@app.route('/gm/logout')
def gm_logout():
    session.pop('gm_logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)