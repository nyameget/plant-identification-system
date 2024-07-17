from bs4 import BeautifulSoup
import wikipediaapi
import requests
import urllib.parse

### This transforms the numbers to a message
def watering_message(watering):
  if watering is not None:
    if watering['max'] is not None and watering['min'] is not None:
      max_water = int(watering['max'])
      min_water = int(watering['min'])
      if min_water == 1 and max_water == 2:
        watering_data = 'Needs no or moderate watering, keep the soil moist or dry.'
      elif min_water == 1 and max_water == 3:
        watering_data = 'Needs moderate watering, keep the soil moist but not waterlogged.'
      elif min_water == 2 and max_water == 3:
        watering_data = 'Needs moderate or more watering, keep the soil moist or waterlogged.'
      elif min_water == 1 and max_water == 1:
        watering_data = 'Needs no watering, keep the soil dry.'
      elif min_water == 2 and max_water == 2:
        watering_data = 'Needs moderate watering, keep soil moist.'
      elif min_water == 3 and max_water == 3:
        watering_data = 'Needs more watering, keep soil waterlogged.'
  else:
    watering_data= "None"
  return watering_data

### This truncates the words so that all have the same word limits
def truncate_words(sentence, word_limit):
    words = sentence.split()
    if len(words) <= word_limit:
      return sentence
    truncated = ''.join(words[:word_limit])
    return truncated + "..."

### This generates the severity level of the disease
def generate_category(number):
    number = int(number)
    if number >= 0 and number <= 0.25:
      return 'Mild'
    elif number > 0.25 and number <= 0.5:
      return 'Moderate'
    elif number > 0.5 and number <= 0.75:
      return 'Serious'
    elif number > 0.75:
      return 'Critical'

def search_pfaf_by_name(name):
  search_url = f"https://pfaf.org/user/DatabaseSearhResult.aspx?CName=%{urllib.parse.quote(name)}%"
  response = requests.get(search_url)
  soup = BeautifulSoup(response.text, 'html.parser')
  return soup.find('table', id='ContentPlaceHolder1_gvresults')

### This finds the exact page url and the latin name of the plant 
def find_plant_page_by_name(common_name, botanical_name):
  result_table = search_pfaf_by_name(common_name)
  botanical_name = botanical_name.split(' ')[0]
  if not result_table and len(common_name.split()) > 1:
    parts = common_name.split()
    result_table_a = search_pfaf_by_name(parts[0])
    result_table_b = search_pfaf_by_name(parts[1])
  else:
    result_table_b = result_table_a = result_table
  ### This checks the table for the reult that best describes the searched plant
  def check_table(result_table):
    if not result_table:
      return None, None
    rows = result_table.find_all('tr')[1:]  # Skip the header row
    for row in rows:
      columns = row.find_all('td')
      if len(columns) < 2:
        continue
      latin_name = columns[0].get_text().strip()
      common_name_ = columns[1].get_text().strip()
      if botanical_name.lower() in latin_name.lower() or common_name.lower() in common_name_.lower():
        return latin_name, f"https://pfaf.org/user/Plant.aspx?LatinName={urllib.parse.quote(latin_name)}"
    return None, None

  latin_name, plant_page_url = check_table(result_table_a)
  if not plant_page_url:
    latin_name, plant_page_url = check_table(result_table_b)

  return latin_name, plant_page_url

def scrape_medical_uses(soup):
  # Find the section containing Edible Uses
  medicinal_uses_section = soup.find('h2', string='Medicinal Uses')
  
  if not medicinal_uses_section:
    print("Medicinal Uses section not found on the page")
    return None
  
  # Find the parent div with class 'boots3' containing Edible Uses content
  boots2_div = medicinal_uses_section.find_next('div', class_='boots2')
  
  if not boots2_div:
    print("Unable to locate the 'boots3' class for Medicnal Uses")
    return None
  
  # Initialize content to collect text
  medicinal_uses = []
  
  # Extract the content within the 'boots3' class
  next_element = boots2_div.find_next()
  
  while next_element:
    # Check if we've reached the end marker (small tag with text-muted class)
    if next_element.name == 'small' and 'text-muted' in next_element.get('class', []):
      break
    
    # Remove <br> tags
    for br_tag in next_element.find_all('br'):
      br_tag.replace_with('\n')  # Replace <br> with newline
    
    # Remove <i> tags and their content
    for i_tag in next_element.find_all('i'):
      i_tag.decompose()  # Completely remove <i> tags and their content
    # Check for "Edible Part" text followed by <a> tags
    if len(next_element.find_all('a')) == 0:
      medicinal_uses.append(next_element.get_text(strip=True))
    else:
      medicinal_uses.append(next_element.find_all(string=True)[-2]) 
    next_element = next_element.find_next_sibling()
  
  return medicinal_uses 

