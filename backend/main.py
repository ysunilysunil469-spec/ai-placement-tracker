import os, json, sqlite3
from datetime import datetime, date, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DB='career_passport.db'
app=FastAPI(title='Career Passport AI')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])

def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init():
 c=db(); c.executescript('''CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,email TEXT UNIQUE,college TEXT,branch TEXT,cgpa REAL,backlogs INTEGER,graduation_year INTEGER,skills TEXT,projects TEXT,certifications TEXT,dream_role TEXT,preferred_location TEXT,created_at TEXT);CREATE TABLE IF NOT EXISTS opportunities(id INTEGER PRIMARY KEY AUTOINCREMENT,company TEXT,role TEXT,description TEXT,package TEXT,location TEXT,min_cgpa REAL,branches TEXT,max_backlogs INTEGER,skills TEXT,deadline TEXT);CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY AUTOINCREMENT,student_id INTEGER,opportunity_id INTEGER,status TEXT,applied_at TEXT,updated_at TEXT);CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY AUTOINCREMENT,student_id INTEGER,message TEXT,type TEXT,is_read INTEGER,created_at TEXT);''')
 if c.execute('SELECT COUNT(*) n FROM opportunities').fetchone()['n']==0:
  today=date.today(); data=[('TechNova','AI Engineer','Build AI products and APIs','₹8 LPA','Hyderabad',7.5,'AI,CSE,AIDS',0,'Python,SQL,Machine Learning,REST API',today+timedelta(days=1)),('DataVision','ML Engineer','Machine learning pipelines','₹9 LPA','Bengaluru',7,'AI,CSE,AIDS',1,'Python,NumPy,Pandas,Machine Learning',today+timedelta(days=3)),('CloudCore','Python Backend Developer','Scalable backend services','₹7 LPA','Chennai',7,'AI,CSE,AIDS,IT',1,'Python,SQL,FastAPI,REST API',today+timedelta(days=5)),('InsightLabs','Data Analyst','Business data and insights','₹6 LPA','Pune',6.5,'AI,CSE,AIDS,IT,ECE',2,'Python,SQL,Pandas,Excel',today+timedelta(days=7)),('NextGen AI','GenAI Application Engineer','LLM applications and databases','₹10 LPA','Remote',7.5,'AI,CSE,AIDS',0,'Python,FastAPI,SQL,LLM,REST API',today+timedelta(days=2))]
  c.executemany('INSERT INTO opportunities(company,role,description,package,location,min_cgpa,branches,max_backlogs,skills,deadline) VALUES(?,?,?,?,?,?,?,?,?,?)',[(a,b,c,d,e,f,g,h,i,str(j)) for a,b,c,d,e,f,g,h,i,j in data])
 c.commit(); c.close()
init()

class Student(BaseModel):
 name:str; email:str; college:str=''; branch:str='AI'; cgpa:float=0; backlogs:int=0; graduation_year:int=2027; skills:list[str]=[]; projects:list[str]=[]; certifications:list[str]=[]; dream_role:str='AI Engineer'; preferred_location:str='Any'
class Apply(BaseModel): student_id:int; opportunity_id:int
class AIReq(BaseModel): student_id:int; opportunity_id:int
class Status(BaseModel): status:str

def js(s):
 try:return json.loads(s or '[]')
 except:return []
def student(r):
 return {**dict(r),'skills':js(r['skills']),'projects':js(r['projects']),'certifications':js(r['certifications'])}
def opp(r):
 d=dict(r); d['allowed_branches']=d.pop('branches').split(','); d['required_skills']=d.pop('skills').split(','); return d

def match(s,o):
 ss={x.strip().lower() for x in s['skills']}; rs={x.strip().lower() for x in o['required_skills']}; branches={x.strip().lower() for x in o['allowed_branches']}
 matched=sorted(ss&rs); missing=sorted(rs-ss); cg=s['cgpa']>=o['min_cgpa']; br=s['branch'].lower() in branches; bl=s['backlogs']<=o['max_backlogs']; eligible=cg and br and bl
 skill=100*len(matched)/len(rs) if rs else 100; role=100 if s['dream_role'].lower() in o['role'].lower() or o['role'].lower() in s['dream_role'].lower() else 55; loc=100 if s['preferred_location'].lower() in ('any','') or s['preferred_location'].lower() in o['location'].lower() else 55; score=round(skill*.6+role*.25+loc*.15); score=score if eligible else min(score,49)
 return {'match_score':score,'eligible':eligible,'matched_skills':matched,'missing_skills':missing,'eligibility':{'cgpa':cg,'branch':br,'backlogs':bl}}

def ai_text(s,o,m):
 gaps=', '.join(m['missing_skills']) or 'no major gaps'; return f'''WHY YOU MATCH\nYou have a {m["match_score"]}% profile match for {o["company"]} {o["role"]}. Your strongest matched skills are {', '.join(m['matched_skills']) or 'still developing'}.\n\nTOP SKILL GAPS\n{gaps}\n\nWHAT TO DO NEXT\nPrioritize {m['missing_skills'][0] if m['missing_skills'] else 'one portfolio project'}, strengthen your best project, and apply before {o['deadline']}.'''

@app.get('/')
def root(): return {'message':'Career Passport AI backend running','database':'connected'}
@app.get('/health')
def health():
 c=db(); out={x:c.execute(f'SELECT COUNT(*) n FROM {x}').fetchone()['n'] for x in ['students','opportunities','applications','notifications']}; c.close(); return {'status':'healthy','database':'connected',**out}
