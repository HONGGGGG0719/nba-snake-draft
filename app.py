import json
import random
import re
import time
import uuid
from datetime import datetime, timezone

import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

st.set_page_config(page_title="NBA 15元蛇行選秀", page_icon="🏀", layout="wide")

BUDGET = 15
ROSTER_SIZE = 5
ROOM_RE = re.compile(r"^[A-Z0-9]{5,8}$")

# 示範價格：可自行調整。球員池刻意放入不同年代的知名球員。
PLAYERS = [
    {"id":"lebron_james","name":"LeBron James","team":"Lakers","price":5},
    {"id":"stephen_curry","name":"Stephen Curry","team":"Warriors","price":5},
    {"id":"kevin_durant","name":"Kevin Durant","team":"Rockets","price":5},
    {"id":"nikola_jokic","name":"Nikola Jokic","team":"Nuggets","price":5},
    {"id":"giannis_antetokounmpo","name":"Giannis Antetokounmpo","team":"Bucks","price":5},
    {"id":"luka_doncic","name":"Luka Doncic","team":"Lakers","price":5},
    {"id":"joel_embiid","name":"Joel Embiid","team":"76ers","price":5},
    {"id":"jayson_tatum","name":"Jayson Tatum","team":"Celtics","price":4},
    {"id":"shai_gilgeous_alexander","name":"Shai Gilgeous-Alexander","team":"Thunder","price":5},
    {"id":"anthony_edwards","name":"Anthony Edwards","team":"Timberwolves","price":4},
    {"id":"anthony_davis","name":"Anthony Davis","team":"Mavericks","price":4},
    {"id":"devin_booker","name":"Devin Booker","team":"Suns","price":4},
    {"id":"ja_morant","name":"Ja Morant","team":"Grizzlies","price":4},
    {"id":"damian_lillard","name":"Damian Lillard","team":"Bucks","price":4},
    {"id":"kawhi_leonard","name":"Kawhi Leonard","team":"Clippers","price":4},
    {"id":"donovan_mitchell","name":"Donovan Mitchell","team":"Cavaliers","price":4},
    {"id":"jimmy_butler","name":"Jimmy Butler","team":"Warriors","price":4},
    {"id":"paul_george","name":"Paul George","team":"76ers","price":4},
    {"id":"kyrie_irving","name":"Kyrie Irving","team":"Mavericks","price":4},
    {"id":"jalen_brunson","name":"Jalen Brunson","team":"Knicks","price":4},
    {"id":"victor_wembanyama","name":"Victor Wembanyama","team":"Spurs","price":4},
    {"id":"tyrese_haliburton","name":"Tyrese Haliburton","team":"Pacers","price":3},
    {"id":"paolo_banchero","name":"Paolo Banchero","team":"Magic","price":3},
    {"id":"trae_young","name":"Trae Young","team":"Hawks","price":3},
    {"id":"deaaron_fox","name":"De'Aaron Fox","team":"Spurs","price":3},
    {"id":"bam_adebayo","name":"Bam Adebayo","team":"Heat","price":3},
    {"id":"jaylen_brown","name":"Jaylen Brown","team":"Celtics","price":3},
    {"id":"james_harden","name":"James Harden","team":"Clippers","price":3},
    {"id":"chet_holmgren","name":"Chet Holmgren","team":"Thunder","price":3},
    {"id":"evan_mobley","name":"Evan Mobley","team":"Cavaliers","price":3},
    {"id":"zach_lavine","name":"Zach LaVine","team":"Kings","price":3},
    {"id":"brandon_ingram","name":"Brandon Ingram","team":"Raptors","price":3},
    {"id":"julius_randle","name":"Julius Randle","team":"Timberwolves","price":3},
    {"id":"fred_vanvleet","name":"Fred VanVleet","team":"Rockets","price":2},
    {"id":"karl_anthony_towns","name":"Karl-Anthony Towns","team":"Knicks","price":3},
    {"id":"klay_thompson","name":"Klay Thompson","team":"Mavericks","price":2},
    {"id":"draymond_green","name":"Draymond Green","team":"Warriors","price":2},
    {"id":"rudy_gobert","name":"Rudy Gobert","team":"Timberwolves","price":2},
    {"id":"cj_mccollum","name":"CJ McCollum","team":"Pelicans","price":2},
    {"id":"demar_derozan","name":"DeMar DeRozan","team":"Kings","price":3},
    {"id":"alperen_sengun","name":"Alperen Sengun","team":"Rockets","price":3},
    {"id":"jaren_jackson_jr","name":"Jaren Jackson Jr.","team":"Grizzlies","price":2},
    {"id":"lamelo_ball","name":"LaMelo Ball","team":"Hornets","price":3},
    {"id":"bradley_beal","name":"Bradley Beal","team":"Suns","price":2},
    {"id":"zion_williamson","name":"Zion Williamson","team":"Pelicans","price":3},
    {"id":"russell_westbrook","name":"Russell Westbrook","team":"Nuggets","price":2},
    {"id":"chris_paul","name":"Chris Paul","team":"Spurs","price":2},
    {"id":"paul_pierce","name":"Paul Pierce","team":"Celtics（傳奇）","price":2},
    {"id":"shaquille_oneal","name":"Shaquille O'Neal","team":"傳奇球員","price":5},
    {"id":"kobe_bryant","name":"Kobe Bryant","team":"傳奇球員","price":5},
    {"id":"michael_jordan","name":"Michael Jordan","team":"傳奇球員","price":5},
    {"id":"tim_duncan","name":"Tim Duncan","team":"傳奇球員","price":4},
    {"id":"magic_johnson","name":"Magic Johnson","team":"傳奇球員","price":4},
    {"id":"larry_bird","name":"Larry Bird","team":"傳奇球員","price":4},
    {"id":"allen_iverson","name":"Allen Iverson","team":"傳奇球員","price":3},
    {"id":"vince_carter","name":"Vince Carter","team":"傳奇球員","price":2},
    {"id":"dirk_nowitzki","name":"Dirk Nowitzki","team":"傳奇球員","price":4},
    {"id":"dwyane_wade","name":"Dwyane Wade","team":"傳奇球員","price":4},
    {"id":"kevin_garnett","name":"Kevin Garnett","team":"傳奇球員","price":4},
    {"id":"steve_nash","name":"Steve Nash","team":"傳奇球員","price":3},
    {"id":"scottie_pippen","name":"Scottie Pippen","team":"傳奇球員","price":3},
    {"id":"charles_barkley","name":"Charles Barkley","team":"傳奇球員","price":3},
    {"id":"hakeem_olajuwon","name":"Hakeem Olajuwon","team":"傳奇球員","price":4},
    {"id":"jason_kidd","name":"Jason Kidd","team":"傳奇球員","price":2},
    {"id":"ray_allen","name":"Ray Allen","team":"傳奇球員","price":2},
    {"id":"carmelo_anthony","name":"Carmelo Anthony","team":"傳奇球員","price":3},
    {"id":"penny_hardaway","name":"Penny Hardaway","team":"傳奇球員","price":2},
    {"id":"tracy_mcgrady","name":"Tracy McGrady","team":"傳奇球員","price":3},
    {"id":"dennis_rodman","name":"Dennis Rodman","team":"傳奇球員","price":2},
    {"id":"reggie_miller","name":"Reggie Miller","team":"傳奇球員","price":2},
    {"id":"pete_maravich","name":"Pete Maravich","team":"傳奇球員","price":2},
    {"id":"isiah_thomas","name":"Isiah Thomas","team":"傳奇球員","price":3},
    {"id":"james_worthy","name":"James Worthy","team":"傳奇球員","price":2},
    {"id":"dominique_wilkins","name":"Dominique Wilkins","team":"傳奇球員","price":2},
    {"id":"dwight_howard","name":"Dwight Howard","team":"傳奇球員","price":2},
    {"id":"tony_parker","name":"Tony Parker","team":"傳奇球員","price":2},
    {"id":"manu_ginobili","name":"Manu Ginobili","team":"傳奇球員","price":2},
    {"id":"pao_gasol","name":"Pau Gasol","team":"傳奇球員","price":2},
    {"id":"yannis_typed","name":"Penny Hardaway（示範備用）","team":"傳奇球員","price":1},
]

