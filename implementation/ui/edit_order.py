import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from ui.common import (
    BG,
    CARD,
    GREEN,
    MUTED,
    TEXT,
    card,
    heading,
    sub,
    field_label,
    nav_row,
    _delivery_str,
)

from application.user_handlers import ListCustomersHandler, GetCustomerHandler
from application.flowers_handlers import GetBouquetHandler
from application.customer_order_handlers import (
    ListCustomerOrdersHandler,
    GetCustomerOrderHandler,
    EditCustomerOrderHandler,
    GetOrderDeliveryHandler,
)

# ══════════════════════════════════════════════════════════════════════════════
# EDIT ORDER – Step 1: prihlasit sa
# ══════════════════════════════════════════════════════════════════════════════


class EditStepCustomer(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self.app.set_header(subtitle="Upraviť objednávku")
        heading(self, "Kto ste?")
        sub(self, "Vyberte zákazníka, ktorého objednávku chcete upraviť")

        customers = ListCustomersHandler().handler()
        self.selected = tk.IntVar(value=self.app.edit_customer_id.get())

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
            back_cmd=self._back,
            next_cmd=lambda: (
                self.app.edit_customer_id.set(self.selected.get()),
                self.app.show(EditStepOrder),
            ),
        )

    def _back(self):
        from ui.app import RoleSelect

        self.app.show(RoleSelect)


# ══════════════════════════════════════════════════════════════════════════════
# EDIT ORDER – Step 2: nacitat objednavky & vybarat objednavku
# ══════════════════════════════════════════════════════════════════════════════


