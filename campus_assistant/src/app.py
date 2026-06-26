from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent import CampusAgent
from src.config import DATA_FILE
from src.retriever import build_retriever


AUTH_FILE = ROOT / ".auth_sessions.json"
CHAT_FILE = ROOT / ".chat_sessions.json"


st.set_page_config(
    page_title="校园百事通助手",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)


APP_CSS = """
<style>
:root {
  --page-bg: #ffffff;
  --surface: #ffffff;
  --surface-muted: #f7f8fa;
  --line: #e5e7eb;
  --line-soft: #edf0f3;
  --text: #1f2329;
  --muted: #8a919f;
  --blue: #4f7cff;
  --blue-soft: #eef4ff;
  --teal-soft: #e7f3f1;
  --sidebar-width: 280px;
  --sidebar-collapsed-width: 52px;
  --input-height: 96px;
}

.stApp {
  background: var(--page-bg);
  color: var(--text);
}

section[data-testid="stSidebar"],
div[data-testid="stDecoration"],
iframe[title*="streamlit"],
iframe[src*="component"],
[data-testid="stToolbar"],
[data-testid="stStatusWidget"] {
  display: none !important;
}

.block-container {
  max-width: none !important;
  padding: 0 !important;
}

header[data-testid="stHeader"] {
  background: transparent;
  pointer-events: none;
}

button[kind="primary"] {
  background: var(--blue) !important;
  border-color: var(--blue) !important;
  border-radius: 14px !important;
}

button[kind="secondary"] {
  border-color: var(--line) !important;
  border-radius: 14px !important;
}

.topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px 0 16px;
  border-bottom: 1px solid var(--line-soft);
}

.product {
  display: flex;
  align-items: center;
  gap: 12px;
}

.product-avatar,
.hero-mark {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--blue-soft);
  color: var(--blue);
  font-size: 25px;
  font-weight: 800;
}

.product-name,
.hero-title {
  color: var(--text);
  font-weight: 760;
}

.product-name {
  font-size: 22px;
  line-height: 1.1;
}

.product-subtitle {
  color: var(--muted);
  font-size: 13px;
  margin-top: 5px;
}

.chat-note {
  max-width: 880px;
  margin: 22px auto 0;
  padding: 10px 14px;
  border: 1px solid #dbe7ff;
  color: #4f6f9f;
  background: #f7faff;
  border-radius: 8px;
  font-size: 14px;
}

.hero-card {
  margin: 74px auto 22px;
  max-width: 880px;
  padding: 24px 28px;
  background: #ffffff;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  box-shadow: 0 16px 46px rgba(31, 35, 41, 0.06);
}

.hero-inner {
  display: flex;
  align-items: center;
  gap: 18px;
}

.hero-mark {
  width: 62px;
  height: 62px;
  font-size: 32px;
}

.hero-title {
  font-size: 30px;
  line-height: 1.2;
}

.hero-copy {
  color: var(--muted);
  margin-top: 8px;
  line-height: 1.7;
  font-size: 15px;
}

.suggestion-wrap {
  max-width: 880px;
  margin: 0 auto 22px;
}

.suggestion-title {
  color: #8a94a3;
  font-size: 16px;
  margin: 8px 0 12px;
}

.chat-shell {
  max-width: 920px;
  margin: 0 auto;
}

.stChatInput {
  max-width: none;
}

div[data-testid="stChatMessage"] {
  border: 0;
  border-radius: 16px;
  box-shadow: none;
  background: #ffffff;
}

div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
  line-height: 1.75;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  margin: 8px 0 12px;
}

.category-chip {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  margin: 0 6px 6px 0;
  border-radius: 999px;
  background: var(--surface-muted);
  border: 1px solid var(--line);
  color: var(--text);
  font-size: 13px;
}

.result-card,
.service-card {
  padding: 16px 18px;
  border-radius: 8px;
  border: 1px solid var(--line-soft);
  background: #ffffff;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.035);
}

.result-card {
  margin-bottom: 12px;
}

.result-title,
.service-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 8px;
}

.result-body,
.service-desc {
  color: #475467;
  line-height: 1.7;
  font-size: 14px;
}

.result-meta,
.service-examples {
  margin-top: 10px;
  color: var(--muted);
  font-size: 12px;
}

.notice-box {
  padding: 14px 16px;
  border-radius: 8px;
  border: 1px solid #b7ddd8;
  background: var(--teal-soft);
  color: #0b5f59;
  line-height: 1.7;
}

.service-card {
  min-height: 154px;
  transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
}

.service-card:hover {
  transform: translateY(-4px);
  border-color: #cddcff;
  box-shadow: 0 18px 36px rgba(65, 105, 255, 0.10);
}

.service-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.st-key-login_page {
  min-height: 100vh;
  padding: clamp(28px, 5vw, 72px);
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #f7faff 0%, #ffffff 46%, #f3fbfa 100%);
  color: var(--text);
  overflow: hidden;
}

.st-key-login_page::before {
  content: "";
  position: fixed;
  inset: auto -6vw -24vh -6vw;
  height: 42vh;
  background:
    linear-gradient(90deg, transparent 0 13%, rgba(79,124,255,0.10) 13% 14%, transparent 14% 30%, rgba(33,167,165,0.10) 30% 31%, transparent 31%),
    linear-gradient(8deg, transparent 0 48%, rgba(79,124,255,0.12) 48% 50%, transparent 50% 100%);
  transform: rotate(-3deg);
  pointer-events: none;
}

.st-key-login_page > div {
  width: min(1180px, 100%);
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.st-key-login_page [data-testid="stHorizontalBlock"] {
  align-items: stretch;
  gap: clamp(28px, 5vw, 64px) !important;
}

.st-key-login_visual_panel,
.st-key-login_form_panel {
  height: 100%;
}

.login-kicker {
  color: #4f6f9f;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0;
  margin-bottom: 14px;
}

.login-brand-line {
  display: flex;
  align-items: center;
  gap: 14px;
}

.login-emblem {
  width: 58px;
  height: 58px;
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #4f7cff, #21a7a5);
  color: #ffffff;
  font-size: 30px;
  font-weight: 900;
  box-shadow: 0 18px 42px rgba(79, 124, 255, 0.22);
}

.login-title {
  font-size: clamp(32px, 5vw, 54px);
  font-weight: 860;
  line-height: 1.08;
  color: #1f2329;
}

.login-school {
  margin-top: 10px;
  color: #667085;
  font-size: 17px;
  font-weight: 650;
}

.login-subtitle {
  max-width: 650px;
  margin-top: 22px;
  color: #667085;
  line-height: 1.8;
  font-size: 15px;
}

.login-route-board {
  margin-top: 34px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  max-width: 620px;
}

.login-route-item {
  min-height: 86px;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e5ecff;
  background: rgba(255,255,255,0.84);
  box-shadow: 0 12px 34px rgba(31, 35, 41, 0.05);
}

.login-route-label {
  color: #8a919f;
  font-size: 12px;
  margin-bottom: 8px;
}

.login-route-value {
  color: #1f2329;
  font-size: 15px;
  line-height: 1.5;
  font-weight: 720;
}

.login-campus-strip {
  margin-top: 28px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.login-campus-strip span {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  color: #4f6f9f;
  border: 1px solid #dbe7ff;
  background: #f7faff;
  font-size: 13px;
}

.st-key-login_form_panel {
  background: #ffffff;
  color: var(--text);
  border-radius: 8px;
  padding: clamp(24px, 4vw, 38px);
  box-shadow: 0 28px 80px rgba(79, 124, 255, 0.12);
  border: 1px solid #e8eefc;
}

.login-form-title {
  font-size: 24px;
  font-weight: 820;
  color: #1f2329;
}

.login-form-copy {
  margin-top: 8px;
  margin-bottom: 22px;
  color: #667085;
  font-size: 14px;
  line-height: 1.7;
}

.st-key-login_form_panel [data-testid="stTextInput"] input {
  border-radius: 8px !important;
}

.st-key-login_form_panel button[kind="primary"],
.st-key-login_form_panel [data-testid="stFormSubmitButton"] button {
  min-height: 44px !important;
  border-radius: 8px !important;
  background: #4f7cff !important;
  border-color: #4f7cff !important;
  font-weight: 760 !important;
  box-shadow: 0 10px 24px rgba(79, 124, 255, 0.22) !important;
}

.st-key-login_form_panel button[kind="primary"]:hover,
.st-key-login_form_panel [data-testid="stFormSubmitButton"] button:hover {
  background: #4169ff !important;
  border-color: #4169ff !important;
}

.login-demo-note {
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 8px;
  background: #f7f8fb;
  color: #667085;
  font-size: 13px;
  line-height: 1.7;
  border: 1px solid #edf0f3;
}

.login-demo-note strong {
  color: #2f61df;
}

.login-form-links {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.login-form-links span {
  min-height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: #f4f6f9;
  color: #475467;
  font-size: 13px;
  font-weight: 650;
}

.brand-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #2f6bff, #21a7a5);
  color: #fff;
  font-weight: 900;
  position: relative;
  overflow: hidden;
}

.brand-icon::before {
  content: "";
  position: absolute;
  width: 34px;
  height: 16px;
  border: 3px solid rgba(255, 255, 255, 0.86);
  border-left: 0;
  border-bottom: 0;
  border-radius: 0 16px 0 0;
  transform: rotate(-28deg);
  top: 12px;
  left: 8px;
}

.brand-icon span {
  position: relative;
  font-size: 18px;
}

.side-brand-row,
.side-logo,
.sidebar-user,
.user-dot {
  display: flex;
  align-items: center;
}

.side-logo {
  gap: 10px;
}

.side-title {
  color: #4169ff;
  font-size: 24px;
  font-weight: 820;
  letter-spacing: 0;
}

.side-section-title {
  margin: 18px 0 8px 10px;
  color: #8f96a3;
  font-size: 13px;
  font-weight: 700;
}

.side-divider {
  height: 1px;
  background: var(--line-soft);
  margin: 16px 6px 8px;
}

.history-label {
  margin: 18px 0 6px 10px;
  color: #8f96a3;
  font-size: 13px;
  font-weight: 650;
}

.sidebar-user {
  margin-top: 20px;
  padding: 14px 4px 8px;
  justify-content: space-between;
  color: #6b7280;
  font-size: 14px;
}

.user-dot {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  justify-content: center;
  background: var(--blue-soft);
  color: var(--blue);
  margin-right: 10px;
}

.sidebar-bottom {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 0;
}

.st-key-app_side {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 60;
  width: var(--sidebar-width);
  height: 100vh;
  padding: 18px 14px 16px;
  background: #f7f8fb;
  border-right: 1px solid #e8ebf0;
  border-radius: 0;
  box-shadow: none;
  overflow-y: auto;
  overflow-x: hidden;
}

.st-key-app_side .side-brand {
  padding: 10px 6px 18px;
}

.st-key-app_side_collapsed {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 60;
  width: var(--sidebar-collapsed-width);
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 72px 0 0;
  background: #fbfcfe;
  border-right: 1px solid #eef1f5;
}

.st-key-main_content {
  min-height: 100vh;
  padding: 0 clamp(24px, 4vw, 58px) calc(var(--input-height) + 42px);
}

@media (max-width: 980px) {
  .st-key-login_page {
    min-height: auto;
    padding: 26px 16px 34px;
    align-items: flex-start;
  }

  .st-key-login_page::before {
    display: none;
  }

  .st-key-login_page [data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
  }

  .st-key-login_page [data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    min-width: 100% !important;
    width: 100% !important;
  }

  .login-route-board {
    grid-template-columns: 1fr;
    margin-top: 22px;
  }

  .st-key-login_form_panel {
    margin-top: 22px;
  }

  .login-form-links {
    grid-template-columns: 1fr 1fr;
  }

  .st-key-app_side {
    width: min(var(--sidebar-width), 78vw);
    z-index: 90;
    box-shadow: 18px 0 44px rgba(15, 23, 42, 0.16);
  }
  .st-key-app_side_collapsed {
    width: var(--sidebar-collapsed-width);
    z-index: 90;
    box-shadow: 10px 0 28px rgba(15, 23, 42, 0.10);
  }
  .st-key-main_content {
    padding: 0 18px calc(var(--input-height) + 34px);
  }

  .st-key-side_toggle {
    left: calc(min(var(--sidebar-width), 78vw) - 48px);
  }

  .st-key-side_expand_toggle {
    top: 18px;
    left: 12px;
  }
}

.st-key-side_toggle {
  position: fixed;
  top: 18px;
  left: calc(var(--sidebar-width) - 54px);
  z-index: 1000;
  width: 36px;
  height: 36px;
  pointer-events: auto;
}

.st-key-side_expand_toggle {
  position: fixed;
  top: 72px;
  left: 3px;
  z-index: 1000;
  width: 40px;
  height: 40px;
  pointer-events: auto;
}

.st-key-side_toggle button,
.st-key-side_expand_toggle button {
  width: 34px !important;
  height: 34px !important;
  min-height: 34px !important;
  padding: 0 !important;
  border-radius: 10px !important;
  border: 1px solid #e2e6ee !important;
  background: #ffffff !important;
  color: #667085 !important;
  box-shadow: none !important;
  justify-content: center !important;
  font-size: 18px !important;
}

.st-key-app_side [data-testid="stButton"] button {
  box-shadow: none !important;
}

.st-key-app_side button[kind="primary"] {
  min-height: 46px !important;
  border-radius: 14px !important;
  background: #eef3ff !important;
  border-color: #dce6ff !important;
  color: #2f61df !important;
  justify-content: flex-start !important;
  padding-left: 14px !important;
  font-weight: 700 !important;
}

[class*="st-key-history_row_"] div[data-testid="stHorizontalBlock"] {
  align-items: center;
  margin: 0 0 2px;
  padding: 0;
  border-radius: 10px;
}

[class*="st-key-history_row_"] div[data-testid="stHorizontalBlock"]:hover {
  background: #eef2f7;
}

[class*="st-key-history_row_"] div[data-testid="stHorizontalBlock"] button {
  min-height: 36px !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  color: var(--text) !important;
  font-size: 14px !important;
  padding: 5px 9px !important;
}

[class*="st-key-history_row_"] div[data-testid="stHorizontalBlock"] div[data-testid="column"]:first-child button {
  justify-content: flex-start !important;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.st-key-app_side .stPopover button {
  width: 34px !important;
  min-width: 34px !important;
  height: 34px !important;
  min-height: 34px !important;
  padding: 0 !important;
  border-radius: 999px !important;
  color: var(--muted) !important;
}

.st-key-app_side .stPopover button svg {
  display: none !important;
}

[class*="st-key-history_row_"] div[data-testid="stHorizontalBlock"]:hover .stPopover button {
  background: #e9edf5 !important;
}

.st-key-chat_input_zone {
  position: fixed;
  left: var(--active-sidebar-width);
  right: 0;
  bottom: 0;
  z-index: 50;
  width: calc(100% - var(--active-sidebar-width)) !important;
  max-width: calc(100% - var(--active-sidebar-width)) !important;
  box-sizing: border-box;
  padding: 14px clamp(24px, 4vw, 58px) 18px;
  background: linear-gradient(180deg, rgba(255,255,255,0), #ffffff 28%, #ffffff 100%);
}

.st-key-chat_input_zone > div {
  max-width: 920px;
  margin: 0 auto;
}

.st-key-chat_input_zone [data-testid="stChatInput"] {
  padding-bottom: 0 !important;
}

.st-key-chat_input_zone [data-testid="stChatInput"] textarea {
  padding-right: 92px !important;
}

.st-key-chat_input_zone textarea {
  max-height: 160px !important;
}

.voice-mic-button {
  position: fixed;
  z-index: 70;
  width: 34px;
  height: 34px;
  border: 0;
  border-radius: 10px;
  background: #eef4ff;
  color: #4f7cff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: none;
}

.voice-mic-button svg {
  width: 18px;
  height: 18px;
}

.voice-mic-button.is-listening {
  background: #4f7cff;
  color: #ffffff;
  animation: micPulse 1100ms ease-in-out infinite;
}

.voice-mic-status {
  position: fixed;
  z-index: 70;
  color: #667085;
  font-size: 12px;
  pointer-events: none;
}

@keyframes micPulse {
  0% { box-shadow: 0 0 0 0 rgba(79, 124, 255, 0.34); }
  70% { box-shadow: 0 0 0 12px rgba(79, 124, 255, 0); }
  100% { box-shadow: 0 0 0 0 rgba(79, 124, 255, 0); }
}

@media (max-width: 980px) {
  .st-key-chat_input_zone {
    left: 0;
    width: 100% !important;
    max-width: 100% !important;
    padding: 12px 14px 14px;
  }

  .topbar {
    padding-top: 70px;
  }

  .hero-card {
    margin-top: 28px;
    padding: 20px;
  }

  .hero-inner {
    align-items: flex-start;
  }

  .hero-title {
    font-size: 24px;
  }

  .suggestion-wrap,
  .chat-shell {
    max-width: 100%;
  }

  div[data-testid="stHorizontalBlock"] {
    gap: 0.75rem !important;
  }
}

@media (max-width: 720px) {
  div[data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
  }

  div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    min-width: 100% !important;
    width: 100% !important;
  }

  [class*="st-key-history_row_"] div[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
  }

  [class*="st-key-history_row_"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    min-width: 0 !important;
  }

  .product-name {
    font-size: 20px;
  }

  .product-subtitle {
    font-size: 12px;
  }

  .chat-note {
    margin-top: 16px;
  }
}
</style>
"""


