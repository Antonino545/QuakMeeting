import random
from datetime import datetime, timedelta
import AppKit
import objc

from ui.macos.banner_window import _run_banner
from ui.macos.banner.renderers.modular_renderer import ModularPilotRenderer
from ui.macos.theme import Theme
from ui.macos.components import (
    CardView,
    HairlineDivider,
    KeywordChipView,
    MascotMiniCanvasView,
)
from core.services.config_service import config
from core.services.event_bus import event_bus
from core.services.language_service import t, get_active_language

def get_animals():
    return [
        ("duck", t("animal_duck")),
        ("owl", t("animal_owl")),
        ("bunny", t("animal_bunny")),
        ("platypus", t("animal_platypus")),
        ("squirrel", t("animal_squirrel"))
    ]

CATEGORIES_DEF = [
    ("study", "cat_study_title", "cat_study_desc", "student", "owl", Theme.MAUVE),
    ("food", "cat_food_title", "cat_food_desc", "chef", "duck", Theme.PEACH),
    ("travel", "cat_travel_title", "cat_travel_desc", "captain", "duck", Theme.SAPPHIRE),
    ("sport", "cat_sport_title", "cat_sport_desc", "gym", "bunny", Theme.RED),
    ("in_person", "cat_in_person_title", "cat_in_person_desc", "racer", "squirrel", Theme.YELLOW),
    ("health", "cat_health_title", "cat_health_desc", "zen", "bunny", Theme.TEAL),
    ("general", "cat_general_title", "cat_general_desc", "aviator", "duck", Theme.GREEN)
]

def get_categories():
    return [
        (k, t(t_key), t(d_key), fo, da, col)
        for (k, t_key, d_key, fo, da, col) in CATEGORIES_DEF
    ]

from ui.common.theme import get_combo_title




