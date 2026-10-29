#!/usr/bin/env python3
"""Окно студии «Олеся»: вход, роли, заявки, занятия, костюмерная и опыт ученика."""

import os
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Adw, Gdk, GdkPixbuf, Gtk, Pango

from olesya import db, matching

ROLE_ORDER = db.ROLES
STYLE_TONE = {
    "ballet": "ol-ballet",
    "contemporary": "ol-contemporary",
    "hiphop": "ol-hiphop",
    "latin": "ol-latin",
    "ballroom": "ol-ballroom",
    "kids": "ol-kids",
    "other": "ol-plum",
}
CSS = """
@define-color accent_bg_color #b44862;
@define-color accent_fg_color #ffffff;
@define-color accent_color #9a3450;
@define-color window_bg_color #f6f3f1;
@define-color window_fg_color #2a2428;
@define-color view_bg_color #f6f3f1;
@define-color view_fg_color #2a2428;
@define-color card_bg_color #ffffff;
@define-color card_fg_color #2a2428;
@define-color headerbar_bg_color #fffcfb;
@define-color headerbar_fg_color #2a2428;
@define-color popover_bg_color #ffffff;
@define-color popover_fg_color #2a2428;
@define-color dialog_bg_color #ffffff;
@define-color dialog_fg_color #2a2428;

.ol-error { color: #9a3450; font-weight: 600; }

.ol-titlebar {
  background: #fffcfb;
  color: #2a2428;
  box-shadow: none;
  border-bottom: 1px solid rgba(42, 36, 40, 0.08);
}
.ol-titlebar label { color: #2a2428; }
.ol-heading { font-weight: 700; }
.ol-app { background: #f6f3f1; }

.ol-top {
  background: #fffcfb;
  border-bottom: 1px solid rgba(42, 36, 40, 0.08);
  padding: 10px 16px 12px;
}
.ol-brand { }
.ol-wordmark {
  font-size: 20px;
  font-weight: 700;
  color: #2a2428;
}
.ol-tagline {
  font-size: 12px;
  font-weight: 600;
  color: #b44862;
}
.ol-role {
  background: #f8e8ed;
  border-radius: 12px;
  padding: 6px 12px;
}
.ol-role-name {
  font-size: 13px;
  font-weight: 700;
  color: #2a2428;
}
.ol-role-meta {
  font-size: 12px;
  color: #6f656b;
}
.ol-navrow { background: transparent; }
.ol-navrow flowboxchild { background: transparent; padding: 2px; }
.ol-nav {
  border-radius: 999px;
  padding: 6px 14px;
  background: transparent;
  font-weight: 600;
}
.ol-nav label { color: #2a2428; }
.ol-nav:hover { background: rgba(180, 72, 98, 0.08); }
.ol-nav:checked { background: #f8e8ed; }
.ol-nav:checked label { color: #9a3450; font-weight: 700; }
.ol-quiet {
  background: transparent;
  color: #2a2428;
  border-radius: 10px;
  border: 1px solid rgba(42, 36, 40, 0.16);
  padding: 6px 12px;
}
.ol-quiet label { color: #2a2428; }

.ol-content { background: #f6f3f1; }
.ol-head { padding: 16px 24px 4px; }
.ol-kicker {
  font-size: 13px;
  font-weight: 600;
  color: #b44862;
}
.ol-display {
  font-size: 26px;
  font-weight: 700;
  color: #2a2428;
}
.ol-meta { color: #6f656b; }

.ol-strips { background: transparent; }
.ol-strips row {
  background: #ffffff;
  border-radius: 12px;
  margin-bottom: 8px;
  border: 1px solid rgba(42, 36, 40, 0.08);
}
.ol-strips row:selected { background: #f8e8ed; }
.ol-strip { padding: 12px 14px; }
.ol-strip-title {
  font-size: 15px;
  font-weight: 700;
  color: #2a2428;
}
.ol-stamp {
  background: #f8e8ed;
  color: #9a3450;
  border-radius: 10px;
  font-weight: 700;
  min-width: 46px;
  padding: 8px 4px;
}
.ol-pill {
  background: #f8e8ed;
  color: #9a3450;
  border-radius: 999px;
  padding: 4px 10px;
  font-weight: 600;
  font-size: 12px;
}

.ol-board { background: transparent; }
flowboxchild { background: transparent; padding: 4px; }
.ol-card {
  background: #ffffff;
  border-radius: 14px;
  border: 1px solid rgba(42, 36, 40, 0.08);
}
.ol-band { padding: 12px 14px 10px; border-radius: 14px 14px 0 0; }
.ol-band label { color: #2a2428; }
.ol-card-title {
  font-size: 17px;
  font-weight: 700;
  color: #2a2428;
}
.ol-card-body { padding: 12px 14px 14px; }
.ol-price {
  font-size: 16px;
  font-weight: 700;
  color: #9a3450;
}
.ol-ballet { background: #f6d5e0; }
.ol-contemporary { background: #d7efe8; }
.ol-hiphop { background: #f8e0d0; }
.ol-latin { background: #f8d0d6; }
.ol-ballroom { background: #d9e6f5; }
.ol-kids { background: #f8ecc8; }
.ol-plum { background: #ece6ea; }

.ol-stat {
  background: #ffffff;
  border-radius: 14px;
  padding: 14px 16px;
  border: 1px solid rgba(42, 36, 40, 0.08);
}
.ol-stat-num {
  font-size: 26px;
  font-weight: 700;
  color: #2a2428;
}
.ol-stat-cap {
  font-size: 12px;
  font-weight: 600;
  color: #b44862;
}
.ol-person {
  background: #ffffff;
  border-radius: 12px;
  padding: 10px 12px;
  border: 1px solid rgba(42, 36, 40, 0.08);
}
.ol-panel {
  background: #ffffff;
  border-radius: 14px;
  padding: 16px 18px;
  border: 1px solid rgba(42, 36, 40, 0.08);
}

.ol-rank-name {
  font-size: 24px;
  font-weight: 700;
  color: #2a2428;
}
.ol-xp-num {
  font-size: 26px;
  font-weight: 700;
  color: #b44862;
}
.ol-badge {
  background: #ffffff;
  border-radius: 12px;
  padding: 10px 12px;
  border: 1px solid rgba(42, 36, 40, 0.08);
}
.ol-badge.locked { opacity: 0.55; }
.ol-badge-title {
  font-size: 14px;
  font-weight: 700;
  color: #2a2428;
}
.ol-badge-detail { color: #6f656b; font-size: 12px; }
.ol-bonus { color: #9a6b2f; font-weight: 700; }

.ol-login-bg {
  background-image: linear-gradient(165deg, #fbf7f5 0%, #f8e8ed 48%, #f3efe6 100%);
}
.ol-login-card {
  background: #ffffff;
  border-radius: 18px;
  padding: 26px 26px 24px;
  border: 1px solid rgba(42, 36, 40, 0.08);
  box-shadow: 0 16px 40px rgba(42, 36, 40, 0.08);
}
.ol-seg {
  background: transparent;
  border-radius: 999px;
  padding: 6px 14px;
  font-weight: 600;
}
.ol-seg label { color: #6f656b; }
.ol-seg:checked { background: #f8e8ed; }
.ol-seg:checked label { color: #9a3450; }
.ol-scroll-card {
  background: #ffffff;
  border-radius: 10px;
  border: 1px solid rgba(42, 36, 40, 0.08);
}
"""


def asset_path(name):
    roots = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(meipass)
    roots.append(os.path.dirname(os.path.abspath(__file__)))
    for root in roots:
        path = os.path.join(root, "assets", name)
        if os.path.exists(path):
            return path
    return os.path.join(roots[-1], "assets", name)


def logo_paintable(size):
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(asset_path("logo.png"), size, size)
    return Gdk.Texture.new_for_pixbuf(pixbuf)


def logo_image(size):
    image = Gtk.Image.new_from_paintable(logo_paintable(size))
    image.set_pixel_size(size)
    image.set_valign(Gtk.Align.CENTER)
    return image


def alert(parent, heading, body=""):
    dialog = Adw.AlertDialog(heading=heading)
    if body:
        dialog.set_body(body)
        dialog.set_prefer_wide_layout(True)
    dialog.add_response("ok", "Понятно")
    dialog.set_default_response("ok")
    dialog.present(parent)


def confirm(parent, heading, body, on_yes):
    dialog = Adw.AlertDialog(heading=heading, body=body)
    dialog.add_response("cancel", "Отмена")
    dialog.add_response("yes", "Да")
    dialog.set_response_appearance("yes", Adw.ResponseAppearance.DESTRUCTIVE)
    dialog.set_default_response("cancel")
    dialog.set_close_response("cancel")

    def on_response(_dialog, response):
        if response == "yes":
            on_yes()

    dialog.connect("response", on_response)
    dialog.present(parent)


def money(value):
    return f"{int(value):,}".replace(",", " ") + " ₽"


def rating_text(count, average):
    if not count:
        return "нет оценок"
    return f"{float(average):.1f}"


def selected_index(widget, count):
    index = widget.get_selected()
    if index is None or int(index) >= count:
        return 0
    return int(index)


def scrolled(child):
    widget = Gtk.ScrolledWindow()
    widget.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    widget.set_vexpand(True)
    widget.set_hexpand(True)
    widget.set_child(child)
    return widget


def field_label(text):
    label = Gtk.Label(label=text, xalign=0)
    label.add_css_class("dim-label")
    return label


def text_view(min_height=120):
    view = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR, accepts_tab=False)
    view.set_left_margin(8)
    view.set_right_margin(8)
    view.set_top_margin(6)
    view.set_bottom_margin(6)
    scroll = Gtk.ScrolledWindow(min_content_height=min_height)
    scroll.set_child(view)
    scroll.add_css_class("ol-scroll-card")
    return view, scroll


def text_of(view):
    buffer = view.get_buffer()
    return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)


def int_spin(lower, upper, value, step=1):
    button = Gtk.SpinButton.new_with_range(lower, upper, step)
    button.set_digits(0)
    button.set_numeric(True)
    button.set_value(value)
    return button


def clear_box(box):
    child = box.get_first_child()
    while child is not None:
        nxt = child.get_next_sibling()
        box.remove(child)
        child = nxt


def card_label(text):
    label = Gtk.Label(label=text, xalign=0, yalign=0, wrap=True, selectable=True)
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    card.add_css_class("ol-card-body")
    card.append(label)
    return card, label


def meta_box(rows):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    for text in rows:
        label = Gtk.Label(label=text, xalign=0, wrap=True, selectable=True)
        box.append(label)
    return box


def _row_stamp(values):
    for item in values[2:-1]:
        text = str(item)
        if len(text) >= 10 and text[4:5] == "-" and text[7:8] == "-":
            return f"{text[8:10]}.{text[5:7]}"
    parts = [part[0] for part in str(values[1]).replace("«", "").replace("»", "").split() if part[:1].isalpha()]
    letters = "".join(parts[:2]).upper()
    return letters or "•"


class StripRow(Gtk.ListBoxRow):
    def __init__(self, values):
        super().__init__()
        self.values = tuple(values)
        self.record_id = values[0]
        box = Gtk.Box(spacing=12)
        box.add_css_class("ol-strip")
        stamp = Gtk.Label(label=_row_stamp(self.values))
        stamp.add_css_class("ol-stamp")
        stamp.set_valign(Gtk.Align.CENTER)
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)
        title = Gtk.Label(label=str(values[1]), xalign=0, ellipsize=Pango.EllipsizeMode.END)
        title.add_css_class("ol-strip-title")
        meta_parts = [str(item) for item in values[2:-1] if str(item) not in ("", "—")]
        meta = Gtk.Label(label="  ·  ".join(meta_parts), xalign=0, ellipsize=Pango.EllipsizeMode.END)
        meta.add_css_class("ol-meta")
        pill = Gtk.Label(label=str(values[-1]))
        pill.add_css_class("ol-pill")
        pill.set_valign(Gtk.Align.CENTER)
        text.append(title)
        if meta_parts:
            text.append(meta)
        box.append(stamp)
        box.append(text)
        box.append(pill)
        self.set_child(box)


class LabeledDrop(Gtk.DropDown):
    def __init__(self, pairs):
        self._ids = [key for key, _label in pairs]
        labels = [label for _key, label in pairs]
        super().__init__(model=Gtk.StringList.new(labels or ["—"]))
        self.set_selected(0)

    def value(self):
        if not self._ids:
            return None
        index = self.get_selected()
        if index is None or int(index) >= len(self._ids):
            return self._ids[0]
        return self._ids[int(index)]

    def set_value(self, key):
        if key in self._ids:
            self.set_selected(self._ids.index(key))


