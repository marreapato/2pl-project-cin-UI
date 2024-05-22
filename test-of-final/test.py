import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time
from collections import defaultdict
from queue import Queue, Empty

# Create a queue for message handling
message_queue = Queue()

# Transaction class
class Transaction:
    def __init__(self, tid, start_time):
        self.tid = tid
        self.start_time = start_time
        self.locks_held = set()

# LockManager class
class LockManager:
    def __init__(self, protocol):
        self.locks = defaultdict(list)
        self.wait_queue = defaultdict(Queue)
        self.lock_table = defaultdict(lambda: None)
        self.transactions = {}
        self.protocol = protocol

    def add_transaction(self, trans):
        self.transactions[trans.tid] = trans

    def request_lock(self, trans, item, lock_type):
        current_lock = self.lock_table[item]

        if current_lock is None:
            self.grant_lock(trans, item, lock_type)
        elif current_lock == 'R' and lock_type == 'R':
            self.grant_lock(trans, item, lock_type)
        else:
            if self.protocol == "wait-die":
                if self.handle_wait_die(trans, item):
                    message_queue.put(f"Transaction {trans.tid} waits for {lock_type} lock on {item}")
                    self.wait_queue[item].put((trans, lock_type))
                else:
                    message_queue.put(f"Transaction {trans.tid} aborted (Wait-Die rule)")
                    self.abort_transaction(trans)
            elif self.protocol == "wound-wait":
                if self.handle_wound_wait(trans, item):
                    message_queue.put(f"Transaction {trans.tid} waits for {lock_type} lock on {item}")
                    self.wait_queue[item].put((trans, lock_type))
                else:
                    message_queue.put(f"Transaction {trans.tid} aborted (Wound-Wait rule)")
                    self.abort_transaction(trans)

    def grant_lock(self, trans, item, lock_type):
        self.locks[item].append(trans.tid)
        self.lock_table[item] = lock_type
        trans.locks_held.add(item)
        lock_type_desc = "shared (read)" if lock_type == 'R' else "exclusive (write)"
        message_queue.put(f"Transaction {trans.tid} granted {lock_type_desc} lock on {item}")

    def release_lock(self, trans, item):
        if trans.tid in self.locks[item]:
            self.locks[item].remove(trans.tid)
            if not self.locks[item]:
                self.lock_table[item] = None
                self.promote_locks(item)
            trans.locks_held.remove(item)
            message_queue.put(f"Transaction {trans.tid} released lock on {item}")

    def promote_locks(self, item):
        if not self.wait_queue[item].empty():
            next_trans, lock_type = self.wait_queue[item].get()
            self.grant_lock(next_trans, item, lock_type)

    def handle_wait_die(self, trans, item):
        if self.lock_table[item] == 'W':
            holding_trans_tid = self.locks[item][0]
        else:
            holding_trans_tid = min(self.locks[item], key=lambda tid: self.transactions[tid].start_time)

        holding_trans = self.transactions[holding_trans_tid]

        if trans.start_time < holding_trans.start_time:
            return True  # Older transaction waits
        else:
            return False  # Younger transaction dies

    def handle_wound_wait(self, trans, item):
        if self.lock_table[item] == 'W':
            holding_trans_tid = self.locks[item][0]
        else:
            holding_trans_tid = min(self.locks[item], key=lambda tid: self.transactions[tid].start_time)

        holding_trans = self.transactions[holding_trans_tid]

        if trans.start_time < holding_trans.start_time:
            self.abort_transaction(holding_trans)  # Older transaction wounds younger
            return True
        else:
            return False  # Younger transaction waits

    def abort_transaction(self, trans):
        for item in list(trans.locks_held):
            self.release_lock(trans, item)
        message_queue.put(f"Transaction {trans.tid} aborted")

def read_item(trans, item, lock_manager):
    lock_manager.request_lock(trans, item, 'R')
    time.sleep(0.1)
    message_queue.put(f"Transaction {trans.tid} reads {item}")
    lock_manager.release_lock(trans, item)

def write_item(trans, item, lock_manager):
    lock_manager.request_lock(trans, item, 'W')
    time.sleep(0.1)
    message_queue.put(f"Transaction {trans.tid} writes to {item}")
    lock_manager.release_lock(trans, item)

