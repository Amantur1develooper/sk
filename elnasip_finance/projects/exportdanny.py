import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, date, time

from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from openpyxl import load_workbook

from .models import Block, Apartment, DealPayment, ApartmentComment
from .forms import BlockApartmentsImportForm
from finances.models import CommonCash, CashFlow, Sale


def _to_decimal(val):
    if val is None:
        return None
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        val = val.replace(" ", "").replace(",", ".")
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError):
        return None


def _is_empty_cell(val):
    return val is None or (isinstance(val, str) and val.strip() == "")


def _normalize_name(raw):
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    if not re.search(r"[A-Za-zА-Яа-яЁё]", s):
        return ""
    s = re.sub(r"\s+", " ", s).strip(" ,.;:-")
    return s


def _to_int(val, default=0):
    if val is None:
        return default
    try:
        if isinstance(val, str):
            val = val.strip()
            if not val:
                return default
        return int(float(val))
    except (ValueError, TypeError):
        return default


def _clean_apartment_number(raw):
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    return s.split("(")[0].strip()


def _parse_contract_date(val):
    if val is None:
        return timezone.now()

    if isinstance(val, datetime):
        dt = val
    elif isinstance(val, date):
        dt = datetime.combine(val, time(0, 0))
    elif isinstance(val, str):
        s = val.strip()
        dt = None
        for fmt in ("%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(s, fmt)
                break
            except ValueError:
                pass
        if dt is None:
            return timezone.now()
    else:
        return timezone.now()

    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _detect_reserved(text1, text2):
    txt = f"{text1 or ''} {text2 or ''}".lower()
    return "брон" in txt


@login_required
def import_block_apartments_excel(request, block_id):
    block = get_object_or_404(Block, id=block_id)

    if request.method == "GET":
        form = BlockApartmentsImportForm()
        return render(request, "projects/block_apartments_import.html", {"block": block, "form": form})

    form = BlockApartmentsImportForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, "projects/block_apartments_import.html", {"block": block, "form": form})

    xlsx = form.cleaned_data["file"]
    update_existing = form.cleaned_data.get("update_existing", True)
    create_missing = form.cleaned_data.get("create_missing", True)

    if not xlsx.name.lower().endswith(".xlsx"):
        messages.error(request, "Загрузи файл именно .xlsx (новый Excel).")
        return render(request, "projects/block_apartments_import.html", {"block": block, "form": form})

    wb = load_workbook(xlsx, data_only=True)
    ws = wb.active

    headers = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(row=1, column=c).value
        if v:
            headers[str(v).strip()] = c

    required = ["Предварительный номер", "Количество комнат", "Общая площадь ориентировочно", "Оплачено"]
    miss = [h for h in required if h not in headers]
    if miss:
        messages.error(request, f"В файле не хватает колонок: {', '.join(miss)}")
        return render(request, "projects/block_apartments_import.html", {"block": block, "form": form})

    common_cash = CommonCash.objects.first()

    created_cnt = 0
    updated_cnt = 0
    skipped_cnt = 0
    payments_created = 0
    cashflows_created = 0
    errors = []

    for row in range(2, ws.max_row + 1):
        try:
            raw_num = ws.cell(row=row, column=headers["Предварительный номер"]).value
            apt_number = _clean_apartment_number(raw_num)
            if not apt_number:
                continue

            apt_existing = Apartment.objects.filter(block=block, apartment_number=apt_number).first()
            exists = apt_existing is not None

            if exists and not update_existing:
                skipped_cnt += 1
                continue
            if (not exists) and not create_missing:
                skipped_cnt += 1
                continue

            # --- читаем минимум для определения "свободна/не свободна" ---
            fio_raw = ws.cell(row=row, column=headers.get("Ф.И.О.", 0)).value if "Ф.И.О." in headers else None
            fio = _normalize_name(fio_raw)

            note = ws.cell(row=row, column=headers.get("Примечание", 0)).value if "Примечание" in headers else None
            excel_reserved = _detect_reserved(raw_num, note)

            paid_cell = ws.cell(row=row, column=headers["Оплачено"]).value
            paid_total_file = _to_decimal(paid_cell)  # может быть None если пусто/мусор

            # ✅ ТИХИЙ ПРОПУСК: квартира свободна в БД и свободна в Excel → ничего не показываем
            if exists:
                db_free = (not apt_existing.is_sold) and (not apt_existing.is_reserved)
                excel_paid_zero_or_empty = _is_empty_cell(paid_cell) or (paid_total_file == Decimal("0"))
                excel_free = (not fio) and (not excel_reserved) and excel_paid_zero_or_empty
                if db_free and excel_free:
                    skipped_cnt += 1
                    continue

            # если квартира уже есть и "оплачено" пусто -> НЕ меняем и НЕ создаём платежи
            if exists and _is_empty_cell(paid_cell):
                errors.append(f"Строка {row} ({apt_number}): 'Оплачено' пусто — пропущено, данные квартиры НЕ менял.")
                skipped_cnt += 1
                continue

            # если квартира уже есть и "оплачено" не число -> тоже НЕ трогаем
            if exists and (paid_total_file is None):
                errors.append(f"Строка {row} ({apt_number}): 'Оплачено' не число — пропущено, данные квартиры НЕ менял.")
                skipped_cnt += 1
                continue

            # для новой квартиры: если пусто/не число, считаем 0
            if paid_total_file is None:
                paid_total_file = Decimal("0")

            # если Excel меньше, чем уже в платежах -> НЕ МЕНЯЕМ КВАРТИРУ, показываем человеку
            if exists:
                paid_total_db_before = apt_existing.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0")
                if paid_total_file < paid_total_db_before:
                    errors.append(
                        f"Строка {row} ({apt_number}): в Excel оплачено меньше, чем уже есть в платежах. "
                        f"(Excel={paid_total_file}, DB={paid_total_db_before}) — пропущено, данные квартиры НЕ менял."
                    )
                    skipped_cnt += 1
                    continue

            # --- дальше обычный импорт (если не пропустили) ---
            floor = _to_int(ws.cell(row=row, column=headers["Этаж"]).value, default=1) if "Этаж" in headers else 1
            rooms = _to_int(ws.cell(row=row, column=headers["Количество комнат"]).value, default=0)
            area = _to_decimal(ws.cell(row=row, column=headers["Общая площадь ориентировочно"]).value) or Decimal("0")

            phone = ws.cell(row=row, column=headers.get("Телефон", 0)).value if "Телефон" in headers else None
            price_m2 = _to_decimal(ws.cell(row=row, column=headers.get("Цена за 1 м.кв.", 0)).value) if "Цена за 1 м.кв." in headers else None
            sum_contract = _to_decimal(ws.cell(row=row, column=headers.get("Сумма договора", 0)).value) if "Сумма договора" in headers else None

            remaining = _to_decimal(ws.cell(row=row, column=headers.get("Остаток на оплату", 0)).value) if "Остаток на оплату" in headers else None
            if sum_contract is not None and remaining is None:
                remaining = sum_contract - paid_total_file

            contract_dt = _parse_contract_date(ws.cell(row=row, column=headers.get("Дата договора", 0)).value) if "Дата договора" in headers else timezone.now()

            has_fio = bool(fio)
            is_sold = (paid_total_file > 0) or has_fio

            is_reserved = False
            if not is_sold:
                is_reserved = excel_reserved

            defaults = {
                "floor": floor,
                "rooms": rooms,
                "area": area,
                "is_sold": is_sold,
                "is_reserved": (False if is_sold else is_reserved),
                "deal_amount": paid_total_file,
            }

            defaults["client_name"] = fio if fio else None

            if price_m2 is not None:
                defaults["planned_price_per_m2"] = price_m2
                defaults["fact_price_per_m2"] = price_m2

            if sum_contract is not None:
                defaults["deal_Fakt_deal_amount"] = sum_contract

            if remaining is not None:
                defaults["remaining_deal_amount"] = remaining

            with transaction.atomic():
                apt, created_flag = Apartment.objects.update_or_create(
                    block=block,
                    apartment_number=apt_number,
                    defaults=defaults
                )

                if created_flag:
                    created_cnt += 1
                else:
                    updated_cnt += 1

                comment_parts = []
                if note:
                    comment_parts.append(str(note).strip())
                if phone:
                    comment_parts.append(f"Телефон: {phone}")
                if comment_parts:
                    ApartmentComment.objects.get_or_create(
                        apartment=apt,
                        text="[Импорт Excel] " + " | ".join(comment_parts),
                        defaults={"author": request.user.get_username()},
                    )

                paid_total_db = apt.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0")
                delta = paid_total_file - paid_total_db

                if delta > 0:
                    DealPayment.objects.create(
                        apartment=apt,
                        amount=delta,
                        payment_date=contract_dt,
                        comment="Импорт из Excel (добавлено по разнице)",
                        created_by=request.user,
                    )
                    payments_created += 1

                    if common_cash:
                        CashFlow.objects.create(
                            common_cash=common_cash,
                            flow_type="income",
                            amount=delta,
                            description=f"Импорт Excel: оплата кв. {apt.apartment_number} ({block})",
                            block=block,
                            created_by=request.user
                        )
                        cashflows_created += 1

                    Sale.objects.create(
                        block=block,
                        area=0,
                        apartment=apt,
                        amount=delta,
                        client_info=f"{apt.client_name or ''}",
                        created_by=request.user
                    )

        except Exception as e:
            errors.append(f"Строка {row}: {e}")

    messages.success(
        request,
        f"Импорт завершён. Создано: {created_cnt}, обновлено: {updated_cnt}, пропущено: {skipped_cnt}. "
        f"Новых платежей: {payments_created}, транзакций в кассу: {cashflows_created}."
    )

    return render(request, "projects/block_apartments_import.html", {
        "block": block,
        "form": BlockApartmentsImportForm(),
        "created": created_cnt,
        "updated": updated_cnt,
        "skipped": skipped_cnt,
        "payments_created": payments_created,
        "cashflows_created": cashflows_created,
        "errors": errors,
    })