class HangarTabController(AppKit.NSObject):
    def init(self):
        self = objc.super(HangarTabController, self).init()
        self.dashboard_controller = None
        self._cached_view = None
        self._cached_sig = None
        self._anim_timer = None
        self.expanded_categories = set()
        self.mini_canvases = {}
        self.subtitle_labels = {}
        self.popups = {}
        self.kw_toggle_buttons = {}
        self.kw_doc_views = {}
        self.kw_scrolls = {}
        self.kw_inputs = {}
        return self

    @objc.python_method
    def start_animation_timer(self):
        if self._anim_timer is None:
            self._anim_timer = AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.04, self, "onAnimTick:", None, True
            )
            AppKit.NSRunLoop.mainRunLoop().addTimer_forMode_(self._anim_timer, AppKit.NSRunLoopCommonModes)

    @objc.python_method
    def stop_animation_timer(self):
        if self._anim_timer is not None:
            self._anim_timer.invalidate()
            self._anim_timer = None

    @objc.IBAction
    def onAnimTick_(self, sender):
        if not self._cached_view:
            return
        w = self._cached_view.window()
        if not w or not w.isVisible():
            return
        for canvas in list(self.mini_canvases.values()):
            canvas.tick += 1
            canvas.setNeedsDisplay_(True)

    @objc.python_method
    def invalidate_cache(self):
        if self._cached_view and self._cached_view.contentView() and self._cached_view.documentView():
            old_doc_h = self._cached_view.documentView().frame().size.height
            clip_y = self._cached_view.contentView().bounds().origin.y
            clip_h = self._cached_view.contentView().bounds().size.height
            self._saved_dist_from_top = max(0.0, old_doc_h - (clip_y + clip_h))
        self.stop_animation_timer()
        self._cached_view = None
        self._cached_sig = None

    @objc.python_method
    def render(self, container, w, h):
        self.dashboard_controller = container
        if not hasattr(self, "expanded_categories") or self.expanded_categories is None:
            self.expanded_categories = set()
        if not hasattr(self, "active_study_subcat") or not self.active_study_subcat:
            self.active_study_subcat = "study"
        self.mini_canvases = {}
        self.subtitle_labels = {}
        self.popups = {}
        self.kw_toggle_buttons = {}
        self.kw_doc_views = {}
        self.kw_scrolls = {}
        self.kw_inputs = {}

        customs = config.get("mascot_customization", {})
        sig = (
            round(w),
            round(h),
            str(customs),
            bool(config.get("force_default_pilot", False)),
            get_active_language(),
            tuple(sorted(self.expanded_categories)),
            str(self.active_study_subcat),
        )
        if self._cached_view is not None and self._cached_sig == sig:
            self.start_animation_timer()
            return self._cached_view

        scroll_view = AppKit.NSScrollView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setDrawsBackground_(False)

        card_base_h = 102.0
        gap = 14.0
        header_h = 52.0
        categories = get_categories()
        n_cards = len(categories)

        def get_drawer_h(ck: str) -> float:
            return 240.0 if ck == "study" else 156.0

        total_cards_h = sum(
            (card_base_h + get_drawer_h(cat_key) if cat_key in self.expanded_categories else card_base_h)
            for cat_key, *_ in categories
        )
        content_h = max(h, 20.0 + header_h + 16.0 + total_cards_h + (n_cards - 1) * gap + 24.0)
        content_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w - 16, content_h))

        # 1. Top Compact Toolbar
        header_card = self._create_header_card(20, content_h - 20 - header_h, w - 56, header_h)
        content_view.addSubview_(header_card)

        # 2. Category Cards
        cur_top = content_h - 20.0 - header_h - 16.0
        for cat_key, cat_title, cat_desc, fixed_outfit, def_animal, cat_color in categories:
            is_exp = cat_key in self.expanded_categories
            this_drawer_h = get_drawer_h(cat_key)
            this_card_h = (card_base_h + this_drawer_h) if is_exp else card_base_h
            c_y = cur_top - this_card_h

            current_setting = customs.get(cat_key, {})
            current_animal = (
                current_setting.get("animal", def_animal)
                if isinstance(current_setting, dict)
                else (current_setting or def_animal)
            )

            card = self._create_customizer_card(
                cat_key,
                cat_title,
                cat_desc,
                fixed_outfit,
                current_animal,
                cat_color,
                20,
                c_y,
                w - 56,
                this_card_h,
                is_exp,
                this_drawer_h,
            )
            content_view.addSubview_(card)
            cur_top = c_y - gap

        scroll_view.setDocumentView_(content_view)
        if scroll_view.contentView():
            if hasattr(self, "_saved_dist_from_top") and self._saved_dist_from_top is not None:
                target_y = max(0.0, min(content_h - h, content_h - h - self._saved_dist_from_top))
            else:
                target_y = max(0.0, content_h - h)
            scroll_view.contentView().scrollToPoint_(AppKit.NSMakePoint(0, target_y))
            scroll_view.reflectScrolledClipView_(scroll_view.contentView())

        self._cached_view = scroll_view
        self._cached_sig = sig
        self.start_animation_timer()
        return scroll_view

    @objc.python_method
    def _create_header_card(self, x, y, w, h):
        container = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, w, h))
        container.setWantsLayer_(True)
        container.layer().setBackgroundColor_(Theme.MANTLE.CGColor())
        container.layer().setCornerRadius_(10.0)
        container.layer().setMasksToBounds_(True)
        container.layer().setBorderWidth_(1.0)
        container.layer().setBorderColor_(Theme.SURFACE0.CGColor())

        # Title on Left
        title_w = max(240.0, w - 380.0)
        title_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, (h - 22) * 0.5, title_w, 22))
        title_lbl.setStringValue_(t("hangar_header_title"))
        title_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(13.5))
        title_lbl.setTextColor_(Theme.TEXT)
        title_lbl.setBezeled_(False)
        title_lbl.setDrawsBackground_(False)
        title_lbl.setEditable_(False)
        container.addSubview_(title_lbl)

        # Actions on Right: Test Chime, Surprise Me, Reset Presets
        chime_btn = Theme.create_button(
            AppKit.NSMakeRect(w - 364, (h - 28) * 0.5, 110, 28),
            title=t("hangar_test_chime"),
            bg_color=Theme.SURFACE0,
            text_color=Theme.TEXT,
            border_color=Theme.SURFACE1,
            corner_radius=6.0,
            font_size=11.0,
            bold=False
        )
        chime_btn.setTarget_(self)
        chime_btn.setAction_("onTestChime:")
        container.addSubview_(chime_btn)

        surprise_btn = Theme.create_button(
            AppKit.NSMakeRect(w - 246, (h - 28) * 0.5, 114, 28),
            title=t("hangar_surprise_me"),
            bg_color=Theme.SURFACE0,
            text_color=Theme.TEXT,
            border_color=Theme.SURFACE1,
            corner_radius=6.0,
            font_size=11.0,
            bold=False
        )
        surprise_btn.setTarget_(self)
        surprise_btn.setAction_("onSurpriseMe:")
        container.addSubview_(surprise_btn)

        reset_btn = Theme.create_button(
            AppKit.NSMakeRect(w - 124, (h - 28) * 0.5, 114, 28),
            title=t("hangar_reset_presets"),
            bg_color=Theme.SURFACE0,
            text_color=Theme.SUBTEXT0,
            border_color=Theme.SURFACE1,
            corner_radius=6.0,
            font_size=11.0,
            bold=False
        )
        reset_btn.setTarget_(self)
        reset_btn.setAction_("onResetDefaults:")
        container.addSubview_(reset_btn)

        return container

    @objc.python_method
    def _create_customizer_card(
        self,
        cat_key,
        cat_title,
        cat_desc,
        fixed_outfit,
        cur_animal,
        accent_color,
        x,
        y,
        w,
        h,
        is_expanded,
        drawer_h,
    ):
        card = CardView.create(
            AppKit.NSMakeRect(x, y, w, h),
            bg_color=(Theme.MANTLE if is_expanded else Theme.BASE),
            corner_radius=12.0,
            border_width=(1.5 if is_expanded else 1.0),
            border_color=(accent_color if is_expanded else Theme.SURFACE0),
        )

        # ── Upper section (always 102px tall) ──
        upper_y = drawer_h if is_expanded else 0.0
        upper_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, upper_y, w, 102.0))
        card.addSubview_(upper_view)

        # Accent Pill Indicator
        pill = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(12, 24, 4, 54))
        pill.setWantsLayer_(True)
        pill.layer().setBackgroundColor_(accent_color.CGColor())
        pill.layer().setCornerRadius_(2.0)
        upper_view.addSubview_(pill)

        # 🌟 Embedded Live Mini Mascot Viewport
        mini_canvas = MascotMiniCanvasView.alloc().initWithFrame_animal_outfit_(
            AppKit.NSMakeRect(22, 16, 74, 68), cur_animal, fixed_outfit
        )
        self.mini_canvases[cat_key] = mini_canvas
        upper_view.addSubview_(mini_canvas)

        # Title and Description
        text_w = max(240.0, w - 316.0)
        title_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(106, 64, text_w, 24))
        title_lbl.setStringValue_(cat_title)
        title_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(13))
        title_lbl.setTextColor_(Theme.TEXT)
        title_lbl.setBezeled_(False)
        title_lbl.setDrawsBackground_(False)
        title_lbl.setEditable_(False)
        upper_view.addSubview_(title_lbl)

        combo_name = get_combo_title(cur_animal, fixed_outfit)
        sub_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(106, 12, text_w, 50))
        sub_lbl.setStringValue_(f"{cat_desc}\n✨ {t('hangar_active_pilot_label')}: {combo_name}")
        sub_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(10.5))
        sub_lbl.setTextColor_(Theme.SUBTEXT0)
        sub_lbl.setBezeled_(False)
        sub_lbl.setDrawsBackground_(False)
        sub_lbl.setEditable_(False)
        sub_lbl.cell().setWraps_(True)
        sub_lbl.setUsesSingleLineMode_(False)
        self.subtitle_labels[cat_key] = (sub_lbl, cat_desc, fixed_outfit)
        upper_view.addSubview_(sub_lbl)

        # Controls on Right
        # Row 1: Mascot Selector (Label stacked cleanly above Popup)
        animal_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(w - 186, 78, 170, 16))
        animal_lbl.setStringValue_(t("hangar_animal_mascot"))
        animal_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(10.5))
        animal_lbl.setTextColor_(Theme.SUBTEXT1)
        animal_lbl.setBezeled_(False)
        animal_lbl.setDrawsBackground_(False)
        animal_lbl.setEditable_(False)
        upper_view.addSubview_(animal_lbl)

        animals = get_animals()
        animal_popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(
            AppKit.NSMakeRect(w - 188, 50, 172, 28), False
        )
        for a_id, a_label in animals:
            animal_popup.addItemWithTitle_(a_label)
        a_idx = next((i for i, (a_id, _) in enumerate(animals) if a_id == cur_animal), 0)
        animal_popup.selectItemAtIndex_(a_idx)
        animal_popup.setIdentifier_(cat_key)
        animal_popup.setTarget_(self)
        animal_popup.setAction_("onAnimalSelectionChanged:")
        self.popups[cat_key] = animal_popup
        upper_view.addSubview_(animal_popup)

        # Row 2: Keywords Toggle Button & Test Button
        if cat_key == "study":
            kw_count = (
                len(config.get_custom_keywords("study"))
                + len(config.get_custom_keywords("class"))
                + len(config.get_custom_keywords("exam"))
            )
        else:
            kw_count = len(config.get_custom_keywords(cat_key))
        toggle_title = t(
            "hangar_keywords_toggle_btn_open" if is_expanded else "hangar_keywords_toggle_btn",
            count=kw_count,
        )
        kw_toggle_btn = Theme.create_button(
            AppKit.NSMakeRect(w - 192, 14, 114, 28),
            title=toggle_title,
            bg_color=Theme.SURFACE1 if is_expanded else Theme.SURFACE0,
            text_color=Theme.TEXT if is_expanded else Theme.SUBTEXT1,
            border_color=Theme.BLUE if is_expanded else Theme.SURFACE1,
            corner_radius=6.0,
            font_size=11.0,
            bold=is_expanded,
        )
        kw_toggle_btn.setIdentifier_(cat_key)
        kw_toggle_btn.setTarget_(self)
        kw_toggle_btn.setAction_("onToggleKeywordsDrawer:")
        self.kw_toggle_buttons[cat_key] = kw_toggle_btn
        upper_view.addSubview_(kw_toggle_btn)

        test_btn = Theme.create_button(
            AppKit.NSMakeRect(w - 74, 14, 60, 28),
            title=t("hangar_test_btn"),
            bg_color=accent_color,
            text_color=Theme.CRUST,
            border_color=None,
            corner_radius=6.0,
            font_size=11.5,
            bold=True,
        )
        test_btn.setIdentifier_(cat_key)
        test_btn.setTarget_(self)
        test_btn.setAction_("onTestCustomCategoryFlight:")
        upper_view.addSubview_(test_btn)

        if not is_expanded:
            return card

        # ── Expanded Drawer ──
        div = HairlineDivider.create(16, drawer_h - 1.0, w - 32.0)
        card.addSubview_(div)

        drawer_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, drawer_h))
        card.addSubview_(drawer_view)

        if cat_key == "study":
            # 🎓 ACADEMIC MASTER DRAWER (drawer_h = 226px)
            cur_subcat = getattr(self, "active_study_subcat", "study")
            subcats = [
                ("study", t("hangar_subcat_study")),
                ("class", t("hangar_subcat_class")),
                ("exam", t("hangar_subcat_exam"))
            ]
            tab_btn_w = (w - 36.0 - 16.0) / 3.0
            for s_i, (s_key, s_label) in enumerate(subcats):
                s_x = 18.0 + s_i * (tab_btn_w + 8.0)
                is_active = (s_key == cur_subcat)
                tab_btn = Theme.create_button(
                    AppKit.NSMakeRect(s_x, drawer_h - 38.0, tab_btn_w, 28.0),
                    title=s_label,
                    bg_color=(Theme.SURFACE1 if is_active else Theme.SURFACE0),
                    text_color=(Theme.TEXT if is_active else Theme.SUBTEXT0),
                    border_color=(Theme.MAUVE if is_active else Theme.SURFACE1),
                    corner_radius=6.0,
                    font_size=11.0,
                    bold=is_active
                )
                tab_btn.setIdentifier_(s_key)
                tab_btn.setTarget_(self)
                tab_btn.setAction_("onSelectStudySubcat:")
                drawer_view.addSubview_(tab_btn)

            # Dynamic Explainer Guide
            guide_keys = {
                "study": "hangar_subcat_study_guide",
                "class": "hangar_subcat_class_guide",
                "exam": "hangar_subcat_exam_guide"
            }
            guide_text = t(guide_keys.get(cur_subcat, "hangar_subcat_study_guide"))
            guide_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, drawer_h - 70.0, w - 36.0, 26.0))
            guide_lbl.setStringValue_(guide_text)
            guide_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(10.5))
            guide_lbl.setTextColor_(Theme.SUBTEXT1)
            guide_lbl.setBezeled_(False)
            guide_lbl.setDrawsBackground_(False)
            guide_lbl.setEditable_(False)
            guide_lbl.cell().setWraps_(True)
            guide_lbl.setUsesSingleLineMode_(False)
            drawer_view.addSubview_(guide_lbl)

            # Subcategory Mascot Selector Row
            sub_m_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, drawer_h - 100.0, 160.0, 18.0))
            sub_m_lbl.setStringValue_(t("hangar_subcat_mascot_label"))
            sub_m_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(10.5))
            sub_m_lbl.setTextColor_(Theme.SUBTEXT0)
            sub_m_lbl.setBezeled_(False)
            sub_m_lbl.setDrawsBackground_(False)
            sub_m_lbl.setEditable_(False)
            drawer_view.addSubview_(sub_m_lbl)

            sub_m_popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(
                AppKit.NSMakeRect(180.0, drawer_h - 104.0, 220.0, 26.0), False
            )
            sub_m_popup.addItemWithTitle_(t("hangar_subcat_mascot_sync"))
            animals = get_animals()
            for a_id, a_label in animals:
                sub_m_popup.addItemWithTitle_(a_label)

            c_dict = config.get("mascot_customization", {})
            subcat_val = c_dict.get(cur_subcat)
            subcat_animal = subcat_val.get("animal") if isinstance(subcat_val, dict) else subcat_val
            if subcat_animal and subcat_animal != cur_animal:
                a_idx = next((i + 1 for i, (a_id, _) in enumerate(animals) if a_id == subcat_animal), 0)
                sub_m_popup.selectItemAtIndex_(a_idx)
            else:
                sub_m_popup.selectItemAtIndex_(0)

            sub_m_popup.setIdentifier_(cur_subcat)
            sub_m_popup.setTarget_(self)
            sub_m_popup.setAction_("onStudySubcatMascotChanged:")
            drawer_view.addSubview_(sub_m_popup)

            # Keywords Scroll Area (with comfortable 2-row height and generous spacing)
            kw_scroll = AppKit.NSScrollView.alloc().initWithFrame_(AppKit.NSMakeRect(18, 48, w - 36, 76))
            kw_scroll.setHasHorizontalScroller_(True)
            kw_scroll.setHasVerticalScroller_(False)
            kw_scroll.setAutohidesScrollers_(True)
            kw_scroll.setDrawsBackground_(False)

            kw_doc = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w - 36, 70))
            kw_scroll.setDocumentView_(kw_doc)
            drawer_view.addSubview_(kw_scroll)
            self.kw_doc_views["study"] = kw_doc
            self.kw_scrolls["study"] = kw_scroll

            # Bottom Action Bar
            kw_input = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, 12, 140, 26))
            kw_input.setPlaceholderString_(t("hangar_keywords_add_placeholder"))
            kw_input.setFont_(AppKit.NSFont.systemFontOfSize_(11.0))
            kw_input.setTextColor_(Theme.TEXT)
            kw_input.setWantsLayer_(True)
            kw_input.layer().setCornerRadius_(5.0)
            kw_input.setBackgroundColor_(Theme.CRUST)
            kw_input.setDrawsBackground_(True)
            kw_input.layer().setBorderWidth_(1.0)
            kw_input.layer().setBorderColor_(Theme.SURFACE0.CGColor())
            kw_input.setFocusRingType_(AppKit.NSFocusRingTypeNone)
            kw_input.setIdentifier_("study")
            kw_input.setTarget_(self)
            kw_input.setAction_("onAddCategoryKeyword:")
            self.kw_inputs["study"] = kw_input
            drawer_view.addSubview_(kw_input)

            add_btn = Theme.create_button(
                AppKit.NSMakeRect(164, 12, 54, 26),
                title=t("hangar_keywords_add_btn"),
                bg_color=Theme.GREEN,
                text_color=Theme.CRUST,
                border_color=None,
                corner_radius=5.0,
                font_size=10.5,
                bold=True,
            )
            add_btn.setIdentifier_("study")
            add_btn.setTarget_(self)
            add_btn.setAction_("onAddCategoryKeyword:")
            drawer_view.addSubview_(add_btn)

            reset_btn = Theme.create_button(
                AppKit.NSMakeRect(224, 12, 64, 26),
                title=t("hangar_keywords_reset_btn"),
                bg_color=Theme.SURFACE1,
                text_color=Theme.SUBTEXT1,
                border_color=Theme.SURFACE2,
                corner_radius=5.0,
                font_size=10.5,
                bold=False,
            )
            reset_btn.setIdentifier_("study")
            reset_btn.setToolTip_(t("hangar_keywords_reset_btn"))
            reset_btn.setTarget_(self)
            reset_btn.setAction_("onResetCategoryKeywords:")
            drawer_view.addSubview_(reset_btn)

            test_subcat_title_keys = {
                "study": "hangar_test_study_btn",
                "class": "hangar_test_class_btn",
                "exam": "hangar_test_exam_btn"
            }
            test_subcat_btn = Theme.create_button(
                AppKit.NSMakeRect(294, 12, 160, 26),
                title=t(test_subcat_title_keys.get(cur_subcat, "hangar_test_study_btn")),
                bg_color=Theme.MAUVE,
                text_color=Theme.CRUST,
                border_color=None,
                corner_radius=5.0,
                font_size=10.5,
                bold=True,
            )
            test_subcat_btn.setIdentifier_(cur_subcat)
            test_subcat_btn.setTarget_(self)
            test_subcat_btn.setAction_("onTestSubcatFlight:")
            drawer_view.addSubview_(test_subcat_btn)

            hide_btn = Theme.create_button(
                AppKit.NSMakeRect(w - 82, 12, 64, 26),
                title=t("hangar_keywords_drawer_hide"),
                bg_color=Theme.SURFACE0,
                text_color=Theme.SUBTEXT0,
                border_color=Theme.SURFACE1,
                corner_radius=5.0,
                font_size=10.5,
                bold=False,
            )
            hide_btn.setIdentifier_("study")
            hide_btn.setTarget_(self)
            hide_btn.setAction_("onToggleKeywordsDrawer:")
            drawer_view.addSubview_(hide_btn)

            self._render_category_keywords("study")
            return card

        # ── Standard Drawer for other categories (height: drawer_h = 156px) ──
        guide_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, drawer_h - 28.0, w - 36, 18))
        guide_lbl.setStringValue_(t("hangar_keywords_drawer_subtitle"))
        guide_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(10.5))
        guide_lbl.setTextColor_(Theme.SUBTEXT0)
        guide_lbl.setBezeled_(False)
        guide_lbl.setDrawsBackground_(False)
        guide_lbl.setEditable_(False)
        drawer_view.addSubview_(guide_lbl)

        # Keywords Scroll Area (with comfortable 2-row height and generous spacing)
        kw_scroll = AppKit.NSScrollView.alloc().initWithFrame_(AppKit.NSMakeRect(18, 46, w - 36, 76))
        kw_scroll.setHasHorizontalScroller_(True)
        kw_scroll.setHasVerticalScroller_(False)
        kw_scroll.setAutohidesScrollers_(True)
        kw_scroll.setDrawsBackground_(False)

        kw_doc = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w - 36, 70))
        kw_scroll.setDocumentView_(kw_doc)
        drawer_view.addSubview_(kw_scroll)
        self.kw_doc_views[cat_key] = kw_doc
        self.kw_scrolls[cat_key] = kw_scroll

        # Bottom Action Bar
        kw_input = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, 10, 160, 26))
        kw_input.setPlaceholderString_(t("hangar_keywords_add_placeholder"))
        kw_input.setFont_(AppKit.NSFont.systemFontOfSize_(11.0))
        kw_input.setTextColor_(Theme.TEXT)
        kw_input.setWantsLayer_(True)
        kw_input.layer().setCornerRadius_(5.0)
        kw_input.setBackgroundColor_(Theme.CRUST)
        kw_input.setDrawsBackground_(True)
        kw_input.layer().setBorderWidth_(1.0)
        kw_input.layer().setBorderColor_(Theme.SURFACE0.CGColor())
        kw_input.setFocusRingType_(AppKit.NSFocusRingTypeNone)
        kw_input.setIdentifier_(cat_key)
        kw_input.setTarget_(self)
        kw_input.setAction_("onAddCategoryKeyword:")
        self.kw_inputs[cat_key] = kw_input
        drawer_view.addSubview_(kw_input)

        add_btn = Theme.create_button(
            AppKit.NSMakeRect(184, 10, 60, 26),
            title=t("hangar_keywords_add_btn"),
            bg_color=Theme.GREEN,
            text_color=Theme.CRUST,
            border_color=None,
            corner_radius=5.0,
            font_size=10.5,
            bold=True,
        )
        add_btn.setIdentifier_(cat_key)
        add_btn.setTarget_(self)
        add_btn.setAction_("onAddCategoryKeyword:")
        drawer_view.addSubview_(add_btn)

        reset_btn = Theme.create_button(
            AppKit.NSMakeRect(250, 10, 76, 26),
            title=t("hangar_keywords_reset_btn"),
            bg_color=Theme.SURFACE1,
            text_color=Theme.SUBTEXT1,
            border_color=Theme.SURFACE2,
            corner_radius=5.0,
            font_size=10.5,
            bold=False,
        )
        reset_btn.setIdentifier_(cat_key)
        reset_btn.setToolTip_(t("hangar_keywords_reset_btn"))
        reset_btn.setTarget_(self)
        reset_btn.setAction_("onResetCategoryKeywords:")
        drawer_view.addSubview_(reset_btn)

        hide_btn = Theme.create_button(
            AppKit.NSMakeRect(w - 92, 10, 76, 26),
            title=t("hangar_keywords_drawer_hide"),
            bg_color=Theme.SURFACE0,
            text_color=Theme.SUBTEXT0,
            border_color=Theme.SURFACE1,
            corner_radius=5.0,
            font_size=10.5,
            bold=False,
        )
        hide_btn.setIdentifier_(cat_key)
        hide_btn.setTarget_(self)
        hide_btn.setAction_("onToggleKeywordsDrawer:")
        drawer_view.addSubview_(hide_btn)

        self._render_category_keywords(cat_key)
        return card

    @objc.python_method
    def _render_category_keywords(self, cat_key: str):
        doc_view = self.kw_doc_views.get(cat_key)
        scroll_view = self.kw_scrolls.get(cat_key)
        if not doc_view or not scroll_view:
            return

        for sub in list(doc_view.subviews()):
            sub.removeFromSuperview()

        effective_cat = getattr(self, "active_study_subcat", "study") if cat_key == "study" else cat_key
        keywords = config.get_custom_keywords(effective_cat)

        # Update toggle button title if present
        if cat_key in self.kw_toggle_buttons:
            is_exp = cat_key in self.expanded_categories
            if cat_key == "study":
                kw_count = (
                    len(config.get_custom_keywords("study"))
                    + len(config.get_custom_keywords("class"))
                    + len(config.get_custom_keywords("exam"))
                )
            else:
                kw_count = len(keywords)
            self.kw_toggle_buttons[cat_key].setTitle_(
                t(
                    "hangar_keywords_toggle_btn_open" if is_exp else "hangar_keywords_toggle_btn",
                    count=kw_count,
                )
            )

        if not keywords:
            empty_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(10, 25, 300, 18))
            empty_lbl.setStringValue_("No trigger keywords. Add keywords below.")
            empty_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(10.5))
            empty_lbl.setTextColor_(Theme.SUBTEXT0)
            empty_lbl.setBezeled_(False)
            empty_lbl.setDrawsBackground_(False)
            empty_lbl.setEditable_(False)
            doc_view.addSubview_(empty_lbl)
            doc_view.setFrame_(AppKit.NSMakeRect(0, 0, 320, 70.0))
            return

        # 2-Row alternating layout for keywords inside the canvas with generous vertical spacing
        chip_h = 24.0
        gap_x = 6.0
        gap_y = 10.0
        x1 = 6.0
        x2 = 6.0

        for i, kw in enumerate(keywords):
            kw_w = max(44.0, min(140.0, len(kw) * 6.8 + 26.0))
            if i % 2 == 0:
                # Row 1 (top row)
                y = 6.0 + chip_h + gap_y  # 40.0 (spans 40.0 to 64.0)
                x = x1
                x1 += kw_w + gap_x
            else:
                # Row 2 (bottom row)
                y = 6.0  # spans 6.0 to 30.0
                x = x2
                x2 += kw_w + gap_x

            chip_view = KeywordChipView.create(
                x,
                y,
                kw_w,
                chip_h,
                kw,
                target=self,
                action="onRemoveCategoryKeyword:",
                tooltip=f"{effective_cat}:::{kw}",
            )
            doc_view.addSubview_(chip_view)

        total_w = max(scroll_view.frame().size.width, max(x1, x2) + 12.0)
        doc_view.setFrame_(AppKit.NSMakeRect(0, 0, total_w, 70.0))

    @objc.IBAction
    def onToggleKeywordsDrawer_(self, sender):
        cat_key = str(sender.identifier())
        if not hasattr(self, "expanded_categories") or self.expanded_categories is None:
            self.expanded_categories = set()

        # Save scroll distance from top before refreshing
        if self._cached_view and self._cached_view.contentView() and self._cached_view.documentView():
            old_doc_h = self._cached_view.documentView().frame().size.height
            clip_y = self._cached_view.contentView().bounds().origin.y
            clip_h = self._cached_view.contentView().bounds().size.height
            self._saved_dist_from_top = max(0.0, old_doc_h - (clip_y + clip_h))

        if cat_key in self.expanded_categories:
            self.expanded_categories.remove(cat_key)
        else:
            self.expanded_categories.add(cat_key)
        self.invalidate_cache()
        if self.dashboard_controller and hasattr(self.dashboard_controller, "refresh_current_tab"):
            self.dashboard_controller.refresh_current_tab()

    @objc.IBAction
    def onAddCategoryKeyword_(self, sender):
        cat_key = str(sender.identifier())
        effective_cat = getattr(self, "active_study_subcat", "study") if cat_key == "study" else cat_key
        kw_input = self.kw_inputs.get(cat_key)
        if not kw_input:
            return
        raw_val = (kw_input.stringValue() or "").strip()
        if not raw_val:
            return
        # Support batch comma-separated keywords: "padel, tennis, workout"
        tokens = [t.strip() for t in raw_val.split(",") if t.strip()]
        any_success = False
        for token in tokens:
            if config.add_custom_keyword(effective_cat, token):
                any_success = True
        if any_success:
            kw_input.setStringValue_("")
            try:
                event_bus.publish("CONFIG_CHANGED", key="custom_keywords", value=config.get_custom_keywords())
            except Exception:
                pass
            self._render_category_keywords(cat_key)

    @objc.IBAction
    def onRemoveCategoryKeyword_(self, sender):
        tip = str(sender.toolTip() or "")
        if ":::" not in tip:
            return
        cat_key, kw = tip.split(":::", 1)
        config.remove_custom_keyword(cat_key, kw)
        try:
            event_bus.publish("CONFIG_CHANGED", key="custom_keywords", value=config.get_custom_keywords())
        except Exception:
            pass
        self._render_category_keywords("study" if cat_key in ("study", "class", "exam") else cat_key)

    @objc.IBAction
    def onResetCategoryKeywords_(self, sender):
        cat_key = str(sender.identifier())
        effective_cat = getattr(self, "active_study_subcat", "study") if cat_key == "study" else cat_key
        config.reset_custom_keywords(effective_cat)
        try:
            event_bus.publish("CONFIG_CHANGED", key="custom_keywords", value=config.get_custom_keywords())
        except Exception:
            pass
        self._render_category_keywords(cat_key)

    @objc.IBAction
    def onSelectStudySubcat_(self, sender):
        self.active_study_subcat = str(sender.identifier())
        self.invalidate_cache()
        if self.dashboard_controller and hasattr(self.dashboard_controller, "refresh_current_tab"):
            self.dashboard_controller.refresh_current_tab()

    @objc.IBAction
    def onStudySubcatMascotChanged_(self, sender):
        subcat = getattr(self, "active_study_subcat", "study")
        sel_idx = sender.indexOfSelectedItem()
        animals = get_animals()
        c_dict = dict(config.get("mascot_customization", {}))

        if sel_idx == 0:
            main_study = c_dict.get("study", {})
            main_animal = main_study.get("animal", "owl") if isinstance(main_study, dict) else (main_study or "owl")
            c_dict[subcat] = {"animal": main_animal, "outfit": "student"}
        else:
            sel_animal = animals[sel_idx - 1][0]
            c_dict[subcat] = {"animal": sel_animal, "outfit": "student"}

        config.set("mascot_customization", c_dict)
        try:
            event_bus.publish("CONFIG_CHANGED", key="mascot_customization", value=c_dict)
        except Exception:
            pass
        self.invalidate_cache()
        if self.dashboard_controller and hasattr(self.dashboard_controller, "refresh_current_tab"):
            self.dashboard_controller.refresh_current_tab()

    @objc.IBAction
    def onTestSubcatFlight_(self, sender):
        from core.services.sound_service import play_test_chime
        play_test_chime()
        subcat = getattr(self, "active_study_subcat", "study")
        customs = config.get("mascot_customization", {})
        setting = customs.get(subcat, customs.get("study", {}))
        animal = setting.get("animal", "owl") if isinstance(setting, dict) else (setting or "owl")
        outfit = "student"

        now = datetime.now().astimezone()
        if subcat == "study":
            _run_banner({
                "title": "Sessione di Studio Individuale - Biblioteca" if get_active_language() == "it" else "Deep Focus & Solo Study Session",
                "provider": "Study Session 📖",
                "pilot_type": f"{animal}_{outfit}",
                "animal": animal,
                "outfit": outfit,
                "event_type": "study",
                "category": "study",
                "action_btn_text": "⚡ TEMPO DI STUDIARE! 📖" if get_active_language() == "it" else "⚡ TIME TO STUDY! DO IT 📖",
                "action_url": "https://calendar.apple.com",
                "start_time": now + timedelta(minutes=10),
                "end_time": now + timedelta(minutes=70),
                "reminder_stage": 10,
                "is_travel": False,
                "is_test_banner": True,
                "is_late": False
            })
        elif subcat == "class":
            _run_banner({
                "title": "Lezione di Reti Neurali & AI (Aula 3B)" if get_active_language() == "it" else "Neural Networks & AI Lecture (Room 3B)",
                "provider": "Class / Lecture 🏫 Aula 3B",
                "pilot_type": f"{animal}_{outfit}",
                "animal": animal,
                "outfit": outfit,
                "event_type": "class",
                "category": "class",
                "classroom": "Aula 3B",
                "teacher": "Prof. Rossi",
                "action_btn_text": "🏫 AULA 3B & NOTE" if get_active_language() == "it" else "🏫 ROOM 3B & NOTES",
                "action_url": "https://maps.apple.com",
                "start_time": now + timedelta(minutes=10),
                "end_time": now + timedelta(minutes=70),
                "reminder_stage": 10,
                "is_travel": True,
                "is_test_banner": True,
                "is_late": False
            })
        elif subcat == "exam":
            _run_banner({
                "title": "Esame di Fisica Generale - Appello Orale (Aula Magna)" if get_active_language() == "it" else "General Physics Final Exam (Main Hall)",
                "provider": "Exam 🎓 Aula Magna",
                "pilot_type": f"{animal}_{outfit}",
                "animal": animal,
                "outfit": outfit,
                "event_type": "exam",
                "category": "exam",
                "classroom": "Aula Magna",
                "action_btn_text": "🎓 AULA MAGNA & NOTE" if get_active_language() == "it" else "🎓 MAIN HALL & NOTES",
                "action_url": "https://maps.apple.com",
                "start_time": now + timedelta(minutes=10),
                "end_time": now + timedelta(minutes=70),
                "reminder_stage": 10,
                "is_travel": True,
                "is_test_banner": True,
                "is_late": False
            })

    @objc.IBAction
    def onAnimalSelectionChanged_(self, sender):
        cat_key = str(sender.identifier())
        sel_idx = sender.indexOfSelectedItem()
        animals = get_animals()
        sel_animal = animals[sel_idx][0]

        fixed_outfit = next((fo for k, _, _, fo, _, _ in CATEGORIES_DEF if k == cat_key), "aviator")

        customs = config.get("mascot_customization", {})
        if not isinstance(customs, dict):
            customs = {}
        if cat_key not in customs or not isinstance(customs[cat_key], dict):
            customs[cat_key] = {"animal": sel_animal, "outfit": fixed_outfit}
        else:
            customs[cat_key]["animal"] = sel_animal
            customs[cat_key]["outfit"] = fixed_outfit

        if cat_key == "study":
            for sub in ("class", "exam"):
                if sub not in customs or not isinstance(customs[sub], dict):
                    customs[sub] = {"animal": sel_animal, "outfit": "student"}

        config.set("mascot_customization", customs)
        event_bus.publish("CONFIG_CHANGED", key="mascot_customization", value=customs)

        # Instant Live Preview Update for this card
        if cat_key in self.mini_canvases:
            self.mini_canvases[cat_key].updateAnimal_(sel_animal)
        if cat_key in self.subtitle_labels:
            lbl, desc, outfit = self.subtitle_labels[cat_key]
            lbl.setStringValue_(f"{desc}\n✨ Active Pilot: {get_combo_title(sel_animal, outfit)}")

        self.invalidate_cache()

    @objc.IBAction
    def onSurpriseMe_(self, sender):
        customs = config.get("mascot_customization", {})
        if not isinstance(customs, dict):
            customs = {}
        animals = get_animals()
        all_a = [a[0] for a in animals]
        for cat_key, _, _, fixed_outfit, _, _ in CATEGORIES_DEF:
            chosen_a = random.choice(all_a)
            customs[cat_key] = {
                "animal": chosen_a,
                "outfit": fixed_outfit
            }
            if cat_key in self.popups:
                a_idx = next((i for i, (a_id, _) in enumerate(animals) if a_id == chosen_a), 0)
                self.popups[cat_key].selectItemAtIndex_(a_idx)
            if cat_key in self.mini_canvases:
                self.mini_canvases[cat_key].updateAnimal_(chosen_a)
            if cat_key in self.subtitle_labels:
                lbl, desc, outfit = self.subtitle_labels[cat_key]
                lbl.setStringValue_(f"{desc}\n✨ {t('hangar_active_pilot_label')}: {get_combo_title(chosen_a, outfit)}")

        config.set("mascot_customization", customs)
        event_bus.publish("CONFIG_CHANGED", key="mascot_customization", value=customs)
        self.invalidate_cache()
        if self.dashboard_controller and hasattr(self.dashboard_controller, "refresh_current_tab"):
            self.dashboard_controller.refresh_current_tab()

    @objc.IBAction
    def onResetDefaults_(self, sender):
        defaults = {
            "study": {"animal": "owl", "outfit": "student"},
            "food": {"animal": "duck", "outfit": "chef"},
            "travel": {"animal": "duck", "outfit": "captain"},
            "sport": {"animal": "bunny", "outfit": "gym"},
            "in_person": {"animal": "squirrel", "outfit": "racer"},
            "health": {"animal": "bunny", "outfit": "zen"},
            "general": {"animal": "duck", "outfit": "aviator"}
        }
        animals = get_animals()
        for cat_key, _, _, fixed_outfit, def_animal, _ in CATEGORIES_DEF:
            pair = defaults.get(cat_key, {"animal": def_animal, "outfit": fixed_outfit})
            chosen_a = pair.get("animal", def_animal)
            if cat_key in self.popups:
                a_idx = next((i for i, (a_id, _) in enumerate(animals) if a_id == chosen_a), 0)
                self.popups[cat_key].selectItemAtIndex_(a_idx)
            if cat_key in self.mini_canvases:
                self.mini_canvases[cat_key].updateAnimal_(chosen_a)
            if cat_key in self.subtitle_labels:
                lbl, desc, outfit = self.subtitle_labels[cat_key]
                lbl.setStringValue_(f"{desc}\n✨ {t('hangar_active_pilot_label')}: {get_combo_title(chosen_a, outfit)}")

        config.set("mascot_customization", defaults)
        event_bus.publish("CONFIG_CHANGED", key="mascot_customization", value=defaults)
        self.invalidate_cache()
        if self.dashboard_controller and hasattr(self.dashboard_controller, "refresh_current_tab"):
            self.dashboard_controller.refresh_current_tab()

    @objc.IBAction
    def onTestChime_(self, sender):
        from core.services.sound_service import play_test_chime
        play_test_chime()

    @objc.IBAction
    def onTestCustomCategoryFlight_(self, sender):
        from core.services.sound_service import play_test_chime
        play_test_chime()

        cat_key = str(sender.identifier())
        customs = config.get("mascot_customization", {})
        setting = customs.get(cat_key, {})
        def_animal = next((da for k, _, _, _, da, _ in CATEGORIES_DEF if k == cat_key), "duck")
        fixed_outfit = next((fo for k, _, _, fo, _, _ in CATEGORIES_DEF if k == cat_key), "aviator")

        animal = setting.get("animal", def_animal) if isinstance(setting, dict) else (setting or def_animal)
        outfit = fixed_outfit

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
        _run_banner({
            "title": titles.get(cat_key, "Custom Mascot Test Flight"),
            "provider": get_combo_title(animal, outfit),
            "pilot_type": f"{animal}_{outfit}",
            "animal": animal,
            "outfit": outfit,
            "action_btn_text": "🚀 TEST FLIGHT",
            "action_url": "https://meet.google.com/test-flight",
            "start_time": now + timedelta(minutes=10),
            "end_time": now + timedelta(minutes=70),
            "reminder_stage": 10,
            "is_travel": cat_key in ("food", "travel", "sport", "in_person"),
            "is_test_banner": True,
            "is_late": False
        })