PLAYER_BY_ID = {p["id"]: p for p in PLAYERS}

# NBA player headshots hosted by ESPN. These URLs are best-effort; the UI keeps
# working if a player image is unavailable.
ESPN_IDS = {
    "lebron_james": "1966", "stephen_curry": "3975", "kevin_durant": "3202",
    "nikola_jokic": "3112335", "giannis_antetokounmpo": "3032977",
    "luka_doncic": "3945274", "joel_embiid": "3059318", "jayson_tatum": "4065648",
    "shai_gilgeous_alexander": "4278073", "anthony_edwards": "4594268",
    "anthony_davis": "6583", "devin_booker": "3136193", "ja_morant": "4279888",
    "damian_lillard": "6606", "kawhi_leonard": "6450", "donovan_mitchell": "3908809",
    "jimmy_butler": "6430", "paul_george": "4251", "kyrie_irving": "6442",
    "jalen_brunson": "3917376", "victor_wembanyama": "5104157",
    "tyrese_haliburton": "4442267", "paolo_banchero": "4432573", "trae_young": "4277905",
    "deaaron_fox": "4066259", "bam_adebayo": "4066261", "jaylen_brown": "3917376",
    "james_harden": "3992", "chet_holmgren": "4433255", "evan_mobley": "4431678",
    "zach_lavine": "3064447", "brandon_ingram": "3913176", "julius_randle": "3064514",
    "fred_vanvleet": "2991230", "karl_anthony_towns": "3136195", "klay_thompson": "6475",
    "draymond_green": "6589", "rudy_gobert": "3024", "cj_mccollum": "2490469",
    "demar_derozan": "3978", "alperen_sengun": "4871144", "jaren_jackson_jr": "427796 mor",
    "lamelo_ball": "4432816", "bradley_beal": "6580", "zion_williamson": "4395628",
    "russell_westbrook": "3468", "chris_paul": "2779",
}
def player_image_url(player_id):
    espn_id = ESPN_IDS.get(player_id)
    if espn_id and espn_id.isdigit():
        return f"https://a.espncdn.com/i/headshots/nba/players/full/{espn_id}.png"
    return None

