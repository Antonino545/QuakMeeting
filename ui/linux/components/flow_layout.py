"""
Qt FlowLayout implementation for multi-row wrapping of widgets.
"""

from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from PyQt6.QtWidgets import QLayout, QSizePolicy


class FlowLayout(QLayout):
    """A layout that arranges child widgets left-to-right and wraps automatically into multiple rows."""

    def __init__(self, parent=None, margin=0, spacing=6):
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only):
        m = self.contentsMargins()
        effective_rect = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0
        space_x = self.spacing()
        space_y = self.spacing()

        for item in self.itemList:
            wid = item.widget()
            if not wid:
                continue
            item_w = wid.sizeHint().width()
            item_h = wid.sizeHint().height()
            next_x = x + item_w + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item_w + space_x
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), wid.sizeHint()))
            x = next_x
            line_height = max(line_height, item_h)

        return y + line_height - rect.y() + m.bottom()
