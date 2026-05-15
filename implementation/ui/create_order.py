import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from ui.common import (
    BG,
    CARD,
    GREEN,
    MUTED,
    TEXT,
    load_bouquet_image,
    card,
    heading,
    sub,
    field_label,
    nav_row,
    _delivery_str,
)

from domain.customer_order import PaymentMethod

from application.flowers_handlers import GetAvailableBouquetsHandler, GetBouquetHandler
from application.user_handlers import ListCustomersHandler, GetCustomerHandler
from application.customer_order_handlers import (
    ValidateCustomerOrderHandler,
    CreateCustomerOrderHandler,
    GetOrderDeliveryHandler,
)

# ══════════════════════════════════════════════════════════════════════════════
# CREATE ORDER – Step 1: prihlasit sa
# ══════════════════════════════════════════════════════════════════════════════


class StepCustomer(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self.app.set_header(subtitle="Nová objednávka")
        heading(self, "Kto ste?")
        sub(self, "Vyberte zákazníka zo zoznamu")

        customers = ListCustomersHandler().handler()
        self.selected = tk.IntVar(value=self.app.customer_id.get())

        c = card(self)
        c.pack(fill="x", pady=4)
        for cust in customers:
            row = tk.Frame(c, bg=CARD)
            row.pack(fill="x", padx=14, pady=8)
            tk.Radiobutton(
                row,
                variable=self.selected,
                value=cust.id,
                bg=CARD,
                activebackground=CARD,
                selectcolor=GREEN,
                cursor="hand2",
            ).pack(side="left")
            tk.Label(
                row,
                text=f"{cust.first_name} {cust.last_name}",
                bg=CARD,
                fg=TEXT,
                font=("Helvetica", 11, "bold"),
            ).pack(side="left", padx=6)
            tk.Label(
                row, text=cust.email, bg=CARD, fg=MUTED, font=("Helvetica", 9)
            ).pack(side="left")

        nav_row(
            self,
            back_cmd=lambda: self.app.go_wizard_back(StepCustomer),
            next_cmd=self._next,
        )

    def _next(self):
        self.app.customer_id.set(self.selected.get())
        self.app.go_wizard_next(StepCustomer)


# ══════════════════════════════════════════════════════════════════════════════
# CREATE ORDER – Step 2: vybrat_dostupne_kytice / nacitatKyticu
# ══════════════════════════════════════════════════════════════════════════════


class StepBouquet(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._img = None

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self.app.set_header(subtitle="Nová objednávka")
        heading(self, "Vyberte kyticu")
        sub(self, "Zobrazujú sa len dostupné kytice")

        # vybrat_dostupne_kytice()
        bouquets = GetAvailableBouquetsHandler().handler()
        self.selected = tk.IntVar(value=self.app.bouquet_id.get())
        self._img = load_bouquet_image(size=(80, 80))

        wrapper = tk.Frame(self, bg=BG)
        wrapper.pack(fill="both", expand=True)

        canvas = tk.Canvas(wrapper, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(wrapper, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

        for b in bouquets:
            c = card(inner)
            c.pack(fill="x", pady=5, padx=2)
            row = tk.Frame(c, bg=CARD)
            row.pack(fill="x", padx=12, pady=10)

            tk.Radiobutton(
                row,
                variable=self.selected,
                value=b.id,
                bg=CARD,
                activebackground=CARD,
                selectcolor=GREEN,
                cursor="hand2",
            ).pack(side="left", padx=(0, 6))

            if self._img:
                lbl = tk.Label(row, image=self._img, bg=CARD, cursor="hand2")
                lbl.pack(side="left", padx=(0, 10))
                lbl.bind("<Button-1>", lambda e, v=b.id: self.selected.set(v))
            else:
                tk.Label(row, text="🌸", bg=CARD, font=("Helvetica", 28)).pack(
                    side="left", padx=(0, 10)
                )

            info = tk.Frame(row, bg=CARD)
            info.pack(side="left", fill="x", expand=True)
            tk.Label(
                info,
                text=b.name,
                bg=CARD,
                fg=TEXT,
                font=("Helvetica", 11, "bold"),
                anchor="w",
            ).pack(anchor="w")
            tk.Label(
                info,
                text=b.description,
                bg=CARD,
                fg=MUTED,
                font=("Helvetica", 9),
                anchor="w",
                wraplength=380,
                justify="left",
            ).pack(anchor="w")

            tk.Label(
                row,
                text=f"{b.total:.2f} €",
                bg=CARD,
                fg=GREEN,
                font=("Helvetica", 13, "bold"),
            ).pack(side="right", padx=8)

        nav_row(
            self,
            back_cmd=lambda: self.app.go_wizard_back(StepBouquet),
            next_cmd=self._next,
        )

    def _next(self):
        if self.selected.get() == -1:
            messagebox.showwarning("Upozornenie", "Prosím vyberte kyticu.")
            return
        # nacitatKyticu() — confirm it is still available before proceeding
        try:
            bouquet = GetBouquetHandler().handler(self.selected.get())
            if not bouquet.is_available():
                messagebox.showwarning(
                    "Nedostupné", f"Kytica '{bouquet.name}' nie je momentalne dostupna."
                )
                return
        except ValueError:
            messagebox.showerror("Chyba", "Kytica nenájdená.")
            return
        self.app.bouquet_id.set(self.selected.get())
        self.app.go_wizard_next(StepBouquet)


# ══════════════════════════════════════════════════════════════════════════════
# CREATE ORDER – Step 3: [loop: skontrolovatUdaje]
# ══════════════════════════════════════════════════════════════════════════════


class StepDelivery(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self.app.set_header(subtitle="Nová objednávka")
        heading(self, "Údaje o doručení")
        sub(self, "Zadajte adresu a čas doručenia")

        c = card(self)
        c.pack(fill="x", pady=4)
        field_label(c, "Adresa doručenia")
        ttk.Entry(c, textvariable=self.app.address_var, width=50).pack(
            fill="x", padx=14, pady=(0, 4)
        )

        time_row = tk.Frame(c, bg=CARD)
        time_row.pack(fill="x", padx=14, pady=(6, 0))
        for label_text, var in [
            ("Dátum doručenia (DD.MM.RRRR)", self.app.from_date_var),
            ("Od (HH:MM)", self.app.from_time_var),
            ("Do (HH:MM)", self.app.to_time_var),
        ]:
            f = tk.Frame(time_row, bg=CARD)
            f.pack(side="left", expand=True, fill="x", padx=(0, 8))
            tk.Label(f, text=label_text, bg=CARD, fg=MUTED, font=("Helvetica", 9)).pack(
                anchor="w"
            )
            ttk.Entry(f, textvariable=var).pack(fill="x")
        tk.Frame(c, bg=CARD, height=12).pack()

        nav_row(
            self,
            back_cmd=lambda: self.app.go_wizard_back(StepDelivery),
            next_cmd=self._next,
        )

    def _next(self):
        try:
            date_str = self.app.from_date_var.get()
            from_dt = datetime.datetime.strptime(
                f"{date_str} {self.app.from_time_var.get()}", "%d.%m.%Y %H:%M"
            )
            to_dt = datetime.datetime.strptime(
                f"{date_str} {self.app.to_time_var.get()}", "%d.%m.%Y %H:%M"
            )
        except ValueError:
            messagebox.showerror(
                "Chyba", "Neplatný formát.\nPoužite DD.MM.RRRR a HH:MM."
            )
            return

        # skontrolovatUdaje() — matches the [loop Nespravne Udaje] block in the diagram
        result = ValidateCustomerOrderHandler().handler(
            customer_id=self.app.customer_id.get(),
            bouquet_id=self.app.bouquet_id.get(),
            address=self.app.address_var.get().strip(),
            from_datetime=from_dt,
            to_datetime=to_dt,
        )
        if not result["valid"]:
            messagebox.showerror("Nesprávne údaje", "\n".join(result["errors"]))
            return

        self.app.go_wizard_next(StepDelivery)


# ══════════════════════════════════════════════════════════════════════════════
# CREATE ORDER – Step 4: [zadatPlatobneUdaje]
# ══════════════════════════════════════════════════════════════════════════════


class StepPayment(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self.app.set_header(subtitle="Nová objednávka")
        heading(self, "Spôsob platby")
        sub(self, "Zvoľte preferovanú metódu platby")

        options = [
            (PaymentMethod.CASH.value, "💵  Hotovosť", "Platba pri doručení"),
            (
                PaymentMethod.CREDIT_CARD.value,
                "💳  Platobná karta",
                "Visa / Mastercard",
            ),
            (
                PaymentMethod.BANK_TRANSFER.value,
                "🏦  Bankový prevod",
                "IBAN platba vopred",
            ),
            (
                PaymentMethod.ONLINE_PAYMENT.value,
                "🌐  Online platba",
                "PayPal / Apple Pay",
            ),
        ]

        def _select(v):
            self.app.payment_var.set(v)
            self.on_show()

        def _bind_all(widget, v):
            widget.config(cursor="hand2")
            widget.bind("<Button-1>", lambda _e, val=v: _select(val))
            for child in widget.winfo_children():
                _bind_all(child, v)

        for val, label, desc in options:
            sel = self.app.payment_var.get() == val
            c = card(self)
            c.pack(fill="x", pady=5)
            row = tk.Frame(c, bg=CARD)
            row.pack(fill="x", padx=14, pady=10)
            tk.Radiobutton(
                row,
                variable=self.app.payment_var,
                value=val,
                bg=CARD,
                activebackground=CARD,
                selectcolor=GREEN,
                cursor="hand2",
                command=lambda v=val: _select(v),
            ).pack(side="left")
            tk.Label(
                row,
                text="●" if sel else "○",
                bg=CARD,
                fg=GREEN if sel else MUTED,
                font=("Helvetica", 14),
                width=2,
            ).pack(side="left")
            info = tk.Frame(row, bg=CARD)
            info.pack(side="left", padx=8, fill="x", expand=True)
            tk.Label(
                info,
                text=label,
                bg=CARD,
                fg=TEXT,
                font=("Helvetica", 11, "bold" if sel else "normal"),
            ).pack(anchor="w")
            tk.Label(info, text=desc, bg=CARD, fg=MUTED, font=("Helvetica", 9)).pack(
                anchor="w"
            )
            self.after(0, lambda w=c, v=val: _bind_all(w, v))

        nav_row(
            self,
            back_cmd=lambda: self.app.go_wizard_back(StepPayment),
            next_cmd=self._submit,
            next_text="Objednať ✓",
        )

    def _submit(self):
        try:
            date_str = self.app.from_date_var.get()
            from_dt = datetime.datetime.strptime(
                f"{date_str} {self.app.from_time_var.get()}", "%d.%m.%Y %H:%M"
            )
            to_dt = datetime.datetime.strptime(
                f"{date_str} {self.app.to_time_var.get()}", "%d.%m.%Y %H:%M"
            )
        except ValueError:
            messagebox.showerror("Chyba", "Neplatný formát dátumu/času.")
            return

        # vytvorit Objednavku()
        try:
            order = CreateCustomerOrderHandler().handler(
                customer_id=self.app.customer_id.get(),
                bouquet_id=self.app.bouquet_id.get(),
                address=self.app.address_var.get().strip(),
                from_datetime=from_dt,
                to_datetime=to_dt,
                payment_method=PaymentMethod(self.app.payment_var.get()),
            )
            self.app.last_order = order
            self.app.go_wizard_next(StepPayment)
        except ValueError as e:
            messagebox.showerror("Chyba pri vytváraní objednávky", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# CREATE ORDER – Step 5: [zobrazit Objednavku]
# ══════════════════════════════════════════════════════════════════════════════


class StepConfirm(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self.app.set_header(subtitle="Potvrdenie")
        order = getattr(self.app, "last_order", None)
        if not order:
            return

        tk.Label(self, text="✅", bg=BG, font=("Helvetica", 36)).pack(pady=(16, 4))
        tk.Label(
            self,
            text="Objednávka bola úspešne vytvorená!",
            bg=BG,
            fg=GREEN,
            font=("Georgia", 14, "bold"),
        ).pack(pady=(0, 16))

        try:
            customer = GetCustomerHandler().handler(order.customer_id)
            cust_name = f"{customer.first_name} {customer.last_name}"
        except ValueError:
            cust_name = "—"

        try:
            bouquet = GetBouquetHandler().handler(order.bouquet_id)
            bouq_name = bouquet.name
        except ValueError:
            bouq_name = f"ID {order.bouquet_id}"

        delivery = GetOrderDeliveryHandler().handler(order.id)
        address, when = _delivery_str(delivery)

        rows = [
            ("Číslo objednávky", f"#{order.id}"),
            ("Zákazník", cust_name),
            ("Kytica", bouq_name),
            ("Adresa", address),
            ("Doručenie", when),
            ("Platba", order.payment_method.name.replace("_", " ").title()),
            ("Cena", f"{order.total:.2f} €"),
            ("Stav", order.status.value.upper()),
        ]
        c = card(self)
        c.pack(fill="x", pady=4)
        for label, value in rows:
            row = tk.Frame(c, bg=CARD)
            row.pack(fill="x", padx=16, pady=4)
            tk.Label(
                row,
                text=label,
                bg=CARD,
                fg=MUTED,
                font=("Helvetica", 9),
                width=18,
                anchor="w",
            ).pack(side="left")
            tk.Label(
                row,
                text=value,
                bg=CARD,
                fg=TEXT,
                font=("Helvetica", 10, "bold"),
                anchor="w",
            ).pack(side="left")
        tk.Frame(c, bg=CARD, height=8).pack()

        ttk.Button(
            self,
            text="➕  Nová objednávka",
            style="Green.TButton",
            command=self._new_order,
        ).pack(pady=16)

    def _new_order(self):
        from ui.app import RoleSelect

        self.app.address_var.set("")
        self.app.bouquet_id.set(-1)
        self.app.payment_var.set(PaymentMethod.CASH.value)
        self.app.from_date_var.set(
            (datetime.date.today() + datetime.timedelta(days=1)).strftime("%d.%m.%Y")
        )
        self.app.from_time_var.set("09:00")
        self.app.to_time_var.set("12:00")
        self.app.show(RoleSelect)
