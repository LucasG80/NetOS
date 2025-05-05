import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import ctypes
import logging
import datetime
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
import locale

class NetOSLogger:
    def __init__(self):
        self.log_file = self.setup_logging()
        
    def setup_logging(self):
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"netos_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        return log_file

class SystemMaintenance:
    def __init__(self, log_queue):
        self.log_queue = log_queue
        
    def log(self, level, message):
        self.log_queue.put((level, message))
        
    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
            
    def nettoyer_temporaire(self):
        self.log("INFO", "Début du nettoyage des fichiers temporaires")
        temp_paths = [os.getenv('TEMP'), os.path.join(os.getenv('WINDIR'), 'Temp')]
        files_removed = 0
        dirs_removed = 0
        
        # Utiliser ThreadPoolExecutor pour paralléliser les opérations
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(self._clean_temp_path, temp_paths))
            
        for path_files, path_dirs in results:
            files_removed += path_files
            dirs_removed += path_dirs
        
        self.log("INFO", f"Nettoyage terminé: {files_removed} fichiers et {dirs_removed} dossiers supprimés")
        return files_removed, dirs_removed
    
    def _clean_temp_path(self, path):
        """Nettoie un chemin temporaire spécifique et retourne (fichiers supprimés, dossiers supprimés)"""
        files_removed = 0
        dirs_removed = 0
        
        if not os.path.exists(path):
            return files_removed, dirs_removed
            
        self.log("INFO", f"Nettoyage du dossier: {path}")
        
        try:
            # Optimisation: supprimer d'abord les fichiers à la racine
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    try:
                        os.remove(item_path)
                        files_removed += 1
                    except Exception as e:
                        self.log("ERROR", f"Impossible de supprimer le fichier {item_path}: {e}")
                        
            # Parcourir les sous-dossiers (de bas en haut)
            for root, dirs, files in os.walk(path, topdown=False):
                # Supprimer d'abord les fichiers
                for name in files:
                    try:
                        file_path = os.path.join(root, name)
                        os.remove(file_path)
                        files_removed += 1
                    except Exception as e:
                        self.log("ERROR", f"Impossible de supprimer le fichier {os.path.join(root, name)}: {e}")
                
                # Puis supprimer les dossiers vides
                for name in dirs:
                    try:
                        dir_path = os.path.join(root, name)
                        if os.path.exists(dir_path) and not os.listdir(dir_path):  # Vérifier si le dossier est vide
                            os.rmdir(dir_path)
                            dirs_removed += 1
                    except Exception as e:
                        self.log("ERROR", f"Impossible de supprimer le dossier {os.path.join(root, name)}: {e}")
        except Exception as e:
            self.log("ERROR", f"Erreur lors du nettoyage de {path}: {e}")
            
        return files_removed, dirs_removed

    def creer_point_restauration(self):
        self.log("INFO", "Création d'un point de restauration")
        try:
            subprocess.run(["powershell.exe", "Enable-ComputerRestore -Drive C:"], 
                          check=True, capture_output=True, text=True)
            self.log("INFO", "Restauration système activée sur le lecteur C:")
            
            result = subprocess.run(
                ["powershell.exe", "Checkpoint-Computer -Description 'Optimisation via NetOS' -RestorePointType MODIFY_SETTINGS"], 
                check=True, capture_output=True, text=True
            )
            self.log("INFO", "Point de restauration créé avec succès")
            return True
        except subprocess.CalledProcessError as e:
            self.log("ERROR", f"Erreur lors de la création du point de restauration: {e}")
            if e.stderr:
                self.log("ERROR", f"Détails: {e.stderr}")
            return False

    def reparer_systeme(self):
        self.log("INFO", "Début de la réparation du système")
        try:
            # DISM avec capture de sortie améliorée
            self.log("INFO", "Exécution de DISM /Online /Cleanup-Image /RestoreHealth")
            dism_process = subprocess.Popen(
                ["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"], 
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, 
                bufsize=1, universal_newlines=True
            )
            
            self._process_output_stream(dism_process, "DISM")
            
            # SFC avec capture de sortie améliorée
            self.log("INFO", "Exécution de SFC /scannow")
            sfc_process = subprocess.Popen(
                ["sfc", "/scannow"], 
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                bufsize=1, universal_newlines=True
            )
            
            self._process_output_stream(sfc_process, "SFC")
            
            self.log("INFO", "Réparation système terminée")
            return True
        except Exception as e:
            self.log("ERROR", f"Erreur pendant la réparation du système: {e}")
            return False

    def _process_output_stream(self, process, prefix):
        """Traite le flux de sortie d'un processus et l'envoie au logger"""
        for line in iter(process.stdout.readline, ''):
            if line.strip():
                self.log("INFO", f"{prefix}: {line.strip()}")
        
        process.stdout.close()
        return_code = process.wait()
        if return_code:
            self.log("WARNING", f"{prefix} a retourné le code {return_code}")

    def nettoyer_disque(self):
        self.log("INFO", "Lancement du nettoyage de disque")
        try:
            # Configuration initiale si nécessaire (décommentez pour configurer à chaque fois)
            # subprocess.run(["cleanmgr.exe", "/sageset:1"], check=True, capture_output=True)
            
            # Exécuter le nettoyage avec les paramètres enregistrés
            subprocess.run(["cleanmgr.exe", "/sagerun:1"], check=True)
            self.log("INFO", "Nettoyage de disque terminé")
            return True
        except subprocess.CalledProcessError as e:
            self.log("ERROR", f"Erreur pendant le nettoyage de disque: {e}")
            return False

