import torch
import spacy
from transformers import AutoTokenizer, AutoModel

# 1. Load SpaCy for linguistic parsing and BERT for contextual embeddings
nlp = spacy.load("en_core_web_sm")
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModel.from_pretrained("bert-base-uncased")

text = "salad topped with toasted almond sauce"

# 2. Automatically isolate custom phrases and words using spaCy
doc = nlp(text)
segments = []

# Merge noun chunks so "toasted almond sauce" becomes a single token unit
with doc.retokenize() as retokenizer:
    for chunk in doc.noun_chunks:
        # Avoid merging the very first noun if it stands alone
        if len(chunk) > 1 or chunk.root.dep_ != "nsubj": 
            retokenizer.merge(chunk)

# Extract the text of our final segmented pieces
segments = [token.text for token in doc]
print(f"Segmented Phrases: {segments}")
# Output: ['salad', 'topped', 'with', 'toasted almond sauce']


# 3. Generate contextual embeddings for the sentence
inputs = tokenizer(text, return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)
    # Extract the last hidden states (shape: [1, sequence_length, 768])
    word_vectors = outputs.last_hidden_state[0] 

# 4. Map the BERT subword vectors back to our custom phrases
tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
phrase_vectors = {}

for segment in segments:
    # Find which BERT subword tokens belong to this phrase
    subtokens = tokenizer.tokenize(segment)
    
    # Locate the indices of these subtokens inside the original sentence token list
    start_idx = None
    for i in range(len(tokens) - len(subtokens) + 1):
        if tokens[i:i+len(subtokens)] == subtokens:
            start_idx = i
            break
            
    if start_idx is not None:
        end_idx = start_idx + len(subtokens)
        # Average the vectors of all subwords making up the phrase
        phrase_vec = word_vectors[start_idx:end_idx].mean(dim=0)
        phrase_vectors[segment] = phrase_vec

# Now you have a sequence of individual vectors for each item
print("\nVector sequence dimensions:")
for phrase, vector in phrase_vectors.items():
    print(f"Phrase: '{phrase}' -> Vector Shape: {list(vector.shape)}")