def firebase_db():
    if not firebase_admin._apps:
        try:
            cfg = dict(st.secrets["firebase"])
            # Allow pasting the entire Firebase service-account JSON into Secrets.
            if "service_account_json" in cfg:
                service_account_info = json.loads(cfg["service_account_json"])
            else:
                # Keep compatibility with the previous per-field configuration.
                service_account_info = {
                    "type": cfg.get("type", "service_account"),
                    "project_id": cfg["project_id"],
                    "private_key_id": cfg["private_key_id"],
                    "private_key": cfg["private_key"].replace("\\n", "\n"),
                    "client_email": cfg["client_email"],
                    "client_id": cfg.get("client_id", ""),
                    "token_uri": cfg.get("token_uri", "https://oauth2.googleapis.com/token"),
                    "auth_uri": cfg.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
                }
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred, {"databaseURL": cfg["database_url"]})
        except Exception as e:
            st.error("Firebase 設定讀取失敗。請檢查 Streamlit Secrets 的 firebase 欄位。")
            st.exception(e)
            st.stop()
    return db.reference("/rooms")


def new_room(host_name, host_token):
    code = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=6))
    now = datetime.now(timezone.utc).isoformat()
    state = {
        "code": code,
        "created_at": now,
        "status": "lobby",
        "host_token": host_token,
        "players": {
            host_token: {
                "token": host_token, "name": host_name, "joined_at": now,
                "draft_order": 0, "picks": [], "spent": 0
            }
        },
        "draft_order": [host_token],
        "current_pick": 0,
        "available_players": [p["id"] for p in PLAYERS],
        "history": [],
        "budget": BUDGET,
        "roster_size": ROSTER_SIZE,
        "version": 1
    }
    ref = firebase_db().child(code)
    ref.set(state)
    return code

