import json
import random
import re
import time
import uuid
from datetime import datetime, timezone

import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

st.set_page_config(page_title="NBA 傳奇夢幻聯盟", page_icon="🏀", layout="wide")

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
    # Famous role players / high-impact specialists
    {"id":"derrick_white","name":"Derrick White","team":"Celtics","price":2},
    {"id":"jrue_holiday","name":"Jrue Holiday","team":"Trail Blazers","price":2},
    {"id":"alex_caruso","name":"Alex Caruso","team":"Thunder","price":2},
    {"id":"kyle_korver","name":"Kyle Korver","team":"傳奇球員","price":1},
    {"id":"robert_horry","name":"Robert Horry","team":"傳奇球員","price":1},
    {"id":"andre_iguodala","name":"Andre Iguodala","team":"傳奇球員","price":2},
    {"id":"shane_battier","name":"Shane Battier","team":"傳奇球員","price":1},
    {"id":"bruce_bowen","name":"Bruce Bowen","team":"傳奇球員","price":1},
    {"id":"marcus_smart","name":"Marcus Smart","team":"Grizzlies","price":1},
    {"id":"mikal_bridges","name":"Mikal Bridges","team":"Knicks","price":2},
    {"id":"khris_middleton","name":"Khris Middleton","team":"Bucks","price":2},
    {"id":"andre_miller","name":"Andre Miller","team":"傳奇球員","price":1},
    {"id":"horace_grant","name":"Horace Grant","team":"傳奇球員","price":1},
    {"id":"luis_scola","name":"Luis Scola","team":"傳奇球員","price":1},
    {"id":"serge_ibaka","name":"Serge Ibaka","team":"傳奇球員","price":1},
]

