import tkinter as tk
from tkinter import messagebox, ttk

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Concurrency Control Protocols")
        
        self.protocol_var = tk.StringVar(value="wait-die")
        self.transactions = []
        self.next_tid = 1
        self.current_operations = []

        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=10, pady=10)

        left_frame = tk.Frame(main_frame)
        left_frame.grid(row=0, column=0, padx=10, pady=10)

        operations_label = tk.Label(left_frame, text="Operations:")
        operations_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.operations_display = tk.Text(left_frame, height=25, width=50)
        self.operations_display.grid(row=1, column=0, padx=5, pady=5)

        right_frame = tk.Frame(main_frame)
        right_frame.grid(row=0, column=1, padx=10, pady=10)

        protocol_label = tk.Label(right_frame, text="Select Protocol:")
        protocol_label.grid(row=0, column=0, sticky=tk.W)

        self.wait_die_radio = tk.Radiobutton(right_frame, text="Wait-Die", variable=self.protocol_var, value="wait-die")
        self.wait_die_radio.grid(row=0, column=1, sticky=tk.W)

        self.wound_wait_radio = tk.Radiobutton(right_frame, text="Wound-Wait", variable=self.protocol_var, value="wound-wait")
        self.wound_wait_radio.grid(row=0, column=2, sticky=tk.W)

        self.add_trans_button = tk.Button(right_frame, text="Add Transaction")
        self.add_trans_button.grid(row=1, column=0, pady=5)

        self.execute_button = tk.Button(right_frame, text="Execute Transactions")
        self.execute_button.grid(row=1, column=1, pady=5)

        self.clear_scaling_button = tk.Button(right_frame, text="Clear Scaling")
        self.clear_scaling_button.grid(row=1, column=2, pady=5)

        self.clear_protocol_button = tk.Button(right_frame, text="Clear Protocol Messages")
        self.clear_protocol_button.grid(row=1, column=3, pady=5)

        self.clear_operations_button = tk.Button(right_frame, text="Clear Operations")
        self.clear_operations_button.grid(row=1, column=4, pady=5)

        self.transaction_frame = tk.Frame(right_frame)
        self.transaction_frame.grid(row=2, column=0, columnspan=5, pady=10)

        self.operation_label = tk.Label(self.transaction_frame, text="Select Operation:")
        self.operation_label.grid(row=0, column=0, padx=5, pady=5)

        self.operation_combo = ttk.Combobox(self.transaction_frame, values=["R", "W"])
        self.operation_combo.grid(row=0, column=1, padx=5, pady=5)

        self.item_label = tk.Label(self.transaction_frame, text="Item (x, y, or z):")
        self.item_label.grid(row=0, column=2, padx=5, pady=5)

        self.item_entry = tk.Entry(self.transaction_frame)
        self.item_entry.grid(row=0, column=3, padx=5, pady=5)

        self.add_op_button = tk.Button(self.transaction_frame, text="Add Operation")
        self.add_op_button.grid(row=0, column=4, padx=5, pady=5)

        # Titles for the displays
        scaling_label = tk.Label(right_frame, text="Log Memory/Scaling:")
        scaling_label.grid(row=3, column=0, columnspan=5, pady=(10, 0))

        self.scaling_display = tk.Text(right_frame, height=10, width=80)
        self.scaling_display.grid(row=4, column=0, columnspan=5, pady=10)

        protocol_label = tk.Label(right_frame, text="Protocol Behavior Messages:")
        protocol_label.grid(row=5, column=0, columnspan=5, pady=(10, 0))

        self.protocol_display = tk.Text(right_frame, height=10, width=80, state=tk.DISABLED)
        self.protocol_display.grid(row=6, column=0, columnspan=5, pady=10)

        log_disk_label = tk.Label(right_frame, text="Log Disk:")
        log_disk_label.grid(row=7, column=0, columnspan=5, pady=(10, 0))

        self.log_disk_display = tk.Text(right_frame, height=10, width=80, state=tk.DISABLED)
        self.log_disk_display.grid(row=8, column=0, columnspan=5, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
