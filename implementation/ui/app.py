import sys
import os
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.customer_order import PaymentMethod

from application.user_handlers import ListFloristsHandler, GetCustomerHandler, GetFloristHandler
from application.flowers_handlers import GetBouquetHandler
from application.customer_order_handlers import (
    ListAllOrdersHandler,
    GetOrderDeliveryHandler,
)

from ui.common import (
    BG, CARD, GREEN, GREEN_LT, GREEN_DK, TEXT, MUTED, BORDER, STEP_DONE, AMBER, AMBER_LT, RED,
    card, heading, sub, nav_row, _delivery_str,
)
from ui.create_order import StepCustomer, StepBouquet, StepDelivery, StepPayment, StepConfirm
from ui.edit_order import EditStepCustomer, EditStepOrder, EditStepForm, EditStepConfirm
from ui.process_order import ProcessStepDetail, ProcessStepPrepare, ProcessStepDone


class FloristApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Slovienka")
        self.geometry("720x620")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.current_user  = None
        self.customer_id   = tk.IntVar(value=0)
        self.bouquet_id    = tk.IntVar(value=-1)
        self.payment_var   = tk.StringVar(value=PaymentMethod.CASH.value)
        self.address_var   = tk.StringVar()
        self.from_date_var = tk.StringVar(value=(datetime.date.today() + datetime.timedelta(days=1)).strftime("%d.%m.%Y"))
        self.from_time_var = tk.StringVar(value="09:00")
        self.to_time_var   = tk.StringVar(value="12:00")

        self.process_order_id      = tk.IntVar(value=-1)
        self.process_result        = {}
        self.process_components_ok = False

        self.edit_customer_id   = tk.IntVar(value=0)
        self.edit_order_id      = tk.IntVar(value=-1)
        self.edit_address_var   = tk.StringVar()
        self.edit_from_date_var = tk.StringVar()
        self.edit_from_time_var = tk.StringVar(value="09:00")
        self.edit_to_time_var   = tk.StringVar(value="12:00")
        self.last_edited_order  = None

        self._style()
        self._build_header()

        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True, padx=24, pady=8)

        self.all_screens = [
            RoleSelect, StepCustomer, StepBouquet, StepDelivery, StepPayment, StepConfirm,
            KvetinarLogin, KvetinarOrders,
            EditStepCustomer, EditStepOrder, EditStepForm, EditStepConfirm,
            ProcessStepDetail, ProcessStepPrepare, ProcessStepDone,
        ]
        self.wizard_steps = [StepCustomer, StepBouquet, StepDelivery, StepPayment, StepConfirm]

        self.frames = {}
        for F in self.all_screens:
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._build_steps_bar()
        self.show(RoleSelect)

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TEntry",         fieldbackground=CARD, bordercolor=BORDER, relief="flat", padding=6)
        s.configure("TCombobox",      fieldbackground=CARD, bordercolor=BORDER, relief="flat", padding=6)
        s.configure("Green.TButton",  background=GREEN,     foreground="white",
                    font=("Helvetica", 11, "bold"), borderwidth=0, padding=(16, 8))
        s.map("Green.TButton",  background=[("active", GREEN_LT)])
        s.configure("Amber.TButton",  background=AMBER,     foreground="white",
                    font=("Helvetica", 11, "bold"), borderwidth=0, padding=(16, 8))
        s.map("Amber.TButton",  background=[("active", AMBER_LT)])
        s.configure("Back.TButton",   background=BORDER,    foreground=TEXT,
                    font=("Helvetica", 10), borderwidth=0, padding=(12, 7))
        s.map("Back.TButton",   background=[("active", "#CCC6BC")])

    def _build_header(self):
        self.hdr = tk.Frame(self, bg=GREEN, height=56)
        self.hdr.pack(fill="x")
        self.hdr.pack_propagate(False)
        self.hdr_title = tk.Label(self.hdr, text="🌸  Slovienka", bg=GREEN, fg="white",
                                  font=("Georgia", 17, "bold"))
        self.hdr_title.pack(side="left", padx=20, pady=12)
        self.hdr_right = tk.Label(self.hdr, text="", bg=GREEN, fg="#C8E6C9",
                                  font=("Helvetica", 10))
        self.hdr_right.pack(side="right", padx=20)

    def set_header(self, subtitle="", right_text="", show_logout=False):
        self.hdr_title.config(text=f"🌸  Slovienka  {'·  ' + subtitle if subtitle else ''}")
        if show_logout:
            self.hdr_right.destroy()
            self.hdr_right = tk.Button(
                self.hdr, text="⬅  Odhlásiť", bg=GREEN_DK, fg="white",
                font=("Helvetica", 9), relief="flat", cursor="hand2",
                activebackground="#2A4A30", activeforeground="white",
                command=self.logout)
            self.hdr_right.pack(side="right", padx=16, pady=14)
        else:
            if isinstance(self.hdr_right, tk.Button):
                self.hdr_right.destroy()
                self.hdr_right = tk.Label(self.hdr, text=right_text, bg=GREEN, fg="#C8E6C9",
                                          font=("Helvetica", 10))
                self.hdr_right.pack(side="right", padx=20)
            else:
                self.hdr_right.config(text=right_text)

    def _build_steps_bar(self):
        self.steps_bar = tk.Frame(self, bg=BG)
        self.steps_bar.pack(fill="x", padx=24, pady=(10, 0))
        labels = ["Zákazník", "Kytica", "Doručenie", "Platba", "Potvrdenie"]
        self.step_labels = []
        for i, name in enumerate(labels):
            f = tk.Frame(self.steps_bar, bg=BG)
            f.pack(side="left", expand=True)
            num = tk.Label(f, text=str(i+1), width=2, font=("Helvetica", 9, "bold"),
                           bg=BORDER, fg=MUTED, relief="flat")
            num.pack()
            lbl = tk.Label(f, text=name, bg=BG, fg=MUTED, font=("Helvetica", 8))
            lbl.pack()
            self.step_labels.append((num, lbl))
            if i < len(labels) - 1:
                tk.Label(self.steps_bar, text="──", bg=BG, fg=BORDER).pack(side="left", expand=True)

    def update_steps_bar(self, current_idx):
        for i, (num, lbl) in enumerate(self.step_labels):
            if i < current_idx:
                num.config(bg=STEP_DONE, fg=GREEN); lbl.config(fg=GREEN, font=("Helvetica", 8))
            elif i == current_idx:
                num.config(bg=GREEN, fg="white");   lbl.config(fg=GREEN, font=("Helvetica", 8, "bold"))
            else:
                num.config(bg=BORDER, fg=MUTED);    lbl.config(fg=MUTED, font=("Helvetica", 8))

    def show(self, frame_class):
        in_wizard = frame_class in self.wizard_steps
        self.steps_bar.pack_configure() if in_wizard else self.steps_bar.pack_forget()
        if in_wizard:
            self.update_steps_bar(self.wizard_steps.index(frame_class))
        frame = self.frames[frame_class]
        frame.on_show()
        frame.lift()

    def go_wizard_next(self, current_class):
        idx = self.wizard_steps.index(current_class)
        if idx + 1 < len(self.wizard_steps):
            self.show(self.wizard_steps[idx + 1])

    def go_wizard_back(self, current_class):
        idx = self.wizard_steps.index(current_class)
        if idx > 0:
            self.show(self.wizard_steps[idx - 1])
        else:
            self.show(RoleSelect)

    def logout(self):
        self.current_user = None
        self.show(RoleSelect)


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 0 – Role selection
# ══════════════════════════════════════════════════════════════════════════════

