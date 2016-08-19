# -*- coding:utf-8 -*-
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QDialog, QComboBox, QLabel, QLineEdit, QGridLayout, QHBoxLayout, QMessageBox, QApplication, \
    QDialogButtonBox, QVBoxLayout, QPushButton
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery

def createConnection():
    """开启数据库并检测"""
    db = QSqlDatabase.addDatabase('QSQLITE')
    db.setHostName('127.0.0.1')
    db.setDatabaseName('universitydb')
    # db.setUserName('dbuser')
    if not db.open():
        QMessageBox.critical(None, "错误", "数据库开启错误", QMessageBox.Ok, 0)
        return False
    return True


class SignIn(QDialog):
    def __init__(self, main):
        QDialog.__init__(self)
        self.main = main
        self.label_name = QLabel("用户名: ")
        self.line_name = QLineEdit()

        self.label_password = QLabel("密码: ")
        self.line_password = QLineEdit()

        layout = QGridLayout()
        layout.addWidget(self.label_name, 0, 0, 1, 1)
        layout.addWidget(self.line_name, 0, 1, 1, 1)
        layout.addWidget(self.label_password, 1, 0, 1, 1)
        layout.addWidget(self.line_password, 1, 1, 1, 1)

        hl = QVBoxLayout()

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.judgment)
        buttonBox.rejected.connect(self.close)

        hl.addLayout(layout)
        hl.addWidget(buttonBox)
        self.setLayout(hl)

    def judgment(self):
        if self.main.isAdministrator(self.line_name.text(), self.line_password.text()):
            self.close()
            self.main.show()
        else:
            QMessageBox.critical(None, "错误", "用户名或密码错误", QMessageBox.Ok, 0)


class AddClassDialog(QDialog):
    """添加教室信息"""

    def __init__(self):
        QDialog.__init__(self)
        self.readSql()

        label_build = QLabel("所处教学楼：")
        self.combo = QComboBox()
        for bl in self.build: self.combo.addItem(bl)

        label_number = QLabel("门牌号:")
        self.line_num = QLineEdit()

        label_ip = QLabel("教室ip:")
        self.line_ip = [QLineEdit() for i in range(4)]
        validator = QIntValidator(0, 255)
        for i in range(4): self.line_ip[i].setValidator(validator)

        layout_h = QHBoxLayout()
        layout_h.addWidget(label_ip)
        for l_ip in self.line_ip:
            l_ip.setFixedSize(50, 30)
            layout_h.addWidget(l_ip)

        layout = QGridLayout()
        layout.addWidget(label_build, 0, 0)
        layout.addWidget(self.combo, 0, 1)
        layout.addWidget(label_number, 1, 0)
        layout.addWidget(self.line_num, 1, 1)
        layout.addLayout(layout_h, 2, 0, 1, 2)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.inSql)
        buttonBox.rejected.connect(self.close)

        hl = QVBoxLayout()
        hl.addLayout(layout)
        hl.addWidget(buttonBox)

        self.setLayout(hl)

    def readSql(self):
        model = QSqlTableModel()
        model.setTable("deparment")
        model.select()

        self.build = set([model.record(i).value("building")
                          for i in range(model.rowCount())])

        self.build = list(self.build)
        self.build.sort()


    def inSql(self):
        model = QSqlTableModel()
        model.setTable("classroom")
        model.insertRows(0, 1)
        model.setData(model.index(0, 0), self.combo.currentText())
        model.setData(model.index(0, 1), self.line_num.text())
        ip = '.'.join([l_ip.text() for l_ip in self.line_ip])
        model.setData(model.index(0, 2), ip)
        if not model.submitAll():
            QMessageBox.critical(None, "错误", "添加信息出错", QMessageBox.Ok, 0)
        else:
            QMessageBox.about(None, "确认", "添加成功")
        self.line_num.setText("")
        for i in range(4): self.line_ip[i].setText("")


