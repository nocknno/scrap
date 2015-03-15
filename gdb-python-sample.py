#!/usr/bin/python
import gdb
import re

class CPU_state_x64:
    regnames=['rax','rbx','rcx','rdx','rdi','rsi','rbp','rsp','r8','r9','r10','r11','r12','r13','r14','r15',
       'eflags','cs','ds','ss','es','fs','gs']
    def __init__(self):
        self.regs={}
        for regname in self.regnames:
            self.regs[regname]=None

    def parse(self,info_registers):
        for line in info_registers.split('\n'):
            words=re.split('[ \t]+',line)
            if len(words)>=2:
                self.regs[words[0]]=words[1]

    def get_state(self):
        out=gdb.execute('info registers',to_string=True)
        self.parse(out)

class Memory:
    size_symbols={
       1:'b',2:'h',4:'w',8:'g'
    }
    def __init__(self):
       self.memory={}

    def read(self,addr,size=4):
        type_str=self.size_symbols[size]
        out=gdb.execute('x/1%s %s' % (type_str,addr),to_string=True)
        words=re.split('[ \t]',out.split('\n')[0])
        val=words[1]
        self.memory[addr]=val

class Snapshot:
    def __init__(self):
        self.signature=None
        self.cpu=CPU_state_x64()
        self.memory=Memory()

    def get(self):
        self.cpu.get_state()

    def set_sig(self,signature):
        self.sig=signature
   
class BreakpointManager:
    def __init__(self):
        self.bps={}

    def create_bp(self,addr):
        bp=Breakpoint()
        num=bp.set_bp(addr)
        if num:
            self.bps[num]=bp
            return bp
        return None

class Breakpoint:
    def __init__(self):
        self.num=None
        self.addr=None
        self.act_func=None
        self.view_func=None

    def set_bp(self,addr):
        print "set_bp %s" % (addr)
        out=gdb.execute("break *%s" % (addr),to_string=True)
        line=out.split('\n')[0]
        print "--%s" % (line)
        m=re.match(r'Breakpoint ([0-9]+) at ',line)
        if m:
             self.num=int(m.group(1))
             self.addr=addr
             return self.num
        return None

def breakpoint_stop_handler (event):
  if (isinstance (event, gdb.StopEvent)):
    print "event type: stop"
    for snap in snaps:
       snap.sig.view_func(snap)
       #view_all_snapshot(snap)
  if (isinstance (event, gdb.BreakpointEvent)):
    print "event type: break"
    print "breakpoint number: %s" % (event.breakpoint.number)
    if bpm.bps.has_key(event.breakpoint.number):
         bp=bpm.bps[event.breakpoint.number]
         bp.act_func(bp)
  gdb.execute('continue')

class Break_0x40085a:
    def get_snapshot(self,bp):
        snap=Snapshot()
        snap.set_sig(bp)
        snap.get()
        cpu=snap.cpu
        mem=snap.memory
        rax=cpu.regs['rax']
        rbp=cpu.regs['rbp']
        mem.read(rax,8)
        rbp_index_124="{0:#x}".format(int(rbp,16)-0x124)
        mem.read(rbp_index_124,4)
        snaps.append(snap)

    def view_snapshot(self,snap):
        cpu=snap.cpu
        mem=snap.memory
        rax=cpu.regs['rax']
        rbp=cpu.regs['rbp']
        print "rax(%s) => %s" % (rax,mem.memory[rax])
        rbp_index_124="{0:#x}".format(int(rbp,16)-0x124)
        print "rbp=%s rbp_index_124=%s => %s" % (rbp,rbp_index_124,mem.memory[rbp_index_124])

snaps=[]
bpm=BreakpointManager()

bp_0x40085a=Break_0x40085a()
bp=bpm.create_bp("0x40085a")
bp.act_func=bp_0x40085a.get_snapshot
bp.view_func=bp_0x40085a.view_snapshot
gdb.events.stop.connect (breakpoint_stop_handler)
gdb.execute('run speech-dispacher')


