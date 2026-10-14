"""Подбор педагога на заявку.

Балл активного педагога:
    * стиль совпал с заявкой: +40;
    * универсальный педагог: +12;
    * та же площадка: +18;
    * педагог с площадкой «любая»: +8;
    * средняя оценка × 4, а если оценок нет — нейтральные 4,2 × 4;
    * за каждую заявку в работе снимаются баллы, у срочной штраф больше;
    * педагог с четырьмя и более активными заявками не выбирается, пока есть кто-то ниже предела.
"""

from olesya import db

STYLE_BONUS = 40
UNIVERSAL_BONUS = 12
BRANCH_BONUS = 18
ANY_BRANCH_BONUS = 8
RATING_WEIGHT = 4
NEUTRAL_RATING = 4.2
MAX_ACTIVE = 4
LOAD_WEIGHT = {
    "low": 3,
    "normal": 5,
    "high": 9,
}
PRIORITY_RANK = {"high": 0, "normal": 1, "low": 2}


def _rating(teacher):
    value = db.teacher_rating(teacher)
    if value is None:
        return NEUTRAL_RATING
    return value


def score_teacher(teacher, style, branch, priority, load):
    """Возвращает (score, reasons). Чем больше score, тем лучше кандидат."""
    reasons = []
    score = 0.0

    if teacher["style"] == style:
        score += STYLE_BONUS
        reasons.append(f"стиль совпал +{STYLE_BONUS}")
    elif teacher["style"] == "other":
        score += UNIVERSAL_BONUS
        reasons.append(f"универсальный педагог +{UNIVERSAL_BONUS}")
    else:
        reasons.append("стиль не совпал")

    if branch != "other" and teacher["branch"] == branch:
        score += BRANCH_BONUS
        reasons.append(f"та же площадка +{BRANCH_BONUS}")
    elif teacher["branch"] == "other":
        score += ANY_BRANCH_BONUS
        reasons.append(f"работает на разных площадках +{ANY_BRANCH_BONUS}")
    else:
        reasons.append("другая площадка")

    rating = _rating(teacher)
    rating_points = rating * RATING_WEIGHT
    score += rating_points
    if db.teacher_rating(teacher) is None:
        reasons.append(f"оценок пока нет, нейтральный балл +{rating_points:.1f}")
    else:
        reasons.append(f"рейтинг {rating:.1f} +{rating_points:.1f}")

    penalty = load * LOAD_WEIGHT.get(priority, 5)
    score -= penalty
    reasons.append(f"загрузка {load} (−{penalty})")
    if load >= MAX_ACTIVE:
        reasons.append(f"предел {MAX_ACTIVE} заявок")
    return score, reasons


def pick_teacher(style, branch, priority="normal"):
    """Возвращает (teacher, debug) либо (None, debug), если активных педагогов нет."""
    teachers = db.list_teachers(only_active=True)
    under, over = [], []
    for teacher in teachers:
        load = db.active_load(teacher["id"])
        score, reasons = score_teacher(teacher, style, branch, priority, load)
        item = (score, load, teacher, reasons)
        (over if load >= MAX_ACTIVE else under).append(item)

    pool = under or over
    if not pool:
        return None, ["нет активных педагогов"]

    pool.sort(key=lambda item: (-item[0], item[1], item[2]["id"]))
    best_score, _load, best, best_reasons = pool[0]
    debug = [f"{teacher['full_name']}: {score:.1f}" for score, _load, teacher, _reasons in pool]
    summary = f"Назначен {best['full_name']} (оценка {best_score:.1f})"
    if not under:
        summary += f". Все на пределе {MAX_ACTIVE}, выбран с меньшей загрузкой"
    elif over:
        skipped = ", ".join(teacher["full_name"] for _score, _load, teacher, _reasons in over)
        debug.append(f"Сверх предела {MAX_ACTIVE}: {skipped}")
    debug.insert(0, summary)
    debug[1:1] = best_reasons
    return best, debug


def distribute(request_id, actor_id=None):
    """Назначает педагога на одну заявку. Возвращает (teacher, debug)."""
    request = db.get_request(request_id)
    if not request:
        return None, ["Заявка не найдена"]
    if request["status"] not in ("new", "assigned"):
        return None, ["Заявка уже закрыта"]
    teacher, debug = pick_teacher(request["style"], request["branch"], request["priority"])
    if not teacher:
        return None, debug
    load = db.active_load(teacher["id"])
    _score, reasons = score_teacher(teacher, request["style"], request["branch"], request["priority"], load)
    ok, message = db.assign_request(request_id, teacher["id"], actor_id, note="; ".join(reasons))
    if not ok:
        return None, [message, *debug]
    return teacher, debug


def distribute_pending(actor_id=None):
    """Назначает педагогов на все новые заявки без педагога. Сначала более срочные."""
    pending = [
        request
        for request in db.list_requests()
        if request["teacher_id"] is None and request["status"] == "new"
    ]
    pending.sort(key=lambda request: (PRIORITY_RANK.get(request["priority"], 9), request["id"]))
    lines = []
    assigned = 0
    for request in pending:
        teacher, _debug = distribute(request["id"], actor_id)
        target = teacher["full_name"] if teacher else "нет педагога"
        lines.append(f"№{request['id']} {request['title']} → {target}")
        if teacher:
            assigned += 1
    return assigned, lines
