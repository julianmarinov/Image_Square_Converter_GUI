import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import whisper
import datetime
import threading
import os
import torch


class TranscriptionService:
    def __init__(self):
        self.cancelled = False

    def cancel_transcription(self):
        self.cancelled = True

    def transcribe_audio_to_srt(self, audio_file_path, srt_file_path, model_type, update_status,
                                update_transcription_text):
        self.cancelled = False
        try:
            update_status("Transcribing...")

            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = whisper.load_model(model_type, device=device)

            result = model.transcribe(audio_file_path)
            if self.cancelled:
                update_status("Transcription cancelled.")
                return

            subtitles = self.process_transcription_segments(result)
            self.write_subtitles_to_file(subtitles, srt_file_path)
            transcription_text = '\n'.join([segment['text'] for segment in result['segments']])
            update_transcription_text(transcription_text)
            update_status("Subtitle file created successfully.")
        except Exception as e:
            update_status(f"Error: {e}")

    def process_transcription_segments(self, result):
        subtitles = []
        for i, segment in enumerate(result["segments"]):
            start_time = self.format_timedelta(datetime.timedelta(seconds=segment["start"]))
            end_time = self.format_timedelta(datetime.timedelta(seconds=segment["end"]))
            subtitles.append(f"{i + 1}\n{start_time} --> {end_time}\n{segment['text']}\n\n")
        return subtitles

    @staticmethod
    def write_subtitles_to_file(subtitles, srt_file_path):
        with open(srt_file_path, "w", encoding="utf-8") as f:
            f.writelines(subtitles)

    @staticmethod
    def format_timedelta(td):
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = td.microseconds // 1000
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


class AudioToSRTConverter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio to SRT Converter")
        self.geometry("780x550")
        self.transcription_service = TranscriptionService()
        self.model_types = ['tiny', 'base', 'small', 'medium', 'large']

        # Explicitly declare attributes
        self.audio_file_entry = None
        self.srt_file_entry = None
        self.model_type_var = None
        self.model_type_combo = None
        self.progress_bar = None
        self.status_label = None
        self.transcription_text = None

        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self)
        frame.pack(padx=10, pady=10, fill='both', expand=True)

        ttk.Label(frame, text="Audio File:").grid(row=0, column=0, sticky="e", padx=(0, 5), pady=(0, 5))
        self.audio_file_entry = ttk.Entry(frame, width=50)
        self.audio_file_entry.grid(row=0, column=1, padx=(0, 5), pady=(0, 5))
        ttk.Button(frame, text="Browse", command=self.browse_audio_file).grid(row=0, column=2, padx=(0, 5), pady=(0, 5))

        ttk.Label(frame, text="Save SRT As:").grid(row=1, column=0, sticky="e", padx=(0, 5), pady=(0, 5))
        self.srt_file_entry = ttk.Entry(frame, width=50)
        self.srt_file_entry.grid(row=1, column=1, padx=(0, 5), pady=(0, 5))
        ttk.Button(frame, text="Save As", command=self.save_srt_file).grid(row=1, column=2, padx=(0, 5), pady=(0, 5))

        ttk.Label(frame, text="Model:").grid(row=2, column=0, sticky="e", padx=(0, 5), pady=(0, 5))
        self.model_type_var = tk.StringVar()
        self.model_type_combo = ttk.Combobox(frame, textvariable=self.model_type_var, values=self.model_types,
                                             state="readonly")
        self.model_type_combo.current(4)  # default to 'large'
        self.model_type_combo.grid(row=2, column=1, sticky="ew", padx=(0, 5), pady=(0, 5))

        self.progress_bar = ttk.Progressbar(frame, orient="horizontal", length=190, mode="indeterminate")
        self.progress_bar.grid(row=5, column=1, pady=(10, 0), sticky='ew')
        self.status_label = ttk.Label(frame, text="Status: Ready")
        self.status_label.grid(row=4, column=1, padx=(10, 0), pady=(10, 0), sticky='w')

        ttk.Button(frame, text="Process", command=self.start_transcription_process).grid(row=3, column=1, padx=(10, 0),
                                                                                         pady=(10, 0), sticky="w")
        ttk.Button(frame, text="Cancel", command=self.cancel_transcription_process).grid(row=3, column=1, padx=(10, 0),
                                                                                         pady=(10, 0), sticky="e")

        ttk.Button(frame, text="Help", command=self.open_help_window).grid(row=6, column=1, pady=(10, 0), sticky="ew")

        self.transcription_text = scrolledtext.ScrolledText(self, width=80, height=20)
        self.transcription_text.pack(padx=10, pady=10)
        self.transcription_text.config(state=tk.DISABLED)

    def open_help_window(self):
        help_window = tk.Toplevel(self)
        help_window.title("Help Information")
        help_window.geometry("650x250")

        help_text = """
What this script does?
This script creates a complete .srt file (Transcription + timing) based on the provided audio file.

Which model to choose?
"Tiny" is the fastest model but least accurate, while "Large" is the slowest, but almost 100% accurate.
Using the large model requires a powerful workstation and not too long audio file. As of my testing,
10 minutes of audio took about 2 hours of processing time using CPU. If you have a CUDA enabled
NVIDIA GPU, it might take significantly less time.

- Supported audio file formats: MP3, WAV, M4A
- Recommended maximum file size: 500MB
- Recommended maximum audio file duration: 2 hours

"""
        ttk.Label(help_window, text=help_text, justify=tk.LEFT).pack(padx=10, pady=10)

    def browse_audio_file(self):
        file_path = filedialog.askopenfilename(title="Select Audio File",
                                               filetypes=(("Audio Files", "*.mp3 *.wav *.m4a"), ("All Files", "*.*")))
        self.audio_file_entry.delete(0, tk.END)
        self.audio_file_entry.insert(0, file_path)

    def save_srt_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".srt", filetypes=[("SRT Files", "*.srt")])
        self.srt_file_entry.delete(0, tk.END)
        self.srt_file_entry.insert(0, file_path)

    def start_transcription_process(self):
        audio_file_path = self.audio_file_entry.get()
        srt_file_path = self.srt_file_entry.get()
        model_type = self.model_type_var.get()

        if not audio_file_path or not srt_file_path:
            messagebox.showwarning("Warning", "Please select an audio file and specify the SRT file save location.")
            return

        if not os.path.exists(audio_file_path):
            messagebox.showerror("Error", "File does not exist.")
            return

        self.progress_bar.start(10)
        threading.Thread(target=self.transcription_service.transcribe_audio_to_srt, args=(
            audio_file_path, srt_file_path, model_type, self.update_status, self.update_transcription_text)).start()

    def update_status(self, message):
        self.status_label.config(text=f"Status: {message}")
        self.status_label.update()

    def update_transcription_text(self, text):
        self.transcription_text.config(state=tk.NORMAL)
        self.transcription_text.delete(1.0, tk.END)
        self.transcription_text.insert(tk.END, text)
        self.transcription_text.config(state=tk.DISABLED)

    def cancel_transcription_process(self):
        self.transcription_service.cancel_transcription()
        self.update_status("Transcription cancelled.")
        self.progress_bar.stop()


if __name__ == "__main__":
    app = AudioToSRTConverter()
    app.mainloop()
