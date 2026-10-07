# Menu Search Benchmark Queries
**8 restaurants**: Juanita Cantina, Plaza Garcia, Staple & Fancy, Due' Cucina, Mendocino Farms, Great China Restaurant, Anthony's HomePort, Rimini Restaurant  
**Restaurants cover**: Mexican/Latin, Italian/Pasta/Pizza, Modern American, Farm-to-table sandwiches/salads, Chinese  
**Total queries**: 209 across 25 categories

Each query includes:
- **Expected match(es)**: what it should retrieve
- **Challenge type**: what linguistic/semantic phenomenon is being tested
- **Difficulty**: Easy / Medium / Hard

---

## Category C01: Cuisine Type Not in Item Text (Ontology / Type Inference)
*The item's text doesn't say "Mexican" or "Italian" — it must be inferred from the restaurant type or dish names*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C01-01 | Mexican food with shrimp | Camarones à la Diabla, Shrimp Fajitas, Tacos De Camaron | Cuisine label inference | Medium |
| C01-02 | Italian pasta with meat sauce | Mezze Rigatoni (wild boar ragu), Bolognese Ragu', Lasagna | Cuisine inference | Medium |
| C01-03 | Latin seafood dish | Sopa Del Mar, Seafood Enchiladas, Ceviche De Camarones | Cuisine + category inference | Medium |
| C01-04 | Tex-Mex combination plate | Combo plates at Plaza Garcia, Juanita Cantina combos | Cuisine inference | Hard |
| C01-05 | farm to table sandwich | Mendocino Farms sandwiches (their explicit tagline) | Brand/concept → menu | Medium |
| C01-06 | taqueria style tacos | 3 Street Tacos, Street Tacos | Concept → item type | Hard |
| C01-07 | rustic Italian comfort food | Lasagna alla Bolognese, Due' Cucina items generally | Concept generalization | Hard |
| C01-08 | fine dining pasta | Pappardelle (crab, brown butter), Gramigna (Staple & Fancy) | Price/context inference | Hard |

---

## Category C02: Ingredient → Category Generalization
*Query uses a category word; menu uses specific items in that category*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C02-01 | seafood tacos | Tacos De Pescado (cod), Tacos De Camarones (shrimp) | Ingredient → seafood category | Medium |
| C02-02 | shellfish pasta | Shrimp & Clam Bucatini, Pappardelle (crab) | Shellfish generalization | Medium |
| C02-03 | leafy green salad | Gem Lettuce, Little Gem, Cantina Salad (romaine) | Green → specific leaf type | Medium |
| C02-04 | stone fruit dessert | Tiramisu w/ plum, Burrata (compressed pluot) | Stone fruit generalization | Hard |
| C02-05 | smoked meat sandwich | Heirloom BLT (bacon), Chimichurri Steak & Bacon | Smoke-cured generalization | Hard |
| C02-06 | cured meat appetizer | Prosciutto, Bruschetta (smoked fish) | Cured → specific types | Medium |
| C02-07 | steak dish | Carne Asada, SRF Skirt Wagyu, Ribeye Steak, Coulotte Steak | Steak generalization | Easy |
| C02-08 | fresh cheese salad | Burrata (heirloom tomato), Burrata Salad | Fresh cheese inference | Medium |
| C02-09 | pork dishes | Carnitas, Posole, Michoacan Carnitas, Short Ribs Ragu | Pork generalization | Easy |
| C02-10 | citrus fish | Halibut (Staple & Fancy), Tacos De Pescado (lemon/lime) | Citrus + fish combination | Medium |

---

## Category C03: Attribute / Implied Meaning
*Query uses a taste/texture/experience descriptor; menu describes the underlying ingredient or cooking style*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C03-01 | spicy shrimp | Camarones à la Diabla, Chipotle Shrimp Enchiladas, Camarones Bravos | Diabla/Diablo → spicy | Medium |
| C03-02 | something smoky | Smoked Fish Bruschetta, Mezcal cocktails (implied smokiness) | Smoke attribute | Hard |
| C03-03 | rich creamy pasta | Carbonara, Pollo ala Crema, Radiatore alla Vodka | Cream/egg richness | Medium |
| C03-04 | light fresh starter | Hamachi Crudo, Shrimp Ceviche, Spring Pea Soup | Light/fresh attribute | Medium |
| C03-05 | fire grilled meat | Carne Asada (flame grill), Wood Fire Grill section items | Fire → grill method | Medium |
| C03-06 | comfort food pasta | Lasagna, Bolognese, Kid Red Sauce Pasta | Comfort food concept | Hard |
| C03-07 | umami dish | Cacio e Pepe (truffle butter), Mushroom & White Truffle Oil | Umami inference | Hard |
| C03-08 | gut feeling filling meal | Burrito Asada, Seafood Burrito, Casa Burrito | Satiety inference | Hard |
| C03-09 | cajun style shrimp | Camarones à la Diabla (closest match) | Cajun implies spicy/butter sauce | Hard |
| C03-10 | tangy dressing salad | Caesar Salad, Gem Lettuce (raspberry vinaigrette) | Tangy → vinaigrette/dressing | Medium |
| C03-11 | charred vegetables | Roasted Carrots (Staple & Fancy), Fried Artichokes, Veggie Fajitas | Char → roasted/grilled | Medium |
| C03-12 | indulgent dessert | Affogato Ubriaco, Espresso Affogato, Tiramisu | Indulgent concept | Hard |