class NetOSApp:
    def __init__(self, root):
        self.root = root
        self.logger = NetOSLogger()
        self.log_file = self.logger.log_file
        
        self.log_queue = queue.Queue()
        self.maintenance = SystemMaintenance(self.log_queue)
        
        self.selected_actions = {
            'cleanTemp': False,
            'restorePoint': False,
            'repairSystem': False,
            'cleanupDisk': False
        }
        
        logging.info("Démarrage de NetOS")
        
        # Vérification des privilèges administrateur
        if not self.maintenance.is_admin():
            logging.warning("Redémarrage avec privilèges administrateur")
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, ' '.join(sys.argv), None, 1)
            sys.exit()
        
        logging.info("Exécution avec privilèges administrateur")
        
        self.setup_ui()
        self.setup_log_handler()
        
    def setup_ui(self):
        # Configuration de la fenêtre principale
        self.root.title("NetOS - Maintenance Système")
        self.root.geometry("550x650")
        self.root.minsize(500, 600)
        
        # Style pour les widgets
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#ccc")
        
        # Frame pour le titre
        header_frame = tk.Frame(self.root, bg="#f0f0f0", pady=10)
        header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            header_frame, 
            text="NetOS - Utilitaire de maintenance système",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0"
        )
        title_label.pack()
        
        # Frame pour les actions
        self.action_frame = tk.LabelFrame(self.root, text="Actions disponibles", padx=10, pady=10)
        self.action_frame.pack(padx=10, pady=10, fill=tk.X)
        
        # Création des boutons d'action
        self.btn_clean_temp = self.create_action_button(
            "Nettoyer fichiers temporaires", 'cleanTemp'
        )
        self.btn_restore_point = self.create_action_button(
            "Créer point de restauration", 'restorePoint'
        )
        self.btn_repair = self.create_action_button(
            "Réparer système (SFC/DISM)", 'repairSystem'
        )
        self.btn_cleanup = self.create_action_button(
            "Nettoyer disque", 'cleanupDisk'
        )
        
        # Barre de progression
        progress_frame = tk.Frame(self.root)
        progress_frame.pack(pady=10, fill=tk.X, padx=20)
        
        self.progress_var = tk.IntVar()
        self.progress = ttk.Progressbar(
            progress_frame, length=300, variable=self.progress_var, maximum=100
        )
        self.progress.pack(fill=tk.X, expand=True)
        
        # Bouton pour lancer les actions
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        self.btn_lancer = tk.Button(
            btn_frame, 
            text="Lancer les actions sélectionnées", 
            width=25, height=2,
            bg="#4CAF50", fg="white", 
            font=("Arial", 10, "bold"),
            command=self.lancer_actions
        )
        self.btn_lancer.pack()
        
        # Zone de log
        log_frame = tk.LabelFrame(self.root, text="Journal d'activité")
        log_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=60, height=15)
        self.log_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # Ajout d'informations initiales dans le log
        self.add_to_log(f"NetOS démarré - {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        self.add_to_log("Sélectionnez les actions à effectuer puis cliquez sur Lancer")
        self.add_to_log(f"Log enregistré dans: {self.log_file}")
        self.add_to_log("------------------------")
        
        logging.info("Interface graphique prête")
    
    def create_action_button(self, text, action_key):
        """Crée un bouton d'action standardisé"""
        frame = tk.Frame(self.action_frame)
        frame.pack(fill=tk.X, pady=5)
        
        btn = tk.Button(
            frame, 
            text=text, 
            width=30, 
            command=lambda: self.toggle(btn, action_key),
            relief=tk.RAISED,
            bd=2
        )
        btn.pack(side=tk.LEFT, padx=5)
        
        # Ajouter une description pour chaque action
        descriptions = {
            'cleanTemp': "Supprime les fichiers temporaires pour libérer de l'espace",
            'restorePoint': "Crée un point de restauration système avant modifications",
            'repairSystem': "Répare les fichiers système corrompus (opération longue)",
            'cleanupDisk': "Nettoie les fichiers inutiles sur le disque dur"
        }
        
        desc_label = tk.Label(
            frame, 
            text=descriptions.get(action_key, ""), 
            fg="gray", 
            anchor="w"
        )
        desc_label.pack(side=tk.LEFT, padx=5, fill=tk.X)
        
        return btn
        
    def toggle(self, button, key):
        """Change l'état d'activation d'une action"""
        if self.selected_actions[key]:
            button.config(bg='SystemButtonFace', relief=tk.RAISED)
            self.selected_actions[key] = False
            logging.info(f"Action désactivée: {key}")
        else:
            button.config(bg='lightgreen', relief=tk.SUNKEN)
            self.selected_actions[key] = True
            logging.info(f"Action activée: {key}")
    
    def setup_log_handler(self):
        """Configure le traitement des messages de log depuis la file d'attente"""
        def check_queue():
            try:
                while True:
                    level, message = self.log_queue.get_nowait()
                    if level == "INFO":
                        logging.info(message)
                    elif level == "WARNING":
                        logging.warning(message)
                    elif level == "ERROR":
                        logging.error(message)
                    
                    # Afficher aussi dans l'interface
                    self.add_to_log(message)
            except queue.Empty:
                pass
            finally:
                # Vérifier à nouveau après 100ms
                self.root.after(100, check_queue)
        
        # Démarrer la vérification
        check_queue()
    
    def add_to_log(self, message):
        """Ajoute un message au widget de log et fait défiler vers le bas"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def lancer_actions(self):
        """Lance les actions sélectionnées dans un thread séparé"""
        tasks = [
            ("Nettoyage temporaire", self.maintenance.nettoyer_temporaire, 'cleanTemp'),
            ("Création point de restauration", self.maintenance.creer_point_restauration, 'restorePoint'),
            ("Réparation système", self.maintenance.reparer_systeme, 'repairSystem'),
            ("Nettoyage disque", self.maintenance.nettoyer_disque, 'cleanupDisk')
        ]
        
        # Vérifier si des actions sont sélectionnées
        selected_tasks = [(label, action) for label, action, key in tasks if self.selected_actions[key]]
        if not selected_tasks:
            logging.warning("Aucune action sélectionnée")
            messagebox.showinfo("Attention", "Aucune action sélectionnée !")
            return
        
        # Désactiver les boutons pendant l'exécution
        self.btn_lancer.config(state=tk.DISABLED, text="Exécution en cours...")
        for btn in [self.btn_clean_temp, self.btn_restore_point, self.btn_repair, self.btn_cleanup]:
            btn.config(state=tk.DISABLED)
        
        # Créer et démarrer un thread pour exécuter les actions
        def execute_tasks():
            logging.info(f"{len(selected_tasks)} actions à exécuter")
            self.add_to_log("------------------------")
            self.add_to_log("Début des opérations sélectionnées")
            
            done = 0
            for label, action in selected_tasks:
                logging.info(f"Exécution de: {label}")
                self.add_to_log(f"► Démarrage: {label}")
                
                try:
                    result = action()
                    self.add_to_log(f"✓ {label} terminé avec succès")
                except Exception as e:
                    error_msg = f"Erreur pendant {label}: {e}"
                    logging.error(error_msg)
                    self.add_to_log(f"✗ {error_msg}")
                
                done += 1
                progress = int((done/len(selected_tasks))*100)
                self.progress_var.set(progress)
            
            # Opérations terminées
            logging.info("Toutes les actions sont terminées")
            self.add_to_log("------------------------")
            self.add_to_log("Toutes les actions terminées !")
            self.add_to_log(f"Log enregistré dans: {self.log_file}")
            
            # Réactiver les boutons
            self.root.after(0, lambda: self.btn_lancer.config(state=tk.NORMAL, text="Lancer les actions sélectionnées"))
            for btn in [self.btn_clean_temp, self.btn_restore_point, self.btn_repair, self.btn_cleanup]:
                self.root.after(0, lambda b=btn: b.config(state=tk.NORMAL))
            
            # Afficher un message à l'utilisateur
            self.root.after(0, lambda: messagebox.showinfo("Terminé", "Toutes les actions sont terminées !"))
        
        # Démarrer le thread
        thread = threading.Thread(target=execute_tasks)
        thread.daemon = True
        thread.start()

# Point d'entrée
if __name__ == "__main__":
    root = tk.Tk()
    app = NetOSApp(root)
    root.mainloop()
    logging.info("Fermeture de l'application")