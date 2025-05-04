import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import ctypes

# Vérification des droits administrateur
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # Relancer le script en administrateur
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, ' '.join(sys.argv), None, 1)
    sys.exit()

# Fonctions d'actions
def nettoyer_temporaire():
    temp_paths = [os.getenv('TEMP'), os.path.join(os.getenv('WINDIR'), 'Temp')]
    for path in temp_paths:
        if os.path.exists(path):
            try:
                for root, dirs, files in os.walk(path, topdown=False):
                    for name in files:
                        try:
                            os.remove(os.path.join(root, name))
                        except:
                            pass
                    for name in dirs:
                        try:
                            os.rmdir(os.path.join(root, name))
                        except:
                            pass
            except Exception as e:
                print(f"Erreur: {e}")

def creer_point_restauration():
    try:
        subprocess.run(["powershell.exe", "Enable-ComputerRestore -Drive C:"], check=True)
        subprocess.run(["powershell.exe", "Checkpoint-Computer -Description 'Optimisation via GUI' -RestorePointType MODIFY_SETTINGS"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la création du point de restauration: {e}")

def reparer_systeme():
    subprocess.run(["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"], check=True)
    subprocess.run(["sfc", "/scannow"], check=True)

def nettoyer_disque():
    subprocess.run(["cleanmgr.exe", "/sagerun:1"], check=True)

# Interface graphique
def toggle(button, key):
    if selected_actions[key]:
        button.config(bg='SystemButtonFace')
        selected_actions[key] = False
    else:
        button.config(bg='lightgreen')
        selected_actions[key] = True

def lancer_actions():
    tasks = [
        ("Nettoyage temporaire", nettoyer_temporaire, 'cleanTemp'),
        ("Création point de restauration", creer_point_restauration, 'restorePoint'),
        ("Réparation système", reparer_systeme, 'repairSystem'),
        ("Nettoyage disque", nettoyer_disque, 'cleanupDisk')
    ]
    
    total = sum(1 for _, _, key in tasks if selected_actions[key])
    done = 0
    
    for label, action, key in tasks:
        if selected_actions[key]:
            try:
                action()
            except Exception as e:
                print(f"Erreur pendant {label}: {e}")
            done += 1
            progress_var.set(int((done/total)*100))
            root.update_idletasks()

    messagebox.showinfo("Terminé", "Toutes les actions sont terminées !")

# Création de la fenêtre
root = tk.Tk()
root.title("Maintenance Système")
root.geometry("400x450")

selected_actions = {
    'cleanTemp': False,
    'restorePoint': False,
    'repairSystem': False,
    'cleanupDisk': False
}

btn_clean_temp = tk.Button(root, text="Nettoyer Temporaire", width=25, command=lambda: toggle(btn_clean_temp, 'cleanTemp'))
btn_clean_temp.pack(pady=10)

btn_restore_point = tk.Button(root, text="Créer Point de Restauration", width=25, command=lambda: toggle(btn_restore_point, 'restorePoint'))
btn_restore_point.pack(pady=10)

btn_repair = tk.Button(root, text="Réparer Système (SFC/DISM)", width=25, command=lambda: toggle(btn_repair, 'repairSystem'))
btn_repair.pack(pady=10)

btn_cleanup = tk.Button(root, text="Nettoyer Disque", width=25, command=lambda: toggle(btn_cleanup, 'cleanupDisk'))
btn_cleanup.pack(pady=10)

progress_var = tk.IntVar()
progress = ttk.Progressbar(root, length=300, variable=progress_var, maximum=100)
progress.pack(pady=20)

btn_lancer = tk.Button(root, text="Lancer", width=20, command=lancer_actions)
btn_lancer.pack(pady=10)

root.mainloop()
