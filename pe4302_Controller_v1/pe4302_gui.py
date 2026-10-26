import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QSlider,QComboBox,QDoubleSpinBox,QGroupBox,QPlainTextEdit)

class PE4302(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PE4302 – USB Attenuator Controller (Simulation)')
        self.resize(740,560)
        self.value=10.5
        self.mem=[0,10,20,31.5]
        root=QWidget(); self.setCentralWidget(root); layout=QVBoxLayout(root)
        top=QHBoxLayout(); top.addWidget(QLabel('Verbindung:'))
        self.port=QComboBox(); self.port.addItems(['Simulation (offline)','COM1','COM2','COM3','COM4','COM5','COM6','COM7','COM8']); top.addWidget(self.port)
        self.connect=QPushButton('USB verbinden (später)'); self.connect.setEnabled(False); top.addWidget(self.connect)
        layout.addLayout(top)
        self.display=QLabel(); self.display.setAlignment(Qt.AlignCenter); self.display.setObjectName('display'); layout.addWidget(self.display)
        self.slider=QSlider(Qt.Horizontal); self.slider.setRange(0,63); self.slider.valueChanged.connect(lambda v:self.set_att(v/2)); layout.addWidget(self.slider)
        controls=QHBoxLayout(); self.minus=QPushButton('−'); self.plus=QPushButton('+'); self.step=QComboBox(); self.step.addItems(['0.5','1','3','6']);
        self.minus.clicked.connect(lambda:self.set_att(self.value-float(self.step.currentText())))
        self.plus.clicked.connect(lambda:self.set_att(self.value+float(self.step.currentText())))
        controls.addWidget(self.minus); controls.addWidget(QLabel('Schrittweite (dB):')); controls.addWidget(self.step); controls.addWidget(self.plus)
        layout.addLayout(controls)
        box=QGroupBox('Direkte Dämpfung'); quick=QHBoxLayout(box)
        for n in [0,3,6,10,20,31.5]:
            b=QPushButton(f'{n:g} dB'); b.clicked.connect(lambda checked=False,v=n:self.set_att(v)); quick.addWidget(b)
        layout.addWidget(box)
        mem=QGroupBox('Speicherplätze (Linksklick: abrufen / Rechtsklick: speichern)'); grid=QGridLayout(mem)
        for i in range(4):
            b=QPushButton(); b.setContextMenuPolicy(Qt.CustomContextMenu)
            b.clicked.connect(lambda checked=False,k=i:self.set_att(self.mem[k]))
            b.customContextMenuRequested.connect(lambda pos,k=i:self.save_memory(k))
            setattr(self,f'mem{i}',b); grid.addWidget(b,0,i)
        layout.addWidget(mem)
        layout.addWidget(QLabel('Befehlsvorschau (noch keine USB-Übertragung):'))
        self.log=QPlainTextEdit(); self.log.setReadOnly(True); layout.addWidget(self.log)
        self.set_att(self.value)
        self.setStyleSheet('QWidget{background:#17212e;color:#ecf2f9;font-size:13px} QPushButton,QComboBox{background:#2a3a4d;border:1px solid #53657b;border-radius:6px;padding:9px} QPushButton:hover{background:#36516d} QGroupBox{border:1px solid #53657b;border-radius:8px;margin-top:12px;padding:10px} QGroupBox::title{subcontrol-origin:margin;left:12px;padding:0 6px} #display{font-size:54px;font-weight:bold;color:#73d5ff;background:#101a25;border-radius:12px;padding:20px} QPlainTextEdit{background:#101a25;border:1px solid #53657b;border-radius:6px}')
    def set_att(self,v):
        v=max(0,min(31.5,round(v*2)/2))
        if v==self.value and self.slider.value()==round(v*2):
            self.refresh(); return
        self.value=v; self.slider.blockSignals(True); self.slider.setValue(round(v*2)); self.slider.blockSignals(False)
        self.refresh(); self.log.appendPlainText(f'ATT {v:.1f}    [SIMULATION]')
    def refresh(self):
        self.display.setText(f'{self.value:.1f} dB')
        for i,v in enumerate(self.mem): getattr(self,f'mem{i}').setText(f'M{i+1}: {v:.1f} dB')
    def save_memory(self,i):
        self.mem[i]=self.value; self.refresh(); self.log.appendPlainText(f'MEM {i+1} = {self.value:.1f} dB    [LOKAL]')

if __name__=='__main__':
    app=QApplication(sys.argv); win=PE4302(); win.show(); sys.exit(app.exec())
