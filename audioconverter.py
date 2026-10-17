import tkinter as tk
from tkinter import filedialog, messagebox
from pydub import AudioSegment
import urllib.request
import io
import base64
import os
import json
import math
import uuid
import threading

class AudioToWavConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio to Roblox Wav Converter")
        self.root.geometry("700x750")
        self.root.configure(padx=20, pady=20)
        
        self.current_audio = None
        self.is_processing = False

        # --- Top Controls Frame ---
        controls_frame = tk.Frame(root)
        controls_frame.pack(fill="x", pady=(0, 10))
        tk.Button(controls_frame, text="Select Audio File", command=self.select_file, width=18).pack(side="left", padx=(0, 10))

        # --- URL Frame ---
        url_frame = tk.Frame(root)
        url_frame.pack(fill="x", pady=(0, 10))
        tk.Label(url_frame, text="URL:").pack(side="left", padx=(0, 5))
        self.url_entry = tk.Entry(url_frame)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Button(url_frame, text="Load URL", command=self.start_url_thread, width=12).pack(side="left")

        # --- Convert Buttons Frame ---
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", pady=5)
        
        self.btn_json = tk.Button(btn_frame, text="Convert (Binary JSON)", command=lambda: self.start_thread(self.convert_json), bg="lightgreen", font=("Arial", 10, "bold"))
        self.btn_json.pack(side="left", padx=(0, 5))
        
        self.btn_rbxmx = tk.Button(btn_frame, text="Export as .rbxmx", command=lambda: self.start_thread(self.export_rbxmx), bg="orange", font=("Arial", 10, "bold"))
        self.btn_rbxmx.pack(side="left")

        # --- Status Label ---
        self.status_label = tk.Label(root, text="No audio loaded.", fg="gray")
        self.status_label.pack(fill="x", pady=5)

        # --- Output Header Frame ---
        output_header = tk.Frame(root)
        output_header.pack(fill="x", pady=(10, 2))
        tk.Label(output_header, text="Output Data:", fg="black").pack(side="left")
        self.copy_btn = tk.Button(output_header, text="Copy Code", command=self.copy_text, relief="flat", bg="#e0e0e0", width=12)
        self.copy_btn.pack(side="right")

        # --- Text Area Frame ---
        text_frame = tk.Frame(root, borderwidth=1, relief="solid")
        text_frame.pack(fill="both", expand=True, pady=(0, 10))
        self.scrollbar = tk.Scrollbar(text_frame)
        self.scrollbar.pack(side="right", fill="y")
        self.text_area = tk.Text(text_frame, yscrollcommand=self.scrollbar.set, wrap="none", font=("Consolas", 10))
        self.text_area.pack(fill="both", expand=True, padx=5, pady=5)
        self.scrollbar.config(command=self.text_area.yview)

    def set_buttons_state(self, state):
        self.btn_json.config(state=state)
        self.btn_rbxmx.config(state=state)

    def start_thread(self, target_function):
        if self.is_processing: return
        self.is_processing = True
        self.set_buttons_state("disabled")
        threading.Thread(target=target_function, daemon=True).start()

    def start_url_thread(self):
        if self.is_processing: return
        self.is_processing = True
        self.set_buttons_state("disabled")
        threading.Thread(target=self.load_from_url, daemon=True).start()

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Audio",
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.flac *.m4a *.webm")]
        )
        if file_path:
            try:
                self.current_audio = AudioSegment.from_file(file_path)
                self.status_label.config(text=f"Loaded: {os.path.basename(file_path)}", fg="black")
                self.text_area.delete(1.0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load audio (Ensure ffmpeg is installed):\n{e}")

    def load_from_url(self):
        url = self.url_entry.get().strip()
        if not url:
            self.is_processing = False
            self.set_buttons_state("normal")
            return
        
        self.root.after(0, lambda: self.status_label.config(text="Downloading audio...", fg="blue"))
        
        try:
            # Check if it's a YouTube/TikTok/Soundcloud link
            if any(x in url for x in ["youtube.com", "youtu.be", "tiktok.com", "soundcloud.com", "instagram.com"]):
                try:
                    import yt_dlp
                except ImportError:
                    self.root.after(0, lambda: messagebox.showerror("Missing Library", "Please install yt-dlp by running:\npip install yt-dlp"))
                    self.root.after(0, lambda: self.status_label.config(text="Missing yt-dlp library.", fg="red"))
                    self.is_processing = False
                    self.set_buttons_state("normal")
                    return
                
                import tempfile
                self.root.after(0, lambda: self.status_label.config(text="Extracting audio via yt-dlp...", fg="blue"))
                
                temp_path = os.path.join(tempfile.gettempdir(), 'yt_audio_%(id)s.%(ext)s')
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': temp_path,
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    downloaded_file = ydl.prepare_filename(info)
                
                # Load the downloaded file with pydub
                self.current_audio = AudioSegment.from_file(downloaded_file)
                
                # Clean up the temporary file
                if os.path.exists(downloaded_file):
                    os.remove(downloaded_file)
            else:
                # Use standard urllib for direct mp3/wav links
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=20) as response:
                    audio_data = response.read()
                self.current_audio = AudioSegment.from_file(io.BytesIO(audio_data))
                
            self.root.after(0, lambda: self.status_label.config(text="Loaded from URL.", fg="black"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to download:\n{e}"))
            self.root.after(0, lambda: self.status_label.config(text="Failed to load URL.", fg="red"))
        
        self.is_processing = False
        self.set_buttons_state("normal")

    def get_wav_bytes(self):
        if not self.current_audio: return None
        # Convert to mono, 22050Hz, 16-bit (optimal for Roblox FFT synthesizer)
        audio = self.current_audio.set_channels(1).set_frame_rate(22050).set_sample_width(2)
        buffer = io.BytesIO()
        audio.export(buffer, format="wav")
        return buffer.getvalue()

    def convert_json(self):
        wav_bytes = self.get_wav_bytes()
        if not wav_bytes:
            self.is_processing = False
            self.set_buttons_state("normal")
            return
            
        b64_data = base64.b64encode(wav_bytes).decode("utf-8")
        json_obj = {"data": b64_data}
        json_str = json.dumps(json_obj, separators=(',', ':'))
        
        def update_ui():
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, json_str)
            self.status_label.config(text=f"Binary JSON complete! (Size: {len(json_str)} chars)", fg="green")
            self.is_processing = False
            self.set_buttons_state("normal")
        self.root.after(0, update_ui)

    def export_rbxmx(self):
        wav_bytes = self.get_wav_bytes()
        if not wav_bytes:
            self.is_processing = False
            self.set_buttons_state("normal")
            return
            
        b64_data = base64.b64encode(wav_bytes).decode("utf-8")
        
        chunk_size = 190000
        total_len = len(b64_data)
        num_chunks = math.ceil(total_len / chunk_size)
        chunks = [b64_data[i*chunk_size:(i+1)*chunk_size] for i in range(num_chunks)]
            
        def escape_xml(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")
        def get_ref(): return "RBX" + uuid.uuid4().hex.upper()
            
        xml_str = '<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">\n'
        xml_str += '\t<External>null</External>\n\t<External>nil</External>\n'
        xml_str += f'\t<Item class="Folder" referent="{get_ref()}">\n'
        xml_str += '\t\t<Properties>\n\t\t\t<string name="Name">WavData</string>\n\t\t\t<BinaryString name="Tags"></BinaryString>\n\t\t</Properties>\n'
        
        def add_string_value(name, value):
            nonlocal xml_str
            xml_str += f'\t\t<Item class="StringValue" referent="{get_ref()}">\n'
            xml_str += f'\t\t\t<Properties>\n\t\t\t\t<string name="Name">{name}</string>\n\t\t\t\t<BinaryString name="Tags"></BinaryString>\n\t\t\t\t<string name="Value">{value}</string>\n\t\t\t</Properties>\n\t\t</Item>\n'
            
        add_string_value("TotalChunks", str(num_chunks))
        for i, chunk in enumerate(chunks):
            add_string_value(str(i+1), escape_xml(chunk))
            
        xml_str += '\t</Item>\n</roblox>'
        
        file_path = filedialog.asksaveasfilename(title="Save RBXMX", defaultextension=".rbxmx", filetypes=[("Roblox Model", "*.rbxmx")])
        
        def finish_ui():
            if file_path:
                with open(file_path, "w", encoding="utf-8") as f: f.write(xml_str)
                self.status_label.config(text=f"Exported {num_chunks} chunk(s) to RBXMX!", fg="green")
                messagebox.showinfo("Success", f"Saved to {file_path}\nYou can now import this into Roblox Studio!")
            self.is_processing = False
            self.set_buttons_state("normal")
        self.root.after(0, finish_ui)

    def copy_text(self):
        code = self.text_area.get(1.0, tk.END).strip()
        if not code: return
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        self.copy_btn.config(text="Copied!", bg="#c3e6cb")
        self.root.after(1500, lambda: self.copy_btn.config(text="Copy Code", bg="#e0e0e0"))

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioToWavConverter(root)
    root.mainloop()