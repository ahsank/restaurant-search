import torch
from transformers import AutoTokenizer, AutoModel
from torch.nn.functional import cosine_similarity

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModel.from_pretrained("bert-base-uncased")

# Sentence 1
inputs1 = tokenizer("toast with jelly", return_tensors="pt")
# Tokens: ['[CLS]', 'toast', 'with', 'jelly', '[SEP]']

# Sentence 2
inputs2 = tokenizer("toasted peanut", return_tensors="pt")
# Tokens: ['[CLS]', 'toast', '##ed', 'peanut', '[SEP]']

with torch.no_grad():
    vecs1 = model(**inputs1).last_hidden_state[0] # Shape: [sequence_length, 768]
    vecs2 = model(**inputs2).last_hidden_state[0]

# Extract the vector for the 'toast' token (Index 1 in both sentences, right after [CLS])
toast_vector_1 = vecs1[1]
toast_vector_2 = vecs2[1]

# Compare them
similarity = cosine_similarity(toast_vector_1.unsqueeze(0), toast_vector_2.unsqueeze(0))
print(f"Cosine Similarity between the two 'toast' vectors: {similarity.item():.4f}")
# Output will be around 0.75 to 0.85 — meaning they are related, but uniquely distinct vectors!

