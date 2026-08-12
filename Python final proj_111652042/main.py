#應數15_111652042_顏友君
import random
import asyncio
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from API import token

# --- 全域設定 ---
PLAYER_SYMBOL = '⭕'
BOT_SYMBOL = '❌'
EMPTY = ' '

# 儲存遊戲狀態
games = {}

# 勝利組合
WIN_COMBINATIONS = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # 橫向
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # 縱向
    (0, 4, 8), (2, 4, 6)  # 斜向
]

#檢查是否勝利
def check_win(board, symbol):

    for a, b, c in WIN_COMBINATIONS:
        if board[a] == symbol and board[b] == symbol and board[c] == symbol:
            return True
    return False

#轉換棋盤為按鈕
def get_board_markup(board, blocked_pos=None):
    keyboard = []
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            idx = i + j
            cell_value = board[idx]

            if cell_value == EMPTY:
                if idx == blocked_pos:
                    text = "⛔"
                else:
                    text = str(idx + 1)
            else:
                text = cell_value

            row.append(InlineKeyboardButton(text, callback_data=str(idx)))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("Restart", callback_data='restart')])
    return InlineKeyboardMarkup(keyboard)


# --- 機器人邏輯 ---

#尋找是否有立刻獲勝(或阻擋)的一步
def get_winning_move(board, symbol, available_moves):
    for a, b, c in WIN_COMBINATIONS:
        line = [board[a], board[b], board[c]]
        if line.count(symbol) == 2 and line.count(EMPTY) == 1:
            empty_idx = [idx for idx in (a, b, c) if board[idx] == EMPTY][0]
            if empty_idx in available_moves:
                return empty_idx
    return None

#整合 Easy 和 Hard 的下棋邏輯
def bot_logic(game_state, mode):
    board = game_state['board']
    bot_blocked = game_state.get('bot_last_removed_pos')

    available_moves = [
        i for i in range(9)
        if board[i] == EMPTY and i != bot_blocked
    ]

    if not available_moves:
        return None

    if mode == 'easy':
        return random.choice(available_moves)

    elif mode == 'hard':
        # 1. 進攻
        win_move = get_winning_move(board, BOT_SYMBOL, available_moves)
        if win_move is not None: return win_move
        # 2. 防守
        block_move = get_winning_move(board, PLAYER_SYMBOL, available_moves)
        if block_move is not None: return block_move
        # 3. 中心
        if 4 in available_moves: return 4
        # 4. 角落
        corners = [0, 2, 6, 8]
        available_corners = [m for m in corners if m in available_moves]
        if available_corners: return random.choice(available_corners)
        # 5. 隨機
        return random.choice(available_moves)

#如果滿3子，執行移除，回傳被移除的索引
def process_bot_removal(game_state):
    board = game_state['board']
    x_pos = game_state['x_pos']

    if len(x_pos) == 3:
        remove_idx = random.choice(x_pos)
        board[remove_idx] = EMPTY
        x_pos.remove(remove_idx)
        game_state['bot_last_removed_pos'] = remove_idx
        return remove_idx

    game_state['bot_last_removed_pos'] = None
    return None

def process_player_removal(game_state):
    board = game_state['board']
    o_pos = game_state['o_pos']

    if len(o_pos) == 3:
        remove_idx = random.choice(o_pos)
        board[remove_idx] = EMPTY
        o_pos.remove(remove_idx)
        game_state['blocked'] = remove_idx
        return remove_idx

    game_state['blocked'] = None
    return None


# --- Telegram Handlers ---
#發送或編輯開始選單
async def start(update, context):
    text = (
        f'Tic-Tac-Toe!\n\n'
        f'You: {PLAYER_SYMBOL}\nBot: {BOT_SYMBOL}\n\n'
        '規則:\n'
        '1. 滿 3 個符號時，舊符號隨機消失。\n'
        '2. 剛消失的位置(⛔)該回合禁填。\n\n'
        '選擇模式:'
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('Easy Mode', callback_data='easy')],
        [InlineKeyboardButton('Hard Mode', callback_data='hard')]
    ])

    # 判斷是來自指令 (/start) 還是按鈕 (Restart)
    if update.message:
        # 來自 /start 指令，發送新訊息
        await update.message.reply_text(text, reply_markup=markup)
    elif update.callback_query:
        # 來自按鈕回調，編輯原有訊息
        await update.callback_query.edit_message_text(text, reply_markup=markup)


