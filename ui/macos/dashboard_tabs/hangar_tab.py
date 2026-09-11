import math
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
    FlippedView,
    MascotMiniCanvasView,
)
from core.services.config_service import config
from core.services.event_bus import event_bus
from core.services.language_service import t, get_active_language

def get_animals():
    return list(ANIMALS)

CATEGORIES_DEF = [
    ("study", "cat_study_title", "cat_study_desc", "student", "owl", Theme.MAUVE),
    ("work", "cat_work_title", "cat_work_desc", "agent", "penguin", Theme.BLUE),
    ("food", "cat_food_title", "cat_food_desc", "chef", "squirrel", Theme.PEACH),
    ("sport", "cat_sport_title", "cat_sport_desc", "gym", "bunny", Theme.RED),
    ("health", "cat_health_title", "cat_health_desc", "zen", "panda", Theme.TEAL),
    ("travel", "cat_travel_title", "cat_travel_desc", "captain", "duck", Theme.SAPPHIRE),
    ("in_person", "cat_in_person_title", "cat_in_person_desc", "racer", "fox", Theme.YELLOW),
    ("concert", "cat_concert_title", "cat_concert_desc", "aviator", "fox", Theme.MAUVE),
    ("general", "cat_general_title", "cat_general_desc", "aviator", "duck", Theme.GREEN)
]

def get_categories():
    return [
        (k, t(t_key), t(d_key), fo, da, col)
        for (k, t_key, d_key, fo, da, col) in CATEGORIES_DEF
    ]

from ui.common.theme import get_combo_title
from ui.common.mascot_catalog import ANIMALS, normalize_accessories



