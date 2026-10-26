import sys, math, re
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QTimer
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

class Chart(QWidget):
 def __init__(self):super().__init__();self.setMinimumHeight(196)
 def paintEvent(self,e):
  p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);w=self.width();h=self.height();l=61;r=w-15;t=19;b=h-42
  p.setPen(QPen(QColor('#b9c5d1'),1))
  for i in range(9):
   x=l+(r-l)*i/8;p.drawLine(int(x),t,int(x),b)
  for i in range(9):
   y=t+(b-t)*i/8;p.drawLine(l,int(y),r,int(y))
  p.setPen(QPen(QColor('#111'),1));p.drawRect(l,t,r-l,b-t)
  p.setFont(QFont('Arial',9))
  for v in [0,-10,-20,-30,-40]:
   y=t+(-v/40)*(b-t);p.drawText(QRectF(14,y-9,40,18),Qt.AlignRight,str(v))
  for val in [1,10,100,1000,4000]:
   x=l+(math.log10(val)/math.log10(4000))*(r-l);p.drawText(QRectF(x-23,b+3,46,18),Qt.AlignCenter,str(val))
  p.drawText(QRectF(l,b+22,r-l,19),Qt.AlignCenter,'Frequenz (MHz)')
  p.save();p.translate(10,t+(b-t)/2);p.rotate(-90);p.drawText(QRectF(-(b-t)/2,-10,b-t,18),Qt.AlignCenter,'Dämpfung (dB)');p.restore()
  for att,color in [(0,'#0863ee'),(10,'#008b28'),(20,'#ff9400'),(31.5,'#e22a32')]:
   path=QPainterPath()
   for i in range(150):
    f=10**(math.log10(4000)*i/149);drop=3.5*(f/4000)**.8+att*.08*(f/4000)**.7
    db=-att-drop;x=l+(r-l)*i/149;y=t+(-db/40)*(b-t)
    if i==0:path.moveTo(x,y)
    else:path.lineTo(x,y)
   p.setPen(QPen(QColor(color),2));p.drawPath(path)
  # Legend
  lx=l+12;ly=b-75;p.setPen(QColor('#b4b4b4'));p.setBrush(QColor('#ffffff'));p.drawRoundedRect(QRectF(lx,ly,98,71),4,4)
  for i,(txt,color) in enumerate([('0 dB','#0863ee'),('10 dB','#008b28'),('20 dB','#ff9400'),('31,5 dB','#e22a32')]):
   yy=ly+11+i*16;p.setPen(QPen(QColor(color),2));p.drawLine(lx+8,int(yy),lx+33,int(yy));p.setPen(QColor('#111'));p.drawText(QRectF(lx+40,yy-9,58,18),Qt.AlignVCenter,txt)