def scrape_edible_uses(soup):
  # Find the section containing Edible Uses
  edible_uses_section = soup.find('h2', string='Edible Uses')
  
  if not edible_uses_section:
    print("Edible Uses section not found on the page")
    return None
  
  # Find the parent div with class 'boots3' containing Edible Uses content
  boots3_div = edible_uses_section.find_next('div', class_='boots3')
  
  if not boots3_div:
    print("Unable to locate the 'boots3' class for Edible Uses")
    return None
  
  # Initialize content to collect text
  edible_parts = []
  edible_uses = []
  
  # Extract the content within the 'boots3' class
  next_element = boots3_div.find_next()
  
  while next_element:
    # Check if we've reached the end marker (small tag with text-muted class)
    if next_element.name == 'small' and 'text-muted' in next_element.get('class', []):
      break
    
    # Remove <br> tags
    for br_tag in next_element.find_all('br'):
      br_tag.replace_with('\n')  # Replace <br> with newline
    
    # Remove <i> tags and their content
    for i_tag in next_element.find_all('i'):
      i_tag.decompose()  # Completely remove <i> tags and their content
    # Check for "Edible Part" text followed by <a> tags
    if "Edible Part" in next_element.get_text():
      edible_part_tags = next_element.find_all('a')
      for tag in edible_part_tags:
        edible_parts.append(tag.get_text(separator='\n', strip=True))

    # Check for "Edible Use"
    if 'Edible Uses' in next_element.get_text():
      edible_uses.append(next_element.find_all(string=True)[-2]) 
    else:
      edible_uses.append(next_element.get_text(strip=True))
    next_element = next_element.find_next_sibling()
  
  return edible_parts, edible_uses 

def scrape_other_uses(soup):
    # Find the section containing Edible Uses
    other_uses_section = soup.find('h2', string='Other Uses')
    
    if not other_uses_section:
      print("Other Uses section not found on the page")
      return None
    
    # Find the parent div with class 'boots3' containing Edible Uses content
    boots4_div = other_uses_section.find_next('div', class_='boots4')
    
    if not boots4_div:
      print("Unable to locate the 'boots4' class for Other Uses")
      return None
    
    # Initialize content to collect text
    other_uses = []
    
    # Extract the content within the 'boots3' class
    next_element = boots4_div.find_next()
    
    while next_element and next_element.name != 'h3':
      if len(next_element.find_all('a')) == 0:
        text = next_element.get_text().strip()
        if text:  # Check if text is not empty
          other_uses.append(text)
      else:
        strings = next_element.find_all(string=True)
        if 'Special Uses' in strings:
          special_index = strings.index('Special Uses')
          if special_index > 0:
            other_uses.append(strings[special_index - 1].strip())
        else:
          if strings[-1].strip():  # Check if last string is not empty
            other_uses.append(strings[-1].strip())

      next_element = next_element.find_next_sibling()

    return other_uses 

### This gets the plant uses by checking pfaf
def get_plant_uses_pfaf(common_name, botanical_name):
  latin_name, plant_page_url = find_plant_page_by_name(common_name, botanical_name)
  if not plant_page_url:
    return None
  response = requests.get(plant_page_url)
  soup = BeautifulSoup(response.text, 'html.parser')
  medicinal_uses = scrape_medical_uses(soup)
  edible_parts, edible_uses = scrape_edible_uses(soup)
  other_uses = scrape_other_uses(soup)

  uses = {
      'Other Uses': other_uses,
      'Edible Parts': edible_parts,
      'Edible Uses': edible_uses,
      'Medicinal Uses': medicinal_uses   
  }

  return uses

### This gets the plant uses by checking wikipedia
def get_plant_use_wikipedia(plant_name):
  plant_name = plant_name.replace(' ', '_')
  wiki = wikipediaapi.Wikipedia('Nyameget (NYAMEGET@GMAIL.COM)', 'en', extract_format=wikipediaapi.ExtractFormat.HTML)
  page = wiki.page(plant_name)
  uses_section = page.section_by_title('Uses')
  
  if uses_section is None:
    return {None, None}
  if len(uses_section.sections) == 1:
    soup = BeautifulSoup(uses_section.text, "html.parser")
    paragraphs = soup.find_all('p')
    
    if len(paragraphs) > 1:
      return {paragraphs[0].text[:-2], paragraphs[1].text[:-2]}
    elif len(paragraphs) == 1:
      return {paragraphs[0].text[:-2], None}
    else:
      return {None, None}
  elif len(uses_section.sections) > 1:
    if len(BeautifulSoup(uses_section.text, "html.parser").find_all('p')) == 0:
      uses_section = uses_section.sections[0]
    soup = BeautifulSoup(uses_section.text, "html.parser")
    paragraphs = soup.find_all('p')
    
    if len(paragraphs) > 1:
      return {paragraphs[0].text[:-2], paragraphs[1].text[:-2]}
    elif len(paragraphs) == 1:
      return {paragraphs[0].text[:-2], None}
    else:
      return {None, None}

### This gets the plant uses by checking pfaf if no result is returned then checks wikipedia
def get_plant_uses(common_name, botanical_name):
  uses = get_plant_uses_pfaf(common_name, botanical_name)
  if uses:
    return uses
  else:
    wikipedia_info = get_plant_use_wikipedia(common_name)
    return wikipedia_info
