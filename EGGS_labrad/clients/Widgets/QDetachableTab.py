from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QPoint, QEvent, QMimeData
from PyQt5.QtGui import QIcon, QCursor, QPainter, QMouseEvent, QDrag, QPixmap
from PyQt5.QtWidgets import QTabBar, QTabWidget, QWidget, QDialog, QVBoxLayout, QApplication, QMainWindow, QLabel

# todo: remove ampersand in front of name when removing


class QDetachableTabWidget(QTabWidget):
    """
    The DetachableTabWidget adds additional functionality to
    Qt's QTabWidget that allows it to detach and re-attach tabs.

    Additional Features:
      - Detach tabs by dragging the tabs away from
      the tab bar double-clicking the tab.
      - Re-attach tabs by closing the detached tab's window
      by double-clicking the detached tab's window frame.

    Modified Features:
        Re-ordering (moving) tabs by dragging was re-implemented.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tabBar = self.TabBar(self)
        self.tabBar.onDetachTabSignal.connect(self.detachTab)
        self.tabBar.onMoveTabSignal.connect(self.moveTab)
        self.setTabBar(self.tabBar)

    def setMovable(self, movable):
        """
        The default movable functionality of QTabWidget must remain
        disabled so as not to conflict with the added features.
        """
        pass

    @pyqtSlot(int, int)
    def moveTab(self, fromIndex, toIndex):
        """
        Move a tab from one position (index) to another.
        @param    fromIndex    the original index location of the tab
        @param    toIndex      the new index location of the tab
        """
        widget = self.widget(fromIndex)
        icon = self.tabIcon(fromIndex)
        text = self.tabText(fromIndex)
        self.removeTab(fromIndex)
        self.insertTab(toIndex, widget, icon, text)
        self.setCurrentIndex(toIndex)

    @pyqtSlot(int, QPoint)
    def detachTab(self, index, point):
        """
        Detach the tab by removing its contents and placing them in a DetachedTab dialog.
        @param index    the index location of the tab to be detached
        @param point    the screen position for creating the new DetachedTab dialog
        """
        # Get the tab content
        name = self.tabText(index)
        icon = self.tabIcon(index)
        if icon.isNull():
            icon = self.window().windowIcon()
        contentWidget = self.widget(index)
        contentWidgetRect = contentWidget.frameGeometry()
        # Create a new detached tab window
        detachedTab = self.DetachedTab(contentWidget, self.parentWidget())
        detachedTab.setWindowModality(Qt.NonModal)
        detachedTab.setWindowTitle(name)
        detachedTab.setWindowIcon(icon)
        detachedTab.setObjectName(name)
        detachedTab.setGeometry(contentWidgetRect)
        # The detached tab returns to the main tab widget upon exit
        detachedTab.onCloseSignal.connect(self.attachTab)
        detachedTab.move(point)
        detachedTab.show()

    @pyqtSlot(QWidget, str, QIcon)
    def attachTab(self, contentWidget, name, icon):
        """
        Re-attach the tab by removing the content from the DetachedTab dialog,
        closing it, and placing the content back into the DetachableTabWidget.
        @param    contentWidget    the content widget from the DetachedTab dialog
        @param    name             the name of the detached tab
        @param    icon             the window icon for the detached tab
        """
        # Make the content widget a child of this widget
        contentWidget.setParent(self)
        # Create an image from the given icon
        if not icon.isNull():
            tabIconPixmap = icon.pixmap(icon.availableSizes()[0])
            tabIconImage = tabIconPixmap.toImage()
        else:
            tabIconImage = None
        # Create an image of the main window icon
        if not icon.isNull():
            windowIconPixmap = self.window().windowIcon().pixmap(icon.availableSizes()[0])
            windowIconImage = windowIconPixmap.toImage()
        else:
            windowIconImage = None
        # Determine if the given image and the main window icon are the same.
        # If they are, then do not add the icon to the tab.
        if tabIconImage == windowIconImage:
            index = self.addTab(contentWidget, name)
        else:
            index = self.addTab(contentWidget, icon, name)
        # Make this tab the current tab
        if index > -1:
            self.setCurrentIndex(index)


    # INTERNAL CLASSES
    class DetachedTab(QDialog):
        """
        When a tab is detached, the contents are placed into this QDialog.
        The tab can be re-attached by closing the dialog or by double-clicking
        on its window frame.
        """

        onCloseSignal = pyqtSignal(QWidget, str, QIcon)

        def __init__(self, contentWidget, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            self.contentWidget = contentWidget
            layout.addWidget(self.contentWidget)
            self.contentWidget.show()

        def event(self, event):
            """
            Capture a double click event on the dialog's window frame.
            @param event    an event
            @return         true if the event was recognized
            """
            # If the event type is QEvent.NonClientAreaMouseButtonDblClick
            # then close the dialog
            if event.type() == 176:
                event.accept()
                self.close()
            return QDialog.event(self, event)

        def closeEvent(self, event):
            """
            If the dialog is closed, emit the onCloseSignal and give
            the content widget back to the DetachableTabWidget.
            @param event    a close event
            """
            self.onCloseSignal.emit(self.contentWidget, str(self.objectName()), self.windowIcon())


    class TabBar(QTabBar):
        """
        The TabBar class re-implements some functionality of the QTabBar widget.
        """

        onDetachTabSignal = pyqtSignal(int, QPoint)
        onMoveTabSignal = pyqtSignal(int, int)

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setAcceptDrops(True)
            self.setElideMode(Qt.ElideRight)
            self.setSelectionBehaviorOnRemove(QTabBar.SelectLeftTab)
            self.dragStartPos = QPoint()
            self.dragDroppedPos = QPoint()
            self.mouseCursor = QCursor()
            self.dragInitiated = False

        def mouseDoubleClickEvent(self, event):
            """
            Send the onDetachTabSignal when a tab is double-clicked.
            @param  event   a mouse double click event
            """
            event.accept()
            self.onDetachTabSignal.emit(self.tabAt(event.pos()), self.mouseCursor.pos())

        def mousePressEvent(self, event):
            """
            Set the starting position for a drag event when the mouse button is pressed.
            @param    event    a mouse press event
            """
            if event.button() == Qt.LeftButton:
                self.dragStartPos = event.pos()
            self.dragDroppedPos.setX(0)
            self.dragDroppedPos.setY(0)
            self.dragInitiated = False
            QTabBar.mousePressEvent(self, event)

        def mouseMoveEvent(self, event):
            """
            Determine if the current movement is a drag.
            If it is, convert it into a QDrag.
            If the drag ends inside the tab bar, emit an onMoveTabSignal.
            If the drag ends outside the tab bar, emit an onDetachTabSignal.
            @param    event    a mouse move event
            """
            # Determine if the current movement is detected as a drag
            if (not self.dragStartPos.isNull()) and ((event.pos() - self.dragStartPos).manhattanLength() < QApplication.startDragDistance()):
                self.dragInitiated = True
            # If the current movement is a drag initiated by the left button
            if (event.buttons() and Qt.LeftButton) and self.dragInitiated:
                # Stop the move event
                finishMoveEvent = QMouseEvent(QEvent.MouseMove, event.pos(), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
                QTabBar.mouseMoveEvent(self, finishMoveEvent)
                # Convert the move event into a drag
                drag = QDrag(self)
                mimeData = QMimeData()
                mimeData.setData('action', b'application/tab-detach')
                drag.setMimeData(mimeData)
                # Create the appearance of dragging the tab content
                pixmap = self.parentWidget().currentWidget().grab()
                targetPixmap = QPixmap(pixmap.size())
                targetPixmap.fill(Qt.transparent)
                painter = QPainter(targetPixmap)
                painter.setOpacity(0.7)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                drag.setPixmap(targetPixmap)

                # Initiate the drag
                dropAction = drag.exec_(Qt.MoveAction | Qt.CopyAction)
                # If the drag completed outside the tab bar, detach the tab
                # and move the content to the current cursor position.
                if dropAction == Qt.IgnoreAction:
                    event.accept()
                    self.onDetachTabSignal.emit(self.tabAt(self.dragStartPos), self.mouseCursor.pos())
                # Else if the drag completed inside the tab bar, move the selected tab to the new position
                elif dropAction == Qt.MoveAction:
                    if not self.dragDroppedPos.isNull():
                        event.accept()
                        self.onMoveTabSignal.emit(self.tabAt(self.dragStartPos), self.tabAt(self.dragDroppedPos))
            else:
                QTabBar.mouseMoveEvent(self, event)

        def dragEnterEvent(self, event):
            """
            Determine if the drag has entered a tab position from another tab position.
            @param  event   a drag enter event
            """
            mimeData = event.mimeData()
            formats = mimeData.formats()
            if ('action' in formats) and mimeData.data('action') == 'application/tab-detach':
                event.acceptProposedAction()
            QTabBar.dragMoveEvent(self, event)

        def dropEvent(self, event):
            """
            Get the position of the end of the drag.
            @param  event   a drop event
            """
            self.dragDroppedPos = event.pos()
            event.accept()
            QTabBar.dropEvent(self, event)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    mainWindow = QMainWindow()
    tabWidget = QDetachableTabWidget(mainWindow)

    tab1 = QLabel('Test Widget 1')
    tabWidget.addTab(tab1, 'Tab1')
    tab2 = QLabel('Test Widget 2')
    tabWidget.addTab(tab2, 'Tab2')
    tab3 = QLabel('Test Widget 3')
    tabWidget.addTab(tab3, 'Tab3')

    tabWidget.show()
    mainWindow.setCentralWidget(tabWidget)
    mainWindow.show()

    try:
        exitStatus = app.exec_()
        sys.exit(exitStatus)
    except Exception as e:
        pass
