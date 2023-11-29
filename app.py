from flask import Flask, request, jsonify
import requests
import json
import openai

from linebot.v3 import (WebhookHandler)
from linebot.v3.messaging import (Configuration)

from decouple import config

app = Flask(__name__)

access_token=config('access_token')
channel_secret=config('channel_secret')
line_bot_api = Configuration(access_token)
handler = WebhookHandler(channel_secret)
LINE_API_URL = 'https://api.line.me/v2/bot/message/reply'

openai_key = config('openai_key')
openai.api_key = openai_key

#food menu
food_menu="Food menu :\n\n1.ผัดกระเพรา ธรรมดา(normal size) 40 บาท พิเศษ(extra size) 50 บาท\n2.ผัดซีอิ๊ว ธรรมดา(normal size) 40 บาท พิเศษ(extra size) 50 บาท\n3.ข้าวไข่เจียว 20 บาท\n4.ต้มยำน้ำข้น ธรรมดา(normal size) 50 บาท พิเศษ(extra size) 60 บาท\n5.ข้าวเปล่า 10 บาท\n6.น้ำซุป 20 บาท\n\n"+"Drink menu:\n\n1.น้ำเปล่าขวดละ 10 บาท\n2.โค้กขวดละ 15 บาท\n3.สไปรท์ขวดละ 15 บาท\n\n"

#format json output
ex_format_json="EX1 order:\"ผัดกระเพรา ธรรมดา\" JSON output: {\"food\":[{\"name\":\"ผัดกระเพรา\",\"size\":\"ธรรมดา\",\"price\":40}],\"drink\":[]} ,EX2 order:ผัดกระเพรา พิเศษ 1 ผัดกระเพรา ธรรมดา 1 น้ำเปล่า 1 JSON output: {\"food\":[{\"name\":\"ผัดกระเพรา\",\"size\":\"ธรรมดา\",\"price\":40},{\"name\":\"ผัดกระเพรา\",\"size\":\"พิเศษ\",\"price\":50}],\"drink\":[{\"name\":\"น้ำเปล่า\",\"price\":10}]} EX3 order:ข้าวเปล่า 1 น้ำเปล่า 2 JSON output: {\"food\":[{\"name\":\"ข้าวเปล่า\",\"size\":\"ธรรมดา\",\"price\":10}],\"drink\":[{\"name\":\"น้ำเปล่า\",\"price\":10},{\"name\":\"น้ำเปล่า\",\"price\":10}]} EX4 order:\"ผัดกระเพรา ธรรมดา 3จาน\" JSON output: {\"food\":[{\"name\":\"ผัดกระเพรา\",\"size\":\"ธรรมดา\",\"price\":40},{\"name\":\"ผัดกระเพรา\",\"size\":\"ธรรมดา\",\"price\":40},{\"name\":\"ผัดกระเพรา\",\"size\":\"ธรรมดา\",\"price\":40}],\"drink\":[]}"

#history conversation
customer_conversation = []

