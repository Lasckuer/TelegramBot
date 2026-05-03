from aiogram import Router, F, types
from app.handlers.utils import load_subs, db

router = Router()

@router.callback_query(F.data.startswith("subpay_"))
async def process_sub_payment(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[1])
    subs = load_subs()
    if idx < len(subs):
        sub = subs[idx]
        db.add_expense(user_id=callback.from_user.id, category="Ежемесячные", name=sub['name'], price=sub['amount'], shop="-")
        await callback.message.edit_text(f"✅ Оплата <b>{sub['name']}</b> ({sub['amount']}р) занесена в расходы.", parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("subcancel_"))
async def cancel_sub_payment(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[1])
    subs = load_subs()
    if idx < len(subs):
        await callback.message.edit_text(f"❌ Списание <b>{subs[idx]['name']}</b> пропущено.", parse_mode="HTML")
    await callback.answer()