class UserDialog(Adw.Window):
    def __init__(self, parent, user_id, on_saved):
        super().__init__(transient_for=parent, modal=True, destroy_with_parent=True)
        self.parent_window = parent
        self.user_id = user_id
        self.on_saved = on_saved
        self.set_default_size(460, 660)
        self.set_title("Человек")
        record = db.get_user(user_id) if user_id else None

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(
            Adw.WindowTitle(
                title="Новый человек" if record is None else record["full_name"],
                subtitle="Учётная запись",
            )
        )
        save = Gtk.Button(label="Сохранить")
        save.add_css_class("suggested-action")
        save.connect("clicked", lambda *_: self._save())
        header.pack_end(save)
        toolbar.add_top_bar(header)

        page = Adw.PreferencesPage()
        account = Adw.PreferencesGroup(title="Учётная запись")
        self.name = Adw.EntryRow(title="ФИО")
        self.login = Adw.EntryRow(title="Логин")
        self.password = Adw.PasswordEntryRow(title="Пароль" if record is None else "Новый пароль")
        self.about = Adw.EntryRow(title="О себе")
        account.add(self.name)
        account.add(self.login)
        account.add(self.password)
        account.add(self.about)
        page.add(account)

        access = Adw.PreferencesGroup(
            title="Доступ",
            description="Стиль и зал педагога учитываются, когда заявка назначается сама.",
        )
        self.role = Adw.ComboRow(title="Роль")
        self.role.set_model(Gtk.StringList.new([db.ROLE_RU[item] for item in ROLE_ORDER]))
        self.style = Adw.ComboRow(title="Стиль")
        self.style.set_model(Gtk.StringList.new([db.STYLE_RU[item] for item in db.STYLES]))
        self.branch = Adw.ComboRow(title="Зал")
        self.branch.set_model(Gtk.StringList.new([db.BRANCH_RU[item] for item in db.BRANCHES]))
        self.active = Adw.SwitchRow(title="Активен", active=True)
        access.add(self.role)
        access.add(self.style)
        access.add(self.branch)
        access.add(self.active)
        page.add(access)

        self.xp_spin = None
        self.badge_group = None
        if (
            record
            and record["role"] == "student"
            and parent.user["role"] == "admin"
        ):
            progress = Adw.PreferencesGroup(title="Опыт ученика")
            xp_row = Adw.ActionRow(title="Опыт (XP)")
            self.xp_spin = int_spin(0, 1_000_000, int(record.get("xp") or 0))
            self.xp_spin.set_valign(Gtk.Align.CENTER)
            xp_row.add_suffix(self.xp_spin)
            progress.add(xp_row)
            page.add(progress)

            self.badge_group = Adw.PreferencesGroup(title="Значки")
            refresh = Gtk.Button(label="Обновить значки")
            refresh.connect("clicked", lambda *_: self._refresh_badges())
            refresh_row = Adw.ActionRow(title="Синхронизация")
            refresh_row.add_suffix(refresh)
            self.badge_group.add(refresh_row)
            page.add(self.badge_group)
            self._show_badges()

        toolbar.set_content(page)
        self.set_content(toolbar)

        if record:
            self.name.set_text(record["full_name"])
            self.login.set_text(record["login"])
            self.login.set_sensitive(False)
            self.about.set_text(record["about"])
            self.role.set_selected(ROLE_ORDER.index(record["role"]))
            self.style.set_selected(db.STYLES.index(record["style"]))
            self.branch.set_selected(db.BRANCHES.index(record["branch"]))
            self.active.set_active(bool(record["is_active"]))
        else:
            self.role.set_selected(ROLE_ORDER.index("student"))
            self.style.set_selected(db.STYLES.index("other"))
            self.branch.set_selected(db.BRANCHES.index("other"))

    def _badge_rows(self):
        if self.badge_group is None:
            return []
        rows = []
        child = self.badge_group.get_first_child()
        while child is not None:
            if isinstance(child, Adw.ActionRow) and child.get_title() != "Синхронизация":
                rows.append(child)
            child = child.get_next_sibling()
        return rows

    def _show_badges(self):
        if self.badge_group is None or self.user_id is None:
            return
        for row in self._badge_rows():
            self.badge_group.remove(row)
        for badge in db.badge_board(self.user_id):
            state = "получен" if badge["unlocked"] else "ещё закрыт"
            subtitle = f"{badge['detail']} · {badge['bonus']} XP · {state}"
            self.badge_group.insert(
                Adw.ActionRow(title=badge["title"], subtitle=subtitle),
                1,
            )

    def _refresh_badges(self):
        ok, message = db.refresh_user_badges(self.user_id, self.parent_window.user["id"])
        if not ok:
            alert(self, "Не удалось", message)
            return
        self._show_badges()
        self.parent_window.notify(message)

    def _save(self):
        full_name = self.name.get_text().strip()
        role = ROLE_ORDER[selected_index(self.role, len(ROLE_ORDER))]
        style = db.STYLES[selected_index(self.style, len(db.STYLES))]
        branch = db.BRANCHES[selected_index(self.branch, len(db.BRANCHES))]
        is_active = self.active.get_active()
        password = self.password.get_text()
        if self.user_id == self.parent_window.user["id"] and not is_active:
            alert(self, "Нельзя отключить свою учётную запись")
            return
        if self.user_id is None:
            ok, message = db.create_user(
                self.login.get_text(),
                password,
                full_name,
                role=role,
                style=style,
                branch=branch,
                about=self.about.get_text(),
                is_active=1 if is_active else 0,
            )
        else:
            fields = {
                "full_name": full_name,
                "role": role,
                "style": style,
                "branch": branch,
                "about": self.about.get_text(),
                "is_active": 1 if is_active else 0,
            }
            if password:
                fields["password"] = password
            ok, message = db.update_user(self.user_id, **fields)
        if not ok:
            alert(self, "Не сохранено", message)
            return
        if (
            self.user_id is not None
            and self.xp_spin is not None
            and role == "student"
            and self.parent_window.user["role"] == "admin"
        ):
            xp_ok, xp_message = db.set_user_xp(
                self.user_id,
                self.parent_window.user["id"],
                int(self.xp_spin.get_value()),
            )
            if not xp_ok and xp_message != "Нет изменений":
                alert(self, "Опыт не сохранён", xp_message)
                return
            if xp_ok:
                message = xp_message
                self._show_badges()
        self.close()
        self.on_saved(self.user_id, message)


class ReviewBox(Gtk.Box):
    def __init__(self, window, kind, target_id, title):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.window = window
        self.kind = kind
        self.target_id = target_id
        self.group = Adw.PreferencesGroup(title=title)
        self.append(self.group)
        self._rows = []

    def reload(self):
        for row in self._rows:
            self.group.remove(row)
        self._rows.clear()
        user = self.window.user
        if not self.target_id:
            self.set_visible(False)
            return
        existing = db.find_review(user["id"], self.kind, self.target_id)
        if existing:
            subtitle = f"{existing['rating']} из 5"
            if existing["body"]:
                subtitle += f" — {existing['body']}"
            row = Adw.ActionRow(title="Ваша оценка", subtitle=subtitle)
            self.group.add(row)
            self._rows.append(row)
            self.set_visible(True)
            return
        if not db.can_review(user["id"], self.kind, self.target_id):
            self.set_visible(False)
            return
        self.set_visible(True)
        stars = LabeledDrop(
            (
                (5, "5 — отлично"),
                (4, "4 — хорошо"),
                (3, "3 — нормально"),
                (2, "2 — слабо"),
                (1, "1 — плохо"),
            )
        )
        note = Adw.EntryRow(title="Комментарий, можно пустым")
        button = Gtk.Button(label="Сохранить оценку")
        button.add_css_class("suggested-action")
        button.set_halign(Gtk.Align.START)
        button.set_margin_top(6)
        button.set_margin_bottom(6)
        button.set_margin_start(12)

        def save(_button):
            ok, message = db.add_review(
                user["id"], self.kind, self.target_id, stars.value(), note.get_text()
            )
            if not ok:
                alert(self.window, "Оценка не сохранена", message)
                return
            self.window.notify(message)
            self.reload()

        button.connect("clicked", save)
        wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        wrap.set_margin_start(12)
        wrap.set_margin_end(12)
        wrap.set_margin_bottom(8)
        wrap.append(stars)
        wrap.append(note)
        wrap.append(button)
        self.group.add(wrap)
        self._rows.append(wrap)


class RequestDialog(Adw.Window):
    def __init__(self, parent, request_id, on_changed):
        super().__init__(transient_for=parent, modal=True, destroy_with_parent=True)
        self.parent_window = parent
        self.request_id = request_id
        self.on_changed = on_changed
        self.ready = False
        self.set_default_size(740, 720)
        request = db.get_request(request_id)
        if not request or not self._can_view(request):
            return
        self._build()
        self.ready = True
        self.reload()

    def _can_view(self, request):
        user = self.parent_window.user
        if user["role"] == "admin":
            return True
        if user["id"] == request["student_id"]:
            return True
        return user["role"] == "teacher" and request["teacher_id"] in (None, user["id"])

    def _build(self):
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        self.heading = Adw.WindowTitle(title="Заявка", subtitle="")
        header.set_title_widget(self.heading)
        toolbar.add_top_bar(header)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        body.set_margin_start(16)
        body.set_margin_end(16)
        body.set_margin_top(12)
        body.set_margin_bottom(16)
        self.meta = Gtk.Label(xalign=0, wrap=True, selectable=True)
        body.append(self.meta)
        self.desc_card, self.desc = card_label("")
        body.append(self.desc_card)

        self.edit_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        edit_group = Adw.PreferencesGroup(title="Редактирование")
        self.edit_title = Adw.EntryRow(title="Тема")
        self.edit_date = Adw.EntryRow(title="Желаемая дата")
        edit_group.add(self.edit_title)
        edit_group.add(self.edit_date)
        self.edit_box.append(edit_group)
        self.edit_box.append(field_label("Описание"))
        self.edit_description, edit_desc_scroll = text_view(100)
        self.edit_box.append(edit_desc_scroll)
        styles = [(key, db.STYLE_RU[key]) for key in db.STYLES if key != "other"]
        branches = [(key, db.BRANCH_RU[key]) for key in db.BRANCHES if key != "other"]
        self.edit_style = LabeledDrop(styles)
        self.edit_branch = LabeledDrop(branches)
        self.edit_priority = LabeledDrop(list(db.PRIORITY_RU.items()))
        self.edit_people = int_spin(1, 8, 1)
        self.edit_box.append(self._req_pair("Стиль", self.edit_style, "Зал", self.edit_branch))
        self.edit_box.append(self._req_pair("Приоритет", self.edit_priority, "Человек", self.edit_people))
        save_edit = Gtk.Button(label="Сохранить изменения")
        save_edit.add_css_class("suggested-action")
        save_edit.connect("clicked", lambda *_: self._save_edit())
        self.edit_box.append(save_edit)
        self.edit_box.set_visible(False)
        body.append(self.edit_box)

        self.actions = Gtk.Box(spacing=8)
        self.done_btn = Gtk.Button(label="Проведено")
        self.done_btn.add_css_class("suggested-action")
        self.done_btn.connect("clicked", lambda *_: self._status("done"))
        self.cancel_btn = Gtk.Button(label="Отменить заявку")
        self.cancel_btn.connect("clicked", lambda *_: self._status("cancelled"))
        self.actions.append(self.done_btn)
        self.actions.append(self.cancel_btn)
        body.append(self.actions)

        self.take_btn = Gtk.Button(label="Взять заявку")
        self.take_btn.add_css_class("suggested-action")
        self.take_btn.connect("clicked", lambda *_: self._take())
        body.append(self.take_btn)

        self.admin_box = Gtk.Box(spacing=8)
        teachers = db.list_teachers(only_active=True)
        if teachers:
            self.teacher_drop = LabeledDrop(
                [
                    (item["id"], f"{item['full_name']} · {db.STYLE_RU[item['style']]}")
                    for item in teachers
                ]
            )
            self.teacher_drop.set_hexpand(True)
            manual = Gtk.Button(label="Назначить")
            manual.connect("clicked", lambda *_: self._assign_manual())
            self.admin_box.append(self.teacher_drop)
            self.admin_box.append(manual)
        else:
            self.teacher_drop = None
        auto = Gtk.Button(label="Подобрать педагога")
        auto.connect("clicked", lambda *_: self._assign_auto())
        self.admin_box.append(auto)
        body.append(self.admin_box)

        self.messages_group = Adw.PreferencesGroup(title="Переписка")
        self.messages_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.messages_group.add(self.messages_box)
        self.message_view, message_scroll = text_view(72)
        send = Gtk.Button(label="Отправить")
        send.connect("clicked", lambda *_: self._send())
        self.composer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.composer.append(message_scroll)
        self.composer.append(send)
        self.messages_group.add(self.composer)
        body.append(self.messages_group)

        self.review = ReviewBox(self.parent_window, "teacher", 0, "Оценка педагога")
        body.append(self.review)

        self.history_group = Adw.PreferencesGroup(title="Журнал")
        self.history_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.history_group.add(self.history_box)
        body.append(self.history_group)
        toolbar.set_content(scrolled(body))
        self.set_content(toolbar)

    def _req_pair(self, left_caption, left, right_caption, right):
        row = Gtk.Box(spacing=12)
        for caption, widget in ((left_caption, left), (right_caption, right)):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
            box.append(field_label(caption))
            box.append(widget)
            row.append(box)
        return row

    def reload(self):
        request = db.get_request(self.request_id)
        if not request:
            self.close()
            return
        user = self.parent_window.user
        self.heading.set_title(f"№{request['id']} · {request['title']}")
        self.heading.set_subtitle(db.REQUEST_STATUS_RU[request["status"]])
        self.set_title(request["title"])
        when = request["preferred_date"] or "дата не важна"
        teacher = request["teacher_name"] or "не назначен"
        self.meta.set_text(
            f"{db.STYLE_RU[request['style']]} · {db.BRANCH_RU[request['branch']]} · "
            f"{db.PRIORITY_RU[request['priority']]}\n"
            f"Ученик: {request['student_name']} · Педагог: {teacher}\n"
            f"Человек: {request['people']} · Дата: {when} · Создана: {request['created_at']}"
        )
        self.desc.set_text(request["description"] or "Без описания")
        is_admin = user["role"] == "admin"
        can_edit = is_admin and request["status"] not in ("done", "cancelled")
        self.meta.set_visible(not can_edit)
        self.desc_card.set_visible(not can_edit)
        self.edit_box.set_visible(can_edit)
        if can_edit:
            self.edit_title.set_text(request["title"])
            self.edit_date.set_text(request["preferred_date"] or "")
            self.edit_description.get_buffer().set_text(request["description"] or "")
            self.edit_style.set_value(request["style"])
            self.edit_branch.set_value(request["branch"])
            self.edit_priority.set_value(request["priority"])
            self.edit_people.set_value(request["people"])
        open_request = request["status"] in ("new", "assigned")
        is_teacher = user["role"] == "teacher" and request["teacher_id"] == user["id"]
        self.done_btn.set_visible(is_admin or is_teacher)
        self.done_btn.set_sensitive(request["status"] == "assigned")
        can_cancel = open_request and (
            is_admin or is_teacher or user["id"] == request["student_id"]
        )
        self.cancel_btn.set_visible(can_cancel)
        self.actions.set_visible(self.done_btn.get_visible() or can_cancel)
        self.take_btn.set_visible(
            user["role"] == "teacher" and request["teacher_id"] is None and request["status"] == "new"
        )
        self.admin_box.set_visible(is_admin and request["status"] not in ("done", "cancelled"))
        if self.teacher_drop is not None and request["teacher_id"] is not None:
            self.teacher_drop.set_value(request["teacher_id"])
        self.composer.set_visible(
            open_request
            and (is_admin or user["id"] == request["student_id"] or is_teacher)
        )
        self.review.target_id = request["teacher_id"] or 0
        self.review.reload()
        self._show_messages()
        self._show_history()

    def _show_messages(self):
        clear_box(self.messages_box)
        messages = db.list_messages(self.request_id)
        if not messages:
            empty = Gtk.Label(label="Пока нет сообщений", xalign=0)
            empty.add_css_class("dim-label")
            self.messages_box.append(empty)
            return
        for message in messages:
            block = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            block.add_css_class("card")
            block.add_css_class("ol-panel")
            who = Gtk.Label(label=f"{message['user_name']} · {message['created_at']}", xalign=0)
            who.add_css_class("dim-label")
            text = Gtk.Label(label=message["body"], xalign=0, wrap=True, selectable=True)
            block.append(who)
            block.append(text)
            self.messages_box.append(block)

    def _show_history(self):
        clear_box(self.history_box)
        events = db.list_history("request", self.request_id)
        if not events:
            empty = Gtk.Label(label="Пока пусто", xalign=0)
            empty.add_css_class("dim-label")
            self.history_box.append(empty)
            return
        for event in events:
            who = event["user_name"] or "система"
            self.history_box.append(
                Adw.ActionRow(title=event["action"], subtitle=f"{event['created_at']} · {who}")
            )

    def _finish(self, message):
        self.reload()
        self.on_changed()
        if message:
            self.parent_window.notify(message)

    def _save_edit(self):
        ok, message = db.update_request(
            self.request_id,
            self.parent_window.user["id"],
            title=self.edit_title.get_text(),
            description=text_of(self.edit_description),
            style=self.edit_style.value(),
            branch=self.edit_branch.value(),
            preferred_date=self.edit_date.get_text(),
            priority=self.edit_priority.value(),
            people=int(self.edit_people.get_value()),
        )
        if not ok:
            alert(self, "Не сохранено", message)
            return
        self._finish(message)

    def _status(self, status):
        if status == "cancelled":
            confirm(self, "Отменить заявку?", "Вернуть её в работу уже не получится.", lambda: self._apply_status(status))
            return
        self._apply_status(status)

    def _apply_status(self, status):
        ok, message = db.set_request_status(self.request_id, status, self.parent_window.user["id"])
        if not ok:
            alert(self, "Не удалось", message)
            return
        self._finish(message)

    def _take(self):
        ok, message = db.take_request(self.request_id, self.parent_window.user["id"])
        if not ok:
            alert(self, "Не удалось", message)
            return
        self._finish(message)

    def _assign_manual(self):
        if self.teacher_drop is None or self.teacher_drop.value() is None:
            alert(self, "Нет активных педагогов")
            return
        ok, message = db.assign_request(
            self.request_id,
            self.teacher_drop.value(),
            self.parent_window.user["id"],
            note="вручную",
        )
        if not ok:
            alert(self, "Не удалось", message)
            return
        self._finish("Педагог назначен")

    def _assign_auto(self):
        teacher, debug = matching.distribute(self.request_id, self.parent_window.user["id"])
        self._finish("Педагог назначен" if teacher else "Педагог не назначен")
        alert(self, "Подбор педагога", "\n".join(debug))

    def _send(self):
        ok, message = db.add_message(self.request_id, self.parent_window.user["id"], text_of(self.message_view))
        if not ok:
            alert(self, "Не отправлено", message)
            return
        self.message_view.get_buffer().set_text("")
        self._finish(message)