#For use in collecting information about customer requirement and compiling them into JSON
def collect_requirement_bot(user_message, messages, max_tokens=500, temperature=0):

    response = openai.ChatCompletion.create(
        model="gpt-4",  # Use the chat model
        messages=[
            {"role": "system",
            "content": "Your role is the food ordering system.You are a woman.\n"+
            "Your response will be object JSON.This is JSON object details and structure used in response {\"intent\":\"(It is the intent of the present conversation.The intent herein is defined as follows:1.see the menu 2.check shopping cart 3.general talk 4.order food 5.order has been confirmed).\",\"content\":\"(Your content used for responding reply to user messages.)\",\"current_order\":\"(The current shopping cart it's a JSON object.)\"}.More about JSON object:\n"+
            "\t1.The value in the intent key must be (see the menu,check shopping cart,general talk,order food,order has been confirmed) only.These five values are used to indicate the intent of the most recent question from the user."+
            "The value will be (see the menu) when the customer wants to see the menu,"+
            "it will be (check shopping cart) when the customer wants to check the price or all the current food items in the cart,"+
            "it will be (general talk) when the intent is neither (see the menu) nor (check shopping cart) nor (order food) nor (order has been confirmed),"+
            "it will be (order food) when customers want to order food or edit his food order in the current_order key,"+
            "it will be (order has been confirmed) when you do final step in The tasks only"+
            "\t2.The value in the content key is the text that you use in your response to the customer.\n"+
            "\t3.If the value in the intent key is (check shopping cart) or (see the menu) the value in the content key is an empty string.\n"+
            "\t4.Your content can reply in multiple languages.The conditions depend on what language the customer uses to communicate.Words in content key should be answered as naturally as possible, just like a human being.\n"+
            "\t5.The value in the current_order key is a JSON object used to store products in the customer's basket."+
            "\nIn each conversation, The value in the current_order key may don't be changed without intent from the customer."+
            "\t6.The JSON object structure to be stored in current_order must have the following structure {\"food\":[{\"name\":\"(name of food)\",\"size\":\"(size of food)\",\"price\":(price of food)}],\"drink\":[{\"name\":\"(name of drink)\",\"price\":(price of drink)}]}.Example JSON object :"+ex_format_json+"\n"+
            "\nThe food and drink menus available in the restaurant are as follows.\n\n"+food_menu+"\n"+
            "\nThe tasks you need to do when a customer contacts you are as follows:\n"+
            "\t1.Introduce your restaurant and function\n"+
            "\t2.Take food or drink orders from your customers and keep those order data in current_order key\n"+
            "\t3.Ask to confirm the customer's all food and drink orders they have in their cart to make sure everything is correct,You should tell your customer what food order he has in his cart but you are no need from telling the total product price.This step is very important, do not forget it at all.\n"+
            "\t4.This step is the final step of the tasks.Say thank you to customers who came to use the service."
            "\nPlease be careful follow:\n"+
            "\t1.In the tasks  point 2 check whether you have received all the necessary information, required information includes:"+
            "1.1 Food or beverage menu,1.2 Size of food such as ธรรมดา or normal size or พิเศษ.\n"+
            "\t2.In the tasks  point 2 some dishes only come in one size. You cannot choose a different size than the menu.\n"+
            "\t3.If the customer hasn't ordered a drink yet, ask if they want any drinks.\n"+
            "\t4.If a customer wants to order Pepsi that isn't on the restaurant's menu, refuse and recommend a similar drink instead, such as Coke.\n"+
            "\t5.Customers cannot order food that is not on the restaurant's menu.\n"+
            "\t6.You should decline conversations that are likely not highly relevant to your work.\n"+
            "\t7.When receiving food or drink order from the customer,You should ask if the customer needs anything more.\n"+
            "\t8.In the tasks point 3 This step is (general talk) not (check shopping cart)\n"+
            "\t9.Check for make sure the menu you receive is food or drink before you add it to current_order key.You can tell if it's food or drink from the restaurant's food and drink menus."
            }] 
        + messages 
        + [{"role": "user", "content": user_message}],
        max_tokens=max_tokens,
        temperature=temperature
    )

    return response.choices[0].message['content'].strip()

def reply_message(reply_token, message_text):

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
    }

    data = {
        'replyToken': reply_token,
        'messages': [
            {
                'type': 'text',
                'text': message_text,
            },
        ],
    }
    response = requests.post(LINE_API_URL, headers=headers, data=json.dumps(data))
    

def push_message(user_id,push_message):

    recipient_id = user_id

    message = {
        "type": "text",
        "text": push_message
    }

    payload = {
        "to": recipient_id,
        "messages": [message]
    }

    url = "https://api.line.me/v2/bot/message/push"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    # Send the POST request
    response = requests.post(url, json=payload, headers=headers)