# Expanded pool: notable role players, defenders, shooters, and additional legends.
PLAYERS.extend([
    {"id":"dennis_johnson","name":"Dennis Johnson","team":"傳奇球員","price":2},
    {"id":"sidney_moncrief","name":"Sidney Moncrief","team":"傳奇球員","price":2},
    {"id":"bobby_jones","name":"Bobby Jones","team":"傳奇球員","price":1},
    {"id":"joe_dumars","name":"Joe Dumars","team":"傳奇球員","price":2},
    {"id":"mitch_richmond","name":"Mitch Richmond","team":"傳奇球員","price":2},
    {"id":"chris_webber","name":"Chris Webber","team":"傳奇球員","price":3},
    {"id":"gary_payton","name":"Gary Payton","team":"傳奇球員","price":3},
    {"id":"penny_hardaway_alt","name":"Penny Hardaway (Classic) ","team":"傳奇球員","price":2},
    {"id":"bob_cousy","name":"Bob Cousy","team":"傳奇球員","price":2},
    {"id":"bill_walton","name":"Bill Walton","team":"傳奇球員","price":2},
    {"id":"wes_unseld","name":"Wes Unseld","team":"傳奇球員","price":2},
    {"id":"willis_reed","name":"Willis Reed","team":"傳奇球員","price":2},
    {"id":"pistol_pete","name":"Pete Maravich (Pistol Pete)","team":"傳奇球員","price":2},
    {"id":"jerry_west","name":"Jerry West","team":"傳奇球員","price":4},
    {"id":"elgin_baylor","name":"Elgin Baylor","team":"傳奇球員","price":3},
    {"id":"george_gervin","name":"George Gervin","team":"傳奇球員","price":3},
    {"id":"alex_english","name":"Alex English","team":"傳奇球員","price":2},
    {"id":"bob_pettit","name":"Bob Pettit","team":"傳奇球員","price":3},
    {"id":"dave_cowens","name":"Dave Cowens","team":"傳奇球員","price":2},
    {"id":"chris_mullin","name":"Chris Mullin","team":"傳奇球員","price":2},
    {"id":"mark_price","name":"Mark Price","team":"傳奇球員","price":2},
    {"id":"detlef_schrempf","name":"Detlef Schrempf","team":"傳奇球員","price":1},
    {"id":"shawn_kemp","name":"Shawn Kemp","team":"傳奇球員","price":3},
    {"id":"penny_hardaway_90s","name":"Penny Hardaway (1990s)","team":"傳奇球員","price":2},
    {"id":"ben_wallace","name":"Ben Wallace","team":"傳奇球員","price":2},
    {"id":"chauncey_billups","name":"Chauncey Billups","team":"傳奇球員","price":2},
    {"id":"rasheed_wallace","name":"Rasheed Wallace","team":"傳奇球員","price":2},
    {"id":"rip_hamilton","name":"Richard Hamilton","team":"傳奇球員","price":2},
    {"id":"ron_artest","name":"Ron Artest","team":"傳奇球員","price":2},
    {"id":"peja_stojakovic","name":"Peja Stojakovic","team":"傳奇球員","price":2},
    {"id":"marc_gasol","name":"Marc Gasol","team":"傳奇球員","price":2},
    {"id":"pau_gasol_alt","name":"Pau Gasol (Lakers)","team":"傳奇球員","price":2},
    {"id":"lamarcus_aldridge","name":"LaMarcus Aldridge","team":"傳奇球員","price":2},
    {"id":"joe_johnson","name":"Joe Johnson","team":"傳奇球員","price":2},
    {"id":"manu_ginobili_alt","name":"Manu Ginobili (Spurs)","team":"傳奇球員","price":2},
    {"id":"jason_terry","name":"Jason Terry","team":"傳奇球員","price":1},
    {"id":"michael_finley","name":"Michael Finley","team":"傳奇球員","price":1},
    {"id":"shawn_marion","name":"Shawn Marion","team":"傳奇球員","price":2},
    {"id":"amar_stoudemire","name":"Amar'e Stoudemire","team":"傳奇球員","price":2},
    {"id":"rashard_lewis","name":"Rashard Lewis","team":"傳奇球員","price":1},
    {"id":"jason_williams","name":"Jason Williams (White Chocolate)","team":"傳奇球員","price":1},
    {"id":"mike_conley","name":"Mike Conley","team":"現役／近代球員","price":2},
    {"id":"brook_lopez","name":"Brook Lopez","team":"現役／近代球員","price":2},
    {"id":"klint_capela","name":"Clint Capela","team":"現役／近代球員","price":1},
    {"id":"derrick_favors","name":"Derrick Favors","team":"現役／近代球員","price":1},
    {"id":"pj_tucker","name":"P.J. Tucker","team":"現役／近代球員","price":1},
    {"id":"daniel_theis","name":"Daniel Theis","team":"現役／近代球員","price":1},
    {"id":"kentavious_caldwell_pope","name":"Kentavious Caldwell-Pope","team":"現役／近代球員","price":2},
    {"id":"danny_green","name":"Danny Green","team":"現役／近代球員","price":1},
    {"id":"pat_bev","name":"Patrick Beverley","team":"現役／近代球員","price":1},
    {"id":"bogdan_bogdanovic","name":"Bogdan Bogdanovic","team":"現役／近代球員","price":2},
    {"id":"bojan_bogdanovic","name":"Bojan Bogdanovic","team":"現役／近代球員","price":1},
    {"id":"buddy_hield","name":"Buddy Hield","team":"現役／近代球員","price":2},
    {"id":"malcolm_brogdon","name":"Malcolm Brogdon","team":"現役／近代球員","price":2},
    {"id":"norman_powell","name":"Norman Powell","team":"現役／近代球員","price":2},
    {"id":"derrick_jones_jr","name":"Derrick Jones Jr.","team":"現役／近代球員","price":1},
    {"id":"isaiah_hartenstein","name":"Isaiah Hartenstein","team":"現役／近代球員","price":2},
    {"id":"nic_claxton","name":"Nic Claxton","team":"現役／近代球員","price":2},
    {"id":"kyle_anderson","name":"Kyle Anderson","team":"現役／近代球員","price":1},
    {"id":"josh_hart","name":"Josh Hart","team":"現役／近代球員","price":2},
    {"id":"donte_divincenzo","name":"Donte DiVincenzo","team":"現役／近代球員","price":2},
    {"id":"lu_dort","name":"Luguentz Dort","team":"現役／近代球員","price":2},
    {"id":"herb_jones","name":"Herb Jones","team":"現役／近代球員","price":2},
    {"id":"jaden_mcdaniels","name":"Jaden McDaniels","team":"現役／近代球員","price":1},
    {"id":"naz_reid","name":"Naz Reid","team":"現役／近代球員","price":2},
    {"id":"al_horford","name":"Al Horford","team":"現役／近代球員","price":2},
    {"id":"serge_ibaka_alt","name":"Serge Ibaka (Raptors)","team":"現役／近代球員","price":1},
    {"id":"bobby_portis","name":"Bobby Portis","team":"現役／近代球員","price":1},
    {"id":"isaiah_thomas","name":"Isaiah Thomas","team":"現役／近代球員","price":1},
    {"id":"tj_mcconnell","name":"T.J. McConnell","team":"現役／近代球員","price":1},
    {"id":"maxi_kleber","name":"Maxi Kleber","team":"現役／近代球員","price":1},
    {"id":"kyle_lowry","name":"Kyle Lowry","team":"現役／近代球員","price":2},
])

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
    "deaaron_fox": "4066259", "bam_adebayo": "4066261", "jaylen_brown": "3918891",
    "james_harden": "3992", "chet_holmgren": "4433255", "evan_mobley": "4431678",
    "zach_lavine": "3064447", "brandon_ingram": "3913176", "julius_randle": "3064514",
    "fred_vanvleet": "2991230", "karl_anthony_towns": "3136195", "klay_thompson": "6475",
    "draymond_green": "6589", "rudy_gobert": "3024", "cj_mccollum": "2490469",
    "demar_derozan": "3978", "alperen_sengun": "4871144", "jaren_jackson_jr": "4277960",
    "lamelo_ball": "4432816", "bradley_beal": "6580", "zion_williamson": "4395628",
    "russell_westbrook": "3468", "chris_paul": "2779",
    "derrick_white": "3078576", "jrue_holiday": "3995", "alex_caruso": "2991350",
    "kyle_korver": "3971", "robert_horry": "398", "andre_iguodala": "2386",
    "shane_battier": "1715", "bruce_bowen": "214", "marcus_smart": "2990992",
    "mikal_bridges": "3895802", "khris_middleton": "6609", "andre_miller": "18",
    "horace_grant": "304", "luis_scola": "2775", "serge_ibaka": "3439",
    "kobe_bryant": "110", "michael_jordan": "1035", "shaquille_oneal": "614",
    "tim_duncan": "215", "magic_johnson": "196", "larry_bird": "397",
    "allen_iverson": "397", "vince_carter": "699", "dirk_nowitzki": "609",
    "dwyane_wade": "1987", "kevin_garnett": "708", "steve_nash": "592",
    "scottie_pippen": "937", "charles_barkley": "268", "hakeem_olajuwon": "301",
    "jason_kidd": "429", "ray_allen": "9", "carmelo_anthony": "1975",
    "tracy_mcgrady": " signature", "dennis_rodman": "765", "reggie_miller": "397",
    "pete_maravich": " signature", "isiah_thomas": "_signature", "james_worthy": "signature",
    "dominique_wilkins": "signature", "dwight_howard": " Howard", "tony_parker": "1015",
    "manu_ginobili": "272", "pao_gasol": "996",
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
        "pick_deadline": None,
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
        human_count = sum(1 for t in room.get("players", {}) if not is_ai_token(t))
        if human_count >= 8:
            raise ValueError("真人玩家已滿 8 位。")
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
        human_tokens = [t for t in room.get("players", {}) if not is_ai_token(t)]
        if len(human_tokens) < 1:
            raise ValueError("至少需要 1 位真人玩家才能開始。")
        if len(human_tokens) > 8:
            raise ValueError("真人玩家最多 8 位。")
        # Fill the league to exactly 8 teams with AI teams.
        for i in range(1, 9):
            ai_token = f"ai_team_{i}"
            if len(human_tokens) + sum(1 for t in room["players"] if is_ai_token(t)) >= 8:
                break
            if ai_token not in room["players"]:
                room["players"][ai_token] = {
                    "token": ai_token, "name": f"AI 球隊 {i}", "joined_at": datetime.now(timezone.utc).isoformat(),
                    "draft_order": 0, "picks": [], "spent": 0, "is_ai": True
                }
        order = list(room.get("players", {}).keys())
        random.SystemRandom().shuffle(order)
        for i, player_token in enumerate(order, start=1):
            room["players"][player_token]["draft_order"] = i
        room["draft_order"] = order
        room["current_pick"] = 0
        room["pick_deadline"] = None
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
        budget = int(room.get("budget", BUDGET))
        slots_after_pick = int(room.get("roster_size", ROSTER_SIZE)) - len(person.get("picks", [])) - 1
        if new_spent + slots_after_pick > budget:
            raise ValueError(
                f"預算配置不允許：選完會剩 ${budget-new_spent}，但還有 {slots_after_pick} 個位置；"
                "每位球員至少需要 $1，請選便宜一點的球員，確保最後能湊滿 5 人。"
            )
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
        room["pick_deadline"] = None
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



