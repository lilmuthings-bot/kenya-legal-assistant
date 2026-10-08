"""
Kenya Legal Assistant — Universal Legal Self-Help Platform
Mission: "Make legal knowledge accessible, not make lawyers mandatory."

Single-file full-stack application:
- Embedded Single-Page Application (HTML5, Mobile-First CSS, ES6 JavaScript)
- Native Python SQLite3 Kenyan Legal Knowledge Graph
- 14-Point Statutory Legal Reasoning Engine
- Dual Execution: Standard Library HTTP Server & Production WSGI (gunicorn app:app)
"""

import os
import sys
import json
import sqlite3
import urllib.parse
import urllib.request
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

PORT = int(os.environ.get("PORT", 3000))
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "kenya_legal.db")

# ==============================================================================
# EMBEDDED FRONTEND (HTML + CSS + JAVASCRIPT IN A SINGLE STRING)
# ==============================================================================

EMBEDDED_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <meta name="theme-color" content="#064e3b">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <title>Kenya Legal Assistant | Make Legal Knowledge Accessible</title>
  <style>
    :root {
      --primary: #064e3b;
      --primary-light: #059669;
      --primary-subtle: #ecfdf5;
      --secondary: #991b1b;
      --secondary-subtle: #fef2f2;
      --accent: #b45309;
      --accent-subtle: #fffbeb;
      --bg-app: #f8fafc;
      --bg-card: #ffffff;
      --border: #e2e8f0;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --shadow: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05);
      --radius: 12px;
      --safe-bottom: env(safe-area-inset-bottom, 16px);
      --safe-top: env(safe-area-inset-top, 16px);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg-app);
      color: var(--text-main);
      line-height: 1.5;
      padding-bottom: calc(75px + var(--safe-bottom));
      min-height: 100vh;
    }
    header {
      background: linear-gradient(135deg, #064e3b 0%, #022c22 100%);
      color: #fff;
      padding: calc(14px + var(--safe-top)) 16px 14px;
      border-bottom: 3px solid var(--accent);
      position: sticky;
      top: 0;
      z-index: 50;
      box-shadow: var(--shadow);
    }
    .header-top { display: flex; justify-content: space-between; align-items: center; }
    .brand-title { font-size: 1.15rem; font-weight: 800; display: flex; align-items: center; gap: 8px; letter-spacing: -0.01em; }
    .brand-badge { background: #b45309; font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; font-weight: 700; }
    .header-btns { display: flex; gap: 8px; }
    .hdr-btn { background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.25); color: #fff; font-size: 0.75rem; padding: 5px 9px; border-radius: 6px; cursor: pointer; }
    .mission-tagline { font-size: 0.78rem; color: #a7f3d0; margin-top: 4px; font-style: italic; opacity: 0.95; }
    .notice-strip { background: var(--secondary-subtle); border-bottom: 1px solid #fecaca; color: var(--secondary); font-size: 0.76rem; padding: 7px 14px; display: flex; justify-content: space-between; align-items: center; }
    .mode-bar { display: flex; overflow-x: auto; gap: 8px; padding: 10px 14px; background: #fff; border-bottom: 1px solid var(--border); scrollbar-width: none; }
    .mode-bar::-webkit-scrollbar { display: none; }
    .mode-chip { background: #f1f5f9; border: 1px solid var(--border); border-radius: 20px; padding: 6px 14px; font-size: 0.8rem; font-weight: 600; color: #334155; white-space: nowrap; cursor: pointer; }
    .mode-chip.active { background: var(--primary); color: #fff; border-color: var(--primary); }
    .mode-desc { font-size: 0.76rem; color: #64748b; padding: 6px 16px 0; font-style: italic; }
    main { padding: 12px 14px; max-width: 820px; margin: 0 auto; }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    .chat-container { display: flex; flex-direction: column; gap: 14px; }
    .messages-list { display: flex; flex-direction: column; gap: 12px; min-height: 250px; }
    .msg { padding: 14px 16px; border-radius: 14px; max-width: 95%; font-size: 0.9rem; line-height: 1.55; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
    .msg-user { background: var(--primary); color: #fff; align-self: flex-end; border-bottom-right-radius: 4px; }
    .msg-assistant { background: #fff; color: var(--text-main); align-self: flex-start; border: 1px solid var(--border); border-bottom-left-radius: 4px; width: 100%; max-width: 100%; }
    .msg-assistant h3, .msg-assistant h4 { color: var(--primary); margin: 8px 0 4px; }
    .msg-assistant p { margin-bottom: 8px; }
    .msg-time { font-size: 0.68rem; opacity: 0.7; margin-top: 6px; text-align: right; }
    .chat-input-card { background: #fff; border: 1px solid var(--border); border-radius: var(--radius); padding: 14px; box-shadow: var(--shadow); position: sticky; bottom: calc(65px + var(--safe-bottom)); z-index: 40; }
    .chat-textarea { width: 100%; min-height: 85px; border: 1px solid var(--border); border-radius: 8px; padding: 10px; font-size: 0.92rem; font-family: inherit; resize: vertical; outline: none; }
    .chat-textarea:focus { border-color: var(--primary); }
    .chat-actions { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; gap: 8px; flex-wrap: wrap; }
    .btn-send { background: var(--primary); color: #fff; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 700; font-size: 0.9rem; cursor: pointer; display: flex; align-items: center; gap: 6px; }
    .scenario-chips { display: flex; gap: 6px; overflow-x: auto; margin-bottom: 8px; padding-bottom: 4px; scrollbar-width: none; }
    .sc-chip { background: var(--primary-subtle); color: var(--primary); border: 1px solid #a7f3d0; border-radius: 16px; font-size: 0.75rem; padding: 4px 10px; white-space: nowrap; cursor: pointer; font-weight: 600; }
    .case-panel { background: #fff; border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; margin-top: 14px; box-shadow: var(--shadow); }
    .case-panel-hdr { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
    .case-panel-title { font-size: 0.95rem; font-weight: 800; color: var(--primary); }
    .panel-section { margin-bottom: 12px; font-size: 0.84rem; }
    .panel-section-title { font-weight: 700; color: #475569; margin-bottom: 4px; font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.04em; }
    .pill-list { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
    .pill { font-size: 0.74rem; padding: 3px 8px; border-radius: 6px; background: #f1f5f9; border: 1px solid #cbd5e1; }
    .pill-issue { background: #e0f2fe; color: #0369a1; border-color: #bae6fd; font-weight: 600; }
    .adv-actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px; margin-top: 12px; }
    .btn-adv { background: #fff; border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; font-size: 0.78rem; font-weight: 700; color: var(--primary); cursor: pointer; text-align: center; }
    .btn-adv:hover { background: var(--primary-subtle); }
    .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; height: calc(60px + var(--safe-bottom)); background: #fff; border-top: 1px solid var(--border); display: flex; justify-content: space-around; align-items: flex-start; padding-top: 6px; z-index: 100; box-shadow: 0 -2px 6px rgba(0,0,0,0.04); }
    .nav-btn { background: none; border: none; display: flex; flex-direction: column; align-items: center; font-size: 0.72rem; color: #64748b; font-weight: 600; cursor: pointer; width: 20%; gap: 2px; }
    .nav-btn.active { color: var(--primary); font-weight: 800; }
    .nav-icon { font-size: 1.25rem; }
    .card { background: #fff; border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; margin-bottom: 12px; box-shadow: var(--shadow); }
    .card-title { font-size: 1rem; font-weight: 800; color: var(--primary); margin-bottom: 6px; }
    .form-control { width: 100%; padding: 8px 10px; border: 1px solid var(--border); border-radius: 6px; font-size: 0.85rem; font-family: inherit; margin-bottom: 8px; }
    .btn-primary { background: var(--primary); color: #fff; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 700; font-size: 0.85rem; cursor: pointer; }
    .btn-secondary { background: #f1f5f9; color: #334155; border: 1px solid var(--border); padding: 8px 16px; border-radius: 6px; font-weight: 700; font-size: 0.85rem; cursor: pointer; }
    .modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: none; align-items: flex-end; justify-content: center; z-index: 200; }
    .modal-backdrop.open { display: flex; }
    .modal-sheet { background: #fff; border-radius: 16px 16px 0 0; width: 100%; max-width: 600px; max-height: 85vh; overflow-y: auto; padding: 20px; box-shadow: var(--shadow); }
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin-bottom: 14px; }
    .metric-box { background: #f8fafc; border: 1px solid var(--border); border-radius: 8px; padding: 12px; text-align: center; }
    .metric-val { font-size: 1.5rem; font-weight: 800; color: var(--primary); }
    .metric-lbl { font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-weight: 700; }
  </style>
</head>
<body>
  <header>
    <div class="header-top">
      <div class="brand-title">
        <span>⚖️ Kenya Legal Assistant</span>
        <span class="brand-badge">Self-Help AI</span>
      </div>
      <div class="header-btns">
        <button class="hdr-btn" onclick="openEmergency()">🚨 999 / 1195</button>
        <button class="hdr-btn" onclick="openAdminOffice()">🔒 Office</button>
      </div>
    </div>
    <div class="mission-tagline">“Make legal knowledge accessible, not make lawyers mandatory.”</div>
  </header>

  <div class="notice-strip">
    <span>⚠️ <strong>Privacy Warning:</strong> Do not enter passwords, PINs, banking info or National ID.</span>
    <button style="background:none;border:none;color:var(--secondary);font-size:0.75rem;font-weight:700;cursor:pointer;text-decoration:underline;" onclick="openPrivacy()">Safety</button>
  </div>

  <div class="mode-bar">
    <button class="mode-chip active" onclick="setMode('rights')">📖 Understand Rights</button>
    <button class="mode-chip" onclick="setMode('handle_myself')">🛠️ Handle It Myself</button>
    <button class="mode-chip" onclick="setMode('represent_myself')">🏛️ Represent Myself</button>
    <button class="mode-chip" onclick="setMode('find_help')">⚖️ Find Legal Help</button>
  </div>
  <div class="mode-desc" id="modeDesc">📖 Understand My Rights: Plain language statutory breakdown under Kenyan law.</div>

  <main>
    <!-- TAB 1: CHAT / ASSISTANT -->
    <div id="tab-chat" class="tab-content active">
      <div class="scenario-chips">
        <div class="sc-chip" onclick="sendSample('My university suspended me and never gave me a chance to explain myself.')">🎓 University Suspension</div>
        <div class="sc-chip" onclick="sendSample('My landlord locked me out today and put padlocks on my door.')">🏠 Landlord Lockout</div>
        <div class="sc-chip" onclick="sendSample('My employer fired me without notice or any hearing.')">💼 Unfair Dismissal</div>
        <div class="sc-chip" onclick="sendSample('What is a contract?')">📜 What is a Contract?</div>
        <div class="sc-chip" onclick="sendSample('Mwenye nyumba amenifungia mlango na kuweka kufuli.')">🇰🇪 Kiswahili: Nyumba</div>
        <div class="sc-chip" onclick="sendSample('I am being blackmailed by my professor for sex or he won\\'t pass my exam. I am above 18.')">⚖️ Harassment Test</div>
      </div>

      <div class="chat-container">
        <div class="messages-list" id="messagesList">
          <div class="msg msg-assistant">
            <h3 style="margin-top:0;">Habari! Welcome to Kenya Legal Assistant.</h3>
            <p>Tell me what happened in your own words. You don’t need to know the law.</p>
            <p>I will investigate your situation, identify legal issues under Kenyan law, distinguish verified facts from allegations, build your live case file, and guide your next lawful steps.</p>
            <div class="msg-time">Today</div>
          </div>
        </div>

        <div class="chat-input-card">
          <textarea id="chatInput" class="chat-textarea" placeholder="Tell me what happened... (e.g. My university suspended me without hearing...)"></textarea>
          <div class="chat-actions">
            <div style="font-size:0.75rem; color:#64748b;">Supported: English, Kiswahili, Sheng</div>
            <button class="btn-send" id="btnSend" onclick="handleSend()">Analyze Situation →</button>
          </div>
        </div>

        <!-- Live Case Panel -->
        <div class="case-panel" id="casePanel" style="display:none;">
          <div class="case-panel-hdr">
            <div class="case-panel-title" id="panelTitle">Active Case File</div>
            <span class="pill pill-issue" id="panelConfid
