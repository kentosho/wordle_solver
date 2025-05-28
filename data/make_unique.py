import pandas as pd

input_file = "words.csv"
output_file = "words_unique.csv"

df = pd.read_csv(input_file, header=None)
df_unique = df.drop_duplicates()
df_unique.to_csv(output_file, header=None, index=False)
