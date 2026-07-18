# Menu Search Benchmark Queries
**5 restaurants**: Juanita Cantina, Plaza Garcia, Staple & Fancy, Due' Cucina, Mendocino Farms  
**Restaurants cover**: Mexican/Latin, Italian/Pasta, Modern American, Farm-to-table sandwiches/salads  
**Total queries**: 200 across 23 categories

Each query includes:
- **Expected match(es)**: what it should retrieve
- **Challenge type**: what linguistic/semantic phenomenon is being tested
- **Difficulty**: Easy / Medium / Hard

---

## Category C01: Cuisine Type Not in Item Text (Ontology / Type Inference)
*The item's text doesn't say "Mexican" or "Italian" — it must be inferred from the restaurant type or dish names*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 1 | Mexican food with shrimp | Camarones à la Diabla, Shrimp Fajitas, Tacos De Camaron | Cuisine label inference | Medium |
| 2 | Italian pasta with meat sauce | Mezze Rigatoni (wild boar ragu), Bolognese Ragu', Lasagna | Cuisine inference | Medium |
| 3 | Latin seafood dish | Sopa Del Mar, Seafood Enchiladas, Ceviche De Camarones | Cuisine + category inference | Medium |
| 4 | Tex-Mex combination plate | Combo plates at Plaza Garcia, Juanita Cantina combos | Cuisine inference | Hard |
| 5 | farm to table sandwich | Mendocino Farms sandwiches (their explicit tagline) | Brand/concept → menu | Medium |
| 6 | taqueria style tacos | 3 Street Tacos, Street Tacos | Concept → item type | Hard |
| 7 | rustic Italian comfort food | Lasagna alla Bolognese, Due' Cucina items generally | Concept generalization | Hard |
| 8 | fine dining pasta | Pappardelle (crab, brown butter), Gramigna (Staple & Fancy) | Price/context inference | Hard |

---

## Category C02: Ingredient → Category Generalization
*Query uses a category word; menu uses specific items in that category*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 9 | seafood tacos | Tacos De Pescado (cod), Tacos De Camarones (shrimp) | Ingredient → seafood category | Medium |
| 10 | shellfish pasta | Shrimp & Clam Bucatini, Pappardelle (crab) | Shellfish generalization | Medium |
| 11 | leafy green salad | Gem Lettuce, Little Gem, Cantina Salad (romaine) | Green → specific leaf type | Medium |
| 12 | stone fruit dessert | Tiramisu w/ plum, Burrata (compressed pluot) | Stone fruit generalization | Hard |
| 13 | smoked meat sandwich | Heirloom BLT (bacon), Chimichurri Steak & Bacon | Smoke-cured generalization | Hard |
| 14 | cured meat appetizer | Prosciutto, Bruschetta (smoked fish) | Cured → specific types | Medium |
| 15 | steak dish | Carne Asada, SRF Skirt Wagyu, Ribeye Steak, Coulotte Steak | Steak generalization | Easy |
| 16 | fresh cheese salad | Burrata (heirloom tomato), Burrata Salad | Fresh cheese inference | Medium |
| 17 | pork dishes | Carnitas, Posole, Michoacan Carnitas, Short Ribs Ragu | Pork generalization | Easy |
| 18 | citrus fish | Halibut (Staple & Fancy), Tacos De Pescado (lemon/lime) | Citrus + fish combination | Medium |

---

