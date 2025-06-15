btnStyle = """
            QPushButton {
                background-color: #212121;
                color: white;
                padding: 5px;
                font-size: 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
cboxStyle = """
            QComboBox {
                background-color: #303030;
                color: white;
                padding: 5px;
                font-size: 12px;
                border-radius: 3px;
            }
            QComboBox:!editable:on, QComboBox::drop-down:editable:on {
                color: white;
            }   
        """

chboxStyle = """
            QCheckBox {
                padding: 3px;
                color: white;
            }
        """