class Main(QMainWindow):
 def __init__(self):
  super().__init__();self.setWindowTitle('PE4302 Attenuator Controller v2.0 (Simulation) – by OE9SAU');self.resize(1500,1010);self.setMinimumSize(1160,800)
  self.att=10.5;self.step=0.5;self.presets=[0.,10.,20.,31.5];self.selected=0
  root=QWidget();self.setCentralWidget(root);outer=QVBoxLayout(root);outer.setContentsMargins(12,10,12,10);outer.setSpacing(9)
  top=QHBoxLayout();top.setSpacing(10);outer.addLayout(top,3)
  left=QVBoxLayout();title=label('PE4302 Digital Step Attenuator',True,22,'white');title.setStyleSheet('background:#0953a2;color:white;font-size:22px;font-weight:700;padding:11px;border-radius:4px');left.addWidget(title)
  specs=QGridLayout();specs.setContentsMargins(12,8,4,4);specs.setHorizontalSpacing(8)
  for i,(k,v) in enumerate([('Frequenzbereich:','DC – 4 GHz'),('Dämpfungsbereich:','0 – 31,5 dB'),('Schrittweite:','0,5 dB (6 Bit)'),('Impedanz:','50 Ω'),('Steuerung:','Seriell (3-Wire) oder Parallel')]):specs.addWidget(label(k,size=14),i,0);specs.addWidget(label(v,size=14),i,1)
  left.addLayout(specs);left.addStretch();top.addWidget(self.panel(left),31)
  s=QVBoxLayout();s.addWidget(label('Dämpfungsglied (vereinfachtes Schema)',True,16));s.addWidget(Schematic(),1);top.addWidget(self.panel(s),33)
  c=QVBoxLayout();c.addWidget(label('Dämpfung über Frequenz (typisch)',True,16));c.addWidget(Chart(),1);top.addWidget(self.panel(c),36)
  middle=QHBoxLayout();middle.setSpacing(10);outer.addLayout(middle,4)
  a=QVBoxLayout();a.addWidget(label('Dämpfung einstellen',True,17,BLUE));displayrow=QHBoxLayout();self.big=label('',True,86,BLUE);self.big.setAlignment(Qt.AlignCenter);displayrow.addWidget(self.big,1)
  lim=QVBoxLayout();bmax=button('MAX\n31,5 dB');bmin=button('MIN\n0 dB');bmax.clicked.connect(lambda:self.set_att(31.5));bmin.clicked.connect(lambda:self.set_att(0));lim.addWidget(bmax);lim.addWidget(bmin);displayrow.addLayout(lim);a.addLayout(displayrow,3)
  self.slider=QSlider(Qt.Horizontal);self.slider.setRange(0,63);self.slider.valueChanged.connect(lambda v:self.set_att(v*.5,False));a.addWidget(self.slider)
  ticks=QHBoxLayout();
  for n in ['0','5','10','15','20','25','30','31,5']:ticks.addWidget(label(n,size=12));
  a.addLayout(ticks)
  controls=QHBoxLayout();steps=QVBoxLayout();steps.addWidget(label('Schrittweite',True,14));sb=QHBoxLayout();self.stepbuttons=[]
  for val in [.5,1,3,6]:
   btn=button(str(val).replace('.',',')+' dB');btn.clicked.connect(lambda checked=False,v=val:self.set_step(v));sb.addWidget(btn);self.stepbuttons.append((val,btn))
  steps.addLayout(sb);controls.addLayout(steps,4)
  steplay=QVBoxLayout();steplay.addWidget(label('Schritt',True,14));sr=QHBoxLayout();minus=button('◀  –');plus=button('+  ▶');minus.clicked.connect(lambda:self.set_att(self.att-self.step));plus.clicked.connect(lambda:self.set_att(self.att+self.step));sr.addWidget(minus);sr.addWidget(plus);steplay.addLayout(sr);controls.addLayout(steplay,2)
  direct=QVBoxLayout();direct.addWidget(label('Direkteingabe',True,14));dr=QHBoxLayout();self.spin=QDoubleSpinBox();self.spin.setRange(0,31.5);self.spin.setSingleStep(.5);self.spin.setDecimals(1);self.spin.setMinimumHeight(40);dr.addWidget(self.spin);dr.addWidget(label('dB',size=14));setb=button('Setzen');setb.clicked.connect(self.apply_direct_input);self.spin.lineEdit().returnPressed.connect(self.apply_direct_input);dr.addWidget(setb);direct.addLayout(dr);controls.addLayout(direct,3);a.addLayout(controls)
  middle.addWidget(self.panel(a),59)
  pres=QVBoxLayout();pres.addWidget(label('Speicherplätze',True,17,BLUE));pg=QGridLayout();self.pbuttons=[]
  for i in range(4):
   b=button('');b.setMinimumHeight(83);b.clicked.connect(lambda checked=False,n=i:self.choose_preset(n));pg.addWidget(b,i//2,i%2);self.pbuttons.append(b)
  pres.addLayout(pg);pres.addStretch();pr=QHBoxLayout();store=button('Speichern');recall=button('Abrufen');store.clicked.connect(self.store);recall.clicked.connect(self.recall);pr.addWidget(store);pr.addWidget(recall);pres.addLayout(pr);middle.addWidget(self.panel(pres),19)
  con=QVBoxLayout();con.addWidget(label('Verbindung (später)',True,17,BLUE));con.addWidget(label('COM-Port:',size=14));portrow=QHBoxLayout();self.ports=QComboBox();self.ports.addItems(['COM3','COM4','COM5','Simulation (offline)']);self.ports.setMinimumHeight(39);portrow.addWidget(self.ports);refresh=button('⟳');refresh.setMaximumWidth(46);refresh.clicked.connect(lambda:self.log('SIMULATION: COM-Port-Suche noch nicht aktiv.'));portrow.addWidget(refresh);con.addLayout(portrow)
  br=QHBoxLayout();br.addWidget(label('Baudrate:',size=14));baud=QComboBox();baud.addItems(['115200','57600','9600']);br.addWidget(baud);con.addLayout(br)
  state=label('●   Nicht verbunden\n     (Simulationsmodus)',size=14);state.setStyleSheet('background:#edf2f6;color:#222;padding:18px;border-radius:5px');con.addWidget(state);cr=QHBoxLayout()
  for t in ['Verbinden','Trennen']:
   b=button(t);b.setEnabled(False);cr.addWidget(b)
  con.addLayout(cr);con.addStretch();middle.addWidget(self.panel(con),21)
  bottom=QHBoxLayout();bottom.setSpacing(10);outer.addLayout(bottom,4)
  commands=QVBoxLayout();commands.addWidget(label('Befehle (geplant)',True,16,BLUE));cmds=[('ATT <Wert>','Dämpfung setzen (0 … 31,5 dB, Schritt 0,5 dB)'),('ATT?','Aktuelle Dämpfung abfragen'),('STEP +0.5','Dämpfung um Schritt erhöhen'),('STEP -0.5','Dämpfung um Schritt verringern'),('MIN','0 dB einstellen'),('MAX','31,5 dB einstellen'),('PRESET 1','Speicherplatz 1 abrufen'),('STORE 1','Aktuelle Dämpfung in Speicherplatz 1 speichern'),('SWEEP 0 31.5 0.5 100','Sweep von 0 bis 31,5 dB, 0,5 dB Schritte, 100 ms'),('IDN?','Gerätekennung abfragen'),('HELP','Befehlsübersicht')]
  for i,(cmd,desc) in enumerate(cmds):
   line=QHBoxLayout();line.setContentsMargins(5,2,5,2);cl=label(cmd,size=12,color='#0759cf');cl.setMinimumWidth(175);line.addWidget(cl);line.addWidget(label(desc,size=11),1);w=QWidget();w.setLayout(line);w.setStyleSheet('background:#edf2f6' if i%2==0 else 'background:white');commands.addWidget(w)
  commands.addStretch();bottom.addWidget(self.panel(commands),44)
  terminal=QVBoxLayout();hd=QHBoxLayout();hd.addWidget(label('Kommando-/Statusanzeige (Simulation)',True,16,BLUE));hd.addStretch();clear=button('Löschen');clear.setMaximumWidth(115);clear.clicked.connect(lambda:self.console.clear());hd.addWidget(clear);terminal.addLayout(hd)
  self.console=QPlainTextEdit();self.console.setReadOnly(True);self.console.setStyleSheet('background:#0d151d;color:#43e77d;font:13px Consolas;border:0;border-radius:4px');terminal.addWidget(self.console,1)
  entry=QHBoxLayout();self.command=QLineEdit();self.command.setPlaceholderText('z.B. ATT 10.5 oder HELP');self.command.setMinimumHeight(39);self.command.returnPressed.connect(self.run_command);send=button('Senden');send.clicked.connect(self.run_command);entry.addWidget(self.command,1);entry.addWidget(send);terminal.addLayout(entry);bottom.addWidget(self.panel(terminal),56)
  self.set_step(.5);self.set_att(10.5);self.refresh_presets();self.log('PE4302 Controller v0.6 (Simulation) – by OE9SAU\nBefehl HELP für Befehlsliste\nSIMULATION: keine USB-Übertragung')
 def panel(self,layout):
  f=QFrame();f.setObjectName('panel');f.setLayout(layout);f.setStyleSheet('QFrame#panel{background:#fafcff;border:1px solid #c6d5e5;border-radius:5px;}');layout.setContentsMargins(13,9,13,10);return f
 def set_att(self,v,update_slider=True):
  self.att=max(0,min(31.5,round(v*2)/2));self.big.setText(f'{self.att:.1f} dB');self.spin.blockSignals(True);self.spin.setValue(self.att);self.spin.blockSignals(False)
  if update_slider:self.slider.blockSignals(True);self.slider.setValue(round(self.att*2));self.slider.blockSignals(False)
 def apply_direct_input(self):
  # Commit the value still being edited before reading the spin box.
  self.spin.interpretText()
  value=self.spin.value()
  self.command.setText(f'ATT {value:.1f}')
  self.run_command()
 def set_step(self,v):
  self.step=v
  for n,b in self.stepbuttons:b.setStyleSheet('background:#dcecff;border:2px solid #1261d7;color:#0044ac;font-weight:bold;' if n==v else '')
 def refresh_presets(self):
  for i,b in enumerate(self.pbuttons):b.setText(f'P{i+1}\n{self.presets[i]:.1f} dB');b.setStyleSheet('background:#dcecff;border:2px solid #1261d7;' if i==self.selected else '')
 def choose_preset(self,n):self.selected=n;self.refresh_presets();self.recall()
 def store(self):self.presets[self.selected]=self.att;self.refresh_presets();self.log(f'OK: P{self.selected+1} gespeichert ({self.att:.1f} dB)')
 def recall(self):self.set_att(self.presets[self.selected]);self.log(f'OK: P{self.selected+1} ({self.att:.1f} dB)')
 def log(self,s):self.console.appendPlainText(s)
 def run_command(self):
  raw=self.command.text().strip();self.command.clear()
  if not raw:return
  self.log('> '+raw);parts=raw.upper().split();cmd=parts[0]
  try:
   if cmd=='ATT?':self.log(f'{self.att:.1f} dB')
   elif cmd=='ATT' and len(parts)==2:self.set_att(float(parts[1].replace(',','.')));self.log(f'OK: Dämpfung auf {self.att:.1f} dB gesetzt')
   elif cmd=='STEP' and len(parts)==2:self.set_att(self.att+float(parts[1].replace(',','.')));self.log(f'OK: {self.att:.1f} dB')
   elif cmd=='MIN':self.set_att(0);self.log('OK: 0 dB')
   elif cmd=='MAX':self.set_att(31.5);self.log('OK: 31.5 dB')
   elif cmd in ('PRESET','STORE') and len(parts)==2:
    n=int(parts[1]);assert 1<=n<=4;self.selected=n-1;self.refresh_presets();self.recall() if cmd=='PRESET' else self.store()
   elif cmd=='IDN?':self.log('PE4302 Attenuator Controller v0.6 – by OE9SAU (Simulation)')
   elif cmd=='HELP':self.log('ATT <Wert> | ATT? | STEP <+/-dB> | MIN | MAX | PRESET 1..4 | STORE 1..4 | IDN? | HELP | SWEEP ...')
   elif cmd=='SWEEP':self.log('SIMULATION: Sweep für spätere Version vorgesehen.')
   else:self.log('ERR: Unbekannter Befehl oder Parameter. HELP eingeben.')
  except (ValueError,AssertionError):self.log('ERR: Ungültiger Parameter')

if __name__=='__main__':
 app=QApplication(sys.argv);app.setStyle('Fusion');app.setStyleSheet('QWidget{font-family:Segoe UI;font-size:12px;} QPushButton{border:1px solid #bdcbd9;border-radius:5px;background:#f5f7fa;padding:4px;} QPushButton:hover{background:#e0edff;} QComboBox,QDoubleSpinBox,QLineEdit{border:1px solid #bdcbd9;border-radius:4px;background:white;padding:4px;}');w=Main();w.show();sys.exit(app.exec())