def get_room(code):
    return firebase_db().child(code).get()

def transact_room(code, mutate):
    """Firebase transaction：對整個房間狀態做原子更新，避免同時選到同一球員。"""
    ref = firebase_db().child(code)
    result = {"error": None}
    def wrapper(current):
        if not current:
            result["error"] = "找不到房間。"
            return current
        try:
            return mutate(current, result)
        except ValueError as e:
            result["error"] = str(e)
            return current
    updated = ref.transaction(wrapper)
    if result["error"]:
        raise ValueError(result["error"])
    return updated

def join_room(code, name, token):
    name = name.strip()[:24]
    if not name:
        raise ValueError("請輸入暱稱。")
    def mutate(room, result):
        if room.get("status") != "lobby":
            # 已經加入過的 token 可重新進入已開始的房間
            if token in room.get("players", {}):
                return room
            raise ValueError("這個房間已開始選秀，不能再加入。")
        if token in room.get("players", {}):
            room["players"][token]["name"] = name
            return room
        if any(p.get("name", "").casefold() == name.casefold() for p in room["players"].values()):
            raise ValueError("這個暱稱已被使用，請換一個。")
        room["players"][token] = {
            "token": token, "name": name, "joined_at": datetime.now(timezone.utc).isoformat(),
            "draft_order": 0, "picks": [], "spent": 0
        }
        room["draft_order"].append(token)
        room["version"] = room.get("version", 0) + 1
        return room
    return transact_room(code, mutate)

def start_draft(code, token):
    def mutate(room, result):
        if room.get("host_token") != token:
            raise ValueError("只有房主可以開始選秀。")
        if room.get("status") != "lobby":
            raise ValueError("選秀已經開始或結束。")
        order = list(room.get("draft_order", []))
        if len(order) < 2:
            raise ValueError("至少需要 2 位玩家才能開始。")
        max_players = len(PLAYERS) // room.get("roster_size", ROSTER_SIZE)
        if len(order) > max_players:
            raise ValueError(f"目前球員池最多支援 {max_players} 位玩家；請減少玩家或增加球員池。")
        random.SystemRandom().shuffle(order)
        for i, player_token in enumerate(order, start=1):
            room["players"][player_token]["draft_order"] = i
        room["draft_order"] = order
        room["current_pick"] = 0
        room["status"] = "drafting"
        room["version"] = room.get("version", 0) + 1
        return room
    return transact_room(code, mutate)

def pick_player(code, token, player_id):
    def mutate(room, result):
        if room.get("status") != "drafting":
            raise ValueError("目前不是選秀階段。")
        order = room.get("draft_order", [])
        total_picks = len(order) * room.get("roster_size", ROSTER_SIZE)
        current = room.get("current_pick", 0)
        if current >= total_picks:
            room["status"] = "finished"
            raise ValueError("選秀已結束。")
        # Snake draft: rounds 1,3,5 go forward; rounds 2,4,6 go backward.
        n = len(order)
        round_no = current // n
        offset = current % n
        idx = offset if round_no % 2 == 0 else n - 1 - offset
        active_token = order[idx]
        if active_token != token:
            active_name = room["players"][active_token]["name"]
            raise ValueError(f"還沒輪到你，目前輪到：{active_name}")
        if player_id not in room.get("available_players", []):
            raise ValueError("這名球員已被選走，請重新整理。")
        player = PLAYER_BY_ID.get(player_id)
        if not player:
            raise ValueError("找不到這名球員。")
        person = room["players"][token]
        if len(person.get("picks", [])) >= room.get("roster_size", ROSTER_SIZE):
            raise ValueError("你的陣容已經選滿。")
        new_spent = int(person.get("spent", 0)) + int(player["price"])
        if new_spent > room.get("budget", BUDGET):
            raise ValueError(f"預算不足：選這名球員會花到 ${new_spent}。")
        person.setdefault("picks", []).append(player_id)
        person["spent"] = new_spent
        room["available_players"].remove(player_id)
        room.setdefault("history", []).append({
            "pick_no": current + 1,
            "round": round_no + 1,
            "player_token": token,
            "player_name": person["name"],
            "player_id": player_id,
            "nba_player": player["name"],
            "price": player["price"],
            "time": datetime.now(timezone.utc).isoformat()
        })
        room["current_pick"] = current + 1
        room["version"] = room.get("version", 0) + 1
        if room["current_pick"] >= total_picks:
            room["status"] = "finished"
        return room
    return transact_room(code, mutate)

