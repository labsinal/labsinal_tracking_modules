#!/usr/bin/env python3
"""
Simple GUI for running the Ultrack pipeline.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os

def run_pipeline():
    input_path = input_entry.get()
    output_base = output_entry.get()
    config_path = config_entry.get()
    conda_env = env_entry.get()

    if not all([input_path, output_base, config_path, conda_env]):
        messagebox.showerror("Error", "All fields are required.")
        return

    if not os.path.exists(input_path):
        messagebox.showerror("Error", "Input path does not exist.")
        return

    if not os.path.exists(config_path):
        messagebox.showerror("Error", "Config path does not exist.")
        return

    # Run the pipeline
    try:
        result = subprocess.run([
            'bash', 'scripts/complete_pipeline.sh',
            input_path, output_base, config_path, conda_env
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            messagebox.showinfo("Success", "Pipeline completed successfully.")
        else:
            messagebox.showerror("Error", f"Pipeline failed:\n{result.stderr}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to run pipeline: {str(e)}")

def browse_input():
    path = filedialog.askdirectory()
    if path:
        input_entry.delete(0, tk.END)
        input_entry.insert(0, path)

def browse_output():
    path = filedialog.askdirectory()
    if path:
        output_entry.delete(0, tk.END)
        output_entry.insert(0, path)

def browse_config():
    path = filedialog.askopenfilename(filetypes=[("TOML files", "*.toml")])
    if path:
        config_entry.delete(0, tk.END)
        config_entry.insert(0, path)

# Create GUI
root = tk.Tk()
root.title("Ultrack Pipeline GUI")
root.configure(bg='black')

# Style for dark theme
style = ttk.Style()
style.configure('TLabel', background='black', foreground='lightblue', font=('Arial', 10))
style.configure('TEntry', fieldbackground='darkblue', foreground='white', insertcolor='white')
style.configure('TButton', background='blue', foreground='white', font=('Arial', 10, 'bold'))
style.map('TButton', background=[('active', 'darkblue')])

tk.Label(root, text="Input Path:", bg='black', fg='lightblue').grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
input_entry = ttk.Entry(root, width=50)
input_entry.grid(row=0, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=browse_input, bg='blue', fg='white', activebackground='darkblue').grid(row=0, column=2, padx=5, pady=5)

tk.Label(root, text="Output Base Path:", bg='black', fg='lightblue').grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
output_entry = ttk.Entry(root, width=50)
output_entry.grid(row=1, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=browse_output, bg='blue', fg='white', activebackground='darkblue').grid(row=1, column=2, padx=5, pady=5)

tk.Label(root, text="Config Path:", bg='black', fg='lightblue').grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
config_entry = ttk.Entry(root, width=50)
config_entry.grid(row=2, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=browse_config, bg='blue', fg='white', activebackground='darkblue').grid(row=2, column=2, padx=5, pady=5)

tk.Label(root, text="Conda Environment:", bg='black', fg='lightblue').grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
env_entry = ttk.Entry(root, width=50)
env_entry.grid(row=3, column=1, padx=5, pady=5)

tk.Button(root, text="Run Pipeline", command=run_pipeline, bg='blue', fg='white', activebackground='darkblue', font=('Arial', 10, 'bold')).grid(row=4, column=1, pady=10)

root.mainloop()