# AI Film Studio MVP v0.1

Online-first production UI for:

Idea → Asset Bible → Scene Planner (`分镜策划`) → Video Prompts (`视频提示词`) → ComfyUI Workflow Export

## Current modules
- Project Manager
- Character / Voice / Prop / Location archives
- 8–15 second micro-scene planning
- Import `分镜策划` JSON
- Generate schema-compatible `视频提示词`
- Export project/planning/video-prompt JSON
- Export ComfyUI workflow when `workflow_template.json` is present

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
This repo is ready for Streamlit Community Cloud. Main file: `app.py`.
