import os
import shutil
import datetime
import threading
import sys
import io
import time
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image
from pathlib import Path

# Decoupled top-level constants from 'procesador_imagenes_ml' to guarantee INSTANTANEOUS startup (< 0.2s)
CANVAS_W, CANVAS_H = 1200, 1500
MAX_PRODUCT_W, MAX_PRODUCT_H = 950, 1100

# UI Theme: Apple Light + Gretel Yellow
APP_BG_COLOR = "#F5F5F7"      # Ultra dark slate
PANEL_COLOR = "#FFFFFF"       # Deep slate grey
ACCENT_COLOR = "#FFD100"       # Mint green/teal highlight
ACCENT_HOVER = "#CCAA00" # Darker green hover
TEXT_COLOR = "#1D1D1F"        # Primary white
TEXT_SECONDARY = "#86868B"    # Cool grey for labels
BORDER_COLOR = "#E5E5EA"      # Discreet divider border

class RedirectStdout:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", string)
        self.text_widget.see("end")
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass

class UnifiedImageApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Gretel - Image E-commerce Hub")
        self.geometry("950x800")
        self.minsize(850, 700)
        
        # Appearance Mode
        ctk.set_appearance_mode("light")
        self.configure(fg_color=APP_BG_COLOR)
        
        # State Variables
        self.mode_var = ctk.StringVar(value="Renombrar y Redimensionar")
        self.brand_var = ctk.StringVar(value="ASICS")
        self.channel_var = ctk.StringVar(value="Inbox")
        self.input_folder = ctk.StringVar()
        self.output_folder = ctk.StringVar()
        
        # Build UI layout
        self.create_widgets()
        
        # Redirect standard output to our UI console
        sys.stdout = RedirectStdout(self.log_box)
        sys.stderr = RedirectStdout(self.log_box)
        
        print("[Iniciado] Gretel Image E-commerce Hub listo.")
        print("Selecciona tu tarea y haz clic en 'Iniciar Procesamiento'.")

    def create_widgets(self):
        # Header Section
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=30, pady=(25, 15))
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="GRETEL IMAGE E-COMMERCE HUB", 
            font=("Segoe UI", 24, "bold"),
            text_color=ACCENT_COLOR
        )
        self.title_label.pack(side="left")
        
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame, 
            text="v2.1 (ASICS / NB / TIMBERLAND)", 
            font=("Segoe UI", 12, "italic"),
            text_color=TEXT_SECONDARY
        )
        self.subtitle_label.pack(side="left", padx=15, pady=(8, 0))

        # Mode Selection (Segmented Button for high-signal clean selection)
        self.mode_frame = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        self.mode_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        self.mode_label = ctk.CTkLabel(
            self.mode_frame, 
            text="SELECCIONA EL MODO DE TRABAJO:", 
            font=("Segoe UI", 11, "bold"),
            text_color=TEXT_SECONDARY
        )
        self.mode_label.pack(side="left", padx=(20, 15), pady=15)
        
        self.mode_selector = ctk.CTkSegmentedButton(
            self.mode_frame,
            values=["Solo Renombrar", "Renombrar y Redimensionar"],
            variable=self.mode_var,
            command=self.on_mode_change,
            font=("Segoe UI", 12, "bold"),
            selected_color=ACCENT_COLOR,
            selected_hover_color=ACCENT_HOVER,
            unselected_color=APP_BG_COLOR,
            text_color=TEXT_COLOR
        )
        self.mode_selector.pack(side="left", fill="x", expand=True, padx=(0, 20), pady=10)

        # Control Panel (Parameters)
        self.panel_frame = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        self.panel_frame.pack(fill="both", padx=30, pady=(0, 20))
        
        # Grid layout for parameters
        self.panel_frame.grid_columnconfigure(0, weight=1)
        self.panel_frame.grid_columnconfigure(1, weight=1)
        
        # Column 1: Brand & Channel Options
        self.brand_frame = ctk.CTkFrame(self.panel_frame, fg_color="transparent")
        self.brand_frame.grid(row=0, column=0, padx=20, pady=15, sticky="nsew")
        
        self.brand_label = ctk.CTkLabel(
            self.brand_frame, 
            text="MARCA", 
            font=("Segoe UI", 11, "bold"),
            text_color=TEXT_SECONDARY
        )
        self.brand_label.pack(anchor="w", pady=(0, 5))
        
        self.brand_menu = ctk.CTkOptionMenu(
            self.brand_frame, 
            variable=self.brand_var, 
            values=["ASICS", "NEW BALANCE", "TIMBERLAND"],
            button_color=ACCENT_COLOR,
            button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=PANEL_COLOR,
            dropdown_hover_color=APP_BG_COLOR,
            dropdown_text_color=TEXT_COLOR,
            fg_color=APP_BG_COLOR,
            text_color=TEXT_COLOR,
            font=("Segoe UI", 12, "bold")
        )
        self.brand_menu.pack(fill="x", pady=(0, 10))
        
        # Channel Selection (Only used for Resizing)
        self.channel_container = ctk.CTkFrame(self.panel_frame, fg_color="transparent")
        self.channel_container.grid(row=0, column=1, padx=20, pady=15, sticky="nsew")
        
        self.channel_label = ctk.CTkLabel(
            self.channel_container, 
            text="CANAL", 
            font=("Segoe UI", 11, "bold"),
            text_color=TEXT_SECONDARY
        )
        self.channel_label.pack(anchor="w", pady=(0, 5))
        
        self.channel_menu = ctk.CTkOptionMenu(
            self.channel_container, 
            variable=self.channel_var, 
            values=["Inbox"],
            button_color=ACCENT_COLOR,
            button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=PANEL_COLOR,
            dropdown_hover_color=APP_BG_COLOR,
            dropdown_text_color=TEXT_COLOR,
            fg_color=APP_BG_COLOR,
            text_color=TEXT_COLOR,
            font=("Segoe UI", 12, "bold")
        )
        self.channel_menu.pack(fill="x", pady=(0, 10))

        # Folder Paths Frame (Full-width inside Panel)
        self.paths_frame = ctk.CTkFrame(self.panel_frame, fg_color="transparent")
        self.paths_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 15), sticky="nsew")
        
        # Origin Folder
        self.src_label = ctk.CTkLabel(
            self.paths_frame, 
            text="CARPETA ORIGEN (FOTOS DE FÁBRICA)", 
            font=("Segoe UI", 11, "bold"),
            text_color=TEXT_SECONDARY
        )
        self.src_label.pack(anchor="w", pady=(5, 5))
        
        self.src_input_frame = ctk.CTkFrame(self.paths_frame, fg_color="transparent")
        self.src_input_frame.pack(fill="x", pady=(0, 10))
        
        self.src_entry = ctk.CTkEntry(
            self.src_input_frame, 
            textvariable=self.input_folder,
            fg_color=APP_BG_COLOR,
            border_color=BORDER_COLOR,
            text_color=TEXT_COLOR,
            placeholder_text="Selecciona la carpeta donde están las imágenes originales..."
        )
        self.src_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.src_btn = ctk.CTkButton(
            self.src_input_frame, 
            text="Buscar Origen", 
            fg_color=ACCENT_COLOR, 
            hover_color=ACCENT_HOVER,
            text_color=APP_BG_COLOR,
            font=("Segoe UI", 11, "bold"),
            command=self.browse_input_folder,
            width=110
        )
        self.src_btn.pack(side="right")
        
        # Destination Folder
        self.dst_label = ctk.CTkLabel(
            self.paths_frame, 
            text="CARPETA DESTINO (FOTOS ESTANDARIZADAS)", 
            font=("Segoe UI", 11, "bold"),
            text_color=TEXT_SECONDARY
        )
        self.dst_label.pack(anchor="w", pady=(5, 5))
        
        self.dst_input_frame = ctk.CTkFrame(self.paths_frame, fg_color="transparent")
        self.dst_input_frame.pack(fill="x", pady=(0, 5))
        
        self.dst_entry = ctk.CTkEntry(
            self.dst_input_frame, 
            textvariable=self.output_folder,
            fg_color=APP_BG_COLOR,
            border_color=BORDER_COLOR,
            text_color=TEXT_COLOR,
            placeholder_text="Selecciona la carpeta de destino para el output..."
        )
        self.dst_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.dst_btn = ctk.CTkButton(
            self.dst_input_frame, 
            text="Buscar Destino", 
            fg_color=ACCENT_COLOR, 
            hover_color=ACCENT_HOVER,
            text_color=APP_BG_COLOR,
            font=("Segoe UI", 11, "bold"),
            command=self.browse_output_folder,
            width=110
        )
        self.dst_btn.pack(side="right")

        # Action and State Area
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=30, pady=(0, 15))
        
        # Reset Button (Discrete Clear)
        self.clear_btn = ctk.CTkButton(
            self.action_frame, 
            text="Limpiar Historial", 
            fg_color="transparent", 
            hover_color="#1E293B",
            border_color=BORDER_COLOR,
            border_width=1,
            text_color=TEXT_COLOR,
            font=("Segoe UI", 12, "bold"),
            command=self.clear_fields,
            width=150,
            height=45
        )
        self.clear_btn.pack(side="left", padx=(0, 15))
        
        # Primary Action Button (Process)
        self.process_btn = ctk.CTkButton(
            self.action_frame, 
            text="Iniciar Procesamiento", 
            fg_color=ACCENT_COLOR, 
            hover_color=ACCENT_HOVER,
            text_color=APP_BG_COLOR,
            font=("Segoe UI", 14, "bold"),
            command=self.start_processing_thread,
            height=45
        )
        self.process_btn.pack(side="right", fill="x", expand=True)

        # Progress Section
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=30, pady=(0, 15))
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame, 
            fg_color=PANEL_COLOR, 
            progress_color=ACCENT_COLOR,
            height=10
        )
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)
        
        # Labels for Percentage and ETA
        self.progress_info_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        self.progress_info_frame.pack(fill="x", pady=(2, 0))
        
        self.progress_percent_label = ctk.CTkLabel(
            self.progress_info_frame, 
            text="0%", 
            font=("Segoe UI", 11, "bold"),
            text_color=ACCENT_COLOR
        )
        self.progress_percent_label.pack(side="left")
        
        self.eta_label = ctk.CTkLabel(
            self.progress_info_frame, 
            text="ETA: --:--", 
            font=("Segoe UI", 11),
            text_color=TEXT_SECONDARY
        )
        self.eta_label.pack(side="right")

        # Real-time console log box
        self.console_label = ctk.CTkLabel(
            self, 
            text="REGISTRO DE PROCESAMIENTO", 
            font=("Segoe UI", 11, "bold"),
            text_color=TEXT_SECONDARY
        )
        self.console_label.pack(anchor="w", padx=30, pady=(0, 5))
        
        self.log_box = ctk.CTkTextbox(
            self, 
            fg_color="#F0F0F2", 
            border_color=BORDER_COLOR, 
            border_width=1,
            text_color="#333333", 
            font=("Consolas", 11),
            corner_radius=10
        )
        self.log_box.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def on_mode_change(self, mode):
        if mode == "Solo Renombrar":
            # Hide channel menu
            self.channel_container.grid_remove()
            self.dst_entry.configure(placeholder_text="Opcional: Si está vacío se renombrará en la carpeta origen...")
            self.process_btn.configure(text="Iniciar Renombrado")
        else:
            # Show channel menu
            self.channel_container.grid()
            self.dst_entry.configure(placeholder_text="Selecciona la carpeta de destino para el output...")
            self.process_btn.configure(text="Iniciar Procesamiento Inteligente")

    def browse_input_folder(self):
        folder = filedialog.askdirectory(title="Selecciona la carpeta ORIGEN")
        if folder:
            self.input_folder.set(folder)
            
    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Selecciona la carpeta DESTINO")
        if folder:
            self.output_folder.set(folder)

    def clear_fields(self):
        self.input_folder.set("")
        self.output_folder.set("")
        self.progress_bar.set(0)
        self.progress_percent_label.configure(text="0%")
        self.eta_label.configure(text="ETA: --:--")
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        print("[Reseteado] Campos y registro borrados.")

    def start_processing_thread(self):
        if not self.input_folder.get():
            print("[!] Error: No has seleccionado una carpeta origen.")
            return
            
        mode = self.mode_var.get()
        if mode == "Renombrar y Redimensionar" and not self.output_folder.get():
            print("[!] Error: Debes seleccionar una carpeta destino para redimensionar.")
            return
            
        # Disable inputs during thread process to avoid click conflicts
        self.toggle_ui_state("disabled")
        
        thread = threading.Thread(target=self.execute_batch)
        thread.start()

    def toggle_ui_state(self, state):
        self.src_btn.configure(state=state)
        self.dst_btn.configure(state=state)
        self.brand_menu.configure(state=state)
        self.channel_menu.configure(state=state)
        self.mode_selector.configure(state=state)
        self.clear_btn.configure(state=state)
        
        if state == "disabled":
            self.process_btn.configure(state="disabled", text="⏳ Procesando imágenes... Por favor espera")
        else:
            mode = self.mode_var.get()
            btn_text = "Iniciar Renombrado" if mode == "Solo Renombrar" else "Iniciar Procesamiento Inteligente"
            self.process_btn.configure(state="normal", text=btn_text)

    def execute_batch(self):
        # Lazy load BOTH processing functions AND brand mapping functions to ensure INSTANT startup of UI
        from procesador_imagenes_ml import (
            procesar_imagen, 
            get_asics_mapped_filename, 
            get_nb_mapped_filename,
            get_timberland_mapped_filename
        )
        
        mode = self.mode_var.get()
        brand = self.brand_var.get()
        src_dir = Path(self.input_folder.get())
        dst_dir = Path(self.output_folder.get()) if self.output_folder.get() else None
        
        print(f"\n=========================================")
        print(f" Tarea: {mode}")
        print(f" Marca: {brand}")
        print(f" Origen: {src_dir}")
        if dst_dir:
            print(f" Destino: {dst_dir}")
        else:
            print(f" Destino: (Misma carpeta origen)")
        print(f"=========================================\n")

        valid_extensions = {".png", ".jpg", ".jpeg"}
        files = []
        for f in src_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in valid_extensions:
                # Skip subfolders that are output folders
                if "procesadas" in f.name.lower() or "exportxls_procesadas" in f.name.lower():
                    continue
                if dst_dir and dst_dir in f.parents and dst_dir.is_relative_to(src_dir):
                    continue
                files.append(f)
                
        total = len(files)
        if total == 0:
            print(f"No se encontraron imágenes válidas en: {src_dir}")
            self.progress_bar.set(0)
            self.toggle_ui_state("normal")
            return
            
        print(f"Se encontraron {total} imágenes para procesar.")
        success = 0
        start_time = time.time()
        
        for i, file in enumerate(files):
            print(f"\n[{i+1}/{total}] {file.name}")
            
            # Map filenames based on brand
            new_stem = file.stem
            if brand == "ASICS":
                new_stem = get_asics_mapped_filename(file)
            elif brand == "NEW BALANCE":
                new_stem = get_nb_mapped_filename(file)
            elif brand == "TIMBERLAND":
                new_stem = get_timberland_mapped_filename(file)
                
            if new_stem == file.stem and brand == "ASICS" and "SL_LT" in file.stem.upper():
                print(f"  [Omitido] Vista de pie izquierdo ('_SL_LT_') ignorada.")
                # Update progress bar
                self.progress_bar.set((i + 1) / total)
                continue
                
            if new_stem == file.stem and brand == "TIMBERLAND" and file.stem.endswith("_8"):
                print(f"  [Omitido] Vista 8 ('_8') ignorada en calzado Timberland.")
                # Update progress bar
                self.progress_bar.set((i + 1) / total)
                continue
                
            if new_stem == file.stem and mode == "Solo Renombrar":
                print(f"  [Omitido] No hay reglas de mapeo para esta vista.")
                self.progress_bar.set((i + 1) / total)
                continue
                
            new_file_name = f"{new_stem}{file.suffix}"
            
            try:
                if mode == "Solo Renombrar":
                    if dst_dir:
                        # Copy renamed file to destination
                        dst_dir.mkdir(parents=True, exist_ok=True)
                        out_file_path = dst_dir / new_file_name
                        shutil.copy(str(file), str(out_file_path))
                        print(f"  [Renombrado] Copiado a: '{out_file_path.name}'")
                    else:
                        # Rename in-place
                        out_file_path = file.parent / new_file_name
                        if file != out_file_path:
                            shutil.move(str(file), str(out_file_path))
                            print(f"  [Renombrado] In-place: '{file.name}' ➔ '{out_file_path.name}'")
                        else:
                            print(f"  [Listo] Ya tiene el formato correcto: '{file.name}'")
                    success += 1
                else:
                    # Rename + Resize
                    dst_dir.mkdir(parents=True, exist_ok=True)
                    out_file_path = dst_dir / f"{new_stem}.jpg" # Export strictly as JPG for sizing
                    
                    procesar_imagen(
                        file, out_file_path, CANVAS_W, CANVAS_H, "#F5F5F5", 
                        MAX_PRODUCT_W, MAX_PRODUCT_H, marca_forzada=brand
                    )
                    success += 1
            except Exception as e:
                print(f"  [ERROR] Falló procesamiento: {e}")
                
            # Update progress bar safely
            progress_ratio = (i + 1) / total
            self.progress_bar.set(progress_ratio)
            self.progress_percent_label.configure(text=f"{int(progress_ratio * 100)}%")
            
            # Calculate ETA
            elapsed_time = time.time() - start_time
            if i >= 0:
                avg_time_per_image = elapsed_time / (i + 1)
                remaining_images = total - (i + 1)
                eta_seconds = avg_time_per_image * remaining_images
                
                eta_m, eta_s = divmod(int(eta_seconds), 60)
                if eta_m > 0:
                    self.eta_label.configure(text=f"ETA: {eta_m:02d}:{eta_s:02d}m")
                else:
                    self.eta_label.configure(text=f"ETA: {eta_s:02d}s")
            
        print(f"\n--- Procesamiento Finalizado: {success}/{total} completados con éxito. ---")
        
        # Restore UI state
        self.toggle_ui_state("normal")

if __name__ == "__main__":
    app = UnifiedImageApp()
    app.mainloop()
