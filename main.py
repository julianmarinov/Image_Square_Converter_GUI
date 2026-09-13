import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

from square_converter import convert_all, find_images, validate_dirs

POLL_MS = 100
MAX_FAILURES_SHOWN = 5


class ConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Square Converter")

        self.import_path_var = tk.StringVar()
        self.export_path_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Select an import and an export folder.")

        self.events = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker = None
        self.closing = False
        self.total = 0

        ttk.Label(root, text="Import Path:").grid(column=0, row=0, sticky=tk.W, padx=10, pady=10)
        ttk.Entry(root, textvariable=self.import_path_var, width=50).grid(column=1, row=0, padx=10)
        self.import_btn = ttk.Button(root, text="Browse", command=self.browse_import_path)
        self.import_btn.grid(column=2, row=0, padx=10)

        ttk.Label(root, text="Export Path:").grid(column=0, row=1, sticky=tk.W, padx=10, pady=10)
        ttk.Entry(root, textvariable=self.export_path_var, width=50).grid(column=1, row=1, padx=10)
        self.export_btn = ttk.Button(root, text="Browse", command=self.browse_export_path)
        self.export_btn.grid(column=2, row=1, padx=10)

        self.convert_btn = ttk.Button(root, text="Convert to Square", command=self.on_convert_click)
        self.convert_btn.grid(column=1, row=2, pady=20)

        self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.grid(column=1, row=3, pady=10, padx=10, sticky=tk.E + tk.W)

        ttk.Label(root, textvariable=self.status_var).grid(column=1, row=4, pady=(0, 10), padx=10)

        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def browse_import_path(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.import_path_var.set(folder_selected)

    def browse_export_path(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.export_path_var.set(folder_selected)

    def set_busy(self, busy):
        state = "disabled" if busy else "normal"
        for button in (self.convert_btn, self.import_btn, self.export_btn):
            button["state"] = state

    def on_convert_click(self):
        import_dir = self.import_path_var.get().strip()
        export_dir = self.export_path_var.get().strip()
        error = validate_dirs(import_dir, export_dir)
        if error:
            messagebox.showerror("Error", error)
            return

        self.set_busy(True)
        self.progress['value'] = 0
        self.status_var.set("Looking for images...")
        self.cancel_event.clear()
        self.worker = threading.Thread(target=self.run_conversion, args=(import_dir, export_dir), daemon=True)
        self.worker.start()
        self.root.after(POLL_MS, self.poll_events)

    def run_conversion(self, import_dir, export_dir):
        # Runs on the worker thread: talk to the GUI only through the queue.
        try:
            paths = find_images(import_dir, export_dir)
            self.events.put(("total", len(paths)))
            result = convert_all(
                paths, import_dir, export_dir,
                on_progress=lambda done, total: self.events.put(("progress", done)),
                cancel_event=self.cancel_event,
            )
            self.events.put(("done", (len(paths),) + result))
        except Exception as e:
            self.events.put(("error", str(e)))

    def poll_events(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "total":
                    self.progress['maximum'] = max(payload, 1)
                    self.status_var.set(f"Converting 0 of {payload}...")
                    self.total = payload
                elif kind == "progress":
                    self.progress['value'] = payload
                    self.status_var.set(f"Converting {payload} of {self.total}...")
                elif kind == "done":
                    self.finish(*payload)
                    return
                elif kind == "error":
                    self.finish_with_error(payload)
                    return
        except queue.Empty:
            pass
        self.root.after(POLL_MS, self.poll_events)

    def finish(self, total, converted, failures):
        if self.closing:
            self.root.destroy()
            return
        self.set_busy(False)

        if total == 0:
            self.status_var.set("No images found.")
            messagebox.showinfo("No images", "No .png, .jpg, .jpeg or .gif images were found in the import folder.")
            return

        summary = f"Converted {converted} of {total} images."
        self.status_var.set(summary)
        if not failures:
            messagebox.showinfo("Success", summary)
            return

        lines = [f"{os.path.basename(path)}: {error}" for path, error in failures[:MAX_FAILURES_SHOWN]]
        if len(failures) > MAX_FAILURES_SHOWN:
            lines.append(f"...and {len(failures) - MAX_FAILURES_SHOWN} more.")
        messagebox.showwarning("Finished with errors", f"{summary}\nSkipped {len(failures)}:\n\n" + "\n".join(lines))

    def finish_with_error(self, error):
        if self.closing:
            self.root.destroy()
            return
        self.set_busy(False)
        self.status_var.set("Conversion failed.")
        messagebox.showerror("Error", f"An error occurred: {error}")

    def on_close(self):
        if self.worker is not None and self.worker.is_alive():
            # Let the current image finish saving, then close from poll_events.
            self.closing = True
            self.cancel_event.set()
            self.status_var.set("Stopping...")
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    ConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