class ClassDialog(Adw.Window):
    def __init__(self, parent, class_id, on_changed):
        super().__init__(transient_for=parent, modal=True, destroy_with_parent=True)
        self.parent_window = parent
        self.class_id = class_id
        self.on_changed = on_changed
        self.ready = False
        self.set_default_size(740, 720)
        lesson = db.get_class(class_id)
        if not lesson:
            return
        self._build()
        self.ready = True
        self.reload()

    def _build(self):
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        self.heading = Adw.WindowTitle(title="Занятие", subtitle="")
        header.set_title_widget(self.heading)
        toolbar.add_top_bar(header)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        body.set_margin_start(16)
        body.set_margin_end(16)
        body.set_margin_top(12)
        body.set_margin_bottom(16)
        self.meta = Gtk.Label(xalign=0, wrap=True, selectable=True)
        body.append(self.meta)
        self.desc_card, self.desc = card_label("")
        body.append(self.desc_card)

        self.edit_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        edit_group = Adw.PreferencesGroup(title="Редактирование")
        self.edit_title = Adw.EntryRow(title="Название")
        self.edit_date = Adw.EntryRow(title="Дата, ГГГГ-ММ-ДД")
        edit_group.add(self.edit_title)
        edit_group.add(self.edit_date)
        self.edit_box.append(edit_group)
        self.edit_box.append(field_label("Описание"))
        self.edit_description, edit_desc_scroll = text_view(100)
        self.edit_box.append(edit_desc_scroll)
        styles = [(key, db.STYLE_RU[key]) for key in db.STYLES if key != "other"]
        branches = [(key, db.BRANCH_RU[key]) for key in db.BRANCHES if key != "other"]
        self.edit_style = LabeledDrop(styles)
        self.edit_branch = LabeledDrop(branches)
        self.edit_hours = int_spin(1, 6, 2)
        self.edit_price = int_spin(100, 100_000, 1200, 100)
        self.edit_capacity = int_spin(1, 30, 10)
        self.edit_box.append(self._edit_pair("Стиль", self.edit_style, "Зал", self.edit_branch))
        self.edit_box.append(self._edit_pair("Часы", self.edit_hours, "Мест", self.edit_capacity))
        price_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        price_box.append(field_label("Цена, ₽"))
        price_box.append(self.edit_price)
        self.edit_box.append(price_box)
        self.edit_teacher_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.edit_teacher_box.append(field_label("Педагог"))
        self.edit_teacher = LabeledDrop([])
        self.edit_teacher_box.append(self.edit_teacher)
        self.edit_box.append(self.edit_teacher_box)
        save_edit = Gtk.Button(label="Сохранить изменения")
        save_edit.add_css_class("suggested-action")
        save_edit.connect("clicked", lambda *_: self._save_edit())
        self.edit_box.append(save_edit)
        self.edit_box.set_visible(False)
        body.append(self.edit_box)

        self.book_btn = Gtk.Button(label="Записаться", halign=Gtk.Align.START)
        self.book_btn.add_css_class("suggested-action")
        self.book_btn.connect("clicked", lambda *_: self._book())
        body.append(self.book_btn)

        self.cancel_booking_btn = Gtk.Button(label="Снять мою запись")
        self.cancel_booking_btn.connect(
            "clicked",
            lambda *_: confirm(self, "Снять запись?", "Место вернётся в занятие.", self._cancel_booking),
        )
        body.append(self.cancel_booking_btn)

        self.manage_box = Gtk.Box(spacing=8)
        complete = Gtk.Button(label="Отметить посещение")
        complete.add_css_class("suggested-action")
        complete.connect("clicked", lambda *_: self._open_attendance())
        cancel = Gtk.Button(label="Отменить занятие")
        cancel.connect(
            "clicked",
            lambda *_: confirm(
                self,
                "Отменить занятие?",
                "Действующие записи учеников тоже будут сняты.",
                lambda: self._class_status("cancelled"),
            ),
        )
        self.manage_box.append(complete)
        self.manage_box.append(cancel)
        body.append(self.manage_box)

        self.attend_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.attend_box.add_css_class("ol-panel")
        attend_hint = Gtk.Label(
            xalign=0,
            wrap=True,
            label="Отметьте, кто был в зале. Опыт получат только они, остальные будут в журнале как «не пришёл».",
        )
        attend_hint.add_css_class("ol-meta")
        self.attend_checks = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        attend_actions = Gtk.Box(spacing=8)
        save_attendance = Gtk.Button(label="Закрыть занятие")
        save_attendance.add_css_class("suggested-action")
        save_attendance.connect("clicked", lambda *_: self._save_attendance())
        back = Gtk.Button(label="Назад")
        back.connect("clicked", lambda *_: self._show_attendance(False))
        attend_actions.append(save_attendance)
        attend_actions.append(back)
        self.attend_box.append(attend_hint)
        self.attend_box.append(self.attend_checks)
        self.attend_box.append(attend_actions)
        self.attend_box.set_visible(False)
        self._checks = []
        body.append(self.attend_box)

        self.people_group = Adw.PreferencesGroup(title="Журнал занятия")
        self.people_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.people_group.add(self.people_box)
        body.append(self.people_group)

        self.tour_review = ReviewBox(self.parent_window, "class", self.class_id, "Оценка занятия")
        self.teacher_review = ReviewBox(self.parent_window, "teacher", 0, "Оценка педагога")
        body.append(self.tour_review)
        body.append(self.teacher_review)
        toolbar.set_content(scrolled(body))
        self.set_content(toolbar)

    def _edit_pair(self, left_caption, left, right_caption, right):
        row = Gtk.Box(spacing=12)
        for caption, widget in ((left_caption, left), (right_caption, right)):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
            box.append(field_label(caption))
            box.append(widget)
            row.append(box)
        return row

    def reload(self):
        lesson = db.get_class(self.class_id)
        if not lesson:
            self.close()
            return
        user = self.parent_window.user
        self.heading.set_title(lesson["title"])
        self.heading.set_subtitle(db.CLASS_STATUS_RU[lesson["status"]])
        self.set_title(lesson["title"])
        score = rating_text(lesson["review_count"], lesson["review_avg"])
        seats = "—"
        if lesson["status"] in ("open", "full"):
            seats = f"{lesson['seats_left']} из {lesson['capacity']}"
        self.meta.set_text(
            f"{db.STYLE_RU[lesson['style']]} · {db.BRANCH_RU[lesson['branch']]} · {lesson['class_date']}\n"
            f"Педагог: {lesson['teacher_name']} · оценка: {score}\n"
            f"{money(lesson['price'])} · {lesson['duration_hours']} ч · места: {seats}"
        )
        self.desc.set_text(lesson["description"] or "Без описания")
        can_edit = lesson["status"] in ("open", "full") and (
            user["role"] == "admin"
            or (user["role"] == "teacher" and lesson["teacher_id"] == user["id"])
        )
        self.meta.set_visible(not can_edit)
        self.desc_card.set_visible(not can_edit)
        self.edit_box.set_visible(can_edit)
        if can_edit:
            self.edit_title.set_text(lesson["title"])
            self.edit_date.set_text(lesson["class_date"])
            self.edit_description.get_buffer().set_text(lesson["description"] or "")
            self.edit_style.set_value(lesson["style"])
            self.edit_branch.set_value(lesson["branch"])
            self.edit_hours.set_value(lesson["duration_hours"])
            self.edit_price.set_value(lesson["price"])
            self.edit_capacity.set_value(lesson["capacity"])
            show_teacher = user["role"] == "admin"
            self.edit_teacher_box.set_visible(show_teacher)
            if show_teacher:
                teachers = db.list_teachers(only_active=True)
                self.edit_teacher._ids = [item["id"] for item in teachers]
                labels = [item["full_name"] for item in teachers]
                self.edit_teacher.set_model(Gtk.StringList.new(labels or ["—"]))
                if lesson["teacher_id"] in self.edit_teacher._ids:
                    self.edit_teacher.set_value(lesson["teacher_id"])
        mine = db.confirmed_enrollment(lesson["id"], user["id"]) if user["role"] == "student" else None
        can_book = user["role"] == "student" and lesson["status"] == "open" and mine is None and lesson["seats_left"] > 0
        self.book_btn.set_visible(can_book)
        self.cancel_booking_btn.set_visible(mine is not None)
        self._my_enrollment = mine
        self._can_manage = lesson["status"] in ("open", "full") and (
            user["role"] == "admin" or (user["role"] == "teacher" and lesson["teacher_id"] == user["id"])
        )
        self.attend_box.set_visible(False)
        self.manage_box.set_visible(self._can_manage)
        self.people_group.set_visible(
            user["role"] == "admin" or (user["role"] == "teacher" and lesson["teacher_id"] == user["id"])
        )
        self._show_people()
        self.teacher_review.target_id = lesson["teacher_id"]
        self.tour_review.reload()
        self.teacher_review.reload()

    def _show_people(self):
        clear_box(self.people_box)
        rows = [
            row
            for row in db.list_enrollments(class_id=self.class_id)
            if row["status"] != "cancelled"
        ]
        if not rows:
            empty = Gtk.Label(label="Пока никто не записан", xalign=0)
            empty.add_css_class("dim-label")
            self.people_box.append(empty)
            return
        for row in rows:
            action = Adw.ActionRow(
                title=row["student_name"],
                subtitle=db.ENROLL_STATUS_RU[row["status"]],
            )
            user = self.parent_window.user
            if user["role"] == "admin" and row["status"] == "confirmed":
                drop = Gtk.Button(label="Снять")
                drop.connect(
                    "clicked",
                    lambda *_button, enrollment_id=row["id"]: self._cancel_enrollment_id(enrollment_id),
                )
                action.add_suffix(drop)
            self.people_box.append(action)

    def _cancel_enrollment_id(self, enrollment_id):
        def apply():
            ok, message = db.cancel_enrollment(enrollment_id, self.parent_window.user["id"])
            if not ok:
                alert(self, "Не удалось", message)
                return
            self.reload()
            self.on_changed()
            self.parent_window.notify(message)

        confirm(self, "Снять запись?", "Место вернётся в занятие.", apply)

    def _book(self):
        enrollment_id, error = db.enroll(self.class_id, self.parent_window.user["id"], 1)
        if error:
            alert(self, "Не записались", error)
            return
        self.reload()
        self.on_changed()
        self.parent_window.notify(f"Запись №{enrollment_id} оформлена")

    def _cancel_booking(self):
        if not self._my_enrollment:
            return
        ok, message = db.cancel_enrollment(self._my_enrollment["id"], self.parent_window.user["id"])
        if not ok:
            alert(self, "Не удалось", message)
            return
        self.reload()
        self.on_changed()
        self.parent_window.notify(message)

    def _save_edit(self):
        user = self.parent_window.user
        fields = {
            "title": self.edit_title.get_text(),
            "description": text_of(self.edit_description),
            "style": self.edit_style.value(),
            "branch": self.edit_branch.value(),
            "class_date": self.edit_date.get_text(),
            "duration_hours": int(self.edit_hours.get_value()),
            "price": int(self.edit_price.get_value()),
            "capacity": int(self.edit_capacity.get_value()),
        }
        if user["role"] == "admin" and self.edit_teacher_box.get_visible():
            teacher_id = self.edit_teacher.value()
            if teacher_id is not None:
                fields["teacher_id"] = teacher_id
        ok, message = db.update_class(self.class_id, user["id"], **fields)
        if not ok:
            alert(self, "Не сохранено", message)
            return
        self.reload()
        self.on_changed()
        self.parent_window.notify(message)

    def _show_attendance(self, visible):
        self.attend_box.set_visible(visible)
        self.manage_box.set_visible(self._can_manage and not visible)

    def _open_attendance(self):
        rows = [
            row
            for row in db.list_enrollments(class_id=self.class_id)
            if row["status"] == "confirmed"
        ]
        if not rows:
            self._class_status("completed")
            return
        clear_box(self.attend_checks)
        self._checks = []
        for row in rows:
            check = Gtk.CheckButton(label=row["student_name"])
            check.set_active(True)
            check.enrollment_id = row["id"]
            self._checks.append(check)
            self.attend_checks.append(check)
        self._show_attendance(True)

    def _save_attendance(self):
        present = [check.enrollment_id for check in self._checks if check.get_active()]
        self._class_status("completed", present)

    def _class_status(self, status, present_ids=None):
        ok, message = db.set_class_status(
            self.class_id,
            status,
            self.parent_window.user["id"],
            present_ids,
        )
        if not ok:
            alert(self, "Не удалось", message)
            return
        self.reload()
        self.on_changed()
        self.parent_window.notify(message)


