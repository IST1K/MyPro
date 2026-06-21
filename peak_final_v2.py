import time
from javascript import require, On, config
import tkinter as tk
from tkinter import scrolledtext
import _thread

config.timeout = 120

# Блокировка чтобы auto_defense не дергал пока работает другая задача
action_lock = _thread.allocate_lock()

HOST = "localhost"
PORT = 25575
USERNAME = "Peak_Bot!"
VERSION = "1.21.1"

mineflayer = require("mineflayer")
pathfinder = require("mineflayer-pathfinder")
vec3 = require('vec3')

try:
    viewer = require('prismarine-viewer').mineflayer
except:
    viewer = None

bot = mineflayer.createBot({
    'host': HOST,
    'port': PORT,
    'username': USERNAME,
    'version': VERSION,
    'checkTimeoutInterval': 120000
})
bot.loadPlugin(pathfinder.pathfinder)

# Цвета и шрифт
BG  = "#d4d0c8"
BTN = "#ece9d8"
FNT = ("Courier New", 10)

# Главное окно
window = tk.Tk()
window.title("Peak Bot")
window.geometry("380x620")
window.resizable(False, False)
window.configure(bg=BG)

# Заголовок
tk.Label(window, text="Peak Bot Control", font=("Courier New", 16, "bold"), bg=BG).pack(pady=(12, 2))

# Статус подключения
status_var = tk.StringVar(value="Отключено")
status_label = tk.Label(window, textvariable=status_var, font=FNT, fg="red", bg=BG)
status_label.pack()

def set_status(text, color="green"):
    window.after(0, lambda: (status_var.set(text), status_label.config(fg=color)))

# Лог
tk.Label(window, text="Лог:", font=FNT, bg=BG).pack(anchor="w", padx=14)

log_box = scrolledtext.ScrolledText(
    window, height=8, width=45,
    font=("Courier New", 9),
    bg="white", relief="sunken", bd=2,
    state="disabled"
)
log_box.pack(padx=14, pady=(2, 6))

def log(msg):
    print(msg)
    def _upd():
        log_box.config(state="normal")
        log_box.insert(tk.END, msg + "\n")
        log_box.see(tk.END)
        log_box.config(state="disabled")
    try:
        window.after(0, _upd)
    except:
        pass

# Панель управления WASD
frame_wasd = tk.Frame(window, bg=BG, relief="groove", bd=2)
frame_wasd.pack(fill="x", padx=14, pady=4)

tk.Label(frame_wasd, text="Управление:", font=FNT, bg=BG).grid(
    row=0, column=0, columnspan=3, sticky="w", padx=6, pady=2)

def move_control(control, state):
    try:
        bot.setControlState(control, state)
    except:
        pass

def create_wasd_btn(text, control, row, col, columnspan=1):
    btn = tk.Button(
        frame_wasd, text=text, bg=BTN,
        font=("Courier New", 10, "bold"),
        width=5 if columnspan == 1 else 12,
        relief="raised", bd=2
    )
    btn.grid(row=row, column=col, columnspan=columnspan, padx=4, pady=4)
    btn.bind("<ButtonPress-1>",   lambda e: move_control(control, True))
    btn.bind("<ButtonRelease-1>", lambda e: move_control(control, False))

create_wasd_btn("W","forward",1, 1)
create_wasd_btn("A","left",2, 0)
create_wasd_btn("S","back",2, 1)
create_wasd_btn("D","right",2, 2)
create_wasd_btn("Прыжок","jump",1, 2)
create_wasd_btn("Присесть","sneak",1, 0)

# Ползунок радиуса поиска руды
frame_scale = tk.Frame(window, bg=BG, relief="groove", bd=2)
frame_scale.pack(fill="x", padx=14, pady=4)

tk.Label(frame_scale, text="Радиус поиска руды:", font=FNT, bg=BG).pack(anchor="w", padx=6)
radius_var = tk.IntVar(value=33)
tk.Scale(
    frame_scale, from_=10, to=64, orient="horizontal",
    variable=radius_var, bg=BG, font=FNT,
    troughcolor="#a0a098", highlightthickness=0, length=320
).pack(padx=6, pady=(0, 4))

