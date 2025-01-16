from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate, PromptTemplate
from datetime import datetime
from flask_cors import CORS
import os
from flask import Flask, request, jsonify
import re
from uuid import uuid4
from threading import Lock
import requests
from dataextractor import generate
from database.vectorsearch import search_products


current_date = datetime.now()
product_list=[]

# Define procurement system rules
procurement_rules = """Follow these rules strictly:
1. Agent:
   - "Can you specify the Product name, Quantity, and Delivery date?"
2. Validate date:
    - "Can you specify the Delivery date?"
3. Ask Product Confirmation:
    - "Are you sure this is the product you are looking for? Please confirm."   
4. Ask Confirmation:
    - Before submitting the PR request, ask for confirmation from the user.
5. Final Bot message:
    -{{proceed:true, product: [product_list], quantity: [quantity_list], shipment_date: [shipment_date_list]}}
6. Rules:
    - "Regarding conversation history donot give give any information to the user"
    - "Respond conversationally but keep responses concise"
    - "Keep the conversation short and simple"
    - "Do not include any other information"
    - "Do not include explanations or conversations"
    - "Do not give date multiple times as response"

Current conversation: {history}
Human input: {input}."""
# procurement_rules = """Follow these rules strictly:
# 1. Agent:
#    - "Can you specify the Product name, Quantity, and Delivery date?"
# 2. Validate date:
#     - "Date should be in the future from the current date."
# 3. Ask Product Confirmation:
#     - "This is the product you are looking for. Please confirm. or select from the list of products"   
# 4. Ask Confirmation:
#     - Before submitting the PR request, ask for confirmation from the user.
# 5. Final Bot message:
#     -{{proceed:true, product: [product_list], quantity: [quantity_list], shipment_date: [shipment_date_list]}}
# 6. Rules:
#     - "Regarding conversation history donot give give any information to the user"

# Current conversation: {history}
# Human input: {input}."""

# Initialize LLM
llm = ChatGroq(
    groq_api_key="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",
    model_name="llama-3.3-70b-versatile"
)

# Dictionary to store user-specific conversations
user_conversations = {}
conversation_lock = Lock()

# List to store search response id
search_response_id=[]


def get_or_create_conversation(user_id):
    with conversation_lock:
        if user_id not in user_conversations:
            # Create new memory and conversation for user
            memory = ConversationBufferMemory()
            prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(procurement_rules+" Todays date is "+str(current_date) ),
                HumanMessagePromptTemplate.from_template("{input}")
            ])
            user_conversations[user_id] = ConversationChain(
                llm=llm,
                memory=memory,
                prompt=prompt,
                verbose=True
            )
        return user_conversations[user_id]

def check_and_clear_memory(response, user_id):
    # print(user_conversations[user_id].memory)
    
    if "true" in response.lower():
        with conversation_lock:
            if user_id in user_conversations:
                user_conversations[user_id].memory.clear()
        return True
    return False

def check_product_exist(user_input):
    system = '''You are a Product Name Extractor.
    Instructions:
    1. Extract ONLY the product name from the given text
    2. Return the product name in plain text format
    3. If multiple products, separate with commas
    4. If no product found, return "NO_PRODUCT"
    5. Do not include any other information
    6. Do not include explanations or conversations
    
    Example Input: "I want to order 5 laptops for delivery"
    Example Output: laptop
    '''
    
    human = "{text}"
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])
    chain = prompt | llm
    result = chain.invoke({"text": user_input})
    return result.content.strip()
  