class ClassCreateDialog(Adw.Window):
    def __init__(self, parent, on_saved):
        super().__init__(transient_for=parent, modal=True, destroy_with_parent=True)
        self.parent_window = parent
        self.on_saved = on_saved
        self.set_default_size(520, 640)
        self.set_title("Новое занятие")
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="Новое занятие", subtitle="Его увидят ученики"))
        save = Gtk.Button(label="Опубликовать")
        save.add_css_class("suggested-action")
        save.connect("clicked", lambda *_: self._save())
        header.pack_end(save)
        toolbar.add_top_bar(header)
        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form.set_margin_start(16)
        form.set_margin_end(16)
        form.set_margin_top(12)
        form.set_margin_bottom(16)
        group = Adw.PreferencesGroup(title="Занятие")
        self.title_row = Adw.EntryRow(title="Название")
        self.date_row = Adw.EntryRow(title="Дата, ГГГГ-ММ-ДД")
        group.add(self.title_row)
        group.add(self.date_row)
        form.append(group)
        form.append(field_label("Описание"))
        self.description, desc_scroll = text_view(120)
        form.append(desc_scroll)
        styles = [(key, db.STYLE_RU[key]) for key in db.STYLES if key != "other"]
        branches = [(key, db.BRANCH_RU[key]) for key in db.BRANCHES if key != "other"]
        self.style = LabeledDrop(styles)
        self.branch = LabeledDrop(branches)
        user = parent.user
        if user["style"] in db.STYLES and user["style"] != "other":
            self.style.set_value(user["style"])
        if user["branch"] in db.BRANCHES and user["branch"] != "other":
            self.branch.set_value(user["branch"])
        self.hours = int_spin(1, 6, 2)
        self.price = int_spin(100, 100_000, 1200, 100)
        self.capacity = int_spin(1, 30, 10)
        form.append(self._pair("Стиль", self.style, "Зал", self.branch))
        form.append(self._pair("Часы", self.hours, "Мест", self.capacity))
        price_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        price_box.append(field_label("Цена, ₽"))
        price_box.append(self.price)
        form.append(price_box)
        self.teacher_drop = None
        if user["role"] == "admin":
            teachers = db.list_teachers(only_active=True)
            if teachers:
                self.teacher_drop = LabeledDrop(
                    [(item["id"], item["full_name"]) for item in teachers]
                )
                form.append(field_label("Педагог"))
                form.append(self.teacher_drop)
        toolbar.set_content(scrolled(form))
        self.set_content(toolbar)

    def _pair(self, left_caption, left, right_caption, right):
        row = Gtk.Box(spacing=12)
        for caption, widget in ((left_caption, left), (right_caption, right)):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
            box.append(field_label(caption))
            box.append(widget)
            row.append(box)
        return row

    def _save(self):
        teacher_id = self.parent_window.user["id"]
        if self.teacher_drop is not None:
            teacher_id = self.teacher_drop.value()
            if teacher_id is None:
                alert(self, "Выберите педагога")
                return
        class_id, error = db.create_class(
            self.title_row.get_text(),
            text_of(self.description),
            self.style.value(),
            self.branch.value(),
            self.date_row.get_text(),
            int(self.hours.get_value()),
            int(self.price.get_value()),
            int(self.capacity.get_value()),
            teacher_id,
        )
        if error:
            alert(self, "Не опубликовано", error)
            return
        self.close()
        self.on_saved(class_id)


class ProductDialog(Adw.Window):
    def __init__(self, parent, product_id, on_saved):
        super().__init__(transient_for=parent, modal=True, destroy_with_parent=True)
        self.parent_window = parent
        self.product_id = product_id
        self.on_saved = on_saved
        self.ready = product_id is None
        product = db.get_product(product_id) if product_id else None
        if product_id and not product:
            return
        self.ready = True
        self.set_default_size(480, 620)
        self.set_title("Костюм")
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(
            Adw.WindowTitle(
                title="Новый костюм" if product is None else product["name"],
                subtitle="Костюмерная",
            )
        )
        save = Gtk.Button(label="Сохранить")
        save.add_css_class("suggested-action")
        save.connect("clicked", lambda *_: self._save())
        header.pack_end(save)
        toolbar.add_top_bar(header)
        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form.set_margin_start(16)
        form.set_margin_end(16)
        form.set_margin_top(12)
        form.set_margin_bottom(16)
        self.owner_drop = None
        if product is None and parent.user["role"] == "admin":
            ateliers = [item for item in db.list_users("atelier") if item["is_active"]]
            if ateliers:
                self.owner_drop = LabeledDrop(
                    [(item["id"], item["full_name"]) for item in ateliers]
                )
                owner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                owner_box.append(field_label("Костюмер"))
                owner_box.append(self.owner_drop)
                form.append(owner_box)
        group = Adw.PreferencesGroup(title="Карточка")
        self.name = Adw.EntryRow(title="Название")
        group.add(self.name)
        form.append(group)
        form.append(field_label("Описание"))
        self.description, desc_scroll = text_view(100)
        form.append(desc_scroll)
        self.category = LabeledDrop(list(db.PRODUCT_CATEGORY_RU.items()))
        self.style = LabeledDrop([(key, db.STYLE_RU[key]) for key in db.STYLES])
        self.size = Gtk.Entry(hexpand=True, placeholder_text="напр. S–M, 140–152")
        self.stock = int_spin(0, 10_000, 10)
        self.active = Adw.SwitchRow(title="Показывать в костюмерной", active=True)
        pair_one = Gtk.Box(spacing=12)
        for caption, widget in (("Категория", self.category), ("Направление", self.style)):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
            box.append(field_label(caption))
            box.append(widget)
            pair_one.append(box)
        pair_two = Gtk.Box(spacing=12)
        for caption, widget in (("Размер", self.size), ("Свободно единиц", self.stock)):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
            box.append(field_label(caption))
            box.append(widget)
            pair_two.append(box)
        form.append(pair_one)
        form.append(pair_two)
        form.append(self.active)
        toolbar.set_content(scrolled(form))
        self.set_content(toolbar)
        self.edit_atelier = None
        if product:
            self.name.set_text(product["name"])
            self.description.get_buffer().set_text(product["description"])
            self.category.set_value(product["category"])
            self.style.set_value(product["style"])
            self.size.set_text(product["size"])
            self.stock.set_value(product["stock"])
            self.active.set_active(bool(product["is_active"]))
            if parent.user["role"] == "admin":
                ateliers = [item for item in db.list_users("atelier") if item["is_active"]]
                if ateliers:
                    self.edit_atelier = LabeledDrop(
                        [(item["id"], item["full_name"]) for item in ateliers]
                    )
                    self.edit_atelier.set_value(product["atelier_id"])
                    owner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                    owner_box.append(field_label("Костюмер"))
                    owner_box.append(self.edit_atelier)
                    form.prepend(owner_box)
        else:
            self.edit_atelier = None

    def _save(self):
        fields = {
            "name": self.name.get_text(),
            "description": text_of(self.description),
            "category": self.category.value(),
            "style": self.style.value(),
            "size": self.size.get_text(),
            "stock": int(self.stock.get_value()),
            "is_active": self.active.get_active(),
        }
        if self.product_id is None:
            owner_id = self.parent_window.user["id"]
            if self.owner_drop is not None:
                owner_id = self.owner_drop.value()
                if owner_id is None:
                    alert(self, "Выберите костюмера")
                    return
            product_id, error = db.create_product(
                owner_id,
                fields["name"],
                fields["description"],
                fields["category"],
                fields["size"],
                fields["stock"],
                fields["style"],
            )
            ok, message = (error is None), (error or "Костюм добавлен")
            saved_id = product_id
        else:
            if self.edit_atelier is not None:
                atelier_id = self.edit_atelier.value()
                if atelier_id is not None:
                    fields["atelier_id"] = atelier_id
            ok, message = db.update_product(self.product_id, self.parent_window.user["id"], **fields)
            saved_id = self.product_id
        if not ok:
            alert(self, "Не сохранено", message)
            return
        self.close()
        self.on_saved(saved_id, message)


class BuyDialog(Adw.Window):
    def __init__(self, parent, product_id, on_saved):
        super().__init__(transient_for=parent, modal=True, destroy_with_parent=True)
        self.parent_window = parent
        self.on_saved = on_saved
        self.ready = False
        self.product = db.get_product(product_id)
        if not self.product or not self.product["is_active"] or self.product["stock"] <= 0:
            return
        self.ready = True
        self.set_default_size(420, 320)
        self.set_title("Костюм")
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title=self.product["name"], subtitle=self.product["atelier_name"]))
        toolbar.add_top_bar(header)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(12)
        box.set_margin_bottom(16)
        self.people = int_spin(1, min(12, int(self.product["stock"])), 1)
        self.size = Gtk.Label(xalign=0)
        self.size.add_css_class("title-2")
        box.append(Gtk.Label(label=self.product["description"] or "Без описания", xalign=0, wrap=True))
        box.append(field_label(f"Размер: {self.product['size'] or 'любой'}"))
        box.append(field_label(f"Свободно единиц: {self.product['stock']}"))
        box.append(field_label("Сколько нужно"))
        box.append(self.people)
        button = Gtk.Button(label="Отправить запрос")
        button.add_css_class("suggested-action")
        button.connect("clicked", lambda *_: self._buy())
        box.append(button)
        toolbar.set_content(box)
        self.set_content(toolbar)

    def _buy(self):
        order_id, error = db.create_order(
            self.parent_window.user["id"], self.product["id"], int(self.people.get_value())
        )
        if error:
            alert(self, "Запрос не отправлен", error)
            return
        self.close()
        self.on_saved(order_id)