# Поле чата
frame_chat = tk.Frame(window, bg=BG, relief="groove", bd=2)
frame_chat.pack(fill="x", padx=14, pady=4)

tk.Label(frame_chat, text="Написать в чат:", font=FNT, bg=BG).pack(anchor="w", padx=6)

chat_row = tk.Frame(frame_chat, bg=BG)
chat_row.pack(fill="x", padx=6, pady=(2, 6))

chat_var = tk.StringVar()
chat_entry = tk.Entry(chat_row, textvariable=chat_var, font=FNT, bg="white", relief="sunken", bd=2, width=26)
chat_entry.pack(side="left", ipady=3)

def send_chat():
    msg = chat_var.get().strip()
    if msg:
        try:
            bot.chat(msg)
            log(f"чат {msg}")
        except Exception as e:
            log(f"Ошибка чата: {e}")
        chat_var.set("")

chat_entry.bind("<Return>", lambda e: send_chat())
tk.Button(chat_row, text="Отправить", command=send_chat,
          bg=BTN, relief="raised", bd=2, font=FNT, cursor="hand2").pack(side="left", padx=6)

# Кнопки действий
frame_btns = tk.Frame(window, bg=BG)
frame_btns.pack(pady=6)

def mk_btn(text, cmd):
    tk.Button(
        frame_btns, text=text, command=cmd,
        bg=BTN, relief="raised", bd=2,
        font=FNT, width=32, cursor="hand2"
    ).pack(pady=2)


NON_ATTACKABLE = {
    'armor_stand', 'item_frame', 'glow_item_frame', 'painting',
    'boat', 'chest_boat', 'minecart', 'leash_knot',
    'end_crystal', 'experience_orb', 'arrow', 'spectral_arrow',
    'item', 'tnt', 'falling_block', 'firework_rocket', 'fireball',
    'small_fireball', 'lightning_bolt', 'marker', 'text_display',
    'block_display', 'item_display', 'interaction', 'evoker_fangs',
    'shulker_bullet', 'eye_of_ender', 'fishing_bobber', 'llama_spit',
    'wither_skull', 'dragon_fireball', 'area_effect_cloud'
}

def is_attackable(e):
    try:
        if not e or not e.isValid:
            return False
        if e.id == bot.entity.id:
            return False
        if e.type not in ('mob', 'player'):
            return False
        if e.name and e.name.lower() in NON_ATTACKABLE:
            return False
        return True
    except:
        return False

# Авто-защита в фоне бьет ближайшего врага если ближе 4 блоков
def auto_defense():
    while True:
        try:
            if not bot.entity or not bot.entity.isValid:
                time.sleep(1)
                continue
            target = None
            min_dis = 9999.0
            for uid in bot.entities:
                e = bot.entities[uid]
                if is_attackable(e):
                    dis = bot.entity.position.distanceTo(e.position)
                    if dis < min_dis:
                        min_dis = dis
                        target = e
            if target and min_dis < 4.0:
                if not action_lock.acquire(False):
                    time.sleep(0.2)
                    continue
                try:
                    sword = next((i for i in bot.inventory.items() if 'sword' in i.name), None)
                    if sword:
                        bot.equip(sword, 'hand')
                    if is_attackable(target):
                        bot.attack(target)
                finally:
                    action_lock.release()
                time.sleep(1.1)
        except:
            pass
        time.sleep(0.2)

# Ждет пока бот дойдет до точки (таймаут в секундах)
def _wait_arrival(pos, timeout=20):
    for _ in range(timeout * 2):
        try:
            if bot.entity.position.distanceTo(pos) < 2.5:
                return True
        except:
            pass
        time.sleep(0.5)
    return False

