import sys, math, re
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QTimer
import serial
from serial.tools import list_ports
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPainterPath
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QFrame,QSlider,QDoubleSpinBox,QComboBox,QPlainTextEdit,QLineEdit,QGroupBox,QSizePolicy)
BLUE='#0953a2'; LIGHT='#e7f2fc'; BORDER='#c6d5e5'

def label(t,bold=False,size=11,color='#111111'):
 x=QLabel(t); x.setStyleSheet(f'color:{color};font-size:{size}px;'+('font-weight:700;' if bold else ''));return x

def button(t):
 x=QPushButton(t);x.setMinimumHeight(40);return x

class Schematic(QWidget):
 def __init__(self): super().__init__();self.setMinimumHeight(196)
 def paintEvent(self,e):
  p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);w=self.width();h=self.height();cx=w/2;cy=h*.45
  p.setPen(QPen(QColor('#0758b2'),2));p.drawLine(int(w*.18),int(cy),int(w*.82),int(cy))
  p.setPen(QPen(QColor('#172d48'),2));p.setBrush(QColor('#ffda7c'));p.drawRect(QRectF(cx-70,cy-36,140,72))
  path=QPainterPath(QPointF(cx-45,cy));
  for dx,dy in [(-27,0),(-19,-12),(-10,12),(0,-12),(10,12),(19,0),(45,0)]:path.lineTo(cx+dx,cy+dy)
  p.drawPath(path);p.setBrush(QColor('white'))
  for x in [w*.18,w*.82]:p.drawEllipse(QPointF(x,cy),9,9)
  p.setPen(QColor('#111'));p.setFont(QFont('Arial',11));p.drawText(QRectF(w*.02,cy-30,w*.16,65),Qt.AlignCenter,'RF IN\n50 Ω');p.drawText(QRectF(w*.82,cy-30,w*.17,65),Qt.AlignCenter,'RF OUT\n50 Ω')
  p.setFont(QFont('Arial',12,QFont.Bold));p.drawText(QRectF(cx-90,cy+42,180,24),Qt.AlignCenter,'PE4302')
  p.setFont(QFont('Arial',10));p.drawText(QRectF(cx-130,cy+65,260,45),Qt.AlignHCenter,'0 … 31,5 dB\n0,5 dB Schritte')

class LevelCalculator(QWidget):
 """Theoretischer HF-Pegel- und Spannungsrechner für 50 Ohm, Sinussignal."""
 def __init__(self):
  super().__init__()
  layout=QVBoxLayout(self);layout.setContentsMargins(8,3,8,3);layout.setSpacing(5)
  row=QHBoxLayout();row.addWidget(label('RF IN:',True,13))
  self.input=QDoubleSpinBox();self.input.setRange(-120.0,40.0);self.input.setDecimals(1);self.input.setSingleStep(1.0);self.input.setSuffix(' dBm');self.input.setValue(0.0);self.input.setMinimumHeight(29)
  self.input.valueChanged.connect(self.recalculate);row.addWidget(self.input,1)
  row.addWidget(label('Dämpfung:',size=12));self.attenuation=label('10,5 dB',True,14,BLUE);row.addWidget(self.attenuation);layout.addLayout(row)
  grid=QGridLayout();grid.setHorizontalSpacing(10);grid.setVerticalSpacing(10)
  grid.addWidget(label('50 Ω · Sinus',size=11,color='#53647a'),0,0)
  for col, heading in ((1, 'RF IN'), (2, 'RF OUT')):
   h=label(heading,True,13,BLUE)
   h.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
   grid.addWidget(h,0,col)
  self.fields={}
  for idx,(key,title) in enumerate([('dbm','Pegel'),('mw','Leistung'),('rms','U RMS'),('peak','U Peak'),('pp','U Spitze-Spitze')],1):
   grid.addWidget(label(title,size=12),idx,0)
   for col in (1,2):
    v=label('–',col==2,12,BLUE if col==2 else '#222222');v.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter);v.setContentsMargins(0,0,0,0)
    grid.addWidget(v,idx,col);self.fields[(key,col)]=v
  grid.setColumnStretch(0,2);grid.setColumnStretch(1,3);grid.setColumnStretch(2,3)
  layout.addLayout(grid);layout.addStretch()
  note=label('Theoretisch · ohne Einfügedämpfung und Frequenzkorrektur',size=10,color='#65758a');note.setWordWrap(True);layout.addWidget(note)
  self.att=10.5;self.recalculate()
 def set_attenuation(self,att):
  self.att=att;self.recalculate()
 @staticmethod
 def voltage(v):
  av=abs(v)
  if av<0.001:return f'{v*1e6:.3g} µV'.replace('.',',')
  if av<1:return f'{v*1000:.0f} mV'
  return f'{v:.4g} V'.replace('.',',')
 @staticmethod
 def power(mw):
  if mw<0.001:return f'{mw*1e6:.3g} nW'.replace('.',',')
  if mw<1:return f'{mw*1000:.4g} µW'.replace('.',',')
  if mw<1000:return f'{mw:.4g} mW'.replace('.',',')
  return f'{mw/1000:.4g} W'.replace('.',',')
 def recalculate(self,*args):
  self.attenuation.setText(f'{self.att:.1f} dB'.replace('.',','))
  for col,dbm in [(1,self.input.value()),(2,self.input.value()-self.att)]:
   mw=10**(dbm/10);rms=math.sqrt(mw*.001*50)
   values={'dbm':f'{dbm:.1f} dBm'.replace('.',','),'mw':self.power(mw),'rms':self.voltage(rms),'peak':self.voltage(rms*math.sqrt(2)),'pp':self.voltage(rms*2*math.sqrt(2))}
   for key,val in values.items():self.fields[(key,col)].setText(val)

