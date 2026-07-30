import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import os
import sys

def run_standalone_test():
    root = tk.Tk()
    root.title("Builderr Admission Preview")
    root.geometry("900x600")
    root.configure(bg='#0a0a1a')
    
    style = ttk.Style()
    style.theme_use('default')
    style.configure('Title.TLabel', font=('Consolas', 12, 'bold'), foreground='#00ccff', background='#0a0a1a')
    
    lbl = ttk.Label(root, text="Running official preview.py simulator on your agent...", style='Title.TLabel')
    lbl.pack(pady=10)
    
    text_area = tk.Text(root, bg='#111133', fg='#00ff88', font=('Consolas', 10))
    text_area.pack(fill='both', expand=True, padx=10, pady=10)
    
    def run_test():
        try:
            agent_path = os.path.abspath("backend/agent.py")
            cwd = os.path.abspath("builderr-template")
            cmd = ["py", "preview.py", agent_path]
            
            process = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
            for line in process.stdout:
                root.after(0, lambda l=line: [text_area.insert(tk.END, l), text_area.see(tk.END)])
            
            process.wait()
            if process.returncode == 0:
                root.after(0, lambda: text_area.insert(tk.END, "\n[SYSTEM] TEST COMPLETED SUCCESSFULLY!\n"))
            else:
                root.after(0, lambda: text_area.insert(tk.END, f"\n[SYSTEM] TEST FAILED with exit code {process.returncode}\n"))
        except Exception as e:
            root.after(0, lambda e=e: text_area.insert(tk.END, f"\n[SYSTEM ERROR]: {str(e)}\n"))

    threading.Thread(target=run_test, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    run_standalone_test()
