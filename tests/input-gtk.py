"""Usage: GDK_BACKEND=wayland|x11 python3 input-gtk.py LABEL NEW_PRIVATE_JSON

Records only the four owned test fields. No global keyboard hooks.
"""
import gi,os,json,sys,signal,time
from pathlib import Path
gi.require_version('Gtk','3.0');from gi.repository import Gtk,Gdk,GLib,Pango
backend=sys.argv[1];out=Path(sys.argv[2])
with out.open('x') as stream: os.chmod(out,0o600); stream.write('{}')
win=Gtk.Window(title='AAG Input Test - '+backend);win.set_default_size(740,380);win.set_position(Gtk.WindowPosition.CENTER)
box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12);box.set_border_width(20);win.add(box)
label=Gtk.Label(label='Temporary input test — use only the supplied harmless phrases.');box.pack_start(label,False,False,0)
entries=[]
for name in ['English 1','Hebrew 1','English 2','Hebrew 2']:
 row=Gtk.Box(spacing=12);row.pack_start(Gtk.Label(label=name),False,False,0);entry=Gtk.Entry();entry.set_hexpand(True);entry.override_font(Pango.FontDescription('Sans 18'));row.pack_start(entry,True,True,0);box.pack_start(row,False,False,0);entries.append(entry)
button=Gtk.Button(label='Close test');button.connect('clicked',lambda *_:win.destroy());box.pack_start(button,False,False,0)
def report(*args):
 j={'pid':os.getpid(),'backend':Gdk.Display.get_default().__class__.__name__,'active':win.is_active(),'focused_row':next((i for i,e in enumerate(entries) if e.has_focus()),None),'values':[e.get_text() for e in entries],'timestamp':time.time(),'closed':False}
 out.write_text(json.dumps(j,ensure_ascii=False,indent=2));return True
for e in entries:e.connect('changed',report)
def close(*args):
 report();j=json.loads(out.read_text());j['closed']=True;j['active']=False;out.write_text(json.dumps(j,ensure_ascii=False,indent=2));Gtk.main_quit()
win.connect('destroy',close);win.show_all();entries[0].grab_focus();win.present();GLib.timeout_add(100,report);GLib.timeout_add_seconds(600,lambda:win.destroy());signal.signal(signal.SIGTERM,lambda *_:GLib.idle_add(win.destroy));Gtk.main()