class RoleSelect(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self):
        for w in self.winfo_children(): w.destroy()
        self.app.set_header()

        tk.Label(self, text="🌸", bg=BG, font=("Helvetica", 42)).pack(pady=(30, 4))
        tk.Label(self, text="Vitajte v Slovienke", bg=BG, fg=TEXT,
                 font=("Georgia", 18, "bold")).pack()
        tk.Label(self, text="Vyberte, s kým vstupujete do systému", bg=BG, fg=MUTED,
                 font=("Helvetica", 11)).pack(pady=(4, 30))

        row = tk.Frame(self, bg=BG)
        row.pack()

        c1 = card(row, width=220, height=190)
        c1.pack(side="left", padx=16)
        c1.pack_propagate(False)
        tk.Label(c1, text="🛍️", bg=CARD, font=("Helvetica", 32)).pack(pady=(16, 4))
        tk.Label(c1, text="Zákazník", bg=CARD, fg=TEXT,
                 font=("Helvetica", 13, "bold")).pack()
        tk.Label(c1, text="Spravovať objednávky", bg=CARD, fg=MUTED,
                 font=("Helvetica", 9)).pack()
        tk.Button(c1, text="Nová objednávka", bg=GREEN, fg="white",
                  font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2",
                  activebackground=GREEN_LT, activeforeground="white",
                  command=lambda: self.app.show(StepCustomer)).pack(pady=(8, 0), ipadx=8, ipady=4)
        tk.Button(c1, text="Upraviť objednávku", bg=GREEN_LT, fg="white",
                  font=("Helvetica", 9), relief="flat", cursor="hand2",
                  activebackground=GREEN, activeforeground="white",
                  command=self._go_edit).pack(pady=(6, 0), ipadx=8, ipady=3)

        c2 = card(row, width=220, height=160)
        c2.pack(side="left", padx=16)
        c2.pack_propagate(False)
        tk.Label(c2, text="🌿", bg=CARD, font=("Helvetica", 32)).pack(pady=(22, 4))
        tk.Label(c2, text="Kvetinár", bg=CARD, fg=TEXT,
                 font=("Helvetica", 13, "bold")).pack()
        tk.Label(c2, text="Prehľad objednávok", bg=CARD, fg=MUTED,
                 font=("Helvetica", 9)).pack()
        tk.Button(c2, text="Vstúpiť", bg=AMBER, fg="white",
                  font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2",
                  activebackground=AMBER_LT, activeforeground="white",
                  command=lambda: self.app.show(KvetinarLogin)).pack(pady=(10, 0), ipadx=12, ipady=4)

    def _go_edit(self):
        self.app.edit_order_id.set(-1)
        self.app.show(EditStepCustomer)


