import json, os, sqlite3, uuid
from datetime import datetime, timedelta, date
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
ROOT=Path(__file__).parent; DB=ROOT/'appointments.db'
SERVICES=[('Electrical systems review',60,180.0,'Power distribution, protection, load flow, and energy monitoring.'),('Automation + control consult',60,180.0,'Instrumentation, IoT, SCADA, and operational visibility.'),('Data science discovery',60,160.0,'Forecasting, anomaly detection, and predictive maintenance.'),('Analytics product session',90,240.0,'Data pipelines, dashboards, and production planning.')]
def db():
 c=sqlite3.connect(DB,timeout=5);c.row_factory=sqlite3.Row;c.execute('PRAGMA journal_mode=WAL');return c
def init():
 c=db();c.execute('CREATE TABLE IF NOT EXISTS services(id INTEGER PRIMARY KEY,name TEXT,duration_minutes INTEGER,price_aud REAL,description TEXT)');c.execute('CREATE TABLE IF NOT EXISTS bookings(id TEXT PRIMARY KEY,service_id INTEGER NOT NULL,location TEXT NOT NULL,start TEXT NOT NULL,end TEXT NOT NULL,name TEXT NOT NULL,email TEXT NOT NULL,note TEXT,payment_status TEXT NOT NULL DEFAULT "pending",created_at TEXT NOT NULL)');c.execute('CREATE UNIQUE INDEX IF NOT EXISTS unique_active_slot ON bookings(start) WHERE payment_status IN ("pending","paid")');
 if c.execute('SELECT COUNT(*) n FROM services').fetchone()['n']==0:c.executemany('INSERT INTO services(name,duration_minutes,price_aud,description) VALUES(?,?,?,?)',SERVICES)
 c.commit();c.close()
def json_body(h):
 n=int(h.headers.get('Content-Length','0'));return json.loads(h.rfile.read(n) or b'{}')
def slots(service_id,day):
 c=db();s=c.execute('SELECT * FROM services WHERE id=?',(service_id,)).fetchone();taken={r['start'] for r in c.execute('SELECT start FROM bookings WHERE date(start)=? AND payment_status IN ("pending","paid")',(day,))};c.close();out=[];d=datetime.fromisoformat(day+'T09:00');end=datetime.fromisoformat(day+'T17:00');
 while d+timedelta(minutes=s['duration_minutes'])<=end:
  iso=d.isoformat(timespec='minutes');
  if d.weekday()<5 and iso not in taken:out.append({'start':iso,'label':d.strftime('%I:%M %p').lstrip('0')})
  d+=timedelta(minutes=30)
 return out
def checkout_url(bid, service, email):
 key=os.getenv("STRIPE_SECRET_KEY")
 if not key:
  return f"/booking-confirmation.html?id={bid}"
 try:
  import stripe
  stripe.api_key=key
  base=os.getenv("PUBLIC_BASE_URL","http://localhost:8000")
  session=stripe.checkout.Session.create(mode="payment",submit_type="book",customer_email=email,success_url=f"{base}/booking-confirmation.html?id={bid}&paid=1",cancel_url=f"{base}/booking-confirmation.html?id={bid}&cancelled=1",line_items=[{"price_data":{"currency":"aud","unit_amount":int(service["price_aud"]*100),"product_data":{"name":service["name"]}},"quantity":1}],metadata={"booking_id":bid})
  return session.url
 except Exception:
  return f"/booking-confirmation.html?id={bid}"

def ics(row):
 return f'BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Your Name//Appointments//EN\nBEGIN:VEVENT\nUID:{row["id"]}@yourname.engineer\nDTSTAMP:{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}\nDTSTART:{row["start"].replace("-","").replace(":","")}00\nDTEND:{row["end"].replace("-","").replace(":","")}00\nSUMMARY:{row["service_name"]}\nDESCRIPTION:Technical session with Your Name\nEND:VEVENT\nEND:VCALENDAR\n'
class App(SimpleHTTPRequestHandler):
 def end(self,code=200,typ='application/json'):self.send_response(code);self.send_header('Content-Type',typ);self.send_header('Access-Control-Allow-Origin','*');self.end_headers()
 def write(self,obj):self.wfile.write(json.dumps(obj).encode())
 def do_OPTIONS(self):self.end(204)
 def do_GET(self):
  u=urlparse(self.path);q=parse_qs(u.query)
  if u.path=='/api/services':
   c=db();self.end();self.write([dict(x) for x in c.execute('SELECT * FROM services')]);c.close();return
  if u.path=='/api/availability':
   try:self.end();self.write({'date':q['date'][0],'slots':slots(int(q['service_id'][0]),q['date'][0])})
   except Exception as e:self.end(400);self.write({'error':str(e)})
   return
  if u.path.startswith('/api/bookings/') and u.path.endswith('/calendar.ics'):
   bid=u.path.split('/')[3];c=db();r=c.execute('SELECT b.*,s.name service_name FROM bookings b JOIN services s ON s.id=b.service_id WHERE b.id=?',(bid,)).fetchone();c.close();
   if not r:self.end(404);self.write({'error':'Booking not found'});return
   self.end(200,'text/calendar');self.wfile.write(ics(r).encode());return
  return super().do_GET()
 def do_POST(self):
  if self.path!='/api/bookings':self.end(404);self.write({'error':'Not found'});return
  try:
   b=json_body(self);c=db();s=c.execute('SELECT * FROM services WHERE id=?',(b['service_id'],)).fetchone();start=datetime.fromisoformat(b['start']);end=start+timedelta(minutes=s['duration_minutes']);
   if start<datetime.now():raise ValueError('Choose a future time')
   bid=uuid.uuid4().hex;c.execute('INSERT INTO bookings(id,service_id,location,start,end,name,email,note,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(bid,s['id'],b['location'],start.isoformat(timespec='minutes'),end.isoformat(timespec='minutes'),b['name'],b['email'],b.get('note',''),datetime.utcnow().isoformat()))
   c.commit();c.close();self.end(201);self.write({'booking_id':bid,'status':'pending_payment','checkout_url':checkout_url(bid,s,b['email'])})
  except sqlite3.IntegrityError:self.end(409);self.write({'error':'That time was just booked. Please choose another available slot.'})
  except Exception as e:self.end(400);self.write({'error':str(e)})
if __name__=='__main__':init();ThreadingHTTPServer(('0.0.0.0',8000),lambda *a,**k:App(*a,directory=str(ROOT),**k)).serve_forever()