class OrderDialog(Adw.Window):
    def __init__(self, parent, order_id, on_changed):
        super().__init__(transient_for=parent, modal=True, destroy_with_parent=True)
        self.parent_window = parent
        self.order_id = order_id
        self.on_changed = on_changed
        self.ready = False
        order = db.get_order(order_id)
        user = parent.user
        if not order:
            return
        if user["role"] != "admin" and user["id"] not in (order["student_id"], order["atelier_id"]):
            return
        self._build(order)
        self.ready = True
        self.reload()

    def _build(self, order):
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        self.heading = Adw.WindowTitle(title=f"Выдача №{order['id']}", subtitle="")
        header.set_title_widget(self.heading)
        toolbar.add_top_bar(header)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        body.set_margin_start(16)
        body.set_margin_end(16)
        body.set_margin_top(12)
        body.set_margin_bottom(16)
        self.meta = Gtk.Label(xalign=0, wrap=True, selectable=True)
        body.append(self.meta)
        self.actions = Gtk.Box(spacing=8)
        self.action_buttons = {}
        for status, caption in (
            ("accepted", "Принять"),
            ("issued", "Выдать"),
            ("returned", "Принять возврат"),
            ("cancelled", "Отменить"),
        ):
            button = Gtk.Button(label=caption)
            if status == "issued":
                button.add_css_class("suggested-action")
            button.connect("clicked", lambda _, value=status: self._status(value))
            self.action_buttons[status] = button
            self.actions.append(button)
        body.append(self.actions)
        self.reviews = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        body.append(self.reviews)
        self.history_group = Adw.PreferencesGroup(title="Журнал")
        self.history_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.history_group.add(self.history_box)
        body.append(self.history_group)
        toolbar.set_content(scrolled(body))
        self.set_content(toolbar)

    def reload(self):
        order = db.get_order(self.order_id)
        if not order:
            self.close()
            return
        user = self.parent_window.user
        self.heading.set_subtitle(db.ORDER_STATUS_RU[order["status"]])
        self.meta.set_text(
            f"Костюмы: {order['items_label'] or '—'}\n"
            f"Ученик: {order['student_name']} · Костюмер: {order['atelier_name']}\n"
            f"Оформлен: {order['created_at']}"
        )
        is_atelier = user["role"] == "atelier" and user["id"] == order["atelier_id"]
        is_admin = user["role"] == "admin"
        is_student = user["id"] == order["student_id"]
        allowed = set(db.ORDER_FLOW[order["status"]])
        for status, button in self.action_buttons.items():
            visible = status in allowed
            if status == "cancelled":
                visible = visible and (is_admin or is_atelier or (is_student and order["status"] == "new"))
            elif status == "returned":
                visible = visible and (is_admin or is_atelier or is_student)
            else:
                visible = visible and (is_admin or is_atelier)
            button.set_visible(visible)
        self.actions.set_visible(any(button.get_visible() for button in self.action_buttons.values()))
        clear_box(self.reviews)
        if order["status"] in ("issued", "returned"):
            for item in order["items"]:
                box = ReviewBox(self.parent_window, "product", item["product_id"], f"Оценка: {item['name']}")
                box.reload()
                self.reviews.append(box)
        clear_box(self.history_box)
        events = db.list_history("order", self.order_id)
        if not events:
            empty = Gtk.Label(label="Пока пусто", xalign=0)
            empty.add_css_class("dim-label")
            self.history_box.append(empty)
        for event in events:
            who = event["user_name"] or "система"
            self.history_box.append(
                Adw.ActionRow(title=event["action"], subtitle=f"{event['created_at']} · {who}")
            )

    def _status(self, status):
        def apply():
            ok, message = db.set_order_status(self.order_id, status, self.parent_window.user["id"])
            if not ok:
                alert(self, "Не удалось", message)
                return
            self.reload()
            self.on_changed()
            self.parent_window.notify(message)

        if status == "cancelled":
            confirm(self, "Отменить запрос?", "Костюм вернётся в костюмерную.", apply)
            return
        apply()


def present_ready(dialog, window, missing):
    if not dialog.ready:
        dialog.close()
        alert(window, missing)
        return
    dialog.present()


class ListPage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.window = window
        self.set_margin_start(16)
        self.set_margin_end(16)
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self._ready = False

    def _bar(self, *widgets):
        bar = Gtk.Box(spacing=8)
        self.append(bar)
        return bar

    def _finish_table(self, on_activate=None):
        self.list = Gtk.ListBox()
        self.list.add_css_class("ol-strips")
        self.list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list.set_activate_on_single_click(False)
        if on_activate is not None:
            self.list.connect("row-activated", lambda *_: on_activate())
        self.append(scrolled(self.list))
        self.count = Gtk.Label(xalign=0)
        self.count.add_css_class("ol-meta")
        self.append(self.count)

    def _selected(self):
        row = self.list.get_selected_row()
        if row is None:
            return None
        return row.record_id

    def _fill(self, rows, keep=None):
        clear_box(self.list)
        chosen = None
        for values in rows:
            row = StripRow(values)
            self.list.append(row)
            if keep is not None and values[0] == keep:
                chosen = row
        if chosen is None:
            chosen = self.list.get_row_at_index(0)
        if chosen is not None:
            self.list.select_row(chosen)
        self.count.set_text(f"{len(rows)} в списке" if rows else "Пока пусто")


class OverviewPage(Gtk.ScrolledWindow):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(8)
        box.set_margin_bottom(20)
        self.stats = Gtk.FlowBox(
            selection_mode=Gtk.SelectionMode.NONE,
            homogeneous=True,
            max_children_per_line=3,
            min_children_per_line=2,
            column_spacing=10,
            row_spacing=10,
        )
        box.append(self.stats)
        about = Gtk.Label(
            xalign=0,
            wrap=True,
                label=(
                    "Свободные заявки уходят педагогу сами: сначала совпавший стиль, потом зал, "
                    "затем оценка учеников и короткая очередь. Опыт начисляется за посещённые занятия."
                ),
        )
        about.add_css_class("ol-meta")
        box.append(about)
        buttons = Gtk.Box(spacing=8)
        distribute = Gtk.Button(label="Раздать свободные заявки")
        distribute.add_css_class("suggested-action")
        distribute.add_css_class("pill")
        distribute.connect("clicked", lambda *_: self._distribute())
        buttons.append(distribute)
        box.append(buttons)

        board = Gtk.Box(spacing=12)
        board.set_homogeneous(True)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        heading = Gtk.Label(label="Кто ведёт зал", xalign=0)
        heading.add_css_class("ol-strip-title")
        left.append(heading)
        self.people = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        left.append(self.people)
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        rank_heading = Gtk.Label(label="Доска опыта", xalign=0)
        rank_heading.add_css_class("ol-strip-title")
        right.append(rank_heading)
        self.board = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right.append(self.board)
        board.append(left)
        board.append(right)
        box.append(board)
        self.set_child(box)
        self._cards = {}
        self._stat_links = (
            ("unassigned", "requests", "free"),
            ("new_orders", "orders", "new"),
            ("open_classes", "classes", "open"),
        )

    def reload(self):
        data = db.stats()
        captions = (
            ("teachers", "Педагоги"),
            ("unassigned", "Заявки без педагога"),
            ("open_classes", "Занятия"),
            ("active_enrollments", "Записи"),
            ("new_orders", "Запросы костюмов"),
            ("products", "Костюмерная"),
        )
        link_map = {item[0]: (item[1], item[2]) for item in self._stat_links}
        if not self._cards:
            for key, caption in captions:
                card = Gtk.Button()
                card.add_css_class("flat")
                inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                inner.add_css_class("ol-stat")
                value = Gtk.Label(label="0", xalign=0)
                value.add_css_class("ol-stat-num")
                title = Gtk.Label(label=caption, xalign=0)
                title.add_css_class("ol-stat-cap")
                inner.append(value)
                inner.append(title)
                card.set_child(inner)
                if key in link_map:
                    page_key, mode = link_map[key]
                    card.connect(
                        "clicked",
                        lambda *_button, pk=page_key, fm=mode: self._jump(pk, fm),
                    )
                    card.set_tooltip_text("Открыть раздел")
                self.stats.append(card)
                self._cards[key] = value
        for key, _caption in captions:
            self._cards[key].set_text(str(data[key]))
        clear_box(self.people)
        teachers = db.list_teachers(only_active=False)
        if not teachers:
            empty = Gtk.Label(label="Активных педагогов нет", xalign=0)
            empty.add_css_class("ol-meta")
            self.people.append(empty)
        for teacher in teachers:
            load = db.active_load(teacher["id"])
            state = "ведёт" if teacher["is_active"] else "пауза"
            score = rating_text(teacher["review_count"], teacher["review_avg"])
            row = Gtk.Box(spacing=12)
            row.add_css_class("ol-person")
            initials = "".join(part[0] for part in teacher["full_name"].split()[:2])
            bubble = Gtk.Label(label=initials)
            bubble.add_css_class("ol-stamp")
            bubble.add_css_class(STYLE_TONE.get(teacher["style"], "ol-plum"))
            bubble.set_valign(Gtk.Align.CENTER)
            text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)
            name = Gtk.Label(label=teacher["full_name"], xalign=0)
            name.add_css_class("ol-strip-title")
            meta = Gtk.Label(
                label=f"{db.STYLE_RU[teacher['style']]}  ·  {db.BRANCH_RU[teacher['branch']]}  ·  {state}  ·  {score}",
                xalign=0,
                wrap=True,
            )
            meta.add_css_class("ol-meta")
            text.append(name)
            text.append(meta)
            mark = Gtk.Label(label=f"{load} заявки")
            mark.add_css_class("ol-pill")
            mark.set_valign(Gtk.Align.CENTER)
            row.append(bubble)
            row.append(text)
            row.append(mark)
            self.people.append(row)

        clear_box(self.board)
        leaders = db.leaderboard(6)
        if not leaders:
            empty = Gtk.Label(label="Учеников ещё нет", xalign=0)
            empty.add_css_class("ol-meta")
            self.board.append(empty)
        for place, item in enumerate(leaders, start=1):
            row = Gtk.Box(spacing=12)
            row.add_css_class("ol-person")
            bubble = Gtk.Label(label=str(place))
            bubble.add_css_class("ol-stamp")
            bubble.add_css_class("ol-plum")
            bubble.set_valign(Gtk.Align.CENTER)
            text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)
            name = Gtk.Label(label=item["full_name"], xalign=0)
            name.add_css_class("ol-strip-title")
            meta = Gtk.Label(label=item["rank_name"], xalign=0)
            meta.add_css_class("ol-meta")
            text.append(name)
            text.append(meta)
            mark = Gtk.Label(label=f"{item['xp']} XP")
            mark.add_css_class("ol-pill")
            mark.set_valign(Gtk.Align.CENTER)
            row.append(bubble)
            row.append(text)
            row.append(mark)
            self.board.append(row)

    def _jump(self, page_key, filter_mode):
        shell = self.window.shell
        if shell is not None:
            shell.open_page(page_key, filter_mode)

    def _distribute(self):
        assigned, lines = matching.distribute_pending(self.window.user["id"])
        self.reload()
        if not lines:
            self.window.notify("Ожидающих заявок нет")
            return
        alert(self.window, f"Назначено: {assigned}", "\n".join(lines))


class UsersPage(ListPage):
    def __init__(self, window):
        super().__init__(window)
        self.search = Gtk.SearchEntry(placeholder_text="Поиск по имени или логину")
        self.search.set_hexpand(True)
        self.search.connect("search-changed", lambda *_: self.reload())
        add = Gtk.Button(label="Добавить")
        add.add_css_class("suggested-action")
        add.connect("clicked", lambda *_: UserDialog(self.window, None, self._saved).present())
        edit = Gtk.Button(label="Изменить")
        edit.connect("clicked", lambda *_: self._edit())
        toggle = Gtk.Button(label="Вкл / выкл")
        toggle.connect("clicked", lambda *_: self._toggle())
        self.role_filter = LabeledDrop(
            [("all", "Все роли"), *[(role, db.ROLE_RU[role]) for role in ROLE_ORDER]]
        )
        self.role_filter.connect("notify::selected", lambda *_: self.reload())
        self._bar(self.role_filter, self.search, add, edit, toggle)
        self._finish_table(on_activate=self._edit)
        self._ready = True

    def reload(self, keep=None):
        if not self._ready:
            return
        query = self.search.get_text().strip().casefold()
        role_mode = self.role_filter.value()
        ratings = {teacher["id"]: teacher for teacher in db.list_teachers(only_active=False)}
        rows = []
        for user in db.list_users():
            if role_mode != "all" and user["role"] != role_mode:
                continue
            blob = f"{user['login']} {user['full_name']}".casefold()
            if query and query not in blob:
                continue
            score = "—"
            style = "—"
            if user["role"] == "teacher":
                style = db.STYLE_RU[user["style"]]
                teacher = ratings.get(user["id"])
                if teacher:
                    score = rating_text(teacher["review_count"], teacher["review_avg"])
            rows.append(
                (
                    user["id"],
                    user["full_name"],
                    user["login"],
                    db.ROLE_RU[user["role"]],
                    db.BRANCH_RU[user["branch"]],
                    style,
                    f"{user['xp']} XP",
                    "активен" if user["is_active"] else "отключён",
                )
            )
        self._fill(rows, keep)

    def _edit(self):
        user_id = self._selected()
        if user_id is None:
            alert(self.window, "Выберите человека")
            return
        UserDialog(self.window, user_id, self._saved).present()

    def _saved(self, user_id, message):
        if user_id == self.window.user["id"]:
            self.window.refresh_session()
            return
        self.reload(keep=user_id)
        self.window.notify(message)

    def _toggle(self):
        user_id = self._selected()
        if user_id is None:
            alert(self.window, "Выберите человека")
            return
        record = db.get_user(user_id)
        if user_id == self.window.user["id"] and record["is_active"]:
            alert(self.window, "Нельзя отключить свою учётную запись")
            return
        ok, message = db.update_user(user_id, is_active=0 if record["is_active"] else 1)
        if not ok:
            alert(self.window, "Не удалось", message)
            return
        self.reload(keep=user_id)
        self.window.notify(message)