# ══════════════════════════════════════════════════════════════════════════════
# KVETINÁR – Login
# ══════════════════════════════════════════════════════════════════════════════

class KvetinarLogin(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self):
        for w in self.winfo_children(): w.destroy()
        self.app.set_header(subtitle="Kvetinár")
        heading(self, "Prihlásenie kvetinára")
        sub(self, "Vyberte svoj účet")

        floristi = ListFloristsHandler().handler()
        self.selected = tk.IntVar(value=floristi[0].id if floristi else -1)

        c = card(self)
        c.pack(fill="x", pady=4)

        if not floristi:
            tk.Label(c, text="Žiadny kvetinár nie je registrovaný.", bg=CARD, fg=RED,
                     font=("Helvetica", 10)).pack(padx=14, pady=14)
        else:
            for f in floristi:
                row = tk.Frame(c, bg=CARD)
                row.pack(fill="x", padx=14, pady=8)
                tk.Radiobutton(row, variable=self.selected, value=f.id,
                               bg=CARD, activebackground=CARD, selectcolor=AMBER,
                               cursor="hand2").pack(side="left")
                tk.Label(row, text="🌿", bg=CARD, font=("Helvetica", 16)).pack(side="left", padx=4)
                tk.Label(row, text=f"{f.first_name} {f.last_name}",
                         bg=CARD, fg=TEXT, font=("Helvetica", 11, "bold")).pack(side="left", padx=4)
                tk.Label(row, text=f.email, bg=CARD, fg=MUTED,
                         font=("Helvetica", 9)).pack(side="left")

        nav_row(self,
                back_cmd=lambda: self.app.show(RoleSelect),
                next_cmd=self._login if floristi else None,
                next_text="Prihlásiť sa →",
                next_style="Amber.TButton")

    def _login(self):
        try:
            user = GetFloristHandler().handler(self.selected.get())
        except ValueError:
            messagebox.showerror("Chyba", "Neplatný kvetinár.")
            return
        self.app.current_user = user
        self.app.show(KvetinarOrders)


# ══════════════════════════════════════════════════════════════════════════════
# KVETINÁR – Orders list
# ══════════════════════════════════════════════════════════════════════════════