def transaction_workflow(trans, operations, lock_manager):
    try:
        for op, item in operations:
            if op == 'R':
                read_item(trans, item, lock_manager)
            elif op == 'W':
                write_item(trans, item, lock_manager)
    except Exception as e:
        message_queue.put(f"Exception in transaction {trans.tid}: {e}")

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Concurrency Control Protocols")
        
        self.protocol_var = tk.StringVar(value="wait-die")
        self.lock_manager = None
        self.transactions = []
        self.next_tid = 1
        self.current_operations = []

        self.create_widgets()
        self.update_message_display()

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

        self.wait_die_radio = tk.Radiobutton(right_frame, text="Wait-Die", variable=self.protocol_var, value="wait-die", command=self.update_protocol)
        self.wait_die_radio.grid(row=0, column=1, sticky=tk.W)

        self.wound_wait_radio = tk.Radiobutton(right_frame, text="Wound-Wait", variable=self.protocol_var, value="wound-wait", command=self.update_protocol)
        self.wound_wait_radio.grid(row=0, column=2, sticky=tk.W)

        self.add_trans_button = tk.Button(right_frame, text="Add Transaction", command=self.add_transaction)
        self.add_trans_button.grid(row=1, column=0, pady=5)

        self.execute_button = tk.Button(right_frame, text="Execute Transactions", command=self.execute_transactions)
        self.execute_button.grid(row=1, column=1, pady=5)

        self.clear_scaling_button = tk.Button(right_frame, text="Clear Scaling", command=self.clear_scaling)
        self.clear_scaling_button.grid(row=1, column=2, pady=5)

        self.clear_protocol_button = tk.Button(right_frame, text="Clear Protocol Messages", command=self.clear_protocol_messages)
        self.clear_protocol_button.grid(row=1, column=3, pady=5)

        self.transaction_frame = tk.Frame(right_frame)
        self.transaction_frame.grid(row=2, column=0, columnspan=4, pady=10)

        self.operation_label = tk.Label(self.transaction_frame, text="Select Operation:")
        self.operation_label.grid(row=0, column=0, padx=5, pady=5)

        self.operation_combo = ttk.Combobox(self.transaction_frame, values=["R", "W"])
        self.operation_combo.grid(row=0, column=1, padx=5, pady=5)

        self.item_label = tk.Label(self.transaction_frame, text="Item (x, y, or z):")
        self.item_label.grid(row=0, column=2, padx=5, pady=5)

        self.item_entry = tk.Entry(self.transaction_frame)
        self.item_entry.grid(row=0, column=3, padx=5, pady=5)

        self.add_op_button = tk.Button(self.transaction_frame, text="Add Operation", command=self.add_operation)
        self.add_op_button.grid(row=0, column=4, padx=5, pady=5)

        self.scaling_display = tk.Text(right_frame, height=10, width=80)
        self.scaling_display.grid(row=3, column=0, columnspan=4, pady=10)

        self.protocol_display = tk.Text(right_frame, height=10, width=80, state=tk.DISABLED)
        self.protocol_display.grid(row=4, column=0, columnspan=4, pady=10)

        self.log_disk_display = tk.Text(right_frame, height=10, width=80, state=tk.DISABLED)
        self.log_disk_display.grid(row=5, column=0, columnspan=4, pady=10)

    def update_protocol(self):
        self.lock_manager = LockManager(self.protocol_var.get())

    def display_scaling(self, message):
        self.scaling_display.insert(tk.END, message + "\n")
        self.scaling_display.see(tk.END)

    def display_message(self, message):
        self.protocol_display.config(state=tk.NORMAL)
        self.protocol_display.insert(tk.END, message + "\n")
        self.protocol_display.config(state=tk.DISABLED)
        self.protocol_display.see(tk.END)

    def display_log_disk(self, message):
        self.log_disk_display.config(state=tk.NORMAL)
        self.log_disk_display.insert(tk.END, message + "\n")
        self.log_disk_display.config(state=tk.DISABLED)
        self.log_disk_display.see(tk.END)

    def add_operation(self):
        operation = self.operation_combo.get().strip().upper()
        item = self.item_entry.get().strip().lower()

        valid_items = {'x', 'y', 'z'}

        if operation not in {"R", "W"}:
            messagebox.showwarning("Input Error", "Please select a valid operation (R or W)")
            return

        if item not in valid_items:
            messagebox.showwarning("Input Error", "Item must be x, y, or z")
            return

        if len(self.current_operations) >= 2:
            messagebox.showwarning("Input Error", "You can only add up to 2 operations")
            return

        self.current_operations.append((operation, item))
        self.item_entry.delete(0, tk.END)
        self.operation_combo.set("")
        self.operations_display.insert(tk.END, f"{operation}({item})\n")
        self.operations_display.see(tk.END)

    def add_transaction(self):
        tid = self.next_tid
        start_time = self.next_tid
        operations = self.current_operations[:]

        if not operations:
            messagebox.showwarning("Input Error", "Please add at least one operation")
            return

        trans = Transaction(tid, start_time)
        self.transactions.append((trans, operations))

        if self.lock_manager is None:
            self.lock_manager = LockManager(self.protocol_var.get())

        self.lock_manager.add_transaction(trans)

        self.next_tid += 1
        self.current_operations.clear()
        self.operations_display.delete(1.0, tk.END)

        operation_str = ', '.join([f"{op}({item})" for op, item in operations])
        self.display_scaling(f"Added Transaction {tid} with operations: {operation_str}, Start Time: {start_time}")

    def execute_transactions(self):
        if not self.transactions:
            messagebox.showwarning("Execution Error", "No transactions to execute")
            return

        def run_transactions():
            threads = []
            for trans, operations in sorted(self.transactions, key=lambda t: t[0].start_time):
                t = threading.Thread(target=transaction_workflow, args=(trans, operations, self.lock_manager))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            execution_order = ", ".join([str(trans.tid) for trans, _ in self.transactions])
            self.display_scaling(f"Transactions executed in order: {execution_order}")

            self.display_log_disk("---------------")
            for trans, operations in self.transactions:
                operation_str = ', '.join([f"{op}({item})" for op, item in operations])
                self.display_log_disk(f"Transaction {trans.tid} with operations: {operation_str}")
            self.display_log_disk("--commit--")

            self.transactions.clear()
            self.lock_manager = LockManager(self.protocol_var.get())
            self.next_tid = 1

        execution_thread = threading.Thread(target=run_transactions)
        execution_thread.start()

    def clear_scaling(self):
        self.scaling_display.delete(1.0, tk.END)

    def clear_protocol_messages(self):
        self.protocol_display.config(state=tk.NORMAL)
        self.protocol_display.delete(1.0, tk.END)
        self.protocol_display.config(state=tk.DISABLED)

    def update_message_display(self):
        try:
            while True:
                message = message_queue.get_nowait()
                self.display_message(message)
        except Empty:
            pass
        self.root.after(100, self.update_message_display)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