def data_version() -> str:
    data_stat = DATA_FILE.stat()
    code_files = [ROOT / "src" / name for name in ["agent.py", "rag.py", "retriever.py", "tools.py"]]
    code_version = "-".join(str(path.stat().st_mtime_ns) for path in code_files if path.exists())
    return f"{data_stat.st_mtime_ns}-{data_stat.st_size}-{code_version}"


@st.cache_resource
def get_agent(version: str) -> CampusAgent:
    return CampusAgent(build_retriever())


@st.cache_data
def load_campus_data(version: str) -> pd.DataFrame:
    return pd.read_csv(DATA_FILE)


def render_category_chips(df: pd.DataFrame) -> None:
    counts = df["category"].value_counts().sort_index()
    chips = "".join(
        f'<span class="category-chip">{category} 路 {count}</span>'
        for category, count in counts.items()
    )
    st.markdown(chips, unsafe_allow_html=True)


def render_service_catalog() -> None:
    services = [
        ("📝", "请假服务", "病假、事假、销假、特殊情况请假和报到请假流程查询。", "学生请假怎么在今日校园提交？"),
        ("🏆", "奖助学金", "国家奖学金、国家励志奖学金、校内资助形式与申请条件。", "国家励志奖学金和助学金有什么区别？"),
        ("🛠", "后勤报修", "宿舍设施、电路、空调等报修入口和处理建议。", "宿舍网络或空调故障怎么处理？"),
        ("💳", "校园卡服务", "一卡通挂失、补办、材料准备和线上操作路径。", "一卡通服务在哪里查？"),
        ("🍽", "校园生活", "食堂、餐厅、超市、快递、打印和医务室等生活设施查询。", "学校食堂在哪里？"),
        ("📚", "教务选课", "选课入口、退选说明和教务系统相关问题。", "选错了课能退吗？"),
        ("🏠", "宿舍管理", "熄灯时间、大门开关时间和宿舍安静要求。", "宿舍熄灯时间是什么时候？"),
        ("🔗", "官网导航", "快速返回官网、校历、教务处、财务处、网上办事大厅等入口。", "教务处入口在哪里？"),
        ("📊", "学习工具", "支持教学周、学期进度、平均绩点和绩点明细计算。", "绩点明细 85,90,78"),
        ("💬", "多轮追问", "可记住上一轮主题，支持省略主语的连续追问。", "一卡通丢了怎么办？怎么挂失？"),
    ]
    cols = st.columns(3)
    for index, (icon, title, desc, sample) in enumerate(services):
        with cols[index % 3]:
            st.markdown(
                f"""
                  <div class="service-card">
                  <div class="service-title"><span>{icon}</span>{title}</div>
                  <div class="service-desc">{desc}</div>
                  <div class="service-examples">点击下方按钮发起：{sample}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"{icon} 使用{title}", key=f"service_{index}", width="stretch"):
                st.session_state.active_panel = "chat"
                st.session_state.pending_prompt = sample
                st.rerun()


def conversation_markdown(messages: list[dict[str, str]]) -> str:
    lines = ["# 校园百事通助手对话记录", ""]
    for message in messages:
        role = "学生" if message["role"] == "user" else "助手"
        lines.append(f"## {role}")
        lines.append(message["content"])
        lines.append("")
    return "\n".join(lines)


def initial_messages() -> list[dict[str, str]]:
    return [
        {
            "role": "assistant",
            "content": "您好，我可以查询校园请假、奖学金、报修、一卡通、选课和宿舍管理等问题。",
        }
    ]


def ensure_chat_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = initial_messages()
    if "pending_answer" not in st.session_state:
        st.session_state.pending_answer = None
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = {}
    if "active_session_id" not in st.session_state:
        st.session_state.active_session_id = None
    if "user_name" not in st.session_state:
        st.session_state.user_name = "璁垮"
    if "active_panel" not in st.session_state:
        st.session_state.active_panel = "chat"
    if "sidebar_collapsed" not in st.session_state:
        st.session_state.sidebar_collapsed = False
    if "pinned_sessions" not in st.session_state:
        st.session_state.pinned_sessions = []
    if "rename_session_id" not in st.session_state:
        st.session_state.rename_session_id = None
    if "demo_history_seeded" not in st.session_state:
        st.session_state.demo_history_seeded = False


def load_auth_sessions() -> dict[str, str]:
    if not AUTH_FILE.exists():
        return {}
    try:
        return json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_auth_sessions(sessions: dict[str, str]) -> None:
    AUTH_FILE.write_text(
        json.dumps(sessions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_all_chat_sessions() -> dict[str, dict[str, dict[str, object]]]:
    if not CHAT_FILE.exists():
        return {}
    try:
        payload = json.loads(CHAT_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def chat_owner_key() -> str:
    username = str(st.session_state.get("user_name") or "guest").strip()
    return username or "guest"


def load_user_chat_sessions() -> None:
    if st.session_state.get("chat_sessions_loaded"):
        return
    all_sessions = load_all_chat_sessions()
    owner_sessions = all_sessions.get(chat_owner_key(), {})
    if isinstance(owner_sessions, dict):
        st.session_state.chat_sessions = owner_sessions
    st.session_state.chat_sessions_loaded = True


def save_user_chat_sessions() -> None:
    if not st.session_state.get("logged_in"):
        return
    all_sessions = load_all_chat_sessions()
    all_sessions[chat_owner_key()] = st.session_state.get("chat_sessions", {})
    CHAT_FILE.write_text(
        json.dumps(all_sessions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def remember_login(username: str) -> None:
    token = uuid4().hex
    sessions = load_auth_sessions()
    sessions[token] = username
    save_auth_sessions(sessions)
    st.query_params["token"] = token


def restore_login_from_token() -> None:
    if st.session_state.get("logged_in"):
        return
    token = st.query_params.get("token")
    if not token:
        return
    username = load_auth_sessions().get(str(token))
    if username:
        st.session_state.logged_in = True
        st.session_state.user_name = username
        st.session_state.active_session_id = uuid4().hex
        st.session_state.chat_sessions_loaded = False


def clear_saved_login() -> None:
    token = st.query_params.get("token")
    if token:
        sessions = load_auth_sessions()
        sessions.pop(str(token), None)
        save_auth_sessions(sessions)
    st.query_params.clear()


def brand_icon_html() -> str:
    return '<div class="brand-icon"><span>交</span></div>'


def render_login_page() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)
    with st.container(key="login_page"):
        visual_col, form_col = st.columns([0.58, 0.42], gap="large")
        with visual_col:
            with st.container(key="login_visual_panel"):
                st.markdown(
                    """
                    <div class="login-kicker">CAMPUS Q&A · RAG ASSISTANT</div>
                    <div class="login-brand-line">
                      <div class="login-emblem">交</div>
                      <div>
                        <div class="login-title">交院小通</div>
                        <div class="login-school">安徽交通职业技术学院</div>
                      </div>
                    </div>
                    <div class="login-subtitle">
                      面向请假、奖助学金、报修、一卡通、选课、宿舍等校园生活问题，
                      结合本地知识库检索、规则工具和多轮追问，把零散办事信息整理成清晰答案。
                    </div>
                    <div class="login-route-board">
                      <div class="login-route-item">
                        <div class="login-route-label">ASK</div>
                        <div class="login-route-value">校园问答 · 连续追问</div>
                      </div>
                      <div class="login-route-item">
                        <div class="login-route-label">RETRIEVE</div>
                        <div class="login-route-value">知识库检索 · 来源提示</div>
                      </div>
                      <div class="login-route-item">
                        <div class="login-route-label">SERVICE</div>
                        <div class="login-route-value">请假 · 一卡通 · 宿舍报修</div>
                      </div>
                      <div class="login-route-item">
                        <div class="login-route-label">TOOLS</div>
                        <div class="login-route-value">教学周 · 绩点 · 服务导航</div>
                      </div>
                    </div>
                    <div class="login-campus-strip">
                      <span>本地 RAG</span>
                      <span>GLM 增强</span>
                      <span>检索审计</span>
                      <span>历史对话</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        with form_col:
            with st.container(key="login_form_panel"):
                st.markdown(
                    """
                    <div class="login-form-title">进入交院小通</div>
                    <div class="login-form-copy">登录后开始校园问答，可保存对话、查看历史记录，并切换服务导航和检索审计。</div>
                    """,
                    unsafe_allow_html=True,
                )
                with st.form("login_form"):
                    username = st.text_input("学号或姓名", placeholder="例如：202431243")
                    password = st.text_input("密码", type="password", placeholder="演示密码：123456")
                    submitted = st.form_submit_button("登录交院小通", type="primary", width="stretch")
                st.markdown(
                    """
                    <div class="login-demo-note">
                      演示鉴权：任意学号或姓名 + <strong>123456</strong> 即可登录。刷新页面后会自动保持登录状态。
                    </div>
                    <div class="login-form-links">
                      <span>校园问答</span>
                      <span>服务导航</span>
                      <span>检索审计</span>
                      <span>知识库管理</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    if submitted:
        if username.strip() and password == "123456":
            st.session_state.logged_in = True
            st.session_state.user_name = username.strip()
            st.session_state.active_session_id = uuid4().hex
            st.session_state.chat_sessions_loaded = False
            remember_login(username.strip())
            st.rerun()
        else:
            st.error("账号或密码不正确。演示密码为 123456。")


def new_session_title(messages: list[dict[str, str]]) -> str:
    for message in messages:
        if message.get("role") == "user":
            content = str(message.get("content", "")).strip()
            return content[:18] + ("..." if len(content) > 18 else "")
    return "鏍″洯闂瓟"


def save_active_session() -> None:
    if not st.session_state.get("logged_in"):
        return
    session_id = st.session_state.get("active_session_id")
    if not session_id:
        session_id = uuid4().hex
        st.session_state.active_session_id = session_id
    messages = list(st.session_state.get("messages", initial_messages()))
    has_user_message = any(message.get("role") == "user" for message in messages)
    if not has_user_message:
        return
    now = datetime.now(timezone.utc).isoformat()
    existing = st.session_state.chat_sessions.get(session_id, {})
    st.session_state.chat_sessions[session_id] = {
        "title": existing.get("title") or new_session_title(messages),
        "messages": messages,
        "created_at": existing.get("created_at") or now,
        "updated_at": now,
    }
    save_user_chat_sessions()


def start_new_chat() -> None:
    save_active_session()
    st.session_state.messages = initial_messages()
    st.session_state.pending_answer = None
    st.session_state.active_session_id = uuid4().hex if st.session_state.get("logged_in") else None
    st.session_state.active_panel = "chat"


def load_chat_session(session_id: str) -> None:
    save_active_session()
    session = st.session_state.chat_sessions.get(session_id)
    if not session:
        return
    st.session_state.active_session_id = session_id
    st.session_state.messages = list(session["messages"])
    st.session_state.pending_answer = None
    st.session_state.active_panel = "chat"


def delete_chat_session(session_id: str) -> None:
    st.session_state.chat_sessions.pop(session_id, None)
    st.session_state.pinned_sessions = [
        item for item in st.session_state.get("pinned_sessions", []) if item != session_id
    ]
    save_user_chat_sessions()
    if session_id == st.session_state.get("active_session_id"):
        st.session_state.messages = initial_messages()
        st.session_state.pending_answer = None
        st.session_state.active_session_id = uuid4().hex if st.session_state.get("logged_in") else None
        st.session_state.active_panel = "chat"


def clear_current_chat() -> None:
    st.session_state.messages = initial_messages()
    st.session_state.pending_answer = None
    if st.session_state.get("logged_in"):
        st.session_state.active_session_id = uuid4().hex
    st.session_state.active_panel = "chat"


def collapse_sidebar() -> None:
    st.session_state.sidebar_collapsed = True


def expand_sidebar() -> None:
    st.session_state.sidebar_collapsed = False


def rename_chat_session(session_id: str, title: str) -> None:
    session = st.session_state.chat_sessions.get(session_id)
    clean_title = title.strip()
    if session and clean_title:
        session["title"] = clean_title[:32]
        session["updated_at"] = datetime.now(timezone.utc).isoformat()
        save_user_chat_sessions()


def toggle_pin_chat_session(session_id: str) -> None:
    pinned = list(st.session_state.get("pinned_sessions", []))
    if session_id in pinned:
        pinned.remove(session_id)
    else:
        pinned.insert(0, session_id)
    st.session_state.pinned_sessions = pinned[:8]
    save_user_chat_sessions()


def sorted_chat_sessions() -> list[tuple[str, dict[str, object]]]:
    sessions = list(st.session_state.chat_sessions.items())
    pinned = st.session_state.get("pinned_sessions", [])
    order = {session_id: index for index, session_id in enumerate(pinned)}
    def timestamp_value(session: dict[str, object]) -> float:
        return parse_session_time(session).timestamp()

    return sorted(
        sessions,
        key=lambda item: (
            0 if item[0] in order else 1,
            order.get(item[0], 0),
            -timestamp_value(item[1]),
        ),
    )


def parse_session_time(session: dict[str, object]) -> datetime:
    raw = str(session.get("updated_at") or session.get("created_at") or "")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def session_group_label(session: dict[str, object]) -> str:
    age_days = (datetime.now(timezone.utc) - parse_session_time(session)).days
    if age_days <= 0:
        return "今天"
    if age_days <= 7:
        return "7 天内"
    return "更早"


def grouped_chat_sessions(group: str) -> list[tuple[str, dict[str, object]]]:
    return [
        (session_id, session)
        for session_id, session in sorted_chat_sessions()
        if session_group_label(session) == group
    ]


def load_demo_history(title: str) -> None:
    demo_answers = {
        "校园百事通实训步骤": "可以按“需求分析、知识库整理、检索问答、Web界面、测试优化、实训报告”这几个阶段推进。",
        "请假流程与销假要求": "请假一般在今日校园 APP 提交，按类型填写时间和事由，上传材料，审批通过后执行；结束后需要完成销假。",
        "选课退课注意事项": "选课和退课要在规定时间内通过教务系统办理，超过时间通常需要咨询教务处或辅导员。",
    }
    st.session_state.messages = [
        {"role": "user", "content": title},
        {
            "role": "assistant",
            "content": demo_answers.get(title, "这是一个历史会话示例，可以继续追问相关校园问题。"),
            "status": "历史示例 · 可继续追问",
        },
    ]
    st.session_state.active_panel = "chat"
    st.session_state.pending_answer = None
    if st.session_state.get("logged_in"):
        session_id = f"demo_{title}"
        st.session_state.active_session_id = session_id
        st.session_state.chat_sessions[session_id] = {
            "title": title,
            "messages": list(st.session_state.messages),
            "group": demo_group(title),
        }


def demo_group(title: str) -> str:
    if title == "校园百事通实训步骤":
        return "今天"
    if title == "请假流程与销假要求":
        return "7 天内"
    return "30 天内"


def seed_demo_history() -> None:
    st.session_state.demo_history_seeded = True


def render_history_row(session_id: str, session: dict[str, object]) -> None:
    title = str(session.get("title") or "校园问答")
    active = session_id == st.session_state.get("active_session_id")
    pinned = session_id in st.session_state.get("pinned_sessions", [])
    display_title = f"{'📌 ' if pinned else ''}{'● ' if active else ''}{title}"
    with st.container(key=f"history_row_{session_id}"):
        open_col, action_col = st.columns([0.82, 0.18], gap="small")
        with open_col:
            if st.button(
                display_title,
                key=f"open_{session_id}",
                width="stretch",
                help="打开历史对话",
            ):
                load_chat_session(session_id)
                st.rerun()
        with action_col:
            with st.popover("⋯", help="历史操作", width="stretch"):
                if st.button("重命名", key=f"rename_start_{session_id}", width="stretch"):
                    st.session_state.rename_session_id = session_id
                    st.rerun()
                if st.button("取消置顶" if pinned else "置顶", key=f"pin_{session_id}", width="stretch"):
                    toggle_pin_chat_session(session_id)
                    st.rerun()
                st.download_button(
                    "导出",
                    data=conversation_markdown(session.get("messages", initial_messages())),
                    file_name=f"{title}_对话记录.md",
                    mime="text/markdown",
                    key=f"export_{session_id}",
                    width="stretch",
                )
                if st.button("删除", key=f"delete_{session_id}", width="stretch", help="删除历史对话"):
                    delete_chat_session(session_id)
                    st.rerun()
    if st.session_state.get("rename_session_id") == session_id:
        with st.form(f"rename_form_{session_id}"):
            new_title = st.text_input("新的会话名称", value=title, label_visibility="collapsed")
            save_name = st.form_submit_button("保存名称", width="stretch")
        if save_name:
            rename_chat_session(session_id, new_title)
            st.session_state.rename_session_id = None
            st.rerun()

def format_llm_status(meta: dict[str, object] | None, use_llm: bool) -> str:
    if not use_llm:
        return "本地RAG · 未启用GLM"
    if not meta:
        return "本地RAG · 无GLM诊断"
    provider = str(meta.get("provider") or "")
    if provider == "本地工具":
        return "本地工具 · 即时响应"
    if meta.get("ok"):
        model = meta.get("model") or "glm-4-flash"
        latency = meta.get("latency_ms")
        if latency is None:
            return f"智谱GLM · {model}"
        return f"智谱GLM · {model} · {latency} ms"
    error = str(meta.get("error") or "调用失败")
    if len(error) > 80:
        error = error[:80] + "..."
    return f"已回退本地RAG · GLM失败：{error}"


def queue_user_message(prompt: str, use_llm: bool) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.pending_answer = {"prompt": prompt, "use_llm": use_llm}
    st.session_state.force_scroll_bottom = True


def append_assistant_answer(agent: CampusAgent) -> None:
    pending = st.session_state.get("pending_answer")
    if not pending:
        return
    prompt = str(pending["prompt"])
    use_llm = bool(pending["use_llm"])
    payload = agent.chat_detail(prompt, use_llm=use_llm)
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": str(payload["answer"]),
            "status": format_llm_status(payload.get("llm"), use_llm),
        }
    )
    st.session_state.pending_answer = None
    save_active_session()
    st.session_state.force_scroll_bottom = True


def scroll_chat_to_bottom() -> None:
    marker = len(st.session_state.get("messages", []))
    components.html(
        f"""
        <script>
        const marker = {marker};
        function scrollBottom() {{
          const doc = window.parent.document;
          const targets = [
            doc.scrollingElement,
            doc.documentElement,
            doc.body,
            doc.querySelector(".stMain"),
            doc.querySelector(".stApp"),
            doc.querySelector('[data-testid="stAppViewContainer"]'),
            doc.querySelector('[data-testid="stVerticalBlock"]')
          ].filter(Boolean);
          targets.forEach((target) => {{
            const maxScroll = Math.max(target.scrollHeight || 0, target.clientHeight || 0);
            if (typeof target.scrollTo === "function") {{
              target.scrollTo({{ top: maxScroll, behavior: "smooth" }});
            }} else {{
              target.scrollTop = maxScroll;
            }}
          }});
        }}
        requestAnimationFrame(scrollBottom);
        setTimeout(scrollBottom, 120);
        setTimeout(scrollBottom, 420);
        </script>
        """,
        height=0,
    )


def render_voice_input() -> None:
    components.html(
        """
        <script>
        const doc = window.parent.document;
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const MIC_ID = 'voiceMicButton';
        const STATUS_ID = 'voiceMicStatus';
        const OBSERVER_KEY = '__campusVoiceObserver';
        const RESIZE_KEY = '__campusVoiceResize';
        const SCROLL_KEY = '__campusVoiceScroll';
        const INTERVAL_KEY = '__campusVoiceInterval';
        window.parent.__campusVoiceEnabled = true;

        function findChatTextarea() {
          return doc.querySelector('.st-key-chat_input_zone textarea')
            || doc.querySelector('[data-testid="stChatInput"] textarea')
            || doc.querySelector('textarea[placeholder*="校园"]');
        }

        function hasChatInputZone() {
          return Boolean(doc.querySelector('.st-key-chat_input_zone') && findChatTextarea());
        }

        function removeVoiceControls() {
          doc.getElementById(MIC_ID)?.remove();
          doc.getElementById(STATUS_ID)?.remove();
        }

        function findSendButton() {
          const zone = doc.querySelector('.st-key-chat_input_zone');
          const buttons = [...(zone || doc).querySelectorAll('button')];
          return buttons
            .filter((item) => item.id !== MIC_ID)
            .find((item) => {
              const rect = item.getBoundingClientRect();
              return rect.width > 20 && rect.height > 20 && rect.top > window.parent.innerHeight / 2;
            });
        }

        function positionVoiceControls() {
          if (!window.parent.__campusVoiceEnabled || !hasChatInputZone()) {
            removeVoiceControls();
            return;
          }
          const button = doc.getElementById(MIC_ID);
          const status = doc.getElementById(STATUS_ID);
          const sendButton = findSendButton();
          const textarea = findChatTextarea();
          if (!button || !sendButton) return;
          const sendRect = sendButton.getBoundingClientRect();
          const micSize = 34;
          const gap = 8;
          const left = Math.round(sendRect.left - micSize - gap);
          const top = Math.round(sendRect.top + (sendRect.height - micSize) / 2);
          button.style.left = `${left}px`;
          button.style.top = `${top}px`;
          if (status) {
            status.style.left = `${Math.max(8, left - 98)}px`;
            status.style.top = `${top + 8}px`;
          }
          if (textarea) {
            textarea.style.paddingRight = `${Math.max(96, sendRect.width + micSize + gap * 4)}px`;
          }
        }

        function setNativeValue(element, value) {
          const prototype = Object.getPrototypeOf(element);
          const descriptor = Object.getOwnPropertyDescriptor(prototype, "value");
          if (descriptor && descriptor.set) {
            descriptor.set.call(element, value);
          } else {
            element.value = value;
          }
          element.dispatchEvent(new Event("input", { bubbles: true }));
          element.dispatchEvent(new Event("change", { bubbles: true }));
          element.focus();
        }

        function ensureVoiceControls() {
          const zone = doc.querySelector('.st-key-chat_input_zone');
          if (!window.parent.__campusVoiceEnabled || !zone || !findChatTextarea()) {
            removeVoiceControls();
            return;
          }
          if (doc.getElementById(MIC_ID)) {
            positionVoiceControls();
            return;
          }

          const button = doc.createElement('button');
          button.id = MIC_ID;
          button.className = 'voice-mic-button';
          button.type = 'button';
          button.title = '语音输入';
          button.setAttribute('aria-label', '语音输入');
          button.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
              <path d="M12 19v3"></path>
            </svg>`;

          const status = doc.createElement('span');
          status.id = STATUS_ID;
          status.className = 'voice-mic-status';

          doc.body.appendChild(button);
          doc.body.appendChild(status);
          positionVoiceControls();

          if (!SpeechRecognition) {
            button.disabled = true;
            button.style.opacity = "0.55";
            status.textContent = "不支持语音";
            return;
          }

          let recognition = null;
          let listening = false;
          button.addEventListener('click', () => {
            if (listening && recognition) {
              recognition.stop();
              return;
            }
            recognition = new SpeechRecognition();
            recognition.lang = 'zh-CN';
            recognition.interimResults = false;
            recognition.continuous = false;
            listening = true;
            button.classList.add('is-listening');
            status.textContent = '正在听...';
            recognition.onresult = (event) => {
              const text = event.results[0][0].transcript.trim();
              const textarea = findChatTextarea();
              if (text && textarea) {
                setNativeValue(textarea, text);
                status.textContent = '已填入输入框';
                positionVoiceControls();
              } else {
                status.textContent = '未识别到内容';
              }
            };
            recognition.onerror = () => {
              status.textContent = '识别失败';
            };
            recognition.onend = () => {
              listening = false;
              button.classList.remove('is-listening');
              setTimeout(() => { status.textContent = ''; }, 2200);
            };
            recognition.start();
          });
        }

        function syncVoiceControls() {
          if (hasChatInputZone()) {
            ensureVoiceControls();
            positionVoiceControls();
          } else {
            removeVoiceControls();
          }
        }

        if (window.parent[OBSERVER_KEY]) {
          window.parent[OBSERVER_KEY].disconnect();
        }
        window.parent[OBSERVER_KEY] = new MutationObserver(() => {
          window.parent.requestAnimationFrame(syncVoiceControls);
        });
        window.parent[OBSERVER_KEY].observe(doc.body, { childList: true, subtree: true });

        if (window.parent[RESIZE_KEY]) {
          window.parent.removeEventListener('resize', window.parent[RESIZE_KEY]);
        }
        window.parent[RESIZE_KEY] = syncVoiceControls;
        window.parent.addEventListener('resize', window.parent[RESIZE_KEY]);

        if (window.parent[SCROLL_KEY]) {
          window.parent.removeEventListener('scroll', window.parent[SCROLL_KEY], true);
        }
        window.parent[SCROLL_KEY] = syncVoiceControls;
        window.parent.addEventListener('scroll', window.parent[SCROLL_KEY], true);

        if (window.parent[INTERVAL_KEY]) {
          clearInterval(window.parent[INTERVAL_KEY]);
        }
        window.parent[INTERVAL_KEY] = setInterval(syncVoiceControls, 500);

        ensureVoiceControls();
        positionVoiceControls();
        setTimeout(syncVoiceControls, 80);
        setTimeout(syncVoiceControls, 260);
        </script>
        """,
        height=0,
    )


def cleanup_voice_input() -> None:
    components.html(
        """
        <script>
        const doc = window.parent.document;
        window.parent.__campusVoiceEnabled = false;
        doc.getElementById('voiceMicButton')?.remove();
        doc.getElementById('voiceMicStatus')?.remove();
        if (window.parent.__campusVoiceObserver) {
          window.parent.__campusVoiceObserver.disconnect();
          window.parent.__campusVoiceObserver = null;
        }
        if (window.parent.__campusVoiceInterval) {
          clearInterval(window.parent.__campusVoiceInterval);
          window.parent.__campusVoiceInterval = null;
        }
        </script>
        """,
        height=0,
    )


def render_topbar(use_llm: bool) -> None:
    st.markdown(
        """
        <div class="topbar">
          <div class="product">
            <div class="product-avatar">交</div>
            <div>
              <div class="product-name">交院小通</div>
              <div class="product-subtitle">安徽交通职业技术学院 · 校园生活问答助手</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_welcome_panel() -> None:
    st.markdown(
        """
        <div class="chat-note">可以直接提问校园事务，也可以继续追问上一轮答案。</div>
        <div class="hero-card">
          <div class="hero-inner">
            <div class="hero-mark">交</div>
            <div>
              <div class="hero-title">交院小通</div>
              <div class="hero-copy">面向请假、奖助学金、报修、一卡通、选课、宿舍和官网入口等校园生活问题；资料不足时会提示咨询辅导员或对应部门。</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_suggestions() -> None:
    examples = [
        ("学生请假怎么在今日校园提交？", "查询请假流程、材料和销假要求"),
        ("国家励志奖学金和助学金有什么区别？", "对比奖助政策和申请条件"),
        ("宿舍网络或空调故障怎么处理？", "定位报修入口和处理建议"),
        ("一卡通服务在哪里查？", "查询挂失、补办和官网入口"),
    ]
    st.markdown('<div class="suggestion-wrap"><div class="suggestion-title">试试这些校园问题</div></div>', unsafe_allow_html=True)
    cols = st.columns(4)
    for index, (title, desc) in enumerate(examples):
        with cols[index]:
            st.caption(desc)
            if st.button(title, key=f"suggest_{index}", width="stretch"):
                st.session_state.pending_prompt = title
                st.rerun()


def render_service_panel() -> None:
    st.markdown('<div class="section-title">服务导航</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="notice-box">使用方式：点击服务卡片下方按钮，系统会自动切回校园问答并发送对应问题；官网导航类问题会返回学校官网、校历、教务处、财务处等常用入口。</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    render_service_catalog()
    st.write("")
    st.markdown('<div class="section-title">常用操作建议</div>', unsafe_allow_html=True)
    st.markdown(
        "- 请假类问题建议直接问：`怎么请病假？`、`请假结束后需要做什么？`\n"
        "- 报修类问题建议描述故障对象：`宿舍空调坏了怎么报修？`\n"
        "- 一卡通问题建议区分挂失和补办：`一卡通怎么挂失？`、`一卡通补办需要什么材料？`\n"
        "- 多轮追问可以省略主语：先问 `一卡通丢了怎么办？`，再问 `怎么挂失？`\n"
        "- 工具类问题可问：`你会什么工具？`、`教务处入口在哪里？`、`绩点明细 85,90,78`"
    )


def render_search_panel(agent: CampusAgent, df: pd.DataFrame, top_k: int) -> None:
    left, right = st.columns([0.58, 0.42], gap="large")
    with left:
        st.markdown('<div class="section-title">检索结果</div>', unsafe_allow_html=True)
        query = st.text_input("检索问题", value="宿舍熄灯时间是什么时候？")
        category_filter = st.selectbox(
            "限定类别",
            ["全部"] + sorted(df["category"].unique().tolist()),
            index=0,
        )
        active_category = None if category_filter == "全部" else category_filter
        results = agent.retriever.search(query, top_k=top_k, category=active_category)
        if not results:
            st.info("没有找到匹配结果。")
        for record, score in results:
            st.markdown(
                f"""
                <div class="result-card">
                  <div class="result-title">{record.category} · {record.question}</div>
                  <div class="result-body">{record.answer}</div>
                  <div class="result-meta">来源：{record.source} · 相似度：{score:.3f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with right:
        st.markdown('<div class="section-title">类别分布</div>', unsafe_allow_html=True)
        render_category_chips(df)
        st.bar_chart(df["category"].value_counts())


def render_data_panel(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">知识库管理</div>', unsafe_allow_html=True)
    col_filter, col_search = st.columns([0.28, 0.72])
    with col_filter:
        selected_category = st.selectbox(
            "类别筛选",
            ["全部"] + sorted(df["category"].unique().tolist()),
        )
    with col_search:
        keyword = st.text_input("关键词筛选", placeholder="输入问题、答案或来源关键词")
    visible_df = df.copy()
    if selected_category != "全部":
        visible_df = visible_df[visible_df["category"] == selected_category]
    if keyword:
        mask = visible_df.apply(
            lambda row: keyword.lower() in " ".join(map(str, row.values)).lower(),
            axis=1,
        )
        visible_df = visible_df[mask]
    st.dataframe(
        visible_df,
        width="stretch",
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "category": st.column_config.TextColumn("类别", width="small"),
            "question": st.column_config.TextColumn("问题", width="medium"),
            "answer": st.column_config.TextColumn("答案", width="large"),
            "source": st.column_config.TextColumn("来源", width="medium"),
        },
    )


def render_full_sidebar(df: pd.DataFrame) -> tuple[bool, int, bool]:
    with st.container(key="app_side"):
        with st.container(key="side_toggle"):
            st.button("‹", key="sidebar_collapse", help="收起边栏", on_click=collapse_sidebar)
        st.markdown(
            """
            <div class="side-brand">
              <div class="side-brand-row">
                <div class="side-logo">
                  <div class="brand-icon"><span>交</span></div>
                  <div class="side-title">交院小通</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("＋ 开启新对话", type="primary", width="stretch"):
            start_new_chat()
            st.rerun()

        menu_items = [
            ("chat", "💬 校园问答"),
            ("services", "🧭 服务导航"),
            ("search", "🔎 检索审计"),
        ]
        st.markdown('<div class="side-section-title">功能区</div>', unsafe_allow_html=True)
        for key, label in menu_items:
            active = key == st.session_state.get("active_panel", "chat")
            button_label = f"● {label}" if active else label
            if st.button(button_label, key=f"panel_{key}", width="stretch"):
                st.session_state.active_panel = key
                st.rerun()

        st.markdown('<div class="side-divider"></div><div class="side-section-title">历史对话区</div>', unsafe_allow_html=True)
        rendered_history = False
        for group in ["今天", "7 天内", "更早"]:
            sessions = grouped_chat_sessions(group)
            if not sessions:
                continue
            rendered_history = True
            st.markdown(f'<div class="history-label">{group}</div>', unsafe_allow_html=True)
            for session_id, session in sessions:
                render_history_row(session_id, session)
        if not rendered_history:
            st.markdown('<div class="history-label">暂无历史对话</div>', unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="sidebar-user">
              <div><span class="user-dot">学</span>{st.session_state.user_name}</div>
              <div>账户</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("账户操作", expanded=False):
            st.caption(f"当前用户：{st.session_state.user_name}")
            st.download_button(
                "导出当前对话",
                data=conversation_markdown(st.session_state.get("messages", initial_messages())),
                file_name="交院小通_对话记录.md",
                mime="text/markdown",
                key="account_export_current_chat",
                width="stretch",
            )
            if st.button("清空当前对话", key="account_clear_chat", width="stretch"):
                clear_current_chat()
                st.rerun()
            if st.button("删除全部历史", key="account_clear_history", width="stretch"):
                st.session_state.chat_sessions = {}
                save_user_chat_sessions()
                clear_current_chat()
                st.rerun()
            if st.button("退出登录", key="account_logout", width="stretch"):
                clear_saved_login()
                st.session_state.logged_in = False
                st.session_state.messages = initial_messages()
                st.session_state.pending_answer = None
                st.session_state.chat_sessions = {}
                st.session_state.chat_sessions_loaded = False
                st.rerun()

        st.markdown('<div class="sidebar-bottom">', unsafe_allow_html=True)
        with st.expander("服务配置", expanded=False):
            use_llm = st.toggle("智谱GLM增强", value=False)
            top_k = st.slider("检索数量", min_value=3, max_value=8, value=5)
            clear_chat = st.button("清空当前对话", key="config_clear_chat", width="stretch")
            if st.button("知识库管理", key="config_data_panel", width="stretch"):
                st.session_state.active_panel = "data"
                st.rerun()
            st.caption(f"知识库 {len(df)} 条 · 类别 {df['category'].nunique()} 个")
            st.caption(f"数据：{DATA_FILE.name}")
        st.markdown("</div>", unsafe_allow_html=True)
    return use_llm, top_k, clear_chat


version = data_version()
df = load_campus_data(version)
ensure_chat_state()
restore_login_from_token()

if not st.session_state.get("logged_in"):
    render_login_page()
    st.stop()

st.markdown(APP_CSS, unsafe_allow_html=True)
load_user_chat_sessions()
seed_demo_history()

sidebar_collapsed = bool(st.session_state.get("sidebar_collapsed", False))
main_offset = "var(--sidebar-collapsed-width)" if sidebar_collapsed else "var(--sidebar-width)"
st.markdown(
    f"""
    <style>
    :root {{
      --active-sidebar-width: {main_offset};
    }}
    .st-key-main_content {{
      margin-left: {main_offset};
      width: calc(100% - {main_offset});
      box-sizing: border-box;
    }}
    @media (max-width: 980px) {{
      :root {{
        --active-sidebar-width: 0px;
      }}
      .st-key-main_content {{
        margin-left: 0;
        width: 100%;
        padding-top: 68px;
      }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

if sidebar_collapsed:
    with st.container(key="app_side_collapsed"):
        with st.container(key="side_expand_toggle"):
            st.button("›", key="sidebar_expand", help="展开边栏", on_click=expand_sidebar)
    use_llm = False
    top_k = 5
    clear_chat = False
else:
    use_llm, top_k, clear_chat = render_full_sidebar(df)

with st.container(key="main_content"):
    agent = get_agent(version)

    if clear_chat:
        clear_current_chat()
        st.rerun()

    render_topbar(use_llm)
    agent = get_agent(version)

    active_panel = st.session_state.get("active_panel", "chat")
    if active_panel == "services":
        cleanup_voice_input()
        render_service_panel()
    elif active_panel == "search":
        cleanup_voice_input()
        render_search_panel(agent, df, top_k)
    elif active_panel == "data":
        cleanup_voice_input()
        render_data_panel(df)
    else:
        messages = st.session_state.messages
        has_user_message = any(message.get("role") == "user" for message in messages)

        if not has_user_message:
            render_welcome_panel()
            render_suggestions()

        st.markdown('<div class="chat-shell">', unsafe_allow_html=True)
        avatars = {"user": "👩‍🎓", "assistant": "🎓"}
        for message in messages:
            if not has_user_message and message.get("role") == "assistant":
                continue
            with st.chat_message(message["role"], avatar=avatars.get(message["role"], "🎓")):
                st.markdown(message["content"])
                if message.get("status"):
                    st.caption(message["status"])

        if st.session_state.pop("force_scroll_bottom", False):
            scroll_chat_to_bottom()

        if st.session_state.get("pending_answer"):
            with st.chat_message("assistant", avatar=avatars["assistant"]):
                with st.spinner("正在查询知识库并生成回答..."):
                    append_assistant_answer(agent)
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        with st.container(key="chat_input_zone"):
            render_voice_input()
            prompt = st.chat_input("询问校园请假、奖学金、报修、一卡通、选课、宿舍等问题...")
        prompt = prompt or st.session_state.pop("pending_prompt", None)
        if prompt:
            queue_user_message(prompt, use_llm)
            with st.chat_message("user", avatar=avatars["user"]):
                st.markdown(prompt)
            with st.chat_message("assistant", avatar=avatars["assistant"]):
                with st.spinner("正在查询知识库并生成回答..."):
                    append_assistant_answer(agent)
            st.rerun()