## Category C03: Attribute / Implied Meaning
*Query uses a taste/texture/experience descriptor; menu describes the underlying ingredient or cooking style*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 19 | spicy shrimp | Camarones à la Diabla, Chipotle Shrimp Enchiladas, Camarones Bravos | Diabla/Diablo → spicy | Medium |
| 20 | something smoky | Smoked Fish Bruschetta, Mezcal cocktails (implied smokiness) | Smoke attribute | Hard |
| 21 | rich creamy pasta | Carbonara, Pollo ala Crema, Radiatore alla Vodka | Cream/egg richness | Medium |
| 22 | light fresh starter | Hamachi Crudo, Shrimp Ceviche, Spring Pea Soup | Light/fresh attribute | Medium |
| 23 | fire grilled meat | Carne Asada (flame grill), Wood Fire Grill section items | Fire → grill method | Medium |
| 24 | comfort food pasta | Lasagna, Bolognese, Kid Red Sauce Pasta | Comfort food concept | Hard |
| 25 | umami dish | Cacio e Pepe (truffle butter), Mushroom & White Truffle Oil | Umami inference | Hard |
| 26 | gut feeling filling meal | Burrito Asada, Seafood Burrito, Casa Burrito | Satiety inference | Hard |
| 27 | cajun style shrimp | Camarones à la Diabla (closest match) | Cajun implies spicy/butter sauce | Hard |
| 28 | tangy dressing salad | Caesar Salad, Gem Lettuce (raspberry vinaigrette) | Tangy → vinaigrette/dressing | Medium |
| 29 | charred vegetables | Roasted Carrots (Staple & Fancy), Fried Artichokes, Veggie Fajitas | Char → roasted/grilled | Medium |
| 30 | indulgent dessert | Affogato Ubriaco, Espresso Affogato, Tiramisu | Indulgent concept | Hard |

---

## Category C04: Cooking Method Synonyms
*Grilled vs seared vs charbroiled vs pan-fried vs flame-cooked*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 31 | charbroiled steak | Carne Asada (flame grill), Steak Matador (char-broiled) | Charbroiled = chargrilled | Easy |
| 32 | seared fish | Halibut (wood fire grill), Pescado a la Parrilla | Seared ↔ grilled | Medium |
| 33 | pan seared salmon | Halibut / Chef's menu salmon items (Staple & Fancy) | Pan seared ↔ wood fire | Medium |
| 34 | blackened chicken | Pollo Asado, Pollo Ranchero (closest matches) | Blackened ↔ seasoned grilled | Hard |
| 35 | flame broiled burger | Jalapeño Cheeseburger, Hawaiian Cheeseburger | Flame broiled = grilled | Medium |
| 36 | wood fired pizza | Mexican Flatbread, Mexican Pizza (closest) | Wood fire concept | Hard |
| 37 | slow cooked pork | Carnitas (slow braised implied), Michoacan Carnitas, Chili Verde | Slow cook inference | Medium |
| 38 | braised beef | Short Ribs Ragu', Taco Birria (beef), Chile Colorado | Braise ↔ ragu/stew | Medium |
| 39 | deep fried appetizer | Taquitos Rancheros, Cheese Sticks, Fried Artichokes | Deep fried = fried | Easy |
| 40 | crispy fried chicken | Not So Fried Chicken (Mendocino), Crispy Chicken Salad | Crispy + fried | Easy |

---