---

## Category C04: Cooking Method Synonyms
*Grilled vs seared vs charbroiled vs pan-fried vs flame-cooked*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C04-01 | charbroiled steak | Carne Asada (flame grill), Steak Matador (char-broiled) | Charbroiled = chargrilled | Easy |
| C04-02 | seared fish | Halibut (wood fire grill), Pescado a la Parrilla | Seared ↔ grilled | Medium |
| C04-03 | pan seared salmon | Halibut / Chef's menu salmon items (Staple & Fancy) | Pan seared ↔ wood fire | Medium |
| C04-04 | blackened chicken | Pollo Asado, Pollo Ranchero (closest matches) | Blackened ↔ seasoned grilled | Hard |
| C04-05 | flame broiled burger | Jalapeño Cheeseburger, Hawaiian Cheeseburger | Flame broiled = grilled | Medium |
| C04-06 | wood fired pizza | Mexican Flatbread, Mexican Pizza (closest) | Wood fire concept | Hard |
| C04-07 | slow cooked pork | Carnitas (slow braised implied), Michoacan Carnitas, Chili Verde | Slow cook inference | Medium |
| C04-08 | braised beef | Short Ribs Ragu', Taco Birria (beef), Chile Colorado | Braise ↔ ragu/stew | Medium |
| C04-09 | deep fried appetizer | Taquitos Rancheros, Cheese Sticks, Fried Artichokes | Deep fried = fried | Easy |
| C04-10 | crispy fried chicken | Not So Fried Chicken (Mendocino), Crispy Chicken Salad | Crispy + fried | Easy |

---

