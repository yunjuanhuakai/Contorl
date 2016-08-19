import threading
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QTime, QDateTime, pyqtSignal, QModelIndex
from PyQt5.QtGui import QPainter, QBrush, QCursor
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtWidgets import QLabel, QApplication, QWidget, QPushButton, QGridLayout, QTableView, QAbstractItemView, \
    QHeaderView, QHBoxLayout, QToolTip, QDialog
from Dialog import CourseSetDialog, createConnection
from ThreadedBeatServer import Heartbeats, Receiver

class CourseModel(QAbstractTableModel):
    def __init__(self):
        QAbstractTableModel.__init__(self)
        self.id_dict = {}
        self._time()

    def rowCount(self, QModelIndex_parent=None, *args, **kwargs):
        return len(self.section)

    def columnCount(self, QModelIndex_parent=None, *args, **kwargs):
        return len(self.time_h)

    def data(self, index, int_role=None):
        if not index.isValid():
            return QVariant()
        if int_role == Qt.TextAlignmentRole:
            return int(Qt.AlignRight | Qt.AlignVCenter)
        elif int_role == Qt.DisplayRole:
            if index.row() == 5 or index.row() == 2:
                return ""
            day = ['M', 'T', 'W', 'R', 'F', 'S', 'U']

            if index.row() > 4:
                index_r = index.row() - 1
            elif index.row() > 1:
                index_r = index.row()
            else:
                index_r = index.row() + 1
            time_slot_id = ''.join((day[index.column()], str(index_r)))
            query = QSqlQuery()
            query.exec_("SELECT course_id, sec_id "
                        "FROM section "
                        "WHERE year = '%s' AND "
                        "semester = '%s' AND "
                        "time_slot_id = '%s' AND "
                        "ip = '%s'"
                        % (self.year, self.semester, time_slot_id, self.ip))
            if query.next():
                self.course_id = query.value(0)
                self.sec_id = query.value(1)
                self.id_dict[self.course_id] = self.sec_id
                query.exec_("SELECT title FROM course WHERE course_id = '%s'" % self.course_id)
                query.next()
                title = query.value(0)
                num = int(len(title) / 5 + 1)
                title = [title[i * 5: (i + 1) * 5] for i in range(num)]

                return '\n'.join(title)
            else:
                return ""

        return QVariant()

    def headerData(self, p_int, Qt_Orientation, int_role=None):
        if int_role != Qt.DisplayRole:
            return QVariant()
        if Qt_Orientation == Qt.Vertical:
            if self.section[p_int] != '午休' and self.section[p_int] != '晚饭':
                if p_int > 4:
                    time = self.time_v[p_int - 2]
                elif p_int > 1:
                    time = self.time_v[p_int - 1]
                else:
                    time = self.time_v[p_int]
                return '\n\n'.join((self.section[p_int], time))
            else:
                return self.section[p_int]
        else:
            return self.time_h[p_int]

    def setYear(self, year):
        self.year = year

    def setSemester(self, semester):
        self.semester = semester

    def setIP(self, ip):
        self.ip = ip

    def _time(self):
        query = QSqlQuery()
        query.exec_("SELECT start_time, end_time FROM time_slot")
        self.time_h = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
        time_set = set()
        while query.next():
            start_time = query.value(0).toString()
            end_time = query.value(1).toString()
            time_set.add('\n    至\n'.join((start_time, end_time)))
        self.time_v = list(time_set)
        self.time_v.sort()
        self.section = ['第一节', '第二节', '午休', '第三节', '第四节', '晚饭', '第五节', '第六节']


class MyTabelView(QTableView):
    rightClicked = pyqtSignal(QModelIndex)

    def mousePressEvent(self, event):
        QTableView.mousePressEvent(self, event)
        if event.buttons() == Qt.RightButton:
            self.rightClicked.emit(self.currentIndex())