def active_pick_info(room):
    order = room.get("draft_order", [])
    if not order:
        return None
    total = len(order) * room.get("roster_size", ROSTER_SIZE)
    current = room.get("current_pick", 0)
    if current >= total:
        return None
    n = len(order)
    round_no = current // n
    offset = current % n
    idx = offset if round_no % 2 == 0 else n - 1 - offset
    token = order[idx]
    return {
        "token": token,
        "name": room["players"][token]["name"],
        "pick_no": current + 1,
        "round": round_no + 1,
        "overall": total,
    }

def money(value):
    return f"${value}"

# Session identity is per browser session; room state itself lives in Firebase.
if "player_token" not in st.session_state:
    st.session_state.player_token = uuid.uuid4().hex
if "display_name" not in st.session_state:
    st.session_state.display_name = ""
if "room_code" not in st.session_state:
    st.session_state.room_code = ""
if "room_error" not in st.session_state:
    st.session_state.room_error = ""

st.title("🏀 NBA 15 元多人蛇行選秀")
st.caption("每人預算 $15・每人 5 名球員・蛇行順位・即時共用球員池")
with st.sidebar:
    st.subheader("玩家資料")
    name_input = st.text_input("你的暱稱", value=st.session_state.display_name, max_chars=24)
    if name_input != st.session_state.display_name:
        st.session_state.display_name = name_input.strip()
    st.markdown("---")
    st.markdown("**遊戲規則**")
    st.write("• 每人 $15 預算")
    st.write("• 每人選 5 名球員")
    st.write("• 球員只能被選一次")
    st.write("• 順位隨機，之後蛇行")
    st.caption("球員價格是本網站的遊戲設定，不代表球員實際身價。")

query_params = st.query_params
query_code = str(query_params.get("room", "")).upper().strip()
if query_code and not st.session_state.room_code:
    st.session_state.room_code = query_code

if not st.session_state.room_code:
    st.subheader("建立新房間或加入朋友的房間")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 建立房間")
        st.write("建立者會自動成為房主。")
        if st.button("➕ 建立新選秀房間", type="primary", use_container_width=True):
            if not st.session_state.display_name:
                st.warning("請先在左側輸入暱稱。")
            else:
                try:
                    code = new_room(st.session_state.display_name, st.session_state.player_token)
                    st.session_state.room_code = code
                    st.query_params["room"] = code
                    st.rerun()
                except Exception as e:
                    st.error(f"建立房間失敗：{e}")
    with col2:
        st.markdown("### 加入房間")
        code_input = st.text_input("輸入朋友分享的房間代碼", max_chars=8).upper().strip()
        if st.button("加入房間", use_container_width=True):
            if not st.session_state.display_name:
                st.warning("請先在左側輸入暱稱。")
            elif not ROOM_RE.match(code_input):
                st.warning("房間代碼格式不正確。")
            else:
                try:
                    room = get_room(code_input)
                    if not room:
                        st.error("找不到這個房間。")
                    else:
                        join_room(code_input, st.session_state.display_name, st.session_state.player_token)
                        st.session_state.room_code = code_input
                        st.query_params["room"] = code_input
                        st.rerun()
                except Exception as e:
                    st.error(str(e))
    st.info("加入房間後，請等待房主開始選秀。每位玩家需在自己的瀏覽器輸入暱稱。")
    st.stop()