class KvetinarOrders(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self):
        for w in self.winfo_children(): w.destroy()
        user = self.app.current_user
        name = f"{user.first_name} {user.last_name}" if user else "Kvetinár"
        self.app.set_header(subtitle=f"Kvetinár  ·  {name}", show_logout=True)

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", pady=(6, 2))
        tk.Label(top, text="Objednávky na prípravu", bg=BG, fg=TEXT,
                 font=("Georgia", 14, "bold")).pack(side="left")
        tk.Button(top, text="↻ Obnoviť", bg=BORDER, fg=TEXT, relief="flat",
                  font=("Helvetica", 9), cursor="hand2", activebackground="#CCC6BC",
                  command=self._load).pack(side="right")

        cols   = ("#", "Zákazník", "Kytica", "Adresa", "Doručenie", "Platba", "Cena €", "Stav")
        widths = (38, 140, 145, 165, 135, 100, 65, 80)

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, pady=(4, 0))

        s = ttk.Style()
        s.configure("K.Treeview",
                    background=CARD, fieldbackground=CARD, foreground=TEXT,
                    rowheight=30, font=("Helvetica", 10))
        s.configure("K.Treeview.Heading",
                    background=AMBER, foreground="white",
                    font=("Helvetica", 10, "bold"), relief="flat")
        s.map("K.Treeview",
              background=[("selected", "#FFF3E0")],
              foreground=[("selected", AMBER)])

        vsb = ttk.Scrollbar(frame, orient="vertical")
        hsb = ttk.Scrollbar(frame, orient="horizontal")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings",
                                 style="K.Treeview",
                                 yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=w, anchor="w")

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self.tree.tag_configure("even",  background="#FFFBF5")
        self.tree.tag_configure("odd",   background=CARD)
        self.tree.tag_configure("faded", foreground="#BBBBBB")

        self.status_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self.status_var, bg=BG, fg=MUTED,
                 font=("Helvetica", 9), anchor="w").pack(fill="x", pady=(4, 0))

        action_row = tk.Frame(self, bg=BG)
        action_row.pack(fill="x", pady=(6, 4))
        ttk.Button(action_row, text="← Späť", style="Back.TButton",
                   command=lambda: self.app.show(RoleSelect)).pack(side="left")
        ttk.Button(action_row, text="Spracovať vybraný →", style="Amber.TButton",
                   command=self._process_selected).pack(side="right")

        self._load()

    def _process_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Upozornenie", "Vyberte objednávku zo zoznamu.")
            return
        self.app.process_order_id.set(int(sel[0]))
        self.app.show(ProcessStepDetail)

    def _load(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        user = self.app.current_user
        if not user:
            return

        try:
            orders = ListAllOrdersHandler().handler(florist_id=user.id)
        except ValueError:
            self.status_var.set("Chyba pri načítaní objednávok.")
            return

        if not orders:
            self.status_var.set("Zatiaľ žiadne objednávky.")
            return

        finished = {"delivered", "completed", "canceled"}
        for i, order in enumerate(orders):
            try:
                customer  = GetCustomerHandler().handler(order.customer_id)
                cust_name = f"{customer.first_name} {customer.last_name}"
            except (ValueError, Exception):
                cust_name = "—"

            try:
                bouquet   = GetBouquetHandler().handler(order.bouquet_id)
                bouq_name = bouquet.name
            except ValueError:
                bouq_name = f"ID {order.bouquet_id}"

            delivery      = GetOrderDeliveryHandler().handler(order.id)
            address, when = _delivery_str(delivery)
            payment       = order.payment_method.name.replace("_", " ").title()
            price         = f"{order.total:.2f}"
            status        = order.status.value.upper()
            is_done       = order.status.value in finished
            tag           = "faded" if is_done else ("even" if i % 2 == 0 else "odd")

            self.tree.insert("", "end", iid=str(order.id),
                             values=(f"#{order.id}", cust_name, bouq_name, address,
                                     when, payment, price, status),
                             tags=(tag,))

        pending = sum(1 for o in orders if o.status.value not in finished)
        self.status_var.set(f"Celkom: {len(orders)} objednávok  ·  Čaká na prípravu: {pending}")