class TableShow(QDialog):
    def __init__(self, ip, date=None):
        QDialog.__init__(self)
        self.setFixedSize(500, 500)
        self.model = CourseModel()
        time = QDateTime.currentDateTime()
        if not date:
            self.year = time.date().year()
            self.model.setYear(self.year)
            self.semester = "Spring" if time.date().month() < 7 else "Fall"
            self.model.setSemester(self.semester)
        else:
            self.model.setYear(date[0])
            self.model.setSemester(date[1])
        self.model.setIP(ip)
        # model.setQuery("SELECT name, dept_name FROM instructor")
        self.ip = ip

        self._init_view()

        layout = QHBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

    def showToolTip(self, index):
        if index.row() == 5 or index.row() == 2:
            return
        if self.model.data(index, Qt.DisplayRole) == "":
            QToolTip.showText(QCursor.pos(), "双击添加课程信息")
            return
        query = QSqlQuery()
        query.exec_("SELECT dept_name FROM course WHERE course_id = '%s'" % self.model.course_id)
        query.next()
        QToolTip.showText(QCursor.pos(), "<html>"
                                         "<p>开课系：</p>"
                                         "<b>%s</b>"
                                         "</html>" % query.value(0))

    def addCourse(self, index):
        day = ['M', 'T', 'W', 'R', 'F', 'S', 'U']

        if index.row() > 4:
            index_r = index.row() - 1
        elif index.row() > 1:
            index_r = index.row()
        else:
            index_r = index.row() + 1

        time_slot_id = ''.join((day[index.column()], str(index_r)))
        courseSet = CourseSetDialog(self.ip, self.year, self.semester, time_slot_id)
        if courseSet.exec_() == 0:
            self.model.resetInternalData()

    def setBuilding(self, building):
        self.building = building

    def setRoomNumber(self, room_number):
        self.room_number = room_number

    def _init_view(self):
        self.view = MyTabelView()
        font = self.view.horizontalHeader().font()
        font.setBold(True)
        self.view.setFont(font)
        self.view.setModel(self.model)
        self.view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.view.resizeColumnsToContents()
        self.view.resizeRowsToContents()
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.view.setMouseTracking(True)

        header = self.view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        for i in range(7): header.resizeSection(i, 150)
        # header.setFixedHeight(50)
        header.setDefaultSectionSize(50)
        # header.setStretchLastSection(True)

        self.view.rightClicked.connect(lambda index: print(index.row(), index.column()))
        self.view.clicked.connect(self.showToolTip)
        self.view.doubleClicked.connect(self.addCourse)

class EllipseButton(QPushButton):
    def __init__(self):
        QWidget.__init__(self)
        self.setFixedSize(20, 20)
        self.open = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        if not self.open:
            painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))
        else:
            painter.setBrush(QBrush(Qt.green, Qt.SolidPattern))
        painter.drawEllipse(10, 10, 10, 10)

    def setOpen(self):
        if self.open == True:
            self.closeC()
        else:
            self.openC()

    def openC(self):
        self.open = True
        self.repaint()

    def closeC(self):
        self.open = False
        self.repaint()

class ClassControl(QWidget):
    doubleClicked = pyqtSignal()
    def __init__(self, ip, data):
        QWidget.__init__(self)
        self.ip = ip
        self.data = data
        self._init_time()
        query = QSqlQuery()
        query.exec_("SELECT course_id, sec_id "
                    "FROM section "
                    "WHERE year = '%s' AND "
                    "semester = '%s' AND "
                    "ip = '%s' AND "
                    "time_slot_id = '%s'"
                    % (self.year, self.semester, self.ip, self.time_slot_id))

        if query.next():
            query.exec_("SELECT title FROM course WHERE course_id = '%s'" % query.value(0))
            query.next()
            self.title = query.value(0)
        else:
            self.title = "无课程信息"

        self.setFixedSize(200, 200)
        query.exec_("SELECT building, room_number FROM classroom WHERE ip = '%s'" % self.ip)
        query.next()
        label = QLabel("<html>"
                       "<p align='center'>%s - %s</p>"
                       "<b align='center'>%s</b>"
                       "</html>" % (query.value(0), query.value(1), self.title))

        self.button = [EllipseButton() for i in range(4)]
        self.setOpen(data)
        [bt.clicked.connect(bt.setOpen) for bt in self.button]
        self.doubleClicked.connect(self.showTabel)

        layout = QGridLayout()
        layout.addWidget(label, 0, 0, 1, 3)
        layout.addWidget(QLabel("笔记本"), 1, 0)
        layout.addWidget(self.button[0], 2, 0)
        layout.addWidget(QLabel("台式机"), 1, 1)
        layout.addWidget(self.button[1], 2, 1)
        layout.addWidget(QLabel("投影仪"), 1, 2)
        layout.addWidget(self.button[2], 2, 2)
        layout.addWidget(QLabel("幕布"), 3, 0)
        layout.addWidget(self.button[3], 4, 0)

        self.setLayout(layout)

    def setOpen(self, data):
        for i in range(len(data)):
            if data[i] == 0:
                self.button[i].closeC()
            else:
                self.button[i].openC()

    def getOpen(self):
        return bytearray([bt.open for bt in self.button])

    def showTabel(self):
        tabel = TableShow(self.ip)
        tabel.exec_()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.fillRect(0, 0, 200, 200, Qt.yellow)

    def mouseDoubleClickEvent(self, event):
        QWidget.mouseDoubleClickEvent(self, event)
        self.doubleClicked.emit()

    def _init_time(self):
        timeList = [QTime(8, 0), QTime(10, 0), QTime(13, 30), QTime(15, 20), QTime(18, 0), QTime(19, 50)]
        day_week = ['M', 'T', 'W', 'R', 'F', 'S', 'U']
        date_time = QDateTime.currentDateTime()
        date = date_time.date()
        time = date_time.time()

        for i in range(len(timeList)):
            if time < timeList[i]:
                break
            if i == 5: i += 1

        self.year = date.year()
        if date.month() > 6:
            self.semester = "Fall"
        else:
            self.semester = "Spring"
        self.time_slot_id = ''.join((day_week[date.dayOfWeek() - 1], str(i)))