code = st.session_state.room_code
try:
    room_ref = firebase_db().child(code)
    room = room_ref.get()
except Exception as e:
    st.error(f"無法讀取房間：{e}")
    st.stop()

if not room:
    st.error("房間不存在或已被刪除。")
    if st.button("返回首頁"):
        st.session_state.room_code = ""
        st.query_params.clear()
        st.rerun()
    st.stop()

my_token = st.session_state.player_token
if my_token not in room.get("players", {}):
    st.subheader(f"加入房間 {code}")
    st.write(f"目前有 {len(room.get('players', {}))} 位玩家。")
    if not st.session_state.display_name:
        st.warning("請先在左側輸入暱稱。")
    if st.button("確認加入此房間", type="primary"):
        try:
            join_room(code, st.session_state.display_name, my_token)
            st.rerun()
        except Exception as e:
            st.error(str(e))
    if st.button("返回首頁"):
        st.session_state.room_code = ""
        st.query_params.clear()
        st.rerun()
    st.stop()

my_player = room["players"][my_token]
host = room.get("host_token") == my_token

top1, top2, top3 = st.columns([2, 2, 1])
with top1:
    st.subheader(f"房間：`{code}`")
with top2:
    share_url = f"{st.context.url if hasattr(st.context, 'url') else ''}"
    st.caption("分享連結（複製目前瀏覽器網址即可）")
    st.code(f"?room={code}", language=None)
with top3:
    if st.button("離開／返回首頁"):
        st.session_state.room_code = ""
        st.query_params.clear()
        st.rerun()

st.markdown("**邀請方式：** 複製瀏覽器網址傳給朋友；若網址沒有 `?room=代碼`，請把 `?room=" + code + "` 加在網址後面。")

players = room.get("players", {})
order = room.get("draft_order", [])
if room["status"] == "lobby":
    st.info("等待玩家加入。房主確認人數後即可開始；開始後不能再加入新玩家。")
    st.subheader(f"已加入玩家（{len(players)} 人）")
    st.dataframe(
        [{"玩家": p["name"], "身份": "房主" if p["token"] == room.get("host_token") else "玩家"}
         for p in players.values()],
        use_container_width=True, hide_index=True
    )
    if host:
        st.warning(f"每位玩家要選 5 人，因此總選秀回合為 {len(players) * ROSTER_SIZE} 次。球員池共 {len(PLAYERS)} 人，最多可容納 {len(PLAYERS)//ROSTER_SIZE} 位玩家。")
        if st.button("🎲 隨機順位並開始選秀", type="primary", disabled=len(players) < 2):
            try:
                start_draft(code, my_token)
                st.rerun()
            except Exception as e:
                st.error(str(e))
    else:
        st.write("你已加入。請等待房主開始選秀。")
    time.sleep(1)
    st.rerun()

