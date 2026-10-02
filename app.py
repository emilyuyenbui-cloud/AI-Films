import streamlit as st
import json, re, uuid
from pathlib import Path
from copy import deepcopy

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
TEMPLATE_PATH = APP_DIR / "workflow_template.json"

st.set_page_config(page_title="AI Film Studio", page_icon="🎬", layout="wide")

def slugify(name: str) -> str:
    name = re.sub(r"\s+", "_", name.strip())
    name = re.sub(r"[^\w\-_]+", "", name, flags=re.UNICODE)
    return name or "film_project"

def default_project():
    return {
        "project_id": str(uuid.uuid4()),
        "title": "Untitled Film",
        "concept": "",
        "genre": "Drama",
        "target_minutes": 10,
        "aspect_ratio": "16:9",
        "language": "Vietnamese",
        "visual_style": "写实电影感现代都市剧情片，自然表演，电影级构图与连续性。",
        "characters": [],
        "voice_profiles": [],
        "props": [],
        "locations": [],
        "scenes": [],
        "video_prompts": []
    }

def save_project(p):
    path = DATA_DIR / f"{slugify(p['title'])}.json"
    path.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

def list_projects():
    return sorted(DATA_DIR.glob("*.json"))

def load_project(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def init_state():
    if "project" not in st.session_state:
        st.session_state.project = default_project()
    if "selected_scene" not in st.session_state:
        st.session_state.selected_scene = 0

def duration_from_type(scene_type):
    m = re.search(r"(\d+(?:\.\d+)?)\s*秒", scene_type or "")
    return float(m.group(1)) if m else 10.0

def make_video_prompt(scene, language="Vietnamese"):
    duration = duration_from_type(scene.get("类型", "文戏：10秒"))
    midpoint = max(2.5, round(duration * 0.52, 1))
    plot = scene.get("情节", "").strip()
    chars = "、".join(scene.get("出现角色", [])) or "无"
    props = "、".join(scene.get("出现道具", [])) or "无"
    loc = scene.get("出现场景", "")
    return {
        "编号": scene.get("编号"),
        "类型": scene.get("类型"),
        "标题": scene.get("标题"),
        "时间段": [
            f"中景建立镜头，地点为{loc}。保持上一镜人物位置、服装、桌面物件和光线连续。出场角色：{chars}。关键道具：{props}。剧情动作：{plot}",
            f"At 00:{midpoint:04.1f} 切近景或反应镜头，突出本镜核心情绪和对白。对白使用{language}，自然口语化，严格控制在本镜时长内，不添加原剧情之外的新信息。"
        ],
        "环境音": f"{loc}真实环境底噪，人物对白清晰靠前，餐具、衣物、手机、珠宝等动作声与画面同步，不使用夸张音效。",
        "BGM": "克制的现代都市剧情配乐，低音量，不抢对白；悬念或身份揭露时降低配乐并留出短暂停顿。"
    }

def planning_payload(p):
    return {
        "整体风格": p["visual_style"],
        "角色档案": p["characters"],
        "音色档案": p["voice_profiles"],
        "道具档案": p["props"],
        "场景档案": p["locations"],
        "分镜数量": len(p["scenes"]),
        "分镜情节": p["scenes"]
    }

def video_payload(p):
    return {"作品名": p["title"], "分镜序列": p["video_prompts"]}

def replace_workflow_nodes(p, template_text=None):
    if template_text:
        wf = json.loads(template_text)
    elif TEMPLATE_PATH.exists():
        wf = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    else:
        raise FileNotFoundError("Hãy upload workflow JSON gốc ở phần Export trước khi build.")
    planning = json.dumps(planning_payload(p), ensure_ascii=False, indent=2)
    video = json.dumps(video_payload(p), ensure_ascii=False, indent=2)
    found = {"分镜策划": False, "视频提示词": False}
    for node in wf.get("nodes", []):
        title = node.get("title")
        if title == "分镜策划":
            node.setdefault("widgets_values", [""])
            node["widgets_values"][0] = planning
            found["分镜策划"] = True
        elif title == "视频提示词":
            node.setdefault("widgets_values", [""])
            node["widgets_values"][0] = video
            found["视频提示词"] = True
    return wf, found

def parse_lines(text):
    return [x.strip() for x in text.splitlines() if x.strip()]

init_state()
p = st.session_state.project

st.title("🎬 AI Film Studio")
st.caption("Idea → Asset Bible → Scene Planner → Video Prompt → Workflow Export")

with st.sidebar:
    st.header("Project")
    existing = list_projects()
    choices = ["— Current —"] + [x.name for x in existing]
    choice = st.selectbox("Open project", choices)
    if choice != "— Current —" and st.button("Load selected"):
        st.session_state.project = load_project(DATA_DIR / choice)
        st.rerun()
    if st.button("New project"):
        st.session_state.project = default_project()
        st.rerun()
    if st.button("Save project", type="primary"):
        path = save_project(st.session_state.project)
        st.success(f"Saved: {path.name}")

tabs = st.tabs(["1. Project", "2. Asset Bible", "3. Scene Planner", "4. Video Prompts", "5. Export"])

with tabs[0]:
    c1, c2 = st.columns([2,1])
    with c1:
        p["title"] = st.text_input("Film title", p["title"])
        p["concept"] = st.text_area("Core idea / synopsis", p["concept"], height=220, placeholder="Nhập ý tưởng phim...")
        p["visual_style"] = st.text_area("Overall visual style", p["visual_style"], height=140)
    with c2:
        p["genre"] = st.text_input("Genre", p["genre"])
        p["target_minutes"] = st.number_input("Target duration (minutes)", 1, 120, int(p["target_minutes"]))
        p["aspect_ratio"] = st.selectbox("Aspect ratio", ["16:9","9:16","1:1","2.39:1"], index=["16:9","9:16","1:1","2.39:1"].index(p["aspect_ratio"]) if p["aspect_ratio"] in ["16:9","9:16","1:1","2.39:1"] else 0)
        p["language"] = st.selectbox("Dialogue language", ["Vietnamese","Chinese","English","Thai","Korean"], index=["Vietnamese","Chinese","English","Thai","Korean"].index(p["language"]) if p["language"] in ["Vietnamese","Chinese","English","Thai","Korean"] else 0)
    st.info("MVP v0.1: phần AI story development chưa gọi API. Bản này tập trung khóa schema sản xuất và export đúng workflow.")

with tabs[1]:
    st.subheader("Asset Bible")
    st.caption("Mỗi asset một dòng mô tả đầy đủ. Tên đầu dòng phải giữ ổn định để Scene Planner tham chiếu chính xác.")
    col1, col2 = st.columns(2)
    with col1:
        chars_text = st.text_area("角色档案 — Characters", "\n".join(p["characters"]), height=320)
        voices_text = st.text_area("音色档案 — Voice profiles", "\n".join(p["voice_profiles"]), height=260)
    with col2:
        props_text = st.text_area("道具档案 — Props", "\n".join(p["props"]), height=280)
        locations_text = st.text_area("场景档案 — Locations", "\n".join(p["locations"]), height=300)
    if st.button("Update Asset Bible"):
        p["characters"] = parse_lines(chars_text)
        p["voice_profiles"] = parse_lines(voices_text)
        p["props"] = parse_lines(props_text)
        p["locations"] = parse_lines(locations_text)
        st.success("Asset Bible updated.")

with tabs[2]:
    st.subheader("Scene Planner")
    left, right = st.columns([1, 2])
    with left:
        st.metric("Scenes", len(p["scenes"]))
        if st.button("Add scene"):
            num = len(p["scenes"]) + 1
            p["scenes"].append({
                "编号": num,
                "类型": "文戏：10秒",
                "标题": f"Scene {num}",
                "情节": "",
                "出现角色": [],
                "出现道具": [],
                "出现场景": p["locations"][0].split("，")[0] if p["locations"] else ""
            })
            st.session_state.selected_scene = len(p["scenes"]) - 1
            st.rerun()
        if p["scenes"]:
            labels = [f"{s.get('编号')}. {s.get('标题','')}" for s in p["scenes"]]
            idx = st.selectbox("Select scene", range(len(labels)), format_func=lambda i: labels[i], index=min(st.session_state.selected_scene, len(labels)-1))
            st.session_state.selected_scene = idx
    with right:
        if p["scenes"]:
            s = p["scenes"][st.session_state.selected_scene]
            c1, c2 = st.columns([1,1])
            with c1:
                s["编号"] = st.number_input("编号", 1, 999, int(s.get("编号",1)), key=f"num_{st.session_state.selected_scene}")
                s["类型"] = st.text_input("类型", s.get("类型","文戏：10秒"), key=f"type_{st.session_state.selected_scene}")
            with c2:
                s["标题"] = st.text_input("标题", s.get("标题",""), key=f"title_{st.session_state.selected_scene}")
                s["出现场景"] = st.text_input("出现场景", s.get("出现场景",""), key=f"loc_{st.session_state.selected_scene}")
            s["情节"] = st.text_area("情节", s.get("情节",""), height=180, key=f"plot_{st.session_state.selected_scene}")
            s["出现角色"] = parse_lines(st.text_area("出现角色 — one name per line", "\n".join(s.get("出现角色",[])), height=120, key=f"char_{st.session_state.selected_scene}"))
            s["出现道具"] = parse_lines(st.text_area("出现道具 — one name per line", "\n".join(s.get("出现道具",[])), height=100, key=f"prop_{st.session_state.selected_scene}"))
            c3, c4 = st.columns(2)
            with c3:
                if st.button("Duplicate scene"):
                    new = deepcopy(s); new["编号"] = len(p["scenes"]) + 1
                    p["scenes"].insert(st.session_state.selected_scene + 1, new); st.rerun()
            with c4:
                if st.button("Delete scene"):
                    p["scenes"].pop(st.session_state.selected_scene)
                    st.session_state.selected_scene = max(0, st.session_state.selected_scene - 1)
                    st.rerun()
        else:
            st.warning("No scenes yet.")
    st.divider()
    st.subheader("Import existing 分镜策划 JSON")
    imported = st.text_area("Paste planning JSON", height=160)
    if st.button("Import planning JSON"):
        try:
            x = json.loads(imported)
            p["visual_style"] = x.get("整体风格", p["visual_style"])
            p["characters"] = x.get("角色档案", [])
            p["voice_profiles"] = x.get("音色档案", [])
            p["props"] = x.get("道具档案", [])
            p["locations"] = x.get("场景档案", [])
            p["scenes"] = x.get("分镜情节", [])
            st.success(f"Imported {len(p['scenes'])} scenes.")
            st.rerun()
        except Exception as e:
            st.error(str(e))

with tabs[3]:
    st.subheader("Video Prompt Generator")
    st.caption("Bản MVP sinh prompt theo schema hiện tại. Sau này adapter AI sẽ thay phần generator này.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Generate / refresh ALL video prompts", type="primary"):
            p["video_prompts"] = [make_video_prompt(s, p["language"]) for s in p["scenes"]]
            st.success(f"Generated {len(p['video_prompts'])} prompts.")
    with c2:
        if st.button("Clear video prompts"):
            p["video_prompts"] = []
            st.success("Cleared.")
    if p["video_prompts"]:
        idx = st.selectbox("Preview prompt", range(len(p["video_prompts"])), format_func=lambda i: f"{p['video_prompts'][i]['编号']}. {p['video_prompts'][i]['标题']}")
        st.json(p["video_prompts"][idx], expanded=True)
    else:
        st.info("No video prompts yet.")

with tabs[4]:
    st.subheader("Export")
    planning = planning_payload(p); video = video_payload(p)
    st.write("**分镜策划 preview**")
    st.code(json.dumps(planning, ensure_ascii=False, indent=2)[:12000], language="json")
    st.write("**视频提示词 preview**")
    st.code(json.dumps(video, ensure_ascii=False, indent=2)[:12000], language="json")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("Download project JSON", json.dumps(p, ensure_ascii=False, indent=2), file_name=f"{slugify(p['title'])}_project.json", mime="application/json")
    with col2:
        st.download_button("Download 分镜策划 JSON", json.dumps(planning, ensure_ascii=False, indent=2), file_name=f"{slugify(p['title'])}_planning.json", mime="application/json")
    with col3:
        st.download_button("Download 视频提示词 JSON", json.dumps(video, ensure_ascii=False, indent=2), file_name=f"{slugify(p['title'])}_video_prompts.json", mime="application/json")
    st.divider()
    st.write("**Workflow template**")
    workflow_upload = st.file_uploader(
        "Upload workflow JSON gốc (file có node 分镜策划 và 视频提示词)",
        type=["json"],
        help="Tool sẽ giữ nguyên toàn bộ workflow và chỉ thay nội dung hai node 分镜策划 / 视频提示词."
    )
    if st.button("Build ComfyUI workflow JSON", type="primary"):
        try:
            template_text = None
            if workflow_upload is not None:
                template_text = workflow_upload.getvalue().decode("utf-8")
            wf, found = replace_workflow_nodes(p, template_text=template_text)
            if not found.get("分镜策划") or not found.get("视频提示词"):
                st.warning(f"Đã build nhưng không tìm đủ node cần thay: {found}")
            st.session_state["workflow_export"] = json.dumps(wf, ensure_ascii=False, indent=2)
            st.success(f"Replaced nodes: {found}")
        except Exception as e:
            st.error(str(e))
    if "workflow_export" in st.session_state:
        st.download_button("Download final workflow", st.session_state["workflow_export"], file_name=f"{slugify(p['title'])}_workflow.json", mime="application/json")