## Category C05: Spelling Variations & Common Misspellings

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 41 | caeser salad | Caesar Salad (Juanita/Plaza Garcia) | Misspelling: Caesar | Easy |
| 42 | quesedilla | Quesadillas | Misspelling: quesadilla | Easy |
| 43 | guacamolee | Fresh Avocado / Guacamole side | Misspelling: guacamole | Easy |
| 44 | enchilladas | Enchiladas (all variants) | Misspelling: enchiladas | Easy |
| 45 | fettucine carbonara | Carbonara (Due' Cucina) | Misspelling: fettuccine; wrong pasta name | Medium |
| 46 | tiramisou | Tiramisu | Misspelling: tiramisu | Easy |
| 47 | prosciuto | Prosciutto | Misspelling: prosciutto | Easy |
| 48 | cevice | Shrimp Ceviche, Ceviche De Camarones | Misspelling: ceviche | Easy |
| 49 | proscuitto and melon | Prosciutto (compressed melon) | Double misspelling | Medium |
| 50 | rigatonni bolognese | Mezze Rigatoni / Bolognese Ragu' | Misspelling: rigatoni | Easy |
| 51 | canoli | Cannolo Siciliano | Misspelling: cannolo | Easy |
| 52 | burratta | Burrata | Misspelling: burrata | Easy |
| 53 | halebut | Halibut | Misspelling: halibut | Easy |
| 54 | focacia sandwich | Artisan Focaccia Sandwiches (Due' Cucina) | Misspelling: focaccia | Easy |

---

## Category C06: Stemming & Lemmatization
*Verb forms, plurals, gerunds that differ from menu text*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 55 | roasted carrot | Roasted Carrots (both restaurants) | Plural stemming | Easy |
| 56 | grilling octopus | Grilled Octopus | Gerund → past participle | Easy |
| 57 | fried artichoke | Fried Artichokes | Plural stemming | Easy |
| 58 | marinated steak | Steak Matador, Fajitas Carne Asada, Tacos Al Carbon | Lemma match | Easy |
| 59 | sauted mushroom | Camarones Mojo de Ajo (mushrooms sautéed) | Misspelling + lemma | Medium |
| 60 | slow braising short rib | Short Ribs Ragu' (slow-braised) | Gerund + plural stem | Medium |
| 61 | breading calamari | Breaded Calamari | Gerund → past participle | Easy |
| 62 | compress melon | Compressed melon (Prosciutto) | Stemming: compressed | Medium |
| 63 | season chicken | Pollo Asado (seasoned), Pollo Ranchero | Lemma: seasoned | Easy |
| 64 | pickle vegetables | Pickled red onion (multiple sandwiches), Dill Pickle Chips | Lemma: pickled | Easy |

---

## Category C07: Hyphenation, Spacing, Apostrophe, Stop Word Variations

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 65 | cacio e pepe | Cacio e Pepe Bucatini | Stop words (e) | Easy |
| 66 | cacioepepe | Cacio e Pepe Bucatini | No-space variant | Easy |
| 67 | al pastor | Burrito Al Pastor, 3 Street Tacos (al pastor option) | Stop word (al) | Easy |
| 68 | alpastor taco | Street Tacos (al pastor) | Merged/no space | Easy |
| 69 | mojo de ajo shrimp | Camarones Mojo de Ajo | Stop words (de) | Easy |
| 70 | arroz con pollo | Arroz Con Pollo | Stop word (con) | Easy |
| 71 | arrozconpollo | Arroz Con Pollo | No space variant | Easy |
| 72 | due cucina pasta | Due' Cucina menu items | Apostrophe drop | Easy |
| 73 | staple fancy restaurant | Staple & Fancy | Ampersand → and/drop | Easy |
| 74 | non dairy pasta | Gramigna, Pomodoro (vegan on request), Mediterranea | Non-dairy = dairy-free | Medium |
| 75 | gluten free pasta | Penne substitution (Staple & Fancy), Pomodoro GF option | Hyphen variation | Easy |
| 76 | glutenfree option | Same as above | No-hyphen variant | Easy |
| 77 | farm-to-table lunch | Mendocino Farms | Hyphenated concept | Easy |
| 78 | egg-free dessert | Sorbetto, Vanilla Gelato (checking for egg) | Hyphen + negation | Hard |

---

## Category C08: Dietary Constraint / Negation Queries
*"no X", "without X", "non-X", "free of X"*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 79 | vegetarian Mexican food | Veggie Fajitas, Spinach Enchilada, Veggie Enchiladas, Queso | Dietary + cuisine | Medium |
| 80 | vegan sandwich | Vegan Banh Mi, Mediterranea (Due' Cucina) | Dietary constraint | Easy |
| 81 | no gluten pasta | GF penne substitution, Pomodoro GF option | Negation = gluten-free | Medium |
| 82 | without dairy | Mediterranea salad (vegan), Southern Potato Salad | Negation = dairy-free | Medium |
| 83 | nut free salad | Golden State Cobb (no nuts noted), Taco Salad | Negation inference | Hard |
| 84 | plant based option | Vegan Banh Mi, Plant-Based Oat Hemp Date Cookie | Plant-based = vegan | Easy |
| 85 | meat free burrito | Burrito Vegetariano, Casa Burrito (no meat option) | Meat-free = vegetarian | Medium |
| 86 | dairy free pasta | Pomodoro (vegan on request), Shrimp & Clam Bucatini | Negation mapping | Hard |
| 87 | pescatarian dinner | Halibut, Pappardelle (crab), Seafood Enchiladas | Pescatarian = fish ok, no meat | Hard |
| 88 | keto friendly | Carne Asada (GF, low carb), salads without tortilla | Keto inference | Hard |

---

## Category C09: Synonym / Paraphrase Variation

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 89 | prawn dish | Camarones (Spanish = shrimp/prawn), Seafood Enchiladas | Prawn ↔ shrimp | Medium |
| 90 | mussel or clam appetizer | Clams with Chorizo | Clam = shellfish synonym | Medium |
| 91 | avocado toast | Bruschetta (Smoked Fish), Sourdough + avocado mentions | Toast = bruschetta | Hard |
| 92 | flatbread | Mexican Flatbread, Bruschetta (grilled bread) | Flatbread concept | Medium |
| 93 | corn tortilla chips and dip | Nachos, Queso Dip, Chips + Salsa | Chips + dip = nachos | Medium |
| 94 | Mexican cheese dip | Queso Dip, Queso Fundido | Cheese dip = queso | Easy |
| 95 | cold raw fish | Hamachi Crudo, Shrimp Ceviche | Raw fish → crudo/ceviche | Medium |
| 96 | Italian rice balls | Suppli Al Telefono | Rice ball = suppli | Hard |
| 97 | espresso based cocktail | Espresso Martini, Oh George (coffee liqueur) | Coffee cocktail | Medium |
| 98 | after dinner drink | Amaro & Liqueur section, Dessert Wine | Post-dinner = digestif/amaro | Hard |

---

## Category C10: Multi-Constraint / Compositional Queries

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 99 | spicy vegetarian taco | Veggie Fajitas w/ salsa, Cauliflower Wings + salsa | Multi-constraint | Hard |
| 100 | gluten free seafood under $30 | Shrimp Fajitas $26 (hit), Ceviche $21 (hit), Halibut $38 (miss) | GF + category + price | Hard |

---

## Category C11: Food Type — Soup
*Single-word and short food-type queries; tests whether the system maps food type to matching items across restaurants. Note: these menus are not soup-heavy so expected recall is low for some queries — useful for testing precision.*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 101 | soup | Tortilla Soup (Juanita/Plaza), Posole, Sopa Del Mar, Tomato Basil Soup, Lemon Chicken & Farro Soup | Broad food type | Easy |
| 102 | chicken soup | Tortilla Soup (grilled chicken in broth), Lemon Chicken & Farro Soup | Ingredient + food type | Easy |
| 103 | tomato soup | Tomato Basil Soup (Mendocino) | Direct food type | Easy |
| 104 | seafood soup | Sopa Del Mar (fish + shrimp in tomato broth) | Category + food type | Medium |
| 105 | spicy soup | Posole (pork stew), Sopa Del Mar | Attribute + food type | Medium |
| 106 | broth based soup | Tortilla Soup, Posole, Lemon Chicken & Farro Soup, Sopa Del Mar | Broth → soup inference | Medium |
| 107 | vegetable soup | Tomato Basil Soup (partial) | Dietary + food type; low recall expected | Hard |

---

## Category C12: Food Type — Burger
*Tests basic food-type retrieval; burgers only appear at the Mexican restaurants.*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 108 | burger | Jalapeño Cheeseburger, Hawaiian Cheeseburger, Cheeseburger, Juanita Chicken Burger, Kids Hamburger | Broad food type | Easy |
| 109 | cheeseburger | Jalapeño Cheeseburger, Hawaiian Cheeseburger, Cheeseburger, Kids Cheeseburger | Direct food type | Easy |
| 110 | chicken burger | Juanita Chicken Burger | Main ingredient + food type | Easy |
| 111 | beef burger | Cheeseburger, Jalapeño Cheeseburger, Hawaiian Cheeseburger | Ingredient inference (beef patty) | Easy |
| 112 | spicy burger | Jalapeño Cheeseburger (jalapeños + pepper jack) | Attribute inference | Medium |
| 113 | Hawaiian burger | Hawaiian Cheeseburger | Direct match (thematic name) | Easy |

---

## Category C13: Food Type — Taco
*Heavy coverage across both Mexican restaurants. Tests Spanish item names (Tacos De Camarones) and filling-based queries against menu titles that don't always name the filling.*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 114 | taco | 3 Street Tacos, Tacos Al Carbon, Taco Birria, Tacos De Pescado, Tacos De Camarones, Street Tacos, Combo 1 | Broad food type | Easy |
| 115 | fish taco | Tacos De Pescado (Pacific cod), Tacos de Pescado (Plaza) | Ingredient + food type | Easy |
| 116 | beef taco | Taco Birria (beef), Tacos Al Carbon (skirt steak) | Ingredient inference | Easy |
| 117 | chicken taco | 3 Street Tacos (chicken option), Tacos Al Carbon (marinated chicken) | Ingredient from description | Medium |
| 118 | shrimp taco | Tacos De Camarones, Tacos De Camaron (Plaza) | Camarones = shrimp inference | Medium |
| 119 | street taco | 3 Street Tacos, Street Tacos (Plaza) | Concept match | Easy |
| 120 | hard taco | Three Hard Tacos (Juanita happy hour) | Direct match | Easy |
| 121 | soft taco | 3 Street Tacos (corn tortillas = soft) | Tortilla type inference | Medium |

---

## Category C14: Food Type — Pasta
*Heavy coverage at Staple & Fancy and Due' Cucina. Tests both generic and specific pasta shape queries, and whether ingredient-in-description queries work (e.g. "pasta with egg" → Carbonara).*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 122 | pasta | Pappardelle, Mezze Rigatoni, Shrimp & Clam Bucatini, Cacio e Pepe Bucatini, Gramigna, Zozzona, Bolognese Ragu', Carbonara, Basil Pesto, Pomodoro | Broad food type | Easy |
| 123 | spaghetti | Spaghetti (chef's veg menu, Staple), Pomodoro (Due', closest shape) | Shape name; partial match expected | Medium |
| 124 | rigatoni | Mezze Rigatoni | Shape name direct match | Easy |
| 125 | bucatini | Shrimp & Clam Bucatini, Cacio e Pepe Bucatini, Bucatini (chef's menu) | Shape name direct match | Easy |
| 126 | pasta with egg | Carbonara (egg yolk explicit), Zozzona (egg yolk) | Ingredient in description | Medium |
| 127 | homemade pasta | All Due' Cucina pasta, Staple & Fancy pasta | Concept: fresh/house-made | Medium |
| 128 | pasta in tomato sauce | Polpette, Bolognese Ragu', Pomodoro, Radiatore alla Vodka (tomato base) | Sauce ingredient | Easy |
| 129 | pasta with truffle | Cacio e Pepe Bucatini (truffle butter), Bucatini (chef's), Mushroom & White Truffle Oil | Ingredient in description | Medium |

---

## Category C15: Food Type — Sandwich
*Concentrated at Mendocino Farms and Due' Cucina focaccia section. Tests whether "sandwich" maps to items described as "focaccia sandwich" or named by their filling.*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 130 | sandwich | All Mendocino Farms sandwiches, all Due' Cucina focaccia sandwiches | Broad food type | Easy |
| 131 | turkey sandwich | The Farm Club, Turkey Avo Salsa Verde | Main ingredient | Easy |
| 132 | chicken sandwich | Not So Fried Chicken, Chicken Parm Dip, Prosciutto & Chicken, Chicken Pesto Caprese | Main ingredient | Easy |
| 133 | BLT | Heirloom BLT; The Farm Club (partial — has B, L, T) | Acronym expansion | Medium |
| 134 | Italian sandwich | Caprese, Mortadella, Porchetta, Milanese (Due' Cucina) | Cuisine inference → sandwich | Medium |
| 135 | focaccia sandwich | All Due' Cucina artisan focaccia items | Bread type + food type | Easy |
| 136 | club sandwich | The Farm Club (name contains "Club") | Name-based inference | Medium |

---

## Category C16: Food Type — Salad
*Mendocino Farms is the primary salad restaurant. Tests breadth of retrieval across named salads.*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 137 | salad | All Mendocino salads, Gem Lettuce (Staple), Caesar Salad (Juanita/Plaza), Carlos Salad (Plaza) | Broad food type | Easy |
| 138 | Caesar salad | The Modern Caesar (Mendocino), Caesar Salad (Juanita), Cesar Salad (Plaza — different spelling) | Direct + spelling variant | Easy |
| 139 | chicken salad | Tuscan Pesto Salad, The Seasonal GOAT, Baja Green Goddess, The Modern Caesar, Chen's Crispy Rice | Ingredient from description | Easy |
| 140 | taco salad | Taco Salad (Juanita/Plaza), Taco Salad Vegetariano | Direct food type | Easy |
| 141 | avocado salad | Avocado & Quinoa Superfood Ensalada, Baja Green Goddess | Ingredient + food type | Easy |
| 142 | quinoa salad | Avocado & Quinoa Superfood Ensalada | Ingredient + food type | Easy |
| 143 | kale salad | Kale & Apple Rainbow Salad | Ingredient + food type | Easy |

---

## Category C17: Food Type — Dessert / Sweet
*Cross-restaurant dessert retrieval. Note intentional gaps: no churros/flan at Staple, Mendocino, or Due' Cucina.*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 144 | dessert | Tiramisu (all), Cheesecake, Espresso Affogato, Cannolo Siciliano, Churros, Flan, Cookies (Mendocino), Sorbetto | Broad food type | Easy |
| 145 | tiramisu | Tiramisu (Staple & Fancy, Due' Cucina, Juanita happy hour) | Direct match across restaurants | Easy |
| 146 | gelato | Vanilla Gelato, Espresso Affogato (vanilla gelato), Affogato Ubriaco | Direct + ingredient match | Easy |
| 147 | churros | Churros (Plaza Garcia only) | Direct match; tests single-restaurant hit | Easy |
| 148 | flan | Flan (Plaza Garcia only) | Direct match | Easy |
| 149 | cheesecake | Cheesecake (Staple & Fancy), Lemon Cheesecake Cookie (Mendocino) | Direct + partial | Easy |
| 150 | cookie | Ginger Molasses Cookie, Lemon Cheesecake Cookie, Plant-Based Oat Hemp Date Cookie, Chocolate Chunk Cookie | Broad food type | Easy |
| 151 | cannoli | Cannolo Siciliano (Due' Cucina) | Direct match; tests singular/plural | Easy |

---

## Category C18: Main Ingredient — Chicken
*Tests retrieval of chicken items described in English ("grilled chicken breast") and Spanish ("pollo asado", "arroz con pollo"). The Spanish-named items are the hard cases.*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 152 | chicken | Pollo Asado, Pollo Chipotle, Arroz Con Pollo, Pollo Ala Crema, Chicken Fajitas, Not So Fried Chicken, Chicken Parm Dip, etc. | Broad ingredient; English + Spanish items | Medium |
| 153 | grilled chicken | Pollo Asado (grilled chicken explicitly), Tacos Al Carbon (marinated grilled chicken) | Cooking method + ingredient | Easy |
| 154 | chicken with mushrooms | Pollo Asado (topped with mushrooms), Arroz Con Pollo (peppers + mushrooms) | Two-ingredient description | Medium |
| 155 | chicken in cream sauce | Pollo Ala Crema, Pollo a la Crema (Plaza) | Sauce inference; Spanish name | Medium |
| 156 | chicken with peppers | Arroz Con Pollo, Chicken Fajitas, Pollo Chipotle, Pollo Bravo | Ingredient in description | Easy |
| 157 | chicken with avocado | Juanita Chicken Burger (avocado in ingredients), Cantina Salad (chicken + avocado option) | Two-ingredient combination | Medium |

---

## Category C19: Main Ingredient — Beef / Steak
*Tests English steak terms against Spanish menu names ("carne asada", "carnitas de res") and specific cut names.*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 158 | beef | Carne Asada, Ribeye Steak, Mexican Steak, Beef Fajitas, Taco Birria, Bolognese Ragu', Short Ribs Ragu', Chile Colorado | Broad ingredient; English + Spanish | Medium |
| 159 | skirt steak | Carne Asada (skirt steak explicit), Mexican Steak (marinated skirt steak), Steak Tapiqueño | Cut name direct match | Easy |
| 160 | ribeye | Ribeye Steak (Juanita), Chef Special (charbroiled ribeye at Plaza) | Cut name direct match | Easy |
| 161 | ground beef | Cheeseburger (ground beef patty), Nacho Supreme (ground beef option) | Ingredient in description | Medium |
| 162 | beef stew | Chile Colorado (beef cubes in spicy red sauce), Posole (stew-style) | Stew concept inference | Medium |
| 163 | short rib | Short Ribs Ragu' (Due' Cucina) | Direct ingredient match | Easy |

---

## Category C20: Main Ingredient — Pork
*Includes Spanish pork terms (carnitas, guanciale, al pastor) that a lexical system will miss without synonym expansion.*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 164 | pork | Michoacan Carnitas, Chili Verde, Burrito Al Pastor, Posole, Zozzona (guanciale), Carbonara (guanciale), Mortadella, Porchetta | Broad ingredient; cross-language | Hard |
| 165 | carnitas | Michoacan Carnitas, Carnitas De Puerco, 3 Street Tacos (option) | Spanish term direct match | Easy |
| 166 | guanciale pasta | Carbonara, Zozzona (both use guanciale explicitly) | Italian ingredient term | Medium |
| 167 | pulled pork | Michoacan Carnitas (closest equivalent — shredded pork) | Synonym: pulled pork = carnitas | Hard |
| 168 | pork with green sauce | Chili Verde, Burrito Chili Verde (tomatillo = green sauce) | Sauce colour inference | Medium |
| 169 | bacon wrapped | Camarones con Bacon (shrimp wrapped in bacon), Camarones Garcia (bacon-wrapped) | Cooking presentation | Easy |

---

## Category C21: Main Ingredient — Shrimp / Seafood
*The most densely covered ingredient across the two Mexican restaurants. Also tests Spanish names (camarones), specific seafood types (crab, scallops, tilapia, cod), and cross-ingredient queries.*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 170 | shrimp | Camarones à la Diabla, Camarones Mojo de Ajo, Camarones con Bacon, Shrimp Juanita, Shrimp Fajitas, Shrimp Ceviche, Tacos De Camarones, Garlic Shrimp, Shrimp & Clam Bucatini, and more | Broad ingredient; English + Spanish | Medium |
| 171 | garlic shrimp | Shrimp Juanita (sautéed in garlic), Camarones Mojo de Ajo (mojo de ajo = garlic sauce), Garlic Shrimp (Plaza) | Mojo de ajo = garlic inference | Medium |
| 172 | shrimp with rice | Camarones à la Diabla (served with rice), Arroz Con Mariscos (shrimp on rice) | Preparation + side | Medium |
| 173 | crab | Pappardelle (crab, brown butter), Seafood Enchiladas (contains crab), Seafood Burrito, Seafood Chimichangas | Ingredient in description | Medium |
| 174 | scallops | Seafood Enchiladas (shrimp, fish, crab, scallops), Seafood Burrito, Seafood Chimichangas | Ingredient in description | Medium |
| 175 | octopus | Grilled Octopus (Staple & Fancy) | Direct match; single restaurant | Easy |
| 176 | fish | Tacos De Pescado, Sopa Del Mar, Pescado a la Parrilla, Halibut, Smoked Fish Bruschetta | Broad ingredient; English + Spanish | Easy |
| 177 | tilapia | Pescado a la Parrilla (grilled tilapia explicitly, Plaza Garcia) | Species name direct match | Easy |
| 178 | cod | Tacos De Pescado (Pacific cod, Juanita) | Species name in description | Medium |

---

## Category C22: Additional Ingredient / Sauce / Flavour
*Tests retrieval by a secondary ingredient or sauce mentioned in item descriptions rather than item names.*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 179 | black bean | Rice & Beans, Beans (Juanita), Nacho Supreme (black beans in description) | Ingredient in description | Easy |
| 180 | avocado | Fresh Avocado, Avocado Tostada, Avocado Slices, Fiesta Avocado, Avocado & Quinoa Ensalada, The Farm Club | Ingredient direct + in description | Easy |
| 181 | chipotle sauce | Chipotle Shrimp Enchiladas, Pollo Chipotle, Pollo Chipotle (Plaza) | Sauce name in item name | Easy |
| 182 | mole sauce | Pollo en Mole, Enchiladas en Mole, Pollo En Mole (Plaza), Deluxe Mole Enchilada | Sauce name in item name | Easy |
| 183 | tomatillo | Chili Verde (green tomatillo sauce), Burrito Chili Verde, Veggie Enchiladas | Ingredient in description | Medium |
| 184 | pico de gallo | Pico De Gallo (side), Carne Asada (garnished with pico) | Ingredient direct + in description | Easy |
| 185 | pesto | Basil Pesto (Due'), Chicken Pesto Caprese, Vegetarian Pesto Caprese, Tuscan Pesto Salad, Basil Pesto Shells | Direct + ingredient in name | Easy |
| 186 | truffle | Cacio e Pepe Bucatini (truffle butter), Bucatini (chef's menu), Mushroom & White Truffle Oil | Ingredient in description | Medium |
| 187 | guacamole | Fresh Avocado, Guacamole (side), Nacho Supreme (in description) | Guacamole = mashed avocado | Easy |
| 188 | salsa verde | Veggie Enchiladas (tomatillo salsa), Turkey Avo Salsa Verde, 1/2 Turkey Avo Salsa Verde | Direct name match + description | Easy |

---

## Category C23: Cuisine Implied — No Cuisine Word in Query
*Queries that imply a cuisine by dish name alone. Includes intentional zero- or near-zero-match queries (marked ✗) to test precision — a system should not return results for things not on any menu.*

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 189 | noodle soup | ✗ No match — not on any menu | Intentional null query; tests precision | — |
| 190 | enchilada | All enchilada variants (Juanita + Plaza Garcia) | Mexican dish name; broad | Easy |
| 191 | burrito | Casa Burrito, Burrito Asada, Seafood Burrito, Burrito Al Pastor, Garcia Burrito, etc. | Mexican dish name; broad | Easy |
| 192 | quesadilla | Quesadillas (Juanita), Grilled Quesadilla, Veggie Quesadilla (Plaza) | Mexican dish name | Easy |
| 193 | fajita | All fajita variants across Juanita and Plaza Garcia | Mexican dish name; broad | Easy |
| 194 | chimichanga | Shrimp Chimichangas, Seafood Chimichangas, Combo 15 (Plaza) | Mexican dish name | Easy |
| 195 | meatball | Polpette, Polpette Al Sugo (Due' Cucina) | Italian dish concept; Polpette = meatballs | Hard |
| 196 | lasagna | Lasagna alla Bolognese (Due' Cucina) | Italian dish name direct match | Easy |
| 197 | risotto | Suppli Al Telefono (fried risotto ball, Due') — partial only | Near-miss; risotto not served as main | Hard |
| 198 | pancakes | ✗ No match — not on any menu | Intentional null query; tests precision | — |
| 199 | banh mi | Vegan Banh Mi, 1/2 Vegan Banh Mi (Mendocino) | Vietnamese dish name; single match | Easy |
| 200 | ceviche | Shrimp Ceviche, Three Ceviche Tostadas (Juanita), Ceviche De Camarones (Plaza) | Latin dish name | Easy |

---

## Full Summary

### Query Count by Category

| Category | ID | Queries | Focus |
|---|---|---|---|
| Cuisine type inference | C01 | 8 | Cuisine label not in item text |
| Ingredient → category | C02 | 10 | Category generalization |
| Attribute / implied | C03 | 12 | Taste/texture/experience descriptors |
| Cooking method synonyms | C04 | 10 | Grilled/seared/charbroiled/braised |
| Spelling & misspellings | C05 | 14 | Common typos and foreign word errors |
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
| Additional ingredient / sauce | C22 | 10 | Secondary ingredients in descriptions |
| Cuisine implied (no label) | C23 | 12 | Dish names + 2 intentional null queries |
| **Total** | | **200** | |

### Difficulty Distribution

| Difficulty | Count |
|------------|-------|
| Easy | 107 |
| Medium | 63 |
| Hard | 28 |
| — (null query) | 2 |

*The new queries (C11–C23) are weighted toward Easy and Medium — they represent the "typical" searches real users type. The harder linguistic challenges are concentrated in C01–C10.*

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

Run all metrics **per category** (C01–C23) to diagnose where each retrieval system breaks down.

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