# Ищет алмазы и копает их
def diamond_mine():
    log("Сканирую алмазы")
    try:
        ore_names = ['diamond_ore', 'deepslate_diamond_ore']
        ids = [bot.registry.blocksByName[n].id for n in ore_names if n in bot.registry.blocksByName]

        target = bot.findBlock({'matching': ids, 'maxDistance': radius_var.get()})
        if not target:
            log(f"Нет алмазов в радиусе {radius_var.get()} блоков")
            return

        log(f"Нашел {target.name}, иду")
        bot.pathfinder.setGoal(
            pathfinder.goals.GoalGetToBlock(target.position.x, target.position.y, target.position.z)
        )

        _wait_arrival(target.position, timeout=20)
        bot.pathfinder.setGoal(None)
        bot.clearControlStates()
        time.sleep(0.3)

        pick = next((i for i in bot.inventory.items() if 'pickaxe' in i.name), None)
        if not pick:
            log("Нет кирки в инвентаре!")
            return

        live_block = bot.blockAt(target.position)
        if not live_block or live_block.name not in ore_names:
            return

        log("Копаю")
        with action_lock:
            bot.equip(pick, 'hand')
            time.sleep(0.2)
            try:
                bot.dig(live_block)
                time.sleep(3.5)
                log("Готово!")
            except Exception as e:
                s = str(e).lower()
                if 'aborted' in s or 'timeout' in s:
                    log("Блок уже добыт — нормально")
                else:
                    log(f"Ошибка dig: {str(e)[:60]}")
    except Exception as e:
        log(f"Ошибка майнинга: {str(e)[:80]}")

# Ищет ближайшую цель и атакует её со спринтом
def attack_all():
    log("Атака!")
    try:
        with action_lock:
            bot.clearControlStates()
            sword = next((i for i in bot.inventory.items() if 'sword' in i.name), None)
            if sword:
                bot.equip(sword, 'hand')

            target = None
            min_dis = 9999.0
            for uid in bot.entities:
                e = bot.entities[uid]
                if is_attackable(e):
                    dis = bot.entity.position.distanceTo(e.position)
                    if dis < min_dis:
                        min_dis = dis
                        target = e

            if not (target and target.isValid):
                log("Никого нет рядом")
                return

            log(f"Цель: {target.name} ({min_dis:.1f} бл.)")
            bot.setControlState('sprint', True)
            bot.pathfinder.setGoal(pathfinder.goals.GoalFollow(target, 1.5), True)

            for _ in range(30):
                try:
                    if not is_attackable(target):
                        log("Цель уничтожена!")
                        break
                    if bot.entity.position.distanceTo(target.position) < 3.5:
                        bot.attack(target)
                except:
                    break
                time.sleep(0.65)

            bot.clearControlStates()
            bot.pathfinder.setGoal(None)
    except Exception as e:
        log(f"Ошибка атаки: {str(e)[:80]}")

def stop_bot():
    try:
        bot.clearControlStates()
        bot.pathfinder.setGoal(None)
        log("Стоп")
    except Exception as e:
        log(f"Ошибка: {e}")

def clear_log():
    log_box.config(state="normal")
    log_box.delete("1.0", tk.END)
    log_box.config(state="disabled")

mk_btn("Атака на всех",  lambda: _thread.start_new_thread(attack_all, ()))
mk_btn("Копать алмазы",  lambda: _thread.start_new_thread(diamond_mine, ()))
mk_btn("Стоп",           stop_bot)
mk_btn("Очистить лог",   clear_log)

# Бот подключился к серверу
@On(bot, 'spawn')
def handle_spawn():
    log("Бот в игре!")
    set_status("ONLINE", "green")
    _thread.start_new_thread(auto_defense, ())
    if viewer:
        try:
            viewer(bot, {'port': 8080, 'firstPerson': True})
            log("Камера: http://127.0.0.1:8080")
        except Exception as e:
            log(f"Камера не запустилась: {e}")
    else:
        log("prismarine-viewer не найден, установи через npm")

# Ошибка соединения
@On(bot, 'error')
def handle_error(err):
    s = str(err)
    if any(x in s for x in ['ECONNRESET', 'ETIMEDOUT', 'PartialReadError']):
        log("Обрыв сети")
    else:
        log(f"Ошибка: {s[:80]}")

# Бота кикнули
@On(bot, 'kicked')
def handle_kicked(reason):
    set_status("KICKED", "orange")
    log(f"Кик: {reason}")

# Соединение закрыто
@On(bot, 'end')
def handle_end():
    set_status("OFFLINE", "red")
    log("Отключен")

window.mainloop()