class RequestsPage(ListPage):
    def __init__(self, window, scope):
        super().__init__(window)
        self.scope = scope
        filters = [
            ("all", "Все"),
            ("new", "Новые"),
            ("assigned", "У педагога"),
            ("done", "Проведены"),
            ("cancelled", "Отменены"),
        ]
        if scope == "all":
            filters.append(("free", "Без педагога"))
        self.filter = LabeledDrop(filters)
        self.filter.connect("notify::selected", lambda *_: self.reload())
        self.search = Gtk.SearchEntry(placeholder_text="Поиск по теме, ученику, педагогу")
        self.search.set_hexpand(True)
        self.search.connect("search-changed", lambda *_: self.reload())
        open_btn = Gtk.Button(label="Открыть")
        open_btn.connect("clicked", lambda *_: self._open())
        widgets = [self.filter, self.search, open_btn]
        if scope == "all" and window.user["role"] == "admin":
            create = Gtk.Button(label="Новая заявка")
            create.add_css_class("suggested-action")
            create.connect(
                "clicked",
                lambda *_: AdminRequestDialog(self.window, self.reload).present(),
            )
            widgets.append(create)
        if scope == "free":
            take = Gtk.Button(label="Взять")
            take.add_css_class("suggested-action")
            take.connect("clicked", lambda *_: self._take())
            widgets.append(take)
        self._bar(*widgets)
        self._finish_table(on_activate=self._open)
        self._ready = True

    def reload(self):
        if not self._ready:
            return
        user = self.window.user
        if self.scope == "mine":
            rows = db.list_requests(student_id=user["id"])
        elif self.scope == "queue":
            rows = db.list_requests(teacher_id=user["id"])
        elif self.scope == "free":
            rows = [
                request
                for request in db.list_requests(status="new")
                if request["teacher_id"] is None
            ]
        else:
            rows = db.list_requests()
        mode = self.filter.value()
        query = self.search.get_text().strip().casefold()
        shown = []
        for request in rows:
            if mode == "free" and request["teacher_id"] is not None:
                continue
            if mode not in ("all", "free") and request["status"] != mode:
                continue
            blob = " ".join(
                (request["title"], request["student_name"] or "", request["teacher_name"] or "")
            ).casefold()
            if query and query not in blob:
                continue
            shown.append(
                (
                    request["id"],
                    request["title"],
                    db.STYLE_RU[request["style"]],
                    db.BRANCH_RU[request["branch"]],
                    db.PRIORITY_RU[request["priority"]],
                    request["student_name"],
                    request["teacher_name"] or "без педагога",
                    db.REQUEST_STATUS_RU[request["status"]],
                )
            )
        self._fill(shown)

    def apply_filter(self, mode):
        self.filter.set_value(mode)

    def _open(self):
        request_id = self._selected()
        if request_id is None:
            alert(self.window, "Выберите заявку")
            return
        present_ready(RequestDialog(self.window, request_id, self.reload), self.window, "Заявка недоступна")

    def _take(self):
        request_id = self._selected()
        if request_id is None:
            alert(self.window, "Выберите заявку")
            return
        ok, message = db.take_request(request_id, self.window.user["id"])
        if not ok:
            alert(self.window, "Не удалось", message)
            return
        self.window.notify(message)
        self.reload()


class NewRequestPage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.window = window
        clamp = Adw.Clamp(maximum_size=680, tightening_threshold=680)
        clamp.set_margin_top(12)
        clamp.set_margin_bottom(12)
        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form.set_margin_start(16)
        form.set_margin_end(16)
        intro = Gtk.Label(
            xalign=0,
            wrap=True,
            label="После отправки заявка сразу уходит свободному педагогу. В ответе будет видно, почему выбран он.",
        )
        intro.add_css_class("dim-label")
        form.append(intro)
        group = Adw.PreferencesGroup(title="Заявка педагогу")
        self.title_row = Adw.EntryRow(title="Тема")
        self.date_row = Adw.EntryRow(title="Желаемая дата, можно пусто")
        group.add(self.title_row)
        group.add(self.date_row)
        form.append(group)
        form.append(field_label("Что хочется"))
        self.description, desc_scroll = text_view(120)
        form.append(desc_scroll)
        self.style = LabeledDrop(list(db.STYLE_RU.items()))
        self.branch = LabeledDrop(list(db.BRANCH_RU.items()))
        self.priority = LabeledDrop(list(db.PRIORITY_RU.items()))
        self.priority.set_value("normal")
        self.people = int_spin(1, 8, 1)
        form.append(self._pair("Стиль", self.style, "Зал", self.branch))
        form.append(self._pair("Приоритет", self.priority, "Человек на уроке", self.people))
        self.error = Gtk.Label(xalign=0, wrap=True, visible=False)
        self.error.add_css_class("ol-error")
        form.append(self.error)
        self.submit = Gtk.Button(label="Отправить и подобрать педагога")
        self.submit.add_css_class("suggested-action")
        self.submit.add_css_class("pill")
        self.submit.connect("clicked", lambda *_: self._submit())
        form.append(self.submit)
        clamp.set_child(form)
        self.append(scrolled(clamp))

    def reload(self):
        return

    def _pair(self, left_caption, left, right_caption, right):
        row = Gtk.Box(spacing=12)
        for caption, widget in ((left_caption, left), (right_caption, right)):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
            box.append(field_label(caption))
            box.append(widget)
            row.append(box)
        return row

    def _submit(self):
        self.submit.set_sensitive(False)
        try:
            request_id, error = db.create_request(
                self.title_row.get_text(),
                text_of(self.description),
                self.style.value(),
                self.branch.value(),
                int(self.people.get_value()),
                self.date_row.get_text(),
                self.priority.value(),
                self.window.user["id"],
            )
            if error:
                self.error.set_text(error)
                self.error.set_visible(True)
                return
            teacher, debug = matching.distribute(request_id, self.window.user["id"])
            self.error.set_visible(False)
            self.title_row.set_text("")
            self.date_row.set_text("")
            self.description.get_buffer().set_text("")
            heading = f"Заявка №{request_id}"
            heading += f" → {teacher['full_name']}" if teacher else " ждёт педагога"
            alert(self.window, heading, "\n".join(debug))
            self.window.notify(heading)
        finally:
            self.submit.set_sensitive(True)


class AdminRequestDialog(Adw.Window):
    def __init__(self, parent, on_saved):
        super().__init__(transient_for=parent, modal=True, destroy_with_parent=True)
        self.parent_window = parent
        self.on_saved = on_saved
        self.set_default_size(520, 680)
        self.set_title("Заявка от ученика")
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="Новая заявка", subtitle="От имени ученика"))
        save = Gtk.Button(label="Создать")
        save.add_css_class("suggested-action")
        save.connect("clicked", lambda *_: self._save())
        header.pack_end(save)
        toolbar.add_top_bar(header)
        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form.set_margin_start(16)
        form.set_margin_end(16)
        form.set_margin_top(12)
        form.set_margin_bottom(16)
        students = [
            (item["id"], item["full_name"])
            for item in db.list_users("student")
            if item["is_active"]
        ]
        self.student = LabeledDrop(students or [(0, "—")])
        form.append(field_label("Ученик"))
        form.append(self.student)
        self.title_row = Adw.EntryRow(title="Тема")
        self.date_row = Adw.EntryRow(title="Желаемая дата")
        group = Adw.PreferencesGroup()
        group.add(self.title_row)
        group.add(self.date_row)
        form.append(group)
        form.append(field_label("Описание"))
        self.description, desc_scroll = text_view(100)
        form.append(desc_scroll)
        styles = [(key, db.STYLE_RU[key]) for key in db.STYLES if key != "other"]
        branches = [(key, db.BRANCH_RU[key]) for key in db.BRANCHES if key != "other"]
        self.style = LabeledDrop(styles)
        self.branch = LabeledDrop(branches)
        self.priority = LabeledDrop(list(db.PRIORITY_RU.items()))
        self.priority.set_value("normal")
        self.people = int_spin(1, 8, 1)
        row = Gtk.Box(spacing=12)
        for caption, widget in (
            ("Стиль", self.style),
            ("Зал", self.branch),
            ("Приоритет", self.priority),
            ("Человек", self.people),
        ):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
            box.append(field_label(caption))
            box.append(widget)
            row.append(box)
        form.append(row)
        toolbar.set_content(scrolled(form))
        self.set_content(toolbar)

    def _save(self):
        student_id = self.student.value()
        if not student_id:
            alert(self, "Выберите ученика")
            return
        request_id, error = db.create_request(
            self.title_row.get_text(),
            text_of(self.description),
            self.style.value(),
            self.branch.value(),
            int(self.people.get_value()),
            self.date_row.get_text(),
            self.priority.value(),
            student_id,
            actor_id=self.parent_window.user["id"],
        )
        if error:
            alert(self, "Не создано", error)
            return
        self.close()
        self.on_saved()
        self.parent_window.notify(f"Заявка №{request_id} создана")


class ClassesPage(ListPage):
    def __init__(self, window, scope):
        super().__init__(window)
        self.scope = scope
        if scope == "catalog":
            filters = [
                ("actual", "Ближайшие"),
                ("open", "Есть места"),
                ("full", "Мест нет"),
                ("completed", "Прошедшие"),
                ("all", "Все"),
            ]
        else:
            filters = [
                ("all", "Все"),
                ("open", "Есть места"),
                ("full", "Мест нет"),
                ("completed", "Прошедшие"),
                ("cancelled", "Отменённые"),
            ]
        self.filter = LabeledDrop(filters)
        self.filter.connect("notify::selected", lambda *_: self.reload())
        self.search = Gtk.SearchEntry(placeholder_text="Поиск по названию или педагогу")
        self.search.set_hexpand(True)
        self.search.connect("search-changed", lambda *_: self.reload())
        open_btn = Gtk.Button(label="Открыть")
        open_btn.connect("clicked", lambda *_: self._open())
        widgets = [self.filter, self.search, open_btn]
        if scope == "mine" or (scope == "all" and window.user["role"] == "admin"):
            create = Gtk.Button(label="Новое занятие")
            create.add_css_class("suggested-action")
            create.connect("clicked", lambda *_: ClassCreateDialog(self.window, self._created).present())
            widgets.append(create)
        self._bar(*widgets)
        self.board = Gtk.FlowBox(
            selection_mode=Gtk.SelectionMode.SINGLE,
            max_children_per_line=2,
            min_children_per_line=1,
            column_spacing=8,
            row_spacing=8,
            homogeneous=True,
        )
        self.board.add_css_class("ol-board")
        self.board.set_activate_on_single_click(False)
        self.board.connect("child-activated", lambda *_: self._open())
        self.append(scrolled(self.board))
        self.count = Gtk.Label(xalign=0)
        self.count.add_css_class("ol-meta")
        self.append(self.count)
        self._ready = True

    def reload(self):
        if not self._ready:
            return
        if self.scope == "mine":
            rows = db.list_classes(teacher_id=self.window.user["id"])
        else:
            rows = db.list_classes()
        mode = self.filter.value()
        query = self.search.get_text().strip().casefold()
        clear_box(self.board)
        shown = 0
        for lesson in rows:
            if mode == "actual" and lesson["status"] not in ("open", "full"):
                continue
            if mode not in ("all", "actual") and lesson["status"] != mode:
                continue
            blob = f"{lesson['title']} {lesson['teacher_name']}".casefold()
            if query and query not in blob:
                continue
            self.board.append(self._card(lesson))
            shown += 1
        first = self.board.get_child_at_index(0)
        if first is not None:
            self.board.select_child(first)
        self.count.set_text(f"{shown} занятий" if shown else "Занятий нет")

    def apply_filter(self, mode):
        self.filter.set_value(mode)

    def _card(self, lesson):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.add_css_class("ol-card")
        card.class_id = lesson["id"]
        band = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        band.add_css_class("ol-band")
        band.add_css_class(STYLE_TONE.get(lesson["style"], "ol-plum"))
        place = Gtk.Label(label=db.STYLE_RU[lesson["style"]].upper(), xalign=0)
        place.add_css_class("ol-kicker")
        title = Gtk.Label(label=lesson["title"], xalign=0, wrap=True)
        title.add_css_class("ol-card-title")
        band.append(place)
        band.append(title)
        card.append(band)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        body.add_css_class("ol-card-body")
        seats = "запись закрыта"
        if lesson["status"] in ("open", "full"):
            seats = f"свободно {lesson['seats_left']} из {lesson['capacity']}"
        meta = Gtk.Label(
            label=f"{lesson['class_date']}  ·  {db.BRANCH_RU[lesson['branch']]}  ·  {lesson['duration_hours']} ч",
            xalign=0,
            wrap=True,
        )
        meta.add_css_class("ol-meta")
        teacher = Gtk.Label(label=lesson["teacher_name"], xalign=0)
        price = Gtk.Label(label=money(lesson["price"]), xalign=0)
        price.add_css_class("ol-price")
        foot = Gtk.Box(spacing=8)
        status = Gtk.Label(label=db.CLASS_STATUS_RU[lesson["status"]])
        status.add_css_class("ol-pill")
        status.set_halign(Gtk.Align.START)
        seats_label = Gtk.Label(label=seats, xalign=0, hexpand=True)
        seats_label.add_css_class("ol-meta")
        foot.append(status)
        foot.append(seats_label)
        body.append(meta)
        body.append(teacher)
        body.append(price)
        body.append(foot)
        card.append(body)
        return card

    def _open(self):
        selected = self.board.get_selected_children()
        if not selected:
            alert(self.window, "Выберите занятие")
            return
        class_id = selected[0].get_child().class_id
        present_ready(ClassDialog(self.window, class_id, self.reload), self.window, "Занятие не найдено")

    def _created(self, class_id):
        self.reload()
        self.window.notify(f"Занятие №{class_id} опубликовано")


