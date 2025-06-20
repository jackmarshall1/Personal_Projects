import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import pickle
import urllib.parse

# Define the URL
urls = {"https://rupaulsdragrace.fandom.com/wiki/Lip_Sync_Performances/RuPaul%27s_Drag_Race" : "RuPaul.27s_Drag_Race_Lip_Sync_Songs",
        "https://rupaulsdragrace.fandom.com/wiki/Lip_Sync_Performances/RuPaul%27s_Drag_Race_All_Stars" : "RuPaul.27s_Drag_Race_All_Stars_Lip_Sync_Songs"}

data = []
for url in urls:
    # Send a GET request
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the table under "RuPaul's Drag Race Lip Sync Songs" section
    section_header = soup.find("span", {"id": urls[url]})
    tables = section_header.find_all_next("table") if section_header else []

    table = tables[0] if len(tables) > 1 else None

    # Extract data if table is found
    for table in tables:

        rows = table.find_all("tr")[1:]  # Skip header row

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 4:

                test = ["image" in str(a) for a in cols]

                if True not in test:
                    continue
                
                image_index = test.index(True) - len(test)

                song = cols[image_index-1].text.strip()
                winner = cols[image_index+1].text.strip()
                loser = cols[image_index+2].text.strip()

                winner_links = cols[image_index+1].find_all("a")  # Find all <a> tags
                winner = [urllib.parse.unquote(link["href"].replace('/wiki/','')) for link in winner_links if "href" in link.attrs]  # Extract hrefs

                loser_links = cols[image_index+2].find_all("a")  # Find all <a> tags
                loser = [urllib.parse.unquote(link["href"].replace('/wiki/','')) for link in loser_links if "href" in link.attrs]  # Extract hrefs

                img_tag = cols[image_index].find("img")
                season = img_tag["data-image-name"] if img_tag else '' 
                season = re.search(r"^(.*?)(?=[LE])", season)

                if season:
                    season = season.group(1)
                else:
                    continue

                if song.startswith('"'):

                    song_comp = song.split('"')

                    data.append([song_comp[1].strip(),song_comp[2].replace('by','').strip(), season, winner, loser])

AS1_Edge_Case = pd.DataFrame({
    'Song' : ["Opposites Attract", "There's No Business Like Show Business", "Nasty", "Don't Cha", "Dancing On My Own", "Responsitrannity"],
    'Artist' : ["Paula Abdul", "Ethel Merman", "Janet Jackson", "The Pussycat Dolls", "Robyn", "RuPaul"],
    'Season' : ["AS1"]*6,
    'Winner' : [["Chad_Michaels"], ["Latrice_Royale"], ["Jujubee"], ["Raven"], ["Jujubee", "Raven"], ["Chad_Michaels"]],
    'Loser' : [["Mimi_Imfurst"], ["Tammie_Brown"], ["Manila_Luzon"], ["Alexis_Mateo", "Yara_Sofia"], [], ["Raven"]]
})

AS5_Edge_Case = pd.DataFrame({
    'Song' : ["Make Me Feel"],
    'Artist' : ["Janelle Monáe"],
    'Season' : ["AS5"],
    'Winner' : [["Shea Couleé"]],
    'Loser' : [["Jujubee", "Miz Cracker"]]
})

S13_Edge_Cast = pd.DataFrame({
    'Song' : ["Be My Lover", "Work Bitch", "Gimme More", "Till the World Ends"],
    'Artist' : ["La Bouche", "Britney Spears", "Britney Spears", "Britney Spears"],
    'Season' : ["S13"]*4,
    'Winner' : [["Denali"], ["Kandy Muse"], ["Symone"], ["Symone"]],
    'Loser' : [["LaLa Ri"], ["Rosé"], ["Gottmik"], ["Kandy Muse"]]
})

S12_Edge_Cast = pd.DataFrame({
    'Song' : ["Survivor"],
    'Artist' : ["Destiny's Child"],
    'Season' : ["S12"],
    'Winner' : [["Jaida Essence Hall"]],
    'Loser' : [["Crystal Methyd", "Gigi Goode"]]
})

