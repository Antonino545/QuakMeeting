"""
PyQt6 Hangar Tab for QuakMeeting Flight Deck on Linux.
Provides interactive mascot workshop, custom animal outfit combinations,
live vector animation previews, and 1-click test flights.
"""

from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QScrollArea, QFrame, QComboBox, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter

from core.services.config_service import config
from core.services.event_bus import event_bus
from core.services.language_service import t


class QtMascotMiniWidget(QFrame):
    """Mini preview widget rendering live vector mascot animations."""

    def __init__(self, animal="duck", outfit="aviator", parent=None):
        super().__init__(parent)
        self.animal = animal
        self.outfit = outfit
        self.tick = 0
        self.setFixedSize(68, 64)
        self.setStyleSheet("""
            QFrame {
                background: #11111b;
                border: 1px solid #313244;
                border-radius: 8px;
            }
        """)

    def update_mascot(self, animal, outfit):
        self.animal = animal
        self.outfit = outfit
        self.update()

    def update_animal(self, animal):
        self.animal = animal
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w = self.width()
        h = self.height()
        p.save()
        p.translate(w * 0.5 - 2, h * 0.5 - 2)
        p.scale(0.68, -0.68)
        from ui.linux.banner.renderers.modular_renderer import QtModularRenderer
        renderer = QtModularRenderer(animal=self.animal, outfit=self.outfit)
        renderer.draw_pilot(p, 0, 0, self.tick)
        p.restore()