class WidgetIndex(object):
    """辅助Main类布局"""
    def __init__(self):
        self._page = [] # 页面信息，为二维字符数组，内容为ip地址，len(self.page)为页数，len(self.page[i]) <= 9
        self._widget = {} # 从ip到部件的映射
        self._index = ((i/ 3, i% 3) for i in range(9))

    def add(self, data, addr):
        self._add_page(addr)
        if addr in self._widget.keys():
            self._widget[addr].setOpen(data)
        else:
            self._widget[addr] = ClassControl(addr, data)

    def get_data(self, addr):
        return self._widget[addr].getOpen()

    def remove(self, addr):
        i, index = self.index(addr)
        self._widget.pop(addr)
        self._page[i].pop(index)
        self._shape_sort(i)

    def index(self, addr):
        i = 0; index = -1
        for i_page in self._page:
            try:
                index = i_page.index(addr)
                break
            except:
                i += 1
        return i, index

    def _add_page(self, addr):
        i, index = self.index(addr)
        if index != -1:
            return
        try:
            if len(self._page[len(self._page) - 1]) == 9:
                self._page.append([addr])
            else:
                self._page[len(self._page) - 1].append(addr)
        except:
            self._page.append([addr])

    def _shape_sort(self, i):
        """形状整理，i是被改变的页"""
        try: self._page[i + 1]
        except: return

        if len(self._page[i]) == 0:
            self._page.pop(i)
            return

        self._page[i].append(self._page[i + 1].pop(0))
        if len(self._page[i]) != 9:
            self._shape_sort(i)
        else:
            self._shape_sort(i + 1)


class Main(QWidget):
    ser_signaled = pyqtSignal(bytearray, str)
    def __init__(self):
        QWidget.__init__(self)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.class_dict = WidgetIndex()
        self.init_sev()
        self.m_data = {} # 用于判断接受信号是否有效

        self.ser_signaled.connect(self.setClassControl)

        self.startTimer(20000)

    def timerEvent(self, event):
        QWidget.timerEvent(self, event)
        silent = self.heartbeats.getSilent()

        for ip in silent:
            self.class_dict.remove(ip)

        self._update_class()

    def setClassControl(self, data, addr):
        if addr not in self.m_data.keys():
            self.m_data[addr] = [data]
        elif len(self.m_data[addr]) == 1:
            self.m_data[addr].append(data)
            self.class_dict.add(data, addr)
        elif data != self.m_data[addr][0] and \
            data != self.m_data[addr][1]:
            self.m_data[addr][0] = self.m_data[addr][1]
            self.m_data[addr][1] = data
            self.class_dict.add(data, addr)
        else: pass
        self._update_class()

    def init_sev(self, num = 1):
        self.receiverEvent = threading.Event()
        self.receiverEvent.set()
        self.heartbeats = Heartbeats()
        self.receivers = []
        for i in range(num):
            receiver = Receiver(goOneEvent=self.receiverEvent, heartbeats=self.heartbeats, fr=self)
            receiver.start()
            self.receivers.append(receiver)

    def close_sev(self):
        for i in range(len(self.receivers)):
            self.receivers[i].join()

    def ser_signal(self, data, addr):
        try: m_data = self.class_dict.get_data(addr[0])
        except: m_data = bytearray([0, 0, 0, 0])

        print(m_data)
        self.ser_signaled.emit(data, addr[0])
        return m_data

    def _update_class(self):
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(0).widget()
            self.layout.removeWidget(widget)
            widget.hide()

        for widget in self.class_dict._widget.values():
            widget.show()
            self.layout.addWidget(widget)

        self.update()

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    if createConnection():
        qb = Main()
        # qb.setClassControl(bytearray([0, 0, 0, 1]), '127.0.0.1')
        qb.show()
    else:
        sys.exit()

    if app.exec_() == 0:
        qb.close_sev()
        sys.exit()