from datetime import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from .models import Block, Apartment


def _dec(val, default=Decimal("0")):
    try:
        return Decimal(val or 0)
    except Exception:
        return default


def _safe_str(val):
    return "" if val is None else str(val).strip()


@login_required
def export_block_apartments_excel(request, block_id):
    """
    Экспорт квартир конкретного блока в .xlsx
    Формат заголовков совместим с import_block_apartments_excel().
    Поддерживает простые фильтры через GET:
      ?only_free=1  -> только свободные
      ?only_rented=1 -> только аренда
      ?only_sold=1  -> только проданные
      ?only_reserved=1 -> только бронь (не проданные)
    """
    block = get_object_or_404(Block, id=block_id)

    qs = Apartment.objects.filter(block=block).prefetch_related("payments", "comments").order_by("floor", "apartment_number")

    # --- фильтры (если нужны) ---
    if request.GET.get("only_free") == "1":
        qs = qs.filter(is_sold=False, is_reserved=False, is_rented=False)
    if request.GET.get("only_rented") == "1":
        qs = qs.filter(is_rented=True)
    if request.GET.get("only_sold") == "1":
        qs = qs.filter(is_sold=True)
    if request.GET.get("only_reserved") == "1":
        qs = qs.filter(is_reserved=True, is_sold=False)

    wb = Workbook()
    ws = wb.active
    ws.title = f"Блок {block.name}"

    headers = [
        "Этаж",
        "Предварительный номер",
        "Количество комнат",
        "Общая площадь ориентировочно",
        "Дата договора",
        "Ф.И.О.",
        "Цена за 1 м.кв.",
        "Сумма договора",
        "Оплачено",
        "Остаток на оплату",
        "Телефон",
        "Примечание",
    ]
    ws.append(headers)

    # ширины колонок (чтобы было удобно)
    widths = [7, 22, 18, 26, 16, 28, 16, 16, 12, 18, 16, 35]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    for apt in qs:
        paid_total = apt.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0")  # важно: как в импорте сравниваешь с платежами
        paid_total = _dec(paid_total)

        contract_sum = _dec(apt.deal_Fakt_deal_amount, default=Decimal("0"))
        if contract_sum <= 0:
            # если суммы договора нет — можно подставить планируемую
            contract_sum = _dec(apt.planned_deal_amount, default=Decimal("0"))

        remaining = _dec(apt.remaining_deal_amount, default=(contract_sum - paid_total))
        if remaining < 0:
            remaining = Decimal("0")

        # дата договора: у тебя явного поля нет — экспортируем created_at (стабильно для обратной загрузки)
        contract_date = apt.created_at.date() if getattr(apt, "created_at", None) else timezone.localdate()

        fio = _safe_str(apt.client_name)

        # телефон: отдельного поля телефона клиента нет — оставим пусто (или можешь заменить на своё поле)
        phone = ""

        # примечание: если бронь — пишем "бронь", чтобы импорт корректно понял
        note_parts = []
        if apt.is_reserved and not apt.is_sold:
            note_parts.append("бронь")

        # (опционально) подтянуть последний комментарий
        last_comment = apt.comments.order_by("-created_at").first()
        if last_comment and last_comment.text:
            txt = last_comment.text.replace("[Импорт Excel]", "").strip()
            if txt:
                note_parts.append(txt[:200])

        note = " | ".join(note_parts)

        ws.append([
            int(apt.floor or 1),
            _safe_str(apt.apartment_number),
            int(apt.rooms or 0),
            float(_dec(apt.area)),
            contract_date.strftime("%d.%m.%Y"),
            fio,
            float(_dec(apt.planned_price_per_m2)),
            float(contract_sum),
            float(paid_total),
            float(remaining),
            phone,
            note,
        ])

    filename = f"block_{block.id}_{block.name}_{timezone.localdate().isoformat()}.xlsx"
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
