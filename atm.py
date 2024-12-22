import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QLineEdit,
                             QMessageBox, QStackedWidget, QInputDialog)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer, pyqtProperty
from PyQt5.QtGui import QColor, QPalette, QFont

class ATM(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tempValue = pyqtProperty(float, lambda self: 0)
        self.initUI()
        self.loadUsers()
        self.current_user = None
        self.current_card = None
        
    def loadUsers(self):
        try:
            with open('users.json', 'r') as file:
                self.users = json.load(file)
        except FileNotFoundError:
            self.users = {
                "1234567890": {
                    "pin": "1234",
                    "balance": 1000.0
                }
            }
            self.saveUsers()
            
    def saveUsers(self):
        with open('users.json', 'w') as file:
            json.dump(self.users, file)

    def initUI(self):
        self.setWindowTitle('Банкомат')
        self.setFixedSize(400, 500)
        
        # Создаем стек виджетов для разных экранов
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Создаем экраны
        self.loginScreen = self.createLoginScreen()
        self.mainScreen = self.createMainScreen()
        
        # Добавляем экраны в стек
        self.stack.addWidget(self.loginScreen)
        self.stack.addWidget(self.mainScreen)
        self.setupStyles()

    def setupStyles(self):
        # Основной стиль приложения
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QWidget {
                color: white;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #3498db;
                border-radius: 5px;
                background-color: #34495e;
                color: white;
                font-size: 14px;
            }
            QPushButton {
                padding: 10px 20px;
                background-color: #3498db;
                border: none;
                border-radius: 5px;
                color: white;
                font-size: 14px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2472a4;
            }
            QLabel {
                font-size: 16px;
                color: white;
            }
        """)
        
        # Установка шрифта для баланса
        balanceFont = QFont()
        balanceFont.setPointSize(18)
        balanceFont.setBold(True)
        self.balanceLabel.setFont(balanceFont)

    def createLoginScreen(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Создаем поля ввода
        self.cardInput = QLineEdit()
        self.cardInput.setPlaceholderText('Введите номер карты')
        self.pinInput = QLineEdit()
        self.pinInput.setPlaceholderText('Введите PIN-код')
        self.pinInput.setEchoMode(QLineEdit.Password)
        
        # Создаем кнопку входа
        loginBtn = QPushButton('Войти')
        loginBtn.clicked.connect(self.login)
        
        # Добавляем виджеты на экран
        layout.addStretch()
        layout.addWidget(QLabel('Добро пожаловать!'))
        layout.addWidget(self.cardInput)
        layout.addWidget(self.pinInput)
        layout.addWidget(loginBtn)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget

    def createMainScreen(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Создаем метку для отображения баланса
        self.balanceLabel = QLabel()
        
        # Создаем поле для ввода суммы
        self.amountInput = QLineEdit()
        self.amountInput.setPlaceholderText('Введите сумму')
        
        # Создаем кнопки операций
        withdrawBtn = QPushButton('Снять')
        depositBtn = QPushButton('Внести')
        changePinBtn = QPushButton('Изменить PIN')
        logoutBtn = QPushButton('Выйти')
        
        # Подключаем обработчики
        withdrawBtn.clicked.connect(self.withdraw)
        depositBtn.clicked.connect(self.deposit)
        changePinBtn.clicked.connect(self.showChangePinDialog)
        logoutBtn.clicked.connect(self.logout)
        
        # Добавляем виджеты на экран
        layout.addWidget(self.balanceLabel)
        layout.addWidget(self.amountInput)
        layout.addWidget(withdrawBtn)
        layout.addWidget(depositBtn)
        layout.addWidget(changePinBtn)
        layout.addWidget(logoutBtn)
        
        widget.setLayout(layout)
        return widget

    def login(self):
        card = self.cardInput.text()
        pin = self.pinInput.text()
        
        if card in self.users and self.users[card]["pin"] == pin:
            self.current_user = self.users[card]
            self.current_card = card
            self.updateBalance()
            
            # Анимация перехода между экранами
            self.stack.setCurrentIndex(1)
            self.cardInput.clear()
            self.pinInput.clear()
            
            # Анимация появления главного экрана
            self.mainScreen.setGraphicsEffect(None)
            self.fadeInAnimation(self.mainScreen)
        else:
            QMessageBox.warning(self, 'Ошибка', 'Неверный номер карты или PIN-код')

    def updateBalance(self):
        self.balanceLabel.setText(f'Баланс: {self.current_user["balance"]:.2f} руб.')

    def withdraw(self):
        try:
            amount = float(self.amountInput.text())
            if amount <= 0:
                raise ValueError
            
            if amount <= self.current_user["balance"]:
                # Создаем анимацию для баланса
                oldBalance = self.current_user["balance"]
                newBalance = oldBalance - amount
                
                # Анимация уменьшения баланса
                self.animateBalance(oldBalance, newBalance)
                
                self.current_user["balance"] = newBalance
                self.saveUsers()
                self.amountInput.clear()
                
                # Анимация кнопки
                self.animateButton(self.sender())
                
                QMessageBox.information(self, 'Успешно', f'Снято {amount:.2f} руб.')
            else:
                QMessageBox.warning(self, 'Ошибка', 'Недостаточно средств')
        except ValueError:
            QMessageBox.warning(self, 'Ошибка', 'Введите корректную сумму')

    def deposit(self):
        try:
            amount = float(self.amountInput.text())
            if amount <= 0:
                raise ValueError
                
            oldBalance = self.current_user["balance"]
            newBalance = oldBalance + amount
            
            # Анимация увеличения баланса
            self.animateBalance(oldBalance, newBalance)
            
            self.current_user["balance"] = newBalance
            self.saveUsers()
            self.amountInput.clear()
            
            # Анимация кнопки
            self.animateButton(self.sender())
            
            QMessageBox.information(self, 'Успешно', f'Внесено {amount:.2f} руб.')
        except ValueError:
            QMessageBox.warning(self, 'Ошибка', 'Введите корректную сумму')

    def showChangePinDialog(self):
        newPin, ok = QInputDialog.getText(self, 'Изменение PIN-кода', 
                                        'Введите новый PIN-код:', 
                                        QLineEdit.Password)
        if ok and newPin:
            self.current_user["pin"] = newPin
            self.saveUsers()
            QMessageBox.information(self, 'Успешно', 'PIN-код изменен')

    def logout(self):
        self.current_user = None
        self.current_card = None
        self.stack.setCurrentIndex(0)
        self.amountInput.clear()

    def animateBalance(self, oldValue, newValue):
        self.animation = QPropertyAnimation(self, b"tempValue")
        self.animation.setStartValue(oldValue)
        self.animation.setEndValue(newValue)
        self.animation.setDuration(1000)  # 1 секунда
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        def updateBalance(value):
            self.balanceLabel.setText(f'Баланс: {value:.2f} руб.')
        
        self.animation.valueChanged.connect(updateBalance)
        self.animation.start()

    def animateButton(self, button):
        # Анимация нажатия кнопки
        originalColor = button.styleSheet()
        button.setStyleSheet("background-color: #27ae60;")  # Зеленый цвет при успешной операции
        QTimer.singleShot(200, lambda: button.setStyleSheet(originalColor))

    def fadeInAnimation(self, widget):
        self.fadeAnimation = QPropertyAnimation(widget, b"windowOpacity")
        self.fadeAnimation.setStartValue(0.0)
        self.fadeAnimation.setEndValue(1.0)
        self.fadeAnimation.setDuration(500)
        self.fadeAnimation.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    atm = ATM()
    atm.show()
    sys.exit(app.exec_()) 