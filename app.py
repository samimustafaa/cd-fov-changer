"""sg0hann FOV Changer — config-only prototype. Does not modify game memory."""
import os
import re
import shutil
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from updater import VERSION, check_for_updates
from game_detector import detect_client, inspect_game_folder, inspect_process_files

KEY = re.compile(r'(?im)^(?P<indent>[ \t]*)(?P<key>fov|fieldofview|camera_fov|camerafov|field_of_view)[ \t]*(?P<sep>[:=])[ \t]*(?P<value>[+-]?\d+(?:\.\d+)?)(?P<rest>[ \t]*(?:[;#].*)?)$')

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f'sg0hann FOV Changer v{VERSION} — Prototype')
        self.geometry('560x650')
        self.minsize(530,630)
        self.configure(bg='#111318')
        self.path = tk.StringVar(value='No configuration file selected')
        self.value = tk.IntVar(value=90)
        self.status = tk.StringVar(value='Waiting for client.exe. Read-only detection does not change FOV.')
        self.game_status = tk.StringVar(value='Game: checking...')
        self.detected = None
        s=ttk.Style(self)
        s.theme_use('clam')
        s.configure('TButton',padding=9,font=('Segoe UI',10))
        s.configure('Horizontal.TScale',background='#111318')
        tk.Label(self,text='sg0hann  /  FOV CHANGER',bg='#111318',fg='#f0f3f8',font=('Segoe UI',20,'bold')).pack(anchor='w',padx=26,pady=(24,6))
        tk.Label(self,text='Config-only prototype • game compatibility unverified',bg='#111318',fg='#a1a6b1',font=('Segoe UI',10)).pack(anchor='w',padx=26)
        tk.Label(self,textvariable=self.game_status,bg='#111318',fg='#81bbff',font=('Segoe UI',10,'bold'),wraplength=490).pack(anchor='w',padx=26,pady=(15,0))
        ttk.Button(self,text='Inspect game configuration locations (read only)',command=self.inspect).pack(fill='x',padx=26,pady=(8,0))
        ttk.Button(self,text='Show active game file and module paths (read only)',command=self.inspect_active).pack(fill='x',padx=26,pady=(6,0))
        panel=tk.Frame(self,bg='#1b1e26',padx=18,pady=18)
        panel.pack(fill='x',padx=26,pady=20)
        ttk.Button(panel,text='Select config file (.ini / .cfg / .txt)',command=self.select).pack(fill='x')
        tk.Label(panel,textvariable=self.path,bg='#1b1e26',fg='#a1a6b1',wraplength=440,font=('Segoe UI',9)).pack(pady=(10,18))
        r=tk.Frame(panel,bg='#1b1e26');r.pack(fill='x')
        tk.Label(r,text='FOV',bg='#1b1e26',fg='#eff2f7',font=('Segoe UI',12,'bold')).pack(side='left')
        tk.Label(r,textvariable=self.value,bg='#1b1e26',fg='#81bbff',font=('Segoe UI',19,'bold')).pack(side='right')
        ttk.Scale(panel,from_=60,to=120,variable=self.value,command=lambda x:self.value.set(round(float(x)))).pack(fill='x',pady=12)
        row=tk.Frame(panel,bg='#1b1e26');row.pack(fill='x')
        for f in (80,90,100,110):
            ttk.Button(row,text=str(f)+'°',command=lambda v=f:self.value.set(v)).pack(side='left',expand=True,fill='x',padx=3)
        buttons=tk.Frame(self,bg='#111318');buttons.pack(fill='x',padx=26)
        self.apply_button = ttk.Button(buttons,text='Apply (game closed only)',command=self.apply)
        self.apply_button.pack(side='left',expand=True,fill='x',padx=(0,5))
        ttk.Button(buttons,text='Restore backup',command=self.restore).pack(side='left',expand=True,fill='x',padx=(5,0))
        ttk.Button(self,text='Check for updates',command=lambda:check_for_updates(self,manual=True)).pack(fill='x',padx=26,pady=(12,0))
        tk.Label(self,textvariable=self.status,bg='#111318',fg='#acb4c4',wraplength=490,justify='left',font=('Segoe UI',9)).pack(anchor='w',padx=26,pady=16)
        # Check asynchronously after the window is visible.
        self.after(1800, lambda:check_for_updates(self,manual=False))
        self.after(300,self.poll_game)
    def poll_game(self):
        self.detected = detect_client()
        if self.detected:
            self.game_status.set('Game detected: client.exe (PID '+str(self.detected['pid'])+')')
            self.apply_button.state(['disabled'])
        else:
            self.game_status.set('Game not running — config editing available only with game closed')
            self.apply_button.state(['!disabled'])
        self.after(2500,self.poll_game)
    def inspect(self):
        if not self.detected:
            messagebox.showinfo('Game not detected','Launch Creative Destruction first to discover its installation folder.')
            return
        result=inspect_game_folder(self.detected['exe'])
        self.show_report('Game installation files',result)
    def show_report(self,title,report):
        dialog=tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry('810x550')
        frame=tk.Frame(dialog)
        frame.pack(fill='both',expand=True,padx=10,pady=10)
        bar=tk.Scrollbar(frame)
        bar.pack(side='right',fill='y')
        area=tk.Text(frame,wrap='none',yscrollcommand=bar.set,font=('Consolas',10))
        area.pack(fill='both',expand=True)
        bar.config(command=area.yview)
        area.insert('1.0',report)
        area.configure(state='disabled')
        ttk.Button(dialog,text='Close',command=dialog.destroy).pack(pady=(0,10))
    def inspect_active(self):
        game=detect_client()
        if not game:
            messagebox.showinfo('Game not running','Launch client.exe first, then inspect active files.')
            return
        self.show_report('OS-reported files for client.exe',inspect_process_files(game['pid']))
    def select(self):
        p=filedialog.askopenfilename(title='Choose an existing FOV config file',filetypes=[('Text config files','*.ini *.cfg *.txt'),('All files','*.*')])
        if not p:return
        self.path.set(p)
        try:
            raw=Path(p).read_text(encoding='utf-8-sig')
            match=KEY.search(raw)
            if not match:self.status.set('No explicit FOV key found. No changes will be made.');return
            self.value.set(max(60,min(120,round(float(match.group('value'))))))
            self.status.set('Found key: '+match.group('key')+'. Close the game before applying.')
        except Exception as e:self.status.set('Could not read file: '+str(e))
    def apply(self):
        if detect_client():
            messagebox.showwarning('Game running','Close client.exe before editing any game configuration.')
            return
        p=Path(self.path.get())
        if not p.is_file():messagebox.showwarning('Select file','Choose a real config file first.');return
        try:
            raw=p.read_bytes()
            if b'\x00' in raw:raise ValueError('Binary files are not supported.')
            enc='utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
            original=raw.decode(enc)
            matches=list(KEY.finditer(original))
            if len(matches)!=1:raise ValueError(f'Expected one FOV key, found {len(matches)}. Nothing changed.')
            m=matches[0]
            updated=original[:m.start('value')]+str(self.value.get())+original[m.end('value'):]
            if updated==original:self.status.set('FOV already set to '+str(self.value.get())+'°');return
            backup=Path(str(p)+'.sg0hann-backup')
            if not backup.exists():shutil.copy2(p,backup)
            tmp=p.with_name(p.name+'.sg0hann-tmp')
            try:
                tmp.write_bytes(updated.encode(enc))
                os.replace(tmp,p)
            finally:
                if tmp.exists():tmp.unlink()
            self.status.set(f'Saved {self.value.get()}°; original backed up. Game compatibility unverified.')
        except Exception as e:messagebox.showerror('No changes applied',str(e))
    def restore(self):
        if detect_client():
            messagebox.showwarning('Game running','Close client.exe before restoring any game configuration.')
            return
        p=Path(self.path.get());backup=Path(str(p)+'.sg0hann-backup')
        if not backup.exists():messagebox.showwarning('No backup','No backup found for this file.');return
        if not messagebox.askyesno('Restore','Restore the original file from backup?'):return
        try:shutil.copy2(backup,p);self.status.set('Original configuration restored.')
        except Exception as e:messagebox.showerror('Restore failed',str(e))

if __name__=='__main__':
    App().mainloop()
