import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image


def make_square(im, fill_color=(255, 255, 255)):
    """
    Add white space to the image to make it square.
    """
    x, y = im.size
    size = max(x, y)
    new_im = Image.new('RGB', (size, size), fill_color)
    new_im.paste(im, ((size - x) // 2, (size - y) // 2))
    return new_im


def convert_images_to_square(import_path, export_path):
    """
    Convert all images in the given folder to square.
    """
    for folder, dirs, files in os.walk(import_path):
        for filename in files:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                file_path = os.path.join(folder, filename)

                with Image.open(file_path) as img:
                    squared_image = make_square(img)
                    squared_image.save(os.path.join(export_path, filename))
                    progress.step(1)
                    root.update()


def browse_import_path():
    folder_selected = filedialog.askdirectory()
    import_path_var.set(folder_selected)


def browse_export_path():
    folder_selected = filedialog.askdirectory()
    export_path_var.set(folder_selected)


def on_convert_click():
    if not import_path_var.get() or not os.path.isdir(import_path_var.get()) or \
       not export_path_var.get() or not os.path.isdir(export_path_var.get()):
        messagebox.showerror("Error", "Please select valid import and export paths.")
        return

    convert_btn["state"] = "disabled"
    progress['maximum'] = len(os.listdir(import_path_var.get()))

    try:
        convert_images_to_square(import_path_var.get(), export_path_var.get())
        messagebox.showinfo("Success", "Conversion completed successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
    finally:
        convert_btn["state"] = "normal"


root = tk.Tk()
root.title("Image Square Converter")

import_path_var = tk.StringVar()
export_path_var = tk.StringVar()

ttk.Label(root, text="Import Path:").grid(column=0, row=0, sticky=tk.W, padx=10, pady=10)

import_entry = ttk.Entry(root, textvariable=import_path_var, width=50)
import_entry.grid(column=1, row=0, padx=10)
import_entry.insert(0, "Select import directory...")  # Placeholder text
ttk.Button(root, text="Browse", command=browse_import_path).grid(column=2, row=0, padx=10)

export_entry = ttk.Entry(root, textvariable=export_path_var, width=50)
export_entry.grid(column=1, row=1, padx=10)
export_entry.insert(0, "Select export directory...")  # Placeholder text
ttk.Button(root, text="Browse", command=browse_export_path).grid(column=2, row=1, padx=10)

convert_btn = ttk.Button(root, text="Convert to Square", command=on_convert_click)
convert_btn.grid(column=1, row=2, pady=20)

progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, mode='determinate')
progress.grid(column=1, row=3, pady=10, padx=10, sticky=tk.E + tk.W)

root.mainloop()