class QtHangarTab(QWidget):
    """Pilot Hangar workshop and category customization tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.h_mini_widgets = []
        self.hangar_anim_timer = None
        self.expanded_categories = set()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.h_scroll = QScrollArea(self)
        self.h_scroll.setWidgetResizable(True)
        self.h_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.h_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.h_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.h_content = QWidget()
        self.h_layout = QVBoxLayout(self.h_content)
        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.h_layout.setSpacing(12)

        self.refresh_hangar()
        self.h_scroll.setWidget(self.h_content)
        layout.addWidget(self.h_scroll)

    def render_hangar_tab(self):
        """Public alias for refreshing hangar tab."""
        self.refresh_hangar()

    def _refresh_hangar(self):
        """Private alias for backwards compatibility."""
        self.refresh_hangar()

    def start_animation_timer(self):
        """Starts the vector animation tick timer for active previewing."""
        try:
            if self.hangar_anim_timer is None:
                self.hangar_anim_timer = QTimer(self)
                self.hangar_anim_timer.setInterval(40)  # 25 fps
                self.hangar_anim_timer.timeout.connect(self._on_hangar_tick)
            if not self.hangar_anim_timer.isActive():
                self.hangar_anim_timer.start()
        except Exception:
            pass

    def stop_animation_timer(self):
        """Stops the vector animation tick timer to conserve CPU when inactive."""
        try:
            if self.hangar_anim_timer is not None and self.hangar_anim_timer.isActive():
                self.hangar_anim_timer.stop()
        except Exception:
            pass

    def _on_hangar_tick(self):
        """Updates animation ticks across all miniature preview widgets."""
        if not self.isVisible():
            return
        for w in self.h_mini_widgets:
            try:
                w.tick += 1
                w.update()
            except Exception:
                pass

    def refresh_hangar(self):
        """Rebuilds the category customizer cards and toolbars."""
        while self.h_layout.count():
            child = self.h_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.h_mini_widgets = []

        # 1. Header Toolbar
        customs = config.get("mascot_customization", {})
        header_card = QFrame(self.h_content)
        header_card.setObjectName("HeaderCard")
        header_card.setStyleSheet("""
            QFrame#HeaderCard {
                background: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 12px;
            }
        """)
        r_box = QHBoxLayout(header_card)
        r_box.setContentsMargins(18, 10, 18, 10)
        r_box.setSpacing(10)

        r_title = QLabel("🦆 Mascot Workshop & Pilot Hangar", header_card)
        r_title.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 13.5px;")
        r_box.addWidget(r_title, stretch=1)

        def _on_surprise():
            import random
            all_a = [a[0] for a in ANIMALS]
            c_dict = config.get("mascot_customization", {})
            if not isinstance(c_dict, dict):
                c_dict = {}
            for ck, _, _, fixed_outfit, _, _ in CATEGORIES:
                c_dict[ck] = {"animal": random.choice(all_a), "outfit": fixed_outfit}
            config.set("mascot_customization", c_dict)
            event_bus.publish("CONFIG_CHANGED", key="mascot_customization", value=c_dict)
            self.refresh_hangar()

        def _on_reset():
            defs = {
                "study": {"animal": "owl", "outfit": "student"},
                "food": {"animal": "duck", "outfit": "chef"},
                "travel": {"animal": "duck", "outfit": "captain"},
                "sport": {"animal": "bunny", "outfit": "gym"},
                "in_person": {"animal": "squirrel", "outfit": "racer"},
                "health": {"animal": "bunny", "outfit": "zen"},
                "general": {"animal": "duck", "outfit": "aviator"}
            }
            config.set("mascot_customization", defs)
            event_bus.publish("CONFIG_CHANGED", key="mascot_customization", value=defs)
            self.refresh_hangar()

        chime_btn = QPushButton("🔔 Test Chime", header_card)
        chime_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        chime_btn.setStyleSheet("background: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 5px 12px; font-size: 11px;")
        def _on_test_chime():
            from core.services.sound_service import play_test_chime
            play_test_chime()
        chime_btn.clicked.connect(_on_test_chime)
        r_box.addWidget(chime_btn)

        sur_btn = QPushButton("🎲 Surprise Me", header_card)
        sur_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        sur_btn.setStyleSheet("background: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 5px 12px; font-size: 11px;")
        sur_btn.clicked.connect(_on_surprise)
        r_box.addWidget(sur_btn)

        res_btn = QPushButton("🔄 Reset Presets", header_card)
        res_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        res_btn.setStyleSheet("background: #313244; color: #a6adc8; border: 1px solid #45475a; border-radius: 6px; padding: 5px 12px; font-size: 11px;")
        res_btn.clicked.connect(_on_reset)
        r_box.addWidget(res_btn)

        self.h_layout.addWidget(header_card)

        # 2. Category Mascot Customizer Cards
        ANIMALS = [
            ("duck", "🦆 Aviator Duck"),
            ("owl", "🦉 Academic Owl"),
            ("bunny", "🐰 Clever Bunny"),
            ("platypus", "🕵️‍♂️ Secret Platypus"),
            ("squirrel", "🐿️ Hyper Squirrel")
        ]

        CATEGORIES = [
            ("study", "🎓 University & Study Sessions", "Lectures, exams, self-study, homework & thesis.", "student", "owl", "#cba6f7"),
            ("food", "🍕 Dining, Lunch & Restaurants", "Dinners, lunch dates, pizzerias & food routes.", "chef", "duck", "#fab387"),
            ("travel", "✈️ Travel, Flights & Trains", "Airports, flights, high-speed trains & trips.", "captain", "duck", "#74c7ec"),
            ("sport", "🏋️ Gym, Palestra & Sports", "Workouts, crossfit, padel, tennis & running.", "gym", "bunny", "#f38ba8"),
            ("in_person", "🏎️ In-Person & Commute", "Doctor visits, dentist & real-time navigation.", "racer", "squirrel", "#f9e2af"),
            ("health", "🌸 Wellness & Therapy", "Serenis sessions, yoga, meditation & calm.", "zen", "bunny", "#94e2d5"),
            ("general", "⏰ General Meetings & Reminders", "Video conferences (Meet, Zoom, Teams) & alerts.", "aviator", "duck", "#a6e3a1")
        ]

        for idx, (cat_key, cat_title, cat_desc, fixed_outfit, def_animal, cat_color) in enumerate(CATEGORIES):
            current_setting = customs.get(cat_key, {})
            current_animal = current_setting.get("animal", def_animal) if isinstance(current_setting, dict) else (current_setting or def_animal)

            card = QFrame(self.h_content)
            card.setObjectName("Card")
            card.setStyleSheet(f"""
                QFrame#Card {{
                    background: #181825;
                    border: 1px solid #313244;
                    border-left: 4px solid {cat_color};
                    border-radius: 10px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(10)

            # ── Top Row: Mini Preview, Titles, Controls ──
            top_row = QHBoxLayout()
            top_row.setSpacing(14)

            # Mini Canvas Preview on Left
            mini_preview = QtMascotMiniWidget(animal=current_animal, outfit=fixed_outfit, parent=card)
            self.h_mini_widgets.append(mini_preview)
            top_row.addWidget(mini_preview)

            p_box = QVBoxLayout()
            p_box.setSpacing(2)
            n_l = QLabel(cat_title, card)
            n_l.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 13px;")
            d_l = QLabel(f"{cat_desc}  •  <span style='color:{cat_color}; font-weight:bold;'>✨ Active Pilot: {current_animal.capitalize()}</span>", card)
            d_l.setStyleSheet("color: #a6adc8; font-size: 11px;")
            p_box.addWidget(n_l)
            p_box.addWidget(d_l)
            top_row.addLayout(p_box, stretch=1)

            # Controls Box
            ctrl_box = QVBoxLayout()
            ctrl_box.setSpacing(3)
            a_lbl = QLabel("Animal Mascot:", card)
            a_lbl.setStyleSheet("color: #a6adc8; font-size: 10px; font-weight: bold;")
            ctrl_box.addWidget(a_lbl)

            btn_row = QHBoxLayout()
            btn_row.setSpacing(10)

            a_combo = QComboBox(card)
            for a_id, a_name in ANIMALS:
                a_combo.addItem(a_name, a_id)
            a_idx = next((i for i, (a_id, _) in enumerate(ANIMALS) if a_id == current_animal), 0)
            a_combo.setCurrentIndex(a_idx)
            a_combo.setFixedHeight(32)
            a_combo.setStyleSheet("""
                QComboBox {
                    background: #313244;
                    color: #cdd6f4;
                    border: 1px solid #45475a;
                    border-radius: 6px;
                    padding: 4px 10px;
                    font-size: 11.5px;
                    min-width: 145px;
                }
            """)
            def _make_animal_cb(ck, fo):
                def _on_a_changed(i_val):
                    sel_a = ANIMALS[i_val][0]
                    c_dict = config.get("mascot_customization", {})
                    if not isinstance(c_dict, dict):
                        c_dict = {}
                    c_dict[ck] = {"animal": sel_a, "outfit": fo}
                    config.set("mascot_customization", c_dict)
                    event_bus.publish("CONFIG_CHANGED", key="mascot_customization", value=c_dict)
                    self.refresh_hangar()
                return _on_a_changed

            a_combo.currentIndexChanged.connect(_make_animal_cb(cat_key, fixed_outfit))
            btn_row.addWidget(a_combo)

            # Test Flight Button
            def _make_test_flight_cb(ck, fo):
                def _trigger_test():
                    c_dict = config.get("mascot_customization", {})
                    val = c_dict.get(ck, {})
                    an = val.get("animal", "duck") if isinstance(val, dict) else (val or "duck")
                    out = fo
                    titles = {
                        "study": "Neural Networks & AI University Lecture",
                        "food": "Dinner with Friends at Pizzeria",
                        "travel": "Flight BA 257 to London Heathrow",
                        "sport": "CrossFit & Palestra Workout Session",
                        "in_person": "Architectural Studio Consultation",
                        "health": "Serenis Mindfulness & Yoga Session",
                        "secret": "Top Secret Agent Mission Briefing",
                        "general": "Weekly Team Sprint Planning"
                    }
                    now = datetime.now().astimezone()
                    evt = {
                        "title": titles.get(ck, "Custom Mascot Test Flight"),
                        "provider": f"{an.capitalize()} wearing {out.capitalize()} Hat ✨",
                        "pilot_type": f"{an}_{out}",
                        "animal": an,
                        "outfit": out,
                        "action_btn_text": "🚀 TEST FLIGHT",
                        "action_url": "https://meet.google.com/test-flight",
                        "start_time": now + timedelta(minutes=10),
                        "end_time": now + timedelta(minutes=70),
                        "reminder_stage": 10,
                        "is_travel": ck in ("food", "travel", "sport", "in_person"),
                        "is_test_banner": True,
                        "is_late": False
                    }
                    from core.services.sound_service import play_test_chime
                    play_test_chime()
                    from ui.linux.banner.qt_banner import show_qt_banner
                    show_qt_banner(evt)
                return _trigger_test

            t_btn = QPushButton("🚀 Test", card)
            t_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            t_btn.setFixedHeight(32)
            t_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {cat_color};
                    color: #11111b;
                    font-weight: bold;
                    font-size: 11.5px;
                    border-radius: 6px;
                    padding: 6px 16px;
                    border: 1px solid {cat_color};
                }}
            """)
            t_btn.clicked.connect(_make_test_flight_cb(cat_key, fixed_outfit))

            kw_count = len(config.get_custom_keywords(cat_key))
            is_exp = cat_key in self.expanded_categories
            kw_toggle_btn = QPushButton(
                t(
                    "hangar_keywords_toggle_btn_open" if is_exp else "hangar_keywords_toggle_btn",
                    count=kw_count,
                ),
                card,
            )
            kw_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            kw_toggle_btn.setFixedHeight(32)
            if is_exp:
                kw_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #45475a;
                        color: #89b4fa;
                        font-size: 11px;
                        font-weight: bold;
                        border-radius: 6px;
                        padding: 6px 12px;
                        border: 1px solid #89b4fa;
                    }
                """)
            else:
                kw_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #313244;
                        color: #cdd6f4;
                        font-size: 11px;
                        font-weight: 500;
                        border-radius: 6px;
                        padding: 6px 12px;
                        border: 1px solid #45475a;
                    }
                    QPushButton:hover {
                        background-color: #45475a;
                        color: #ffffff;
                    }
                """)
            btn_row.addWidget(kw_toggle_btn)
            btn_row.addWidget(t_btn)

            ctrl_box.addLayout(btn_row)
            top_row.addLayout(ctrl_box)
            card_layout.addLayout(top_row)

            # ── Hairline Divider ──
            h_line = QFrame(card)
            h_line.setFrameShape(QFrame.Shape.HLine)
            h_line.setStyleSheet("background-color: #313244; max-height: 1px; border: none;")
            h_line.setVisible(is_exp)
            card_layout.addWidget(h_line)

            # ── Expandable Drawer (Bigger Section) ──
            drawer = QFrame(card)
            drawer.setStyleSheet("background: transparent; border: none;")
            drawer.setVisible(is_exp)
            drawer_layout = QVBoxLayout(drawer)
            drawer_layout.setContentsMargins(4, 6, 4, 4)
            drawer_layout.setSpacing(6)
            card_layout.addWidget(drawer)

            # Drawer Guidance Subtitle
            guide_lbl = QLabel(t("hangar_keywords_drawer_subtitle"), drawer)
            guide_lbl.setStyleSheet("color: #a6adc8; font-size: 10.5px; font-style: italic; border: none;")
            drawer_layout.addWidget(guide_lbl)

            # Spacious Keywords Scroll Area
            kw_scroll = QScrollArea(drawer)
            kw_scroll.setFixedHeight(64)
            kw_scroll.setWidgetResizable(True)
            kw_scroll.setFrameShape(QFrame.Shape.NoFrame)
            kw_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            kw_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            kw_scroll.setStyleSheet("""
                QScrollArea {
                    background: #11111b;
                    border: 1px solid #313244;
                    border-radius: 6px;
                }
            """)

            chips_widget = QWidget()
            chips_widget.setStyleSheet("background: transparent;")
            chips_lay = QHBoxLayout(chips_widget)
            chips_lay.setContentsMargins(8, 4, 8, 4)
            chips_lay.setSpacing(6)
            kw_scroll.setWidget(chips_widget)
            drawer_layout.addWidget(kw_scroll)

            def _render_cat_chips(
                ck=cat_key,
                container=chips_lay,
                c_widget=chips_widget,
                btn=kw_toggle_btn,
                d_frame=drawer,
            ):
                while container.count():
                    it = container.takeAt(0)
                    if it.widget():
                        it.widget().deleteLater()
                    elif it.layout():
                        while it.layout().count():
                            s = it.layout().takeAt(0)
                            if s.widget():
                                s.widget().deleteLater()

                keywords = config.get_custom_keywords(ck)
                is_open = d_frame.isVisible()
                btn.setText(
                    t(
                        "hangar_keywords_toggle_btn_open" if is_open else "hangar_keywords_toggle_btn",
                        count=len(keywords),
                    )
                )

                if not keywords:
                    empty = QLabel("No trigger keywords. Add keywords below.", c_widget)
                    empty.setStyleSheet("color: #6c7086; font-size: 10.5px; font-style: italic; border: none;")
                    container.addWidget(empty)
                    container.addStretch()
                    return

                for kw in keywords:
                    tag = QFrame(c_widget)
                    tag.setStyleSheet("""
                        QFrame {
                            background-color: #313244;
                            border: 1px solid #45475a;
                            border-radius: 4px;
                            padding: 2px 6px;
                        }
                    """)
                    tl = QHBoxLayout(tag)
                    tl.setContentsMargins(6, 2, 6, 2)
                    tl.setSpacing(4)

                    klbl = QLabel(kw, tag)
                    klbl.setStyleSheet("color: #cdd6f4; font-size: 11px; font-weight: 500; border: none;")
                    tl.addWidget(klbl)

                    del_b = QPushButton("✕", tag)
                    del_b.setCursor(Qt.CursorShape.PointingHandCursor)
                    del_b.setStyleSheet("""
                        QPushButton {
                            color: #f38ba8;
                            background: transparent;
                            border: none;
                            font-size: 10px;
                            font-weight: bold;
                            padding: 0px 2px;
                        }
                        QPushButton:hover { color: #eba0ac; }
                    """)

                    def _make_del(kw_del=kw, k_cat=ck):
                        def _del_action():
                            config.remove_custom_keyword(k_cat, kw_del)
                            try:
                                event_bus.publish(
                                    "CONFIG_CHANGED",
                                    key="custom_keywords",
                                    value=config.get_custom_keywords(),
                                )
                            except Exception:
                                pass
                            _render_cat_chips(k_cat, container, c_widget, btn, d_frame)

                        return _del_action

                    del_b.clicked.connect(_make_del())
                    tl.addWidget(del_b)
                    container.addWidget(tag)

                container.addStretch()

            _render_cat_chips(cat_key, chips_lay, chips_widget, kw_toggle_btn, drawer)

            # Bottom Action Bar
            act_bar = QHBoxLayout()
            act_bar.setSpacing(8)

            kw_input = QLineEdit(drawer)
            kw_input.setPlaceholderText(t("hangar_keywords_add_placeholder"))
            kw_input.setFixedHeight(28)
            kw_input.setStyleSheet("""
                QLineEdit {
                    background: #11111b;
                    color: #cdd6f4;
                    border: 1px solid #313244;
                    border-radius: 5px;
                    padding: 3px 8px;
                    font-size: 11px;
                }
                QLineEdit:focus { border-color: #89b4fa; }
            """)
            act_bar.addWidget(kw_input, stretch=1)

            add_btn = QPushButton(t("hangar_keywords_add_btn"), drawer)
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.setFixedHeight(28)
            add_btn.setStyleSheet("""
                QPushButton {
                    background: #a6e3a1;
                    color: #11111b;
                    font-size: 11px;
                    font-weight: bold;
                    border: 1px solid #a6e3a1;
                    border-radius: 5px;
                    padding: 4px 12px;
                }
                QPushButton:hover { background: #94e2d5; }
            """)

            def _make_add(
                ck=cat_key,
                inp=kw_input,
                lay=chips_lay,
                cw=chips_widget,
                btn=kw_toggle_btn,
                d_frame=drawer,
            ):
                def _add_action():
                    txt = inp.text().strip()
                    if not txt:
                        return
                    tokens = [t.strip() for t in txt.split(",") if t.strip()]
                    any_added = False
                    for tok in tokens:
                        if config.add_custom_keyword(ck, tok):
                            any_added = True
                    if any_added:
                        inp.clear()
                        try:
                            event_bus.publish(
                                "CONFIG_CHANGED",
                                key="custom_keywords",
                                value=config.get_custom_keywords(),
                            )
                        except Exception:
                            pass
                        _render_cat_chips(ck, lay, cw, btn, d_frame)

                return _add_action

            add_btn.clicked.connect(_make_add())
            kw_input.returnPressed.connect(_make_add())
            act_bar.addWidget(add_btn)

            rst_btn = QPushButton(t("hangar_keywords_reset_btn"), drawer)
            rst_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            rst_btn.setFixedHeight(28)
            rst_btn.setStyleSheet("""
                QPushButton {
                    background: #313244;
                    color: #a6adc8;
                    font-size: 11px;
                    border: 1px solid #45475a;
                    border-radius: 5px;
                    padding: 4px 10px;
                }
                QPushButton:hover { background: #45475a; color: #cdd6f4; }
            """)

            def _make_rst(
                ck=cat_key,
                lay=chips_lay,
                cw=chips_widget,
                btn=kw_toggle_btn,
                d_frame=drawer,
            ):
                def _rst_action():
                    config.reset_custom_keywords(ck)
                    try:
                        event_bus.publish(
                            "CONFIG_CHANGED",
                            key="custom_keywords",
                            value=config.get_custom_keywords(),
                        )
                    except Exception:
                        pass
                    _render_cat_chips(ck, lay, cw, btn, d_frame)

                return _rst_action

            rst_btn.clicked.connect(_make_rst())
            act_bar.addWidget(rst_btn)

            hide_btn = QPushButton(t("hangar_keywords_drawer_hide"), drawer)
            hide_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            hide_btn.setFixedHeight(28)
            hide_btn.setStyleSheet("""
                QPushButton {
                    background: #181825;
                    color: #a6adc8;
                    font-size: 11px;
                    border: 1px solid #313244;
                    border-radius: 5px;
                    padding: 4px 10px;
                }
                QPushButton:hover { background: #313244; color: #cdd6f4; }
            """)
            act_bar.addWidget(hide_btn)

            drawer_layout.addLayout(act_bar)

            # Toggle Handlers
            def _make_toggle(ck=cat_key, b=kw_toggle_btn, d=drawer, hl=h_line):
                def _toggle_action():
                    if ck in self.expanded_categories:
                        self.expanded_categories.remove(ck)
                    else:
                        self.expanded_categories.add(ck)
                    now_open = ck in self.expanded_categories
                    d.setVisible(now_open)
                    hl.setVisible(now_open)
                    cnt = len(config.get_custom_keywords(ck))
                    b.setText(
                        t(
                            "hangar_keywords_toggle_btn_open" if now_open else "hangar_keywords_toggle_btn",
                            count=cnt,
                        )
                    )
                    if now_open:
                        b.setStyleSheet("""
                            QPushButton {
                                background-color: #45475a;
                                color: #89b4fa;
                                font-size: 11px;
                                font-weight: bold;
                                border-radius: 6px;
                                padding: 6px 12px;
                                border: 1px solid #89b4fa;
                            }
                        """)
                    else:
                        b.setStyleSheet("""
                            QPushButton {
                                background-color: #313244;
                                color: #cdd6f4;
                                font-size: 11px;
                                font-weight: 500;
                                border-radius: 6px;
                                padding: 6px 12px;
                                border: 1px solid #45475a;
                            }
                            QPushButton:hover {
                                background-color: #45475a;
                                color: #ffffff;
                            }
                        """)

                return _toggle_action

            kw_toggle_btn.clicked.connect(_make_toggle())
            hide_btn.clicked.connect(_make_toggle())

            self.h_layout.addWidget(card)

        self.h_layout.addStretch()
        if self.isVisible():
            self.start_animation_timer()