class EditStepOrder(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self.app.set_header(subtitle="Upraviť objednávku")
        heading(self, "Vaše objednávky")
        sub(self, "Vyberte objednávku, ktorú chcete zmeniť")

        customer_id = self.app.edit_customer_id.get()
        orders = ListCustomerOrdersHandler().handler(customer_id=customer_id)

        self.selected = tk.IntVar(
            value=(
                self.app.edit_order_id.get()
                if self.app.edit_order_id.get() in [o.id for o in orders]
                else -1
            )
        )

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

        if not orders:
            tk.Label(
                inner,
                text="Nemáte žiadne objednávky.",
                bg=BG,
                fg=MUTED,
                font=("Helvetica", 11),
            ).pack(pady=20)
        else:
            for order in orders:
                try:
                    bouq_name = GetBouquetHandler().handler(order.bouquet_id).name
                except ValueError:
                    bouq_name = f"ID {order.bouquet_id}"

                delivery = GetOrderDeliveryHandler().handler(order.id)
                address, when = _delivery_str(delivery)
                status = order.status.value.upper()

                c = card(inner)
                c.pack(fill="x", pady=5, padx=2)
                row = tk.Frame(c, bg=CARD)
                row.pack(fill="x", padx=12, pady=10)
                tk.Radiobutton(
                    row,
                    variable=self.selected,
                    value=order.id,
                    bg=CARD,
                    activebackground=CARD,
                    selectcolor=GREEN,
                    cursor="hand2",
                ).pack(side="left", padx=(0, 8))
                info = tk.Frame(row, bg=CARD)
                info.pack(side="left", fill="x", expand=True)
                tk.Label(
                    info,
                    text=f"#{order.id}  ·  {bouq_name}",
                    bg=CARD,
                    fg=TEXT,
                    font=("Helvetica", 11, "bold"),
                    anchor="w",
                ).pack(anchor="w")
                tk.Label(
                    info,
                    text=f"{address}  ·  {when}",
                    bg=CARD,
                    fg=MUTED,
                    font=("Helvetica", 9),
                    anchor="w",
                ).pack(anchor="w")
                tk.Label(
                    row, text=status, bg=CARD, fg=MUTED, font=("Helvetica", 9, "italic")
                ).pack(side="right", padx=8)
                tk.Label(
                    row,
                    text=f"{order.total:.2f} €",
                    bg=CARD,
                    fg=GREEN,
                    font=("Helvetica", 12, "bold"),
                ).pack(side="right", padx=4)

        nav_row(
            self,
            back_cmd=lambda: self.app.show(EditStepCustomer),
            next_cmd=self._next if orders else None,
            next_text="Upraviť →",
        )

    def _next(self):
        if self.selected.get() == -1:
            messagebox.showwarning("Upozornenie", "Prosím vyberte objednávku.")
            return
        self.app.edit_order_id.set(self.selected.get())
        self._prefill()
        self.app.show(EditStepForm)

    def _prefill(self):
        order_id = self.app.edit_order_id.get()
        customer_id = self.app.edit_customer_id.get()
        try:
            GetCustomerOrderHandler().handler(
                customer_id=customer_id, order_id=order_id
            )
        except ValueError:
            return
        delivery = GetOrderDeliveryHandler().handler(order_id)
        if delivery:
            self.app.edit_address_var.set(delivery.address)
            self.app.edit_from_date_var.set(delivery.from_datetime.strftime("%d.%m.%Y"))
            self.app.edit_from_time_var.set(delivery.from_datetime.strftime("%H:%M"))
            self.app.edit_to_time_var.set(delivery.to_datetime.strftime("%H:%M"))


# ══════════════════════════════════════════════════════════════════════════════
# EDIT ORDER – Step 3: upravit objednavku
# ══════════════════════════════════════════════════════════════════════════════


class EditStepForm(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self.app.set_header(subtitle="Upraviť objednávku")
        heading(self, "Zmeniť údaje doručenia")
        sub(self, f"Objednávka #{self.app.edit_order_id.get()}")

        c = card(self)
        c.pack(fill="x", pady=4)
        tk.Label(
            c, text="Doručenie", bg=CARD, fg=TEXT, font=("Helvetica", 10, "bold")
        ).pack(anchor="w", padx=14, pady=(10, 0))

        field_label(c, "Adresa doručenia")
        ttk.Entry(c, textvariable=self.app.edit_address_var, width=50).pack(
            fill="x", padx=14, pady=(0, 4)
        )

        time_row = tk.Frame(c, bg=CARD)
        time_row.pack(fill="x", padx=14, pady=(6, 0))
        for label_text, var in [
            ("Dátum doručenia (DD.MM.RRRR)", self.app.edit_from_date_var),
            ("Od (HH:MM)", self.app.edit_from_time_var),
            ("Do (HH:MM)", self.app.edit_to_time_var),
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
            back_cmd=lambda: self.app.show(EditStepOrder),
            next_cmd=self._save,
            next_text="Uložiť zmeny ✓",
        )

    def _save(self):
        try:
            date_str = self.app.edit_from_date_var.get()
            from_dt = datetime.datetime.strptime(
                f"{date_str} {self.app.edit_from_time_var.get()}", "%d.%m.%Y %H:%M"
            )
            to_dt = datetime.datetime.strptime(
                f"{date_str} {self.app.edit_to_time_var.get()}", "%d.%m.%Y %H:%M"
            )
        except ValueError:
            messagebox.showerror(
                "Chyba", "Neplatný formát dátumu/času.\nPoužite DD.MM.RRRR a HH:MM."
            )
            return

        try:
            EditCustomerOrderHandler().handler(
                customer_id=self.app.edit_customer_id.get(),
                order_id=self.app.edit_order_id.get(),
                address=self.app.edit_address_var.get().strip() or None,
                from_datetime=from_dt,
                to_datetime=to_dt,
            )
        except ValueError as e:
            messagebox.showerror("Chyba", str(e))
            return

        try:
            order = GetCustomerOrderHandler().handler(
                customer_id=self.app.edit_customer_id.get(),
                order_id=self.app.edit_order_id.get(),
            )
            self.app.last_edited_order = order
        except ValueError:
            pass
        self.app.show(EditStepConfirm)


# ══════════════════════════════════════════════════════════════════════════════
# EDIT ORDER – Step 4: potvrdit zmeny
# ══════════════════════════════════════════════════════════════════════════════


class EditStepConfirm(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self.app.set_header(subtitle="Potvrdenie zmeny")

        order = getattr(self.app, "last_edited_order", None)
        if not order:
            return

        tk.Label(self, text="✅", bg=BG, font=("Helvetica", 36)).pack(pady=(16, 4))
        tk.Label(
            self,
            text="Objednávka bola úspešne upravená!",
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
            self, text="⬅  Späť na hlavnú", style="Green.TButton", command=self._back
        ).pack(pady=16)

    def _back(self):
        from ui.app import RoleSelect

        self.app.show(RoleSelect)