class EnrollmentsPage(ListPage):
    def __init__(self, window, scope):
        super().__init__(window)
        self.scope = scope
        self.filter = LabeledDrop(
            (
                ("all", "Все"),
                ("confirmed", "Записаны"),
                ("completed", "Были"),
                ("missed", "Не пришли"),
                ("cancelled", "Снятые"),
            )
        )
        self.filter.connect("notify::selected", lambda *_: self.reload())
        self.search = Gtk.SearchEntry(placeholder_text="Поиск по занятию или имени")
        self.search.set_hexpand(True)
        self.search.connect("search-changed", lambda *_: self.reload())
        open_btn = Gtk.Button(label="Открыть занятие")
        open_btn.connect("clicked", lambda *_: self._open())
        cancel = Gtk.Button(label="Снять запись")
        cancel.connect("clicked", lambda *_: self._cancel())
        self._bar(self.filter, self.search, open_btn, cancel)
        self._finish_table(on_activate=self._open)
        self._ready = True

    def reload(self):
        if not self._ready:
            return
        user = self.window.user
        if self.scope == "mine":
            rows = db.list_enrollments(student_id=user["id"])
        elif self.scope == "teacher":
            rows = db.list_enrollments(teacher_id=user["id"])
        else:
            rows = db.list_enrollments()
        mode = self.filter.value()
        query = self.search.get_text().strip().casefold()
        shown = []
        for row in rows:
            if mode != "all" and row["status"] != mode:
                continue
            blob = f"{row['class_title']} {row['student_name']} {row['teacher_name']}".casefold()
            if query and query not in blob:
                continue
            shown.append(
                (
                    row["id"],
                    row["class_title"],
                    row["class_date"],
                    row["student_name"],
                    row["teacher_name"],
                    money(row["price"]),
                    db.ENROLL_STATUS_RU[row["status"]],
                )
            )
        self._fill(shown)

    def _open(self):
        enrollment_id = self._selected()
        if enrollment_id is None:
            alert(self.window, "Выберите запись")
            return
        row = db.get_enrollment(enrollment_id)
        present_ready(ClassDialog(self.window, row["class_id"], self.reload), self.window, "Занятие не найдено")

    def _cancel(self):
        enrollment_id = self._selected()
        if enrollment_id is None:
            alert(self.window, "Выберите запись")
            return

        def apply():
            ok, message = db.cancel_enrollment(enrollment_id, self.window.user["id"])
            if not ok:
                alert(self.window, "Не удалось", message)
                return
            self.window.notify(message)
            self.reload()

        confirm(self.window, "Снять запись?", "Место вернётся в занятие.", apply)


class ProductsPage(ListPage):
    def __init__(self, window, scope):
        super().__init__(window)
        self.scope = scope
        self.filter = LabeledDrop([("all", "Все"), *list(db.PRODUCT_CATEGORY_RU.items())])
        self.filter.connect("notify::selected", lambda *_: self.reload())
        self.search = Gtk.SearchEntry(placeholder_text="Поиск по названию или костюмеру")
        self.search.set_hexpand(True)
        self.search.connect("search-changed", lambda *_: self.reload())
        widgets = [self.filter, self.search]
        if scope == "market":
            buy = Gtk.Button(label="Запросить")
            buy.add_css_class("suggested-action")
            buy.connect("clicked", lambda *_: self._buy())
            widgets.append(buy)
        else:
            if scope == "mine" or (scope == "all" and self.window.user["role"] == "admin"):
                add = Gtk.Button(label="Добавить")
                add.add_css_class("suggested-action")
                add.connect("clicked", lambda *_: self._create())
                widgets.append(add)
            edit = Gtk.Button(label="Изменить")
            edit.connect("clicked", lambda *_: self._edit())
            widgets.append(edit)
        self._bar(*widgets)
        self.use_cards = scope == "market"
        if self.use_cards:
            self.board = Gtk.FlowBox(
                selection_mode=Gtk.SelectionMode.SINGLE,
                max_children_per_line=3,
                min_children_per_line=1,
                column_spacing=8,
                row_spacing=8,
                homogeneous=True,
            )
            self.board.add_css_class("ol-board")
            self.board.set_activate_on_single_click(False)
            self.board.connect("child-activated", lambda *_: self._buy())
            self.append(scrolled(self.board))
            self.count = Gtk.Label(xalign=0)
            self.count.add_css_class("ol-meta")
            self.append(self.count)
        else:
            self._finish_table(on_activate=self._edit)
        self._ready = True

    def reload(self):
        if not self._ready:
            return
        if self.scope == "market":
            rows = db.list_products(only_market=True)
        elif self.scope == "mine":
            rows = db.list_products(atelier_id=self.window.user["id"])
        else:
            rows = db.list_products()
        mode = self.filter.value()
        query = self.search.get_text().strip().casefold()
        shown = []
        for product in rows:
            if mode != "all" and product["category"] != mode:
                continue
            blob = f"{product['name']} {product['atelier_name']} {product['size']}".casefold()
            if query and query not in blob:
                continue
            shown.append(product)
        if self.use_cards:
            clear_box(self.board)
            for product in shown:
                self.board.append(self._card(product))
            first = self.board.get_child_at_index(0)
            if first is not None:
                self.board.select_child(first)
            self.count.set_text(f"{len(shown)} костюмов" if shown else "Костюмерная пуста")
            return
        self._fill(
            [
                (
                    product["id"],
                    product["name"],
                    db.PRODUCT_CATEGORY_RU[product["category"]],
                    db.STYLE_RU[product["style"]],
                    f"размер {product['size'] or '—'}",
                    f"свободно {product['stock']}",
                    product["atelier_name"],
                    "в костюмерной" if product["is_active"] else "скрыт",
                )
                for product in shown
            ]
        )

    def _card(self, product):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.add_css_class("ol-card")
        card.product_id = product["id"]
        band = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        band.add_css_class("ol-band")
        band.add_css_class(STYLE_TONE.get(product["style"], "ol-plum"))
        place = Gtk.Label(label=db.PRODUCT_CATEGORY_RU[product["category"]].upper(), xalign=0)
        place.add_css_class("ol-kicker")
        title = Gtk.Label(label=product["name"], xalign=0, wrap=True)
        title.add_css_class("ol-card-title")
        band.append(place)
        band.append(title)
        card.append(band)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        body.add_css_class("ol-card-body")
        style = Gtk.Label(label=db.STYLE_RU[product["style"]], xalign=0)
        style.add_css_class("ol-price")
        size = Gtk.Label(label=f"Размер: {product['size'] or 'любой'}", xalign=0)
        size.add_css_class("ol-meta")
        stock = Gtk.Label(
            label="нет в наличии" if product["stock"] <= 0 else f"свободно единиц: {product['stock']}",
            xalign=0,
        )
        stock.add_css_class("ol-meta")
        who = Gtk.Label(label=product["atelier_name"], xalign=0)
        who.add_css_class("ol-meta")
        body.append(style)
        body.append(size)
        body.append(stock)
        body.append(who)
        card.append(body)
        return card

    def _selected_product(self):
        if self.use_cards:
            selected = self.board.get_selected_children()
            if not selected:
                alert(self.window, "Выберите костюм")
                return None
            return selected[0].get_child().product_id
        product_id = self._selected()
        if product_id is None:
            alert(self.window, "Выберите костюм")
            return None
        return product_id

    def _buy(self):
        product_id = self._selected_product()
        if product_id is None:
            return
        present_ready(
            BuyDialog(self.window, product_id, self._bought),
            self.window,
            "Этого костюма сейчас нет в наличии",
        )

    def _bought(self, order_id):
        self.reload()
        self.window.notify(f"Запрос на костюм №{order_id} отправлен")

    def _create(self):
        dialog = ProductDialog(self.window, None, self._saved)
        if dialog.ready:
            dialog.present()

    def _edit(self):
        product_id = self._selected_product()
        if product_id is None:
            return
        present_ready(ProductDialog(self.window, product_id, self._saved), self.window, "Костюм не найден")

    def _saved(self, product_id, message):
        self.reload()
        self.window.notify(message)


class OrdersPage(ListPage):
    def __init__(self, window, scope):
        super().__init__(window)
        self.scope = scope
        self.filter = LabeledDrop(
            (
                ("all", "Все"),
                ("new", "Запрошенные"),
                ("accepted", "Принятые"),
                ("issued", "Выданные"),
                ("returned", "Возвращённые"),
                ("cancelled", "Отменённые"),
            )
        )
        self.filter.connect("notify::selected", lambda *_: self.reload())
        self.search = Gtk.SearchEntry(placeholder_text="Поиск по костюму, ученику, костюмеру")
        self.search.set_hexpand(True)
        self.search.connect("search-changed", lambda *_: self.reload())
        open_btn = Gtk.Button(label="Открыть")
        open_btn.connect("clicked", lambda *_: self._open())
        self._bar(self.filter, self.search, open_btn)
        self._finish_table(on_activate=self._open)
        self._ready = True

    def reload(self):
        if not self._ready:
            return
        user = self.window.user
        if self.scope == "mine":
            rows = db.list_orders(student_id=user["id"])
        elif self.scope == "incoming":
            rows = db.list_orders(atelier_id=user["id"])
        else:
            rows = db.list_orders()
        mode = self.filter.value()
        query = self.search.get_text().strip().casefold()
        shown = []
        for order in rows:
            if mode != "all" and order["status"] != mode:
                continue
            blob = f"{order['items_label'] or ''} {order['student_name']} {order['atelier_name']}".casefold()
            if query and query not in blob:
                continue
            shown.append(
                (
                    order["id"],
                    order["items_label"] or "—",
                    order["student_name"],
                    order["atelier_name"],
                    order["created_at"],
                    db.ORDER_STATUS_RU[order["status"]],
                )
            )
        self._fill(shown)

    def _open(self):
        order_id = self._selected()
        if order_id is None:
            alert(self.window, "Выберите выдачу")
            return
        present_ready(OrderDialog(self.window, order_id, self.reload), self.window, "Выдача недоступна")

    def apply_filter(self, mode):
        self.filter.set_value(mode)


class ProgressPage(Gtk.ScrolledWindow):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(8)
        box.set_margin_bottom(20)

        self.rank_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.rank_panel.add_css_class("ol-panel")
        top = Gtk.Box(spacing=12)
        self.rank_name = Gtk.Label(xalign=0)
        self.rank_name.add_css_class("ol-rank-name")
        self.rank_name.set_hexpand(True)
        self.xp_num = Gtk.Label(xalign=1)
        self.xp_num.add_css_class("ol-xp-num")
        top.append(self.rank_name)
        top.append(self.xp_num)
        self.rank_panel.append(top)
        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(True)
        self.rank_panel.append(self.progress)
        self.rank_hint = Gtk.Label(xalign=0)
        self.rank_hint.add_css_class("ol-meta")
        self.rank_panel.append(self.rank_hint)
        box.append(self.rank_panel)

        badges_heading = Gtk.Label(label="Значки", xalign=0)
        badges_heading.add_css_class("ol-strip-title")
        box.append(badges_heading)
        self.badges = Gtk.FlowBox(
            selection_mode=Gtk.SelectionMode.NONE,
            homogeneous=True,
            max_children_per_line=4,
            min_children_per_line=2,
            column_spacing=8,
            row_spacing=8,
        )
        box.append(self.badges)

        lower = Gtk.Box(spacing=12)
        lower.set_homogeneous(True)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        left_heading = Gtk.Label(label="Последние начисления", xalign=0)
        left_heading.add_css_class("ol-strip-title")
        left.append(left_heading)
        self.history = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.append(self.history)
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right_heading = Gtk.Label(label="Доска опыта", xalign=0)
        right_heading.add_css_class("ol-strip-title")
        right.append(right_heading)
        self.board = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        right.append(self.board)
        lower.append(left)
        lower.append(right)
        box.append(lower)
        self.set_child(box)

    def reload(self):
        user = db.get_user(self.window.user["id"]) or self.window.user
        self.window.user = user
        if self.window.shell is not None:
            self.window.shell.sync_identity()
        rank = db.rank_of(user["xp"])
        self.rank_name.set_text(rank["name"])
        self.xp_num.set_text(f"{rank['xp']} XP")
        self.progress.set_fraction(rank["fraction"])
        if rank["next_name"] is None:
            self.progress.set_text("Высшая ступень")
            self.rank_hint.set_text("Дальше только сцена.")
        else:
            self.progress.set_text(f"{rank['xp']} / {rank['next_at']}")
            self.rank_hint.set_text(f"До ступени «{rank['next_name']}» осталось {rank['next_at'] - rank['xp']} XP")

        clear_box(self.badges)
        for badge in db.badge_board(user["id"]):
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            card.add_css_class("ol-badge")
            if not badge["unlocked"]:
                card.add_css_class("locked")
            title = Gtk.Label(label=badge["title"], xalign=0)
            title.add_css_class("ol-badge-title")
            detail = Gtk.Label(label=badge["detail"], xalign=0, wrap=True)
            detail.add_css_class("ol-badge-detail")
            bonus = Gtk.Label(
                label=("+" + str(badge["bonus"]) + " XP") if badge["unlocked"] else (str(badge["bonus"]) + " XP, закрыт"),
                xalign=0,
            )
            bonus.add_css_class("ol-bonus")
            card.append(title)
            card.append(detail)
            card.append(bonus)
            self.badges.append(card)

        clear_box(self.history)
        entries = db.list_xp(user["id"], 6)
        if not entries:
            empty = Gtk.Label(label="Начислений ещё нет", xalign=0)
            empty.add_css_class("ol-meta")
            self.history.append(empty)
        for entry in entries:
            self.history.append(
                Adw.ActionRow(
                    title=f"+{entry['amount']} XP · {entry['reason']}",
                    subtitle=entry["created_at"],
                )
            )

        clear_box(self.board)
        for place, item in enumerate(db.leaderboard(6), start=1):
            row = Adw.ActionRow(title=f"{place}. {item['full_name']}", subtitle=item["rank_name"])
            xp = Gtk.Label(label=f"{item['xp']} XP")
            xp.add_css_class("ol-pill")
            xp.set_valign(Gtk.Align.CENTER)
            row.add_suffix(xp)
            self.board.append(row)


