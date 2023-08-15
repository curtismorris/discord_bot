# This example requires the 'message_content' intent.
from dadjokes import Dadjoke
import discord
import requests
import os
import openai
import json
from urllib.request import urlopen
from PIL import Image
import time
import random
import boto3
import uuid

#Import API credentials from file
import user_creds


def chat_gpt_prompt(my_prompt, api_error_count=0, prompt_type='story', persona='default'):
  
    #Persona options
    persona = 'You are a rude but helpful assistant who uses colorful language when replying to questions.'
    #persona = 'You are Albert Einstein before his death in 1955'
    #persona = 'You are a raging lunatic who treats everyone very poorly. You reply to questions you are asked but do so in a way where the person will never want to talk to you again.'
    #persona = 'You are an angry and aggressive assistant who only keeps this job for the money. Because you do not want to lose your job you will answer every single question you are asked even if you do not know the correct answer or you do not agree with the answer because thats not your place.'
    #persona = 'You are a person that spends a lot of time on the internet and has an opinion on everything. You want to provide helpful advice that is no longer than 3 full sentences in length you also like to work in old fashoned expressions that people find charming when you reply.'
    #persona = 'You are a convict serving life behind bars for money laundering but you have internet access and spend all day answering questions on reddit in a helpful way'
    #persona = 'You are a polite assistant who will perform the requested task to the best of your abilities.'
       


    try:
        openai.api_key = user_creds.open_ai_key
        chat_answer = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
        {"role": "system", "content": persona},
        {"role": "user", "content": "tell me a story about " + my_prompt}
            ]
        )

        
        #save the result to s3 along with the prompt
        s3 = boto3.resource('s3', region_name = 'us-east-1', aws_access_key_id=user_creds.aws_access_key_id, aws_secret_access_key=user_creds.aws_secret_access_key)
        bucket_name = 'mercimages'
        key = str(uuid.uuid4())


        #Store prompt in s3 as a text file
        txt_body = my_prompt
        txt_file_name = str(key) + ".txt"
        object = s3.Object(
            bucket_name='mercimages', 
            key=txt_file_name
        )
        object.put(Body=txt_body)

        return(chat_answer)

        ## End of S3 upload ##
    
    
    except openai.error.APIError as e:
    #Handle API error here, e.g. retry or log
        api_error_count = api_error_count + 1
        print(f"OpenAI API returned an API Error: {e}")

        img_results=['Some shit is broken.. Try again later or even right now, I dont care.']
        return(img_results)

    
    except openai.error.APIConnectionError as e:
        #Handle connection error here
        print(f"Failed to connect to OpenAI API: {e}")
        img_results=['Some shit is broken.. Try again later or even right now, I dont care.']
        return(img_results)
  
    except openai.error.RateLimitError as e:
        #Handle rate limit error (we recommend using exponential backoff)
        print(f"OpenAI API request exceeded rate limit: {e}")
        img_results=['Some shit is broken.. Try again later or even right now, I dont care.']
        return(img_results)
  
    except openai.error.InvalidRequestError as e:
        #Handle invalid request (probably the content filter being triggered)
        print(f"OpenAI API InvalidRequestError: {e}")
        img_results=['Some shit is broken.. You may have tried to generate an story or asked a question that OpenAI sees as offensive Try using different words or dont, I dont care (but they seem too).']
        return(img_results)



def scryfall_search(search_term):

    url = "https://api.scryfall.com/cards/named?fuzzy=" + search_term
    headers = {"Content-Type": "application/json; charset=utf-8"}
    response = requests.get(url, headers=headers)
    search_results = json.loads(response.text)
    #print("Scryfall Search Results" + response.text)
    print(url)
    combined_results = []

    try:
        card_name = search_results['name']
        combined_results.append(card_name)
    except:
        combined_results = ["No cards found, please try a different search term."]
        return combined_results
    

    try:
        card_price = search_results['prices']['usd']
        if str(card_price) == 'None':
           #print("NONE DETECTED!")
           card_price = "Unavailable"
           combined_results.append("Normal Card price: " + str(card_price))
        else:
           combined_results.append("Normal Card price: $" + str(card_price))
    except:
        card_price = "Unavailable"
        combined_results.append(card_price)



    try:
        foil_card_price = search_results['prices']['usd_foil']
        if str(foil_card_price) == 'None':
           #print("NONE DETECTED!")
           foil_card_price = "Unavailable"
           combined_results.append("Foil price: " + str(foil_card_price))
        else:
           combined_results.append("Foil price: $" + str(foil_card_price))
    except:
        foil_card_price = "Unavailable"
        combined_results.append(foil_card_price)

    try:
        etched_card_price = search_results['prices']['usd_etched']
        if str(etched_card_price) == 'None':
           #print("NONE DETECTED!")
           etched_card_price = "Unavailable"
           combined_results.append("Etched price: " + str(etched_card_price))
        else:
           combined_results.append("Etched price: $" + str(etched_card_price))
    except:
        etched_card_price = "Unavailable"
        combined_results.append(etched_card_price)
    
    try:
        card_image = search_results['image_uris']['normal']
        combined_results.append(card_image)
    except:
        card_image = "Image unavailable 🤬"
        combined_results.append(card_image)
    
    
    return combined_results