@app.get('/student')
def get_student(email='sunil@example.com'):
 c=db(); r=c.execute('SELECT * FROM students WHERE email=?',(email,)).fetchone(); c.close(); return student(r) if r else None
@app.post('/student')
def save_student(s:Student):
 c=db(); old=c.execute('SELECT id FROM students WHERE email=?',(s.email,)).fetchone(); vals=(s.name,s.email,s.college,s.branch,s.cgpa,s.backlogs,s.graduation_year,json.dumps(s.skills),json.dumps(s.projects),json.dumps(s.certifications),s.dream_role,s.preferred_location,datetime.utcnow().isoformat())
 if old:c.execute('UPDATE students SET name=?,college=?,branch=?,cgpa=?,backlogs=?,graduation_year=?,skills=?,projects=?,certifications=?,dream_role=?,preferred_location=?,created_at=? WHERE email=?',vals[0],vals[2],vals[3],vals[4],vals[5],vals[6],vals[7],vals[8],vals[9],vals[10],vals[11],vals[12],s.email)
 else:c.execute('INSERT INTO students(name,email,college,branch,cgpa,backlogs,graduation_year,skills,projects,certifications,dream_role,preferred_location,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',vals)
 c.commit(); r=c.execute('SELECT * FROM students WHERE email=?',(s.email,)).fetchone(); c.close(); return student(r)
@app.get('/matches')
def matches(student_id:int):
 c=db(); s=student(c.execute('SELECT * FROM students WHERE id=?',(student_id,)).fetchone()); rows=c.execute('SELECT * FROM opportunities').fetchall(); c.close(); return sorted([{**opp(o),**match(s,opp(o))} for o in rows],key=lambda x:x['match_score'],reverse=True)
@app.get('/career-score')
def score(student_id:int):
 c=db(); s=student(c.execute('SELECT * FROM students WHERE id=?',(student_id,)).fetchone()); c.close(); return {'score':max(0,min(100,round(len(s['skills'])*12*.35+len(s['projects'])*25*.2+len(s['certifications'])*20*.1+s['cgpa']/10*100*.35-s['backlogs']*12)))}
@app.post('/ai/analyze')
def analyze(x:AIReq):
 c=db(); sr=c.execute('SELECT * FROM students WHERE id=?',(x.student_id,)).fetchone(); orow=c.execute('SELECT * FROM opportunities WHERE id=?',(x.opportunity_id,)).fetchone(); c.close(); s=student(sr); o=opp(orow); m=match(s,o); return {'powered_by':'Career Passport AI','text':ai_text(s,o,m)}
@app.post('/applications')
def apply(x:Apply):
 c=db(); r=c.execute('SELECT id,status FROM applications WHERE student_id=? AND opportunity_id=?',(x.student_id,x.opportunity_id)).fetchone()
 if r:return {'message':'Already applied','application_id':r['id'],'status':r['status']}
 now=datetime.utcnow().isoformat(); cur=c.execute('INSERT INTO applications(student_id,opportunity_id,status,applied_at,updated_at) VALUES(?,?,?,?,?)',(x.student_id,x.opportunity_id,'Applied',now,now)); c.commit(); aid=cur.lastrowid; c.close(); return {'message':'Application saved','application_id':aid,'status':'Applied'}
@app.get('/applications')
def applications(student_id:int):
 c=db(); rows=c.execute('SELECT a.*,o.company,o.role,o.package,o.location,o.deadline FROM applications a JOIN opportunities o ON o.id=a.opportunity_id WHERE a.student_id=? ORDER BY a.id DESC',(student_id,)).fetchall(); c.close(); return [dict(r) for r in rows]
@app.get('/notifications')
def notifications(student_id:int):
 c=db(); today=date.today().isoformat(); exists=c.execute("SELECT id FROM notifications WHERE student_id=? AND type='career_pulse' AND created_at LIKE ?",(student_id,today+'%')).fetchone()
 if not exists:
  s=student(c.execute('SELECT * FROM students WHERE id=?',(student_id,)).fetchone()); rows=c.execute('SELECT * FROM opportunities').fetchall(); best=max(( {**opp(o),**match(s,opp(o))} for o in rows),key=lambda x:x['match_score']); msg=f'Good morning, {s["name"].split()[0]}! {best["company"]} has a {best["match_score"]}% match for you. Today: review the opportunity and close your biggest skill gap.'; c.execute('INSERT INTO notifications(student_id,message,type,is_read,created_at) VALUES(?,?,?,?,?)',(student_id,msg,'career_pulse',0,datetime.utcnow().isoformat())); c.commit()
 rows=c.execute('SELECT * FROM notifications WHERE student_id=? ORDER BY id DESC LIMIT 10',(student_id,)).fetchall(); c.close(); return [dict(r) for r in rows]
@app.get('/officer/applications')
def officer():
 c=db(); rows=c.execute('SELECT a.*,s.name,s.branch,s.cgpa,o.company,o.role FROM applications a JOIN students s ON s.id=a.student_id JOIN opportunities o ON o.id=a.opportunity_id ORDER BY a.id DESC').fetchall(); c.close(); return [dict(r) for r in rows]
@app.put('/officer/applications/{aid}/status')
def status(aid:int,x:Status):
 c=db(); c.execute('UPDATE applications SET status=?,updated_at=? WHERE id=?',(x.status,datetime.utcnow().isoformat(),aid)); c.commit(); c.close(); return {'ok':True,'status':x.status}