class AddCourseDialog(QDialog):
    """添加课程信息"""
    def __init__(self):
        QDialog.__init__(self)
        label_id = QLabel("课程号:")
        self.line_id = QLineEdit()

        label_title = QLabel("课程名:")
        self.line_title = QLineEdit()

        query = QSqlQuery()
        query.exec_("SELECT dept_name FROM deparment")
        dept_name = set()
        while query.next(): dept_name.add(query.value(0))
        dept_name = list(dept_name)
        dept_name.sort()

        label_dept = QLabel("开课系:")
        self.combo = QComboBox()
        self.combo.addItems(dept_name)

        layout = QGridLayout()
        layout.addWidget(label_id, 0, 0)
        layout.addWidget(self.line_id, 0, 1)
        layout.addWidget(label_title, 1, 0)
        layout.addWidget(self.line_title, 1, 1)
        layout.addWidget(label_dept, 2, 0)
        layout.addWidget(self.combo, 2, 1)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.inSql)
        buttonBox.rejected.connect(self.close)

        hl = QVBoxLayout()
        hl.addLayout(layout)
        hl.addWidget(buttonBox)

        self.setLayout(hl)

    def inSql(self):
        model = QSqlTableModel()
        model.setTable("course")
        model.insertRows(0, 1)
        model.setData(model.index(0, 0), self.line_id.text())
        model.setData(model.index(0, 1), self.line_title.text())
        model.setData(model.index(0, 2), self.combo.currentText())

        if not model.submitAll():
            QMessageBox.critical(None, "错误", "添加失败请仔细检测", QMessageBox.Ok, 0)
        else:
            QMessageBox.about(None, "添加成功", "添加成功请继续添加或退出")
            self.line_id.setText("")
            self.line_title.setText("")

class CourseSetDialog(QDialog):
    def __init__(self, ip, year, semester, time_slot_id):
        QDialog.__init__(self)
        self.query = QSqlQuery()
        self.query.exec_("SELECT course_id, sec_id "
                         "FROM section "
                         "WHERE year = %d AND "
                         "semester = '%s' AND "
                         "time_slot_id = '%s' AND "
                         "ip = '%s'"
                         % (year, semester, time_slot_id, ip))

        if self.query.next():
            course_id = self.query.value(0)
            self.sec_id = self.query.value(1)
            self.query.prepare("UPDATE section "
                               "SET course_id = ?, sec_id = ?"
                               "WHERE course_id = '%s' AND sec_id = '%s'"
                               % (course_id, self.sec_id))

            query_s = QSqlQuery()
            query_s.exec_("SELECT title FROM course WHERE course_id = '%s'" % course_id)
            if query_s.next(): self.course_title = query_s.value(0)
        else:
            self.course_title = ""
            self.sec_id = ""
            self.query.prepare("INSERT INTO section "
                               "VALUES (?, ?, '%s', %d, '%s', '%s')"
                               % (semester, year, ip, time_slot_id))
            print(semester, year, ip, time_slot_id)

        lable_id = QLabel("课程名:")
        self.line_id = QComboBox()
        self.init_id()
        self.line_id.setCurrentText(self.course_title)

        lable_secid = QLabel("课序号:")
        self.line_secid = QLineEdit()
        self.line_secid.setText(self.sec_id)

        layout = QGridLayout()
        layout.addWidget(lable_id, 0, 0)
        layout.addWidget(self.line_id, 0, 1)
        layout.addWidget(lable_secid, 1, 0)
        layout.addWidget(self.line_secid, 1, 1)

        add = QPushButton("添加课程")
        add.clicked.connect(self.show_add)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.inSql)
        buttonBox.rejected.connect(self.close)

        hl = QHBoxLayout()
        hl.addWidget(add)
        hl.addStretch()
        hl.addWidget(buttonBox)

        vl = QVBoxLayout()
        vl.addLayout(layout)
        vl.addLayout(hl)

        self.setLayout(vl)

    def init_id(self):
        id = []
        query_s = QSqlQuery()
        query_s.exec_("SELECT title FROM course")
        while query_s.next(): id.append(query_s.value(0))

        self.line_id.clear()
        self.line_id.addItems(id)

    def inSql(self):
        query = QSqlQuery()
        query.exec_("SELECT course_id FROM course WHERE title = '%s'" % self.line_id.currentText())
        query.next(); id = query.value(0)
        print(id)
        self.query.addBindValue(id)
        self.query.addBindValue(self.line_secid.text())
        if self.query.exec_():
            QMessageBox.about(None, "设置成功", "设置成功，请继续设置或退出")
        else:
            QMessageBox.critical(None, "错误", "设置失败请仔细检测", QMessageBox.Ok, 0)

    def show_add(self):
        add = AddCourseDialog()
        if add.exec_() == 0:
            self.init_id()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    if createConnection():
        qb = AddClassDialog()
        qb.show()
    else:
        sys.exit()

    sys.exit(app.exec_())