class HangarTabController(AppKit.NSObject):
    def init(self):
        self = objc.super(HangarTabController, self).init()
        self.dashboard_controller = None
        self._cached_view = None
        self._cached_sig = None
        self._anim_timer = None
        self.expanded_categories = set()
        self.expanded_presets = set()
        self.mini_canvases = {}
        self.subtitle_labels = {}
        self.popups = {}
        self.kw_toggle_buttons = {}
        self.kw_inputs = {}
        self.custom_cnt_labels = {}
        self.custom_doc_views = {}
        self.custom_scrolls = {}
        self.preset_toggle_buttons = {}
        self.preset_doc_views = {}
        self.preset_scrolls = {}
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
        for canvas in self.mini_canvases.values():
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
        if not hasattr(self, "expanded_presets") or self.expanded_presets is None:
            self.expanded_presets = set()
        if not hasattr(self, "active_study_subcat") or not self.active_study_subcat:
            self.active_study_subcat = "study"
        customs = config.get("mascot_customization", {})
        sig = (
            round(w),
            round(h),
            str(customs),
            bool(config.get("force_default_pilot", False)),
            get_active_language(),
            tuple(sorted(self.expanded_categories)),
            tuple(sorted(self.expanded_presets)),
            str(self.active_study_subcat),
        )
        if self._cached_view is not None and self._cached_sig == sig:
            self.start_animation_timer()
            return self._cached_view

        self.mini_canvases = {}
        self.subtitle_labels = {}
        self.popups = {}
        self.kw_toggle_buttons = {}
        self.kw_inputs = {}
        self.custom_cnt_labels = {}
        self.custom_doc_views = {}
        self.custom_scrolls = {}
        self.preset_toggle_buttons = {}
        self.preset_doc_views = {}
        self.preset_scrolls = {}

        scroll_view = AppKit.NSScrollView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setDrawsBackground_(False)

        card_base_h = 102.0
        gap = 14.0
        header_h = 52.0
        categories = get_categories()
        n_cards = len(categories)

        def get_drawer_h(ck: str) -> float:
            target_k = self.active_study_subcat if ck == "study" else ck
            is_preset_open = target_k in self.expanded_presets
            preset_extra = 123.0 if is_preset_open else 0.0
            return (424.0 if ck == "study" else 226.0) + preset_extra


        total_cards_h = sum(
            (card_base_h + get_drawer_h(cat_key) if cat_key in self.expanded_categories else card_base_h)
            for cat_key, *_ in categories
        )
        content_h = max(h, 20.0 + header_h + 16.0 + total_cards_h + (n_cards - 1) * gap + 36.0)
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
        preview_outfit = "agent" if cur_animal == "platypus" else fixed_outfit
        mini_canvas = MascotMiniCanvasView.alloc().initWithFrame_animal_outfit_(
            AppKit.NSMakeRect(22, 16, 74, 68), cur_animal, preview_outfit
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

        combo_name = get_combo_title(cur_animal, preview_outfit)
        sub_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(106, 12, text_w, 50))
        sub_lbl.setStringValue_(f"{cat_desc}\n✨ {t('hangar_active_pilot_label')}: {combo_name}")
        sub_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(10.5))
        sub_lbl.setTextColor_(Theme.SUBTEXT0)
        sub_lbl.setBezeled_(False)
        sub_lbl.setDrawsBackground_(False)
        sub_lbl.setEditable_(False)
        sub_lbl.cell().setWraps_(True)
        sub_lbl.setUsesSingleLineMode_(False)
        self.subtitle_labels[cat_key] = (sub_lbl, cat_desc, preview_outfit)
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
            AppKit.NSMakeRect(w - 236, 14, 126, 28),
            title=toggle_title,
            bg_color=Theme.SURFACE1 if is_expanded else Theme.SURFACE0,
            text_color=Theme.TEXT if is_expanded else Theme.SUBTEXT1,
            border_color=Theme.BLUE if is_expanded else Theme.SURFACE1,
            corner_radius=7.0,
            font_size=11.0,
            bold=is_expanded,
        )
        kw_toggle_btn.setIdentifier_(cat_key)
        kw_toggle_btn.setTarget_(self)
        kw_toggle_btn.setAction_("onToggleKeywordsDrawer:")
        self.kw_toggle_buttons[cat_key] = kw_toggle_btn
        upper_view.addSubview_(kw_toggle_btn)

        test_btn = Theme.create_button(
            AppKit.NSMakeRect(w - 102, 14, 94, 28),
            title=t("hangar_test_btn"),
            bg_color=accent_color.colorWithAlphaComponent_(0.16),
            text_color=accent_color,
            border_color=accent_color,
            corner_radius=7.0,
            font_size=11.0,
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

        drawer_view = FlippedView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, drawer_h))
        card.addSubview_(drawer_view)

        target_k = getattr(self, "active_study_subcat", "study") if cat_key == "study" else cat_key
        is_preset_open = target_k in self.expanded_presets
        deck_h = 295.0 if is_preset_open else 172.0

        if cat_key == "study":
            # 🎓 ACADEMIC MASTER DRAWER
            cur_subcat = target_k
            subcats = [
                ("study", t("hangar_subcat_study")),
                ("class", t("hangar_subcat_class")),
                ("exam", t("hangar_subcat_exam")),
            ]
            tab_btn_w = (w - 36.0 - 16.0) / 3.0
            for s_i, (s_key, s_label) in enumerate(subcats):
                s_x = 18.0 + s_i * (tab_btn_w + 8.0)
                is_active = (s_key == cur_subcat)
                tab_btn = Theme.create_button(
                    AppKit.NSMakeRect(s_x, 10.0, tab_btn_w, 28.0),
                    title=s_label,
                    bg_color=(Theme.SURFACE1 if is_active else Theme.SURFACE0),
                    text_color=(Theme.TEXT if is_active else Theme.SUBTEXT0),
                    border_color=(Theme.MAUVE if is_active else Theme.SURFACE1),
                    corner_radius=6.0,
                    font_size=11.0,
                    bold=is_active,
                )
                tab_btn.setIdentifier_(s_key)
                tab_btn.setTarget_(self)
                tab_btn.setAction_("onSelectStudySubcat:")
                drawer_view.addSubview_(tab_btn)

            # Dynamic Explainer Guide
            guide_keys = {
                "study": "hangar_subcat_study_guide",
                "class": "hangar_subcat_class_guide",
                "exam": "hangar_subcat_exam_guide",
            }
            guide_text = t(guide_keys.get(cur_subcat, "hangar_subcat_study_guide"))
            guide_lbl = AppKit.NSTextField.alloc().initWithFrame_(
                AppKit.NSMakeRect(18.0, 44.0, w - 36.0, 18.0)
            )
            guide_lbl.setStringValue_(guide_text)
            guide_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(10.5))
            guide_lbl.setTextColor_(Theme.SUBTEXT1)
            guide_lbl.setBezeled_(False)
            guide_lbl.setDrawsBackground_(False)
            guide_lbl.setEditable_(False)
            guide_lbl.cell().setWraps_(True)
            guide_lbl.setUsesSingleLineMode_(False)
            drawer_view.addSubview_(guide_lbl)

            # Live Alert Banner Preview Mockup Frame (height: 124px, y = 68.0)
            sim_dw = w - 36.0
            sim_frame_h = 124.0
            sim_frame = FlippedView.alloc().initWithFrame_(
                AppKit.NSMakeRect(18.0, 68.0, sim_dw, sim_frame_h)
            )
            sim_frame.setWantsLayer_(True)
            sim_frame.layer().setBackgroundColor_(Theme.MANTLE.CGColor())
            sim_frame.layer().setCornerRadius_(10.0)
            sim_frame.layer().setBorderWidth_(1.0)
            sim_frame.layer().setBorderColor_(Theme.SURFACE0.CGColor())
            drawer_view.addSubview_(sim_frame)

            # Top Header Row of Simulator Frame
            # Left: Tag pill badge
            tag_view = FlippedView.alloc().initWithFrame_(
                AppKit.NSMakeRect(10.0, 8.0, 154.0, 24.0)
            )
            tag_view.setWantsLayer_(True)
            tag_view.layer().setBackgroundColor_(Theme.SURFACE0.CGColor())
            tag_view.layer().setBorderWidth_(1.0)
            tag_view.layer().setBorderColor_(Theme.MAUVE.CGColor())
            tag_view.layer().setCornerRadius_(4.0)

            tag_lbl = AppKit.NSTextField.alloc().initWithFrame_(
                AppKit.NSMakeRect(0, 3.0, 154.0, 18.0)
            )
            tag_lbl.setStringValue_(t("hangar_subcat_preview_tag"))
            tag_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(10.0))
            tag_lbl.setTextColor_(Theme.MAUVE)
            tag_lbl.setAlignment_(AppKit.NSTextAlignmentCenter)
            tag_lbl.setBezeled_(False)
            tag_lbl.setDrawsBackground_(False)
            tag_lbl.setEditable_(False)
            tag_lbl.setUsesSingleLineMode_(True)
            tag_view.addSubview_(tag_lbl)
            sim_frame.addSubview_(tag_view)

            # Right: Test button, Mascot sync popup, Mascot label
            test_btn_w = 135.0
            test_btn_x = sim_dw - 10.0 - test_btn_w
            flight_test_btn = Theme.create_button(
                AppKit.NSMakeRect(test_btn_x, 8.0, test_btn_w, 24.0),
                title=t("hangar_subcat_test_btn"),
                bg_color=Theme.MAUVE,
                text_color=Theme.CRUST,
                border_color=None,
                corner_radius=5.0,
                font_size=10.0,
                bold=True,
            )
            flight_test_btn.setIdentifier_(cur_subcat)
            flight_test_btn.setTarget_(self)
            flight_test_btn.setAction_("onTestSubcatFlight:")
            sim_frame.addSubview_(flight_test_btn)

            popup_w = 215.0
            popup_x = test_btn_x - 8.0 - popup_w
            sub_m_popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(
                AppKit.NSMakeRect(popup_x, 8.0, popup_w, 24.0), False
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
            sim_frame.addSubview_(sub_m_popup)

            lbl_w = 140.0
            lbl_x = popup_x - 6.0 - lbl_w
            sub_m_lbl = AppKit.NSTextField.alloc().initWithFrame_(
                AppKit.NSMakeRect(lbl_x, 11.0, lbl_w, 18.0)
            )
            sub_m_lbl.setStringValue_(t("hangar_subcat_mascot_label"))
            sub_m_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(10.5))
            sub_m_lbl.setTextColor_(Theme.SUBTEXT0)
            sub_m_lbl.setAlignment_(AppKit.NSTextAlignmentRight)
            sub_m_lbl.setBezeled_(False)
            sub_m_lbl.setDrawsBackground_(False)
            sub_m_lbl.setEditable_(False)
            sub_m_lbl.setUsesSingleLineMode_(True)
            sim_frame.addSubview_(sub_m_lbl)

            # Mockup Banner Card (x=10, y=40, width=sim_dw-20, height=76)
            mockup_box_w = sim_dw - 20.0
            mockup_box_h = 76.0
            mockup_box = FlippedView.alloc().initWithFrame_(
                AppKit.NSMakeRect(10.0, 40.0, mockup_box_w, mockup_box_h)
            )
            mockup_box.setWantsLayer_(True)
            mockup_box.layer().setBackgroundColor_(Theme.CRUST.CGColor())
            mockup_box.layer().setCornerRadius_(8.0)
            mockup_box.layer().setBorderWidth_(1.0)
            mockup_box.layer().setBorderColor_(Theme.SURFACE0.CGColor())
            sim_frame.addSubview_(mockup_box)

            # Live Mini Mascot inside mockup card (68x60, centered at y=8)
            sc_pilot_animal = subcat_animal if (subcat_animal and subcat_animal != cur_animal) else cur_animal
            sim_mini = MascotMiniCanvasView.alloc().initWithFrame_animal_outfit_(
                AppKit.NSMakeRect(10.0, 8.0, 68.0, 60.0), sc_pilot_animal, "student"
            )
            sim_mini.setCustomCornerRadius_(8.0)
            sim_mini.setBgColor_(Theme.CRUST)
            sim_mini.setAccentColor_(Theme.MAUVE)
            self.mini_canvases["study_sim"] = sim_mini
            mockup_box.addSubview_(sim_mini)

            # Mockup Action Button on Right
            mockup_btn_texts = {
                "study": t("hangar_subcat_sim_study_btn"),
                "class": t("hangar_subcat_sim_class_btn"),
                "exam": t("hangar_subcat_sim_exam_btn"),
            }
            subcat_btn_colors = {
                "study": Theme.YELLOW,
                "class": Theme.BLUE,
                "exam": Theme.RED,
            }
            btn_bg = subcat_btn_colors.get(cur_subcat, Theme.MAUVE)
            btn_title = mockup_btn_texts.get(cur_subcat, t("hangar_subcat_sim_study_btn"))
            btn_font = AppKit.NSFont.boldSystemFontOfSize_(11.0)
            text_size = AppKit.NSString.stringWithString_(btn_title).sizeWithAttributes_({AppKit.NSFontAttributeName: btn_font})
            action_btn_w = max(135.0, math.ceil(text_size.width) + 24.0)
            action_btn_h = 32.0
            action_btn_x = mockup_box_w - 12.0 - action_btn_w
            action_btn_y = (mockup_box_h - action_btn_h) / 2.0  # 22.0

            mockup_action_btn = Theme.create_button(
                AppKit.NSMakeRect(action_btn_x, action_btn_y, action_btn_w, action_btn_h),
                title=btn_title,
                bg_color=btn_bg,
                text_color=Theme.CRUST,
                border_color=None,
                corner_radius=6.0,
                font_size=11.0,
                bold=True,
            )
            mockup_action_btn.setIdentifier_(cur_subcat)
            mockup_action_btn.setTarget_(self)
            mockup_action_btn.setAction_("onTestSubcatFlight:")
            mockup_box.addSubview_(mockup_action_btn)

            # Middle Information Column: Title + Badges
            info_x = 88.0
            info_w = max(140.0, action_btn_x - info_x - 12.0)
            mockup_titles = {
                "study": t("hangar_subcat_sim_study_title"),
                "class": t("hangar_subcat_sim_class_title"),
                "exam": t("hangar_subcat_sim_exam_title"),
            }
            m_title_lbl = AppKit.NSTextField.alloc().initWithFrame_(
                AppKit.NSMakeRect(info_x, 14.0, info_w, 18.0)
            )
            m_title_lbl.setStringValue_(mockup_titles.get(cur_subcat, t("hangar_subcat_sim_study_title")))
            m_title_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.5))
            m_title_lbl.setTextColor_(Theme.TEXT)
            m_title_lbl.setBezeled_(False)
            m_title_lbl.setDrawsBackground_(False)
            m_title_lbl.setEditable_(False)
            m_title_lbl.setUsesSingleLineMode_(True)
            mockup_box.addSubview_(m_title_lbl)

            # Badges Row
            badge_specs = {
                "study": [
                    (t("hangar_subcat_sim_study_badge1"), Theme.YELLOW),
                    (t("hangar_subcat_sim_study_badge2"), Theme.BLUE),
                    (t("hangar_subcat_sim_in_10m"), Theme.PEACH),
                ],
                "class": [
                    (t("hangar_subcat_sim_class_badge1"), Theme.GREEN),
                    (t("hangar_subcat_sim_class_badge2"), Theme.BLUE),
                    (t("hangar_subcat_sim_in_10m"), Theme.PEACH),
                ],
                "exam": [
                    (t("hangar_subcat_sim_exam_badge1"), Theme.RED),
                    (t("hangar_subcat_sim_exam_badge2"), Theme.YELLOW),
                    (t("hangar_subcat_sim_in_10m"), Theme.PEACH),
                ],
            }.get(cur_subcat, [])

            bx = info_x
            b_font = AppKit.NSFont.boldSystemFontOfSize_(9.5)
            for b_txt, b_color in badge_specs:
                b_str_w = AppKit.NSString.stringWithString_(b_txt).sizeWithAttributes_({AppKit.NSFontAttributeName: b_font}).width
                b_w = math.ceil(b_str_w) + 16.0
                b_view = FlippedView.alloc().initWithFrame_(AppKit.NSMakeRect(bx, 40.0, b_w, 20.0))
                b_view.setWantsLayer_(True)
                b_view.layer().setBackgroundColor_(b_color.colorWithAlphaComponent_(0.15).CGColor())
                b_view.layer().setBorderWidth_(1.0)
                b_view.layer().setBorderColor_(b_color.colorWithAlphaComponent_(0.45).CGColor())
                b_view.layer().setCornerRadius_(4.0)

                b_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(0, 2.0, b_w, 16.0))
                b_lbl.setStringValue_(b_txt)
                b_lbl.setFont_(b_font)
                b_lbl.setTextColor_(b_color)
                b_lbl.setAlignment_(AppKit.NSTextAlignmentCenter)
                b_lbl.setBezeled_(False)
                b_lbl.setDrawsBackground_(False)
                b_lbl.setEditable_(False)
                b_lbl.setUsesSingleLineMode_(True)
                b_view.addSubview_(b_lbl)
                mockup_box.addSubview_(b_view)
                bx += b_w + 6.0

            # Subcategory Keywords Section Header
            subcat_name_map = {
                "study": t("hangar_subcat_study"),
                "class": t("hangar_subcat_class"),
                "exam": t("hangar_subcat_exam"),
            }
            kw_head_lbl = AppKit.NSTextField.alloc().initWithFrame_(
                AppKit.NSMakeRect(18.0, 206.0, sim_dw, 18.0)
            )
            kw_head_lbl.setStringValue_(t("hangar_subcat_keywords_heading", subcat=subcat_name_map.get(cur_subcat, "")))
            kw_head_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(11.0))
            kw_head_lbl.setTextColor_(Theme.SUBTEXT1)
            kw_head_lbl.setBezeled_(False)
            kw_head_lbl.setDrawsBackground_(False)
            kw_head_lbl.setEditable_(False)
            drawer_view.addSubview_(kw_head_lbl)

            deck_y = 230.0
        else:
            # Drawer Guidance Subtitle for standard categories
            guide_lbl = AppKit.NSTextField.alloc().initWithFrame_(
                AppKit.NSMakeRect(18.0, 10.0, w - 36.0, 18.0)
            )
            guide_lbl.setStringValue_(t("hangar_keywords_drawer_subtitle"))
            guide_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(10.5))
            guide_lbl.setTextColor_(Theme.SUBTEXT0)
            guide_lbl.setBezeled_(False)
            guide_lbl.setDrawsBackground_(False)
            guide_lbl.setEditable_(False)
            drawer_view.addSubview_(guide_lbl)

            deck_y = 34.0

        # ── Build Dual-Tier Omni Deck ──
        self._build_dual_tier_deck(cat_key, target_k, is_preset_open, w, deck_y, deck_h, drawer_view)
        self._render_category_keywords(cat_key)
        return card

    @objc.python_method
    def _build_dual_tier_deck(self, cat_key, target_k, is_preset_open, w, deck_y, deck_h, drawer_view):
        dw = w - 36.0
        deck_frame = FlippedView.alloc().initWithFrame_(AppKit.NSMakeRect(18.0, deck_y, dw, deck_h))
        deck_frame.setWantsLayer_(True)
        deck_frame.layer().setBackgroundColor_(Theme.MANTLE.CGColor())
        deck_frame.layer().setCornerRadius_(10.0)
        deck_frame.layer().setBorderWidth_(1.0)
        deck_frame.layer().setBorderColor_(Theme.SURFACE1.CGColor())
        drawer_view.addSubview_(deck_frame)

        # 1. Top Omni-Adder Bar
        hide_w = 72.0
        rst_w = 155.0
        add_w = 150.0

        hide_x = dw - 12.0 - hide_w
        rst_x = hide_x - 8.0 - rst_w
        add_x = rst_x - 8.0 - add_w
        kw_input_w = max(120.0, add_x - 8.0 - 12.0)

        kw_input = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(12.0, 10.0, kw_input_w, 30.0)
        )
        kw_input.setPlaceholderString_(t("hangar_keywords_add_placeholder_custom"))
        kw_input.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
        kw_input.setTextColor_(Theme.TEXT)
        kw_input.setWantsLayer_(True)
        kw_input.layer().setCornerRadius_(6.0)
        kw_input.setBackgroundColor_(Theme.CRUST)
        kw_input.setDrawsBackground_(True)
        kw_input.layer().setBorderWidth_(1.0)
        kw_input.layer().setBorderColor_(Theme.SURFACE1.CGColor())
        kw_input.setFocusRingType_(AppKit.NSFocusRingTypeNone)
        kw_input.setIdentifier_(cat_key)
        kw_input.setTarget_(self)
        kw_input.setAction_("onAddCategoryKeyword:")
        self.kw_inputs[cat_key] = kw_input
        deck_frame.addSubview_(kw_input)

        add_btn = Theme.create_button(
            AppKit.NSMakeRect(add_x, 10.0, add_w, 30.0),
            title=t("hangar_keywords_add_custom_btn"),
            bg_color=Theme.MAUVE,
            text_color=Theme.CRUST,
            border_color=None,
            corner_radius=6.0,
            font_size=11.0,
            bold=True,
        )
        add_btn.setIdentifier_(cat_key)
        add_btn.setTarget_(self)
        add_btn.setAction_("onAddCategoryKeyword:")
        deck_frame.addSubview_(add_btn)

        rst_btn = Theme.create_button(
            AppKit.NSMakeRect(rst_x, 10.0, rst_w, 30.0),
            title=t("hangar_keywords_reset_to_defaults"),
            bg_color=Theme.SURFACE0,
            text_color=Theme.SUBTEXT1,
            border_color=Theme.SURFACE1,
            corner_radius=6.0,
            font_size=11.0,
            bold=False,
        )
        rst_btn.setIdentifier_(cat_key)
        rst_btn.setTarget_(self)
        rst_btn.setAction_("onResetCategoryKeywords:")
        deck_frame.addSubview_(rst_btn)

        hide_btn = Theme.create_button(
            AppKit.NSMakeRect(hide_x, 10.0, hide_w, 30.0),
            title=t("hangar_keywords_drawer_hide"),
            bg_color=Theme.MANTLE,
            text_color=Theme.SUBTEXT1,
            border_color=Theme.SURFACE1,
            corner_radius=6.0,
            font_size=11.0,
            bold=False,
        )
        hide_btn.setIdentifier_(cat_key)
        hide_btn.setTarget_(self)
        hide_btn.setAction_("onToggleKeywordsDrawer:")
        deck_frame.addSubview_(hide_btn)

        # 2. Tier 1: Custom Triggers Section
        c_head_lbl = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(12.0, 48.0, 180.0, 18.0)
        )
        c_head_lbl.setStringValue_(t("hangar_keywords_custom_title"))
        c_head_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(11.5))
        c_head_lbl.setTextColor_(Theme.MAUVE)
        c_head_lbl.setBezeled_(False)
        c_head_lbl.setDrawsBackground_(False)
        c_head_lbl.setEditable_(False)
        title_w = AppKit.NSString.stringWithString_(t("hangar_keywords_custom_title")).sizeWithAttributes_(
            {AppKit.NSFontAttributeName: c_head_lbl.font()}
        ).width + 6.0
        c_head_lbl.setFrame_(AppKit.NSMakeRect(12.0, 48.0, title_w, 18.0))
        deck_frame.addSubview_(c_head_lbl)

        c_cnt_lbl = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(12.0 + title_w + 8.0, 48.0, 90.0, 18.0)
        )
        c_cnt_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(10.0))
        c_cnt_lbl.setTextColor_(Theme.MAUVE)
        c_cnt_lbl.setBezeled_(False)
        c_cnt_lbl.setDrawsBackground_(True)
        c_cnt_lbl.setBackgroundColor_(Theme.MAUVE.colorWithAlphaComponent_(0.15))
        c_cnt_lbl.setWantsLayer_(True)
        c_cnt_lbl.layer().setCornerRadius_(4.0)
        c_cnt_lbl.setEditable_(False)
        self.custom_cnt_labels[cat_key] = c_cnt_lbl
        deck_frame.addSubview_(c_cnt_lbl)

        custom_box = AppKit.NSScrollView.alloc().initWithFrame_(
            AppKit.NSMakeRect(12.0, 70.0, dw - 24.0, 54.0)
        )
        custom_box.setBorderType_(AppKit.NSNoBorder)
        custom_box.setWantsLayer_(True)
        custom_box.layer().setBackgroundColor_(Theme.CRUST.CGColor())
        custom_box.layer().setBorderWidth_(1.0)
        custom_box.layer().setBorderColor_(Theme.MAUVE.colorWithAlphaComponent_(0.25).CGColor())
        custom_box.layer().setCornerRadius_(8.0)
        custom_box.setDrawsBackground_(False)
        custom_box.setHasVerticalScroller_(True)
        custom_box.setAutohidesScrollers_(True)

        custom_doc = FlippedView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, dw - 24.0, 54.0))
        custom_box.setDocumentView_(custom_doc)
        deck_frame.addSubview_(custom_box)
        self.custom_doc_views[cat_key] = custom_doc
        self.custom_scrolls[cat_key] = custom_box

        # 3. Tier 2: Built-in Core Presets Toggle & Section
        all_kws_init = config.get_custom_keywords(target_k)
        def_kws_init = config.get_default_keywords(target_k)
        def_set_init = {d.strip().lower() for d in def_kws_init}
        init_preset_cnt = len([k for k in all_kws_init if k.strip().lower() in def_set_init])
        preset_title = t(
            "hangar_keywords_presets_toggle_hide" if is_preset_open else "hangar_keywords_presets_toggle_show",
            count=init_preset_cnt,
        )
        preset_toggle_btn = Theme.create_button(
            AppKit.NSMakeRect(12.0, 132.0, min(dw - 24.0, 390.0), 28.0),
            title=preset_title,
            bg_color=Theme.SURFACE0,
            text_color=Theme.SUBTEXT1,
            border_color=Theme.SURFACE1,
            corner_radius=6.0,
            font_size=11.0,
            bold=True,
        )
        preset_toggle_btn.setIdentifier_(cat_key)
        preset_toggle_btn.setTarget_(self)
        preset_toggle_btn.setAction_("onTogglePresets:")
        self.preset_toggle_buttons[cat_key] = preset_toggle_btn
        deck_frame.addSubview_(preset_toggle_btn)

        if is_preset_open:
            preset_scroll = AppKit.NSScrollView.alloc().initWithFrame_(
                AppKit.NSMakeRect(12.0, 168.0, dw - 24.0, 115.0)
            )
            preset_scroll.setBorderType_(AppKit.NSNoBorder)
            preset_scroll.setWantsLayer_(True)
            preset_scroll.layer().setBackgroundColor_(Theme.CRUST.CGColor())
            preset_scroll.layer().setBorderWidth_(1.0)
            preset_scroll.layer().setBorderColor_(Theme.SURFACE1.CGColor())
            preset_scroll.layer().setCornerRadius_(8.0)
            preset_scroll.setDrawsBackground_(False)
            preset_scroll.setHasVerticalScroller_(True)
            preset_scroll.setAutohidesScrollers_(True)

            preset_doc = FlippedView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, dw - 24.0, 115.0))
            preset_scroll.setDocumentView_(preset_doc)
            deck_frame.addSubview_(preset_scroll)
            self.preset_doc_views[cat_key] = preset_doc
            self.preset_scrolls[cat_key] = preset_scroll

    @objc.python_method
    def _layout_pills(self, doc_view, scroll_view, keywords, is_custom, target_k, min_h):
        for sub in list(doc_view.subviews()):
            sub.removeFromSuperview()

        max_w = scroll_view.frame().size.width
        content_max_w = max_w - 14.0
        chip_h = 24.0
        gap_x = 6.0
        gap_y = 6.0
        margin_x = 8.0
        margin_y = 8.0

        if not keywords and is_custom:
            empty_lbl = AppKit.NSTextField.alloc().initWithFrame_(
                AppKit.NSMakeRect(10.0, 16.0, content_max_w - 20.0, 20.0)
            )
            empty_lbl.setStringValue_(t("hangar_keywords_custom_empty"))
            empty_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(10.5))
            empty_lbl.setTextColor_(Theme.OVERLAY0)
            empty_lbl.setBezeled_(False)
            empty_lbl.setDrawsBackground_(False)
            empty_lbl.setEditable_(False)
            doc_view.addSubview_(empty_lbl)
            doc_view.setFrame_(AppKit.NSMakeRect(0, 0, max_w, min_h))
            return

        font = (
            AppKit.NSFont.boldSystemFontOfSize_(10.5)
            if is_custom
            else AppKit.NSFont.systemFontOfSize_weight_(10.5, AppKit.NSFontWeightMedium)
        )

        calc_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, 1000, 24))
        calc_lbl.setFont_(font)
        calc_lbl.cell().setWraps_(False)
        calc_lbl.setUsesSingleLineMode_(True)

        cur_x = margin_x
        cur_y = margin_y

        for kw in keywords:
            display_text = f"✨ {kw}" if is_custom else kw
            calc_lbl.setStringValue_(display_text)
            text_w = math.ceil(calc_lbl.cell().cellSize().width)
            chip_w = max(48.0, text_w + 32.0)

            if cur_x + chip_w > content_max_w and cur_x > margin_x:
                cur_x = margin_x
                cur_y += chip_h + gap_y

            chip = KeywordChipView.create(
                cur_x,
                cur_y,
                chip_w,
                chip_h,
                text=kw,
                is_custom=is_custom,
                target=self,
                action="onRemoveCategoryKeyword:",
                tooltip=f"{target_k}:::{kw}",
            )
            doc_view.addSubview_(chip)
            cur_x += chip_w + gap_x

        total_h = cur_y + chip_h + margin_y
        doc_view.setFrame_(AppKit.NSMakeRect(0, 0, max_w, max(min_h, total_h)))

    @objc.python_method
    def _render_category_keywords(self, cat_key: str):
        target_k = getattr(self, "active_study_subcat", "study") if cat_key == "study" else cat_key
        all_kws = config.get_custom_keywords(target_k)
        default_kws = config.get_default_keywords(target_k)
        default_set = {d.strip().lower() for d in default_kws}

        custom_kws = [k for k in all_kws if k.strip().lower() not in default_set]
        preset_kws = [k for k in all_kws if k.strip().lower() in default_set]

        # 1. Update Card Toggle Button title
        if cat_key in self.kw_toggle_buttons:
            is_exp = cat_key in self.expanded_categories
            if cat_key == "study":
                total_cnt = (
                    len(config.get_custom_keywords("study"))
                    + len(config.get_custom_keywords("class"))
                    + len(config.get_custom_keywords("exam"))
                )
            else:
                total_cnt = len(all_kws)
            self.kw_toggle_buttons[cat_key].setTitle_(
                t(
                    "hangar_keywords_toggle_btn_open" if is_exp else "hangar_keywords_toggle_btn",
                    count=total_cnt,
                )
            )

        # 2. Update Custom Count badge
        if cat_key in self.custom_cnt_labels:
            c_cnt_lbl = self.custom_cnt_labels[cat_key]
            badge_text = t("hangar_keywords_custom_active", count=len(custom_kws))
            c_cnt_lbl.setStringValue_(f" {badge_text} ")
            str_obj = AppKit.NSString.stringWithString_(f" {badge_text} ")
            b_w = str_obj.sizeWithAttributes_({AppKit.NSFontAttributeName: c_cnt_lbl.font()}).width + 8.0
            cur_f = c_cnt_lbl.frame()
            c_cnt_lbl.setFrame_(AppKit.NSMakeRect(cur_f.origin.x, cur_f.origin.y, b_w, cur_f.size.height))

        # 3. Update Custom Doc View
        custom_doc = self.custom_doc_views.get(cat_key)
        custom_scroll = self.custom_scrolls.get(cat_key)
        if custom_doc and custom_scroll:
            self._layout_pills(custom_doc, custom_scroll, custom_kws, is_custom=True, target_k=target_k, min_h=54.0)

        # 4. Update Preset Toggle Button
        is_preset_open = target_k in self.expanded_presets
        if cat_key in self.preset_toggle_buttons:
            btn_title = t(
                "hangar_keywords_presets_toggle_hide" if is_preset_open else "hangar_keywords_presets_toggle_show",
                count=len(preset_kws),
            )
            self.preset_toggle_buttons[cat_key].setTitle_(btn_title)

        # 5. Update Preset Doc View
        preset_doc = self.preset_doc_views.get(cat_key)
        preset_scroll = self.preset_scrolls.get(cat_key)
        if preset_doc and preset_scroll:
            self._layout_pills(preset_doc, preset_scroll, preset_kws, is_custom=False, target_k=target_k, min_h=115.0)

    @objc.IBAction
    def onTogglePresets_(self, sender):
        cat_key = str(sender.identifier())
        target_k = getattr(self, "active_study_subcat", "study") if cat_key == "study" else cat_key
        if not hasattr(self, "expanded_presets") or self.expanded_presets is None:
            self.expanded_presets = set()

        if self._cached_view and self._cached_view.contentView() and self._cached_view.documentView():
            old_doc_h = self._cached_view.documentView().frame().size.height
            clip_y = self._cached_view.contentView().bounds().origin.y
            clip_h = self._cached_view.contentView().bounds().size.height
            self._saved_dist_from_top = max(0.0, old_doc_h - (clip_y + clip_h))

        if target_k in self.expanded_presets:
            self.expanded_presets.remove(target_k)
        else:
            self.expanded_presets.add(target_k)
        self.invalidate_cache()
        if self.dashboard_controller and hasattr(self.dashboard_controller, "refresh_current_tab"):
            self.dashboard_controller.refresh_current_tab()

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
        if self._cached_view and self._cached_view.contentView() and self._cached_view.documentView():
            old_doc_h = self._cached_view.documentView().frame().size.height
            clip_y = self._cached_view.contentView().bounds().origin.y
            clip_h = self._cached_view.contentView().bounds().size.height
            self._saved_dist_from_top = max(0.0, old_doc_h - (clip_y + clip_h))
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
            selected_outfit = "agent" if sel_animal == "platypus" else fixed_outfit
            customs[cat_key] = {"animal": sel_animal, "outfit": selected_outfit, "accessories": list(normalize_accessories(selected_outfit, animal=sel_animal))}
        else:
            customs[cat_key]["animal"] = sel_animal
            selected_outfit = "agent" if sel_animal == "platypus" else fixed_outfit
            customs[cat_key]["outfit"] = selected_outfit
            customs[cat_key]["accessories"] = list(normalize_accessories(selected_outfit, animal=sel_animal))

        if cat_key == "study":
            for sub in ("class", "exam"):
                if sub not in customs or not isinstance(customs[sub], dict):
                    customs[sub] = {"animal": sel_animal, "outfit": "student"}

        config.set("mascot_customization", customs)
        event_bus.publish("CONFIG_CHANGED", key="mascot_customization", value=customs)

        # Instant Live Preview Update for this card
        active_outfit = "agent" if sel_animal == "platypus" else fixed_outfit
        if cat_key in self.mini_canvases:
            self.mini_canvases[cat_key].updateAnimal_(sel_animal)
            self.mini_canvases[cat_key].updateOutfit_(active_outfit)
        if cat_key in self.subtitle_labels:
            lbl, desc, outfit = self.subtitle_labels[cat_key]
            lbl.setStringValue_(f"{desc}\n✨ Active Pilot: {get_combo_title(sel_animal, active_outfit)}")

        self.invalidate_cache()
        self.start_animation_timer()

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
            "food": {"animal": "squirrel", "outfit": "chef"},
            "travel": {"animal": "duck", "outfit": "captain"},
            "sport": {"animal": "bunny", "outfit": "gym"},
            "in_person": {"animal": "fox", "outfit": "racer"},
            "health": {"animal": "panda", "outfit": "zen"},
            "work": {"animal": "penguin", "outfit": "agent"},
            "concert": {"animal": "fox", "outfit": "aviator"},
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
        outfit = "agent" if animal == "platypus" else fixed_outfit

        titles = {
            "study": "Neural Networks & AI University Lecture",
            "food": "Dinner with Friends at Pizzeria",
            "travel": "Flight BA 257 to London Heathrow",
            "sport": "CrossFit & Palestra Workout Session",
            "in_person": "Architectural Studio Consultation",
            "health": "Serenis Mindfulness & Yoga Session",
            "work": "Executive Board Strategy & Sprint Review",
            "concert": "Rock Arena Live World Tour Concert",
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
            "is_travel": cat_key in ("food", "travel", "sport", "in_person", "concert"),
            "is_test_banner": True,
            "is_late": False
        })