if room["status"] in ("drafting", "finished"):
    current = active_pick_info(room) if room["status"] == "drafting" else None
    if current:
        st.subheader(f"第 {current['round']} 輪｜第 {current['pick_no']} / {current['overall']} 順位")
        if current["token"] == my_token:
            st.success("🏀 現在輪到你選球員！")
        else:
            st.info(f"目前輪到：**{current['name']}**")
    else:
        st.success("🎉 選秀完成！")

    total_cost = int(my_player.get("spent", 0))
    remaining = int(room.get("budget", BUDGET)) - total_cost
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("你的已選球員", f"{len(my_player.get('picks', []))}/{ROSTER_SIZE}")
    m2.metric("已花費", money(total_cost))
    m3.metric("剩餘預算", money(remaining))
    m4.metric("尚未被選走", len(room.get("available_players", [])))

    if room["status"] == "drafting" and current and current["token"] == my_token:
        st.markdown("### 選擇球員")
        search = st.text_input("搜尋球員名稱", key=f"search_{code}")
        max_price = st.slider("最高可接受價格", min_value=1, max_value=5, value=5)
        available = [
            PLAYER_BY_ID[pid] for pid in room.get("available_players", [])
            if pid in PLAYER_BY_ID
            and PLAYER_BY_ID[pid]["price"] <= remaining
            and PLAYER_BY_ID[pid]["price"] <= max_price
            and search.casefold() in PLAYER_BY_ID[pid]["name"].casefold()
        ]
        available.sort(key=lambda p: (-p["price"], p["name"]))
        if not available:
            st.warning("沒有符合條件的球員。可以清除搜尋文字或降低價格篩選。")
        else:
            cols = st.columns(3)
            for i, player in enumerate(available):
                with cols[i % 3]:
                    with st.container(border=True):
                        image_url = player_image_url(player["id"])
                        if image_url:
                            st.image(image_url, width=120)
                        else:
                            st.markdown("🏀")
                        st.markdown(f"**{player['name']}**")
                        st.caption(player["team"])
                        st.markdown(f"### ${player['price']}")
                        if st.button("選擇此球員", key=f"pick_{code}_{player['id']}", use_container_width=True):
                            try:
                                pick_player(code, my_token, player["id"])
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
    elif room["status"] == "drafting":
        st.caption("等待目前玩家完成選擇。畫面會自動更新。")

    st.markdown("### 🏆 選秀結果｜各玩家陣容")
    if room["status"] == "finished":
        st.success("選秀已全部完成！以下是最終陣容與預算統計。")
        result_rows = []
        for token in order:
            p = players[token]
            result_rows.append({
                "順位": p.get("draft_order", "-"),
                "玩家": p["name"],
                "球員": "、".join(PLAYER_BY_ID[pid]["name"] for pid in p.get("picks", []) if pid in PLAYER_BY_ID),
                "選秀人數": len(p.get("picks", [])),
                "總花費": f"${p.get('spent', 0)}",
                "剩餘預算": f"${room.get('budget', BUDGET)-p.get('spent',0)}",
            })
        st.dataframe(result_rows, use_container_width=True, hide_index=True)
        csv_data = __import__("pandas").DataFrame(result_rows).to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ 下載選秀結果 CSV", data=csv_data, file_name=f"nba_draft_{code}.csv", mime="text/csv")
    roster_cols = st.columns(min(4, max(1, len(order))))
    for i, token in enumerate(order):
        p = players[token]
        with roster_cols[i % len(roster_cols)]:
            with st.container(border=True):
                st.markdown(f"**{p['draft_order']}｜{p['name']}**")
                st.caption(f"已選 {len(p.get('picks', []))}/{ROSTER_SIZE} 人")
                st.write(f"花費 ${p.get('spent', 0)}｜剩餘 ${room.get('budget', BUDGET)-p.get('spent',0)}")
                for pid in p.get("picks", []):
                    player = PLAYER_BY_ID.get(pid)
                    if player:
                        image_url = player_image_url(pid)
                        if image_url:
                            st.image(image_url, width=90)
                        st.write(f"• {player['name']} (${player['price']})")
                if not p.get("picks"):
                    st.caption("尚未選擇球員")

    with st.expander("📜 完整選秀順位紀錄", expanded=True):
        history = room.get("history", [])
        if history:
            st.dataframe([
                {"順位": h["pick_no"], "輪次": h["round"], "玩家": h["player_name"],
                 "球員": h["nba_player"], "價格": f"${h['price']}"}
                for h in reversed(history)
            ], use_container_width=True, hide_index=True)
        else:
            st.write("尚無選秀紀錄。")

    if host and room["status"] == "finished":
        st.success("所有玩家都已完成 5 名球員的選擇。")
    st.caption("此頁面每約 2 秒重新讀取一次共用資料庫；若未更新，可手動重新整理。")
    time.sleep(2)
    st.rerun()
