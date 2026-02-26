from aiogram import Dispatcher

# ==========================
# Команды
# ==========================
from handlers.profile import router as profile_router
from commands.start import router as start_router
from commands.menu import router as menu_router
from commands.daily_bonus import router as daily_bonus_router
from commands.cars import router as cars_router
from commands.phones import router as phones_router
from commands.planes import router as planes_router
from commands.yachts import router as yachts_router
from commands.helicopters import router as helicopters_router
from commands.houses import router as houses_router
from commands.nick import router as nick_router
from commands.rp import router as rp_router
from commands.heist import router as heist_router
from commands.bitcoin import router as bitcoin_router
from commands.balance import router as balance_router
from commands.kazna import router as kazna_router
from commands.bank import router as bank_router
from commands.inventory import router as inventory_router
from commands.transfer import router as transfer_router
from commands import check_business
from commands.chat import router as chat_router
from commands.give_money import router as give_money_router

# ===== Бизнесы =====
from commands.business.larek import larek_router
from commands.business.vape_shop import router as vape_router
from commands.business.withdraw import router as withdraw_router
from commands.business.store import store_router
from commands.business.security import security_router as sec_router
from commands.business.nightclub import router as club_router
from commands.business.stripclub import stripclub_router
from commands.business.autosalon import autosalon_router
from commands.business.casinos import casinos_router
from commands.business.yachtclub import yacht_router
from commands.business.investbank import invest_router
from commands.business.lab import lab_router
from commands.business.spaceport import space_router
from commands.business.corporation import corp_router
from commands.business.itholding import itholding_router
from commands.business.quantum_station import quantum_router
from commands.business.drug_control import drug_router

# ===== Руда =====
from commands.ores_market import router as ores_market_router
from commands.ores_rate import router as ores_rate_router
from commands.mine.mine_dig import router as mine_dig_router
from commands.mine.energy import router as energy_router
from commands.mine.mine_menu import router as mine_menu_router
from commands.mine.refill_energy import router as refill_energy_router

# ===== Inline =====
from handlers.callback_handler import router as callback_router

# ===== Игры =====
from commands.games.dice import router as dice_router
from commands.games.casino import router as casino_router
from commands.games.slot import router as slot_router
from commands.games.basketball import router as basketball_router
from commands.games.darts import router as darts_router
from commands.games.bowling import router as bowling_router
from commands.games.trade import router as trade_router
from commands.games.choose import choose_router
from commands.games.info import info_router
from commands.games.ball import ball_router
from commands.games.marry import marry_router
from commands.games.duel import duel_router
from commands.business import forbes
from commands.games.top_games import router as top_games_router
from commands.top import router as top_router

# ===== охота =====
from commands.hunt.loot_rate import router as loot_rate_router
from commands.hunt.hunt_help import router as hunt_help_router
from commands.hunt.hunt import router as hunt_router
from commands.hunt import top_hunters

# ===== админс =====
from commands import terms
from commands.admins.admin_panel import admin_router

# ===== Донат =====
from commands.donate.donate import donate_router
from commands.donate.statuses import statuses_router
from commands.donate.give_coins import donate_router as give_coins_router
from commands.donate.vip_status import status_router
from commands.donate.admins import router as admins_router

# ===== клан =====
from commands.klans.klans import klans_router
from commands.klans.klans_manage import klans_manage_router
from commands.klans.clan_war import router as clan_war_router

def setup_dispatcher(dp: Dispatcher):
    # ================= Команды = ================
    dp.include_router(profile_router)
    dp.include_router(klans_manage_router)
    dp.include_router(start_router)
    dp.include_router(menu_router)
    dp.include_router(daily_bonus_router)
    dp.include_router(cars_router)
    dp.include_router(phones_router)
    dp.include_router(planes_router)
    dp.include_router(yachts_router)
    dp.include_router(helicopters_router)
    dp.include_router(houses_router)
    dp.include_router(nick_router)
    dp.include_router(rp_router)
    dp.include_router(heist_router)
    dp.include_router(bitcoin_router)
    dp.include_router(balance_router)
    dp.include_router(kazna_router)
    dp.include_router(bank_router)
    dp.include_router(inventory_router)
    dp.include_router(transfer_router)
    dp.include_router(check_business.router)
    dp.include_router(chat_router)
    dp.include_router(give_money_router)

    # ===== Бизнесы =====
    dp.include_router(larek_router)
    dp.include_router(vape_router)
    dp.include_router(withdraw_router)
    dp.include_router(store_router)
    dp.include_router(sec_router)
    dp.include_router(club_router)
    dp.include_router(stripclub_router)
    dp.include_router(autosalon_router)
    dp.include_router(casinos_router)
    dp.include_router(yacht_router)
    dp.include_router(invest_router)
    dp.include_router(lab_router)
    dp.include_router(space_router)
    dp.include_router(corp_router)
    dp.include_router(quantum_router)
    dp.include_router(drug_router)
    dp.include_router(itholding_router)

    # ===== Руда =====
    dp.include_router(ores_market_router)
    dp.include_router(ores_rate_router)
    dp.include_router(mine_dig_router)
    dp.include_router(energy_router)
    dp.include_router(mine_menu_router)
    dp.include_router(refill_energy_router)

    # ===== Inline =====
    dp.include_router(callback_router)

    # ===== Игры =====
    dp.include_router(dice_router)
    dp.include_router(casino_router)
    dp.include_router(slot_router)
    dp.include_router(basketball_router)
    dp.include_router(darts_router)
    dp.include_router(bowling_router)
    dp.include_router(trade_router)
    dp.include_router(choose_router)
    dp.include_router(info_router)
    dp.include_router(ball_router)
    dp.include_router(marry_router)
    dp.include_router(duel_router)
    dp.include_router(forbes.router)
    dp.include_router(top_games_router)
    dp.include_router(top_router)
    dp.include_router(status_router)

    # ===== охота =====
    dp.include_router(loot_rate_router)
    dp.include_router(hunt_help_router)
    dp.include_router(hunt_router)
    dp.include_router(top_hunters.router)

    # ===== админс =====
    dp.include_router(terms.router)
    dp.include_router(admin_router)

    # ===== Донат =====
    dp.include_router(donate_router)
    dp.include_router(statuses_router)
    dp.include_router(give_coins_router)
    dp.include_router(admins_router)

    # ===== кланы =====
    dp.include_router(klans_router)
    dp.include_router(clan_war_router)

