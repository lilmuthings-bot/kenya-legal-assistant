import os
import sys
import json
import sqlite3
import datetime
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
        CREATE TABLE IF NOT EXISTS workspace_cases (
            id TEXT PRIMARY KEY,
            caseTitle TEXT NOT NULL,
            caseType TEXT NOT NULL,
            institutionOrForum TEXT NOT NULL,
            caseNumber TEXT,
            applicant TEXT NOT NULL,
            respondent TEXT NOT NULL,
            currentStage TEXT NOT NULL,
            nextDate TEXT,
            urgentDeadlines TEXT,
            notes TEXT,
            updatedAt TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS workspace_facts (
            id TEXT PRIMARY KEY,
            caseId TEXT NOT NULL,
            dateOrTime TEXT,
            description TEXT NOT NULL,
            type TEXT NOT NULL,
            supportingEvidenceIds TEXT
        );
        CREATE TABLE IF NOT EXISTS workspace_opponents (
            id TEXT PRIMARY KEY,
            caseId TEXT NOT NULL,
            allegation TEXT NOT NULL,
            theirClaimedEvidence TEXT,
            contradictionOrFlaw TEXT,
            myCounterPosition TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS workspace_evidence (
            id TEXT PRIMARY KEY,
            caseId TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            dateObtained TEXT,
            description TEXT NOT NULL,
            lawfulStatus TEXT NOT NULL,
            custodyNotes TEXT
        );
        CREATE TABLE IF NOT EXISTS generated_documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            content TEXT NOT NULL,
            factsUsed TEXT,
            missingFactsNoted TEXT
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
        CREATE TABLE IF NOT EXISTS case_facts (
            id TEXT PRIMARY KEY,
            caseId TEXT NOT NULL,
            factText TEXT NOT NULL,
            factType TEXT NOT NULL,
            dateOrTime TEXT,
            source TEXT NOT NULL,
            confidence TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS case_issues (
            id TEXT PRIMARY KEY,
            caseId TEXT NOT NULL,
            issueTitle TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL,
            createdAt TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS case_timeline (
            id TEXT PRIMARY KEY,
            caseId TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            source TEXT NOT NULL,
            status TEXT NOT NULL,
            confidence TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS failed_searches (
            id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            detectedIssue TEXT,
            sourcesSearched TEXT,
            reasonForFailure TEXT,
            createdAt TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

def dispatch_request(method, path, query_params, body_dict):
    # 0. Frontend Interface
    if method == "GET" and (path == "/" or not path.startswith("/api/")):
        index_path = os.path.join(BASE_DIR, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "rb") as f:
                return 200, "text/html; charset=utf-8", f.read()
        return 200, "text/html; charset=utf-8", b"<h1>Kenya Legal Assistant</h1><p>Please upload index.html</p>"

    # 1. Health check
    if method == "GET" and path == "/api/health":
        return 200, "application/json; charset=utf-8", json.dumps({
            "status": "healthy",
            "app": "Kenya Legal Assistant",
            "version": "1.0.0",
            "mission": "Make legal knowledge accessible, not make lawyers mandatory."
        }).encode("utf-8")

    # 2. Official Sources
    if method == "GET" and path in ["/api/sources", "/api/official-sources"]:
        conn = get_db()
        rows = [dict(r) for r in conn.cursor().execute("SELECT * FROM official_sources").fetchall()]
        conn.close()
        return 200, "application/json; charset=utf-8", json.dumps({"sources": rows}).encode("utf-8")

    # 3. Law Search
    if method == "GET" and path in ["/api/law", "/api/statutes"]:
        q = (query_params.get("q", [""])[0]).lower()
        conn = get_db()
        if q:
            cur = conn.cursor().execute(
                "SELECT * FROM legal_statutes WHERE lower(topic) LIKE ? OR lower(document) LIKE ? OR lower(section) LIKE ? OR lower(exactText) LIKE ?",
                (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")
            )
        else:
            cur = conn.cursor().execute("SELECT * FROM legal_statutes LIMIT 20")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return 200, "application/json; charset=utf-8", json.dumps({"statutes": rows}).encode("utf-8")

    # 4. Case Precedents
    if method == "GET" and path == "/api/cases":
        q = (query_params.get("q", [""])[0]).lower()
        conn = get_db()
        if q:
            cur = conn.cursor().execute(
                "SELECT * FROM case_law WHERE lower(caseName) LIKE ? OR lower(legalIssues) LIKE ? OR lower(holding) LIKE ?",
                (f"%{q}%", f"%{q}%", f"%{q}%")
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
                "title": "Can They Do This? — Legal Powers Assessment",
                "summary": "Assessment under Kenyan constitutional and statutory law.",
                "sections": [
                    {"heading": "1. What they may legally do", "items": ["Institutions may conduct inquiries in line with established written rules."]},
                    {"heading": "2. What they CANNOT simply do", "items": [
                        "Cannot penalize without advance written notice stating allegations.",
                        "Cannot bypass fair hearing (FAAA 2015 s. 4(3)).",
                        "Cannot act without providing prompt written reasons (Article 47(2))."
                    ]},
                    {"heading": "3. Procedural requirements", "items": ["Advance show-cause letter, impartial committee, and right to respond."]},
                    {"heading": "4. What you can do now", "items": ["Submit an immediate written objection asserting Article 47 due process rights."]}
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
                    {"heading": "Route 3: Ombudsman (CAJ)", "items": ["File a maladministration complaint with CAJ (Ombudsman) under CAJ Act 2011."]},
                    {"heading": "Route 4: Judicial Review", "items": ["Apply under Order 53 Civil Procedure Rules within 6 months."]}
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

        # Simple legal definition check
        if low.startswith("what is a contract") or low == "what is a contract?":
            reply = (
                "Under Kenyan law (**Law of Contract Act - Cap 23**), a **contract** is an agreement enforceable by law. "
                "Essential elements: Offer, Acceptance, Intention to create legal relations, Consideration, and Contractual Capacity."
            )
            return 200, "application/json; charset=utf-8", json.dumps({
                "replyText": reply,
                "isSimpleQuestion": True,
                "casePanel": {"stage": "Informational", "issues": ["Contract Law"], "keyFacts": [], "nextStep": "Ready for questions."}
            }).encode("utf-8")

        # University suspension scenario
        if "suspend" in low or "suspension" in low or "university" in low:
            questions = [
                {"question": "Did the university give you a written suspension notice?", "whyItMatters": "Determines whether Section 4(3)(a) FAAA was breached."},
                {"question": "Does the notice state the reason for the suspension?", "whyItMatters": "Article 47(2) guarantees an absolute right to written reasons."},
                {"question": "Were you invited to a disciplinary hearing before the decision?", "whyItMatters": "Suspension without hearing is void under Republic v UoN ex parte Wanjiku [2018]."},
                {"question": "Is there an internal appeal process?", "whyItMatters": "Appeals typically have strict 14 to 21-day deadlines."},
                {"question": "When did you receive the suspension decision?", "whyItMatters": "Crucial for calculating limitation periods."}
            ]
            q_text = "\\n".join([f"**{i+1}. {q['question']}**\\n*Why this matters:* {q['whyItMatters']}\\n" for i, q in enumerate(questions)])
            reply = (
                f"I can help you work through this under Kenyan administrative law. I need to investigate **5 material questions** first:\\n\\n"
                f"{q_text}\\n"
                f"As you provide your answers, your **Case Workspace** will update automatically."
            )
            return 200, "application/json; charset=utf-8", json.dumps({
                "replyText": reply,
                "isInvestigationMode": True,
                "targetedQuestions": questions,
                "clarifyingQuestions": [q["question"] for q in questions],
                "casePanel": {
                    "stage": "Investigation",
                    "issues": ["Right to Fair Administrative Action (Art 47)", "Procedural Fairness (FAAA 2015)"],
                    "keyFacts": [{"type": "Reported Fact", "text": "University suspension without prior hearing"}],
                    "nextStep": "Answer the clarifying questions above."
                }
            }).encode("utf-8")

        # Fallback analysis
        reply = (
            "### ⚖️ Kenyan Legal Assessment\\n\\n"
            "**1. Principles Applied:** Article 47 (Fair Administrative Action) and natural justice.\\n"
            "**2. Procedural Notice:** Any adverse administrative action requires prior notice, opportunity to be heard, and written reasons.\\n"
            "**3. Recommended Next Step:** Document your factual timeline and preserve all correspondence under Section 106B of the Evidence Act."
        )
        return 200, "application/json; charset=utf-8", json.dumps({
            "replyText": reply,
            "casePanel": {"stage": "Intake", "issues": ["Administrative Law"], "keyFacts": [], "nextStep": "Preserve all written evidence."}
        }).encode("utf-8")

    # 7. Workspace
    if method == "GET" and path == "/api/workspace":
        conn = get_db()
        c_row = conn.cursor().execute("SELECT * FROM workspace_cases LIMIT 1").fetchone()
        facts = [dict(r) for r in conn.cursor().execute("SELECT * FROM workspace_facts").fetchall()]
        evidence = [dict(r) for r in conn.cursor().execute("SELECT * FROM workspace_evidence").fetchall()]
        conn.close()
        return 200, "application/json; charset=utf-8", json.dumps({
            "caseDetails": dict(c_row) if c_row else None,
            "facts": facts,
            "evidence": evidence
        }).encode("utf-8")

    # 8. Document Generation
    if method == "POST" and path in ["/api/document/generate", "/api/documents/generate"]:
        user_facts = body_dict.get("userFacts", {})
        c_name = user_facts.get("complainantName") or "Complainant"
        inst_name = user_facts.get("institutionName") or "Institution Authority"
        content = (
            f"DATE: {datetime.datetime.now().strftime('%d %B %Y')}\\n\\n"
            f"TO:\\n{inst_name}\\nP.O. Box [Address]\\nKenya\\n\\n"
            f"RE: FORMAL COMPLAINT UNDER ARTICLE 47 CONSTITUTION OF KENYA AND SECTION 4 FAAA 2015\\n\\n"
            f"I, {c_name}, hereby submit this formal complaint regarding unfair administrative actions taken without due process."
        )
        return 200, "application/json; charset=utf-8", json.dumps({
            "title": "Formal Complaint (Art. 47 & FAAA 2015)",
            "content": content,
            "factsUsed": list(user_facts.keys())
        }).encode("utf-8")

    # 9. Admin Metrics
    if method == "GET" and path == "/api/admin/metrics":
        conn = get_db()
        cur = conn.cursor()
        c_cnt = cur.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        s_cnt = cur.execute("SELECT COUNT(*) FROM legal_statutes").fetchone()[0]
        l_cnt = cur.execute("SELECT COUNT(*) FROM case_law").fetchone()[0]
        f_cnt = cur.execute("SELECT COUNT(*) FROM failed_searches").fetchone()[0]
        conn.close()
        return 200, "application/json; charset=utf-8", json.dumps({
            "totalCases": max(c_cnt, 1),
            "totalStatutes": s_cnt,
            "totalSuperiorCourtCases": l_cnt,
            "totalFailedSearches": f_cnt
        }).encode("utf-8")

    return 404, "application/json", json.dumps({"error": "Not found"}).encode("utf-8")

class LegalAssistantHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        code, ctype, body = dispatch_request("GET", parsed.path, params, {})
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
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

def app(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("PATH_INFO", "/")
    query = urllib.parse.parse_qs(environ.get("QUERY_STRING", ""))
    body_dict = {}
    try:
        size = int(environ.get("CONTENT_LENGTH", 0) or 0)
        if size > 0:
            body_dict = json.loads(environ["wsgi.input"].read(size).decode("utf-8"))
    except Exception:
        pass
    code, ctype, body = dispatch_request(method, path, query, body_dict)
    status_map = {200: "200 OK", 400: "400 Bad Request", 404: "404 Not Found", 500: "500 Internal Server Error"}
    start_response(status_map.get(code, f"{code} OK"), [("Content-Type", ctype), ("Content-Length", str(len(body)))])
    return [body]

if __name__ == "__main__":
    init_db()
    server = ThreadingServer(("0.0.0.0", PORT), LegalAssistantHandler)
    print(f"Kenya Legal Assistant active on http://0.0.0.0:{PORT}")
    server.serve_forever()
