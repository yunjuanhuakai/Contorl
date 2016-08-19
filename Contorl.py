# -*- coding:utf-8 -*-
from PyQt5.QtWidgets import QMessageBox, QMainWindow, QDesktopWidget, QApplication, QMenu, QMenuBar
from PyQt5.QtSql import QSqlDatabase
from Dialog import AddClassDialog, SignIn


def createConnection():
    """开启数据库并检测"""
    db = QSqlDatabase.addDatabase('QSQLITE')
    db.setHostName('127.0.0.1')
    db.setDatabaseName('universitydb')
    db.setUserName('dbuser')
    if not db.open():
        QMessageBox.critical(None, "错误", "数据库开启错误", QMessageBox.Ok, 0)
        return False
    return True


class MainFrame(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.createMenu()
        self.center()

    def createMenu(self):
        menuBar = QMenuBar(self)
        self.menu = QMenu("管理")
        self.actions = [self.menu.addAction(action) for action in ["添加", "修改", "删除", "退出"]]
        self.actions[0].triggered.connect(self.addClass)
        self.actions[1].triggered.connect(self.setClass)
        self.actions[2].triggered.connect(self.remClass)
        self.actions[3].triggered.connect(self.close)

        menuBar.addMenu(self.menu)

    def center(self):  # 主窗口居中
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)

    def isAdministrator(self, name, password):
        """判断是否为管理员"""
        if name == '2013131510' and password == '123456':
            return True
        return True

    def addClass(self):
        addDialog = AddClassDialog()
        addDialog.exec_()

    def setClass(self):
        pass

    def remClass(self):
        pass


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    if createConnection():
        qb = SignIn(MainFrame())
        qb.show()
    else:
        sys.exit()

    sys.exit(app.exec_())