S11_Edge_Cast = pd.DataFrame({
    'Song' : ["The Edge of Glory"],
    'Artist' : ["Lady Gaga"],
    'Season' : ["S11"],
    'Winner' : [["Yvie Oddly"]],
    'Loser' : [["Brooke_Lynn_Hytes"]]
})

S10_Edge_Cast = pd.DataFrame({
    'Song' : ["Bang Bang"],
    'Artist' : ["Jessie J, Ariana Grande, Nicki Minaj"],
    'Season' : ["S10"],
    'Winner' : [["Aquaria"]],
    'Loser' : [["Eureka!", "Kameron Michaels"]]
})

lipsync_df = pd.DataFrame(data, columns=["Song", "Artist", "Season", "Winner", "Loser"])
lipsync_df = pd.concat([lipsync_df[lipsync_df['Season'] != 'AS1'],AS1_Edge_Case, AS5_Edge_Case, S11_Edge_Cast, S10_Edge_Cast])
lipsync_df['Season'] = lipsync_df['Season'].apply(lambda x : 'AS6' if x == 'R' else 'AS4' if x == '' else x)

def extract_bio_info(label, bio_section):
    if bio_section:
        data_div = bio_section.find("h3", string=label)
        if data_div:
            value_div = data_div.find_next("div", class_="pi-data-value pi-font")
            return value_div.text.strip() if value_div else None
    return None

unique_list_of_queens = pd.concat([lipsync_df['Winner'].explode(), lipsync_df['Loser'].explode()]).unique()

data = []

for queen in unique_list_of_queens:

    if str(queen) == 'nan':
        continue

    # URL of the wiki page
    url = "https://rupaulsdragrace.fandom.com/wiki/"+queen

    # Send a GET request
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    actual_url = response.url
    corrected_queen_name = actual_url.split('/wiki/')[-1]

    if corrected_queen_name == queen:
        queen = None

    # Locate the "Biographical Information" section
    bio_section = soup.find("section", class_="pi-item pi-group pi-border-color")

    # Extracting Age and Height
    age = extract_bio_info("Age", bio_section)
    height = extract_bio_info("Height", bio_section)
    birthplace = extract_bio_info("Birthplace", bio_section)

    data.append([corrected_queen_name, queen, age, height, birthplace])

queen_df = pd.DataFrame(data, columns=["Queen", "Queen Synonym", "Age", "Height", "Birthplace"]).fillna('N/A')

queen_df = queen_df.groupby(['Queen', 'Age', 'Height', 'Birthplace'])[['Queen Synonym']].agg(list).reset_index().sort_values(by='Queen')
queen_df['index'] = queen_df.index
queen_df['Queen'] = queen_df['Queen'].apply(lambda x : urllib.parse.unquote(x))
queen_df = queen_df.set_index('index')

def drop_na_from_list(l):
    return [a for a in l if a != 'N/A']

queen_df['Queen Synonym'] = queen_df['Queen Synonym'].apply(drop_na_from_list)

def remove_citation(string):
    if string:
        return re.sub(r'\[.*?\]', '', string)
    else:
        return None

queen_df['Height'] = queen_df['Height'].apply(remove_citation)
queen_df['Birthplace'] = queen_df['Birthplace'].apply(remove_citation)

with open('./data/queen_df.pkl', 'wb') as f:
    pickle.dump(queen_df, f)

def synonym_to_name(name):
    queen_df_exp = queen_df.explode('Queen Synonym')
    queen_df_exp = queen_df_exp[~queen_df_exp['Queen Synonym'].isna()]
    queen_df_exp = queen_df_exp.set_index('Queen Synonym')[['Queen']]

    if name in queen_df_exp.index:
        return queen_df_exp.loc[name]['Queen']
    else:
        return name

lipsync_df['Winner'] = lipsync_df['Winner'].apply(lambda x : [synonym_to_name(a) for a in x])
lipsync_df['Loser'] = lipsync_df['Loser'].apply(lambda x : [synonym_to_name(a) for a in x])

lipsync_df['Queens'] = lipsync_df['Winner'] + lipsync_df['Loser']

with open('./data/lipsync_data.pkl', 'wb') as f:
    pickle.dump(lipsync_df, f)