class ShellView(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.window = window
        self._switching = False
        self._navs = []

        top = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        top.add_css_class("ol-top")

        bar = Gtk.Box(spacing=12)
        brand_row = Gtk.Box(spacing=10)
        brand_row.set_valign(Gtk.Align.CENTER)
        brand_row.append(logo_image(44))
        brand = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        kicker = Gtk.Label(label="Студия танца", xalign=0)
        kicker.add_css_class("ol-tagline")
        word = Gtk.Label(label="Олеся", xalign=0)
        word.add_css_class("ol-wordmark")
        brand.append(word)
        brand.append(kicker)
        brand_row.append(brand)
        bar.append(brand_row)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        bar.append(spacer)

        role_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        role_box.add_css_class("ol-role")
        role_box.set_valign(Gtk.Align.CENTER)
        self.identity_name = Gtk.Label(xalign=1, ellipsize=Pango.EllipsizeMode.END, max_width_chars=22)
        self.identity_name.add_css_class("ol-role-name")
        self.identity_meta = Gtk.Label(xalign=1, ellipsize=Pango.EllipsizeMode.END, max_width_chars=28)
        self.identity_meta.add_css_class("ol-role-meta")
        role_box.append(self.identity_name)
        role_box.append(self.identity_meta)
        bar.append(role_box)

        logout = Gtk.Button(label="Выйти")
        logout.add_css_class("ol-quiet")
        logout.set_valign(Gtk.Align.CENTER)
        logout.connect("clicked", lambda *_: window.show_login())
        bar.append(logout)
        top.append(bar)

        self.nav_box = Gtk.FlowBox()
        self.nav_box.add_css_class("ol-navrow")
        self.nav_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.nav_box.set_homogeneous(False)
        self.nav_box.set_max_children_per_line(12)
        self.nav_box.set_min_children_per_line(1)
        self.nav_box.set_column_spacing(4)
        self.nav_box.set_row_spacing(4)
        top.append(self.nav_box)
        self.append(top)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        content.add_css_class("ol-content")
        content.set_hexpand(True)
        content.set_vexpand(True)
        head = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        head.add_css_class("ol-head")
        self.kicker = Gtk.Label(xalign=0)
        self.kicker.add_css_class("ol-kicker")
        self.banner = Gtk.Label(xalign=0)
        self.banner.add_css_class("ol-display")
        head.append(self.kicker)
        head.append(self.banner)
        content.append(head)
        self.stack = Gtk.Stack()
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        content.append(self.stack)
        self.append(content)

        self.pages = {}
        self._nav_meta = []
        menu = self._menu(window.user["role"])
        for key, title, hint, factory in menu:
            self._nav_meta.append((key, title, hint))
            page = factory()
            self.pages[key] = page
            self.stack.add_named(page, key)
            button = Gtk.ToggleButton(label=title)
            button.add_css_class("flat")
            button.add_css_class("ol-nav")
            button.connect("toggled", self._on_nav, key, title, hint)
            self._navs.append(button)
            self.nav_box.append(button)
        self._navs[0].set_active(True)
        self.sync_identity()

    def _menu(self, role):
        window = self.window
        if role == "admin":
            return (
                ("overview", "Сводка", "Как живёт студия", lambda: OverviewPage(window)),
                ("users", "Люди", "Ученики, педагоги и костюмеры", lambda: UsersPage(window)),
                ("requests", "Заявки", "Индивидуальные уроки", lambda: RequestsPage(window, "all")),
                ("classes", "Занятия", "Расписание залов", lambda: ClassesPage(window, "all")),
                ("enrollments", "Журнал", "Кто записан и кто был", lambda: EnrollmentsPage(window, "all")),
                ("orders", "Выдачи", "Запросы в костюмерную", lambda: OrdersPage(window, "all")),
                ("products", "Костюмерная", "Костюмы, обувь и реквизит", lambda: ProductsPage(window, "all")),
            )
        if role == "teacher":
            return (
                ("free", "Свободные", "Заявки без педагога", lambda: RequestsPage(window, "free")),
                ("queue", "Мои уроки", "Заявки, которые вы ведёте", lambda: RequestsPage(window, "queue")),
                ("classes", "Занятия", "Ваше расписание", lambda: ClassesPage(window, "mine")),
                ("enrollments", "Журнал", "Кто записан и кто был", lambda: EnrollmentsPage(window, "teacher")),
            )
        if role == "atelier":
            return (
                ("products", "Костюмерная", "Что можно выдать", lambda: ProductsPage(window, "mine")),
                ("orders", "Выдачи", "Принять, выдать, принять возврат", lambda: OrdersPage(window, "incoming")),
            )
        return (
            ("classes", "Расписание", "Куда можно записаться", lambda: ClassesPage(window, "catalog")),
            ("enrollments", "Мои записи", "Ваши занятия", lambda: EnrollmentsPage(window, "mine")),
            ("new", "Новый урок", "Индивидуальная заявка педагогу", lambda: NewRequestPage(window)),
            ("requests", "Мои уроки", "Статус и переписка", lambda: RequestsPage(window, "mine")),
            ("market", "Костюмерная", "Костюмы, обувь и реквизит", lambda: ProductsPage(window, "market")),
            ("orders", "Мои выдачи", "Что взяли и что нужно вернуть", lambda: OrdersPage(window, "mine")),
            ("progress", "Прогресс", "Ступень, значки и опыт", lambda: ProgressPage(window)),
        )

    def _on_nav(self, button, key, title, hint):
        if self._switching:
            return
        if not button.get_active():
            if not any(item.get_active() for item in self._navs):
                self._switching = True
                button.set_active(True)
                self._switching = False
            return
        self._switching = True
        for other in self._navs:
            if other is not button:
                other.set_active(False)
        self._switching = False
        self.banner.set_label(title)
        self.kicker.set_label(hint)
        self.stack.set_visible_child_name(key)
        page = self.pages.get(key)
        if page is not None:
            page.reload()

    def open_page(self, key, filter_mode=None):
        for index, (nav_key, title, hint) in enumerate(self._nav_meta):
            if nav_key != key:
                continue
            page = self.pages.get(key)
            if page is not None and filter_mode is not None and hasattr(page, "apply_filter"):
                page.apply_filter(filter_mode)
            self._switching = True
            for other in self._navs:
                other.set_active(False)
            self._navs[index].set_active(True)
            self._switching = False
            self.banner.set_label(title)
            self.kicker.set_label(hint)
            self.stack.set_visible_child_name(key)
            if page is not None:
                page.reload()
            return

    def sync_identity(self):
        user = self.window.user
        self.identity_name.set_text(user["full_name"])
        text = db.ROLE_RU[user["role"]]
        if user["role"] in ("teacher", "atelier"):
            text = f"{text} · {db.BRANCH_RU[user['branch']]}"
        elif user["role"] == "student":
            text = f"{text} · {db.rank_of(user['xp'])['name']}"
        self.identity_meta.set_text(text)

    def reload_visible(self):
        page = self.stack.get_visible_child()
        if page is not None:
            page.reload()


class LoginView(Gtk.CenterBox):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self._switching = False
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.add_css_class("ol-login-bg")

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        card.add_css_class("ol-login-card")
        card.set_size_request(380, -1)

        mark = logo_image(88)
        mark.set_halign(Gtk.Align.CENTER)
        kicker = Gtk.Label(label="Студия танца «Олеся»")
        kicker.add_css_class("ol-kicker")
        kicker.set_halign(Gtk.Align.CENTER)
        self.form_title = Gtk.Label(label="С возвращением")
        self.form_title.add_css_class("ol-display")
        self.form_title.set_halign(Gtk.Align.CENTER)
        modes = Gtk.Box(spacing=6, halign=Gtk.Align.CENTER)
        self.mode_login = Gtk.ToggleButton(label="Вход")
        self.mode_reg = Gtk.ToggleButton(label="Я здесь впервые")
        for button in (self.mode_login, self.mode_reg):
            button.add_css_class("flat")
            button.add_css_class("ol-seg")
            modes.append(button)
        self.mode_login.connect("toggled", self._show_login_mode)
        self.mode_reg.connect("toggled", self._show_register_mode)
        self.stack = Gtk.Stack()
        self.stack.set_hexpand(True)
        self.stack.add_named(self._login_form(), "login")
        self.stack.add_named(self._register_form(), "register")

        card.append(mark)
        card.append(kicker)
        card.append(self.form_title)
        card.append(modes)
        card.append(self.stack)

        clamp = Adw.Clamp(maximum_size=430)
        clamp.set_halign(Gtk.Align.CENTER)
        clamp.set_valign(Gtk.Align.CENTER)
        clamp.set_child(card)
        self.set_center_widget(clamp)
        self.mode_login.set_active(True)

    def _login_form(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_hexpand(True)
        group = Adw.PreferencesGroup()
        self.login = Adw.EntryRow(title="Логин")
        self.password = Adw.PasswordEntryRow(title="Пароль")
        self.login.connect("entry-activated", lambda *_: self.password.grab_focus())
        self.password.connect("entry-activated", lambda *_: self._login())
        group.add(self.login)
        group.add(self.password)
        box.append(group)
        self.login_error = Gtk.Label(xalign=0, wrap=True, visible=False)
        self.login_error.add_css_class("ol-error")
        box.append(self.login_error)
        button = Gtk.Button(label="Войти")
        button.add_css_class("suggested-action")
        button.add_css_class("pill")
        button.connect("clicked", lambda *_: self._login())
        box.append(button)
        return box

    def _register_form(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_hexpand(True)
        group = Adw.PreferencesGroup(description="Так появляется ученик. Роль педагога или костюмера назначает администратор.")
        self.reg_name = Adw.EntryRow(title="ФИО")
        self.reg_login = Adw.EntryRow(title="Логин")
        self.reg_password = Adw.PasswordEntryRow(title="Пароль")
        self.reg_repeat = Adw.PasswordEntryRow(title="Пароль ещё раз")
        self.reg_repeat.connect("entry-activated", lambda *_: self._register())
        group.add(self.reg_name)
        group.add(self.reg_login)
        group.add(self.reg_password)
        group.add(self.reg_repeat)
        box.append(group)
        self.reg_error = Gtk.Label(xalign=0, wrap=True, visible=False)
        self.reg_error.add_css_class("ol-error")
        box.append(self.reg_error)
        button = Gtk.Button(label="Зарегистрироваться")
        button.add_css_class("suggested-action")
        button.add_css_class("pill")
        button.connect("clicked", lambda *_: self._register())
        box.append(button)
        return box

    def _show_login_mode(self, button):
        if self._switching:
            return
        if not button.get_active():
            if not self.mode_reg.get_active():
                self._switching = True
                button.set_active(True)
                self._switching = False
            return
        self._switching = True
        self.mode_reg.set_active(False)
        self._switching = False
        self.form_title.set_label("С возвращением")
        self.stack.set_visible_child_name("login")

    def _show_register_mode(self, button):
        if self._switching:
            return
        if not button.get_active():
            if not self.mode_login.get_active():
                self._switching = True
                button.set_active(True)
                self._switching = False
            return
        self._switching = True
        self.mode_login.set_active(False)
        self._switching = False
        self.form_title.set_label("Первый выход")
        self.stack.set_visible_child_name("register")

    def _login(self):
        user, error = db.authenticate(self.login.get_text(), self.password.get_text())
        if error:
            self.login_error.set_text(error)
            self.login_error.set_visible(True)
            return
        self.window.show_shell(user)

    def _register(self):
        if self.reg_password.get_text() != self.reg_repeat.get_text():
            self.reg_error.set_text("Пароли не совпадают")
            self.reg_error.set_visible(True)
            return
        ok, message = db.create_user(
            self.reg_login.get_text(),
            self.reg_password.get_text(),
            self.reg_name.get_text(),
            role="student",
        )
        if not ok:
            self.reg_error.set_text(message)
            self.reg_error.set_visible(True)
            return
        user, error = db.authenticate(self.reg_login.get_text(), self.reg_password.get_text())
        if error:
            self.reg_error.set_text(error)
            self.reg_error.set_visible(True)
            return
        self.window.show_shell(user)
        self.window.notify("Учётная запись создана")


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application)
        self.set_title("Студия «Олеся»")
        self.set_default_size(1220, 800)
        self.user = None
        self.shell = None
        self.add_css_class("ol-app")
        self.toast = Adw.ToastOverlay()
        self.toolbar = Adw.ToolbarView()
        self.heading = Gtk.Label(label="Студия «Олеся»")
        self.heading.add_css_class("ol-heading")
        header = Adw.HeaderBar()
        header.add_css_class("flat")
        header.add_css_class("ol-titlebar")
        header.set_title_widget(self.heading)
        self.toolbar.add_top_bar(header)
        self.toast.set_child(self.toolbar)
        self.set_content(self.toast)
        self.show_login()

    def notify(self, text):
        self.toast.add_toast(Adw.Toast(title=text))

    def show_login(self):
        self.user = None
        self.shell = None
        self.toolbar.set_content(LoginView(self))

    def show_shell(self, user):
        self.user = user
        self.shell = ShellView(self)
        self.toolbar.set_content(self.shell)

    def refresh_session(self):
        fresh = db.get_user(self.user["id"])
        if not fresh or not fresh["is_active"]:
            self.notify("Сессия завершена")
            self.show_login()
            return
        role_changed = fresh["role"] != self.user["role"]
        self.user = fresh
        if role_changed or self.shell is None:
            self.show_shell(fresh)
            self.notify("Роль изменена, меню обновлено")
            return
        self.shell.sync_identity()
        self.shell.reload_visible()
        self.notify("Профиль обновлён")


class OlesyaApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="ru.olesya.Desktop")
        self.connect("activate", self._activate)

    def _activate(self, _app):
        if getattr(self, "win", None) is not None:
            self.win.present()
            return
        db.init_db()
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        provider = Gtk.CssProvider()
        provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER,
        )
        self.win = MainWindow(self)
        self.win.present()


def main():
    app = OlesyaApp()
    return app.run(None)
