# Menu Search Benchmark Queries
**5 restaurants**: Juanita Cantina, Plaza Garcia, Staple & Fancy, Due' Cucina, Mendocino Farms  
**Restaurants cover**: Mexican/Latin, Italian/Pasta, Modern American, Farm-to-table sandwiches/salads

Each query includes:
- **Expected match(es)**: what it should retrieve
- **Challenge type**: what linguistic/semantic phenomenon is being tested
- **Difficulty**: Easy / Medium / Hard

---

## Category 1: Cuisine Type Not in Item Text (Ontology / Type Inference)
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

## Category 2: Ingredient → Category Generalization
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

## Category 3: Attribute / Implied Meaning
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

## Category 4: Cooking Method Synonyms
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

## Category 5: Spelling Variations & Common Misspellings

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

## Category 6: Stemming & Lemmatization
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

## Category 7: Hyphenation, Spacing, Apostrophe, Stop Word Variations

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

## Category 8: Dietary Constraint / Negation Queries
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

## Category 9: Synonym / Paraphrase Variation

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

## Category 10: Multi-Constraint / Compositional Queries

| # | Query | Expected Match | Challenge Type | Difficulty |
|---|-------|----------------|----------------|------------|
| 99 | spicy vegetarian taco | Veggie Fajitas w/ salsa, Cauliflower Wings + salsa | Multi-constraint | Hard |
| 100 | gluten free seafood under $30 | Halibut $38 (miss), Shrimp Fajitas $26 (hit), Ceviche $21 (hit) | GF + category + price | Hard |

---

## Summary by Challenge Type

| Challenge Type | Query Count |
|----------------|-------------|
| Cuisine/concept inference (not in item text) | 8 |
| Ingredient → category generalization | 10 |
| Attribute / implied meaning | 12 |
| Cooking method synonyms | 10 |
| Spelling misspellings | 14 |
| Stemming & lemmatization | 10 |
| Hyphenation / spacing / stop words / negation | 14 |
| Dietary constraint / negation | 10 |
| Synonym / paraphrase | 10 |
| Multi-constraint compositional | 2 |
| **Total** | **100** |

## Difficulty Distribution

| Difficulty | Count |
|------------|-------|
| Easy | 40 |
| Medium | 38 |
| Hard | 22 |

---

## Evaluation Notes

**Relevance tiers to apply per query:**
- `2` — Exact / direct match (the item is obviously the target)
- `1` — Partial / plausible match (related category, dietary-compatible, same cuisine section)
- `0` — Irrelevant

**Metrics to run per difficulty tier:**
- NDCG@5, Recall@10, MRR

**Suggested ablation experiments** using this set:
1. BM25 baseline (lexical only) — will score well on Easy, poorly on Medium/Hard
2. BM25 + synonym expansion (cooking methods, food categories) — gains on Category 4 & 9
3. Dense embedding (e.g. `text-embedding-3-small`) — gains on attribute/implication queries
4. Dense + FoodOn ontology → query expansion — gains on ingredient → category queries
5. Full hybrid (BM25 + dense + ontology + spell correction) — should score well across all tiers