class Main(QMainWindow):
 def __init__(self):
  super().__init__();self.setWindowTitle('PE4302 Attenuator Controller v1.01 – by OE9SAU');self.resize(1500,1010);self.setMinimumSize(1160,800)
  self.ser=None;self.rx_buffer=b'';self.att=10.5;self.step=0.5;self.presets=[0.,10.,20.,31.5];self.selected=0
  root=QWidget();self.setCentralWidget(root);outer=QVBoxLayout(root);outer.setContentsMargins(12,10,12,10);outer.setSpacing(9)
  top=QHBoxLayout();top.setSpacing(10);outer.addLayout(top,3)
  left=QVBoxLayout();title=label('PE4302 Digital Step Attenuator',True,22,'white');title.setStyleSheet('background:#0953a2;color:white;font-size:22px;font-weight:700;padding:11px;border-radius:4px');left.addWidget(title)
  specs=QGridLayout();specs.setContentsMargins(12,8,4,4);specs.setHorizontalSpacing(8)
  for i,(k,v) in enumerate([('Frequenzbereich:','DC – 4 GHz'),('Dämpfungsbereich:','0 – 31,5 dB'),('Schrittweite:','0,5 dB (6 Bit)'),('Impedanz:','50 Ω'),('Steuerung:','Seriell (3-Wire) oder Parallel')]):specs.addWidget(label(k,size=14),i,0);specs.addWidget(label(v,size=14),i,1)
  left.addLayout(specs);left.addStretch();top.addWidget(self.panel(left),31)
  s=QVBoxLayout();s.addWidget(label('Dämpfungsglied (vereinfachtes Schema)',True,16));s.addWidget(Schematic(),1);top.addWidget(self.panel(s),33)
  c=QVBoxLayout();c.addWidget(label('HF-Pegel- und Spannungsrechner (50 Ω)',True,16));self.level_calculator=LevelCalculator();c.addWidget(self.level_calculator,1);top.addWidget(self.panel(c),36)
  middle=QHBoxLayout();middle.setSpacing(10);outer.addLayout(middle,4)
  a=QVBoxLayout();a.addWidget(label('Dämpfung einstellen',True,17,BLUE));displayrow=QHBoxLayout();self.big=label('',True,86,BLUE);self.big.setAlignment(Qt.AlignCenter);displayrow.addWidget(self.big,1)
  lim=QVBoxLayout();bmax=button('MAX\n31,5 dB');bmin=button('MIN\n0 dB');bmax.clicked.connect(lambda:self.request_att(31.5));bmin.clicked.connect(lambda:self.request_att(0));lim.addWidget(bmax);lim.addWidget(bmin);displayrow.addLayout(lim);a.addLayout(displayrow,3)
  self.slider=QSlider(Qt.Horizontal);self.slider.setRange(0,63);self.slider.valueChanged.connect(lambda v:self.request_att(v*.5));a.addWidget(self.slider)
  ticks=QHBoxLayout();
  for n in ['0','5','10','15','20','25','30','31,5']:ticks.addWidget(label(n,size=12));
  a.addLayout(ticks)
  controls=QHBoxLayout();steps=QVBoxLayout();steps.addWidget(label('Schrittweite',True,14));sb=QHBoxLayout();self.stepbuttons=[]
  for val in [.5,1,3,6]:
   btn=button(str(val).replace('.',',')+' dB');btn.clicked.connect(lambda checked=False,v=val:self.set_step(v));sb.addWidget(btn);self.stepbuttons.append((val,btn))
  steps.addLayout(sb);controls.addLayout(steps,4)
  steplay=QVBoxLayout();steplay.addWidget(label('Schritt',True,14));sr=QHBoxLayout();minus=button('◀  –');plus=button('+  ▶');minus.clicked.connect(lambda:self.request_att(self.att-self.step));plus.clicked.connect(lambda:self.request_att(self.att+self.step));sr.addWidget(minus);sr.addWidget(plus);steplay.addLayout(sr);controls.addLayout(steplay,2)
  direct=QVBoxLayout();direct.addWidget(label('Direkteingabe',True,14));dr=QHBoxLayout();self.spin=QDoubleSpinBox();self.spin.setRange(0,31.5);self.spin.setSingleStep(.5);self.spin.setDecimals(1);self.spin.setMinimumHeight(40);dr.addWidget(self.spin);dr.addWidget(label('dB',size=14));setb=button('Setzen');setb.clicked.connect(self.apply_direct_input);self.spin.lineEdit().returnPressed.connect(self.apply_direct_input);dr.addWidget(setb);direct.addLayout(dr);controls.addLayout(direct,3);a.addLayout(controls)
  middle.addWidget(self.panel(a),59)
  pres=QVBoxLayout();pres.addWidget(label('Speicherplätze',True,17,BLUE));pg=QGridLayout();self.pbuttons=[]
  for i in range(4):
   b=button('');b.setMinimumHeight(83);b.clicked.connect(lambda checked=False,n=i:self.choose_preset(n));pg.addWidget(b,i//2,i%2);self.pbuttons.append(b)
  pres.addLayout(pg);pres.addStretch();pr=QHBoxLayout();store=button('Speichern');recall=button('Abrufen');store.clicked.connect(self.store);recall.clicked.connect(self.recall);pr.addWidget(store);pr.addWidget(recall);pres.addLayout(pr);middle.addWidget(self.panel(pres),19)
  con=QVBoxLayout();con.addWidget(label('Verbindung',True,17,BLUE));con.addWidget(label('COM-Port:',size=14));portrow=QHBoxLayout();self.ports=QComboBox();self.ports.setMinimumHeight(39);portrow.addWidget(self.ports);refresh=button('⟳');refresh.setMaximumWidth(46);refresh.clicked.connect(self.refresh_ports);portrow.addWidget(refresh);con.addLayout(portrow)
  br=QHBoxLayout();br.addWidget(label('Baudrate:',size=14));self.baud=QComboBox();self.baud.addItems(['38400','115200','57600','9600']);br.addWidget(self.baud);con.addLayout(br)
  self.state=label('●   Nicht verbunden',size=14);self.state.setStyleSheet('background:#edf2f6;color:#222;padding:18px;border-radius:5px');con.addWidget(self.state);cr=QHBoxLayout()
  self.connect_btn=button('Verbinden');self.connect_btn.clicked.connect(self.connect_device);cr.addWidget(self.connect_btn)
  self.disconnect_btn=button('Trennen');self.disconnect_btn.clicked.connect(self.disconnect_device);self.disconnect_btn.setEnabled(False);cr.addWidget(self.disconnect_btn)
  con.addLayout(cr);con.addStretch();middle.addWidget(self.panel(con),21)
  bottom=QHBoxLayout();bottom.setSpacing(10);outer.addLayout(bottom,4)
  commands=QVBoxLayout();commands.addWidget(label('Befehle',True,16,BLUE));cmds=[('ATT <Wert>','Dämpfung setzen (0 … 31,5 dB, Schritt 0,5 dB)'),('ATT?','Aktuelle Dämpfung abfragen'),('STEP +0.5','Dämpfung um Schritt erhöhen'),('STEP -0.5','Dämpfung um Schritt verringern'),('MIN','0 dB einstellen'),('MAX','31,5 dB einstellen'),('PRESET 1','Speicherplatz 1 abrufen'),('STORE 1','Aktuelle Dämpfung in Speicherplatz 1 speichern'),('SWEEP 0 31.5 0.5 100','Sweep von 0 bis 31,5 dB, 0,5 dB Schritte, 100 ms'),('IDN?','Gerätekennung abfragen'),('HELP','Befehlsübersicht')]
  for i,(cmd,desc) in enumerate(cmds):
   line=QHBoxLayout();line.setContentsMargins(5,2,5,2);cl=label(cmd,size=12,color='#0759cf');cl.setMinimumWidth(175);line.addWidget(cl);line.addWidget(label(desc,size=11),1);w=QWidget();w.setLayout(line);w.setStyleSheet('background:#edf2f6' if i%2==0 else 'background:white');commands.addWidget(w)
  commands.addStretch();bottom.addWidget(self.panel(commands),44)
  terminal=QVBoxLayout();hd=QHBoxLayout();hd.addWidget(label('Kommando-/Statusanzeige',True,16,BLUE));hd.addStretch();clear=button('Löschen');clear.setMaximumWidth(115);clear.clicked.connect(lambda:self.console.clear());hd.addWidget(clear);terminal.addLayout(hd)
  self.console=QPlainTextEdit();self.console.setReadOnly(True);self.console.setStyleSheet('background:#0d151d;color:#43e77d;font:13px Consolas;border:0;border-radius:4px');terminal.addWidget(self.console,1)
  entry=QHBoxLayout();self.command=QLineEdit();self.command.setPlaceholderText('z.B. ATT 10.5 oder HELP');self.command.setMinimumHeight(39);self.command.returnPressed.connect(self.run_command);send=button('Senden');send.clicked.connect(self.run_command);entry.addWidget(self.command,1);entry.addWidget(send);terminal.addLayout(entry);bottom.addWidget(self.panel(terminal),56)
  self.set_step(.5);self.set_att(10.5);self.refresh_presets();self.refresh_ports();self.log('PE4302 Controller v1.01 – by OE9SAU\nUSB: 38400 Baud; Arduino V3.0')
  self.poll_timer=QTimer(self);self.poll_timer.timeout.connect(self.poll_serial);self.poll_timer.start(30)
 def panel(self,layout):
  f=QFrame();f.setObjectName('panel');f.setLayout(layout);f.setStyleSheet('QFrame#panel{background:#fafcff;border:1px solid #c6d5e5;border-radius:5px;}');layout.setContentsMargins(13,9,13,10);return f
 def set_att(self,v,update_slider=True):
  self.att=max(0,min(31.5,round(v*2)/2));self.level_calculator.set_attenuation(self.att);self.big.setText(f'{self.att:.1f} dB');self.spin.blockSignals(True);self.spin.setValue(self.att);self.spin.blockSignals(False)
  if update_slider:self.slider.blockSignals(True);self.slider.setValue(round(self.att*2));self.slider.blockSignals(False)
 def apply_direct_input(self):
  # Commit the value still being edited before reading the spin box.
  self.spin.interpretText()
  value=self.spin.value()
  self.request_att(value)
 def set_step(self,v):
  self.step=v
  for n,b in self.stepbuttons:b.setStyleSheet('background:#dcecff;border:2px solid #1261d7;color:#0044ac;font-weight:bold;' if n==v else '')
 def refresh_presets(self):
  for i,b in enumerate(self.pbuttons):b.setText(f'P{i+1}\n{self.presets[i]:.1f} dB');b.setStyleSheet('background:#dcecff;border:2px solid #1261d7;' if i==self.selected else '')
 def choose_preset(self,n):self.selected=n;self.refresh_presets();self.recall()
 def store(self):self.presets[self.selected]=self.att;self.refresh_presets();self.log(f'OK: P{self.selected+1} gespeichert ({self.att:.1f} dB)')
 def recall(self):self.request_att(self.presets[self.selected]);self.log(f'P{self.selected+1} abgerufen')
 def log(self,s):self.console.appendPlainText(s)
 def refresh_ports(self):
  current=self.ports.currentText();ports=[p.device for p in list_ports.comports()]
  self.ports.clear();self.ports.addItems(ports)
  if current in ports:self.ports.setCurrentText(current)
  elif 'COM6' in ports:self.ports.setCurrentText('COM6')
  if not ports:self.log('Kein serieller Anschluss gefunden.') if hasattr(self,'console') else None
 def connect_device(self):
  if self.ser:return
  port=self.ports.currentText()
  if not port:self.log('ERR: Bitte COM-Port auswählen.');return
  try:
   self.ser=serial.Serial(port,int(self.baud.currentText()),timeout=0,write_timeout=.5)
   self.rx_buffer=b''
   self.state.setText('●   Verbunden: '+port)
   self.connect_btn.setEnabled(False);self.disconnect_btn.setEnabled(True)
   self.log('Verbunden mit '+port+' (Arduino kann beim Öffnen neu starten)')
   # Arduino Uno/Nano setzt beim Öffnen des COM-Ports meist zurück.
   QTimer.singleShot(2200,self.query_status)
  except (serial.SerialException,OSError,ValueError) as e:
   self.ser=None;self.log('ERR Verbindung: '+str(e))
 def query_status(self):
  if self.ser:self.send_serial('STATUS?')
 def disconnect_device(self):
  if self.ser:
   try:self.ser.close()
   except (serial.SerialException,OSError):pass
  self.ser=None;self.rx_buffer=b''
  self.state.setText('●   Nicht verbunden')
  self.connect_btn.setEnabled(True);self.disconnect_btn.setEnabled(False)
  self.log('Verbindung getrennt')
 def send_serial(self,cmd):
  if not self.ser:
   self.log('ERR: Nicht verbunden – Befehl nicht gesendet');return False
  try:
   self.ser.write((cmd+'\n').encode('ascii'))
   self.log('> '+cmd);return True
  except (serial.SerialException,OSError) as e:
   self.log('ERR Senden: '+str(e));self.disconnect_device();return False
 def request_att(self,value):
  value=max(0,min(31.5,round(value*2)/2))
  self.send_serial(f'ATT {value:.1f}')
  # Die Anzeige wird erst mit der Arduino-Rückmeldung aktualisiert.
 def poll_serial(self):
  if not self.ser:return
  try:
   count=self.ser.in_waiting
   if count:
    self.rx_buffer+=self.ser.read(min(count,1024))
    if len(self.rx_buffer)>4096:self.rx_buffer=b'';self.log('ERR: Empfangspuffer zurückgesetzt')
    while b'\n' in self.rx_buffer:
     raw,self.rx_buffer=self.rx_buffer.split(b'\n',1)
     line=raw.decode('utf-8',errors='replace').strip()
     if line:self.handle_response(line)
  except (serial.SerialException,OSError) as e:
   self.log('ERR Empfang: '+str(e));self.disconnect_device()
 def handle_response(self,line):
  self.log('< '+line)
  if line.startswith('STATUS '):
   values=dict(re.findall(r'(ATT|REAL|CORR)=(-?\d+(?:\.\d+)?)',line))
   if 'ATT' in values:self.set_att(float(values['ATT']))
  elif line.startswith('EVENT ATT ') or line.startswith('OK ATT ') or line.startswith('ATT '):
   try:self.set_att(float(line.split()[-1]))
   except ValueError:pass
 def run_command(self):
  raw=self.command.text().strip();self.command.clear()
  if not raw:return
  parts=raw.upper().split();cmd=parts[0]
  try:
   if cmd in ('PRESET','STORE') and len(parts)==2:
    n=int(parts[1]);assert 1<=n<=4
    self.selected=n-1;self.refresh_presets()
    self.recall() if cmd=='PRESET' else self.store()
   elif cmd=='SWEEP':self.log('SWEEP wird von Arduino V3.0 nicht unterstützt.')
   else:self.send_serial(raw.replace(',','.'))
  except (ValueError,AssertionError):self.log('ERR: Ungültiger Parameter')
 def closeEvent(self,event):
  if self.ser:
   try:self.ser.close()
   except (serial.SerialException,OSError):pass
  event.accept()

if __name__=='__main__':
 app=QApplication(sys.argv);app.setStyle('Fusion');app.setStyleSheet('QWidget{font-family:Segoe UI;font-size:12px;} QPushButton{border:1px solid #bdcbd9;border-radius:5px;background:#f5f7fa;padding:4px;} QPushButton:hover{background:#e0edff;} QComboBox,QDoubleSpinBox,QLineEdit{border:1px solid #bdcbd9;border-radius:4px;background:white;padding:4px;}');w=Main();w.show();sys.exit(app.exec())