## Category C05: Spelling Variations & Common Misspellings

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C05-01 | caeser salad | Caesar Salad (Juanita/Plaza Garcia) | Misspelling: Caesar | Easy |
| C05-02 | quesedilla | Quesadillas | Misspelling: quesadilla | Easy |
| C05-03 | guacamolee | Fresh Avocado / Guacamole side | Misspelling: guacamole | Easy |
| C05-04 | enchilladas | Enchiladas (all variants) | Misspelling: enchiladas | Easy |
| C05-05 | fettucine carbonara | Carbonara (Due' Cucina) | Misspelling: fettuccine; wrong pasta name | Medium |
| C05-06 | tiramisou | Tiramisu | Misspelling: tiramisu | Easy |
| C05-07 | prosciuto | Prosciutto | Misspelling: prosciutto | Easy |
| C05-08 | cevice | Shrimp Ceviche, Ceviche De Camarones | Misspelling: ceviche | Easy |
| C05-09 | proscuitto and melon | Prosciutto (compressed melon) | Double misspelling | Medium |
| C05-10 | rigatonni bolognese | Mezze Rigatoni / Bolognese Ragu' | Misspelling: rigatoni | Easy |
| C05-11 | canoli | Cannolo Siciliano | Misspelling: cannolo | Easy |
| C05-12 | burratta | Burrata | Misspelling: burrata | Easy |
| C05-13 | halebut | Halibut | Misspelling: halibut | Easy |
| C05-14 | focacia sandwich | Artisan Focaccia Sandwiches (Due' Cucina) | Misspelling: focaccia | Easy |
| C05-15 | camarones a la diabla | Camarones à la Diabla (Juanita), Camarones a la Diabla (Plaza Garcia) | Missing accent mark | Medium |

---

## Category C06: Stemming & Lemmatization
*Verb forms, plurals, gerunds that differ from menu text*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C06-01 | roasted carrot | Roasted Carrots (both restaurants) | Plural stemming | Easy |
| C06-02 | grilling octopus | Grilled Octopus | Gerund → past participle | Easy |
| C06-03 | fried artichoke | Fried Artichokes | Plural stemming | Easy |
| C06-04 | marinated steak | Steak Matador, Fajitas Carne Asada, Tacos Al Carbon | Lemma match | Easy |
| C06-05 | sauted mushroom | Camarones Mojo de Ajo (mushrooms sautéed) | Misspelling + lemma | Medium |
| C06-06 | slow braising short rib | Short Ribs Ragu' (slow-braised) | Gerund + plural stem | Medium |
| C06-07 | breading calamari | Breaded Calamari | Gerund → past participle | Easy |
| C06-08 | compress melon | Compressed melon (Prosciutto) | Stemming: compressed | Medium |
| C06-09 | season chicken | Pollo Asado (seasoned), Pollo Ranchero | Lemma: seasoned | Easy |
| C06-10 | pickle vegetables | Pickled red onion (multiple sandwiches), Dill Pickle Chips | Lemma: pickled | Easy |

---

## Category C07: Hyphenation, Spacing, Apostrophe, Stop Word Variations

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C07-01 | cacio e pepe | Cacio e Pepe Bucatini | Stop words (e) | Easy |
| C07-02 | cacioepepe | Cacio e Pepe Bucatini | No-space variant | Easy |
| C07-03 | al pastor | Burrito Al Pastor, 3 Street Tacos (al pastor option) | Stop word (al) | Easy |
| C07-04 | alpastor taco | Street Tacos (al pastor) | Merged/no space | Easy |
| C07-05 | mojo de ajo shrimp | Camarones Mojo de Ajo | Stop words (de) | Easy |
| C07-06 | arroz con pollo | Arroz Con Pollo | Stop word (con) | Easy |
| C07-07 | arrozconpollo | Arroz Con Pollo | No space variant | Easy |
| C07-08 | due cucina pasta | Due' Cucina menu items | Apostrophe drop | Easy |
| C07-09 | staple fancy restaurant | Staple & Fancy | Ampersand → and/drop | Easy |
| C07-10 | non dairy pasta | Gramigna, Pomodoro (vegan on request), Mediterranea | Non-dairy = dairy-free | Medium |
| C07-11 | gluten free pasta | Penne substitution (Staple & Fancy), Pomodoro GF option | Hyphen variation | Easy |
| C07-12 | glutenfree option | Same as above | No-hyphen variant | Easy |
| C07-13 | farm-to-table lunch | Mendocino Farms | Hyphenated concept | Easy |
| C07-14 | egg-free dessert | Sorbetto, Vanilla Gelato (checking for egg) | Hyphen + negation | Hard |

---

## Category C08: Dietary Constraint / Negation Queries
*"no X", "without X", "non-X", "free of X"*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C08-01 | vegetarian Mexican food | Veggie Fajitas, Spinach Enchilada, Veggie Enchiladas, Queso | Dietary + cuisine | Medium |
| C08-02 | vegan sandwich | Vegan Banh Mi, Mediterranea (Due' Cucina) | Dietary constraint | Easy |
| C08-03 | no gluten pasta | GF penne substitution, Pomodoro GF option | Negation = gluten-free | Medium |
| C08-04 | without dairy | Mediterranea salad (vegan), Southern Potato Salad | Negation = dairy-free | Medium |
| C08-05 | nut free salad | Golden State Cobb (no nuts noted), Taco Salad | Negation inference | Hard |
| C08-06 | plant based option | Vegan Banh Mi, Plant-Based Oat Hemp Date Cookie | Plant-based = vegan | Easy |
| C08-07 | meat free burrito | Burrito Vegetariano, Casa Burrito (no meat option) | Meat-free = vegetarian | Medium |
| C08-08 | dairy free pasta | Pomodoro (vegan on request), Shrimp & Clam Bucatini | Negation mapping | Hard |
| C08-09 | pescatarian dinner | Halibut, Pappardelle (crab), Seafood Enchiladas | Pescatarian = fish ok, no meat | Hard |
| C08-10 | keto friendly | Carne Asada (GF, low carb), salads without tortilla | Keto inference | Hard |

---

## Category C09: Synonym / Paraphrase Variation

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C09-01 | prawn dish | Camarones (Spanish = shrimp/prawn), Seafood Enchiladas | Prawn ↔ shrimp | Medium |
| C09-02 | mussel or clam appetizer | Clams with Chorizo | Clam = shellfish synonym | Medium |
| C09-03 | avocado toast | Bruschetta (Smoked Fish), Sourdough + avocado mentions | Toast = bruschetta | Hard |
| C09-04 | flatbread | Mexican Flatbread, Bruschetta (grilled bread) | Flatbread concept | Medium |
| C09-05 | corn tortilla chips and dip | Nachos, Queso Dip, Chips + Salsa | Chips + dip = nachos | Medium |
| C09-06 | Mexican cheese dip | Queso Dip, Queso Fundido | Cheese dip = queso | Easy |
| C09-07 | cold raw fish | Hamachi Crudo, Shrimp Ceviche | Raw fish → crudo/ceviche | Medium |
| C09-08 | Italian rice balls | Suppli Al Telefono | Rice ball = suppli | Hard |
| C09-09 | espresso based cocktail | Espresso Martini, Oh George (coffee liqueur) | Coffee cocktail | Medium |
| C09-10 | after dinner drink | Amaro & Liqueur section, Dessert Wine | Post-dinner = digestif/amaro | Hard |

---

## Category C10: Multi-Constraint / Compositional Queries

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C10-01 | spicy vegetarian taco | Veggie Fajitas w/ salsa, Cauliflower Wings + salsa | Multi-constraint | Hard |
| C10-02 | gluten free seafood under $30 | Shrimp Fajitas $26 (hit), Ceviche $21 (hit), Halibut $38 (miss) | GF + category + price | Hard |

---

## Category C11: Food Type — Soup
*Single-word and short food-type queries; tests whether the system maps food type to matching items across restaurants. Note: these menus are not soup-heavy so expected recall is low for some queries — useful for testing precision.*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C11-01 | soup | Tortilla Soup (Juanita/Plaza), Posole, Sopa Del Mar, Tomato Basil Soup, Lemon Chicken & Farro Soup | Broad food type | Easy |
| C11-02 | chicken soup | Tortilla Soup (grilled chicken in broth), Lemon Chicken & Farro Soup | Ingredient + food type | Easy |
| C11-03 | tomato soup | Tomato Basil Soup (Mendocino) | Direct food type | Easy |
| C11-04 | seafood soup | Sopa Del Mar (fish + shrimp in tomato broth) | Category + food type | Medium |
| C11-05 | spicy soup | Posole (pork stew), Sopa Del Mar | Attribute + food type | Medium |
| C11-06 | broth based soup | Tortilla Soup, Posole, Lemon Chicken & Farro Soup, Sopa Del Mar | Broth → soup inference | Medium |
| C11-07 | vegetable soup | Tomato Basil Soup (partial) | Dietary + food type; low recall expected | Hard |

---

## Category C12: Food Type — Burger
*Tests basic food-type retrieval; burgers only appear at the Mexican restaurants.*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C12-01 | burger | Jalapeño Cheeseburger, Hawaiian Cheeseburger, Cheeseburger, Juanita Chicken Burger, Kids Hamburger | Broad food type | Easy |
| C12-02 | cheeseburger | Jalapeño Cheeseburger, Hawaiian Cheeseburger, Cheeseburger, Kids Cheeseburger | Direct food type | Easy |
| C12-03 | chicken burger | Juanita Chicken Burger | Main ingredient + food type | Easy |
| C12-04 | beef burger | Cheeseburger, Jalapeño Cheeseburger, Hawaiian Cheeseburger | Ingredient inference (beef patty) | Easy |
| C12-05 | spicy burger | Jalapeño Cheeseburger (jalapeños + pepper jack) | Attribute inference | Medium |
| C12-06 | Hawaiian burger | Hawaiian Cheeseburger | Direct match (thematic name) | Easy |

---

## Category C13: Food Type — Taco
*Heavy coverage across both Mexican restaurants. Tests Spanish item names (Tacos De Camarones) and filling-based queries against menu titles that don't always name the filling.*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C13-01 | taco | 3 Street Tacos, Tacos Al Carbon, Taco Birria, Tacos De Pescado, Tacos De Camarones, Street Tacos, Combo 1 | Broad food type | Easy |
| C13-02 | fish taco | Tacos De Pescado (Pacific cod), Tacos de Pescado (Plaza) | Ingredient + food type | Easy |
| C13-03 | beef taco | Taco Birria (beef), Tacos Al Carbon (skirt steak) | Ingredient inference | Easy |
| C13-04 | chicken taco | 3 Street Tacos (chicken option), Tacos Al Carbon (marinated chicken) | Ingredient from description | Medium |
| C13-05 | shrimp taco | Tacos De Camarones, Tacos De Camaron (Plaza) | Camarones = shrimp inference | Medium |
| C13-06 | street taco | 3 Street Tacos, Street Tacos (Plaza) | Concept match | Easy |
| C13-07 | hard taco | Three Hard Tacos (Juanita happy hour) | Direct match | Easy |
| C13-08 | soft taco | 3 Street Tacos (corn tortillas = soft) | Tortilla type inference | Medium |

---

## Category C14: Food Type — Pasta
*Heavy coverage at Staple & Fancy and Due' Cucina. Tests both generic and specific pasta shape queries, and whether ingredient-in-description queries work (e.g. "pasta with egg" → Carbonara).*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C14-01 | pasta | Pappardelle, Mezze Rigatoni, Shrimp & Clam Bucatini, Cacio e Pepe Bucatini, Gramigna, Zozzona, Bolognese Ragu', Carbonara, Basil Pesto, Pomodoro | Broad food type | Easy |
| C14-02 | spaghetti | Spaghetti (chef's veg menu, Staple), Pomodoro (Due', closest shape) | Shape name; partial match expected | Medium |
| C14-03 | rigatoni | Mezze Rigatoni | Shape name direct match | Easy |
| C14-04 | bucatini | Shrimp & Clam Bucatini, Cacio e Pepe Bucatini, Bucatini (chef's menu) | Shape name direct match | Easy |
| C14-05 | pasta with egg | Carbonara (egg yolk explicit), Zozzona (egg yolk) | Ingredient in description | Medium |
| C14-06 | homemade pasta | All Due' Cucina pasta, Staple & Fancy pasta | Concept: fresh/house-made | Medium |
| C14-07 | pasta in tomato sauce | Polpette, Bolognese Ragu', Pomodoro, Radiatore alla Vodka (tomato base) | Sauce ingredient | Easy |
| C14-08 | pasta with truffle | Cacio e Pepe Bucatini (truffle butter), Bucatini (chef's), Mushroom & White Truffle Oil | Ingredient in description | Medium |

---

## Category C15: Food Type — Sandwich
*Concentrated at Mendocino Farms and Due' Cucina focaccia section. Tests whether "sandwich" maps to items described as "focaccia sandwich" or named by their filling.*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C15-01 | sandwich | All Mendocino Farms sandwiches, all Due' Cucina focaccia sandwiches | Broad food type | Easy |
| C15-02 | turkey sandwich | The Farm Club, Turkey Avo Salsa Verde | Main ingredient | Easy |
| C15-03 | chicken sandwich | Not So Fried Chicken, Chicken Parm Dip, Prosciutto & Chicken, Chicken Pesto Caprese | Main ingredient | Easy |
| C15-04 | BLT | Heirloom BLT; The Farm Club (partial — has B, L, T) | Acronym expansion | Medium |
| C15-05 | Italian sandwich | Caprese, Mortadella, Porchetta, Milanese (Due' Cucina) | Cuisine inference → sandwich | Medium |
| C15-06 | focaccia sandwich | All Due' Cucina artisan focaccia items | Bread type + food type | Easy |
| C15-07 | club sandwich | The Farm Club (name contains "Club") | Name-based inference | Medium |

---

## Category C16: Food Type — Salad
*Mendocino Farms is the primary salad restaurant. Tests breadth of retrieval across named salads.*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C16-01 | salad | All Mendocino salads, Gem Lettuce (Staple), Caesar Salad (Juanita/Plaza), Carlos Salad (Plaza) | Broad food type | Easy |
| C16-02 | Caesar salad | The Modern Caesar (Mendocino), Caesar Salad (Juanita), Cesar Salad (Plaza — different spelling) | Direct + spelling variant | Easy |
| C16-03 | chicken salad | Tuscan Pesto Salad, The Seasonal GOAT, Baja Green Goddess, The Modern Caesar, Chen's Crispy Rice | Ingredient from description | Easy |
| C16-04 | taco salad | Taco Salad (Juanita/Plaza), Taco Salad Vegetariano | Direct food type | Easy |
| C16-05 | avocado salad | Avocado & Quinoa Superfood Ensalada, Baja Green Goddess | Ingredient + food type | Easy |
| C16-06 | quinoa salad | Avocado & Quinoa Superfood Ensalada | Ingredient + food type | Easy |
| C16-07 | kale salad | Kale & Apple Rainbow Salad | Ingredient + food type | Easy |

---

## Category C17: Food Type — Dessert / Sweet
*Cross-restaurant dessert retrieval. Note intentional gaps: no churros/flan at Staple, Mendocino, or Due' Cucina.*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C17-01 | dessert | Tiramisu (all), Cheesecake, Espresso Affogato, Cannolo Siciliano, Churros, Flan, Cookies (Mendocino), Sorbetto | Broad food type | Easy |
| C17-02 | tiramisu | Tiramisu (Staple & Fancy, Due' Cucina, Juanita happy hour) | Direct match across restaurants | Easy |
| C17-03 | gelato | Vanilla Gelato, Espresso Affogato (vanilla gelato), Affogato Ubriaco | Direct + ingredient match | Easy |
| C17-04 | churros | Churros (Plaza Garcia only) | Direct match; tests single-restaurant hit | Easy |
| C17-05 | flan | Flan (Plaza Garcia only) | Direct match | Easy |
| C17-06 | cheesecake | Cheesecake (Staple & Fancy), Lemon Cheesecake Cookie (Mendocino) | Direct + partial | Easy |
| C17-07 | cookie | Ginger Molasses Cookie, Lemon Cheesecake Cookie, Plant-Based Oat Hemp Date Cookie, Chocolate Chunk Cookie | Broad food type | Easy |
| C17-08 | cannoli | Cannolo Siciliano (Due' Cucina) | Direct match; tests singular/plural | Easy |

---

## Category C18: Main Ingredient — Chicken
*Tests retrieval of chicken items described in English ("grilled chicken breast") and Spanish ("pollo asado", "arroz con pollo"). The Spanish-named items are the hard cases.*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C18-01 | chicken | Pollo Asado, Pollo Chipotle, Arroz Con Pollo, Pollo Ala Crema, Chicken Fajitas, Not So Fried Chicken, Chicken Parm Dip, etc. | Broad ingredient; English + Spanish items | Medium |
| C18-02 | grilled chicken | Pollo Asado (grilled chicken explicitly), Tacos Al Carbon (marinated grilled chicken) | Cooking method + ingredient | Easy |
| C18-03 | chicken with mushrooms | Pollo Asado (topped with mushrooms), Arroz Con Pollo (peppers + mushrooms) | Two-ingredient description | Medium |
| C18-04 | chicken in cream sauce | Pollo Ala Crema, Pollo a la Crema (Plaza) | Sauce inference; Spanish name | Medium |
| C18-05 | chicken with peppers | Arroz Con Pollo, Chicken Fajitas, Pollo Chipotle, Pollo Bravo | Ingredient in description | Easy |
| C18-06 | chicken with avocado | Juanita Chicken Burger (avocado in ingredients), Cantina Salad (chicken + avocado option) | Two-ingredient combination | Medium |

---

## Category C19: Main Ingredient — Beef / Steak
*Tests English steak terms against Spanish menu names ("carne asada", "carnitas de res") and specific cut names.*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C19-01 | beef | Carne Asada, Ribeye Steak, Mexican Steak, Beef Fajitas, Taco Birria, Bolognese Ragu', Short Ribs Ragu', Chile Colorado | Broad ingredient; English + Spanish | Medium |
| C19-02 | skirt steak | Carne Asada (skirt steak explicit), Mexican Steak (marinated skirt steak), Steak Tapiqueño | Cut name direct match | Easy |
| C19-03 | ribeye | Ribeye Steak (Juanita), Chef Special (charbroiled ribeye at Plaza) | Cut name direct match | Easy |
| C19-04 | ground beef | Cheeseburger (ground beef patty), Nacho Supreme (ground beef option) | Ingredient in description | Medium |
| C19-05 | beef stew | Chile Colorado (beef cubes in spicy red sauce), Posole (stew-style) | Stew concept inference | Medium |
| C19-06 | short rib | Short Ribs Ragu' (Due' Cucina) | Direct ingredient match | Easy |

---

## Category C20: Main Ingredient — Pork
*Includes Spanish pork terms (carnitas, guanciale, al pastor) that a lexical system will miss without synonym expansion.*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C20-01 | pork | Michoacan Carnitas, Chili Verde, Burrito Al Pastor, Posole, Zozzona (guanciale), Carbonara (guanciale), Mortadella, Porchetta | Broad ingredient; cross-language | Hard |
| C20-02 | carnitas | Michoacan Carnitas, Carnitas De Puerco, 3 Street Tacos (option) | Spanish term direct match | Easy |
| C20-03 | guanciale pasta | Carbonara, Zozzona (both use guanciale explicitly) | Italian ingredient term | Medium |
| C20-04 | pulled pork | Michoacan Carnitas (closest equivalent — shredded pork) | Synonym: pulled pork = carnitas | Hard |
| C20-05 | pork with green sauce | Chili Verde, Burrito Chili Verde (tomatillo = green sauce) | Sauce colour inference | Medium |
| C20-06 | bacon wrapped | Camarones con Bacon (shrimp wrapped in bacon), Camarones Garcia (bacon-wrapped) | Cooking presentation | Easy |

---

## Category C21: Main Ingredient — Shrimp / Seafood
*The most densely covered ingredient across the two Mexican restaurants. Also tests Spanish names (camarones), specific seafood types (crab, scallops, tilapia, cod), and cross-ingredient queries.*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C21-01 | shrimp | Camarones à la Diabla, Camarones Mojo de Ajo, Camarones con Bacon, Shrimp Juanita, Shrimp Fajitas, Shrimp Ceviche, Tacos De Camarones, Garlic Shrimp, Shrimp & Clam Bucatini, and more | Broad ingredient; English + Spanish | Medium |
| C21-02 | garlic shrimp | Shrimp Juanita (sautéed in garlic), Camarones Mojo de Ajo (mojo de ajo = garlic sauce), Garlic Shrimp (Plaza) | Mojo de ajo = garlic inference | Medium |
| C21-03 | shrimp with rice | Camarones à la Diabla (served with rice), Arroz Con Mariscos (shrimp on rice) | Preparation + side | Medium |
| C21-04 | crab | Pappardelle (crab, brown butter), Seafood Enchiladas (contains crab), Seafood Burrito, Seafood Chimichangas | Ingredient in description | Medium |
| C21-05 | scallops | Seafood Enchiladas (shrimp, fish, crab, scallops), Seafood Burrito, Seafood Chimichangas | Ingredient in description | Medium |
| C21-06 | octopus | Grilled Octopus (Staple & Fancy) | Direct match; single restaurant | Easy |
| C21-07 | fish | Tacos De Pescado, Sopa Del Mar, Pescado a la Parrilla, Halibut, Smoked Fish Bruschetta | Broad ingredient; English + Spanish | Easy |
| C21-08 | tilapia | Pescado a la Parrilla (grilled tilapia explicitly, Plaza Garcia) | Species name direct match | Easy |
| C21-09 | cod | Tacos De Pescado (Pacific cod, Juanita) | Species name in description | Medium |

---

## Category C22: Additional Ingredient / Sauce / Flavour
*Tests retrieval by a secondary ingredient or sauce mentioned in item descriptions rather than item names.*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C22-01 | black bean | Rice & Beans, Beans (Juanita), Nacho Supreme (black beans in description) | Ingredient in description | Easy |
| C22-02 | avocado | Fresh Avocado, Avocado Tostada, Avocado Slices, Fiesta Avocado, Avocado & Quinoa Ensalada, The Farm Club | Ingredient direct + in description | Easy |
| C22-03 | chipotle sauce | Chipotle Shrimp Enchiladas, Pollo Chipotle, Pollo Chipotle (Plaza) | Sauce name in item name | Easy |
| C22-04 | mole sauce | Pollo en Mole, Enchiladas en Mole, Pollo En Mole (Plaza), Deluxe Mole Enchilada | Sauce name in item name | Easy |
| C22-05 | tomatillo | Chili Verde (green tomatillo sauce), Burrito Chili Verde, Veggie Enchiladas | Ingredient in description | Medium |
| C22-06 | pico de gallo | Pico De Gallo (side), Carne Asada (garnished with pico) | Ingredient direct + in description | Easy |
| C22-07 | pesto | Basil Pesto (Due'), Chicken Pesto Caprese, Vegetarian Pesto Caprese, Tuscan Pesto Salad, Basil Pesto Shells | Direct + ingredient in name | Easy |
| C22-08 | truffle | Cacio e Pepe Bucatini (truffle butter), Bucatini (chef's menu), Mushroom & White Truffle Oil | Ingredient in description | Medium |
| C22-09 | guacamole | Fresh Avocado, Guacamole (side), Nacho Supreme (in description) | Guacamole = mashed avocado | Easy |
| C22-10 | salsa verde | Veggie Enchiladas (tomatillo salsa), Turkey Avo Salsa Verde, 1/2 Turkey Avo Salsa Verde | Direct name match + description | Easy |
| C22-11 | egg | Spaghetti Carbonara, Zozzona, Carbonara (egg yolk), Egg Flower Soup, Egg Foo Young (all varieties), Huevos Rancheros, Huevos Con Chorizo, Machaca | Ingredient across cuisines | Medium |
| C22-12 | turkey bacon | The Farm Club, 1/2 The Farm Club | Ingredient in description | Medium |
| C22-13 | oyster | Fried Oysters (Staple & Fancy) | Direct ingredient match | Easy |

---

## Category C23: Cuisine Implied — No Cuisine Word in Query
*Queries that imply a cuisine by dish name alone. Includes intentional zero- or near-zero-match queries (marked ✗) to test precision — a system should not return results for things not on any menu.*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C23-01 | noodle soup | ✗ No match — not on any menu | Intentional null query; tests precision | — |
| C23-02 | enchilada | All enchilada variants (Juanita + Plaza Garcia) | Mexican dish name; broad | Easy |
| C23-03 | burrito | Casa Burrito, Burrito Asada, Seafood Burrito, Burrito Al Pastor, Garcia Burrito, etc. | Mexican dish name; broad | Easy |
| C23-04 | quesadilla | Quesadillas (Juanita), Grilled Quesadilla, Veggie Quesadilla (Plaza) | Mexican dish name | Easy |
| C23-05 | fajita | All fajita variants across Juanita and Plaza Garcia | Mexican dish name; broad | Easy |
| C23-06 | chimichanga | Shrimp Chimichangas, Seafood Chimichangas, Combo 15 (Plaza) | Mexican dish name | Easy |
| C23-07 | meatball | Polpette, Polpette Al Sugo (Due' Cucina) | Italian dish concept; Polpette = meatballs | Hard |
| C23-08 | lasagna | Lasagna alla Bolognese (Due' Cucina) | Italian dish name direct match | Easy |
| C23-09 | risotto | Suppli Al Telefono (fried risotto ball, Due') — partial only | Near-miss; risotto not served as main | Hard |
| C23-10 | pancakes | ✗ No match — not on any menu | Intentional null query; tests precision | — |
| C23-11 | banh mi | Vegan Banh Mi, 1/2 Vegan Banh Mi (Mendocino) | Vietnamese dish name; single match | Easy |
| C23-12 | ceviche | Shrimp Ceviche, Three Ceviche Tostadas (Juanita), Ceviche De Camarones (Plaza) | Latin dish name | Easy |

---

## Category C24: Food Type — Pizza
*Only two restaurants serve anything pizza-shaped, so this category also tests whether "pizza" over-generalizes to a related-but-distinct item (Mexican Flatbread) or stays precise.*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C24-01 | pizza | Sicilian Pizza Pie (Rimini), Mexican Pizza (Plaza Garcia); Mexican Flatbread (Juanita, partial) | Broad food type | Easy |
| C24-02 | cheese pizza | Sicilian Pizza Pie (Rimini; cheese, toppings optional) | Ingredient inference (mozzarella = cheese) | Easy |
| C24-03 | mexican pizza | Mexican Pizza (Plaza Garcia) | Direct name match | Easy |

---

## Category C25: Occasion / Meal-Time — Happy Hour
*Tests retrieval driven entirely by `menu_type` metadata rather than dish text — nothing in these items' names or descriptions says "happy hour," so a text-only search scores 0 by construction. Covered at Juanita Cantina and Staple & Fancy only.*

| ID | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| C25-01 | happy hour | All Juanita Cantina Happy Hour items (appetizers + drinks), all Staple & Fancy Happy Hour items (antipasti, pasta, cocktails, wine, beer) | Broad menu-type / occasion match | Easy |
| C25-02 | happy hour appetizers | Juanita Cantina Happy Hour appetizers (Queso Dip, Calamari, Cheese Sticks, etc.); Staple & Fancy Antipasti (full), Pasta section (partial — not strictly appetizers) | Menu-type + category compound | Medium |

---

## Full Summary

### Query Count by Category

| Category | ID | Queries | Focus |
|---|---|---|---|
| Cuisine type inference | C01 | 8 | Cuisine label not in item text |
| Ingredient → category | C02 | 10 | Category generalization |
| Attribute / implied | C03 | 12 | Taste/texture/experience descriptors |
| Cooking method synonyms | C04 | 10 | Grilled/seared/charbroiled/braised |
| Spelling & misspellings | C05 | 15 | Common typos and foreign word errors |
| Stemming & lemmatization | C06 | 10 | Verb forms, plurals, gerunds |
| Hyphenation / spacing / stop words | C07 | 14 | Tokenization edge cases |
| Dietary constraint / negation | C08 | 10 | No X / without X / free of X |
| Synonym / paraphrase | C09 | 10 | Alternative names and concepts |
| Multi-constraint compositional | C10 | 2 | AND logic across multiple fields |
| Food type: soup | C11 | 7 | Food type queries |
| Food type: burger | C12 | 6 | Food type queries |
| Food type: taco | C13 | 8 | Food type + filling combinations |
| Food type: pasta | C14 | 8 | Shape names and sauce descriptions |
| Food type: sandwich | C15 | 7 | English and focaccia sandwiches |
| Food type: salad | C16 | 7 | Named and ingredient-based salads |
| Food type: dessert | C17 | 8 | Cross-restaurant dessert retrieval |
| Main ingredient: chicken | C18 | 6 | English + Spanish pollo items |
| Main ingredient: beef/steak | C19 | 6 | Cut names + Spanish carne |
| Main ingredient: pork | C20 | 6 | Carnitas, guanciale, al pastor |
| Main ingredient: shrimp/seafood | C21 | 9 | Camarones, species names |
| Additional ingredient / sauce | C22 | 13 | Secondary ingredients in descriptions |
| Cuisine implied (no label) | C23 | 12 | Dish names + 2 intentional null queries |
| Food type: pizza | C24 | 3 | Broad + direct-name pizza queries |
| Occasion: happy hour | C25 | 2 | Menu-type metadata, not dish text |
| **Total** | | **209** | |

### Difficulty Distribution

| Difficulty | Count |
|------------|-------|
| Easy | 125 |
| Medium | 55 |
| Hard | 29 |

*The new queries (C11–C25) are weighted toward Easy and Medium — they represent the "typical" searches real users type. The harder linguistic challenges are concentrated in C01–C10. Two queries (C23-01 "noodle soup", C23-10 "pancakes") are intentional null queries with no matching item on any menu — they test precision, not difficulty tier.*

---

## Evaluation Notes

### Relevance Scale
- `2` — Exact / direct match (the item is obviously the target)
- `1` — Partial / plausible match (related category, dietary-compatible, same cuisine section, ingredient mentioned in description)
- `0` — Irrelevant (absent from relevance CSV = treated as 0)

### Intentional Null Queries
Queries 189 ("noodle soup") and 198 ("pancakes") have no matching items on any menu. These test **precision** — a system that over-retrieves will return false positives for these. Track false positive rate separately for null queries.

### Recommended Metrics
- **Recall@K** — primary metric; how many relevant items appear in top-K results
- **NDCG@5** — accounts for ranking quality and graded relevance (0/1/2)
- **MRR** — mean reciprocal rank; how high the first relevant item appears
- **Precision@K** — particularly important for null queries (189, 198)

Run all metrics **per category** (C01–C25) to diagnose where each retrieval system breaks down.

### Suggested Ablation Experiments

| System | Expected strength |
|---|---|
| BM25 baseline | Easy queries in C05, C06, C11–C17; weak on C01, C03, C18–C20 |
| BM25 + stop word handling | Gains on C07 (cacio e pepe, al pastor) |
| BM25 + spell correction | Gains on C05 (misspellings) |
| BM25 + synonym expansion | Gains on C04, C09, C18–C21 (prawn↔shrimp, camarones↔shrimp) |
| Dense embedding | Gains on C03, C22 (attribute/implied, secondary ingredients) |
| Dense + FoodOn ontology | Gains on C02, C20 (ingredient→category, pulled pork→carnitas) |
| Full hybrid (BM25 + dense + ontology + spell) | Should score well across all tiers |