async def func(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    data = query.data

    # === 處理 Restart ===
    if data == 'restart':
        await query.answer("Restarting...")
        # 直接呼叫修正後的 start，它會自動處理 edit_message_text
        await start(update, context)
        return

    # === 遊戲初始化 ===
    if data in ['easy', 'hard']:
        games[chat_id] = {
            'board': [EMPTY] * 9,
            'x_pos': [],
            'o_pos': [],
            'mode': data,
            'blocked': None,
            'game_over': False,
            'bot_last_removed_pos': None
        }
        game = games[chat_id]

        if data == 'easy':
            await query.answer()
            await query.edit_message_text(
                text=f"Easy Mode! You ({PLAYER_SYMBOL}) start first.",
                reply_markup=get_board_markup(game['board'])
            )
            return

        else:  # Hard Mode (Bot First)
            await query.answer()
            first_move = bot_logic(game, 'hard')
            game['board'][first_move] = BOT_SYMBOL
            game['x_pos'].append(first_move)

            await query.edit_message_text(
                text=f"Hard Mode! Bot ({BOT_SYMBOL}) goes first.\nBot chose spot {first_move + 1}.",
                reply_markup=get_board_markup(game['board'])
            )
            return

    # === 玩家回合 ===
    if chat_id not in games or games[chat_id].get('game_over', True):
        await query.answer("Session expired.", show_alert=True)
        return

    game = games[chat_id]

    try:
        move = int(data)
    except ValueError:
        await query.answer()
        return

    board = game['board']
    blocked_pos = game['blocked']

    # 驗證
    if move == blocked_pos:
        await query.answer("⛔ 不能下在剛消失的位置！", show_alert=True)
        return
    if board[move] != EMPTY:
        await query.answer("這裡已經有棋子了！", show_alert=True)
        return

    await query.answer()

    # 玩家下棋
    board[move] = PLAYER_SYMBOL
    game['o_pos'].append(move)
    game['blocked'] = None

    # 檢查玩家勝
    if check_win(board, PLAYER_SYMBOL):
        game['game_over'] = True
        await query.edit_message_text(
            text=f"🎉 You Won! ({PLAYER_SYMBOL} wins)\nBot was in {game['mode']} mode.",
            reply_markup=get_board_markup(board)
        )
        return

    # === 電腦回合 ===

    # 移除階段
    bot_removed_idx = process_bot_removal(game)
    if bot_removed_idx is not None:
        await query.edit_message_text(
            text=f"Bot ({BOT_SYMBOL}) removed a piece...",
            reply_markup=get_board_markup(board, blocked_pos=bot_removed_idx)
        )
        await asyncio.sleep(0.5)

    # 思考階段
    await query.edit_message_text(
        text=f"Bot ({BOT_SYMBOL}) is thinking...",
        reply_markup=get_board_markup(board, blocked_pos=bot_removed_idx)
    )
    think_time = random.uniform(0.3, 1.0)
    await asyncio.sleep(think_time)

    # 下棋階段
    bot_move = bot_logic(game, game['mode'])
    if bot_move is not None:
        board[bot_move] = BOT_SYMBOL
        game['x_pos'].append(bot_move)

    # 檢查電腦勝
    if check_win(board, BOT_SYMBOL):
        game['game_over'] = True
        await query.edit_message_text(
            text=f"💀 You Lost! Bot ({BOT_SYMBOL}) Won.",
            reply_markup=get_board_markup(board)
        )
        return

    # === 下一輪玩家 ===
    msg_text = f"Your Turn ({PLAYER_SYMBOL})"

    player_removed_idx = process_player_removal(game)
    if player_removed_idx is not None:
        msg_text += "\n⚠️ 隨機移除了一格！該處暫時禁填 (⛔)。"

    await query.edit_message_text(
        text=msg_text,
        reply_markup=get_board_markup(board, blocked_pos=player_removed_idx)
    )


def main():
    """Start the bot."""
    application = Application.builder().token(token).job_queue(None).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(func))
    print("Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()