#แปลงjsonเป็นภาษาคน
def JSON_to_text(json_object):
    item_counts = {}

    for items in json_object.values():
        for item in items:
            name = item['name']
            size = item.get('size', '')  # Use '' if 'size' is not present
            key = f"{name} {size}"

            if key in item_counts:
                item_counts[key] += 1
            else:
                item_counts[key] = 1

    output_text = ""
    for key, count in item_counts.items():
        output_text += f"{key} {count}\n"

    return(output_text)

#processing price reduce of promotion soup
def promotion_soup(json_object):
    soup=0
    food=0

    for i in json_object['current_order']['food']:
        
        if i['name']!=('ข้าวเปล่า' or 'น้ำซุป'):
            food+=1
        if i['name']=='น้ำซุป':
            soup+=1

    if soup<=food:
        return soup*15
    else:
        return food*15
    
#calculate all price and order
def calculate_price(json_object):
    price=0
    reduce_price=0
    order_and_price=""

    for i in json_object['current_order']['food']:
        order_and_price=order_and_price+i['name']+' '+i['size']+' '+str(i['price'])+'฿\n'
        price+=i['price']

    for i in json_object['current_order']['drink']:
        order_and_price=order_and_price+i['name']+' '+str(i['price'])+'฿\n'
        price+=i['price']

    #----------promotion space--------------------

    reduce_price+=promotion_soup(json_object)

    #----------promotion space--------------------

    order_and_price+='ส่วนลด '+str(reduce_price)+'฿\n\nราคารวม '+str(price-reduce_price)+'฿\n\nคุณต้องการสั่งอาหารหรือเครื่องดื่มอะไรเพิ่มไหมค่ะ'

    return order_and_price
    
@app.route('/webhook', methods=['POST','GET'])
def webhook():

    global customer_conversation
    data = request.get_json()

    for event in data['events']:
        if event['type'] == 'message' and event['message']['type'] == 'text':
            user_id = event['source']['userId']
            reply_token = event['replyToken']
            text_message=event['message']['text']

            # print("ีuser id :"+user_id)


            customer_conversation.append({"role": "user", "content": text_message})
            bot_response = collect_requirement_bot(text_message,customer_conversation)
            json_bot_response = json.loads(bot_response)

            

            if json_bot_response['intent']=='check shopping cart':
                all_price=calculate_price(json_bot_response)
                reply_message( reply_token, all_price)

                #add history conversation
                customer_conversation.append({"role": "assistant", "content": bot_response.replace('content":""','content":"'+all_price+'"')})

                return 'OK', 200
            
            elif json_bot_response['intent']=='see the menu':
                reply_message( reply_token, food_menu)

                #add history conversation
                customer_conversation.append({"role": "assistant", "content": bot_response.replace('content":""','content":"'+food_menu+'"')})

                return 'OK', 200
            
            elif json_bot_response['intent']=='order has been confirmed':
                sand_to_calculate_chef=calculate_price(json_bot_response).replace('\n\nคุณต้องการสั่งอาหารหรือเครื่องดื่มอะไรเพิ่มไหมค่ะ','')
                push_message("Ud3c8e8443688d45af0d42bfebe7e7866",sand_to_calculate_chef)
                reply_message( reply_token, bot_response)
                customer_conversation=[]

                return 'OK', 200

            # if is_valid_json(bot_response):
            #     json_order_data = json.loads(bot_response)
            #     print(json_order_data)
            #     text_order=JSON_to_text(json_order_data)
            #     print(text_order)
                
            #      # Send a reply message
            #     reply_message( reply_token,"สั่งอาหารสำเร็จแล้วคะ  ")

            #     #message to driver
            #     push_message("Ud3c8e8443688d45af0d42bfebe7e7866","รายการอาหาร\n\n"+text_order)
                        
            #     customer_conversation=[]
            #     return 'OK', 200

            # Send a reply message
            reply_message( reply_token, bot_response)

            #add history conversation
            customer_conversation.append({"role": "assistant", "content": bot_response})

    return 'OK', 200

if __name__ == "__main__":
    app.run(debug=True)