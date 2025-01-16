import os
from crewai import Agent, Task, Crew, LLM
from pydantic import BaseModel

# Set environment variables
os.environ["Groq_llama_Model"] = "groq/llama-3.3-70b-versatile"
os.environ["Groqapikey"] = "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"  # Replace with your API key


class Blog(BaseModel):
    product: list
    quantity: list
    shipment_date: list

def generate(user_input):
    try:
        # Retrieve the 'prompt' from the POST request body

        
        # Define the agent
        info_agent = Agent(
            role="Information Extractor Agent",
            goal="Your goal is to extract information from the given text whether it has the product details like product name, product quantity and extract shipment date also.",
            backstory="""
                You love to know information. People love and hate you for it. You win most of the
                extraction at your local pub.
            """,
            llm=LLM(
                model=os.getenv("Groq_llama_Model"),
                api_key=os.getenv("Groqapikey"),
                temperature=0.7
            )
        )

        # Define the task
        task1 = Task(
            description=user_input,
            expected_output='''Give me product details with name and quantity and shipment date and check. 
        class Blog(BaseModel):
    product: list
    quantity: list
    shipment_date: list''',
            agent=info_agent,
            output_json=Blog,
            
            
               
        )

        
        # Execute the task
        crew = Crew(
            agents=[info_agent],
            tasks=[task1],
            verbose=False,
            
        )

        

        result = crew.kickoff()
         # Convert the result to a dictionary
        result_dict = result.dict() if hasattr(result, 'dict') else result
        
        
        # Return the result as JSON
        return result_dict.get('json_dict')

    except Exception as e:
        return str(e)

