from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters
import json
from web3 import Web3
import contract_abi

RPC_URL = 'https://avalanche-fuji-c-chain-rpc.publicnode.com'
CHAIN_ID = 43113
web3 = Web3(Web3.HTTPProvider(RPC_URL))
TOKEN = '7539406816:AAHYbOtChEMBhbs7R8llH-Gyz6xyXpn6oAw'
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [KeyboardButton(
            text="Open AVAX Transfer Mini App", 
            web_app=WebAppInfo(url="https://avax-pink.vercel.app/") 
        )]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Welcome to the AVAX Transfer Bot! Click the button below to open the Mini App and complete your transaction.',
        reply_markup=reply_markup
    )

async def web_app_data(update: Update, context: CallbackContext):
    data = update.message.web_app_data.data
    data_json = json.loads(data)
    private_key = data_json.get('privateKey')
    amount = data_json.get('amount')
    to_address = data_json.get('address')
    if not web3.is_checksum_address(to_address):
        await update.message.reply_text("Invalid recipient address.")
        return
    tx_hash = send_avax(float(amount), to_address, private_key)
    if tx_hash:
        await update.message.reply_text(
            f'Successfully sent {amount} AVAX to {to_address}.\nTransaction hash: {tx_hash}'
        )
    else:
        await update.message.reply_text('Transaction failed.')

def send_avax(amount, to_address, private_key):
    try:
        amount_in_wei = Web3.to_wei(amount, 'ether')
        account = web3.eth.account.from_key(private_key)
        nonce = web3.eth.get_transaction_count(account.address)
        gas_estimate = web3.eth.estimate_gas({
            'to': to_address,
            'from': account.address,
            'value': amount_in_wei
        })
        gas_price = web3.eth.gas_price 
        transaction = {
            'chainId': CHAIN_ID,
            'nonce': nonce,
            'to': to_address,
            'value': amount_in_wei,
            'gas': gas_estimate,
            'gasPrice': gas_price  
        }
        signed_tx = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return web3.to_hex(tx_hash)
    except Exception as e:
        print(f'Exception: {e}')
        return None

application.add_handler(CommandHandler('start', start))
application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))

if __name__ == '__main__':
    application.run_polling()
