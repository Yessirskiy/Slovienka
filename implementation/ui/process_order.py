import tkinter as tk
from tkinter import ttk, messagebox

from ui.common import (
    BG,
    CARD,
    GREEN,
    AMBER,
    MUTED,
    TEXT,
    RED,
    card,
    heading,
    sub,
    nav_row,
    _delivery_str,
)

from application.user_handlers import GetCustomerHandler
from application.flowers_handlers import GetBouquetHandler
from application.customer_order_handlers import (
    GetOrderHandler,
    GetOrderDeliveryHandler,
    StartPreparingCustomerOrderHandler,
    FinishPreparingCustomerOrderHandler,
)

# ══════════════════════════════════════════════════════════════════════════════
# PROCESS ORDER – Step 1: oznacitAkoVPriprave
# ══════════════════════════════════════════════════════════════════════════════


class ProcessStepDetail(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        user = self.app.current_user
        name = f"{user.first_name} {user.last_name}" if user else "Kvetinár"
        self.app.set_header(subtitle=f"Kvetinár  ·  {name}", show_logout=True)

        order_id = self.app.process_order_id.get()
        try:
            order = GetOrderHandler().handler(florist_id=user.id, order_id=order_id)
        except ValueError:
            messagebox.showerror("Chyba", "Objednávka nenájdená.")
            self._go_orders()
            return

        try:
            customer = GetCustomerHandler().handler(order.customer_id)
            cust_name = f"{customer.first_name} {customer.last_name}"
        except ValueError:
            cust_name = "—"

        try:
            bouq_name = GetBouquetHandler().handler(order.bouquet_id).name
        except ValueError:
            bouq_name = f"ID {order.bouquet_id}"

        delivery = GetOrderDeliveryHandler().handler(order_id)
        address, when = _delivery_str(delivery)

        heading(self, f"Spracovanie objednávky #{order_id}")
        sub(self, "Skontrolujte detaily a dostupnosť komponentov")

        c = card(self)
        c.pack(fill="x", pady=4)
        for label, value in [
            ("Zákazník", cust_name),
            ("Kytica", bouq_name),
            ("Adresa", address),
            ("Doručenie", when),
            ("Platba", order.payment_method.name.replace("_", " ").title()),
            ("Cena", f"{order.total:.2f} €"),
            ("Stav", order.status.value.upper()),
        ]:
            row = tk.Frame(c, bg=CARD)
            row.pack(fill="x", padx=16, pady=3)
            tk.Label(
                row,
                text=label,
                bg=CARD,
                fg=MUTED,
                font=("Helvetica", 9),
                width=14,
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
        tk.Frame(c, bg=CARD, height=6).pack()

        c2 = card(self)
        c2.pack(fill="x", pady=(8, 4))
        tk.Label(
            c2,
            text="Sú všetky komponenty dostupné?",
            bg=CARD,
            fg=TEXT,
            font=("Helvetica", 10, "bold"),
        ).pack(anchor="w", padx=14, pady=(10, 6))

        self.components_var = tk.StringVar(value="yes")
        missing_frame = tk.Frame(c2, bg=CARD)
        self.missing_entry = ttk.Entry(missing_frame, width=50)

        def _toggle():
            if self.components_var.get() == "no":
                tk.Label(
                    missing_frame,
                    text="Uveďte chýbajúce komponenty (oddeľte čiarkou):",
                    bg=CARD,
                    fg=MUTED,
                    font=("Helvetica", 9),
                ).pack(anchor="w")
                self.missing_entry.pack(fill="x", pady=(2, 0))
                missing_frame.pack(fill="x", padx=14, pady=(0, 10))
            else:
                missing_frame.pack_forget()

        btn_row = tk.Frame(c2, bg=CARD)
        btn_row.pack(fill="x", padx=14, pady=(0, 8))
        tk.Radiobutton(
            btn_row,
            text="Áno – pripraviť",
            variable=self.components_var,
            value="yes",
            bg=CARD,
            activebackground=CARD,
            selectcolor=GREEN,
            font=("Helvetica", 10),
            cursor="hand2",
            command=_toggle,
        ).pack(side="left", padx=(0, 24))
        tk.Radiobutton(
            btn_row,
            text="Nie – chýbajú komponenty",
            variable=self.components_var,
            value="no",
            bg=CARD,
            activebackground=CARD,
            selectcolor=RED,
            font=("Helvetica", 10),
            cursor="hand2",
            command=_toggle,
        ).pack(side="left")

        nav_row(
            self,
            back_cmd=self._go_orders,
            next_cmd=self._confirm,
            next_text="Potvrdiť →",
            next_style="Amber.TButton",
        )

    def _go_orders(self):
        from ui.app import KvetinarOrders

        self.app.show(KvetinarOrders)

    def _confirm(self):
        order_id = self.app.process_order_id.get()
        florist_id = self.app.current_user.id
        comp_avail = self.components_var.get() == "yes"
        missing = None
        if not comp_avail:
            text = self.missing_entry.get().strip()
            if text:
                missing = [c.strip() for c in text.split(",") if c.strip()]

        try:
            # oznacitAkoVPriprave() → zmenitStavObjednavky()
            result = StartPreparingCustomerOrderHandler().handler(
                florist_id=florist_id,
                order_id=order_id,
                components_available=comp_avail,
                missing_components=missing,
            )
            self.app.process_result = result
            self.app.process_components_ok = comp_avail
            if comp_avail and result["status"] == "success":
                # pripraviKyticu() — florist physically prepares the bouquet
                self.app.show(ProcessStepPrepare)
            else:
                self.app.show(ProcessStepDone)
        except ValueError as e:
            messagebox.showerror("Chyba", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# PROCESS ORDER – Step 2: pripraviKyticu
# ══════════════════════════════════════════════════════════════════════════════


class ProcessStepPrepare(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        user = self.app.current_user
        name = f"{user.first_name} {user.last_name}" if user else "Kvetinár"
        self.app.set_header(subtitle=f"Kvetinár  ·  {name}", show_logout=True)

        order_id = self.app.process_order_id.get()

        tk.Label(self, text="🌸", bg=BG, font=("Helvetica", 42)).pack(pady=(20, 4))
        heading(self, f"Pripravte kyticu — objednávka #{order_id}")
        sub(
            self,
            "Objednávka je označená ako PRIPRAVUJE SA. Po fyzickej príprave kytice kliknite na tlačidlo.",
        )

        c = card(self)
        c.pack(fill="x", pady=8)
        tk.Label(
            c,
            text="✔  Stav objednávky zmenený na: PRIPRAVUJE SA",
            bg=CARD,
            fg=GREEN,
            font=("Helvetica", 10, "bold"),
        ).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(
            c,
            text="⏳  Čaká sa na prípravu kytice kvetinárom...",
            bg=CARD,
            fg=AMBER,
            font=("Helvetica", 10),
        ).pack(anchor="w", padx=14, pady=(0, 12))

        nav_row(
            self,
            back_cmd=self._go_orders,
            next_cmd=self._finish,
            next_text="Kytica je pripravená ✓",
            next_style="Amber.TButton",
        )

    def _go_orders(self):
        from ui.app import KvetinarOrders

        self.app.show(KvetinarOrders)

    def _finish(self):
        # oznacitAkoDokoncenu() → zmenitStavObjednavky, vygenerujKod, vytvoritNotifikaciu
        try:
            result = FinishPreparingCustomerOrderHandler().handler(
                florist_id=self.app.current_user.id,
                order_id=self.app.process_order_id.get(),
            )
            self.app.process_result = result
            self.app.process_components_ok = True
            self.app.show(ProcessStepDone)
        except ValueError as e:
            messagebox.showerror("Chyba", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# PROCESS ORDER – Step 3: zobrazit potvrdenie
# ══════════════════════════════════════════════════════════════════════════════


class ProcessStepDone(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        user = self.app.current_user
        name = f"{user.first_name} {user.last_name}" if user else "Kvetinár"
        self.app.set_header(subtitle=f"Kvetinár  ·  {name}", show_logout=True)

        result = self.app.process_result
        comp_ok = self.app.process_components_ok
        order_id = self.app.process_order_id.get()

        if comp_ok and result.get("status") == "success":
            tk.Label(self, text="✅", bg=BG, font=("Helvetica", 36)).pack(pady=(16, 4))
            tk.Label(
                self,
                text=f"Objednávka #{order_id} je pripravená na doručenie!",
                bg=BG,
                fg=GREEN,
                font=("Georgia", 14, "bold"),
            ).pack(pady=(0, 16))
            c = card(self)
            c.pack(fill="x", pady=4)
            tk.Label(
                c,
                text="Dokončené kroky",
                bg=CARD,
                fg=TEXT,
                font=("Helvetica", 10, "bold"),
            ).pack(anchor="w", padx=14, pady=(10, 4))
            for text in [
                '✔  Stav objednávky zmenený na "Pripravuje sa"',
                "✔  Kytica bola pripravená a zviazaná",
                '✔  Stav objednávky zmenený na "Pripravená na doručenie"',
            ]:
                tk.Label(c, text=text, bg=CARD, fg=GREEN, font=("Helvetica", 10)).pack(
                    anchor="w", padx=18, pady=2
                )
            tk.Label(
                c,
                text="Paralelné akcie (vykonané súčasne):",
                bg=CARD,
                fg=MUTED,
                font=("Helvetica", 9, "italic"),
            ).pack(anchor="w", padx=14, pady=(10, 2))
            for text in [
                "⚡  Vygenerovaný kód kuriéra",
                "⚡  Odoslaná notifikácia zákazníkovi",
                "⚡  Kuriér bol informovaný o objednávke",
            ]:
                tk.Label(c, text=text, bg=CARD, fg=AMBER, font=("Helvetica", 10)).pack(
                    anchor="w", padx=18, pady=2
                )
            tk.Frame(c, bg=CARD, height=8).pack()
        else:
            tk.Label(self, text="⚠️", bg=BG, font=("Helvetica", 36)).pack(pady=(16, 4))
            tk.Label(
                self,
                text=f"Objednávka #{order_id} nebola spracovaná",
                bg=BG,
                fg=AMBER,
                font=("Georgia", 14, "bold"),
            ).pack(pady=(0, 16))
            c = card(self)
            c.pack(fill="x", pady=4)
            tk.Label(
                c,
                text="Dôvod: Chýbajúce komponenty boli zaznamenané.",
                bg=CARD,
                fg=TEXT,
                font=("Helvetica", 10),
            ).pack(anchor="w", padx=14, pady=14)

        ttk.Button(
            self,
            text="⬅  Späť na objednávky",
            style="Amber.TButton",
            command=self._go_orders,
        ).pack(pady=16)

    def _go_orders(self):
        from ui.app import KvetinarOrders

        self.app.show(KvetinarOrders)
