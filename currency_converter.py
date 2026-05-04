import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime
import threading

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter - Конвертер валют")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        
        # API ключ (зарегистрируйтесь на exchangerate-api.com для получения бесплатного ключа)
        self.api_key = "1a5462dabd4f06d7e6b17764"  # Замените на свой ключ
        self.base_url = "https://v6.exchangerate-api.com/v6/"
        
        # Файл для сохранения истории
        self.history_file = "conversion_history.json"
        self.history = self.load_history()
        
        # Доступные валюты
        self.currencies = []
        
        # Создание интерфейса
        self.create_widgets()
        
        # Загрузка списка валют
        self.load_currencies()
        
        # Загрузка истории в таблицу
        self.refresh_history_table()
    
    def create_widgets(self):
        # ========== Верхняя панель конвертации ==========
        main_frame = ttk.LabelFrame(self.root, text="Конвертация валют", padding="15")
        main_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Сумма для конвертации
        ttk.Label(main_frame, text="Сумма:", font=("Arial", 11)).grid(row=0, column=0, sticky=tk.W, padx=5, pady=10)
        self.amount_entry = ttk.Entry(main_frame, width=20, font=("Arial", 12))
        self.amount_entry.grid(row=0, column=1, padx=5, pady=10)
        self.amount_entry.bind('<Return>', lambda e: self.convert_currency())
        
        # Валюта ИЗ
        ttk.Label(main_frame, text="Из валюты:", font=("Arial", 11)).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.from_currency = ttk.Combobox(main_frame, width=15, font=("Arial", 11))
        self.from_currency.grid(row=1, column=1, padx=5, pady=5)
        
        # Валюта В
        ttk.Label(main_frame, text="В валюту:", font=("Arial", 11)).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.to_currency = ttk.Combobox(main_frame, width=15, font=("Arial", 11))
        self.to_currency.grid(row=2, column=1, padx=5, pady=5)
        
        # Кнопка конвертации
        self.convert_btn = ttk.Button(main_frame, text="💱 Конвертировать", command=self.convert_currency)
        self.convert_btn.grid(row=0, column=2, rowspan=2, padx=20, pady=5)
        
        # Результат конвертации
        result_frame = ttk.Frame(main_frame)
        result_frame.grid(row=3, column=0, columnspan=3, pady=15, sticky=tk.W+tk.E)
        
        self.result_label = ttk.Label(result_frame, text="", font=("Arial", 14, "bold"), foreground="green")
        self.result_label.pack()
        
        # ========== Панель истории ==========
        history_frame = ttk.LabelFrame(self.root, text="📜 История конвертаций", padding="10")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Кнопки управления историей
        btn_frame = ttk.Frame(history_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="🗑️ Очистить историю", command=self.clear_history).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="💾 Сохранить историю", command=self.save_history_manual).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📂 Загрузить историю", command=self.load_history_from_file).pack(side=tk.LEFT, padx=2)
        
        # Таблица для истории
        table_frame = ttk.Frame(history_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создаем Treeview для таблицы
        columns = ("Дата", "Сумма", "Из валюты", "В валюту", "Результат", "Курс")
        self.history_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        
        # Настройка колонок
        self.history_tree.heading("Дата", text="Дата и время")
        self.history_tree.heading("Сумма", text="Сумма")
        self.history_tree.heading("Из валюты", text="Из валюты")
        self.history_tree.heading("В валюту", text="В валюту")
        self.history_tree.heading("Результат", text="Результат")
        self.history_tree.heading("Курс", text="Курс")
        
        self.history_tree.column("Дата", width=150)
        self.history_tree.column("Сумма", width=100)
        self.history_tree.column("Из валюты", width=80)
        self.history_tree.column("В валюту", width=80)
        self.history_tree.column("Результат", width=120)
        self.history_tree.column("Курс", width=100)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Статус бар
        self.status_label = ttk.Label(self.root, text="✅ Готов к работе", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_currencies(self):
        """Загрузка списка доступных валют из API"""
        try:
            url = f"{self.base_url}{self.api_key}/codes"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("result") == "success":
                    self.currencies = [code for code, name in data.get("supported_codes", [])]
                    self.from_currency['values'] = self.currencies
                    self.to_currency['values'] = self.currencies
                    
                    # Устанавливаем значения по умолчанию
                    if "USD" in self.currencies:
                        self.from_currency.set("USD")
                    if "EUR" in self.currencies:
                        self.to_currency.set("EUR")
                    
                    self.status_label.config(text="✅ Список валют загружен")
                else:
                    messagebox.showerror("Ошибка API", data.get("error-type", "Неизвестная ошибка"))
            else:
                # Если API не работает, используем стандартный список
                self.set_default_currencies()
        except Exception as e:
            self.status_label.config(text=f"⚠️ Ошибка загрузки валют: {str(e)}")
            self.set_default_currencies()
    
    def set_default_currencies(self):
        """Стандартный список валют на случай ошибки API"""
        self.currencies = ["USD", "EUR", "RUB", "GBP", "CNY", "JPY", "CAD", "CHF", "TRY", "KZT"]
        self.from_currency['values'] = self.currencies
        self.to_currency['values'] = self.currencies
        self.from_currency.set("USD")
        self.to_currency.set("EUR")
    
    def convert_currency(self):
        """Конвертация валюты"""
        # ПРОВЕРКА: сумма должна быть положительным числом
        amount_str = self.amount_entry.get().strip()
        
        if not amount_str:
            messagebox.showwarning("Ошибка ввода", "⚠️ Введите сумму для конвертации!")
            self.status_label.config(text="❌ Ошибка: сумма не введена")
            return
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showwarning("Ошибка ввода", "⚠️ Сумма должна быть положительным числом!")
                self.status_label.config(text="❌ Ошибка: сумма должна быть > 0")
                return
        except ValueError:
            messagebox.showwarning("Ошибка ввода", "⚠️ Введите корректное число!")
            self.status_label.config(text="❌ Ошибка: неверный формат числа")
            return
        
        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()
        
        if not from_curr or not to_curr:
            messagebox.showwarning("Ошибка", "⚠️ Выберите валюты для конвертации!")
            return
        
        self.status_label.config(text=f"🔄 Конвертация {amount} {from_curr} → {to_curr}...")
        self.convert_btn.config(state=tk.DISABLED, text="⏳ Конвертация...")
        
        # Запуск в отдельном потоке
        thread = threading.Thread(target=self.fetch_exchange_rate, args=(amount, from_curr, to_curr))
        thread.daemon = True
        thread.start()
    
    def fetch_exchange_rate(self, amount, from_curr, to_curr):
        """Получение курса валют из API"""
        try:
            url = f"{self.base_url}{self.api_key}/pair/{from_curr}/{to_curr}/{amount}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("result") == "success":
                    result = data.get("conversion_result")
                    rate = data.get("conversion_rate")
                    
                    self.root.after(0, self.display_result, amount, from_curr, to_curr, result, rate)
                    self.root.after(0, self.status_label.config, {'text': f"✅ Конвертация выполнена"})
                else:
                    error_msg = data.get("error-type", "Неизвестная ошибка")
                    if "invalid-api-key" in error_msg:
                        self.root.after(0, messagebox.showerror, "Ошибка API", 
                                       "Неверный API ключ! Получите бесплатный ключ на exchangerate-api.com")
                    else:
                        self.root.after(0, messagebox.showerror, "Ошибка API", f"Ошибка: {error_msg}")
                    self.root.after(0, self.status_label.config, {'text': "❌ Ошибка API"})
            else:
                self.root.after(0, messagebox.showerror, "Ошибка", f"HTTP ошибка: {response.status_code}")
                self.root.after(0, self.status_label.config, {'text': "❌ Ошибка соединения"})
                
        except requests.RequestException as e:
            self.root.after(0, messagebox.showerror, "Ошибка сети", f"Не удалось подключиться: {str(e)}")
            self.root.after(0, self.status_label.config, {'text': "❌ Ошибка сети"})
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Ошибка", f"Произошла ошибка: {str(e)}")
            self.root.after(0, self.status_label.config, {'text': f"❌ Ошибка: {str(e)}"})
        finally:
            self.root.after(0, self.convert_btn.config, {'state': tk.NORMAL, 'text': "💱 Конвертировать"})
    
    def display_result(self, amount, from_curr, to_curr, result, rate):
        """Отображение результата конвертации"""
        self.result_label.config(text=f"{amount:.2f} {from_curr} = {result:.2f} {to_curr} (Курс: {rate:.4f})")
        
        # Добавляем в историю
        history_entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "from_currency": from_curr,
            "to_currency": to_curr,
            "result": result,
            "rate": rate
        }
        
        self.history.insert(0, history_entry)  # Новые записи сверху
        
        # Ограничиваем историю 50 записями
        if len(self.history) > 50:
            self.history = self.history[:50]
        
        self.save_history()
        self.refresh_history_table()
    
    def refresh_history_table(self):
        """Обновление таблицы истории"""
        # Очищаем таблицу
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Добавляем записи
        for entry in self.history:
            self.history_tree.insert("", 0, values=(
                entry.get("date", ""),
                f"{entry.get('amount', 0):.2f}",
                entry.get("from_currency", ""),
                entry.get("to_currency", ""),
                f"{entry.get('result', 0):.2f}",
                f"{entry.get('rate', 0):.4f}"
            ))
    
    def clear_history(self):
        """Очистка истории"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить всю историю?"):
            self.history = []
            self.save_history()
            self.refresh_history_table()
            self.status_label.config(text="🗑️ История очищена")
    
    def save_history_manual(self):
        """Ручное сохранение истории"""
        self.save_history()
        messagebox.showinfo("Успех", "История сохранена в файл!")
    
    def load_history_from_file(self):
        """Загрузка истории из файла"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    loaded_history = json.load(f)
                    if isinstance(loaded_history, list):
                        self.history = loaded_history
                        self.refresh_history_table()
                        self.status_label.config(text="📂 История загружена из файла")
                        messagebox.showinfo("Успех", f"Загружено {len(self.history)} записей")
                    else:
                        messagebox.showerror("Ошибка", "Неверный формат файла")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить историю: {str(e)}")
        else:
            messagebox.showwarning("Предупреждение", "Файл с историей не найден")
    
    def save_history(self):
        """Сохранение истории в JSON"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
    
    def load_history(self):
        """Загрузка истории из JSON файла"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []


if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()