app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message')
        user_id = data.get('user_id')
        line_items=[]
        search_response=""
        

        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        extracted_product=check_product_exist(user_message)
        print(extracted_product)
        if extracted_product!="NO_PRODUCT":   
            res=search_products(extracted_product)
            print(res.get("materialid"))
            print(res.get("materialDescription"))
            search_response=f"Product found in the database {res.get('materialDescription')}"
            search_response_id.append(res.get("materialid"))
        # Get user-specific conversation
        conversation = get_or_create_conversation(user_id)
        
        # Get response using conversation chain    
        response = conversation.predict(input=user_message+search_response)

        
        print(search_response_id)
        # Check for PR confirmation and clear memory if needed
        memory_cleared = check_and_clear_memory(response, user_id)
        if memory_cleared:
            product_extract = generate(response)
            print(product_extract.get('product'))
            print(product_extract.get('quantity'))
            print(product_extract.get('shipment_date'))
            product=product_extract.get('product')
            quantity=product_extract.get('quantity')
            date=product_extract.get('shipment_date')
            
            for index in range(0,len(product_extract.get('product'))):
                line_item_structure['briefDescription']=product[index]
                line_item_structure['purchaseQty']=quantity[index]
                line_item_structure['schedules'][0]['scheduleDate']=date[0]
                line_items.append(line_item_structure)
            print(line_items)
        return jsonify({
            "citations": [
                {
                    "link": "",
                    "match_percentage": 100,
                    "page_number": "",
                    "title": "Model's knowledge"
                }
            ],
            "generated_response":   f"<h3>Greeting</h3>\n<br>\n<div>{response}</div>" ,
            "status": "true",
            # "res": res.to_json(),

            "user_id": user_id,
            "memory_cleared": memory_cleared,
            "statusCode": 200,
            
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

line_item_structure={
      "purchaseDocumentItem": 10,
      "productType": 0,
      "itemDeleteFlag": "",
      "itemChangeDate": "0000-00-00",
      "briefDescription": "Water Bottle 1 Ltr",
      "material": "000000000001000002",
      "businessLocation": "3002",
      "storagePlace": "",
      "internalReference": "",
      "targetQty": 0,
      "purchaseQty": 100,
      "orderUnit": "EA",
      "orderPriceUnit": "EA",
      "puToOuRatio": 1,
      "ouToPuRatio": "",
      "netPrice": 10000000,
      "priceUnit": 1,
      "netValue": 0,
      "grossValue": 0,
      "bidDeadlineDate": "0000-00-00",
      "taxId": "",
      "stockType": "",
      "expediter1": 0,
      "startDate": "0000-00-00",
      "endDate": "0000-00-00",
      "expediter2": 0,
      "expediter3": 0,
      "excessTolerance": 0,
      "noLimitFlag": "",
      "shortageTolerance": 0,
      "rejectionFlag": "",
      "itemFullfilledFlag": "",
      "finalInvoiceFlag": "",
      "itemClass": "",
      "accountClass": "",
      "partialInvoiceIndicator": "",
      "grIvFlag": "",
      "acknowledgmentRequirement": "",
      "baseUnitOfMeasure": "",
      "purchaseItemValue": 0,
      "grossWeight": 0,
      "packageNumber": 0,
      "rfxItem": 0,
      "requestItemNumber": 0,
      "orderAcknowledgement": "",
      "specialStockIndicator": "",
      "qadFlag": "",
      "orderNumber": "",
      "salesOrderNumber": "",
      "salesOrderItem": "",
      "accountingLedger": "",
      "sourceOfFund": "",
      "fundsCenter": "",
      "department": "",
      "budgetingLedger": "",
      "operationsArea": "",
      "classification": "",
      "statusItem": "new",
      "amendmentStatusItem": "na",
      "itemAcknowledgementFlag": "",
      "itemAcknowledgementRemarks": "",
      "requestNumber": "",
      "itemText": "",
      "itemTextId": "",
      "taxValue": "",
      "taxcode": "",
      "taxPercent": "",
      "tolerancePercentage": 0,
      "unlimitedTolerance": "",
      "underDeliveryTolerance": 0,
      "incoTerms1": "",
      "incoTerms2L": "",
      "incoTerms3L": "",
      "accountAssignmentCategory": "",
      "itemCategory": "-Standard",
      "valuationType": "",
      "valuationCategory": "",
      "serialNoProfile": "",
      "originAccept": "",
      "storageLocation": "",
      "schedules": [
        {
          "scheduleNr": 1,
          "scheduleDate": "2024-05-20",
          "dateCategory": "1",
          "scheduleQuantity": 100,
          "grnQuantity": 0,
          "openQuantity": 100,
          "issuedQuantity": 0,
          "deliveryTime": "00:00:00",
          "reservationNumber": 0,
          "batchNumber": ""
        }
      ]
    }



if __name__ == '__main__':
    app.run(debug=True)