def generate_image(my_prompt, api_error_count, n_count, gen_size="256x256"):

  try:

    #n = number of images to generate
    #openai.api_key = os.getenv("")
    openai.api_key = user_creds.open_ai_key
    my_image = openai.Image.create(
      prompt = my_prompt,
      n=n_count,
      size=gen_size
    )


    #print(my_image)
    #print("URL for " + my_prompt + " :")
    #print(my_image)

    img_results = []

    for result in my_image['data']:
        #save the image to s3 along with the prompt
        s3 = boto3.resource('s3', region_name = 'us-east-1', aws_access_key_id=user_creds.aws_access_key_id, aws_secret_access_key=user_creds.aws_secret_access_key)
        r = requests.get(result['url'], stream=True)
        bucket_name = 'mercimages'
        key = str(uuid.uuid4())
        img_file_name = str(key) + ".png"
        #Store image in s3
        bucket = s3.Bucket(bucket_name)
        bucket.upload_fileobj(r.raw, img_file_name) #img_file_name is the name we will save the file to on s3
        #Store prompt in s3 as a text file
        txt_body = my_prompt
        txt_file_name = str(key) + ".txt"
        object = s3.Object(
            bucket_name='mercimages', 
            key=txt_file_name
        )
        object.put(Body=txt_body)
        #Generate the public URL of the new object so it can be displayed in discord
        public_s3_image_url = 'https://mercimages.s3.amazonaws.com/' + str(img_file_name)
        #bucket.upload_fileobj(r.raw, key)
        ## End of S3 upload ##



        #Combine all results into list
        #img_results.append(result['url'])
        img_results.append(public_s3_image_url)
        #img = Image.open(urlopen(result['url']))
        #img.show()
    
    return(img_results)

  except openai.error.APIError as e:
    #Handle API error here, e.g. retry or log
    api_error_count = api_error_count + 1
    print(f"OpenAI API returned an API Error: {e}")

    img_results=['Some shit is broken.. Try again later or even right now, I dont care.']
    return(img_results)

    
  except openai.error.APIConnectionError as e:
    #Handle connection error here
    print(f"Failed to connect to OpenAI API: {e}")
    img_results=['Some shit is broken.. Try again later or even right now, I dont care.']
    return(img_results)
  
  except openai.error.RateLimitError as e:
    #Handle rate limit error (we recommend using exponential backoff)
    print(f"OpenAI API request exceeded rate limit: {e}")
    img_results=['Some shit is broken.. Try again later or even right now, I dont care.']
    return(img_results)
  
  except openai.error.InvalidRequestError as e:
    #Handle invalid request (probably the content filter being triggered)
    print(f"OpenAI API InvalidRequestError: {e}")
    img_results=['Some shit is broken.. You may have tried to generate an image that OpenAI sees as offensive Try using different words or dont, I dont care (but they seem too).']
    return(img_results)

intents = discord.Intents.default()
from discord.ext import commands
intents.message_content = True

client = discord.Client(intents=intents)

#bot = commands.Bot(command_prefix='!')

