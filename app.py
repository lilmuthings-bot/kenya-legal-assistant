import os
import sys
import json
import sqlite3
import datetime
from urllib.parse import parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

PORT = int(os.environ.get("PORT", 3000))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "kenya_legal.db")

os.makedirs(DATA_DIR, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS official_sources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                url TEXT NOT NULL,
                type TEXT NOT NULL,
                authorityLevel TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS legal_statutes (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                document TEXT NOT NULL,
                part TEXT,
                section TEXT NOT NULL,
                subsection TEXT,
                topic TEXT NOT NULL,
                exactText TEXT NOT NULL,
                plainEnglish TEXT,
                currentStatus TEXT NOT NULL,
                effectiveDate TEXT NOT NULL,
                amendmentHistory TEXT,
                sourceUrl TEXT NOT NULL,
                relatedCases TEXT,
                category TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS case_law (
                id TEXT PRIMARY KEY,
                citation TEXT NOT NULL,
                caseName TEXT NOT NULL,
                court TEXT NOT NULL,
                year INTEGER NOT NULL,
                authorityType TEXT NOT NULL,
                legalIssues TEXT NOT NULL,
                factsSummary TEXT NOT NULL,
                holding TEXT NOT NULL,
                legalTest TEXT NOT NULL,
                relevanceExplanation TEXT NOT NULL,
                sourceUrl TEXT NOT NULL,
                cautionaryNote TEXT
            );
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                primaryIssue TEXT,
                situationSummary TEXT,
                userObjective TEXT,
                urgency TEXT,
                currentStage TEXT,
                confidence TEXT,
                nextStep TEXT,
                createdAt TEXT NOT NULL,
                updatedAt TEXT NOT NULL
            );
        """)
        if cur.execute("SELECT count(*) FROM official_sources").fetchone()[0] == 0:
            sources = [
                ("src_kenyalaw", "Kenya Law", "Official publisher of the Laws of Kenya", "https://new.kenyalaw.org/legislation", "Legislation", "Primary Binding"),
                ("src_judiciary", "Judiciary of Kenya", "Court practice directions and rules", "https://judiciary.go.ke/downloads/", "Judiciary", "Primary Binding"),
                ("src_supremecourt", "Supreme Court of Kenya", "Supreme Court decisions", "https://supremecourt.judiciary.go.ke/", "Supreme Court", "Primary Binding"),
                ("src_parliament", "Parliament of Kenya", "Acts of Parliament", "https://www.parliament.go.ke/", "Parliament Acts", "Primary Binding")
            ]
            cur.executemany("INSERT OR IGNORE INTO official_sources VALUES (?, ?, ?, ?, ?, ?)", sources)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database initialization: {e}")

# Always run database initialization on startup
init_db()

def dispatch_request(method, path, query_params, body_dict):
    try:
        # Ignore favicon requests cleanly
        if path == "/favicon.ico":
            return 204, "image/x-icon", b""

        # 0. Serve Frontend UI (index.html)
        if method == "GET" and (path == "/" or not path.startswith("/api/")):
            index_path = os.path.join(BASE_DIR, "index.html")
            if os.path.exists(index_path):
                with open(index_path, "rb") as f:
                    return 200, "text/html; charset=utf-8", f.read()
            return 200, "text/html; charset=utf-8", b"""<!DOCTYPE html>
            <html>
            <head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Kenya Legal Assistant</title></head>
            <body style="font-family:sans-serif; text-align:center; padding:40px; color:#064e3b;">
                <h2>Kenya Legal Assistant Backend is Active</h2>
                <p>Please make sure <strong>index.html</strong> is in the same directory as app.py</p>
            </body>
            </html>"""

        # 1. Health check
        if method == "GET" and path == "/api/health":
            return 200, "application/json; charset=utf-8", json.dumps({
                "status": "healthy",
                "app": "Kenya Legal Assistant",
                "version": "1.0.0"
            }).encode("utf-8")

        # 2. Official Sources
        if method == "GET" and path in ["/api/sources", "/api/official-sources"]:
            conn = get_db()
            rows = [dict(r) for r in conn.cursor().execute("SELECT * FROM official_sources").fetchall()]
            conn.close()
            return 200, "application/json; charset=utf-8", json.dumps({"sources": rows}).encode("utf-8")

        # 3. Statutes Search
        if method == "GET" and path in ["/api/law", "/api/statutes"]:
            q = (query_params.get("q", [""])[0]).lower()
            conn = get_db()
            if q:
                cur = conn.cursor().execute(
                    "SELECT * FROM legal_statutes WHERE lower(topic) LIKE ? OR lower(document) LIKE ? OR lower(section) LIKE ?",
                    (f"%{q}%", f"%{q}%", f"%{q}%")
                )
            else:
                cur = conn.cursor().execute("SELECT * FROM legal_statutes LIMIT 20")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            return 200, "application/json; charset=utf-8", json.dumps({"statutes": rows}).encode("utf-8")

        # 4. Precedents Search
        if method == "GET" and path == "/api/cases":
            q = (query_params.get("q", [""])[0]).lower()
            conn = get_db()
            if q:
                cur = conn.cursor().execute(
                    "SELECT * FROM case_law WHERE lower(caseName) LIKE ? OR lower(holding) LIKE ?",
                    (f"%{q}%", f"%{q}%")
                )
            else:
                cur = conn.cursor().execute("SELECT * FROM case_law LIMIT 20")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            return 200, "application/json; charset=utf-8", json.dumps({"cases": rows}).encode("utf-8")

        # 5. Specialized Actions
        if method == "POST" and path == "/api/action":
            action_type = body_dict.get("actionType") or "can_they_do_this"
            if action_type == "can_they_do_this":
                payload = {
                    "actionType": "can_they_do_this",
                    "title": "Can They Do This? — Statutory & Constitutional Powers Assessment",
                    "summary": "Assessment under Kenyan constitutional and statutory law.",
                    "sections": [
                        {"heading": "1. What they may legally do", "items": ["Institutions may conduct inquiries in line with established written rules."]},
                        {"heading": "2. What they CANNOT simply do", "items": [
                            "Cannot penalize without advance written notice stating allegations.",
                            "Cannot bypass fair hearing (Fair Administrative Action Act 2015 s. 4(3)).",
                            "Cannot act without providing prompt written reasons (Article 47(2) Constitution)."
                        ]},
                        {"heading": "3. Immediate Next Step", "items": ["Submit an immediate written objection asserting Article 47 due process rights."]}
                    ]
                }
            elif action_type == "what_can_i_do":
                payload = {
                    "actionType": "what_can_i_do",
                    "title": "What Can I Do? — Lawful Action Routes",
                    "summary": "Practical dispute resolution channels under Kenyan law.",
                    "sections": [
                        {"heading": "Route 1: Formal Written Demand", "items": ["Serve a statutory demand letter citing Article 47 and FAAA Section 4."]},
                        {"heading": "Route 2: Internal Administrative Appeal", "items": ["Lodge an appeal within the handbook deadline (usually 14-21 days)."]},
                        {"heading": "Route 3: Ombudsman (CAJ)", "items": ["File a maladministration complaint with CAJ (Ombudsman) under CAJ Act 2011."]}
                    ]
                }
            else:
                payload = {
                    "actionType": action_type,
                    "title": action_type.replace("_", " ").title(),
                    "summary": "Statutory assessment under Kenyan law.",
                    "sections": [
                        {"heading": "Key Principles", "items": ["Preserve original evidence under Section 106B of the Evidence Act.", "Adhere strictly to filing limitation windows."]}
                    ]
                }
            return 200, "application/json; charset=utf-8", json.dumps(payload).encode("utf-8")

        # 6. Chat & Reasoning Engine
        if method == "POST" and path == "/api/chat":
            msg = body_dict.get("message", "").strip()
            low = msg.lower()

            if low.startswith("what is a contract") or low == "what is a contract?":
                reply = (
                    "Under Kenyan law (**Law of Contract Act - Cap 23**), a **contract** is an agreement enforceable by law. "
                    "Essential elements include: Offer, Acceptance, Intention to create legal relations, Consideration, and Contractual Capacity."
                )
                return 200, "application/json; charset=utf-8", json.dumps({
                    "replyText": reply,
                    "casePanel": {"stage": "Informational", "issues": ["Contract Law"], "keyFacts": [], "nextStep": "Ready for next question."}
                }).encode("utf-8")

            if "suspend" in low or "suspension" in low or "university" in low:
                reply = (
                    "I can help you work through this under Kenyan administrative law. I need to investigate **3 material questions** first:\\n\\n"
                    "**1. Did the university give you a written suspension notice?**\\n*Why this matters:* Section 4(3)(a) of the Fair Administrative Action Act mandates prior written notice.\\n\\n"
                    "**2. Does the notice state the reason for the suspension?**\\n*Why this matters:* Article 47(2) of the Constitution guarantees an absolute right to written reasons.\\n\\n"
                    "**3. Were you invited to a disciplinary hearing before the decision was taken?**\\n*Why this matters:* Under *Republic v University of Nairobi ex parte Wanjiku [2018]*, suspension without a hearing is void ab initio.\\n\\n"
                    "As you answer these, your **Case Workspace** will update automatically."
                )
                return 200, "application/json; charset=utf-8", json.dumps({
                    "replyText": reply,
                    "casePanel": {
                        "stage": "Investigation",
                        "issues": ["Right to Fair Administrative Action (Art 47)", "Procedural Fairness (FAAA 2015)"],
                        "keyFacts": [{"type": "Reported Fact", "text": "University suspension without prior hearing"}],
                        "nextStep": "Answer the clarifying questions above."
                    }
                }).encode("utf-8")

            reply = (
                "### ⚖️ Kenyan Legal Assessment\\n\\n"
                "**1. What I Understand:** You have described an adverse action requiring examination under Kenyan law.\\n\\n"
                "**2. Applicable Principles:** Under **Article 47 of the Constitution of Kenya 2010** and the **Fair Administrative Action Act 2015**, any administrative or disciplinary action affecting your rights must be lawful, reasonable, and procedurally fair.\\n\\n"
                "**3. Recommended Next Step:** Preserve all letters, text messages, and emails as electronic evidence under Section 106B of the Evidence Act (Cap 80)."
            )
            return 200, "application/json; charset=utf-8", json.dumps({
                "replyText": reply,
                "casePanel": {"stage": "Intake", "issues": ["Administrative Law", "Due Process"], "keyFacts": [], "nextStep": "Preserve all written evidence."}
            }).encode("utf-8")

        # 7. Document Drafting
        if method == "POST" and path in ["/api/document/generate", "/api/documents/generate"]:
            user_facts = body_dict.get("userFacts", {})
            c_name = user_facts.get("complainantName") or "Complainant"
            inst_name = user_facts.get("institutionName") or "Authority"
            content = (
                f"DATE: {datetime.datetime.now().strftime('%d %B %Y')}\\n\\n"
                f"TO:\\n{inst_name}\\nKenya\\n\\n"
                f"RE: FORMAL COMPLAINT UNDER ARTICLE 47 CONSTITUTION OF KENYA AND SECTION 4 FAIR ADMINISTRATIVE ACTION ACT 2015\\n\\n"
                f"I, {c_name}, hereby submit this formal complaint regarding unfair administrative actions taken against me without prior notice or opportunity to be heard."
            )
            return 200, "application/json; charset=utf-8", json.dumps({
                "title": "Formal Complaint (Art. 47 & FAAA 2015)",
                "content": content
            }).encode("utf-8")

        return 404, "application/json", json.dumps({"error": "Not found"}).encode("utf-8")

    except Exception as err:
        return 500, "application/json", json.dumps({"error": "Server error", "details": str(err)}).encode("utf-8")

# WSGI Handler for Gunicorn on Render
def app(environ, start_response):
    try:
        method = environ.get("REQUEST_METHOD", "GET")
        path = environ.get("PATH_INFO", "/")
        query = parse_qs(environ.get("QUERY_STRING", ""))
        body_dict = {}
        try:
            size = int(environ.get("CONTENT_LENGTH", 0) or 0)
            if size > 0:
                body_dict = json.loads(environ["wsgi.input"].read(size).decode("utf-8"))
        except Exception:
            pass

        code, ctype, body = dispatch_request(method, path, query, body_dict)
        status_map = {200: "200 OK", 204: "204 No Content", 400: "400 Bad Request", 404: "404 Not Found", 500: "500 Internal Server Error"}
        status_str = status_map.get(code, f"{code} OK")
        start_response(status_str, [("Content-Type", ctype), ("Content-Length", str(len(body)))])
        return [body]
    except Exception as e:
        err_msg = json.dumps({"error": "Critical WSGI error", "details": str(e)}).encode("utf-8")
        start_response("500 Internal Server Error", [("Content-Type", "application/json"), ("Content-Length", str(len(err_msg)))])
        return [err_msg]

# Standard HTTP Server (Fallback)
class LegalAssistantHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        code, ctype, body = dispatch_request("GET", parsed.path, parse_qs(parsed.query), {})
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body_dict = {}
        if length > 0:
            try:
                body_dict = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception:
                pass
        code, ctype, body = dispatch_request("POST", parsed.path, {}, body_dict)
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

class ThreadingServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

if __name__ == "__main__":
    server = ThreadingServer(("0.0.0.0", PORT), LegalAssistantHandler)
    print(f"Kenya Legal Assistant active on http://0.0.0.0:{PORT}")
    server.serve_forever()