def is_ai_token(token):
    return str(token).startswith("ai_team_")

def player_ratings(player):
    """遊戲用估算能力值，不是官方統計。"""
    price = int(player.get("price", 1))
    legend = "傳奇" in player.get("team", "")
    base = {1: 66, 2: 73, 3: 80, 4: 87, 5: 94}.get(price, 70)
    n = sum(ord(c) for c in player["id"])
    name = player["name"]
    defense_bonus = 2 if any(k in name for k in ["Duncan", "Olajuwon", "Rodman", "Gobert", "Wembanyama", "Davis", "Garnett"]) else 0
    shooting_bonus = 3 if any(k in name for k in ["Curry", "Bird", "Allen", "Miller", "Durant", "Thompson"]) else 0
    playmaking_bonus = 3 if any(k in name for k in ["Magic", "Nash", "Paul", "Kidd", "Doncic", "Jokic", "Haliburton"]) else 0
    rebounding_bonus = 3 if any(k in name for k in ["O'Neal", "Duncan", "Garnett", "Gobert", "Giannis", "Jokic", "Olajuwon"]) else 0
    return {
        "overall": min(99, base + (n % 5) - 2 + (1 if legend else 0)),
        "offense": min(99, base + ((n // 3) % 7) - 3),
        "defense": min(99, base + ((n // 7) % 7) - 3 + defense_bonus),
        "shooting": min(99, base + ((n // 11) % 7) - 3 + shooting_bonus),
        "playmaking": min(99, base + ((n // 13) % 7) - 3 + playmaking_bonus),
        "rebounding": min(99, base + ((n // 17) % 7) - 3 + rebounding_bonus),
    }

def roster_analysis(player_ids):
    roster = [PLAYER_BY_ID[pid] for pid in player_ids if pid in PLAYER_BY_ID]
    if not roster:
        return {"overall": 0, "offense": 0, "defense": 0, "shooting": 0, "playmaking": 0, "rebounding": 0,
                "strengths": ["尚未完成選秀"], "weaknesses": ["尚無球員可供分析"]}
    ratings = [player_ratings(p) for p in roster]
    keys = ["overall", "offense", "defense", "shooting", "playmaking", "rebounding"]
    avgs = {k: round(sum(r[k] for r in ratings) / len(ratings), 1) for k in keys}
    strengths, weaknesses = [], []
    labels = {
        "offense": ("進攻火力", "進攻火力"),
        "defense": ("防守強度", "防守強度"),
        "shooting": ("外線投射", "外線投射"),
        "playmaking": ("組織傳球", "組織傳球"),
        "rebounding": ("籃板能力", "籃板能力"),
    }
    sorted_skills = sorted(labels, key=lambda k: avgs[k], reverse=True)
    for k in sorted_skills[:2]:
        if avgs[k] >= 82:
            strengths.append(f"{labels[k][0]}佳（{avgs[k]}）")
    for k in sorted(labels, key=lambda k: avgs[k])[:2]:
        if avgs[k] < 83:
            weaknesses.append(f"{labels[k][1]}較弱（{avgs[k]}）")
    if not strengths:
        strengths = ["陣容能力平均，具備一定均衡性"]
    if not weaknesses:
        weaknesses = ["明顯短板不多，需看對位與比賽波動"]
    return {**avgs, "strengths": strengths, "weaknesses": weaknesses}

def ai_choose_player(room, ai_token):
    """AI 在自己的順位挑選可用球員，兼顧能力、價格與剩餘預算。"""
    team = room["players"][ai_token]
    roster = [PLAYER_BY_ID[pid] for pid in team.get("picks", []) if pid in PLAYER_BY_ID]
    spent = int(team.get("spent", 0))
    remaining_slots = int(room.get("roster_size", ROSTER_SIZE)) - len(roster)
    remaining_budget = int(room.get("budget", BUDGET)) - spent
    candidates = [
        PLAYER_BY_ID[pid] for pid in room.get("available_players", [])
        if pid in PLAYER_BY_ID and PLAYER_BY_ID[pid]["price"] <= remaining_budget
        and PLAYER_BY_ID[pid]["price"] <= remaining_budget - max(0, remaining_slots - 1)
    ]
    if not candidates:
        candidates = [PLAYER_BY_ID[pid] for pid in room.get("available_players", [])
                      if pid in PLAYER_BY_ID and PLAYER_BY_ID[pid]["price"] <= remaining_budget]
    if not candidates:
        raise ValueError("AI 找不到符合剩餘預算的球員。")
    current = roster_analysis([p["id"] for p in roster])
    def score(p):
        r = player_ratings(p)
        # Encourage team balance while prioritizing high overall value per dollar.
        weakest = min(current.get(k, 75) for k in ["offense", "defense", "shooting", "playmaking", "rebounding"]) if roster else 75
        # Score team fit: boost missing skills and role-player specialists, while keeping enough budget for remaining slots.
        skill_keys = ["offense", "defense", "shooting", "playmaking", "rebounding"]
        weakest_skill = min(skill_keys, key=lambda k: current.get(k, 75)) if roster else None
        fit_bonus = (r[weakest_skill] - 75) * 0.32 if weakest_skill else 0
        price_value = r["overall"] / max(1, p["price"])
        budget_pacing = 2.5 if p["price"] <= 2 and remaining_slots >= 3 else 0
        return r["overall"] * 0.85 + price_value * 0.75 + fit_bonus + budget_pacing - p["price"] * 0.7 + random.random() * 1.5
    return max(candidates, key=score)

def ai_pick_current(code):
    """只在當前順位是 AI 時進行一次原子選秀。"""
    def mutate(room, result):
        if room.get("status") != "drafting":
            return room
        order = room.get("draft_order", [])
        current = int(room.get("current_pick", 0))
        if not order or current >= len(order) * int(room.get("roster_size", ROSTER_SIZE)):
            room["status"] = "finished"
            return room
        n = len(order)
        round_no, offset = divmod(current, n)
        idx = offset if round_no % 2 == 0 else n - 1 - offset
        token = order[idx]
        if not is_ai_token(token):
            return room
        player = ai_choose_player(room, token)
        person = room["players"][token]
        person.setdefault("picks", []).append(player["id"])
        person["spent"] = int(person.get("spent", 0)) + int(player["price"])
        room["available_players"].remove(player["id"])
        room.setdefault("history", []).append({
            "pick_no": current + 1, "round": round_no + 1,
            "player_token": token, "player_name": person["name"],
            "player_id": player["id"], "nba_player": player["name"],
            "price": player["price"], "time": datetime.now(timezone.utc).isoformat(),
            "is_ai": True
        })
        room["current_pick"] = current + 1
        total_picks = len(order) * int(room.get("roster_size", ROSTER_SIZE))
        room["pick_deadline"] = None
        room["version"] = room.get("version", 0) + 1
        if room["current_pick"] >= total_picks:
            room["status"] = "finished"
        return room
    return transact_room(code, mutate)

def auto_pick_expired(code):
    """超過 30 秒未選時，替當前真人玩家依 AI 評分規則選一位可負擔球員。"""
    room = get_room(code)
    if not room or room.get("status") != "drafting":
        return False
    deadline = room.get("pick_deadline")
    if not deadline or time.time() < float(deadline):
        return False
    current = active_pick_info(room)
    if not current or is_ai_token(current["token"]):
        return False
    token = current["token"]
    player = ai_choose_player(room, token)
    pick_player(code, token, player["id"])
    # Mark the history entry as a timed-out automatic selection.
    def annotate(state, result):
        if state and state.get("history"):
            last = state["history"][-1]
            if last.get("player_token") == token and last.get("player_id") == player["id"]:
                last["auto_pick"] = True
        return state
    try:
        transact_room(code, annotate)
    except Exception:
        pass
    return True


def player_tier(player):
    """以遊戲內能力評分顯示分級；不是 NBA 官方排名。"""
    rating = player_ratings(player)["overall"]
    if rating >= 93: return "S 級"
    if rating >= 87: return "A 級"
    if rating >= 80: return "B 級"
    if rating >= 73: return "C 級"
    return "D 級"

def simulate_league(room):
    """每隊互打一次，固定保存結果，避免每次頁面刷新重新抽比分。"""
    teams = room.get("draft_order", [])
    results = []
    wins = {token: 0 for token in teams}
    losses = {token: 0 for token in teams}
    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            a, b = teams[i], teams[j]
            ra = roster_analysis(room["players"][a].get("picks", []))
            rb = roster_analysis(room["players"][b].get("picks", []))
            # Score model combines offense and overall, with bounded random variance.
            seed = sum(ord(c) for c in (room.get("code", "") + a + b))
            rng = random.Random(seed)
            score_a = round(101 + (ra["offense"] - 80) * 0.42 + (ra["overall"] - 80) * 0.25 + rng.gauss(0, 8))
            score_b = round(101 + (rb["offense"] - 80) * 0.42 + (rb["overall"] - 80) * 0.25 + rng.gauss(0, 8))
            if score_a == score_b:
                if rng.random() > 0.5: score_a += 1
                else: score_b += 1
            winner, loser = (a, b) if score_a > score_b else (b, a)
            wins[winner] += 1
            losses[loser] += 1
            results.append({
                "home": a, "away": b, "home_name": room["players"][a]["name"],
                "away_name": room["players"][b]["name"], "home_score": score_a,
                "away_score": score_b, "winner": winner
            })
    standings = []
    for token in teams:
        analysis = roster_analysis(room["players"][token].get("picks", []))
        standings.append({
            "token": token, "team": room["players"][token]["name"],
            "wins": wins[token], "losses": losses[token], "overall": analysis["overall"],
        })
    standings.sort(key=lambda x: (x["wins"], x["overall"]), reverse=True)
    return {"matches": results, "standings": standings, "games": len(results)}

def save_league_results(code):
    def mutate(room, result):
        if room.get("status") != "finished":
            raise ValueError("必須先完成選秀才能進行對戰模擬。")
        if len(room.get("draft_order", [])) != 8:
            raise ValueError("聯盟必須有 8 隊才能模擬 28 場比賽。")
        if not room.get("league_results"):
            room["league_results"] = simulate_league(room)
            room["version"] = room.get("version", 0) + 1
        return room
    return transact_room(code, mutate)



def simulate_championship(room):
    """聯盟 28 場結束後，取戰績前四名進行準決賽與冠軍賽。"""
    league = room.get("league_results") or simulate_league(room)
    standings = league.get("standings", [])
    if len(standings) < 4:
        raise ValueError("至少需要 4 隊才能進行季後賽。")
    seeds = [row["token"] for row in standings[:4]]
    rounds = []
    rng = random.Random(sum(ord(c) for c in room.get("code", "")) + 2026)

    def play(a, b, round_name):
        aa = roster_analysis(room["players"][a].get("picks", []))
        bb = roster_analysis(room["players"][b].get("picks", []))
        sa = round(98 + (aa["offense"] - 80) * 0.45 + (aa["overall"] - 80) * 0.30 + rng.gauss(0, 6))
        sb = round(98 + (bb["offense"] - 80) * 0.45 + (bb["overall"] - 80) * 0.30 + rng.gauss(0, 6))
        if sa == sb:
            if rng.random() > 0.5: sa += 1
            else: sb += 1
        winner = a if sa > sb else b
        return {
            "round": round_name, "team_a": a, "team_a_name": room["players"][a]["name"],
            "score_a": sa, "team_b": b, "team_b_name": room["players"][b]["name"],
            "score_b": sb, "winner": winner, "winner_name": room["players"][winner]["name"]
        }

    semi1 = play(seeds[0], seeds[3], "準決賽 1")
    semi2 = play(seeds[1], seeds[2], "準決賽 2")
    final = play(semi1["winner"], semi2["winner"], "冠軍賽")
    return {
        "format": "例行賽前四名進季後賽，單場淘汰",
        "semifinals": [semi1, semi2],
        "final": final,
        "champion": final["winner"],
        "champion_name": final["winner_name"],
        "runner_up": final["team_b"] if final["winner"] == final["team_a"] else final["team_a"],
        "runner_up_name": final["team_b_name"] if final["winner"] == final["team_a"] else final["team_a_name"]
    }

def save_championship(code):
    def mutate(room, result):
        if room.get("status") != "finished":
            raise ValueError("必須先完成選秀。")
        if not room.get("league_results"):
            raise ValueError("請先完成 28 場聯盟賽。")
        if not room.get("championship"):
            room["championship"] = simulate_championship(room)
            room["version"] = room.get("version", 0) + 1
        return room
    return transact_room(code, mutate)


# Session identity is per browser session; room state itself lives in Firebase.
if "player_token" not in st.session_state:
    st.session_state.player_token = uuid.uuid4().hex
if "display_name" not in st.session_state:
    st.session_state.display_name = ""
if "room_code" not in st.session_state:
    st.session_state.room_code = ""
if "room_error" not in st.session_state:
    st.session_state.room_error = ""

st.title("🏀 NBA 傳奇 × 2026 球星夢幻選秀聯盟")
st.caption("每隊 $15・每隊 5 名球員・真人不足 8 隊由 AI 補滿・蛇行選秀・28 場聯盟模擬")
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

# Unlimited human pick time; AI turns advance automatically.
if room.get("status") == "drafting":
    for _ in range(8):
        current_info = active_pick_info(room)
        if not current_info or not is_ai_token(current_info["token"]):
            break
        try:
            ai_pick_current(code)
            room = get_room(code) or room
        except Exception as e:
            st.error(f"AI 選秀發生問題：{e}")
            break

players = room.get("players", {})
order = room.get("draft_order", [])
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
    st.info("等待真人玩家加入。房主開始後，系統會自動補足至 8 隊；開始後不能再加入新玩家。")
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
            st.info("⏳ 本回合不限時，可以慢慢挑選球員。")
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
            and PLAYER_BY_ID[pid]["price"] <= remaining - max(0, ROSTER_SIZE - len(my_player.get("picks", [])) - 1)
            and PLAYER_BY_ID[pid]["price"] <= max_price
            and search.casefold() in PLAYER_BY_ID[pid]["name"].casefold()
        ]
        available.sort(key=lambda p: (-p["price"], p["name"]))
        if not available:
            st.warning("沒有符合條件的球員。請清除搜尋文字或提高價格篩選；系統會保留足夠預算，讓你能把 5 人陣容選滿。")
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
                        st.caption(f"{player['team']}｜{player_tier(player)}｜能力值 {player_ratings(player)['overall']}")
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

        st.markdown("## 🧠 AI 球隊戰力分析")
        analysis_rows = []
        for token in order:
            p = players[token]
            a = roster_analysis(p.get("picks", []))
            analysis_rows.append({
                "球隊": p["name"], "綜合": a["overall"], "進攻": a["offense"],
                "防守": a["defense"], "外線": a["shooting"],
                "組織": a["playmaking"], "籃板": a["rebounding"],
                "優勢": "、".join(a["strengths"]), "弱點": "、".join(a["weaknesses"])
            })
        st.dataframe(analysis_rows, use_container_width=True, hide_index=True)
        for token in order:
            p = players[token]
            a = roster_analysis(p.get("picks", []))
            with st.expander(f"{p['name']}｜綜合戰力 {a['overall']}"):
                st.write("**優勢：** " + "；".join(a["strengths"]))
                st.write("**弱點：** " + "；".join(a["weaknesses"]))
                st.caption("能力值由遊戲價格與球員特徵估算，用於娛樂性模擬，並非官方球員數據。")

        if host and not room.get("league_results"):
            if st.button("🏀 模擬 8 隊互打（共 28 場）", type="primary"):
                try:
                    save_league_results(code)
                    st.rerun()
                except Exception as e:
                    st.error(f"無法模擬聯盟：{e}")

        league = room.get("league_results")
        if league:
            st.markdown("## 🏆 八隊聯盟戰績")
            st.caption(f"已完成 {league.get('games', 0)} 場模擬比賽；每隊與其他 7 隊各交手一次。比分為遊戲模型模擬，並非真實比賽。")
            st.dataframe([
                {"排名": i + 1, "球隊": row["team"], "勝": row["wins"], "敗": row["losses"], "綜合戰力": row["overall"]}
                for i, row in enumerate(league.get("standings", []))
            ], use_container_width=True, hide_index=True)
            with st.expander("📋 查看全部 28 場比分", expanded=True):
                st.dataframe([
                    {"主隊": m["home_name"], "主隊得分": m["home_score"],
                     "客隊": m["away_name"], "客隊得分": m["away_score"],
                     "勝隊": room["players"][m["winner"]]["name"]}
                    for m in league.get("matches", [])
                ], use_container_width=True, hide_index=True)

            st.markdown("## 🏆 季後賽與總冠軍")
            st.caption("例行賽戰績前四名晉級：第 1 名對第 4 名、第 2 名對第 3 名；準決賽勝者進行單場冠軍賽。")
            if host and not room.get("championship"):
                if st.button("👑 進行季後賽並決出總冠軍", type="primary"):
                    try:
                        save_championship(code)
                        st.rerun()
                    except Exception as e:
                        st.error(f"季後賽模擬失敗：{e}")

            championship = room.get("championship")
            if championship:
                st.success(f"🏆 本屆總冠軍：{championship['champion_name']}！")
                st.write(f"亞軍：**{championship['runner_up_name']}**")
                st.markdown("### 準決賽")
                st.dataframe([
                    {"賽事": m["round"], "球隊 A": m["team_a_name"], "比分": m["score_a"],
                     "球隊 B": m["team_b_name"], "比分 ": m["score_b"], "晉級": m["winner_name"]}
                    for m in championship["semifinals"]
                ], use_container_width=True, hide_index=True)
                final = championship["final"]
                st.markdown("### 🥇 冠軍賽")
                st.markdown(f"**{final['team_a_name']} {final['score_a']} : {final['score_b']} {final['team_b_name']}**")
                st.success(f"冠軍：{championship['champion_name']}")
                st.caption("季後賽比分為遊戲模型模擬，不是真實 NBA 比賽結果。")

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
    st.caption("真人選秀不限時；AI 球隊會自動選人。球員分級與能力值為遊戲模型估算，非官方 NBA 評分。此頁面每約 2 秒重新讀取一次共用資料庫。")
    time.sleep(2)
    st.rerun()