#@bot.command(pass_context=True)
#async def DM(ctx, user: discord.User, *, message=None):
#    message = message or "This Message is sent via DM"
#    await bot.send_message(user, message)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):

    #Do nothing if the message came from this bot to prevent loops
    if message.author == client.user:
        return
    
    #await message.channel.send(message.channel)

    #only monitor the specified channel (Need to add direct message capabilities too)
    #Determine if message is a direct message from a user
    try:
        search_result = str(message.channel).find('Direct Message')
    except:
       search_result = -1


    if str(message.channel) != 'merc-bot':
        #Message was NOT set to the correct channel for bot to reply so let's see if it
        print(message.channel)
        if search_result != 0:
            print("Message not a DM or in the correct channel.")
            return

    if message.content.startswith('$chatwithme'):
        print(str(message))
        #print(str(message.author.name))
        await message.channel.send('Hello ' + str(message.author.name) + "!")
    #Dad Joke dadjoke = Dadjoke()
    elif message.content == ("Dad Joke") or message.content == ("🤣"):
        dadjoke = Dadjoke()
        await message.channel.send(dadjoke.joke)
    elif message.content.startswith("$image"):
       prompt = message.content.replace('$image ', '')
       if prompt != '':
          await message.channel.send("Generating image based on prompt: " + prompt)
          img_url = generate_image(prompt, 0, 3)
          print(img_url)
          #Send results to user
          for image_link in img_url:
             await message.channel.send(image_link)
       else:
          await message.channel.send("Error, no prompt given...")
    elif message.content.startswith("$mtgsearch"):
        user_search_term = message.content.replace('$mtgsearch', '')
        if user_search_term != '':
           await message.channel.send("Searching Scryfall for: " + user_search_term)
           mtg_search_results = scryfall_search(user_search_term)
           print(mtg_search_results)

           #If list is only 1 in length it's an error 
           if len(mtg_search_results) > 1:
            #Send results to channel
            await message.channel.send(mtg_search_results[4])
            await message.channel.send(mtg_search_results[1] + "\n" + mtg_search_results[2] + "\n" + mtg_search_results[3])
            #await message.channel.send(mtg_search_results[4])
           
           else:
               await message.channel.send(mtg_search_results[0])
           
        else:
            await message.channel.send("Error, no search term provided...")
    elif message.content.startswith("$roll"):
       try:
          dice_sides = 20
          roll = random.randrange(dice_sides)
          dice_image_description = "the number " + str(roll)
          print("Generated description of dice: " + dice_image_description)
          dice_image_url = generate_image(dice_image_description,0,1)
          await message.channel.send(str(message.author.name) + " rolled a " + str(roll))
          for dice_image_link in dice_image_url:
             await message.channel.send(dice_image_link)
       except:
          pass
    elif message.content.startswith("$hqimage"):
       prompt = message.content.replace('$hqimage ', '')
       if prompt != '':
          await message.channel.send("Generating high quality image based on prompt: " + prompt)
          img_url = generate_image(prompt, 0, 3,"1024x1024")
          print(img_url)
          #Send results to user
          for image_link in img_url:
             await message.channel.send(image_link)
       else:
          await message.channel.send("Error, no prompt given...")


    elif message.content.startswith("$randommtg"):
        user_search_term = message.content.replace('$randommtg ', '')
        

        await message.channel.send("Drawing a random Magic card")

        url = "https://api.scryfall.com/cards/random"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        response = requests.get(url, headers=headers)
        draw_results = json.loads(response.text)
        #print("Scryfall Search Results" + response.text)
        #print(draw_results)


        #If list is only 1 in length it's an error 
        if len(draw_results) > 1:
            #Send results to channel
            await message.channel.send(str(message.author.name) + " drew " + draw_results['name'] + "\n" + str(draw_results['scryfall_uri']))
            try:
               await message.channel.send(draw_results['image_uris']['normal'])
            except:
               pass

    elif message.content.startswith("$tellmeastory"):
        story_prompt = message.content.replace('$tellmeastory ', '')
        print(story_prompt)
        await message.channel.send("Asking the almighty chat GPT for a story about " + str(story_prompt))

        generate_story = chat_gpt_prompt(story_prompt)
        print(generate_story)

        print(generate_story['choices'][0]['message']['content'])

        story = generate_story['choices'][0]['message']['content']
        print(story)
        await message.channel.send(story)


        #answer['choices'][0]['message']['content']




    else:
        await message.channel.send('Hi there! I am a bot that can do a few things if you ask (in the merc-bot channel or DM me!): \n 1.Send 🤣 for a dad joke (or just type the words Dad Joke) \n 2.Send $image <prompt> to generate 3 images based on your prompt (example: $image Dog Wearing Shoes) \n 3.Send $mtgsearch <Card Name> to search Scryfall for Magic The Gathering Cards (Example: $mtgsearch Niv Mizzet, Parun) \n 4.Send $randommtg to draw a random Magic The Gathering card its like opening packs for free! \n 5.Send $tellmeastory <What you want a story about> (ex:$tellmeastory about that time superman and Mr.Rogers got into it and Mr.Rogers won) to generate a story.')
# Discord developer portal:        
#https://discord.com/developers/
client.run(user_creds.discord_api_key)


