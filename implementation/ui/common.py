import sys
import os
import tkinter as tk
from tkinter import ttk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BG        = "#FAF7F2"
CARD      = "#FFFFFF"
GREEN     = "#4A7C59"
GREEN_LT  = "#6B9E78"
GREEN_DK  = "#3A6347"
TEXT      = "#1A1A1A"
MUTED     = "#888888"
BORDER    = "#E0DAD0"
STEP_DONE = "#D6EAD9"
AMBER     = "#D4861A"
AMBER_LT  = "#F5A623"
RED       = "#C0392B"


def load_bouquet_image(size=(80, 80)):
    path = os.path.join(SCRIPT_DIR, "kytica.png")
    if not os.path.exists(path):
        return None
    try:
        if HAS_PIL:
            img = Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        else:
            photo = tk.PhotoImage(file=path)
            factor = max(1, min(photo.width() // size[0], photo.height() // size[1]))
            return photo.subsample(factor, factor) if factor > 1 else photo
    except Exception:
        return None


def card(parent, **kw):
    return tk.Frame(parent, bg=CARD, relief="flat",
                    highlightbackground=BORDER, highlightthickness=1, **kw)


def heading(parent, text, bg=BG):
    tk.Label(parent, text=text, bg=bg, fg=TEXT,
             font=("Georgia", 15, "bold")).pack(anchor="w", pady=(8, 2))


def sub(parent, text, bg=BG):
    tk.Label(parent, text=text, bg=bg, fg=MUTED,
             font=("Helvetica", 10)).pack(anchor="w", pady=(0, 10))


def field_label(parent, text):
    tk.Label(parent, text=text, bg=CARD, fg=MUTED,
             font=("Helvetica", 9)).pack(anchor="w", padx=14, pady=(10, 1))


def nav_row(parent, back_cmd=None, next_cmd=None, next_text="Ďalej →", next_style="Green.TButton"):
    row = tk.Frame(parent, bg=BG)
    row.pack(fill="x", pady=(14, 4))
    if back_cmd:
        ttk.Button(row, text="← Späť", style="Back.TButton", command=back_cmd).pack(side="left")
    if next_cmd:
        ttk.Button(row, text=next_text, style=next_style, command=next_cmd).pack(side="right")


def _delivery_str(delivery):
    if not delivery:
        return "—", "—"
    address = delivery.address
    when = (delivery.from_datetime.strftime("%d.%m.%Y  %H:%M") + "–" +
            delivery.to_datetime.strftime("%H:%M"))
    return address, when
